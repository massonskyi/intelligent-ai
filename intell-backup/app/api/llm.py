# app/api/llm.py
import asyncio
from fastapi.responses import StreamingResponse
from models.schemas import GenerateRequest, GenerateResponse
from models.schemas import (
    BatchGenerateRequest,
    BatchGenerateResponse,
    BatchGenerateResponseItem,
)

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.llm_service import llm_service
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/generate", response_model=GenerateResponse, tags=["llm"])
async def generate_pipeline(req: GenerateRequest, request: Request):
    """
    Генерация пайплайна или любого текста через выбранную модель.
    """
    logger.info(f"Запрос генерации: model={req.model}, user={req.user_id}")
    try:
        # Передаём все параметры в сервис (он дальше сам роутит к раннеру)
        result = await llm_service.generate(
            model=req.model,
            prompt=req.prompt,
            params={
                **(req.params or {}),
                "temperature": req.temperature,
                "top_p": req.top_p,
                "max_new_tokens": req.max_new_tokens,
            },
            user_id=req.user_id
        )
        # result может быть либо строкой, либо dict c деталями (если runner поддерживает)
        if isinstance(result, dict):
            text = result.get("text") or result.get("result")
            usage = result.get("usage", None)
        else:
            text = result
            usage = None
        # Можно вернуть id из истории, если нужно
        return GenerateResponse(
            model=req.model,
            prompt=req.prompt,
            result=text,
            usage=usage
        )
    except Exception as e:
        logger.exception("Ошибка генерации")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {e}")

@router.post("/batch_generate", response_model=BatchGenerateResponse, tags=["llm"])
async def batch_generate(req: BatchGenerateRequest, request: Request):
    """
    Параллельная генерация по массиву запросов.
    """
    logger.info(f"Batch generation: {len(req.requests)} запрос(ов)")
    tasks = []
    for item in req.requests:
        # Формируем таск для каждого запроса
        params = dict(item.params or {})
        if item.temperature is not None:
            params["temperature"] = item.temperature
        if item.top_p is not None:
            params["top_p"] = item.top_p
        if item.max_new_tokens is not None:
            params["max_new_tokens"] = item.max_new_tokens
        # Корректный порядок возвращается всегда
        tasks.append(
            llm_service.generate(
                model=item.model,
                prompt=item.prompt,
                params=params,
                user_id=item.user_id
            )
        )
    # Выполняем всё параллельно
    results = await asyncio.gather(*tasks, return_exceptions=True)
    response_items = []
    for item, result in zip(req.requests, results):
        if isinstance(result, Exception):
            response_items.append(BatchGenerateResponseItem(
                model=item.model,
                prompt=item.prompt,
                result="",
                error=str(result)
            ))
        elif isinstance(result, dict):
            response_items.append(BatchGenerateResponseItem(
                model=item.model,
                prompt=item.prompt,
                result=result.get("text") or result.get("result") or "",
                usage=result.get("usage"),
            ))
        else:
            response_items.append(BatchGenerateResponseItem(
                model=item.model,
                prompt=item.prompt,
                result=str(result)
            ))
    return BatchGenerateResponse(results=response_items)

@router.post("/stream_generate", response_class=StreamingResponse, tags=["llm"])
async def stream_generate(req: GenerateRequest, request: Request):
    """
    Стриминговая генерация — отдаёт ответ по мере генерации токенов.
    """
    # Выбор раннера
    runner = llm_service.get_runner(req.model)
    # Обработаем параметры
    gen_kwargs = dict(req.params or {})
    if req.temperature is not None:
        gen_kwargs["temperature"] = req.temperature
    if req.top_p is not None:
        gen_kwargs["top_p"] = req.top_p
    if req.max_new_tokens is not None:
        gen_kwargs["max_new_tokens"] = req.max_new_tokens

    async def event_stream():
        try:
            async for chunk in runner.generate_stream(req.prompt, **gen_kwargs):
                # Форматируем как SSE (text/event-stream) — либо просто text-plain
                # Можно JSON-оборачивать для совместимости с фронтом
                yield chunk
        except Exception as e:
            logger.exception("Ошибка stream генерации")
            yield f"\n[ERROR]: {str(e)}"

    return StreamingResponse(event_stream(), media_type="text/plain")  # или "text/event-stream"