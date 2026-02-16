from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import OAuth2PasswordBearer

from config import settings
from db.database import get_db
from db.models import User
from sqlalchemy.orm import Session

# Defines the scheme for expecting a token in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# JWT Token Creation
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Generates a new JWT access token
    The payload includes the user's ID for identification and a timestamp for expiration
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRATION_MINUTES) 
        
    to_encode.update({"exp": expire, "sub": "access"})
    
    # Encode and sign the token
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt

# JWT Token Decoding & Validation
def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodes and validates a JWT access token. Raises JWTError on failure.
    """
    try:
        # Decode and verify the signature and expiry
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # Ensure the token is intended for access
        if payload.get("sub") != "access":
            raise JWTError("Invalid token type")
            
        return payload
        
    except JWTError:
        HTTPException(status_code=401, detail="Could not validate credentials")

# Dependency to retrieve the current user from the token
def get_current_user(request: Request, db: Session = Depends(get_db)):
    # Get JWT token
    token = request.cookies.get("user_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify the user, else return an error
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")