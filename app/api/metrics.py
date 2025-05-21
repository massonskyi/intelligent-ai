# app/api/metrics.py
from fastapi import APIRouter, Response
from services.metrics_service import metrics_service

router = APIRouter()

@router.get("/prometheus", response_class=Response, tags=["metrics"])
async def prometheus_metrics():
    """Возвращает метрики в формате Prometheus."""
    data = await metrics_service.get_metrics()
    lines = []
    lines.append(f'# HELP llm_total_requests Total LLM requests')
    lines.append(f'# TYPE llm_total_requests counter')
    lines.append(f'llm_total_requests {data["total_requests"]}')
    lines.append(f'# HELP llm_total_tokens Total generated tokens')
    lines.append(f'# TYPE llm_total_tokens counter')
    lines.append(f'llm_total_tokens {data["total_tokens"]}')
    lines.append(f'# HELP llm_avg_latency_ms Average request latency (ms)')
    lines.append(f'# TYPE llm_avg_latency_ms gauge')
    lines.append(f'llm_avg_latency_ms {data["avg_latency_ms"]:.3f}')
    # По моделям
    for model, stats in data["models_stats"].items():
        lines.append(f'# HELP llm_model_requests_total Requests per model')
        lines.append(f'# TYPE llm_model_requests_total counter')
        lines.append(f'llm_model_requests_total{{model="{model}"}} {stats["requests"]}')
        lines.append(f'# HELP llm_model_tokens_total Tokens per model')
        lines.append(f'# TYPE llm_model_tokens_total counter')
        lines.append(f'llm_model_tokens_total{{model="{model}"}} {stats["tokens"]}')
        lines.append(f'# HELP llm_model_avg_latency_ms Average latency per model (ms)')
        lines.append(f'# TYPE llm_model_avg_latency_ms gauge')
        lines.append(f'llm_model_avg_latency_ms{{model="{model}"}} {stats["avg_latency_ms"]:.3f}')
    return Response("\n".join(lines), media_type="text/plain")
