import base64
from sqlalchemy.orm import Session
from db.models import Email, User, Attachment
from authent.token_service import get_gmail_service 
from authent.encryption import encrypt_token, decrypt_token

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

def get_recent_emails_for_user(db: Session, user_id: int):
    """
    Returns list of emails for the user, ordered by recency
    """
    return db.query(Email)\
        .filter(Email.user_id == user_id)\
        .order_by(Email.id.desc())\
        .all()

def get_email_details(db: Session, user_id: int, email_id: int):
    """
    Fetches a specific email, decrypts its body, and formats attachments
    """
    email = db.query(Email).filter(Email.id == email_id, Email.user_id == user_id).first()
    
    # If email doesn't exist or has no body, return a default message
    if not email or not email.body_text:
        return {"body": "No content available.", "attachments": []}

    try:
        decrypted_body = decrypt_token(email.body_text)
        
        # Obtain attachments
        valid_attachments = [
            {
                "id": att.id,
                "filename": att.filename,
                "filetype": att.mime_type,
                "url": att.google_attachment_id
            } for att in email.attachments 
            if att.filename and "signature" not in att.filename.lower() and "image" not in att.filename.lower()
        ]

        return {
            "body": decrypted_body,
            "attachments": valid_attachments
        }
    except Exception as e:
        print(f"Decryption error: {e}")
        return {"body": "Error decrypting content.", "attachments": []}