import base64
from sqlalchemy.orm import Session
from fastapi.responses import Response
from datetime import datetime, timezone
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

    if not messages:
        return

    # Fetch all maxResults emails from DB to avoid multiple queries in the loop
    fetched_msg_ids = [msg['id'] for msg in messages]
    existing_records = db.query(Email.email_id).filter(Email.email_id.in_(fetched_msg_ids)).all()
    existing_ids = {record[0] for record in existing_records}

    # Process each email message
    for msg_info in messages:
        msg_id = msg_info['id']
        
        # Skip if email has already been fetched
        if msg_id in existing_ids:
            continue
        
        try:
            # Use a nested transaction to ensure that if any step fails, we can roll back just that email's processing without affecting others
            with db.begin_nested(): 
                msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                payload = msg.get('payload')
            
                # Get HTML and Attachments
                html_content, found_attachments = get_email_body_content(payload) 
                
                # Extract email headers for subject and sender information
                headers = payload.get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
                sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
                
                # Get email's internal timestamp and convert to datetime
                internal_date_ms = int(msg.get('internalDate', 0))
                received_timestamp = datetime.fromtimestamp(internal_date_ms / 1000.0, tz=timezone.utc)

                # Create Email record
                email_record = Email(
                    user_id=user.id,
                    email_id=msg_id,
                    thread_id=msg_info.get('threadId'),
                    sender=sender,
                    subject=subject,
                    received_at=received_timestamp,
                    body_text=encrypt_token(html_content),
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
        
        # Catch any exceptions during processing of an email, log it, and continue with the next one
        except Exception as e:
            print(f"Failed to process email {msg_id}: {e}")
            continue
    db.commit()

def get_recent_emails_for_user(db: Session, user_id: int, limit: int = 50):
    """
    Returns list of emails for the user, ordered by recency
    """
    return db.query(Email)\
        .filter(Email.user_id == user_id)\
        .order_by(Email.id.desc())\
        .limit(limit)\
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
                "url": att.google_attachment_id,
                "size": att.size
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
    
def download_attachment(db: Session, user: User, email_id: int, attachment_id: int):
    """
    Fetches raw attachment data from Google API and decodes it.
    """
    # Get the email and attachment records
    email_record = db.query(Email).filter(Email.id == email_id, Email.user_id == user.id).first()
    if not email_record:
        raise Exception("Email not found")
        
    attachment_record = db.query(Attachment).filter(Attachment.id == attachment_id, Attachment.email_id == email_id).first()
    if not attachment_record:
        raise Exception("Attachment not found")

    # Fetch the raw data from Gmail API
    service = get_gmail_service(db, user)
    try:
        attachment_obj = service.users().messages().attachments().get(
            userId='me', 
            messageId=email_record.email_id, # Google's message ID
            id=attachment_record.google_attachment_id # Google's attachment ID
        ).execute()
        
        # Decode the base64 URL-safe string
        file_data = base64.urlsafe_b64decode(attachment_obj['data'])
        return file_data, attachment_record.mime_type, attachment_record.filename, attachment_record.size
        
    except Exception as e:
        print(f"Failed to fetch attachment: {e}")
        raise Exception("Could not retrieve attachment from Google")