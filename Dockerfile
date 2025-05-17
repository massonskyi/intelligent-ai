#######################################################################
#  Dockerfile — AI Pipeline Generator (GPU edition, CUDA 12.1)
#######################################################################

# ─────────────────────────────────────────────────────────────────────
# 1. БАЗОВЫЙ ОБРАЗ  (CUDA 12.1 Runtime + Ubuntu 22.04 LTS)
#    • содержит libcuda, libcudart и др.
#    • NVIDIA-драйвер на хосте должен быть ≥ 535
# ─────────────────────────────────────────────────────────────────────
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04 AS runtime

# ─────────────────────────────────────────────────────────────────────
# 2. СИСТЕМНЫЕ ПАКЕТЫ  (Python 3.10 + git)
# ─────────────────────────────────────────────────────────────────────
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3.10 python3.10-venv python3-pip git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # чтобы «python» → python3.10
    PATH=/usr/local/bin:/usr/local/sbin:/usr/local/cuda/bin:/usr/sbin:/usr/bin:/sbin:/bin

WORKDIR /app

# ─────────────────────────────────────────────────────────────────────
# 3. TORCH / VISION / AUDIO  c CUDA 12.1
#    — ставим до остальных зависимостей
# ─────────────────────────────────────────────────────────────────────
RUN python3.10 -m pip install --upgrade pip && \
    pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cu121 \
        torch==2.5.1+cu121 \
        torchvision==0.20.1+cu121 \
        torchaudio==2.5.1+cu121

# ─────────────────────────────────────────────────────────────────────
# 4. ОСНОВНОЙ requirements.txt
# ─────────────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────────────────────
# 5. КОД ПРИЛОЖЕНИЯ
# ─────────────────────────────────────────────────────────────────────
COPY . .

# ─────────────────────────────────────────────────────────────────────
# 6. НЕРУТОВЫЙ ПОЛЬЗОВАТЕЛЬ
# ─────────────────────────────────────────────────────────────────────
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# ─────────────────────────────────────────────────────────────────────
# 7. СТАРТ:  python -m src.main
#    (main.py проверяет модель и поднимает Uvicorn)
# ─────────────────────────────────────────────────────────────────────
ENTRYPOINT ["python3.10", "-m", "main"]
