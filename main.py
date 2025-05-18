# """
# Entry-point для AI-сервиса генерации Jenkinsfile.
# Запускает Uvicorn, предварительно убеждаясь,
# что модель скачана и зависимости присутствуют.
# """
# import asyncio, logging, importlib.util, sys
# import uvicorn

# from src.settings import get_settings
# from src.engine.model_fetcher import ensure_model   # см. предыдущий ответ

# log = logging.getLogger("server.main")
# logging.basicConfig(level=logging.INFO,
#                     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


# def _ensure_python_multipart() -> None:
#     """
#     Проверяем, что модуль `multipart` доступен.
#     Если нет — ДАЁМ чёткую ошибку вместо RuntimeError глубоко в Starlette.
#     """
#     if importlib.util.find_spec("multipart") is None:
#         log.error(
#             'python-multipart не найден в среде %s\n'
#             'Установите его:  pip install python-multipart',
#             sys.executable,
#         )
#         sys.exit(1)


# async def main() -> None:
#     # 1. проверки окружения
#     _ensure_python_multipart()

#     settings = get_settings()
#     ensure_model(settings.MODEL_PATH)

#     # 2. старт Uvicorn
#     reload = settings.DEBUG and settings.ENVIRONMENT != "production"
#     log.info("Starting Uvicorn (reload=%s, workers=%d)…", reload, 1)
#     config = uvicorn.Config(
#         "src.server.server:app",
#         host=settings.HOST,
#         port=settings.PORT,
#         reload=reload,
#         workers=1,
#         log_level="info",
#     )
#     server = uvicorn.Server(config)
#     await server.serve()


# if __name__ == "__main__":
#     asyncio.run(main())
import argparse
import json
import sys
import asyncio
from src.engine.model_handler import JenkinsPipelineGenerator

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            input_json = json.load(f)

        generator = JenkinsPipelineGenerator()
        await generator.initialize()
        pipeline = await generator.generate_pipeline(input_json)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(pipeline)

        print(json.dumps({"status": "success"}))
    except Exception as e:
        print(json.dumps({"error": str(e), "status": "error"}))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
