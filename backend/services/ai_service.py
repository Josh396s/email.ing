from google import genai
from google.genai import types
from authent.encryption import decrypt_token
import json
from config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def prepare_email_for_ai(email_record):
    """
    Decrypts and cleans the email body for the LLM prompt
    """
    try:
        if not email_record.body_text:
            return "No content."
            
        # Decrypt and decode
        body = decrypt_token(email_record.body_text).decode('utf-8')
        
        # Limit to 2500 chars for resource purposes
        return body[:2500].strip() 
    except:
        return "[Content Error]"

def classify_and_summarize_batch(email_records: list):
    """
    Prompt LLM for categorization and summarization
    """
    # Create list of emails for processing
    email_blocks = []
    for e in email_records:
        content = prepare_email_for_ai(e)
        email_blocks.append(
            f"ID: {e.id}\nSender: {e.sender}\nSubject: {e.subject}\nContent: {content}\n---"
        )
    
    prompt = f"""
    Analyze these {len(email_records)} emails. 
    Use the 'Content' field to provide a deep, action-oriented summary.
    
    EMAILS:
    {chr(10).join(email_blocks)}

    Return exactly this JSON list structure:
    [
        {{
            "id": <id>,
            "category": "Work/Personal/Newsletter/Transactional",
            "urgency": "1-5",
            "summary": "Focus on general content & next step. Limit summary to 25 words"
        }}
    ]
    """
    
    # Return LLM output
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Batch AI Error: {e}")
        raise e