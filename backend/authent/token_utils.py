from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Import security constants from your existing file
from .encryption import JWT_SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRATION 
from db.database import get_db
from db.models import User
from sqlalchemy.orm import Session

# Defines the scheme for expecting a token in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# JWT Token Creation
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Generates a new JWT access token.
    The payload includes the user's ID for identification and a timestamp for expiry.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRATION) 
        
    to_encode.update({"exp": expire, "sub": "access"})
    
    # Encode and sign the token
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

# JWT Token Decoding & Validation
def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodes and validates a JWT access token. Raises JWTError on failure.
    """
    try:
        # Decode and verify the signature and expiry
        payload = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[ALGORITHM]
        )
        # Ensure the token is intended for access
        if payload.get("sub") != "access":
            raise JWTError("Invalid token type")
            
        return payload
        
    except JWTError:
        # Raise an exception that will be caught by the FastAPI dependency handler
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Dependency to retrieve the current user from the token
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Retrieves the User object corresponding to the valid JWT in the Authorization header.
    """
    payload = decode_access_token(token)
    user_id: int = payload.get("user_id")
    
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")
        
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
        
    return user