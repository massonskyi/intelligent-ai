# app/core/config.py
import threading
from typing import Dict, Any, Callable, final
from pydantic import BaseModel, Field
import yaml
import os
import glob

MODELS_DIR = os.environ.get("MODELS_CONFIG_DIR", "models_configuration")

@final
class LLMModelConfig(BaseModel):
    name: str
    type: str  # 'llama_cpp' | 'transformers' | etc
    model_path: str
    params: Dict[str, Any] = Field(default_factory=dict)
    temperature: float = 0.7
    top_p: float = 0.95
    # Можно добавить другие runtime-настройки

@final
class AppConfig(BaseModel):
    max_context: int = 4096
    history_db: str = "history.sqlite"
    admin_password: str = "admin"
    # models: dict = {}
    default_model: str = "deepseek-r1-qwen-14b"   # значение по умолчанию
    # Можно расширить по мере надобности

def load_all_model_configs(dir_path="models_configuration") -> dict:
    configs = {}
    for fname in os.listdir(dir_path):
        if fname.endswith(".yaml"):
            with open(os.path.join(dir_path, fname), "r") as f:
                data = yaml.safe_load(f)
                # можно поддержать разные структуры (в файле как объект или под ключом "model")
                if "name" in data:
                    model_cfg = LLMModelConfig(**data)
                    configs[model_cfg.name] = model_cfg
                elif "model" in data:
                    model_cfg = LLMModelConfig(**data["model"])
                    configs[model_cfg.name] = model_cfg
    return configs
@final
class ConfigStore:
    """Singleton для server-wide config и моделей. Thread-safe. Live-reload."""
    _instance = None
    _lock = threading.Lock()
    _config_path = "config.yaml"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._lock = threading.Lock()
        self._subscribers: list[Callable[[Any], None]] = []
        self._models: Dict[str, LLMModelConfig] = {}    # name -> config
        self._model_files: Dict[str, str] = {}          # name -> yaml path
        self._load_app_config()
        self._load_models()

    def _load_app_config(self):
        path = os.environ.get("APP_CONFIG_PATH", self._config_path)
        if os.path.exists(path):
            with open(path, "r") as f:
                data = yaml.safe_load(f)
        else:
            data = {}
        admin_pass = os.environ.get("ADMIN_PASSWORD")
        if admin_pass:
            data["admin_password"] = admin_pass
        self.app_config = AppConfig(**data)

    def _load_models(self):
        self._models.clear()
        self._model_files.clear()
        for file in glob.glob(f"{MODELS_DIR}/*.yaml"):
            with open(file, "r") as f:
                d = yaml.safe_load(f)
                model_cfg = LLMModelConfig(**d)
                self._models[model_cfg.name] = model_cfg
                self._model_files[model_cfg.name] = file

    def reload_models(self):
        """Reload all model configs from disk."""
        with self._lock:
            self._load_models()
            self._notify()

    def reload_app_config(self):
        with self._lock:
            self._load_app_config()
            self._notify()

    def get_app_config(self) -> AppConfig:
        return self.app_config

    def get_model_config(self, name: str) -> LLMModelConfig:
        return self._models[name]

    def get_all_model_configs(self) -> Dict[str, LLMModelConfig]:
        return dict(self._models)

    def set_model_param(self, model_name: str, param: str, value: Any):
        """Update a param for given model and save to YAML."""
        with self._lock:
            if model_name not in self._models:
                raise KeyError(f"Model {model_name} not found")
            setattr(self._models[model_name], param, value)
            self._save_model_config(model_name)
            self._notify()

    def add_or_update_model(self, cfg: LLMModelConfig, file_path: str = None):
        """Add or update a model config, save to YAML (file_path is optional)."""
        with self._lock:
            self._models[cfg.name] = cfg
            if not file_path:
                # Auto-generate file path
                file_path = os.path.join(MODELS_DIR, f"{cfg.name}.yaml")
            self._model_files[cfg.name] = file_path
            self._save_model_config(cfg.name)
            self._notify()
    def get_default_model(self) -> str:
        # Если явно задано — вернуть его, иначе первый из models
        return getattr(self.app_config, "default_model", None) or (next(iter(self._models)) if self._models else None)

    def set_default_model(self, model_name: str):
        if model_name not in self._models:
            raise ValueError(f"Model {model_name} not found")
        self.app_config.default_model = model_name
        self._save_app_config()
        self._notify()

    def _save_app_config(self):
        path = os.environ.get("APP_CONFIG_PATH", self._config_path)
        with open(path, "w") as f:
            yaml.safe_dump(self.app_config.dict(), f)

    def remove_model(self, model_name: str):
        """Remove model from registry and optionally delete yaml file."""
        with self._lock:
            if model_name in self._models:
                file_path = self._model_files.get(model_name)
                self._models.pop(model_name)
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                self._model_files.pop(model_name, None)
                self._notify()

    def _save_model_config(self, model_name: str):
        """Save single model config to its YAML file."""
        cfg = self._models[model_name]
        file_path = self._model_files[model_name]
        with open(file_path, "w") as f:
            yaml.safe_dump(cfg.dict(), f)

    def subscribe(self, callback):
        """Subscribe to config changes (for runners, admin UI, etc)."""
        self._subscribers.append(callback)

    def _notify(self):
        for sub in self._subscribers:
            sub(self)

    # Если нужен API для параметров/моделей сразу в dict
    def dict(self):
        return {
            "app": self.app_config.dict(),
            "models": {n: m.dict() for n, m in self._models.items()}
        }

# Глобальный DI/Store
config_store = ConfigStore()
