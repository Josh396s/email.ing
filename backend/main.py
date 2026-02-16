from fastapi import FastAPI, Depends, Request, Response, HTTPException, Cookie, status
from fastapi.responses import RedirectResponse

from fastapi.middleware.cors import CORSMiddleware

from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware

from db.database import get_db
from db.models import User, Email
from sqlalchemy.orm import Session

from authent.encryption import encrypt_token
from authent.token_utils import create_access_token, decode_access_token, get_current_user

from tasks import sync_user_emails

from config import settings
from datetime import datetime, timezone

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!secret")

# Allow your local Next.js dev server to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Your Next.js address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/login")
async def login(request: Request):
    """
    Initiate google Oauth process
    """
    redirect_uri=request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri, access_type='offline')

@app.get("/auth")
async def auth(request: Request, db: Session = Depends(get_db)):
    """
    Authentication route. Handles Google callback, user creation/update, and JWT issuance
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Google auth failed: {str(e)}")
    
    # Get user info
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user info from Google.")

    google_access_token = token.get('access_token')
    google_refresh_token = token.get('refresh_token')
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
    
    # Redirect user back to main page
    redirect = RedirectResponse(url='http://localhost:3000')
    
    # Inclulde JWT token in cookies
    redirect.set_cookie(
        key="user_token", 
        value=access_token_jwt, 
        httponly=True,
        path="/",
        samesite="lax", # Important for cross-port local dev
        secure = True
    )
    
    return redirect

@app.get("/auth/status")
async def get_auth_status(request: Request):
    """
    Authenticate user by decoding token
    """
    token = request.cookies.get("user_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        return {"authenticated": True, "user_id": payload.get("user_id")}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")

@app.post("/sync")
async def trigger_sync(current_user: User = Depends(get_current_user)):
    """
    Fetches new emails and generates AI content
    """
    # Sends Redis task
    task = sync_user_emails.delay(current_user.id)
    return {"message": "Sync started", "task_id": task.id}

@app.get("/emails")
def get_emails(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Gets user's recent emails from DB
    """
    user_emails = db.query(Email)\
        .filter(Email.user_id == current_user.id)\
        .order_by(Email.id.desc())\
        .all()
    
    return user_emails

@app.get("/logout")
async def logout(response: Response):
    """
    Logs user out of session
    """
    response.delete_cookie(
        key="user_token",
        path="/",
        samesite="lax",
    )
    return {"message": "Successfully logged out"}