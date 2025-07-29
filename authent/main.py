from auth_utils import get_credentials, load_credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import base64

def main():
    print("Welcome!")
    
    # Ask user to input email
    email = input("Enter your email: ").strip().lower()

    # Try to load credentials
    creds = load_credentials(email)

    # If credentials aren't saved, ask them to log in
    if not creds:
        print("No credentials found or expired. Please log in.")
        creds, actual_email = get_credentials()
        
        # If user inputs email different than the one signed in to, return
        if actual_email != email:
            print(f"Error: The email you typed ({email}) does not match the account you just logged into ({actual_email}).")
            return

    try:
        # Call the Gmail API to get user emails
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me").execute()
        messages = results.get('messages', [])

        # Print user's first email for testing purposes
        if messages:
            message_id = messages[0]['id']
            msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
            
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')

            print(f"Subject: {subject}")
            print(f"From: {sender}")

            # Accessing message body
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                        body_data = part['body']['data']
                        decoded_body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        print(f"\nBody:\n{decoded_body}")
                        break

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

if __name__ == '__main__':
    main()
