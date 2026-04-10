"""Phase 1: Foundation & Data Layer.

This phase includes:
- Data loading from HuggingFace
- Data preprocessing and cleaning
- Core utilities and configuration
"""
from .data.loader import DataLoader
from .data.preprocessor import DataPreprocessor
from .core.utils import setup_logging, validate_preferences, format_currency, truncate_text

__all__ = [
    "DataLoader",
    "DataPreprocessor",
    "setup_logging",
    "validate_preferences",
    "format_currency",
    "truncate_text"
]
