# llm/gemini_client.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def ask_gemini(context, query):
    """
    Sends context + query to Gemini API and returns the answer text.
    """
    prompt = f"""
    You are a helpful assistant. Use the context below to answer the query.
    Context:
    {context}

    Query: {query}
    Answer:
    """
    response = model.generate_content(prompt)
    return response.text
