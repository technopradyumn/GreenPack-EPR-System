from fastapi import APIRouter, HTTPException
from ..db import declarations_collection
from ..services.reconciliation import reconcile
from ..services.llm import generate_text
import pandas as pd
import os
import re

router = APIRouter()


def strip_markdown(text: str) -> str:
    """Remove markdown formatting characters from LLM output to return clean plain text."""
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)

    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)

    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

@router.get("/summary/{producer_id}/{month}")
def get_summary(producer_id: str, month: str):
    declaration = declarations_collection.find_one({
        "producer_id": producer_id,
        "month": month
    })

    if not declaration:
        raise HTTPException(
            status_code=404,
            detail="Data is not declared by company"
        )

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(BASE_DIR, "data", "erp_feed.csv")

    filtered_erp = pd.DataFrame()

    if os.path.exists(csv_path):
        erp_df = pd.read_csv(csv_path)
        filtered_erp = erp_df[
            (erp_df["producer_id"] == producer_id) &
            (erp_df["month"] == month)
        ]

    if filtered_erp.empty:
        from ..db import db as mongo_db
        erp_collection = mongo_db["erp_data"]
        erp_records = list(erp_collection.find({"producer_id": producer_id, "month": month}, {"_id": 0}))
        if erp_records:
            filtered_erp = pd.DataFrame(erp_records)

    if filtered_erp.empty:
        raise HTTPException(
            status_code=404,
            detail="Data is not available on ERP"
        )

    reconciliation_result = reconcile(
        declaration.get("declared_quantities_kg", {}),
        filtered_erp
    )

    prompt = f"""
You are an expert EPR (Extended Producer Responsibility) compliance advisor for GreenPack Industries.
Your task is to write a highly professional, 3-5 sentence compliance summary based on the following reconciliation data.

Data:
{reconciliation_result}

In your response:
1. State the overall compliance status.
2. Explicitly mention any categories that are flagged for exceeding the 5% mismatch threshold.
3. Recommend a concrete corrective action (e.g., audit procurement logs, adjust next month's declaration, or file a correction report).

This is a structured generation task. Focus on a clear narrative, keep your tone objective, and be direct. Do not add general greetings or conversational filler.
"""

    summary = generate_text(prompt)
    summary = strip_markdown(summary)

    return {
        "reconciliation": reconciliation_result,
        "summary": summary
    }