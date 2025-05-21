# Llama Pipeline Generator

## Features

- Кроссплатформенный запуск (Windows + Linux)
- Быстрый inference через llama.cpp (gguf модели)
- Docker-образ для CPU (поддержка CUDA в планах)
- Пример генерации Jenkins pipeline по описанию проекта

## Запуск

### 1. Конвертируй модель (см. README llama.cpp)
### 2. Запусти:
```bash
python main.py
```

### 3. Для Docker

docker build -t llama-pipeline .
docker run -v /your/models:/models llama-pipeline

### 4. Для Windows — укажи путь к GGUF в main.py


---

## **Примечания**

- Модели `.gguf` идентичны для Linux и Windows.
- llama-cpp-python умеет использовать CUDA, если сборка поддерживает (требует ручной сборки llama.cpp с CUBLAS/DirectML).
- Для масштабирования просто деплой через Docker, CI для проверки кода.

---

## **Расширения**
- Добавить web API (FastAPI/Flask), чтобы делать pipeline generation REST-запросами.
- Добавить поддержку авто-скачивания моделей с HuggingFace и автоконверта в GGUF.

---

**Если нужно что-то ещё (webapi, fastapi, docker compose, автоматизация скачивания моделей) — скажи!  
Если нужна CUDA-интеграция или инструкция для GPU-билда под Windows — тоже подскажу.**