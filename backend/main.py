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

# NEW IMPORTS
from authent.encryption import encrypt_token, decrypt_token
from authent.token_utils import create_access_token, get_current_user

import os, json
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

oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url=os.environ.get('GOOGLE_METADATA_URL'),
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account',
        'redirect_uri': os.getenv("GOOGLE_REDIRECT_URI")
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
async def auth(request: Request, db: Session=Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    
    if user_info:
        google_access_token = token['access_token']
        google_refresh_token = token.get('refresh_token')
        google_sub = user_info['sub']
        user_email = user_info['email']
        user_name = user_info.get('name', '')

        entry = db.query(User).filter(User.email==user_email).first()
        
        # If user is new, redirect to creation route
        if not entry:
            refresh_param = f"&refresh={google_refresh_token}" if google_refresh_token else ""
            return RedirectResponse(url=f'/create_user?email={user_email}&name={user_name}&sub={google_sub}&access={google_access_token}{refresh_param}', status_code=status.HTTP_307_TEMPORARY_REDIRECT)

        # User exists: Update tokens and issue JWT
        
        # 1. Update encrypted tokens in DB
        entry.encrypted_access_token = encrypt_token(google_access_token)
        if google_refresh_token:
            entry.encrypted_refresh_token = encrypt_token(google_refresh_token)
        db.commit()
        
        # 2. Issue JWT
        access_token_jwt = create_access_token(data={"user_id": entry.id})
        
        return JSONResponse(content={
            "message": "Login successful",
            "access_token": access_token_jwt,
            "token_type": "bearer",
            "user_id": entry.id
        })
    
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google authentication failed.")
    
@app.get("/create_user")
async def create_user(request:Request, email: str, name: str, sub: str, access: str, refresh: str | None = None, db: Session=Depends(get_db)):
    # Encrypt sensitive tokens
    user_encrypt = {
        'google_sub' : encrypt_token(sub),
        'encrypted_access_token' : encrypt_token(access),
        'encrypted_refresh_token' : encrypt_token(refresh) if refresh else None
    }

    # Create user entry
    user = User(
        email = email,
        full_name = name,
        created_at = datetime.now(timezone.utc),
        google_sub = user_encrypt['google_sub'],
        encrypted_access_token = user_encrypt['encrypted_access_token'],
        encrypted_refresh_token = user_encrypt['encrypted_refresh_token']
    )
    
    # Add user to db
    db.add(user)
    db.commit()
    db.refresh(user)

    # 4. Issue JWT upon creation
    access_token_jwt = create_access_token(data={"user_id": user.id})

    return JSONResponse(content={
        "message": "User created and logged in successful",
        "access_token": access_token_jwt,
        "token_type": "bearer",
        "user_id": user.id
    })

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')