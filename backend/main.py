from fastapi import FastAPI
from pydantic import BaseModel
from backend.database import supabase
from backend.services.ai_service import get_answer_from_kb

# Initialize FastAPI
app = FastAPI(title="SPS SecureDesk AI API")

# Define the request model
class QueryRequest(BaseModel):
    query: str

# 1. Root Health Check
@app.get("/")
def read_root():
    return {"message": "SPS SecureDesk AI is connected and running!"}

# 2. Test DB Connection
@app.get("/test-db")
def test_db():
    try:
        response = supabase.table("kb_articles").select("*").limit(1).execute()
        return {"status": "Database connected!", "data": response.data}
    except Exception as e:
        return {"status": "Database error", "error": str(e)}

# 3. Chat with AI
@app.post("/chat")
def chat_with_kb(request: QueryRequest):
    try:
        answer = get_answer_from_kb(request.query)
        return {"query": request.query, "response": answer}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)