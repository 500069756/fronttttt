"""Restaurant Recommendation System.

Phase-based architecture:
- Phase 1: Foundation & Data Layer (data loading, preprocessing)
- Phase 2: Core Recommendation Engine (filtering, ranking, LLM)
- Phase 3: API & Service Layer (REST API)
- Phase 4: User Interface Layer (Streamlit frontend)
"""
__version__ = "1.0.0"

# Phase 1: Foundation & Data Layer
from .phase1_foundation import DataLoader, DataPreprocessor, setup_logging, format_currency

# Phase 2: Core Recommendation Engine
from .phase2_engine import RestaurantFilter, RestaurantRanker, LLMClient, PromptTemplates

__all__ = [
    # Phase 1
    "DataLoader",
    "DataPreprocessor",
    "setup_logging",
    "format_currency",
    # Phase 2
    "RestaurantFilter",
    "RestaurantRanker",
    "LLMClient",
    "PromptTemplates",
]
