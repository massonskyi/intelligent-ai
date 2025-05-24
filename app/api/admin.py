# app/api/admin.py
from fastapi import APIRouter, HTTPException, Body
from services.retriever_service import retriever_service
from core.config import config_store

router = APIRouter()

@router.post("/import_docs", tags=["admin"])
async def import_docs(docs: list = Body(...)):
    """
    Импорт новых документов в базу знаний (ChromaDB).
    docs: [{id, text, metadata}]
    """
    if not docs:
        raise HTTPException(status_code=400, detail="Docs are required")
    retriever_service.add_docs(docs)
    return {"status": "imported", "count": len(docs)}

@router.get("/docs", tags=["admin"])
async def list_docs(limit: int = 20, offset: int = 0):
    """
    Получить список документов из базы знаний.
    """
    return retriever_service.list_docs(limit=limit, offset=offset)

@router.get("/model_configs", tags=["admin"])
async def get_model_configs():
    """
    Получить текущие конфиги моделей (для UI/отладки).
    """
    return {name: cfg.dict() for name, cfg in config_store.get_all_model_configs().items()}

@router.post("/set_model_param", tags=["admin"])
async def set_model_param(path: str, value):
    """
    Изменить параметр модели на лету (например, temperature для deepseek).
    path: "models.deepseek.temperature"
    """
    config_store.set(path, value)
    return {"status": "updated", "path": path, "value": value}

@router.post("/set_default_model")
async def set_default_model(model: str):
    config_store.set_default_model(model)
    return {"status": "ok", "default_model": model}

@router.get("/app_config")
async def get_app_config():
    return config_store.get_app_config().dict()

@router.post("/set_app_config")
async def set_app_config(payload: dict):
    for k, v in payload.items():
        setattr(config_store.app_config, k, v)
    config_store.reload_app_config()
    return {"ok": True}
