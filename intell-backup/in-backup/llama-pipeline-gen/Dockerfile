FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY main.py ./

# Монтируй свою модель в /models/ через docker run -v /your/models:/models
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
