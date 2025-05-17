import asyncio
import functools
import json
import logging
import os
import time
from typing import Callable, Final, Optional
from concurrent.futures import ThreadPoolExecutor
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from pygments import highlight
from pygments.lexers import GroovyLexer
from pygments.formatters import TerminalFormatter
from src.settings import get_settings
from typing import final
import torch

def time_it(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time taken for {func.__name__}: {end_time - start_time:.2f} seconds")
        return result
    return wrapper



@final
class JenkinsPipelineGenerator:
    def __init__(self):
        """Инициализация генератора Jenkins pipeline с использованием настроек."""
        self.settings = get_settings()
        self.model = None
        self.tokenizer = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.log = logging.getLogger(__name__)
        # Задаём устройство (GPU, если доступно, иначе CPU)
        self.device: Final = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.log.info(f"Device: {self.device}")
    async def initialize(self):
        """Асинхронная инициализация: загружаем токенизатор, модель и оборачиваем её в LoRA."""
        @time_it
        def load_and_wrap():
            self.log.info("Loading tokenizer and model...")
            # 1) Токенизатор
            tok = AutoTokenizer.from_pretrained(f"{os.getcwd()}/codet5p_finetuned")
            self.log.info("Loading base_model...")
            # 2) Базовая модель
            base_model = AutoModelForSeq2SeqLM.from_pretrained(f"{os.getcwd()}/codet5p_finetuned")
            self.log.info("Loading LoRA config...")
            # 3) Конфиг LoRA
            lora_cfg = LoraConfig(
                r=8,
                lora_alpha=32,
                target_modules=["q", "v"],   # или точные имена слоёв: ["q_proj","v_proj"]
                lora_dropout=0.1,
                bias="none",
                task_type="SEQ_2_SEQ_LM",
            )

            # 4) Оборачивание
            lora_model = get_peft_model(base_model, lora_cfg)

            # 5) Переводим на устройство
            lora_model.to(self.device)

            # Опционально: посчитаем обучаемые параметры
            total = sum(p.numel() for p in lora_model.parameters())
            trainable = sum(p.numel() for p in lora_model.parameters() if p.requires_grad)
            print(f"Total params: {total:,}, trainable: {trainable:,}")

            return tok, lora_model

        loop = asyncio.get_event_loop()
        self.tokenizer, self.model = await loop.run_in_executor(self.executor, load_and_wrap)

   # ------------------------- generate_pipeline -------------------------
    @time_it
    async def generate_pipeline(
        self,
        input_json: dict,
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:

        input_text = f"{json.dumps(input_json)}"

        # -- 1. Токенизация и ПЕРЕНОС на нужное устройство ──────────── 🔑
        def _tokenize_to_device(txt: str):
            enc = self.tokenizer(
                txt,
                return_tensors="pt",
                max_length=self.settings.MAX_LENGTH,
                truncation=True,
            )
            # enc — это dict; переносим каждый тензор
            return {k: v.to(self.device) for k, v in enc.items()}

        loop = asyncio.get_event_loop()
        inputs = await loop.run_in_executor(self.executor,
                                            lambda: _tokenize_to_device(input_text))

        # -- 2. Генерация (теперь и модель, и inputs — на одном девайсе)
        start = time.time()
        outputs = await loop.run_in_executor(
            self.executor,
            lambda: self.model.generate(
                **inputs,
                max_length=self.settings.MAX_LENGTH,
                num_beams=5,
            ),
        )
        if self.settings.DEBUG:
            print(f"Generation time: {time.time() - start:.2f}s")

        # -- 3. Декодируем на CPU (иначе tokenizer.decode ругается)
        generated_ids = outputs[0].detach().cpu()           # 🔑
        pipeline = await loop.run_in_executor(
            self.executor,
            lambda: self.tokenizer.decode(generated_ids, skip_special_tokens=True),
        )

        if callback:
            callback(pipeline)
        return pipeline

    async def demo_formatter(self, pipeline_text: str, callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Демонстрация форматирования с подсветкой синтаксиса (для отладки).

           Args:
            pipeline_text: Текст pipeline для форматирования.
            callback: Функция обратного вызова.

        Returns:
            str: Отформатированный pipeline.
        """
        if self.settings.DEBUG:
            print("=== Исходный текст ===")
            print(pipeline_text)
            print("\n=== Форматированный pipeline ===")

        highlighted = highlight(pipeline_text, GroovyLexer(), TerminalFormatter())
        print(highlighted)

        if callback:
            callback(pipeline_text)

        return pipeline_text

    def __del__(self):
        """Очистка ресурсов."""
        self.executor.shutdown(wait=True)