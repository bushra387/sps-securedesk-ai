from langchain_openai import ChatOpenAI
from backend.database import supabase
from backend.config import settings

# Initialize the LLM (Ensure you have OPENAI_API_KEY in your .env)
llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)
def get_answer_from_kb(query: str):
    # 1. REMOVED .ilike to fetch all data so the AI can process it
    response = supabase.table("kb_articles").select("title, content").execute()
    
    # 2. Extract content from all articles
    # This ensures the AI sees the title and the content to make sense of it
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
    ai_response = llm.invoke(prompt)
    return ai_response.content
