import argparse
import json
from pathlib import Path
import sys
from huggingface_hub import snapshot_download
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import time
import functools
import os
import traceback
import re

LOGFILE = "ai_debug.log"
REPO_ID = "masonskiy/codet5p-200m-jenkins-pipeline"
import re

def fix_jenkins_pipeline(pipeline: str) -> str:
    """
    Автоматически исправляет синтаксические ошибки в Jenkinsfile, сгенерированном моделью:
    - Переносит bat/sh из when в steps.
    - Исправляет when { bat ... } → when { expression { ... } } + перенос в steps.
    - Гарантирует, что каждый stage содержит steps.
    - Удаляет пустые/невалидные when.
    - Исправляет stage без steps.
    """

    # --- 1. Переносим bat/sh из when в steps ---
    def move_bat_sh_from_when(match):
        cmd = match.group(2).strip()
        step_type = match.group(1)
        # Простой эвристический шаблон: можно заменить на expression, steps
        return (
            "when {\n"
            "    expression { env.BRANCH_NAME == 'main' }\n"
            "}\n"
            "steps {\n"
            f"    {step_type} '{cmd}'\n"
            "}"
        )

    # Перенос всех when { bat ... } или when { sh ... }
    pipeline = re.sub(
        r"when\s*\{\s*(bat|sh)\s+'([^']+)'\s*\}",
        move_bat_sh_from_when,
        pipeline,
        flags=re.MULTILINE | re.DOTALL,
    )

    # --- 2. Удаляем пустые/невалидные when ---
    pipeline = re.sub(r"when\s*\{\s*\}", "", pipeline)

    # --- 3. Исправляем stage без steps (только с when) ---
    # Находит stage, внутри которого только when {...}, без steps, и добавляет пустой steps {}
    def add_steps_if_missing(match):
        content = match.group(2)
        # Если нет блока steps
        if re.search(r"steps\s*\{", content):
            return match.group(0)
        else:
            # После блока when добавляем пустой steps
            fixed = re.sub(
                r"(when\s*\{[^}]*\})",
                r"\1\n    steps {\n        echo 'TODO'\n    }",
                content,
                flags=re.DOTALL,
            )
            # Если не было when — просто добавляем steps
            if fixed == content:
                fixed += "\n    steps {\n        echo 'TODO'\n    }"
            return f"stage{match.group(1)} {{{fixed}\n}}"

    pipeline = re.sub(
        r"stage(\s*\([^)]+\))\s*\{([^}]*)\}",
        add_steps_if_missing,
        pipeline,
        flags=re.DOTALL,
    )

    # --- 4. Удаляем лишние пробелы перед закрытием блоков ---
    pipeline = re.sub(r"\n\s*\}", "\n}", pipeline)

    # --- 5. Удаляем пустые строки подряд ---
    pipeline = re.sub(r"\n{3,}", "\n\n", pipeline)

    # --- 6. Исправляем невалидные when внутри stage без expression ---
    # (возможно, не нужно, если бат был только там, но можно добавить на всякий)
    # pipeline = re.sub(
    #     r"when\s*\{\s*([^\{\}]+)\s*\}", r"when {\n    expression { \1 }\n}", pipeline
    # )

    return pipeline

def ensure_model(model_dir: str):
    """
    Проверяет, есть ли файлы модели в `model_dir`.
    Если нет – скачивает их из HuggingFace Hub.
    """
    target = Path(model_dir)
    if target.exists() and any(target.rglob("*.*")):
        return


    target.mkdir(parents=True, exist_ok=True)

    path = snapshot_download(
        repo_id=REPO_ID,
        local_dir=model_dir,  # скачивать сразу в нужный каталог!
        local_dir_use_symlinks=False,
        resume_download=True
    )
    
def log(msg, flush=True):
    # Пишет и в файл, и на экран/стдераут
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()
    print(msg, flush=flush)  # Можно заменить на print(msg, file=sys.stderr, flush=flush)

def log_exc(e):
    # Логгирует traceback
    with open(LOGFILE, "a", encoding="utf-8") as f:
        traceback.print_exc(file=f)
        f.flush()

def time_it(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        msg = f"Time taken for {func.__name__}: {end_time - start_time:.2f} seconds"
        log(msg)
        return result
    return wrapper

log(f"[PYTHON EXECUTABLE] {sys.executable}")
log(f"[VIRTUAL ENV] {os.environ.get('VIRTUAL_ENV')}")
log(f"[WORKDIR] {os.getcwd()}")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
log(f"Используемое устройство: {device}")

@time_it
def load_model(model_path):
    log("Загрузка модели и токенизатора...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
    model = model.to(device)
    log("Модель и токенизатор загружены")
    return tokenizer, model

@time_it
def prepare_input(input_dict):
    if isinstance(input_dict, dict):
        if "instruction" in input_dict and "input" in input_dict:
            formatted_input = f"{input_dict['instruction']}\n\n{input_dict['input']}"
        else:
            formatted_input = json.dumps(input_dict, ensure_ascii=False)
        log(f"Prepared input: {formatted_input[:100]}...")
        return formatted_input
    elif isinstance(input_dict, str):
        log("Input уже строка")
        return input_dict
    else:
        raise ValueError(f"Unsupported input type: {type(input_dict)}")

@time_it
def tokenize_input(tokenizer, text):
    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
    log(f"Tokenized input keys: {list(inputs.keys())}, shapes: {[v.shape for v in inputs.values()]}")
    return {key: value.to(device) for key, value in inputs.items()}

@time_it
def generate_pipeline(model, tokenizer, inputs):
    log("Генерируем Jenkins pipeline...")
    outputs = model.generate(**inputs, max_length=512, num_beams=4)
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    log(f"Pipeline сгенерирован, длина: {len(generated_text)}")
    return generated_text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-path", default="./codet5p_finetuned")
    args = parser.parse_args()

    try:
        ensure_model(args.model_path)
        log(f"main() запущен: input={args.input}, output={args.output}, model_path={args.model_path}")

        tokenizer, model = load_model(args.model_path)
        with open(args.input, "r", encoding="utf-8") as f:
            input_json = json.load(f)
        formatted_input = prepare_input(input_json)
        inputs = tokenize_input(tokenizer, formatted_input)

        generated_pipeline = generate_pipeline(model, tokenizer, inputs)
        fixed_pipeline = fix_jenkins_pipeline(generated_pipeline)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(fixed_pipeline)
        log("Pipeline записан в файл успешно.")
        print(json.dumps({"status": "success"}))
    except Exception as e:
        log_exc(e)
        log(f"ERROR: {e}")
        print(json.dumps({"error": str(e), "status": "error"}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
