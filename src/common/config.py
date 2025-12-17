"""Configuration loader for YAML config files."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: str, env: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
        env: Optional environment name (overrides config)
    
    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    # Override with environment variables if specified
    if env:
        env_config_path = config_file.parent / f"{env}.yaml"
        if env_config_path.exists():
            with open(env_config_path, "r", encoding="utf-8") as f:
                env_config = yaml.safe_load(f) or {}
                config = _merge_config(config, env_config)
    
    # Load environment variables for sensitive data
    config = _load_env_vars(config)
    
    return config


def _merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two configuration dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    
    return result


def _load_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load environment variables for API keys and sensitive data."""
    # OpenAI API Key
    if "llm" in config and "api_key" not in config["llm"]:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            config["llm"]["api_key"] = api_key
    
    if "embedding" in config and "api_key" not in config["embedding"]:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            config["embedding"]["api_key"] = api_key
    
    return config


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get configuration value using dot notation.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated key path (e.g., "llm.model")
        default: Default value if key not found
    
    Returns:
        Configuration value or default
    """
    keys = key_path.split(".")
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value

