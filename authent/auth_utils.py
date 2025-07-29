import os
import json
from google.auth.transport.requests import Request # pyright: ignore[reportMissingImports]
from google.oauth2.credentials import Credentials # pyright: ignore[reportMissingImports]
from google_auth_oauthlib.flow import InstalledAppFlow # pyright: ignore[reportMissingImports]
from googleapiclient.discovery import build # pyright: ignore[reportMissingImports]

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_DIR = 'tokens'

# Function that runs OAuth process and saves user's info
def get_credentials():
    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file('authent/credentials.json', SCOPES)
    creds = flow.run_local_server(port=8080, access_type='offline', prompt='consent')

    # Use the access token to get the user's email
    service = build('gmail', 'v1', credentials=creds)
    user_info = service.users().getProfile(userId='me').execute()
    user_email = user_info['emailAddress']

    # Save token using actual email
    os.makedirs(TOKEN_DIR, exist_ok=True)
    token_path = os.path.join(TOKEN_DIR, f'{user_email}.json')
    with open(token_path, 'w') as token_file:
        token_file.write(creds.to_json())

    return creds, user_email

# Function that checks for user's saved info
def load_credentials(email):
    token_path = os.path.join(TOKEN_DIR, f'{email}.json')
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'w') as token_file:
                token_file.write(creds.to_json())
        return creds
    return None
