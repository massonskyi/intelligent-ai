import asyncio
from typing import Callable, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, TextIteratorStreamer
import torch
import time
from threading import RLock
from core.logging import get_logger
logger = get_logger(__name__)
class TransformersRunner:
    """
    Production-ready HuggingFace runner:
    - Асинхронный (через run_in_executor)
    - Поддерживает hot-reload модели по сигналу
    - Самооптимизация quantization для low VRAM
    - Логирование и интеграция с метриками
    - Thread-safe reload
    """
    def __init__(self, cfg):
        self.cfg = cfg
        self.model = None
        self.tokenizer = None
        self.text_generator: Optional[Callable] = None
        self.device = self._select_device(cfg)
        self._lock = RLock()
        self._load_model_and_tokenizer()
        from core.config import config_store
        config_store.subscribe(self._on_config_change)
        logger.info(
            f"[TransformersRunner] Initialized for model: {getattr(cfg, 'name', '<missing>')} at {cfg.model_path}")

    def _on_config_change(self, _):
        asyncio.create_task(self.reload())
    def filter_generate_kwargs(self, kwargs: dict) -> dict:
        """
        The function `filter_generate_kwargs` filters and validates input keyword arguments based on a
        predefined set of allowed keys, with additional protection against invalid temperature values.
        
        :param kwargs: The `kwargs` parameter in the `filter_generate_kwargs` function is a dictionary that
        contains various key-value pairs representing different parameters for a text generation model. The
        function filters out only the allowed parameters based on the keys specified in the `allowed` set.
        Additionally, it includes a check to remove the
        :type kwargs: dict
        :return: The function `filter_generate_kwargs` returns a dictionary containing only the key-value
        pairs from the input `kwargs` dictionary that have keys specified in the `allowed` set.
        Additionally, it removes the key-value pair with key "temperature" if the corresponding value is
        less than or equal to 0 or if the value cannot be converted to a float.
        """
        allowed = {
            "max_length", "min_length", "max_new_tokens", "min_new_tokens",
            "do_sample", "temperature", "top_p", "top_k", "repetition_penalty",
            "num_return_sequences", "eos_token_id", "pad_token_id",
            "early_stopping", "length_penalty", "penalty_alpha",
            "no_repeat_ngram_size", "typical_p", "logits_processor", "bad_words_ids",
            "output_scores", "return_dict_in_generate", "renormalize_logits",
            "forced_bos_token_id", "forced_eos_token_id", "remove_invalid_values"
        }
        filtered = {k: v for k, v in kwargs.items() if k in allowed}
        # Защита от temperature <= 0
        if "temperature" in filtered:
            try:
                if float(filtered["temperature"]) <= 0:
                    del filtered["temperature"]
            except Exception:
                del filtered["temperature"]
        return filtered
    def _select_device(self, cfg):
        # auto-detect, user can override via cfg.params.device
        forced_device = (cfg.params or {}).get("device", None)
        if forced_device:
            if forced_device == "cpu":
                return torch.device("cpu")
            if forced_device == "cuda" and torch.cuda.is_available():
                return torch.device("cuda")
            if forced_device == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return torch.device("mps")
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    async def reload(self):
        """Safe reload (thread/async-safe)."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._reload_sync)

    def _reload_sync(self):
        with self._lock:
            self._load_model_and_tokenizer()

    def _select_quantization(self, vram_gb, params):
        # Smart quantization: BnB 4bit/8bit для low VRAM
        if vram_gb < 6:
            try:
                from transformers import BitsAndBytesConfig
                params["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
            except ImportError:
                pass
        elif vram_gb < 12:
            try:
                from transformers import BitsAndBytesConfig
                params["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
            except ImportError:
                pass
        return params

    def _load_model_and_tokenizer(self):
        with self._lock:
            params = dict(self.cfg.params or {})
            # Авто-детект VRAM
            vram_gb = 0
            if self.device.type == "cuda":
                vram_gb = torch.cuda.get_device_properties(self.device.index or 0).total_memory / (1024 ** 3)
            params = self._select_quantization(vram_gb, params)
            torch_dtype = params.get("torch_dtype", "auto")
            if isinstance(torch_dtype, str):
                torch_dtype = {
                    "auto": None,
                    "float16": torch.float16,
                    "bfloat16": torch.bfloat16,
                    "float32": torch.float32,
                }.get(torch_dtype.lower(), None)
            load_kwargs = {}
            if torch_dtype:
                load_kwargs["torch_dtype"] = torch_dtype
            if params.get("device_map"):
                load_kwargs["device_map"] = params["device_map"]
            if params.get("quantization_config"):
                load_kwargs["quantization_config"] = params["quantization_config"]
            self.tokenizer = AutoTokenizer.from_pretrained(self.cfg.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.cfg.model_path,
                **load_kwargs
            )
            device_idx = (
                0 if self.device.type == "cuda" else
                -1 if self.device.type == "cpu" else
                self.device.type
            )
            self.text_generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=device_idx,
                torch_dtype=load_kwargs.get("torch_dtype", None)
            )

    async def generate(self, prompt, **gen_kwargs):
        """
        Асинхронный вызов модели. Возвращает generated_text и runtime-метрики.
        """
        loop = asyncio.get_running_loop()
        default_gen_kwargs = {
            "max_new_tokens": gen_kwargs.get("max_new_tokens", 256),
            "do_sample": True,
            "temperature": gen_kwargs.get("temperature", getattr(self.cfg, "temperature", 0.7)),
            "top_p": gen_kwargs.get("top_p", getattr(self.cfg, "top_p", 0.95)),
        }
        final_gen_kwargs = {**default_gen_kwargs, **gen_kwargs}
        final_gen_kwargs = self.filter_generate_kwargs(final_gen_kwargs)  # Фильтруем!

        def sync_gen():
            t_start = time.monotonic()
            if not self.text_generator:
                return 
            result = self.text_generator(prompt, **final_gen_kwargs)
            t_end = time.monotonic()
            output = result[0]["generated_text"]
            
            assert hasattr(self.tokenizer, "encode"), "Tokenizer is wrong initialize"
            
            prompt_tokens = len(self.tokenizer.encode(prompt))
            result_tokens = len(self.tokenizer.encode(output))
            return {
                "text": output,
                "tokens_prompt": prompt_tokens,
                "tokens_result": result_tokens,
                "latency_ms": int((t_end - t_start) * 1000)
            }

        # run sync in executor
        res = await loop.run_in_executor(None, sync_gen)

        # Интеграция с метриками (если есть)
        try:
            from services.metrics_service import metrics_service
            logger.debug(
                f"[generate] model={self.cfg.name} | latency={res['latency_ms']}ms | tokens={res['tokens_result']}")

            await metrics_service.record_request(
                model=self.cfg.name,
                tokens=res["tokens_result"],
                latency_ms=res["latency_ms"]
            )
        except Exception:
            pass
        return res["text"]

    async def generate_stream(self, prompt: str, **gen_kwargs):
        loop = asyncio.get_running_loop()
        def sync_stream():
            streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True)
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            gen_kwargs_full = {
                "inputs": inputs.input_ids,
                "attention_mask": inputs.attention_mask,
                "max_new_tokens": gen_kwargs.get("max_new_tokens", 256),
                "do_sample": gen_kwargs.get("do_sample", True),
                "temperature": gen_kwargs.get("temperature", getattr(self.cfg, "temperature", 0.7)),
                "top_p": gen_kwargs.get("top_p", getattr(self.cfg, "top_p", 0.95)),
                "streamer": streamer
            }
            import threading
            t = threading.Thread(target=self.model.generate, kwargs=gen_kwargs_full)
            t.start()
            for text in streamer:
                yield text
            t.join()
        # yield-им чанк в event loop
        for chunk in await loop.run_in_executor(None, lambda: list(sync_stream())):
            yield chunk