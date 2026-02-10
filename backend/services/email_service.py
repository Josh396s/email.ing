# backend/services/email_service.py

import base64 
from dateutil import parser 
from datetime import datetime, timezone 
from sqlalchemy.orm import Session
from db.models import Email, User
from authent.token_service import get_gmail_service 
from authent.encryption import encrypt_token
from bs4 import BeautifulSoup 

def get_email_body_content(msg_payload: dict) -> str:
    """
    Recursively extracts the decoded, plain-text body content.
    It prioritizes 'text/plain' and falls back to stripping 'text/html'.
    """
    
    # 1. Handle multipart/alternative (the most common email format)
    if msg_payload.get('mimeType') == 'multipart/alternative':
        plain_text_part = None
        html_part = None
        
        for part in msg_payload.get('parts', []):
            if part.get('mimeType') == 'text/plain':
                plain_text_part = part
            if part.get('mimeType') == 'text/html':
                html_part = part
        
        # Prioritize plain text if it exists, as it's already clean
        if plain_text_part:
            return get_email_body_content(plain_text_part)
        # Fallback to HTML if no plain text is found
        if html_part:
            return get_email_body_content(html_part)

    # 2. Handle other multipart (like mixed for attachments)
    if 'multipart' in msg_payload.get('mimeType', ''):
        for part in msg_payload.get('parts', []):
            # Recurse to find the first text part
            body = get_email_body_content(part)
            if body:
                return body

    # 3. Base Case: Handle the actual content part (plain or HTML)
    if 'text/' in msg_payload.get('mimeType', ''):
        if msg_payload.get('body', {}).get('data'):
            data = msg_payload['body']['data']
            data = data.replace('-', '+').replace('_', '/')
            padding = len(data) % 4
            if padding != 0:
                data += '=' * (4 - padding)
            
            try:
                decoded_data = base64.b64decode(data).decode('utf-8')
                
                # CRITICAL: Strip HTML tags if this is an HTML part
                if msg_payload['mimeType'] == 'text/html':
                    soup = BeautifulSoup(decoded_data, 'html.parser')
                    # Use .get_text() to extract only human-readable text
                    return soup.get_text(separator=' ') 
                else:
                    return decoded_data # It's plain text

            except Exception as e:
                print(f"Error decoding/parsing body data: {e}")
                return ""

    return "" # No text part found


def fetch_and_store_emails(db: Session, user: User): 
    
    service = get_gmail_service(db, user)

    signup_timestamp = int(user.created_at.timestamp())
    query = f"after:{signup_timestamp}"

    results = service.users().messages().list(
        userId="me", 
        maxResults=50, 
        q=query  # This is the new "since signup" filter
    ).execute()

    messages = results.get('messages', [])

    for msg_info in messages:
        msg_id = msg_info['id']
        thread_id = msg_info.get('threadId') 
        
        existing_email = db.query(Email).filter(Email.email_id == msg_id).first()
        if existing_email:
            continue
        
        msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        
        payload = msg.get('payload')
        if not payload:
            print(f"Warning: Skipping message {msg_id} due to missing payload.")
            continue
        
        # --- HEADER EXTRACTION LOGIC ---
        headers = payload.get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), None)
        sender = next((h['value'] for h in headers if h['name'] == 'From'), None)
        
        received_at_str = next((h['value'] for h in headers if h['name'] == 'Date'), None)
        parsed_received_at = None
        if received_at_str:
            try:
                parsed_received_at = parser.parse(received_at_str) 
            except Exception:
                print(f"Warning: Failed to parse date: {received_at_str}")
        
        # --- BODY EXTRACTION (NOW WITH HTML STRIPPING) ---
        full_body = get_email_body_content(payload) 
        
        # --- ENCRYPTION STEP ---
        encrypted_body = encrypt_token(full_body)
        
        # 4. Create the Email record
        email_record = Email(
            user_id=user.id,
            email_id=msg_id,
            thread_id=thread_id,          
            sender=sender,
            subject=subject,
            received_at=parsed_received_at,
            body_text=encrypted_body,      # STORE THE ENCRYPTED (AND CLEANED) BODY
            category=None,                 
            urgency=None                   
        )
        db.add(email_record)
        
    db.commit()

def reconcile_deleted_emails(db: Session, user: User, gmail_service):
    """
    Identifies emails in the DB that no longer exist in Gmail and sets is_deleted=True (Soft Delete).
    WARNING: This process is SLOW as it requires fetching ALL message IDs from Gmail.
    """
    
    # 1. Get all email IDs currently stored for this user (Fast DB query)
    # Exclude already soft-deleted emails from the check
    stored_email_ids = db.query(Email.email_id).filter(
        Email.user_id == user.id,
        Email.is_deleted == False
    ).all()
    stored_ids = {id[0] for id in stored_email_ids} # Convert to set for fast lookup
    
    if not stored_ids:
        print(f"No active emails found for reconciliation for user {user.id}")
        return 0
        
    # 2. Get ALL currently existing message IDs from Gmail (Slow operation - requires pagination)
    gmail_existing_ids = set()
    next_page_token = None
    
    while True:
        # Fetch up to 500 message IDs per request (better than the default 100)
        results = gmail_service.users().messages().list(
            userId="me", 
            maxResults=500,
            pageToken=next_page_token
        ).execute()
        
        for message in results.get('messages', []):
            gmail_existing_ids.add(message['id'])
            
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break
            
    # 3. Find deleted IDs: IDs in our storage but NOT in Gmail's current list
    deleted_ids_to_soft_delete = stored_ids - gmail_existing_ids
    
    if deleted_ids_to_soft_delete:
        # 4. Execute Soft Deletion: Update the is_deleted flag
        print(f"Soft-deleting {len(deleted_ids_to_soft_delete)} emails for user {user.id}")
        
        (db.query(Email)
            .filter(Email.user_id == user.id)
            .filter(Email.email_id.in_(deleted_ids_to_soft_delete))
            .update({Email.is_deleted: True}, synchronize_session=False))
            
        db.commit()
        return len(deleted_ids_to_soft_delete)
    
    return 0