from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.database import supabase
from backend.services.ai_service import get_answer_from_kb
import uuid
from datetime import datetime

from backend.services.email_service import send_ticket_confirmation

@app.post("/tickets")
def create_ticket(ticket: TicketCreate):
    try:
        new_ticket_id = f"SPS-{datetime.now().year}-{str(uuid.uuid4())[:4].upper()}"
        
        # 1. Create Ticket
        supabase.table("tickets").insert({
            "id": new_ticket_id,
            "subject": ticket.subject,
            "requester_email": ticket.requester_email,
            "category": ticket.category,
            "source": ticket.source,
            "status": "Open",
            "priority": ticket.priority 
        }).execute()
        
        # 2. Add Message
        supabase.table("ticket_messages").insert({
            "ticket_id": new_ticket_id,
            "sender_type": "user",
            "content": ticket.description
        }).execute()

        # 3. Trigger Email Notification
        send_ticket_confirmation(ticket.requester_email, new_ticket_id, ticket.subject)
        
        return {"ticket_id": new_ticket_id, "message": "Ticket created and notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app = FastAPI(title="SPS SecureDesk AI API")

# --- Models ---
class QueryRequest(BaseModel):
    query: str

class TicketCreate(BaseModel):
    subject: str
    description: str
    requester_email: str
    category: str
    source: str 
    priority: str  # ADDED: Priority field

class MessageAdd(BaseModel):
    ticket_id: str 
    sender_type: str 
    content: str

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "SPS SecureDesk AI is live"}

@app.post("/chat")
def chat_with_kb(request: QueryRequest):
    try:
        answer = get_answer_from_kb(request.query)
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tickets")
def create_ticket(ticket: TicketCreate):
    # 1. AI Classification
    # We ignore the user's manual category and let AI decide (or use AI to validate)
    ai_category = classify_ticket(ticket.subject, ticket.description)
    
    try:
        new_ticket_id = f"SPS-{datetime.now().year}-{str(uuid.uuid4())[:4].upper()}"
        
        supabase.table("tickets").insert({
            "id": new_ticket_id,
            "subject": ticket.subject,
            "requester_email": ticket.requester_email,
            "category": ai_category, # Use AI category
            "source": ticket.source,
            "status": "Open",
            "priority": ticket.priority
        }).execute()
        
        # 2. Add the initial description
        supabase.table("ticket_messages").insert({
            "ticket_id": new_ticket_id,
            "sender_type": "user",
            "content": ticket.description
        }).execute()
        
        return {"ticket_id": new_ticket_id, "message": "Ticket created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tickets/all")
def get_all_tickets():
    try:
        response = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    try:
        ticket = supabase.table("tickets").select("*").eq("id", ticket_id).single().execute()
        messages = supabase.table("ticket_messages").select("*").eq("ticket_id", ticket_id).order("created_at").execute()
        
        return {
            "ticket": ticket.data,
            "timeline": messages.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tickets/message")
def add_message(msg: MessageAdd):
    try:
        supabase.table("ticket_messages").insert({
            "ticket_id": msg.ticket_id,
            "sender_type": msg.sender_type,
            "content": msg.content
        }).execute()
        return {"status": "Message added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# In your API endpoint that updates ticket status
def update_ticket_status(ticket_id: str, new_status: str):
    # 1. Update Database
    supabase.table("tickets").update({"status": new_status}).eq("id", ticket_id).execute()
    
    # 2. Notify User via Email
    requester = get_requester_email(ticket_id) # Helper to fetch email
    send_email(requester, f"Ticket {ticket_id} is now {new_status}")        