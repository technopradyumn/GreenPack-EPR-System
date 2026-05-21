from google import genai
from ..config import settings


def generate_text(prompt: str):
    if not settings.GEMINI_API_KEY:
        return "LLM Service Unavailable: GEMINI_API_KEY is not set in .env"
    
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"LLM Service Unavailable: {str(e)}"