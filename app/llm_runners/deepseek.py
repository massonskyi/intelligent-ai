import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
from accelerate import infer_auto_device_map, init_empty_weights, load_checkpoint_and_dispatch
from typing import Any, Dict
from core.logging import get_logger

logger = get_logger(__name__)

class DeepSeekModel:
    def __init__(self, model_id: str = "deepseek-ai/deepseek-llm-7b-base", device: str = None):
        logger.info(f"Инициализация DeepSeekModel. model_id: '{model_id}', запрошенное устройство: '{device}'")
        # Определяем устройство: CUDA, MPS, CPU
        self.device = self._get_best_device(device)
        logger.debug(f"Выбрано устройство: {self.device}")
        self.model_id = model_id

        # Настраиваем параметры загрузки под VRAM
        self.load_kwargs = self._select_load_config(self.device)
        logger.debug(f"Параметры для загрузки модели: {self.load_kwargs}")

        # Загружаем токенизатор
        logger.info(f"Загрузка токенизатора для '{self.model_id}'...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            logger.info("Токенизатор успешно загружен.")
        except Exception as e:
            logger.exception(f"Ошибка при загрузке токенизатора для '{self.model_id}'.")
            raise
        
        # Загружаем модель (с авто-оптимизацией под VRAM)
        logger.info(f"Загрузка модели '{self.model_id}'...")
        self.model = self._load_model()

        # Создаём pipeline для inference
        logger.info("Создание text-generation pipeline...")
        try:
            self.text_generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device.type == "cuda" else (-1 if self.device.type == "cpu" else self.device.type),
                torch_dtype=self.load_kwargs.get("torch_dtype", None)
            )
            logger.info("Text-generation pipeline успешно создан.")
        except Exception as e:
            logger.exception("Ошибка при создании text-generation pipeline.")
            raise

    def _get_best_device(self, forced_device: str = None) -> torch.device:
        logger.debug(f"Определение оптимального устройства. Принудительное устройство: {forced_device}")
        if forced_device is not None:
            logger.info(f"Используется принудительно заданное устройство: {forced_device}")
            return torch.device(forced_device)
        if torch.cuda.is_available():
            logger.info("CUDA доступна. Используется устройство 'cuda'.")
            return torch.device("cuda")
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            logger.info("MPS доступен (для Apple Silicon). Используется устройство 'mps'.")
            return torch.device("mps")
        logger.info("CUDA и MPS недоступны. Используется устройство 'cpu'.")
        return torch.device("cpu")

    def _get_gpu_memory_gb(self) -> float:
        logger.debug(f"Получение объема памяти GPU для устройства {self.device.type}.")
        if self.device.type == "cuda":
            idx = torch.cuda.current_device()
            if self.device.index is not None:
                idx = self.device.index
            props = torch.cuda.get_device_properties(idx)
            vram_gb = props.total_memory / (1024 ** 3)
            logger.debug(f"Доступно VRAM (CUDA:{idx}): {vram_gb:.2f} GB.")
            return vram_gb
        elif self.device.type == "mps":
            logger.debug("Устройство MPS, точный объем выделенной VRAM не определяется стандартно, предполагаем достаточно для float16.")
            return 8.0
        logger.debug("Устройство не CUDA и не MPS. Объем VRAM: 0.0 GB.")
        return 0.0

    def _select_load_config(self, device: torch.device) -> Dict[str, Any]:
        vram_gb = self._get_gpu_memory_gb()
        logger.info(f"Выбор конфигурации загрузки. Устройство: {device.type}, VRAM: {vram_gb:.1f} GB.")
        load_kwargs = {}
        # CUDA
        if device.type == "cuda":
            if vram_gb >= 12:
                load_kwargs = {"torch_dtype": torch.float16, "device_map": "auto"}
                logger.info("Конфигурация для CUDA >=12GB VRAM: torch.float16, device_map='auto'.")
            elif vram_gb >= 6:
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_enable_fp32_cpu_offload=True
                )
                load_kwargs = {
                    "device_map": "auto",
                    "quantization_config": quantization_config
                }
                logger.info("Конфигурация для CUDA 6-12GB: 8bit quant, device_map='auto', cpu offload.")
            elif vram_gb >= 4:
                # Пробуем 4bit quant (на bitsandbytes >= 0.41)
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    llm_int8_enable_fp32_cpu_offload=True
                )
                load_kwargs = {
                    "device_map": "auto",
                    "quantization_config": quantization_config
                }
                logger.info("Конфигурация для CUDA 4-6GB: 4bit quant, агрессивный offload.")
            else:
                err_msg = f"VRAM слишком мало ({vram_gb:.1f} GB). DeepSeek 7B требует минимум 4GB (4bit quant)."
                logger.error(err_msg)
                raise RuntimeError(err_msg)
        # MPS (Apple Silicon)
        elif device.type == "mps":
            load_kwargs = {"torch_dtype": torch.float16, "device_map": "mps"}
            logger.info("Конфигурация для MPS: torch.float16, device_map='mps'.")
        # CPU
        else:
            # BitsAndBytes не поддерживает quantization на CPU напрямую.
            # Варианты: либо все в fp32, либо попробуем quantization_config и offload всё на CPU (будет работать медленно).
            try:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float32,  # Можно оставить float32 для CPU
                    bnb_4bit_use_double_quant=True
                )
                load_kwargs = {
                    "device_map": "cpu",
                    "quantization_config": quantization_config
                }
                logger.info("CPU: загрузка в 4bit quant через BitsAndBytes (медленно, но экономно).")
            except Exception as e:
                load_kwargs = {"torch_dtype": torch.float32, "device_map": "cpu"}
                logger.warning("CPU: BitsAndBytes не доступен, fallback на fp32.")
            # Для совсем слабых — warning
            import psutil
            ram_gb = psutil.virtual_memory().total / (1024 ** 3)
            if ram_gb < 10:
                logger.warning(f"Очень мало RAM для DeepSeek 7B на CPU ({ram_gb:.1f} GB). Возможен OutOfMemory! Рекомендуется >= 16GB RAM.")
        return load_kwargs

    def _load_model(self):
        logger.info(f"Начало загрузки модели '{self.model_id}' с параметрами: {self.load_kwargs}")
        try:
            model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                **self.load_kwargs
            )
            logger.info(f"Модель '{self.model_id}' успешно загружена.")
            return model
        except Exception as e:
            logger.exception(f"Критическая ошибка при загрузке модели '{self.model_id}'.")
            raise

    def inference(self, prompt: str, **gen_kwargs) -> str:
        logger.info(f"Выполнение инференса. Промпт (начало): '{prompt[:100]}...'")
        logger.debug(f"Переданные параметры генерации: {gen_kwargs}")
        
        default_gen_kwargs = {
            "max_new_tokens": 256,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.95,
        }
        final_gen_kwargs = {**default_gen_kwargs, **gen_kwargs}
        logger.debug(f"Финальные параметры генерации: {final_gen_kwargs}")

        try:
            result = self.text_generator(
                prompt,
                **final_gen_kwargs
            )
            generated_text = result[0]["generated_text"]
            logger.info(f"Инференс успешно завершен. Результат (начало): '{generated_text[:100]}...'")
            return generated_text
        except Exception as e:
            logger.exception("Ошибка во время выполнения инференса.")
            raise

