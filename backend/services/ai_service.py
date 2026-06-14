import uuid
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.database import supabase
from backend.config import settings

# Initialize the Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=settings.GEMINI_API_KEY
)

# 1. RAG SERVICE: Retrieve and Answer
def get_answer_from_kb(query: str):
    # Use RPC for efficient searching
    response = supabase.rpc("search_kb", {"query_text": query}).execute()
    
    # Extract content if results exist
    if not response.data:
        context_text = "No specific SPS internal policy found."
    else:
        context_text = "\n\n".join([f"Title: {item['title']}\nContent: {item['content']}" for item in response.data])
    
    # Enhanced Prompt
    prompt = f"""
    You are SPS SecureDesk AI, a professional enterprise helpdesk assistant for Software Productivity Strategists (SPS).
    
    INSTRUCTIONS:
    - Base your answers primarily on the KNOWLEDGE BASE provided below.
    - If the answer is in the KNOWLEDGE BASE, provide a clear, professional answer.
    - If the user asks about SPS internal procedures and the information is NOT in the knowledge base, 
      politely state: "I don't have that specific internal information available. Would you like me to create a Support Request for you?"
    - For GENERAL technology questions, use your general knowledge.
    - IMPORTANT: Always refer to issues as "Support Requests". Never use the word "ticket" in your chat responses to the user.
    - Tone: Professional, helpful, enterprise-ready.

    KNOWLEDGE BASE:
    {context_text}
    
    USER QUESTION: {query}
    """
    
    ai_response = llm.invoke(prompt)
    return ai_response.content

# 2. ESCALATION SERVICE: Convert Chat to Support Request
def create_support_request(requester_email: str, title: str, description: str):
    """
    Creates a new entry in the 'tickets' table.
    """
    # 1. Generate a unique ID (Reference Number)
    year = datetime.now().year
    random_suffix = str(uuid.uuid4())[:6].upper()
    reference_id = f"SPS-{year}-{random_suffix}"
    
    # 2. Insert into the database
    # FIX: Changed "title" to "subject" to match your DB column
    ticket_data = {
        "id": reference_id,
        "source": "chat",
        "requester_email": requester_email,
        "subject": title, 
        "status": "Open",
        "priority": "Medium"
    }
    
    ticket_response = supabase.table("tickets").insert(ticket_data).execute()
    
    # 3. Add to the timeline
    if ticket_response.data:
        timeline_data = {
            "ticket_id": reference_id,
            "sender_type": "system",
            "content": f"Support Request created via AI Chat. Summary: {description}"
        }
        supabase.table("ticket_messages").insert(timeline_data).execute()
        
    return reference_id
    # backend/services/ai_service.py

def classify_ticket(subject: str, description: str) -> str:
    """
    Simulates AI classification. 
    In a real app, send this to an LLM (OpenAI/Gemini/Local model).
    """
    content = f"Subject: {subject}. Description: {description}"
    
    # Simple keyword-based logic (Replace with API call to LLM for production)
    content_lower = content.lower()
    if "laptop" in content_lower or "screen" in content_lower or "keyboard" in content_lower:
        return "Hardware"
    elif "password" in content_lower or "login" in content_lower or "install" in content_lower:
        return "Software"
    elif "wifi" in content_lower or "internet" in content_lower:
        return "Network"
    else:
        return "General"