"""Centralized configuration management for the restaurant recommendation system."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# PATHS
# =============================================================================
# We use .parent because this file is in config/
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_CACHE_DIR_PATH = os.getenv("DATA_CACHE_DIR", "")
if DATA_CACHE_DIR_PATH:
    DATA_CACHE_DIR = Path(DATA_CACHE_DIR_PATH)
else:
    DATA_CACHE_DIR = BASE_DIR / "data_cache"

# Ensure directory exists but handle potential permission issues gracefully
try:
    DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    # Fallback to current working directory if root is read-only
    DATA_CACHE_DIR = Path("data_cache")
    DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# API SETTINGS
# =============================================================================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# =============================================================================
# LLM SETTINGS (Groq API - OpenAI-compatible)
# =============================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_BASE = os.getenv("GROQ_API_BASE", "https://api.groq.com/openai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_MAX_TOKENS = 1000
LLM_TEMPERATURE = 0.7
LLM_TIMEOUT = 30

# =============================================================================
# DATA SETTINGS
# =============================================================================
DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"
MAX_RESTAURANTS = int(os.getenv("MAX_RESTAURANTS", "1000"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))

# =============================================================================
# BUSINESS LOGIC - BUDGET CATEGORIES
# =============================================================================
BUDGET_CATEGORIES = {
    "low": (0, 500),
    "medium": (500, 1500),
    "high": (1500, float("inf"))
}

# =============================================================================
# BUSINESS LOGIC - RATING THRESHOLDS
# =============================================================================
RATING_THRESHOLDS = {
    "excellent": 4.5,
    "good": 4.0,
    "average": 3.0,
    "poor": 0.0
}

# =============================================================================
# BUSINESS LOGIC - SCORING WEIGHTS
# =============================================================================
DEFAULT_WEIGHTS = {
    "rating": 0.35,      # Quality is most important
    "popularity": 0.25,  # Social proof matters
    "value": 0.20,       # Price-performance ratio
    "location": 0.10,    # Convenience
    "diversity": 0.10    # Preference matching
}

__all__ = [
    "BASE_DIR",
    "DATA_CACHE_DIR",
    "API_HOST",
    "API_PORT",
    "DEBUG",
    "GROQ_API_KEY",
    "GROQ_API_BASE",
    "LLM_MODEL",
    "LLM_MAX_TOKENS",
    "LLM_TEMPERATURE",
    "LLM_TIMEOUT",
    "DATASET_NAME",
    "MAX_RESTAURANTS",
    "CACHE_TTL",
    "BUDGET_CATEGORIES",
    "RATING_THRESHOLDS",
    "DEFAULT_WEIGHTS",
]
