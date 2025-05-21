# ======================
# Пример использования:
# ======================
import logging
from src.models.deepseek import DeepSeekModel
from src.utils.logging_config import get_logger
logger = get_logger(__name__)

if __name__ == "__main__":
    from src.utils.logging_config import setup_logging
    
    listener = setup_logging(log_level=logging.DEBUG)
    
    logger.info("Запуск примера использования DeepSeekModel...")
    
    try:
        model = DeepSeekModel("deepseek-ai/deepseek-llm-7b-base")
        prompt_example = "Write a Python function to calculate Fibonacci numbers up to n."
        logger.info(f"Тестовый промпт: {prompt_example}")
        
        response = model.inference(prompt_example, max_new_tokens=150)
        print("\nGenerated Response:\n", response)
        logger.info("Пример DeepSeekModel успешно выполнен.")
    except RuntimeError as e:
        logger.error(f"Ошибка выполнения примера: {e}")
    except Exception as e:
        logger.exception("Непредвиденная ошибка в примере DeepSeekModel.")
    finally:
        if 'listener' in locals() and listener:
            logger.info("Остановка QueueListener логирования...")
            listener.stop()
            logger.info("QueueListener остановлен.")
