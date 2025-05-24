# app/core/settings.py
from pydantic_settings import BaseSettings # Изменено для Pydantic v2
from pydantic import Field, validator
from typing import Optional, List, Union

class Settings(BaseSettings):
    # Базовые параметры приложения
    app_name: str = "LLM Pipeline Server"
    debug: bool = Field(default=False, env="DEBUG")
    env: str = Field(default="dev", env="ENV")
    host: str = Field(default="127.0.0.1", env="HOST")
    port: int = Field(default=8000, env="PORT")
    # Пути
    app_config_path: str = Field(default="config.yaml", env="APP_CONFIG_PATH")
    models_config_dir: str = Field(default="models_configuration", env="MODELS_CONFIG_DIR")

    huggingface_token: Optional[str] = Field(default=None, env="HUGGINGFACE_TOKEN")  # <-- обязательно Optional и дефолт None!
    # База данных
    db_url: str = Field(default="sqlite+aiosqlite:///history.sqlite", env="DB_URL")

    # Логи
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="color", env="LOG_FORMAT")
    log_path: str = Field(default="logs/app.log", env="LOG_PATH")

    # Админ-пароль
    admin_password: Optional[str] = Field(default="admin", env="ADMIN_PASSWORD")

    # Безопасность/лимиты
    max_request_length: int = Field(default=8192, env="MAX_REQUEST_LENGTH")
    max_context: int = Field(default=4096, env="MAX_CONTEXT")
    max_history_days: int = Field(default=30, env="MAX_HISTORY_DAYS")

    # CORS
    cors_origins: Union[str, List[str]] = Field(default="*", env="CORS_ORIGINS")

    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            # Если это строка и не похожа на список (например, "*"),
            # или если это строка с запятыми, то преобразуем в список
            if v == "*": # Специальный случай для FastAPI - "*" должен быть строкой
                return v
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)): # Если это уже список или строка, похожая на список (например "['http://localhost']")
            return v
        raise ValueError(v)

    # (расширить по мере надобности)
    # smtp_server: Optional[str] = Field(default=None, env="SMTP_SERVER")
    # s3_bucket: Optional[str] = Field(default=None, env="S3_BUCKET")
    # oauth_client_id: Optional[str] = Field(default=None, env="OAUTH_CLIENT_ID")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # <-- если хочешь разрешить любые ENV-поля

settings = Settings()
