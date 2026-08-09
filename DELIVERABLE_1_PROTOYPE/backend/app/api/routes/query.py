# app/api/routes/query.py — FULL FILE (copy-paste karo)
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

from app.db.connection import get_db
from app.ai.query_translator import QueryTranslator

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    hadm_id: Optional[int] = None
    subject_id: Optional[int] = None

class QueryResponse(BaseModel):
    answer: Optional[str] = None
    query: dict = {}
    supporting_rows: int = 0
    evidence: list[dict] = []
    refused: bool = True
    error: Optional[str] = None

@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    translator = QueryTranslator(db)
    result = await translator.ask(
        question=request.question,
        hadm_id=request.hadm_id,
        subject_id=request.subject_id,
    )
    return QueryResponse(**result)