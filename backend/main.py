from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

from google_auth_oauthlib.flow import Flow
from authent.auth_utils import SCOPES, get_credentials, load_credentials, save_credentials
from db.init_db import SessionLocal
from db.models import User

from jose import jwt
import requests, os

app = FastAPI()
GOOGLE_CLIENT_SECRETS_FILE = "authent/credentials.json"
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth2callback")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/login")
async def login():
    flow = get_credentials()
    auth_url, _ = flow.authorization_url(prompt="consent")
    return RedirectResponse(auth_url)

@app.get("/oauth2callback")
async def oauth2callback(request: Request, db: SessionLocal = Depends(get_db)):
    code = request.query_params.get("code", None)
    if not code:
        raise HTTPException(status_code=400, detail="No code in request")

    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Get user email
    resp = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {creds.token}"}
    )
    userinfo = resp.json()
    email = userinfo.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Unable to get user email")

    # Save user to DB if needed
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Use your existing save_credentials to save tokens for this email
    save_credentials(email, creds)

    return JSONResponse({"message": f"User {email} logged in successfully!"})

@app.get("/emails")
async def list_emails(email: str, db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    creds = load_credentials(email)
    if not creds or not creds.valid:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Use creds to call Gmail API here
    service = build("gmail", "v1", credentials=creds)
    # fetch emails...

    return {"emails": "Emails fetched successfully"}