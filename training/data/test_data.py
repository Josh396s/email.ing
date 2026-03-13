from bs4 import BeautifulSoup
import mailbox
from email.header import decode_header
import csv
import re

def get_body(message):
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == 'text/plain':
                charset = part.get_content_charset() or 'utf-8'
                return part.get_payload(decode=True).decode(charset, errors='replace')
    else:
        if message.get_content_type() == 'text/plain':
            charset = message.get_content_charset() or 'utf-8'
            return message.get_payload(decode=True).decode(charset, errors='replace')
    return None

emails = mailbox.mbox('data/personal_emails.mbox')

for i in range(10):
    message = emails[i]

    subject = message['subject']
    subject = decode_header(subject)

    ########## USE REGEX TO REMOVE \x STUFF##################################################################################################################
    print(f'{subject[0][0]}\n')

    # Get the body
    body = get_body(message)

    # Parse the HTML body to retrieve only the text
    body = BeautifulSoup(body, 'html.parser')
    body = body.get_text()

    # Remove any links
    body = re.sub(r'http\S+', '', body)

    print(f'{body}\n\n')

    print("'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''")