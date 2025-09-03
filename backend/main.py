from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse

from authlib.integrations.starlette_client import OAuth
from db.database import get_db
from db.models import User
from db.schemas import UserInfo, UserEncrypt
from sqlalchemy.orm import Session
from authent.Encryption import encrypt_token, decrypt_token

import os, json
from datetime import datetime

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="!secret")

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
    user = request.session.get('user')
    if user:
        data = json.dumps(user)
        html = (
            f'<pre>{data}</pre>'
            '<a href="/logout">logout</a>'
        )
        return HTMLResponse(html)
    return HTMLResponse('<a href="/login">login</a>')

@app.get("/login")
async def login(request: Request):
    redirect_uri=request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri, access_type='offline')

@app.get("/auth")
async def auth(request: Request, db: Session=Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user = token.get('userinfo')
    if user:
        request.session['user'] = user
        request.session['access_token'] = token['access_token']
        request.session['refresh_token'] = token.get('refresh_token')

        # Check if user is in db, if not add them
        user_email = request.session['user']['email']
        entry = db.query(User).filter(User.email==user_email).first()
        if not entry:
            return RedirectResponse(url='/create_user')    
        return RedirectResponse(url='/')
            
    
@app.get("/create_user")
async def create_user(request:Request, db: Session=Depends(get_db)):
    user_info = {
        'email' : request.session['user']['email'],
        'full_name' : request.session['user']['name'],
        'created_at' : datetime.now()
    }
    user_encrypt = {
        'google_sub' : encrypt_token(request.session['user']['sub']),
        'encrypted_access_token' : encrypt_token(request.session['access_token']),
        'encrypted_refresh_token' : encrypt_token(request.session['refresh_token'])
    }

    # Validate info via pendatic schemas
    user = UserInfo(**user_info) 
    user_crypt = UserEncrypt(**user_encrypt)

    # Create user entry
    user = User(
        email = user_info['email'],
        full_name = user_info['full_name'],
        created_at = user_info['created_at'],
        google_sub = user_encrypt['google_sub'],
        encrypted_access_token = user_encrypt['encrypted_access_token'],
        encrypted_refresh_token = user_encrypt['encrypted_refresh_token']
    )
    
    # Add user to db
    db.add(user)
    db.commit()

    return RedirectResponse(url='/')

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

# @app.get("/oauth2callback")
# async def oauth2callback(request: Request, db: SessionLocal = Depends(get_db)):
#     code = request.query_params.get("code", None)
#     if not code:
#         raise HTTPException(status_code=400, detail="No code in request")

#     flow = Flow.from_client_secrets_file(
#         GOOGLE_CLIENT_SECRETS_FILE,
#         scopes=SCOPES,
#         redirect_uri=REDIRECT_URI
#     )
#     flow.fetch_token(code=code)
#     creds = flow.credentials

#     # Get user email
#     resp = requests.get(
#         "https://www.googleapis.com/oauth2/v2/userinfo",
#         headers={"Authorization": f"Bearer {creds.token}"}
#     )
#     userinfo = resp.json()
#     email = userinfo.get("email")

#     if not email:
#         raise HTTPException(status_code=400, detail="Unable to get user email")

#     # Save user to DB if needed
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         user = User(email=email)
#         db.add(user)
#         db.commit()
#         db.refresh(user)

#     # Use your existing save_credentials to save tokens for this email
#     save_credentials(email, creds)

#     return JSONResponse({"message": f"User {email} logged in successfully!"})

# @app.get("/emails")
# async def list_emails(email: str, db: SessionLocal = Depends(get_db)):
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     creds = load_credentials(email)
#     if not creds or not creds.valid:
#         raise HTTPException(status_code=401, detail="User not authenticated")

#     # Use creds to call Gmail API here
#     service = build("gmail", "v1", credentials=creds)
#     # fetch emails...

#     return {"emails": "Emails fetched successfully"}

















# from fastapi import Request 
# from starlette.responses import RedirectResponse 
# from authlib.integrations.starlette_client import OAuthError 

# @app.route('/login') 
# async def login(request: Request, id: str): 
#     redirect_uri = request.url_for('auth') # This creates the url for the /auth endpoint \
#     return await oauth.google.authorize_redirect(request, redirect_uri, state=id) 

# @app.route('/auth') 
# async def auth(request: Request, state: str = ''): 
#     try:
#         access_token = await oauth.google.authorize_access_token(request) 
#     except OAuthError:
#          return RedirectResponse(url='/')
#     user_data = await oauth.google.parse_id_token(request, access_token) 
#     request.session['user'] = dict(user_data) 
#     return RedirectResponse(url=f'/{id}')