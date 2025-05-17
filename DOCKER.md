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
docker run --gpus all \
           --rm \
           -p 8000:8000 \         # хост:контейнер
           --name ai-pipeline \
           ai-pipeline-server:gpu     # или :latest, если так собрали

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