from fastapi import FastAPI, Depends, Request, Response, HTTPException, Cookie, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User, Email
from authent.token_utils import create_access_token, decode_access_token, get_current_user

from services import user_service, email_service
from tasks import sync_user_emails
from config import settings

# Initialize FastAPI app and middleware
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!secret")

# Allow your local Next.js dev server to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up OAuth client for Google
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
    # Exchange authorization code for tokens
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Google auth failed: {str(e)}")
    
    # Get user info
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user info from Google.")

    # Create or update user in DB
    user = user_service.create_or_update_user(
        db=db,
        email=user_info.get('email'),
        name=user_info.get('name', ''),
        google_sub=user_info.get('sub'),
        access_token=token.get('access_token'),
        refresh_token=token.get('refresh_token')
    )

    # Create JWT token for session
    access_token_jwt = create_access_token(data={"user_id": user.id})
    
    # Set JWT in HttpOnly cookie and redirect to frontend
    redirect = RedirectResponse(url='http://localhost:3000')
    redirect.set_cookie(
        key="user_token", 
        value=access_token_jwt, 
        httponly=True,
        path="/",
        samesite="lax", 
        secure=True
    )
    return redirect

@app.get("/auth/status")
async def get_auth_status(request: Request, db: Session = Depends(get_db)):
    """
    Authenticate user and fetch sync status
    """
    # Check for JWT token in cookies
    token = request.cookies.get("user_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Decode token to get user ID and sync status    
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")

        last_synced = user_service.get_user_sync_status(db, user_id)

        return {
            "authenticated": True, 
            "user_id": user_id,
            "last_synced": last_synced
        }
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
    return email_service.get_recent_emails_for_user(db, current_user.id)

@app.get("/emails/{email_id}/body")
async def get_email_body(email_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieves and decrypts the body content of a specific email, along with its attachments
    """
    return email_service.get_email_details(db, current_user.id, email_id)


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