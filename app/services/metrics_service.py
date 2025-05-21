# app/services/metrics_service.py
import asyncio
from collections import defaultdict
import json
from typing import Dict, Any
from datetime import datetime

from db.database import get_session
from models.orm import LLMMetricsSnapshot

class MetricsService:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.reset()

    def reset(self):
        self.total_requests = 0
        self.total_tokens = 0
        self.total_latency_ms = 0
        self.total_errors = 0
        self.total_queue_time_ms = 0
        self.users_stats = defaultdict(lambda: {
            "requests": 0,
            "errors": 0,
            "tokens": 0
        })
        self.models_stats = defaultdict(lambda: {
            "requests": 0,
            "tokens": 0,
            "total_latency_ms": 0,
            "total_queue_time_ms": 0,
            "avg_latency_ms": 0.0,
            "errors": 0
        })
        self.last_reset = datetime.utcnow()
        
    async def record_error(self, model: str = None, user: str = None):
        async with self._lock:
            self.total_errors += 1
            if model:
                self.models_stats[model]["errors"] += 1
            if user:
                self.users_stats[user]["errors"] += 1

    async def record_queue_time(self, model: str, queue_time_ms: int):
        async with self._lock:
            self.total_queue_time_ms += queue_time_ms
            self.models_stats[model]["total_queue_time_ms"] += queue_time_ms

    async def record_user(self, user: str, tokens: int):
        async with self._lock:
            self.users_stats[user]["requests"] += 1
            self.users_stats[user]["tokens"] += tokens
            
    async def record_request(self, model: str, tokens: int, latency_ms: int):
        async with self._lock:
            self.total_requests += 1
            self.total_tokens += tokens
            self.total_latency_ms += latency_ms
            stats = self.models_stats[model]
            stats["requests"] += 1
            stats["tokens"] += tokens
            stats["total_latency_ms"] += latency_ms
            stats["avg_latency_ms"] = (
                stats["total_latency_ms"] / stats["requests"]
                if stats["requests"] > 0 else 0.0
            )

    async def get_metrics(self):
        async with self._lock:
            avg_latency_ms = (
                self.total_latency_ms / self.total_requests
                if self.total_requests > 0 else 0.0
            )
            return {
                "total_requests": self.total_requests,
                "total_tokens": self.total_tokens,
                "avg_latency_ms": avg_latency_ms,
                "models_stats": dict(self.models_stats),
                "last_reset": self.last_reset.isoformat(),
            }

    async def reset_metrics(self):
        async with self._lock:
            self.reset()

    async def save_snapshot(self):
        data = await self.get_metrics()
        async with get_session() as session:
            snap = LLMMetricsSnapshot(
                timestamp=datetime.utcnow(),
                total_requests=data["total_requests"],
                total_tokens=data["total_tokens"],
                total_errors=getattr(self, 'total_errors', 0),
                avg_latency_ms=data["avg_latency_ms"],
                models_stats_json=json.dumps(data["models_stats"]),
                users_stats_json=json.dumps(getattr(self, 'users_stats', {})),
            )
            session.add(snap)
            await session.commit()
            
    async def restore_from_last_snapshot(self):
        async with get_session() as session:
            from sqlmodel import select
            stmt = select(LLMMetricsSnapshot).order_by(LLMMetricsSnapshot.timestamp.desc()).limit(1)
            result = await session.exec(stmt)
            snap = result.first()
            if snap:
                self.total_requests = snap.total_requests
                self.total_tokens = snap.total_tokens
                self.total_errors = snap.total_errors
                self.total_latency_ms = int(snap.avg_latency_ms * snap.total_requests)  # грубо
                self.models_stats = json.loads(snap.models_stats_json or '{}')
                self.users_stats = json.loads(snap.users_stats_json or '{}')
                self.last_reset = snap.timestamp
            # Если нет snapshot — просто reset()
# Singleton
metrics_service = MetricsService()
