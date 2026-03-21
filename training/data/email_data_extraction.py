from bs4 import BeautifulSoup
import mailbox
from email.header import decode_header, make_header
import csv
import re

# Function that walks through the email object and returns only the main content decoded
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

# Set where we will read our data and where we will save the processed output
input_path = 'data/personal_emails.mbox'
output_path = 'emails.csv'

# Read in our mbox file of emails
emails = mailbox.mbox(input_path)

# Set up the columns
headers = ['subject', 'body']

# Write the processed data in our output file
with open(output_path, mode='w', newline='', encoding='utf-8-sig') as csv_file:
    writer = csv.writer(csv_file)

    writer.writerow(headers)

    for email in emails:

        # Get the email
        message = email

        # Extract the header and add to row
        subject = message['subject']
        if subject is None:
            continue
        decoded_header = decode_header(subject)
        new_subject = make_header(decoded_header)
        row = [new_subject]

        # Extract the body, clean it, and add to row
        body = get_body(message)
        if body is None:
            continue
        body = BeautifulSoup(body, 'html.parser')
        body = body.get_text()
        body = re.sub(r'http\S+', '', body)
        body = ' '.join(body.split())
        row.append(body)

        # Write the row to the csv file
        writer.writerow(row)