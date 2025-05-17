# Jenkins Pipeline Generator

Интеллектуальный генератор Jenkinsfile на основе метаданных проекта с использованием моделей машинного обучения.

## Описание

Jenkins Pipeline Generator - это инструмент, который автоматически создает Jenkins-пайплайны на основе данных о проекте. Сервис анализирует метаданные проекта (язык программирования, инструменты сборки, тестовые фреймворки и т.д.) и генерирует оптимальный Jenkinsfile.

Основные возможности:
- Генерация Jenkinsfile на основе метаданных проекта
- Форматирование и структурирование пайплайна
- API для интеграции с другими инструментами
- Поддержка различных языков программирования и инструментов сборки

## Архитектура

Проект состоит из следующих компонентов:
- **Model Handler**: обработчик модели машинного обучения для генерации пайплайнов
- **API-сервер**: FastAPI для обработки HTTP-запросов
- **Форматтер пайплайнов**: компонент для форматирования и структурирования вывода

## Установка

### Предварительные требования

- Python 3.10+
- Модель T5 (должна находиться в директории `model/final/` или указана в настройках)

### Стандартная установка

```bash
# Клонирование репозитория
git clone https://github.com/your-username/jenkins-pipeline-generator.git
cd jenkins-pipeline-generator

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python main.py
```
## Установка модели

### Загрузка модели с Hugging Face

Модель размещена на Hugging Face в репозитории [masonskiy/JenkinsGeneratePipeline](https://huggingface.co/masonskiy/JenkinsGeneratePipeline).

#### Автоматическая загрузка

Для автоматической загрузки модели, используйте предоставленный скрипт:

```bash
# Установка зависимостей для загрузки
pip install huggingface_hub

# Загрузка модели
python download_model.py
```

#### Загрузка всех файлов из репозитория

Если вам нужны все файлы из репозитория Hugging Face:



#### Ручная загрузка

Вы также можете загрузить модель вручную:

1. Посетите [репозиторий модели](https://huggingface.co/masonskiy/JenkinsGeneratePipeline)
2. Скачайте файл `model.safetensors`
3. Поместите его в директорию `model/final/`

### Предварительные требования

- Python 3.10+
- huggingface_hub (`pip install huggingface_hub`)
### Запуск с Docker

Подробные инструкции по запуску в Docker доступны в файле [DOCKER.md](DOCKER.md).

```bash
# Быстрый запуск с Docker Compose
docker-compose up -d
```

## Использование

### API Endpoints

#### Генерация пайплайна

```http
POST /generate-pipeline
Content-Type: application/json

{
  "input_data": {
    "project": {
      "type": "java",
      "build_tool": "maven",
      "test_frameworks": ["junit5"],
      "dockerfile_present": true,
      "files": ["pom.xml", "src/main/java/App.java"],
      "dependencies": ["spring-boot"],
      "scripts": {"build": "mvn clean install"}
    }
  }
}
```

#### Демонстрация форматирования

```http
POST /demo-format
Content-Type: application/json

{
  "input_data": {
    "project": {
      "type": "java",
      "build_tool": "maven",
      "test_frameworks": ["junit5"]
    }
  }
}
```

### Пример ответа

```json
{
  "pipeline": "pipeline {\n    agent any\n    stages {\n        stage('Build') {\n            steps {\n                sh 'mvn clean install'\n            }\n        }\n        stage('Test') {\n            steps {\n                sh 'mvn test'\n            }\n        }\n    }\n}"
}
```

## Тестирование

Проект включает набор тестов для проверки функциональности:

```bash
# Установка зависимостей для тестирования
pip install -r tests/requirements-test.txt

# Запуск всех тестов
pytest tests/

# Запуск определенных тестов
pytest tests/test_api.py
pytest tests/test_model_handler.py
pytest tests/test_integration.py
```

## Настройка

Настройки можно изменить через переменные окружения:

| Переменная      | Описание                            | По умолчанию    |
|-----------------|-------------------------------------|-----------------|
| HOST            | Хост для сервера                    | 0.0.0.0         |
| PORT            | Порт для сервера                    | 8000            |
| MODEL_PATH      | Путь к модели                       | model/final     |
| MODEL_NAME      | Название модели                     | t5-small        |
| MAX_LENGTH      | Максимальная длина вывода           | 100             |
| DEBUG           | Режим отладки                       | true            |
| ENVIRONMENT     | Окружение (development/production)  | development     |

## Лицензия

Этот проект распространяется под лицензией MIT. См. файл LICENSE для получения дополнительной информации. 