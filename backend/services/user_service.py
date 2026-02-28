from datetime import datetime, timezone
from sqlalchemy.orm import Session
from db.models import User
from authent.encryption import encrypt_token

def create_or_update_user(db: Session, email: str, name: str, google_sub: str, access_token: str, refresh_token: str = None) -> User:
    """
    Creates a new user or updates an existing user's tokens
    """
    user = db.query(User).filter(User.email == email).first()

    # If user doesn't exist, create new entry. If user exists, update tokens
    if not user:
        user = User(
            email=email,
            full_name=name,
            created_at=datetime.now(timezone.utc),
            google_sub=encrypt_token(google_sub),
            encrypted_access_token=encrypt_token(access_token),
            encrypted_refresh_token=encrypt_token(refresh_token) if refresh_token else None
        )
        db.add(user)
    else:
        user.encrypted_access_token = encrypt_token(access_token)
        if refresh_token:
            user.encrypted_refresh_token = encrypt_token(refresh_token)
    
    db.commit()
    db.refresh(user)
    return user

def get_user_sync_status(db: Session, user_id: int):
    """
    Retrieves timestamp for the last sync of a user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.last_synced:
        return user.last_synced.isoformat() + "Z"
    return None