# src/server/server.py
import shutil
import tarfile
import tempfile
import json, os, signal, asyncio, time
from typing import Any, Dict, Union
import zipfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from src.engine.model_fetcher import ensure_model
from src.model_handler import JenkinsPipelineGenerator
from src.engine.analyze_project import analyze_async
from src.server.models import PipelineRequest, AnalyzeResp
from src.settings import get_settings

app = FastAPI(title="Jenkins Pipeline Generator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

generator = JenkinsPipelineGenerator()


@app.on_event("startup")
async def on_startup():
    """Загружаем модель один раз при поднятии контейнера."""
    app.state.started_at = time.time()
    settings = get_settings()
    # 1) синхронная проверка/загрузка модели
    ensure_model(settings.MODEL_PATH)
    # 2) асинхронно инициализируем веса
    await generator.initialize()


# ─────────── health-check — Jenkins ждёт 200 OK ────────────
@app.get("/healthz", summary="Health probe")
async def healthz():
    return {"status": "ok", "uptime": round(time.time() - app.state.started_at, 1)}


# ─────────── основная генерация ───────────
@app.post("/generate-pipeline", summary="Сгенерировать Jenkinsfile")
async def generate_pipeline(req: PipelineRequest):
    try:
        project_json = req.input if isinstance(req.input, str) else json.dumps(req.input)
        pipeline = await generator.generate_pipeline(project_json)
        return {"pipeline": pipeline}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ─────────── демо-форматирование ───────────
@app.post("/demo-format", summary="Форматировать Jenkinsfile только для демо")
async def demo_format(req: PipelineRequest):
    try:
        project_json = req.input if isinstance(req.input, str) else json.dumps(req.input)
        formatted = await generator.demo_formatter(project_json)
        return {"formatted_pipeline": formatted}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ─────────── graceful-shutdown по запросу плагина ───────────
@app.post("/shutdown", summary="Остановить сервер")
async def shutdown():
    """
    Jenkins-плагин отправит POST /shutdown, когда сборка закончилась.
    Контейнер гасится мягко — сначала отдаём ответ, затем SIGINT uvicorn’у.
    """
    loop = asyncio.get_event_loop()
    loop.call_later(1, lambda: os.kill(os.getpid(), signal.SIGINT))
    return {"detail": "shutting-down"}

@app.post("/analyze", response_model=AnalyzeResp,
          summary="Сканирует репозиторий и возвращает JSON для модели")
async def analyze_repo(archive: UploadFile = File(...)):
    """
    Плагин пересылает tar/zip с рабочей директорией.
    Сервер разархивирует во временную папку, запускает анализ и
    отдаёт JSON (тот же, что потом пойдёт на /generate-pipeline).
    """
    # 1. сохраняем архив во временный файл
    with tempfile.TemporaryDirectory() as tmp:
        a_path = Path(tmp, archive.filename)
        with open(a_path, "wb") as f:
            shutil.copyfileobj(archive.file, f)

        # 2. распаковываем
        repo_dir = Path(tmp, "repo")
        repo_dir.mkdir()
        if tarfile.is_tarfile(a_path):
            with tarfile.open(a_path) as tar:
                tar.extractall(repo_dir)
        elif zipfile.is_zipfile(a_path):
            with zipfile.ZipFile(a_path) as z:
                z.extractall(repo_dir)
        else:
            raise HTTPException(400, "Only tar or zip archives are supported")

        # 3. анализ
        try:
            analysis, h = await analyze_async(str(repo_dir))
            return {"analysis": analysis, "hash": h}
        except Exception as exc:
            raise HTTPException(500, str(exc))