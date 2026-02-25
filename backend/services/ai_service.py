from google import genai
from google.genai import types
from authent.encryption import decrypt_token
import json
from config import settings
from services.privacy import mask_content, deanonymize_text

# Initialize the Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

def prepare_email_for_ai(email_record):
    """
    Decrypts the email body, masks PII, and prepares it for AI processing
    """
    try:
        if not email_record.body_text:
            return "No content.", {}
            
        body = decrypt_token(email_record.body_text)
        masked_body, pii_map = mask_content(body)
        
        # Truncate after masking to keep placeholders intact
        return masked_body[:2500].strip(), pii_map
    except Exception as e:
        return "[Content Error]", {}

def classify_and_summarize_batch(email_records: list):
    """
    Sends a batch of masked emails to Gemini with safety settings enabled.
    """
    email_blocks = []
    pii_vault = {} 

    # Prepare each email for the prompt
    for e in email_records:
        content, pii_map = prepare_email_for_ai(e)
        pii_vault[e.id] = pii_map
        
        email_blocks.append(
            f"ID: {e.id}\nSender: {e.sender}\nSubject: {e.subject}\nContent: {content}\n---"
        )

    prompt = f"""
    Analyze these {len(email_records)} emails. 
    
    CRITICAL: If an email contains harmful or dangerous content, 
    DO NOT summarize it. Instead, set the category to "Safety Warning" 
    and the summary to "Content blocked due to safety concerns."

    EMAILS:
    {chr(10).join(email_blocks)}

    Return exactly this JSON list structure:
    [
        {{
            "id": <id>,
            "category": "Work/Personal/Newsletter/Transactional",
            "urgency": "1-5",
            "summary": "25-word action-oriented summary."
        }}
    ]
    """

    # Safety settings to block harmful content
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    ]

    # Call the Gemini API
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                safety_settings=safety_settings
            )
        )

        results = json.loads(response.text)
        
        # Unmask any masked PII in the summaries before returning 
        for res in results:
            email_id = res.get("id")
            if email_id in pii_vault:
                res["summary"] = deanonymize_text(res["summary"], pii_vault[email_id])
        return results
    
    except Exception as e:
        print(f"Batch AI Error: {e}")
        return [{"id": e.id, "summary": "Error: Batch processing failed.", "category": "Error"} for e in email_records]