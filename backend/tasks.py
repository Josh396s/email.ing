import os
from celery import Celery
from services.email_service import fetch_and_store_emails
from db.database import Session
from db.models import User, Email

from services.ai_service import classify_and_summarize_batch
from google.api_core import exceptions
import json

# Initialize Celery
celery_app = Celery(
    "email_ing",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
)

@celery_app.task(name="sync_user_emails")
def sync_user_emails(user_id: int):
    """
    Update DB with user's emails and AI content
    """
    db = Session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "User not found"
        
        fetch_and_store_emails(db, user)
        process_emails_with_ai.delay(user_id)
        return f"Successfully synced emails for user {user_id}"
    finally:
        db.close()

@celery_app.task(
    name="process_emails_with_ai",
    bind=True,
    autoretry_for=(exceptions.ResourceExhausted,),
    retry_backoff=60,
    max_retries=5
)
def process_emails_with_ai(self, user_id: int):
    """
    Fetch emails and generate AI content
    """
    db = Session()
    try:
        # Fetch 5-10 records at a time
        records = db.query(Email).filter(
            Email.user_id == user_id, 
            Email.is_processed == False
        ).limit(10).all()

        if not records:
            return "Inbox analyzed."

        # Pass the whole records list to the batch function
        results = classify_and_summarize_batch(records)

        # Update the DB with the AI's "Deep" insights
        results_map = {res['id']: res for res in results}
        for r in records:
            if r.id in results_map:
                data = results_map[r.id]
                r.category = data.get("category")
                r.summary = data.get("summary")
                r.urgency = str(data.get("urgency"))
                r.is_processed = True
        
        db.commit()
        return f"Deep analysis complete for {len(records)} emails."
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()