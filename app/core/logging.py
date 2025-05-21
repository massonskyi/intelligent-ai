# app/core/logging.py
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_PATH = os.getenv("LOG_PATH", "logs/app.log")
LOG_FORMAT = os.getenv("LOG_FORMAT", "color")  # color | json | plain

# Цветной форматтер для консоли
class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",
        "INFO": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "CRITICAL": "\033[1;91m",
        "RESET": "\033[0m"
    }
    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["RESET"]
        msg = super().format(record)
        return f"{color}{msg}{reset}"

# JSON форматтер (минимальный, можно заменить на python-json-logger для prod)
class JsonFormatter(logging.Formatter):
    import json
    def format(self, record):
        d = {
            "level": record.levelname,
            "time": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "name": record.name,
            "msg": record.getMessage(),
            "file": record.pathname,
            "line": record.lineno,
        }
        return self.json.dumps(d)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    # Удаляем старые хендлеры
    for h in logger.handlers[:]:
        logger.removeHandler(h)

    if LOG_FORMAT == "json":
        formatter = JsonFormatter()
    elif LOG_FORMAT == "plain":
        formatter = logging.Formatter(
            "[%(levelname)s] %(asctime)s %(name)s:%(lineno)d - %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )
    else:  # color
        formatter = ColorFormatter(
            "[%(levelname)s] %(asctime)s %(name)s:%(lineno)d - %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )

    # Консоль
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Файл (c ротацией, если не test/dev)
    if LOG_PATH:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        file_handler = RotatingFileHandler(LOG_PATH, maxBytes=5*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Отдельно логгер uvicorn, чтобы не дублировались запросы
    logging.getLogger("uvicorn.access").propagate = False

    logger.info(f"Logging setup: level={LOG_LEVEL}, format={LOG_FORMAT}, file={LOG_PATH}")

def get_logger(name=None):
    return logging.getLogger(name or "app")

# Автоматически инициализировать при старте
setup_logging()
