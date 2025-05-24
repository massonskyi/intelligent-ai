# app/services/llm_service.py

from typing import Optional, Dict, Any
from core.config import config_store
from llm_runners.llama_cpp import LlamaCppRunner
from llm_runners.transformers import TransformersRunner
from llm_runners.deepseek import DeepSeekModel
from llm_runners.mistral import MistralModel
from llm_runners.codellama import CodeLlamaModel
from llm_runners.starcoder import StarCoderModel
from llm_runners.llama2 import Llama2Model
from db.database import get_session
from models.orm import LLMHistory
import json
from datetime import datetime

LLM_CLASS_REGISTRY = {
    "deepseek": DeepSeekModel,
    "mistral": MistralModel,
    "codellama": CodeLlamaModel,
    "starcoder": StarCoderModel,
    "llama2": Llama2Model,
    "llama_cpp": LlamaCppRunner,
    "transformers": TransformersRunner,
}

class LLMService:
    def __init__(self):
        self.runners: Dict[str, Any] = {}
        self.reload_all_runners()
        config_store.subscribe(self.reload_all_runners)

    def get_runner(self, model_name: str):
        model_name = model_name.strip().lower()  # <-- normalize
        cfg = config_store.get_model_config(model_name)
        model_type = cfg.type.lower()
        if model_name not in self.runners:
            runner_cls = LLM_CLASS_REGISTRY.get(model_type)
            if not runner_cls:
                raise RuntimeError(f"Unknown model type: {model_type}")
            self.runners[model_name] = runner_cls(cfg)
        return self.runners[model_name]

    def reload_all_runners(self, *_):
        """Полный reset всех runners (напр., при изменении конфига моделей)."""
        self.runners = {}

    async def generate(self, model: str, prompt: str, params: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
        cfg = config_store.get_model_config(model)
        runner = self.get_runner(model)

        # Merge runtime params: model config < request params
        runtime_params = dict(cfg.params or {})
        if params:
            runtime_params.update(params)
        if "temperature" not in runtime_params and hasattr(cfg, "temperature"):
            runtime_params["temperature"] = cfg.temperature
        if "top_p" not in runtime_params and hasattr(cfg, "top_p"):
            runtime_params["top_p"] = cfg.top_p

        result = await runner.generate(prompt, **runtime_params)
        await self.add_history(model, prompt, result, user_id, runtime_params)
        return result

    async def generate_stream(self, model: str, prompt: str, params: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
        cfg = config_store.get_model_config(model)
        runner = self.get_runner(model)
        runtime_params = dict(cfg.params or {})
        if params:
            runtime_params.update(params)
        if "temperature" not in runtime_params and hasattr(cfg, "temperature"):
            runtime_params["temperature"] = cfg.temperature
        if "top_p" not in runtime_params and hasattr(cfg, "top_p"):
            runtime_params["top_p"] = cfg.top_p

        # Stream через async-генератор
        async for chunk in runner.generate_stream(prompt, **runtime_params):
            yield chunk

    async def add_history(self, model, prompt, response, user_id, params):
        record = LLMHistory(
            model=model,
            prompt=prompt,
            response=response,
            user_id=user_id,
            params=json.dumps(params),
            timestamp=datetime.utcnow()
        )
        async with get_session() as session:
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    async def get_history(self, model: Optional[str] = None, user_id: Optional[str] = None, limit: int = 20, offset: int = 0):
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

llm_service = LLMService()
