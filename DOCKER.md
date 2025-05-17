# Запуск в Docker

Этот документ содержит инструкции по запуску Jenkins Pipeline Generator с использованием Docker и Docker Compose.

## Предварительные требования

- Docker
- Docker Compose
- Модель машинного обучения, находящаяся в директории `model/final/`

## Быстрый запуск

```bash
# Запустить приложение с Docker Compose
docker-compose up -d

# Проверить логи
docker-compose logs -f
```

## Сборка и запуск вручную

Если вы хотите собрать и запустить контейнер вручную:

```bash
# Собрать образ
docker build -t jenkins-pipeline-generator .

# Запустить контейнер
docker run -d \
  --name jenkins-pipeline-generator \
  -p 8000:8000 \
  -v $(pwd)/model:/app/model \
  -e HOST=0.0.0.0 \
  -e PORT=8000 \
  -e MODEL_PATH=model/final \
  -e MODEL_NAME=t5-small \
  -e MAX_LENGTH=100 \
  -e DEBUG=true \
  -e ENVIRONMENT=production \
  jenkins-pipeline-generator
```

## Доступ к API

После запуска контейнера API будет доступен по адресу:

- http://localhost:8000/generate-pipeline - для генерации Jenkinsfile
- http://localhost:8000/demo-format - для демонстрации форматирования

## Остановка и очистка

```bash
# Остановить контейнеры
docker-compose down

# Удалить образ (при необходимости)
docker rmi jenkins-pipeline-generator
```

## Структура томов

Директория `model` монтируется внутрь контейнера, чтобы не включать большие файлы модели в образ Docker.
Убедитесь, что модель находится в директории `model/final/` на хосте перед запуском контейнера. 