from langchain_openai import ChatOpenAI
from backend.main import supabase  # Importing your existing client

# Initialize the LLM (Ensure you have OPENAI_API_KEY in your .env)
llm = ChatOpenAI(model="gpt-4o-mini", api_key="OPENAI_API_KEY")

def get_answer_from_kb(query: str):
    # 1. Search database for relevant articles (Simple keyword search for now)
    response = supabase.table("kb_articles").select("content").ilike("content", f"%{query}%").limit(3).execute()
    
    # 2. Extract content from search results
    context_text = "\n".join([item['content'] for item in response.data])
    
    if not context_text:
        return "I'm sorry, I couldn't find any relevant articles in the knowledge base."

    # 3. Create a prompt for the AI
    prompt = f"""
    You are a helpful assistant for SPS SecureDesk. 
    Use the following knowledge base articles to answer the user's question:
    
    {context_text}
    
    User Question: {query}
    """
    
    # 4. Get AI response
    ai_response = llm.invoke(prompt)
    return ai_response.content