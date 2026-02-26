from google import genai
from google.genai import types
from authent.encryption import decrypt_token
import json
import requests
from config import settings
from services.privacy import mask_content, deanonymize_text
from bs4 import BeautifulSoup

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
    prompt = f"""
        You are a precise email classifier. Analyze the email below and return EXACTLY a valid JSON object with 'category' and 'urgency'. Do not output any markdown or conversational text.

        CATEGORIES:
        - Work: Direct messages from colleagues, clients, or specific project updates.
        - Transactional: Receipts, shipping updates, password resets, subscriptions.
        - Newsletter: Automated job alerts, promotional offers, marketing, and mailing lists.
        - Personal: Messages from real human friends or family.

        URGENCY SCALE:
        1 - Very Low: Promotions, marketing, spam, glasses sales.
        2 - Low: Automated digests, receipts, subscription notices, LinkedIn job alerts.
        3 - Normal: Standard emails requiring an eventual response.
        4 - High: Time-sensitive tasks, meetings happening today.
        5 - Critical: Server outages, absolute emergencies.

        Example 1:
        Email: "LinkedIn: 10 new Machine Learning Engineer roles in your area. Apply to IBM and more..."
        Output: {{"category": "Newsletter", "urgency": 2}}

        Example 2:
        Email: "Massive Weekend Sale! Get 50% off all prescription glasses."
        Output: {{"category": "Newsletter", "urgency": 1}}

        Example 3:
        Email: "Your Cosmo: Learn GenAI subscription from CodeSignal on Google Play will be canceled on Oct 14."
        Output: {{"category": "Transactional", "urgency": 2}}

        Example 4:
        Email: "Hey man, are we still on for grabbing food on Friday?"
        Output: {{"category": "Personal", "urgency": 3}}

        Example 5:
        Email: "Production server is down! We need a fix immediately."
        Output: {{"category": "Work", "urgency": 5}}

        Now analyze this email:
        Email: {email_text[:1500]}
        Output:
    """
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=30)

        return json.loads(response.json()['response'])
    except Exception as e:
        print(f"Ollama Error: {e}")
        return {"category": "Uncategorized", "urgency": "1"}

def classify_and_summarize_batch(email_records: list):
    """
    Summarization LLM: Combines Ollama's classification with Gemini's summaries
    """
    email_blocks = []
    pii_vault = {} 
    ollama_results = {}

    # Extract Category & Urgency with Llama
    for e in email_records:
        content, pii_map = prepare_email_for_ai(e)
        pii_vault[e.id] = pii_map
        
        class_data = get_classification_ollama(content)
        ollama_results[e.id] = class_data
        
        email_blocks.append(
            f"ID: {e.id}\nSender: {e.sender}\nSubject: {e.subject}\nContent: {content}\n---"
        )

    # Generate summary using Gemini
    prompt = f"""
    Analyze these {len(email_records)} emails. 
    CRITICAL: If an email contains harmful or dangerous content, summarize it as "Content blocked due to safety concerns."

    EMAILS:
    {chr(10).join(email_blocks)}

    Return exactly this JSON list structure:
    [
        {{
            "id": <id>,
            "summary": "25-word action-oriented summary."
        }}
    ]
    """

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    ]

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                safety_settings=safety_settings
            )
        )

        gemini_results = json.loads(response.text)
        final_results = []
        
        # Combine classification and summary, and deanonymize if needed
        for res in gemini_results:
            email_id = res.get("id")
            
            if email_id in pii_vault:
                res["summary"] = deanonymize_text(res["summary"], pii_vault[email_id])
            
            class_data = ollama_results.get(email_id, {})
            final_results.append({
                "id": email_id,
                "category": class_data.get("category", "Uncategorized"),
                "urgency": str(class_data.get("urgency", "1")),
                "summary": res["summary"]
            })
            
        return final_results
    
    except Exception as e:
        print(f"Batch AI Error: {e}")
        return [{"id": e.id, "summary": "Error: Batch processing failed.", "category": "Error"} for e in email_records]