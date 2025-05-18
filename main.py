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

def extract_steps(input_json):
    scripts = input_json.get("input", {}).get("project", {}).get("scripts", {})
    stages = {}
    if "build" in scripts:
        stages["Build"] = [v for v in scripts["build"].values() if isinstance(v, str)]
    if "test" in scripts:
        stages["Test"] = [v for v in scripts["test"].values() if isinstance(v, str)]
    if "lint" in scripts:
        stages["Lint"] = [v for v in scripts["lint"].values() if isinstance(v, str)]
    if "docker" in scripts:
        stages["Build Docker Image"] = [v for v in scripts["docker"].values() if isinstance(v, str)]
    if "deploy" in scripts:
        stages["Deploy"] = [v for v in scripts["deploy"].values() if isinstance(v, str)]
    return stages

def fix_brace_nesting(pipeline: str) -> str:
    # То же, что выше, но с доп. очисткой пустых строк
    lines = pipeline.splitlines()
    fixed_lines = []
    brace_stack = []
    for i, line in enumerate(lines):
        opens = line.count('{')
        closes = line.count('}')
        fixed_lines.append(line)
        for _ in range(opens):
            brace_stack.append(i)
        for _ in range(closes):
            if brace_stack:
                brace_stack.pop()
    for _ in range(len(brace_stack)):
        fixed_lines.append('}')
    return '\n'.join(fixed_lines).strip()

def fix_jenkins_pipeline(pipeline: str, input_json: dict = None) -> str:
    """
    Расширенная постобработка Jenkinsfile:
      - Исправляет типовые и сложные ошибки.
      - Переносит bat/sh из when в steps, валидирует when/steps.
      - Вставляет команды из input_json или echo TODO.
      - Исправляет скобки, stages, post, environment.
      - Очищает лишние или битые блоки.
    """

    # 1. Удаление комментариев в стиле // ... (если они мешают парсингу)
    pipeline = re.sub(r"//.*", "", pipeline)

    # 2. Перенос bat/sh из when в steps
    def move_when_command_to_steps(match):
        stage_name = match.group(1)
        when_body = match.group(2)
        cmd_match = re.search(r"(bat|sh)\s+'([^']+)'", when_body)
        if cmd_match:
            step_type, step_cmd = cmd_match.groups()
            return (
                f"stage('{stage_name}') {{\n"
                f"    when {{ expression {{ env.BRANCH_NAME == 'main' }} }}\n"
                f"    steps {{\n"
                f"        {step_type} '{step_cmd}'\n"
                f"        echo 'TODO'\n"
                f"    }}\n"
                f"}}"
            )
        return f"stage('{stage_name}') {{\n    steps {{ echo 'TODO' }}\n}}"
    pipeline = re.sub(
        r"stage\('([^']+)'\)\s*\{\s*when\s*\{([^}]+)\}",
        move_when_command_to_steps,
        pipeline,
        flags=re.DOTALL
    )

    # 3. Удаляем невалидные when без expression
    pipeline = re.sub(r"when\s*\{\s*(bat|sh)[^}]+\}", "when { expression { env.BRANCH_NAME == 'main' } }", pipeline, flags=re.DOTALL)
    pipeline = re.sub(r"when\s*\{\s*\}", "", pipeline)

    # 4. Исправляем дублирующиеся или вложенные steps, когда steps встречается несколько раз подряд
    pipeline = re.sub(r"(steps\s*\{[^\}]*\})\s*steps\s*\{[^\}]*\}", r"\1", pipeline, flags=re.DOTALL)

    # 5. Добавляем steps, если их нет
    stage_cmds = extract_steps(input_json) if input_json else {}
    def ensure_steps(match):
        stage_name = match.group(1)
        body = match.group(2)
        if 'steps' in body:
            return match.group(0)
        cmds = stage_cmds.get(stage_name, [])
        steps_code = "\n".join(f"        bat '{cmd}'" for cmd in cmds) if cmds else "        echo 'TODO'"
        return f"stage('{stage_name}') {{{body}\n    steps {{\n{steps_code}\n    }}\n}}"
    pipeline = re.sub(r"stage\('([^']+)'\)\s*\{([^}]*)\}", ensure_steps, pipeline, flags=re.DOTALL)

    # 6. Исправление батч-команд типа bat pip → bat 'pip'
    pipeline = re.sub(r"bat\s+([^\n{]+)", lambda m: f"bat '{m.group(1).strip()}'", pipeline)

    # 7. Вставка/коррекция основных блоков pipeline, stages, environment, post если вдруг они утеряны
    if not re.search(r'pipeline\s*\{', pipeline):
        stages_block = re.search(r"(stages\s*\{[^\}]*\})", pipeline, flags=re.DOTALL)
        stages_text = stages_block.group(0) if stages_block else ""
        pipeline = f"pipeline {{\n    agent any\n{stages_text}\n}}"

    if not re.search(r'stages\s*\{', pipeline):
        # Добавляем все stages в один блок stages { ... }
        stages = re.findall(r"(stage\s*\([^)]+\)\s*\{[^\}]*\})", pipeline, flags=re.DOTALL)
        if stages:
            stages_block = "stages {\n" + "\n".join("    " + s.replace('\n', '\n    ') for s in stages) + "\n}"
            pipeline = re.sub(r"(stage\s*\([^)]+\)\s*\{[^\}]*\})", "", pipeline, flags=re.DOTALL)
            pipeline = re.sub(r'(pipeline\s*\{)', r'\1\n' + stages_block, pipeline)
        else:
            pipeline = re.sub(r'(pipeline\s*\{)', r'\1\n    stages {\n    }\n', pipeline)

    # 8. Исправляем дублирующиеся или незакрытые скобки, вложенные blocks
    pipeline = fix_brace_nesting(pipeline)

    # 9. Удаляем пустые строки, trailing пробелы, дублирующиеся stages, пустые этапы
    pipeline = re.sub(r'\n\s*\n', '\n', pipeline)
    pipeline = re.sub(r'stage\s*\([^)]+\)\s*\{\s*steps\s*\{\s*\}\s*\}', '', pipeline, flags=re.DOTALL)
    pipeline = re.sub(r'(archiveArtifacts[^\}]+)\n[^\n]*archiveArtifacts', r'\1', pipeline)
    pipeline = re.sub(r'^\s*$', '', pipeline, flags=re.MULTILINE)

    # 10. Финальный фикс вложенности
    pipeline = fix_brace_nesting(pipeline)
    return pipeline.strip()

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
        # после генерации pipeline
        fixed_pipeline = fix_jenkins_pipeline(generated_pipeline, input_json)

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
