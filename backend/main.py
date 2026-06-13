import os
from fastapi import FastAPI
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import BaseModel

# 1. Load variables and create client
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Create a global supabase client
supabase: Client = create_client(url, key)

# 2. Initialize FastAPI
app = FastAPI(title="SPS SecureDesk AI API")

# 3. Simple health check
@app.get("/")
def read_root():
    return {"message": "SPS SecureDesk AI is connected and running!"}

# 4. Test endpoint to verify DB access
@app.get("/test-db")
def test_db():
    try:
        # Simple query to list tables or get a record
        # Replace 'your_table_name' with an actual table name in your Supabase
        response = supabase.table("kb_articles").select("*").limit(1).execute()
        return {"status": "Database connected!", "data": response.data}
    except Exception as e:
        return {"status": "Database error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)