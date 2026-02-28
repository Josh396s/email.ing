import logging
import time
import re
import json
import requests
from google import genai
from google.genai import types
from authent.encryption import decrypt_token
from config import settings
from services.privacy import mask_content, deanonymize_text
from bs4 import BeautifulSoup
from prompts import LLAMA_CLASSIFICATION_PROMPT, GEMINI_SUMMARIZATION_PROMPT

client = genai.Client(api_key=settings.GEMINI_API_KEY)

OLLAMA_URL = "http://ollama:11434/api/generate" 

def prepare_email_for_ai(email_record):
    """
    Decrypts the email body, strips HTML, masks PII, and prepares it for AI processing
    """
    try:
        if not email_record.body_text:
            return "No content.", {}
            
        raw_body = decrypt_token(email_record.body_text)
        
        # Remove all HTML/CSS
        soup = BeautifulSoup(raw_body, "html.parser")
        clean_text = soup.get_text(separator=" ", strip=True)
        
        masked_body, pii_map = mask_content(clean_text)
        
        return masked_body[:1500].strip(), pii_map
    except Exception as e:
        print(f"Preparation Error: {e}")
        return "[Content Error]", {}

def get_classification_ollama(email_text):
    """
    Classification LLM: Local Llama handles classification and urgency scoring
    """
    prompt = LLAMA_CLASSIFICATION_PROMPT
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "keep_alive": "1h"
        }, timeout=120)

        raw_response = response.json()['response']

        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(raw_response)
    
    except (json.JSONDecodeError, Exception) as e:
        logging.error(f"Failed to parse LLM output: {raw_response}")
        return {"category": "Uncategorized", "urgency": "3"}

def classify_and_summarize_batch(email_records: list):
    """
    Summarization LLM: Combines Ollama's classification with Gemini's summaries
    """
    email_blocks = []
    pii_vault = {} 
    ollama_results = {}
    ollama_times = {}

    # Extract Category & Urgency with Llama
    for e in email_records:
        content, pii_map = prepare_email_for_ai(e)
        pii_vault[e.id] = pii_map
        
        start_ollama = time.time()
        class_data = get_classification_ollama(content)
        end_ollama = time.time()

        ollama_results[e.id] = class_data
        ollama_times[e.id] = (end_ollama - start_ollama) * 1000

        email_blocks.append(
            f"ID: {e.id}\nSender: {e.sender}\nSubject: {e.subject}\nContent: {content}\n---"
        )

    # Generate summary using Gemini
    prompt = GEMINI_SUMMARIZATION_PROMPT.format(
        num_emails=len(email_records), 
        email_blocks=chr(10).join(email_blocks)
    )

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    ]

    try:
        start_gemini = time.time()

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                safety_settings=safety_settings
            )
        )

        end_gemini = time.time()
        gemini_total_ms = (end_gemini - start_gemini) * 1000
        gemini_ms_per_email = gemini_total_ms / len(email_records)

        gemini_results = json.loads(response.text)
        final_results = []
        
        # Combine classification and summary, and deanonymize if needed
        for res in gemini_results:
            try:
                email_id = int(res.get("id"))
            except (TypeError, ValueError):
                print(f"AI returned invalid ID format: {res.get('id')}")
                continue
            
            if email_id in pii_vault:
                res["summary"] = deanonymize_text(res["summary"], pii_vault[email_id])
            
            class_data = ollama_results.get(email_id, {})

            local_ms = ollama_times.get(email_id, 0)
            total_ms = round(local_ms + gemini_ms_per_email)


            final_results.append({
                "id": email_id,
                "category": class_data.get("category", "Uncategorized"),
                "urgency": str(class_data.get("urgency", "1")),
                "summary": res["summary"],
                "inference_time": total_ms
            })
            
        return final_results
    
    except Exception as e:
        print(f"Batch AI Error: {e}")
        return [{"id": e.id, "summary": "Error: Batch processing failed.", "category": "Error"} for e in email_records]