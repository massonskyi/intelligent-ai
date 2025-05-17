# src/engine/model_fetcher.py
import os, shutil, logging
from pathlib import Path
from huggingface_hub import snapshot_download, HfApi

log = logging.getLogger(__name__)

REPO_ID = "masonskiy/codet5p-200m-jenkins-pipeline"

def ensure_model(model_dir: str):
    """
    Проверяет, есть ли файлы модели в `model_dir`.
    Если нет – скачивает их из HuggingFace Hub.
    Повторный вызов ничего не делает.
    """
    target = Path(model_dir)
    # «Есть ли хоть один файл весов?»
    if target.exists() and any(target.rglob("*.*")):
        log.info("Model directory %s already populated – skipping download", target)
        return

    log.info("Downloading model from HF hub → %s …", target)
    target.mkdir(parents=True, exist_ok=True)

    path = snapshot_download(
        repo_id=REPO_ID,
        local_dir_use_symlinks=False,     # безопасно для Windows и Docker
        resume_download=True
    )
    # копируем (snapshot_download кладёт в кеш ~/.cache/huggingface)
    for src in Path(path).rglob("*"):
        if src.is_file():
            rel = src.relative_to(path)
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    log.info("Model downloaded & copied to %s", target)
