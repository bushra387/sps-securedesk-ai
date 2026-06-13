from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.database import supabase
from backend.services.ai_service import get_answer_from_kb

app = FastAPI(title="SPS SecureDesk AI API")

# --- Models ---
class QueryRequest(BaseModel):
    query: str

class TicketCreate(BaseModel):
    subject: str
    description: str
    requester_email: str
    category: str
    source: str  # "email", "portal_form", "chat"

class MessageAdd(BaseModel):
    ticket_id: int
    sender_type: str  # "user", "agent"
    content: str

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "SPS SecureDesk AI is live"}

# 1. Unified Chat Endpoint (The Chat Channel)
@app.post("/chat")
def chat_with_kb(request: QueryRequest):
    try:
        answer = get_answer_from_kb(request.query)
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Ticket Creation Endpoint (The Web Form & Escalation Channel)
@app.post("/tickets")
def create_ticket(ticket: TicketCreate):
    try:
        # 1. Create the Ticket
        ticket_res = supabase.table("tickets").insert({
            "subject": ticket.subject,
            "requester_email": ticket.requester_email,
            "category": ticket.category,
            "source": ticket.source,
            "status": "New"
        }).execute()
        
        ticket_id = ticket_res.data[0]['id']
        
        # 2. Add the initial description as the first message
        supabase.table("ticket_messages").insert({
            "ticket_id": ticket_id,
            "sender_type": "user",
            "content": ticket.description
        }).execute()
        
        return {"ticket_id": ticket_id, "message": "Ticket created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Get Ticket & Timeline (For Portal/Agent View)
# --- Unified Ticket Management ---

@app.get("/tickets/all")
def get_all_tickets():
    """Fetches all tickets for the Agent Dashboard."""
    try:
        response = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    """Fetches full ticket details and message history (The Timeline)."""
    try:
        # Fetch ticket details
        ticket = supabase.table("tickets").select("*").eq("id", ticket_id).single().execute()
        # Fetch all messages for this ticket
        messages = supabase.table("ticket_messages").select("*").eq("ticket_id", ticket_id).order("created_at").execute()
        
        return {
            "ticket": ticket.data,
            "timeline": messages.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# 4. Add Message (Reply from Agent or User)
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