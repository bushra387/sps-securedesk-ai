import sys
import os
import uuid
import re
import smtplib
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr
from datetime import datetime
from backend.database import supabase
from backend.utils.security import sanitize_and_log

# --- OUTBOUND EMAIL FUNCTIONS ---

def send_confirmation(to_email, ticket_id, subject):
    """Sends an automated confirmation email to the user."""
    smtp_user = os.getenv("EMAIL_USER")
    smtp_pass = os.getenv("EMAIL_PASS")
    
    if not smtp_user or not smtp_pass:
        print("SMTP Credentials missing.")
        return

    msg = MIMEMultipart()
    msg['From'] = f"SPS SecureDeskAI <{smtp_user}>"
    msg['To'] = to_email
    msg['Subject'] = f"SPS SecureDesk: Ticket {ticket_id} Received"
    
    body = f"""
    <h3>Your request has been received</h3>
    <p>We have successfully created a ticket for your inquiry.</p>
    <p><strong>Ticket ID:</strong> {ticket_id}</p>
    <p><strong>Subject:</strong> {subject}</p>
    <p>Our support team will get back to you shortly.</p>
    """
    msg.attach(MIMEText(body, 'html'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        print(f"Confirmation sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email confirmation: {e}")

def send_agent_reply(to_email, ticket_id, reply_content):
    """Sends an agent's response to the requester."""
    smtp_user = os.getenv("EMAIL_USER")
    smtp_pass = os.getenv("EMAIL_PASS")
    
    if not smtp_user or not smtp_pass:
        print("SMTP Credentials missing.")
        return

    msg = MIMEMultipart()
    msg['From'] = f"SPS SecureDeskAI <{smtp_user}>"
    msg['To'] = to_email
    msg['Subject'] = f"Re: [{ticket_id}] Support Update"
    
    body = f"""
    <p>Hello,</p>
    <p>An agent has updated your support ticket:</p>
    <div style="background-color: #f9f9f9; padding: 10px; border-left: 3px solid #002060;">
        {reply_content}
    </div>
    <p>Thank you for using SPS SecureDesk.</p>
    """
    msg.attach(MIMEText(body, 'html'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        print(f"Agent reply sent to {to_email} for ticket {ticket_id}")
    except Exception as e:
        print(f"Failed to send agent reply: {e}")

# --- INBOUND EMAIL PROCESSOR ---

def process_inbound_emails():
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")

    mail = None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        mail.select('"[Gmail]/All Mail"')

        status, messages = mail.search(None, 'UNSEEN')
        
        if status != 'OK' or not messages[0]:
            return "No new emails"

        for num in messages[0].split():
            _, msg_data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            
            # Extract Subject
            subject_raw = decode_header(msg["Subject"])[0][0]
            subject = subject_raw.decode() if isinstance(subject_raw, bytes) else str(subject_raw)
            
            # Extract Sender Email
            _, sender_email = parseaddr(msg.get("From"))
            
            # Extract Body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors='ignore')

            # SANITIZATION & LOGGING
            clean_body = sanitize_and_log(body, "email_inbound")

            # Logic: Check if this is a reply to an existing ticket
            match = re.search(r"\[(SPS-\d{4}-[A-Z0-9]+)\]", subject)
            
            if match:
                ticket_id_ref = match.group(1)
                supabase.table("ticket_messages").insert({
                    "ticket_id": ticket_id_ref,
                    "sender_type": "user",
                    "content": f"Email reply: {clean_body}"
                }).execute()
            else:
                # NEW TICKET CREATION
                new_ticket_id = f"SPS-{datetime.now().year}-{str(uuid.uuid4())[:4].upper()}"
                
                supabase.table("tickets").insert({
                    "id": new_ticket_id,
                    "subject": subject,
                    "requester_email": sender_email,
                    "status": "Open",
                    "source": "email",
                    "priority": "Medium"
                }).execute()
                
                supabase.table("ticket_messages").insert({
                    "ticket_id": new_ticket_id,
                    "sender_type": "system",
                    "content": f"Ticket created from email: {clean_body}"
                }).execute()
                
                # TRIGGER CONFIRMATION
                send_confirmation(sender_email, new_ticket_id, subject)
            
            mail.store(num, '+FLAGS', '\\Seen')
            
        return "Sync Complete"
    finally:
        if mail: mail.logout()