from db.db import SessionLocal
from db.models import User
from sqlalchemy.exc import NoResultFound

def get_or_create_user(email: str):
    session = SessionLocal()
    user = session.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        session.add(user)
        session.commit()
        session.refresh(user)
    session.close()
    return user
