from google import genai
from google.genai import types
import json
from config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def classify_and_summarize_batch(email_list: list):
    """
    email_list: A list of dicts [{'id': 1, 'subject': '...', 'sender': '...'}, ...]
    """
    # Create a compact string of the emails for the prompt
    emails_str = "\n".join([
        f"ID: {e['id']} | From: {e['sender']} | Subject: {e['subject']}" 
        for e in email_list
    ])

    prompt = f"""
    Analyze these {len(email_list)} emails and return a JSON array of objects.
    
    Emails:
    {emails_str}

    Return exactly this JSON structure:
    [
        {{
            "id": <id_from_input>,
            "category": "Work/Social/etc",
            "urgency": "1-5",
            "summary": "one sentence"
        }},
        ...
    ]
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Batch AI Error: {e}")
        raise e # Let Celery handle the retry