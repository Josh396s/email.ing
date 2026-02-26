import base64
from sqlalchemy.orm import Session
from db.models import Email, User, Attachment
from authent.token_service import get_gmail_service 
from authent.encryption import encrypt_token

def get_email_body_content(msg_payload: dict):
    '''
    Walks through the email payload to extract key information
    '''
    html_body = ""
    plain_text = ""
    attachments = []

    def walk_parts(parts):
        nonlocal html_body, plain_text

        # Walk through each part of the email payload
        for part in parts:
            mime_type = part.get("mimeType")
            filename = part.get("filename")
            body = part.get("body", {})
            data = body.get("data")
            attachment_id = body.get("attachmentId")

            # Capture HTML, plain text, or attachments
            if mime_type == "text/html" and data:
                html_body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            elif mime_type == "text/plain" and data:
                plain_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            elif filename and attachment_id:
                attachments.append({
                    "filename": filename,
                    "mime_type": mime_type,
                    "attachment_id": attachment_id,
                    "size": body.get("size", 0)
                })

            if "parts" in part:
                walk_parts(part["parts"])

    walk_parts(msg_payload.get("parts", [msg_payload]))
    
    # Prioritize HTML for the UI, fall back to Plain Text for simple emails
    final_body = html_body if html_body else plain_text
    return final_body, attachments

def fetch_and_store_emails(db: Session, user: User): 
    '''
    Fetches emails from Gmail API and stores them in the database.
    '''
    service = get_gmail_service(db, user)

    # Only fetch emails received after the user's signup date
    signup_timestamp = int(user.created_at.timestamp())
    query = f"after:{signup_timestamp}"

    # Fetch the list of email IDs matching the query
    results = service.users().messages().list(userId="me", maxResults=20, q=query).execute()
    messages = results.get('messages', [])

    # Process each email message
    for msg_info in messages:
        msg_id = msg_info['id']
        if db.query(Email).filter(Email.email_id == msg_id).first():
            continue
        
        msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        payload = msg.get('payload')
        
        # Get HTML and Attachments
        html_content, found_attachments = get_email_body_content(payload) 
        
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")

        # Create Email record
        email_record = Email(
            user_id=user.id,
            email_id=msg_id,
            thread_id=msg_info.get('threadId'),
            sender=sender,
            subject=subject,
            body_text=encrypt_token(html_content), # Encrypting HTML
            is_processed=False
        )
        db.add(email_record)
        db.flush()

        # Create Attachment records
        for att in found_attachments:
            db_att = Attachment(
                email_id=email_record.id,
                filename=att['filename'],
                mime_type=att['mime_type'],
                google_attachment_id=att['attachment_id'],
                size=att['size']
            )
            db.add(db_att)
        
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