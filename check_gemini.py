import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. Load environment variables
load_dotenv()

# 2. Initialize Gemini
# We use the key from your .env file
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    # 3. Simple Test
    print("Testing connection to Gemini...")
    response = llm.invoke("Hello, Gemini! Are you working?")
    
    print("\n✅ SUCCESS! Gemini responded:")
    print(response.content)

except Exception as e:
    print("\n❌ ERROR: Connection failed.")
    print(f"Details: {e}")