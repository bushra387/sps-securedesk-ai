import sys
import os
from pathlib import Path
import imaplib
import email
from email.header import decode_header

# Ensure backend can be imported
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
        print("DEBUG: Connecting to Gmail...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        mail.select("inbox")

        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK' or not messages[0]:
            return "No new emails"

        # LIMIT TO LAST 5 EMAILS to prevent hanging
        email_ids = messages[0].split()
        recent_ids = email_ids[-5:] 
        print(f"DEBUG: Found {len(email_ids)} unread, processing last {len(recent_ids)}...")

        for num in recent_ids:
            print(f"DEBUG: Fetching email {num.decode()}...")
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
                                break # Stop after finding the first text body
                    else:
                        body = msg.get_payload(decode=True).decode(errors='ignore')

                    print(f"DEBUG: Inserting ticket for: {subject}")
                    ticket_res = supabase.table("tickets").insert({
                        "subject": subject,
                        "requester_email": msg.get("From"),
                        "status": "New",
                        "source": "email",
                        "category": "General IT"
                    }).execute()
                    
                    ticket_id = ticket_res.data[0]['id']
                    print(f"DEBUG: Inserting message for ticket {ticket_id}")
                    supabase.table("ticket_messages").insert({
                        "ticket_id": ticket_id,
                        "sender_type": "user",
                        "content": body
                    }).execute()
                    
                    # Mark as seen so we don't process it again next time
                    mail.store(num, '+FLAGS', '\\Seen')
                    print(f"DEBUG: Successfully processed email {num.decode()}")
                    
        return "Sync Complete"
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        raise e
    finally:
        if mail:
            mail.logout()
            print("DEBUG: Logged out.")