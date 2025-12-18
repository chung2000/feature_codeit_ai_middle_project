import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

class ConfigLoader:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to local.yaml if not provided, or check env var
            config_path = os.getenv("CONFIG_PATH", "config/local.yaml")
        
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # Override with environment variables if necessary (simple implementation)
        # For example, override OPENAI_API_KEY if present in env (though usually handled by lib)
        return config

    @property
    def config(self) -> Dict[str, Any]:
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

# Singleton instance for easy access
# Usage: from src.common.config import config
# val = config.get("model.llm_name")
try:
    config_loader = ConfigLoader()
    config = config_loader.config
except Exception as e:
    print(f"Warning: Could not load default config: {e}")
    config = {}
