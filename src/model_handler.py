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
import sys

def time_it(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time taken for {func.__name__}: {end_time - start_time:.2f} seconds")
        return result
    return wrapper

def prepare_input(input_dict):
    if isinstance(input_dict, dict):
        if "instruction" in input_dict and "input" in input_dict:
            # --- Важно! Не сериализуем input! ---
            formatted_input = f"{input_dict['instruction']}\n\n{input_dict['input']}"
        else:
            formatted_input = str(input_dict)
        print(f"Prepared input: {formatted_input[:100]}...", file=sys.stderr)
        return formatted_input
    elif isinstance(input_dict, str):
        return input_dict
    else:
        raise ValueError(f"Unsupported input type: {type(input_dict)}")

def tokenize_input(tokenizer, text, device, max_length=512):
    inputs = tokenizer(text, return_tensors="pt", max_length=max_length, truncation=True)
    print(f"Tokenized input keys: {list(inputs.keys())}, shapes: {[v.shape for v in inputs.values()]}", file=sys.stderr)
    return {key: value.to(device) for key, value in inputs.items()}

@final
class JenkinsPipelineGenerator:
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.tokenizer = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.log = logging.getLogger(__name__)
        self.device: Final = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.log.info(f"Device: {self.device}")

    async def initialize(self):
        @time_it
        def load_and_wrap():
            self.log.info("Loading tokenizer and model...")
            tok = AutoTokenizer.from_pretrained(f"{os.getcwd()}/codet5p_finetuned")
            self.log.info("Loading base_model...")
            base_model = AutoModelForSeq2SeqLM.from_pretrained(f"{os.getcwd()}/codet5p_finetuned")
            self.log.info("Loading LoRA config...")
            lora_cfg = LoraConfig(
                r=8,
                lora_alpha=32,
                target_modules=["q", "v"],
                lora_dropout=0.1,
                bias="none",
                task_type="SEQ_2_SEQ_LM",
            )
            lora_model = get_peft_model(base_model, lora_cfg)
            lora_model.to(self.device)
            total = sum(p.numel() for p in lora_model.parameters())
            trainable = sum(p.numel() for p in lora_model.parameters() if p.requires_grad)
            print(f"Total params: {total:,}, trainable: {trainable:,}")
            return tok, lora_model

        loop = asyncio.get_event_loop()
        self.tokenizer, self.model = await loop.run_in_executor(self.executor, load_and_wrap)

    @time_it
    async def generate_pipeline(
        self,
        input_json: dict,
        callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        # --- 1. Подготовка входа как в тестовом скрипте ---
        formatted_input = prepare_input(input_json)

        # --- 2. Токенизация ---
        loop = asyncio.get_event_loop()
        inputs = await loop.run_in_executor(
            self.executor,
            lambda: tokenize_input(
                self.tokenizer, 
                formatted_input, 
                self.device, 
                512
            )
        )

        # --- 3. Генерация пайплайна ---
        def _generate(inputs):
            outputs = self.model.generate(
                **inputs,
                max_length=512,
                num_beams=4,
            )
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"Generated pipeline: {generated_text[:200]}...", file=sys.stderr)
            return generated_text

        pipeline = await loop.run_in_executor(self.executor, lambda: _generate(inputs))

        if callback:
            callback(pipeline)
        return pipeline

    async def demo_formatter(self, pipeline_text: str, callback: Optional[Callable[[str], None]] = None) -> str:
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
        self.executor.shutdown(wait=True)
