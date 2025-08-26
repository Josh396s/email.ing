import base64
from db.db import SessionLocal
from db.models import Email, User

def fetch_and_store_emails(service, user: User):
    session = SessionLocal()

    results = service.users().messages().list(userId="me").execute()
    messages = results.get('messages', [])

    for msg_info in messages:
        msg_id = msg_info['id']
        existing_email = session.query(Email).filter(Email.email_id == msg_id).first()
        if existing_email:
            continue  # Skip if already stored
        
        msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), None)
        sender = next((h['value'] for h in headers if h['name'] == 'From'), None)
        received_at = None
        for h in headers:
            if h['name'] == 'Date':
                # Parse date string if needed
                received_at = h['value']
                break

        email_record = Email(
            user_id=user.id,
            email_id=msg_id,
            sender=sender,
            subject=subject,
            received_at=received_at
        )
        session.add(email_record)
    session.commit()
    session.close()
