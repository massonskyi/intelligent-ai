# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

# ===== 1. Для конфигов моделей =====

class ModelParams(BaseModel):
    # Гибко, чтобы не ограничивать конкретным набором, но можно добавить кастомные поля
    n_ctx: Optional[int] = None
    n_threads: Optional[int] = None
    n_gpu_layers: Optional[int] = None
    device: Optional[str] = None
    max_new_tokens: Optional[int] = None
    torch_dtype: Optional[str] = None
    
class LLMModelConfigSchema(BaseModel):
    name: str
    type: str = Field(..., description="llama_cpp | transformers | ...")
    model_path: str
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    temperature: float = 0.7
    top_p: float = 0.95
    
    

class LLMModelConfigUpdateSchema(BaseModel):
    # Для PATCH-запросов (обновить только часть параметров)
    temperature: Optional[float]
    top_p: Optional[float]
    params: Optional[Dict[str, Any]]
    
# ===== 2. Для истории =====

class LLMHistoryRecord(BaseModel):
    id: Optional[int]
    model: str
    prompt: str
    response: str
    timestamp: datetime
    user_id: Optional[str] = None  # если нужен multi-user
    duration_ms: Optional[int] = None
    params: Optional[Dict[str, Any]] = None

class LLMHistoryRequest(BaseModel):
    limit: int = 20
    offset: int = 0
    model: Optional[str] = None
    user_id: Optional[str] = None

class LLMHistoryList(BaseModel):
    items: List[LLMHistoryRecord]
    total: int


# ===== 3. Для генерации / пайплайна =====

class GenerateRequest(BaseModel):
    model: str = Field(..., description="Model name")
    prompt: str
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    params: Optional[Dict[str, Any]] = None  # любые доп параметры для модели

class GenerateResponse(BaseModel):
    model: str
    prompt: str
    result: str
    id: Optional[int] = None  # id в истории
    usage: Optional[Dict[str, Any]] = None  # токены, время, цена, и т.д.


# ===== 4. Для списка моделей и инфо =====

class ModelInfo(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    is_online: bool = True
    config: LLMModelConfigSchema

class ModelListResponse(BaseModel):
    models: List[ModelInfo]
    

# ===== 5. Для админки/метрик =====

class MetricsResponse(BaseModel):
    total_requests: int
    total_tokens: int
    avg_latency_ms: float
    models_stats: Dict[str, Any]  # можно расширить

# ===== 6. Для конфигурации приложения =====

class AppConfigSchema(BaseModel):
    max_context: int = 4096
    history_db: str = "history.sqlite"
    admin_password: Optional[str] = None
    

# --- Pydantic-схемы запроса/ответа ---
class GenerateRequest(BaseModel):
    model: str
    prompt: str
    max_new_tokens: Optional[int] = 256
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    params: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class GenerateResponse(BaseModel):
    model: str
    prompt: str
    result: str
    usage: Optional[Dict[str, Any]] = None  # токены, latency и т.д.
    id: Optional[int] = None  # id в истории (если пишем)
    
    
# --- Batch-generation ---

class BatchGenerateRequestItem(BaseModel):
    model: str
    prompt: str
    max_new_tokens: Optional[int] = 256
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    params: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class BatchGenerateRequest(BaseModel):
    requests: List[BatchGenerateRequestItem]

class BatchGenerateResponseItem(BaseModel):
    model: str
    prompt: str
    result: str
    usage: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BatchGenerateResponse(BaseModel):
    results: List[BatchGenerateResponseItem]
    
    
# --- RAG (Retrieval-Augmented Generation) ---
class RAGRequest(BaseModel):
    model: str
    question: str
    top_k: Optional[int] = 3
    user_id: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class RAGResponse(BaseModel):
    answer: str
    context_docs: List[str]
