from langchain_google_genai import ChatGoogleGenerativeAI
from backend.database import supabase
from backend.config import settings

# Initialize the Gemini LLM
# Ensure GEMINI_API_KEY is in your .env and settings
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=settings.GEMINI_API_KEY
)

def get_answer_from_kb(query: str):
    # 1. Fetch data from Supabase
    response = supabase.table("kb_articles").select("title, content").execute()
    
    # 2. Extract content
    context_text = "\n\n".join([f"Title: {item['title']}\nContent: {item['content']}" for item in response.data])
    
    if not response.data:
        return "I'm sorry, I couldn't find any articles in the database."

    # 3. Create the prompt
    prompt = f"""
    You are a helpful assistant for SPS SecureDesk. 
    Use the following knowledge base articles to answer the user's question accurately.
    If the answer isn't in the articles, just say you don't know.

    KNOWLEDGE BASE:
    {context_text}
    
    USER QUESTION: {query}
    """
    
    # 4. Get AI response
    # LangChain's invoke() works exactly the same for Gemini
    ai_response = llm.invoke(prompt)
    return ai_response.content