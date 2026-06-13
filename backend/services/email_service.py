import sys
import os
from pathlib import Path
import imaplib
import email
from email.header import decode_header

# This ensures that even when called from frontend, it can find backend.database
root_path = str(Path(__file__).resolve().parent.parent.parent)
if root_path not in sys.path:
    sys.path.append(root_path)

from backend.database import supabase

def process_inbound_emails():
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")

    if not email_user or not email_pass:
        raise Exception("Missing EMAIL_USER or EMAIL_PASS in .env file")

    mail = None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        mail.select("inbox")

        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK' or not messages[0]:
            return "No new emails"

        for num in messages[0].split():
            _, msg_data = mail.fetch(num, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject_raw = decode_header(msg["Subject"])[0][0]
                    subject = subject_raw.decode() if isinstance(subject_raw, bytes) else str(subject_raw)
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors='ignore')
                    else:
                        body = msg.get_payload(decode=True).decode(errors='ignore')

                    ticket_res = supabase.table("tickets").insert({
                        "subject": subject,
                        "requester_email": msg.get("From"),
                        "status": "New",
                        "source": "email",
                        "category": "General IT"
                    }).execute()
                    
                    ticket_id = ticket_res.data[0]['id']
                    supabase.table("ticket_messages").insert({
                        "ticket_id": ticket_id,
                        "sender_type": "user",
                        "content": body
                    }).execute()
                    
                    mail.store(num, '+FLAGS', '\\Seen')
        return "Sync Complete"
    except Exception as e:
        print(f"Error: {e}")
        raise e
    finally:
        if mail:
            mail.logout()