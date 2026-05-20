from fastapi import APIRouter
from ..schemas import SubmitRequest
from ..db import declarations_collection
import uuid
import datetime


router = APIRouter()


@router.post("/submit")
def submit_declaration(payload: SubmitRequest):

    record = payload.model_dump()

    record["record_id"] = str(uuid.uuid4())

    record["created_at"] = datetime.datetime.utcnow().isoformat()

    declarations_collection.insert_one(record)

    record.pop("_id", None)

    return record