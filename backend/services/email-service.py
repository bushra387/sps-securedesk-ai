import imaplib
import email
from email.header import decode_header
from backend.database import supabase

def fetch_and_process_emails():
    # 1. Connect to your mail server (e.g., Gmail)
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login("your-email@gmail.com", "your-app-password")
    mail.select("inbox")

    # 2. Search for unread emails
    status, messages = mail.search(None, 'UNSEEN')
    
    for num in messages[0].split():
        res, msg_data = mail.fetch(num, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes): subject = subject.decode()
                
                # 3. Insert into Supabase (The same table as Web Form!)
                supabase.table("tickets").insert({
                    "subject": subject,
                    "requester_email": msg.get("From"),
                    "status": "New",
                    "source": "email"
                }).execute()
    
    mail.logout()