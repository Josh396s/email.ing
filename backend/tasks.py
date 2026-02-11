import os
from celery import Celery
from services.email_service import fetch_and_store_emails
from db.database import Session
from db.models import User

# Initialize Celery
celery_app = Celery(
    "email_ing",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
)

@celery_app.task(name="sync_user_emails")
def sync_user_emails(user_id: int):
    db = Session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "User not found"
        
        # Run the email fetching and storing logic for the user
        fetch_and_store_emails(db, user)
        return f"Successfully synced emails for user {user_id}"
    finally:
        db.close()