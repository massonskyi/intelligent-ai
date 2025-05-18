import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List
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


def extract_stage_steps(input_json: Dict) -> Dict[str, List[str]]:
    """Извлекает команды для каждого stage из входной конфигурации."""
    if not input_json:
        return {}

    project = input_json.get("input", {}).get("project", {})
    scripts = project.get("scripts", {})
    build_tool = project.get("buildTool", "")
    test_frameworks = project.get("testFrameworks", [])
    dockerfile_present = project.get("dockerfilePresent", False)

    stages = {}

    # Build stage
    if "build" in scripts:
        build_cmd = scripts["build"].get("windows", scripts["build"].get("unix", ""))
        if build_cmd:
            stages["Build"] = [build_cmd]
    elif build_tool == "pip":
        stages["Build"] = ["pip install -r requirements.txt"]

    # Test stage
    if "test" in scripts:
        test_cmd = scripts["test"].get("windows", scripts["test"].get("unix", ""))
        if test_cmd:
            stages["Test"] = [test_cmd]
    elif test_frameworks:
        if "unittest" in test_frameworks:
            stages["Test"] = ["python -m unittest discover"]
        elif "pytest" in test_frameworks:
            stages["Test"] = ["pytest"]

    # Lint stage
    if "lint" in scripts:
        lint_cmd = scripts["lint"].get("windows", scripts["lint"].get("unix", ""))
        if lint_cmd:
            stages["Lint"] = [lint_cmd]

    # Docker stage
    if dockerfile_present and "docker" in scripts:
        docker_cmd = scripts["docker"].get("windows", scripts["docker"].get("unix", ""))
        if docker_cmd:
            stages["Build Docker Image"] = [docker_cmd]
    elif dockerfile_present:
        stages["Build Docker Image"] = ["docker build -t app:latest ."]

    # Deploy stage
    if "deploy" in scripts:
        deploy_cmd = scripts["deploy"].get("windows", scripts["deploy"].get("unix", ""))
        if deploy_cmd:
            stages["Deploy"] = [deploy_cmd]

    return stages
def remove_docker_stages(stage_blocks):
    """Удаляет stage-блоки, связанные с Docker."""
    return [
        stage for stage in stage_blocks
        if not re.search(r"stage\s*\(\s*['\"][^'\"]*[Dd]ocker[^'\"]*['\"]\s*\)", stage)
    ]
def extract_stage_blocks(pipeline: str):
    """Извлекает все stage('...'){...} блоки как есть (с вложенными скобками)."""
    stages = []
    regex = re.compile(r'(stage\s*\(\s*[\'"][^\'"]+[\'"]\s*\)\s*\{)', re.MULTILINE)
    pos = 0
    while True:
        m = regex.search(pipeline, pos)
        if not m:
            break
        start = m.start()
        brace_count = 0
        in_string = False
        escape = False
        for i in range(start, len(pipeline)):
            c = pipeline[i]
            if c == '{' and not in_string:
                brace_count += 1
            elif c == '}' and not in_string:
                brace_count -= 1
                if brace_count == 0:
                    stages.append(pipeline[start:i+1])
                    pos = i + 1
                    break
            elif c in ("'", '"'):
                if not escape:
                    in_string = not in_string
            escape = (c == '\\' and not escape)
        else:
            break
    return stages
def format_jenkins_pipeline(raw_pipeline: str, input_json: dict) -> str:
    """Формирует рабочий Jenkinsfile на основе результата ИИ и json-конфига."""

    # 1. Парсим stage-блоки
    stage_blocks = extract_stage_blocks(raw_pipeline)
    # 1.1. Удаляем docker stage если dockerfilePresent == False
    dockerfile_present = input_json.get("input", {}).get("project", {}).get("dockerfilePresent", False)
    if not dockerfile_present:
        stage_blocks = remove_docker_stages(stage_blocks)
    # 2. Получаем команды для stage из json
    stage_cmds = extract_stage_steps(input_json)

    # 3. Для каждого блока stage, обновляем steps по json (если надо)
    fixed_stage_blocks = []
    for stage in stage_blocks:
        # Получаем название stage
        m = re.match(r'stage\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)\s*\{', stage)
        if m:
            name = m.group(1)
            cmds = stage_cmds.get(name)
            if cmds:
                # Заменяем весь steps-блок на нужные команды
                stage = re.sub(
                    r'steps\s*\{[^\}]*\}',
                    'steps {\n' + '\n'.join(f'    bat \'{cmd}\'' for cmd in cmds) + '\n}',
                    stage,
                    flags=re.DOTALL
                )
        fixed_stage_blocks.append(stage)

    # 4. Собираем stages-блок
    stages_block = '    stages {\n'
    for stage in fixed_stage_blocks:
        for line in stage.splitlines():
            stages_block += '        ' + line.rstrip() + '\n'
    stages_block += '    }'

    # 5. agent, environment
    env_block = '    environment {\n        BUILD_TAG = "${env.BUILD_ID}"\n        PYTHON_VERSION = \'3.9\'\n        PIP_CACHE_DIR = \'.pip-cache\'\n    }\n'

    # 6. post
    post_block = '''
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Build for python succeeded with tag ${BUILD_TAG}!'
        }
        failure {
            echo 'Build for python failed with tag ${BUILD_TAG}!'
        }
    }
    '''.strip('\n')

    # 7. Итоговый pipeline
    result = 'pipeline {\n'
    result += '    agent any\n'
    result += env_block + '\n'
    result += stages_block + '\n'
    result += post_block + '\n'
    result += '}'

    # 8. Финальная чистка
    result = re.sub(r'\n\s*\n', '\n', result)
    result = re.sub(r'[ \t]+$', '', result, flags=re.MULTILINE)
    open_c = result.count('{')
    close_c = result.count('}')
    if close_c < open_c:
        result += '\n' + ('}' * (open_c - close_c))
    elif open_c < close_c:
        result = result.rstrip('}' * (close_c - open_c))
    
    return result

