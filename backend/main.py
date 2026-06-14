from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from backend.database import supabase
from backend.services.ai_service import get_answer_from_kb, classify_ticket
from backend.services.email_service import send_confirmation, send_agent_reply
from backend.utils.security import sanitize_and_log
import uuid
from datetime import datetime

app = FastAPI(title="SPS SecureDesk AI API")

# FIX: Allow Frontend to communicate with Backend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class QueryRequest(BaseModel):
    query: str

class TicketCreate(BaseModel):
    subject: str
    description: str
    requester_email: str
    source: str 
    priority: str

class MessageAdd(BaseModel):
    ticket_id: str 
    sender_type: str 
    content: str
    is_public: bool = True

class StatusUpdate(BaseModel):
    new_status: str

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
    clean_desc = sanitize_and_log(ticket.description, "web_form")
    ai_category = classify_ticket(ticket.subject, clean_desc)
    try:
        new_ticket_id = f"SPS-{datetime.now().year}-{str(uuid.uuid4())[:4].upper()}"
        supabase.table("tickets").insert({
            "id": new_ticket_id,
            "subject": ticket.subject,
            "requester_email": ticket.requester_email,
            "category": ai_category,
            "source": ticket.source,
            "status": "Open",
            "priority": ticket.priority
        }).execute()
        supabase.table("ticket_messages").insert({
            "ticket_id": new_ticket_id,
            "sender_type": "user",
            "content": clean_desc
        }).execute()
        send_confirmation(ticket.requester_email, new_ticket_id, ticket.subject)
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
        return {"ticket": ticket.data, "timeline": messages.data}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Ticket not found")

@app.post("/tickets/message")
def add_message(msg: MessageAdd):
    try:
        clean_content = sanitize_and_log(msg.content, "web_form")
        supabase.table("ticket_messages").insert({
            "ticket_id": msg.ticket_id,
            "sender_type": msg.sender_type,
            "content": clean_content
        }).execute()
        if msg.sender_type == "agent" and msg.is_public:
            ticket = supabase.table("tickets").select("requester_email").eq("id", msg.ticket_id).single().execute()
            send_agent_reply(ticket.data['requester_email'], msg.ticket_id, clean_content)
        return {"status": "Message added and logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/tickets/{ticket_id}/status")
def update_status(ticket_id: str, status_data: StatusUpdate):
    try:
        supabase.table("tickets").update({"status": status_data.new_status}).eq("id", ticket_id).execute()
        ticket = supabase.table("tickets").select("requester_email").eq("id", ticket_id).single().execute()
        send_agent_reply(ticket.data['requester_email'], ticket_id, f"The status of your ticket has been updated to: {status_data.new_status}")
        return {"message": "Status updated and user notified"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Launch command
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)