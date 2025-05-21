# app/main.py
import asyncio
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from fastapi.responses import JSONResponse
from core.metrics_persist import metrics_persist_task
from services.metrics_service import metrics_service
from core.settings import settings
from core.logging import setup_logging, get_logger
from db.database import init_db
from api.llm import router as llm_router
from api.rag import router as rag_router
from api.admin import router as admin_router
from api.history import router as history_router
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: Restoring metrics from last snapshot...")
    await metrics_service.restore_from_last_snapshot()
    logger.info("Startup: Starting metrics persist background task.")
    
    task = asyncio.create_task(metrics_persist_task(metrics_service, interval_sec=300))
    yield
    logger.info("Shutdown: Cancelling metrics persist task.")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Shutdown: Persist task stopped.")

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,    # вот тут!
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"error": str(exc)})

Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)

app.include_router(llm_router, prefix="/llm", tags=["llm"])
app.include_router(rag_router, prefix="/llm", tags=["rag"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(history_router, prefix="/llm", tags=["history"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
