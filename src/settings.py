from typing import final
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os
@final
class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/src/v1"
    PROJECT_NAME: str = "IntelligentAI"
    
    # Server Settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    
    # Model Settings
    MODEL_NAME: str = Field(default=f"{os.getcwd()}/codet5p_finetuned")
    MODEL_PATH: str = Field(default=f"{os.getcwd()}/codet5p_finetuned")
    print(MODEL_NAME)

    MAX_LENGTH: int = Field(default=2048)
    
    # Environment Settings
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    
    class Config:
        env_file = "base.env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance
    """
    return Settings()