def validate_pipeline_structure(pipeline: str) -> List[str]:
    """Возвращает список найденных проблем в pipeline."""
    issues = []

    if not re.search(r'pipeline\s*\{', pipeline):
        issues.append("Отсутствует основной блок pipeline")

    if not re.search(r'agent\s+any', pipeline):
        issues.append("Отсутствует agent any")

    if not re.search(r'stages\s*\{', pipeline):
        issues.append("Отсутствует блок stages")

    open_count = pipeline.count('{')
    close_count = pipeline.count('}')
    if open_count != close_count:
        issues.append(f"Несоответствие скобок: {open_count} открывающих, {close_count} закрывающих")

    bad_quotes = re.findall(r"(bat|sh)\s+''[^']*''", pipeline)
    if bad_quotes:
        issues.append(f"Найдены двойные кавычки в командах: {len(bad_quotes)} случаев")

    # Проверяем наличие пустых steps
    empty_steps = re.findall(r"steps\s*\{\s*\}", pipeline)
    if empty_steps:
        issues.append(f"Найдены пустые steps блоки: {len(empty_steps)} случаев")

    # Проверяем наличие дублирующихся steps
    duplicate_steps = re.findall(r"steps\s*\{[^}]*\}\s*steps\s*\{", pipeline, flags=re.DOTALL)
    if duplicate_steps:
        issues.append(f"Найдены дублирующиеся steps блоки: {len(duplicate_steps)} случаев")

    return issues
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
# Пример использования с входной конфигурацией
def test():
    """Пример использования функций постобработки"""
    
    # Входная конфигурация
    input_json = {
        "instruction": "Generate a Jenkins pipeline for the given project configuration",
        "input": {
            "project": {
                "type": "python",
                "buildTool": "pip",
                "testFrameworks": ["unittest"],
                "dockerfilePresent": False,
                "files": [
                    "config/cfg.py",
                    "config/__init__.py",
                    "gui/main_window.py",
                    "gui/startmenu.py",
                    "gui/Threads/CallbackThread.py"
                ],
                "dependencies": [
                    "altgraph==0.17.4",
                    "cffi==1.16.0",
                    # ... остальные зависимости
                ],
                "scripts": {
                    "build": {
                        "unix": "pip install -r requirements.txt",
                        "windows": "pip install -r requirements.txt"
                    },
                    "test": {
                        "unix": "pytest",
                        "windows": "pytest"
                    },
                    "lint": {
                        "unix": "flake8 .",
                        "windows": "flake8 ."
                    }
                }
            }
        }
    }
    
    # Исходный сломанный pipeline
    broken_pipeline = """
    pipeline {
        agent any
        environment {
            BUILD_TAG = 'a9b9b9b9'
        }
        stages {
            stage('Build') {
                steps {
                    bat ''pip''
                }
            }
            stage('Deploy') {
        steps { echo 'TODO' }
    }
                }
                steps {
                    bat ''echo Deploying to staging''
                }
            }
            stage('Test') {
                steps {
                    bat ''unittest''
                }
            }
        }
    }
    """
    
    # Исправление pipeline
    fixed_pipeline = fix_jenkins_pipeline(broken_pipeline, input_json)
    
    # Валидация
    issues = validate_pipeline_structure(fixed_pipeline)
    
    print("Исправленный pipeline:")
    print(fixed_pipeline)
    print(f"\nНайдено проблем: {len(issues)}")
    for issue in issues:
        print(f"- {issue}")
    return fixed_pipeline
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument('--test', default=False)
    parser.add_argument("--model-path", default="./codet5p_finetuned")
    args = parser.parse_args()
    if args.test:
        pipeline = test()
        """Возвращает список найденных проблем в pipeline"""
        issues = []
        
        # Проверяем основную структуру
        if not re.search(r'pipeline\s*\{', pipeline):
            issues.append("Отсутствует основной блок pipeline")
        
        if not re.search(r'agent\s+any', pipeline):
            issues.append("Отсутствует agent any")
        
        if not re.search(r'stages\s*\{', pipeline):
            issues.append("Отсутствует блок stages")
        
        # Проверяем вложенность скобок
        open_count = pipeline.count('{')
        close_count = pipeline.count('}')
        if open_count != close_count:
            issues.append(f"Несоответствие скобок: {open_count} открывающих, {close_count} закрывающих")
        
        # Проверяем кавычки в командах
        bad_quotes = re.findall(r"(bat|sh)\s+''[^']*''", pipeline)
        if bad_quotes:
            issues.append(f"Найдены двойные кавычки в командах: {len(bad_quotes)} случаев")
        
        return issues
    else:
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
            fixed_pipeline = format_jenkins_pipeline(generated_pipeline, input_json)

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
