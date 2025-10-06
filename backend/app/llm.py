# app/llm.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def chat_with_groq(prompt: str, emotion: str = "neutral") -> str:
    """Send prompt with emotion context to Groq LLM"""
    system_prompt = f"You are an AI tutor. Respond in a {emotion} tone."

    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content
