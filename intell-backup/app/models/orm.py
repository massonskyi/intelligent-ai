# app/models/orm.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class LLMHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model: str
    prompt: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    duration_ms: Optional[int] = None
    params: Optional[str] = None  # json-строка (или dict с encode/decode)
    # Можно добавить ещё usage/tokens etc
    

class LLMRequestMetric(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model: str
    tokens: int
    duration_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class LLMMetricsSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_requests: int = 0
    total_tokens: int = 0
    total_errors: int = 0
    avg_latency_ms: float = 0.0
    # Можно добавить по моделям/юзерам в json (или завести отдельные таблицы/модели для детальной статистики)
    models_stats_json: Optional[str] = None  # Сериализуем dict как JSON строку
    users_stats_json: Optional[str] = None
    

class RAGHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[str] = None
    model: str
    question: str
    context_docs_json: str  # json.dumps([...])
    answer: str
    created_at: datetime = Field(default_factory=datetime.utcnow)