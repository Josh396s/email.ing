from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from authent.auth_utils import SCOPES, get_credentials, load_credentials, save_credentials
from starlette.responses import HTMLResponse
from starlette.applications import Starlette
from starlette.config import Config
from authlib.integrations.starlette_client import OAuth
from db.init_db import SessionLocal
from db.models import User

from jose import jwt
import requests, os, json

#REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret")


oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account',
        'redirect_uri': 'http://localhost:8000/auth'
        }
)

@app.route('/')
async def homepage(request):
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
    return await oauth.google.authorize_redirect(request, redirect_uri)
    
@app.get("/auth")
async def auth(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = token.get('userinfo')
    if user:
        request.session['user'] = user
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