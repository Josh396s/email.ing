from db.database import Session
from db.models import User, Email
from services.ai_service import prepare_email_for_ai

#### USE TO PULL EMAILS FROM DB AND DECRYPT THEM/PRE-PROCESS THEM FOR TESTING ONLY!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

db = Session()

records = db.query(Email).filter(
            Email.user_id == 1, 
        ).limit(20).all()

for r in records:
    print(f'EMAIL:\n{prepare_email_for_ai(r)}\n\n')