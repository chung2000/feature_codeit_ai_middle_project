"""Utility functions for file I/O, data validation, etc."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


def ensure_dir(dir_path: str) -> Path:
    """
    Ensure directory exists, create if not.
    
    Args:
        dir_path: Directory path
    
    Returns:
        Path object
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_file(file_path: str, required: bool = True) -> bool:
    """
    Validate that file exists.
    
    Args:
        file_path: File path to validate
        required: If True, raise error if file doesn't exist
    
    Returns:
        True if file exists, False otherwise
    
    Raises:
        FileNotFoundError: If required=True and file doesn't exist
    """
    path = Path(file_path)
    exists = path.exists() and path.is_file()
    
    if required and not exists:
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    return exists


def save_json(data: Any, file_path: str, indent: int = 2) -> None:
    """Save data to JSON file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_json(file_path: str) -> Any:
    """Load data from JSON file."""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jsonl(data: List[Dict], file_path: str) -> None:
    """Save list of dictionaries to JSONL file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def load_jsonl(file_path: str) -> List[Dict]:
    """Load JSONL file and return list of dictionaries."""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {file_path}")
    
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    
    return data


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    return Path(file_path).stat().st_size


def get_file_extension(file_path: str) -> str:
    """Get file extension (without dot)."""
    return Path(file_path).suffix[1:].lower()


def normalize_text(text: str) -> str:
    """
    Basic text normalization.
    
    Args:
        text: Input text
    
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Remove BOM
    text = text.lstrip("\ufeff")
    
    # Normalize whitespace (preserve newlines)
    lines = text.split("\n")
    normalized_lines = [" ".join(line.split()) for line in lines]
    text = "\n".join(normalized_lines)
    
    # Remove excessive newlines (more than 2 consecutive)
    import re
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text.strip()


def validate_metadata(metadata: Dict, required_fields: List[str]) -> bool:
    """
    Validate that metadata contains required fields.
    
    Args:
        metadata: Metadata dictionary
        required_fields: List of required field names
    
    Returns:
        True if all required fields present, False otherwise
    """
    return all(field in metadata for field in required_fields)

