from fastapi import APIRouter
from ..schemas import AskRequest
from ..services.rag import search_documents
from ..services.llm import generate_text
import re

router = APIRouter()


def strip_markdown(text: str) -> str:
    """Remove markdown formatting characters from LLM output to return clean plain text."""
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[Source:.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

@router.post("/ask")
def ask_question(payload: AskRequest):
    docs = search_documents(payload.question)

    if not docs:
        return {
            "answer": "I do not know based on the provided documents",
            "sources": []
        }

    formatted_contexts = []
    for doc in docs:
        formatted_contexts.append(doc.get('text'))

    context = "\n\n---\n\n".join(formatted_contexts)

    prompt = f"""
You are an expert EPR (Extended Producer Responsibility) Compliance AI Assistant for GreenPack Industries.
Your task is to answer the compliance officer's question using ONLY the provided document context below.

Context:
{context}

Question:
{payload.question}

Guidelines:
1. Answer the question comprehensively, accurately, and professionally based ONLY on the provided context.
2. Do not use outside knowledge or assume/hallucinate any facts.
3. If the answer cannot be found in the provided context, you MUST reply with exactly:
"I do not know based on the provided documents"
4. Keep your answer professional, objective, and directly supported by the context.
"""

    answer = generate_text(prompt).strip()
    answer = strip_markdown(answer)

    dont_know_phrases = [
        "i do not know", 
        "i don't know", 
        "not provided in the context", 
        "not mentioned in the context",
        "provided documents do not contain",
        "cannot answer",
        "cannot be answered",
        "does not provide",
        "not provide any information",
        "no information",
        "is not mentioned",
        "does not mention",
        "does not contain",
        "no mention of",
        "not contain information"
    ]
    
    if any(phrase in answer.lower() for phrase in dont_know_phrases):
        return {
            "answer": "I do not know based on the provided documents"
        }

    return {
        "answer": answer
    }