import asyncio
import time
from threading import RLock

class LlamaCppRunner:
    """
    Production-ready llama.cpp runner:
    - Поддержка hot-reload
    - Thread-safe и async
    - Интеграция с метриками
    - Авто-оптимизация ресурсов
    """
    def __init__(self, cfg):
        self.cfg = cfg
        self.model = None
        self._lock = RLock()
        self._load_model()
        from app.core.config import config_store
        config_store.subscribe(self._on_config_change)

    def _on_config_change(self, _):
        asyncio.create_task(self.reload())

    async def reload(self):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._reload_sync)

    def _reload_sync(self):
        with self._lock:
            self._load_model()

    def _load_model(self):
        from llama_cpp import Llama
        with self._lock:
            params = dict(self.cfg.params or {})
            # авто-детект числа потоков (можно расширить)
            import os
            if "n_threads" not in params:
                try:
                    params["n_threads"] = min(os.cpu_count() or 8, 16)
                except Exception:
                    params["n_threads"] = 8
            # поддержка других параметров: n_ctx, n_gpu_layers и т.д.
            self.model = Llama(
                model_path=self.cfg.model_path,
                n_ctx=params.get("n_ctx", 4096),
                n_threads=params.get("n_threads", 8),
                n_gpu_layers=params.get("n_gpu_layers", 0)
            )

    async def generate(self, prompt: str, **kwargs):
        loop = asyncio.get_running_loop()
        # обработка параметров temperature, top_p, max_new_tokens
        def sync_gen():
            t_start = time.monotonic()
            try:
                result = self.model(
                    prompt,
                    max_tokens=kwargs.get("max_new_tokens", 256),
                    temperature=kwargs.get("temperature", getattr(self.cfg, "temperature", 0.7)),
                    top_p=kwargs.get("top_p", getattr(self.cfg, "top_p", 0.95))
                )
                t_end = time.monotonic()
                text = result["choices"][0]["text"]
                # Токены (llama-cpp выдает stats)
                prompt_tokens = result.get("usage", {}).get("prompt_tokens", 0)
                result_tokens = result.get("usage", {}).get("completion_tokens", 0)
                latency_ms = int((t_end - t_start) * 1000)
                # Логируем метрики
                try:
                    from app.services.metrics_service import metrics_service
                    asyncio.create_task(metrics_service.record_request(
                        model=self.cfg.name,
                        tokens=prompt_tokens + result_tokens,
                        latency_ms=latency_ms
                    ))
                except Exception:
                    pass
                return text
            except Exception as e:
                # Логируем ошибку
                try:
                    from app.services.metrics_service import metrics_service
                    asyncio.create_task(metrics_service.record_error(
                        model=self.cfg.name
                    ))
                except Exception:
                    pass
                raise e
        return await loop.run_in_executor(None, sync_gen)
    
    async def generate_stream(self, prompt: str, **kwargs):
        loop = asyncio.get_running_loop()
        def sync_stream():
            for chunk in self.model(
                prompt,
                max_tokens=kwargs.get("max_new_tokens", 256),
                temperature=kwargs.get("temperature", getattr(self.cfg, "temperature", 0.7)),
                top_p=kwargs.get("top_p", getattr(self.cfg, "top_p", 0.95)),
                stream=True
            ):
                yield chunk["choices"][0]["text"]
        for chunk in await loop.run_in_executor(None, lambda: list(sync_stream())):
            yield chunk
