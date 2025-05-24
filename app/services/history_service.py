# app/services/history_service.py
from app.models.orm import LLMHistory
from app.db.database import get_session
from typing import List, Optional

async def add_history(model: str, prompt: str, response: str, user_id: Optional[str] = None, params: Optional[dict] = None, duration_ms: Optional[int] = None):
    from datetime import datetime
    import json
    params_str = json.dumps(params) if params else None
    record = LLMHistory(
        model=model, prompt=prompt, response=response,
        user_id=user_id, duration_ms=duration_ms,
        params=params_str, timestamp=datetime.utcnow()
    )
    async with get_session() as session:
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

async def get_history(limit=20, offset=0, model=None, user_id=None) -> List[LLMHistory]:
    from sqlmodel import select
    async with get_session() as session:
        stmt = select(LLMHistory)
        if model:
            stmt = stmt.where(LLMHistory.model == model)
        if user_id:
            stmt = stmt.where(LLMHistory.user_id == user_id)
        stmt = stmt.order_by(LLMHistory.timestamp.desc()).offset(offset).limit(limit)
        result = await session.exec(stmt)
        return result.all()
