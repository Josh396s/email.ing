from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from authlib.integrations.starlette_client import OAuth
from starlette.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from db.database import get_db
from db.models import User
from db.schemas import UserInfo, UserEncrypt
from sqlalchemy.orm import Session

from authent.encryption import encrypt_token, decrypt_token
from authent.token_utils import create_access_token, get_current_user

from services.email_service import fetch_and_store_emails

from tasks import sync_user_emails

from config import settings
from datetime import datetime, timezone

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!secret")

# Allow the Chrome Extension to connect
app.add_middleware(
    CORSMiddleware,
    # This regex allows local development (http://localhost:8000) and any chrome-extension origin
    allow_origin_regex="^https?:\/\/localhost.*|chrome-extension:\/\/.*",
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*", "Authorization"],
)

######################################## TEST ##################################################
@app.post("/test/fetch_emails")
async def test_fetch_emails(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    TEMPORARY: Tests the full Day 2 flow: JWT -> Decrypt Tokens -> Gmail API -> DB Storage.
    """
    try:
        # Call the core service function
        fetch_and_store_emails(db, current_user)
        
        return {
            "message": "SUCCESS: Email fetching and storing completed.",
            "user": current_user.email,
            "status": "Check your database for new 'emails' entries."
        }
    except Exception as e:
        # This will catch errors in decryption, token refresh, or Gmail API calls
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Email fetching failed: {str(e)}"
        )
######################################## TEST ##################################################


oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url=settings.GOOGLE_METADATA_URL,
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    client_kwargs={
        'scope': settings.SCOPES,
        'prompt': 'select_account',
        'redirect_uri': settings.GOOGLE_REDIRECT_URI
    }
)

@app.get('/')
async def homepage(request: Request):
    return HTMLResponse('Welcome to Email.ing. <a href="/login">login</a> or <a href="/docs">View API Docs</a>')


######################################## TEST ##################################################
@app.get("/test_protected")
async def test_protected_route(current_user: User = Depends(get_current_user)):
    """
    A simple route that requires a valid JWT in the Authorization header.
    """
    # This shows the user object retrieved securely from the DB using the JWT's payload
    return {"message": f"Hello, {current_user.full_name}. This is a protected route! Your ID is {current_user.id}."}

######################################## TEST ##################################################

@app.get("/login")
async def login(request: Request):
    redirect_uri=request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri, access_type='offline')

@app.get("/auth")
async def auth(request: Request, db: Session = Depends(get_db)):
    """
    Authentication route. Handles Google callback, 
    user creation/update, and JWT issuance.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Google auth failed: {str(e)}")
        
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user info from Google.")

    google_access_token = token.get('access_token')
    google_refresh_token = token.get('refresh_token')  # Only present on first login or if prompt=consent
    google_sub = user_info.get('sub')
    user_email = user_info.get('email')
    user_name = user_info.get('name', '')

    # Check if user exists
    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        # Create New User
        user = User(
            email=user_email,
            full_name=user_name,
            created_at=datetime.now(timezone.utc),
            google_sub=encrypt_token(google_sub),
            encrypted_access_token=encrypt_token(google_access_token),
            encrypted_refresh_token=encrypt_token(google_refresh_token) if google_refresh_token else None
        )
        db.add(user)
    else:
        # Update Existing User
        user.encrypted_access_token = encrypt_token(google_access_token)
        # Only update refresh token if a new one is provided
        if google_refresh_token:
            user.encrypted_refresh_token = encrypt_token(google_refresh_token)
    
    db.commit()
    db.refresh(user)

    # Issue secure application JWT
    access_token_jwt = create_access_token(data={"user_id": user.id})
    
    # Return directly to the client (Chrome Extension or Frontend)
    return JSONResponse(content={
        "message": "Authentication successful",
        "access_token": access_token_jwt,
        "token_type": "bearer",
        "user_id": user.id
    })

@app.post("/sync")
async def trigger_sync(current_user: User = Depends(get_current_user)):
    # Sends task to Redis and returns immediately
    task = sync_user_emails.delay(current_user.id)
    return {"message": "Sync started", "task_id": task.id}

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')