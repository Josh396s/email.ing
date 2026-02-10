from config import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from db.models import User
from .encryption import decrypt_token, encrypt_token

def get_gmail_service(db: Session, user: User):
    """
    Retrieves, decrypts, and possibly refreshes the user's Google tokens,
    then returns an initialized Gmail API service object.
    """
    
    # Decrypt the tokens stored in the database
    access_token = decrypt_token(user.encrypted_access_token)
    
    # Check if a refresh token exists and decrypt it
    refresh_token = None
    if user.encrypted_refresh_token:
        refresh_token = decrypt_token(user.encrypted_refresh_token)

    # Build the Credentials object
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=settings.SCOPES
    )

    # Check if token is expired and needs refreshing
    if creds.expired and creds.refresh_token:
        # Use the Request object from google.auth.transport.requests to initiate the refresh
        creds.refresh(Request())
        
        # Update the DB with the new access token after refresh
        user.encrypted_access_token = encrypt_token(creds.token)
        db.commit()
    
    # Initialize and return the Gmail API service
    service = build("gmail", "v1", credentials=creds)
    return service