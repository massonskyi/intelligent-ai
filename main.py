import argparse
import json
from pathlib import Path
import sys
from huggingface_hub import snapshot_download
import os
from src.utils import log, log_exc
from src.codet5p_formatter import *

REPO_ID = "masonskiy/codet5p-200m-jenkins-pipeline"
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


log(f"[PYTHON EXECUTABLE] {sys.executable}")
log(f"[VIRTUAL ENV] {os.environ.get('VIRTUAL_ENV')}")
log(f"[WORKDIR] {os.getcwd()}")

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
