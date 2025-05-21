# app/api/history.py
from fastapi import APIRouter, Query
from models.orm import RAGHistory
from db.database import get_session
import json

router = APIRouter()

@router.get("/llm_history", tags=["history"])
async def get_llm_history(user_id: str = None, limit: int = 20):
    """
    История LLM/RAG-запросов для UI или аудита.
    """
    from sqlmodel import select
    async with get_session() as session:
        query = select(RAGHistory).order_by(RAGHistory.created_at.desc()).limit(limit)
        if user_id:
            query = query.where(RAGHistory.user_id == user_id)
        res = await session.exec(query)
        items = res.all()
        return [
            {
                "id": h.id,
                "user_id": h.user_id,
                "model": h.model,
                "question": h.question,
                "context_docs": json.loads(h.context_docs_json),
                "answer": h.answer,
                "created_at": h.created_at.isoformat()
            }
            for h in items
        ]
