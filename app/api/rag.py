import json
from fastapi import APIRouter, Request
from torch import select
from db.database import get_session
from models.orm import RAGHistory
from scripts.text_processing import extract_jenkinsfile_block
from services.retriever_service import retriever_service
from services.rag_history_service import rag_history_service
from rag.template import format_context_block, get_prompt_template, truncate_prompt
from services.llm_service import llm_service
from core.logging import get_logger
from models.schemas import RAGRequest, RAGResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("/rag_generate", response_model=RAGResponse, tags=["llm"])
async def rag_generate(req: RAGRequest, request: Request):
    docs = retriever_service.query(req.question, top_k=req.top_k)
    context_block = format_context_block(docs, max_length=2048)
    prompt_template = get_prompt_template(req.model)
    prompt = prompt_template.format(
        context_block=context_block,
        question=req.question
    )
    runner = llm_service.get_runner(req.model)
    if hasattr(runner, "tokenizer"):
        prompt = truncate_prompt(prompt, runner.tokenizer, max_tokens=2048)

    result = await llm_service.generate(
        model=req.model,
        prompt=prompt,
        params=req.params or {},
        user_id=req.user_id
    )
    # Логируем историю
    await rag_history_service.log(
        user_id=req.user_id, model=req.model, question=req.question,
        context_docs=docs, answer=result
    )
    result_text = extract_jenkinsfile_block(result)
    return RAGResponse(answer=result, context_docs=docs)


@router.get("/rag_history", tags=["llm"])
async def get_rag_history(user_id: str = None, limit: int = 10):
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
