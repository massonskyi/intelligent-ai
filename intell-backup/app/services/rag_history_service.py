import json
from db.database import get_session
from models.orm import RAGHistory

class RAGHistoryService:
    async def log(self, *, user_id, model, question, context_docs, answer):
        async with get_session() as session:
            entry = RAGHistory(
                user_id=user_id,
                model=model,
                question=question,
                context_docs_json=json.dumps(context_docs),
                answer=answer,
            )
            session.add(entry)
            await session.commit()
rag_history_service = RAGHistoryService()
