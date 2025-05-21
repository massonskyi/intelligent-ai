import logging
import sys
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
import queue
import os

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.log')

def setup_logging(log_level=logging.INFO):
    """Настраивает сквозное логирование в консоль и файл."""
    
    # Убираем все существующие обработчики у корневого логгера, чтобы избежать дублирования
    # если эта функция вызывается несколько раз (например, при перезагрузке uvicorn).
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        for handler in root_logger.handlers[:]: # Итерируемся по копии списка
            root_logger.removeHandler(handler)
            handler.close() # Закрываем обработчик

    # Форматтер
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    )

    # Консольный обработчик (синхронный, т.к. вывод в stdout/stderr обычно быстрый)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level)

    # Файловый обработчик (будет использоваться через QueueListener)
    # Ротация: 5 файлов по 5MB каждый
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)

    # Очередь для асинхронной передачи логов файловому обработчику
    log_queue = queue.Queue(-1)  # Бесконечная очередь

    # QueueHandler отправляет логи в очередь
    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(log_level)
    
    # QueueListener слушает очередь в отдельном потоке и передает файловому обработчику
    # Это делает запись в файл неблокирующей для основного потока.
    # Добавляем и консольный, и файловый обработчики в listener,
    # но корневой логгер будет использовать QueueHandler для всего,
    # а listener будет распределять.
    # Однако, для простоты, консольный обработчик можно оставить синхронным и добавить напрямую к root_logger.
    # Файловый обработчик сделаем асинхронным.
    
    listener = QueueListener(log_queue, file_handler, respect_handler_level=True)
    listener.start() # Запускаем listener в фоновом потоке

    # Настройка корневого логгера
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler) # Синхронный вывод в консоль
    root_logger.addHandler(queue_handler)   # Асинхронный вывод в файл через очередь

    # Важно: зарегистрировать остановку listener при завершении программы
    # Это можно сделать через atexit, но для FastAPI лучше использовать shutdown event.
    # Мы вернем listener, чтобы его можно было остановить при завершении работы FastAPI.
    
    logging.info(f"Логирование настроено. Уровень: {logging.getLevelName(log_level)}. Файл: {LOG_FILE_PATH}")
    
    return listener

def get_logger(name: str):
    """Вспомогательная функция для получения логгера."""
    return logging.getLogger(name)

