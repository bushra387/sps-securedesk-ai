from langchain_openai import ChatOpenAI
from backend.config import settings

def get_ai_response(prompt: str):
    llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY)
    response = llm.invoke(prompt)
    return response.content