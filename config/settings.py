"""Centralized configuration management for the restaurant recommendation system."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = Path(__file__).parent.parent
DATA_CACHE_DIR = Path(os.getenv("DATA_CACHE_DIR", BASE_DIR / "data_cache"))
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
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_API_BASE = os.getenv("GROK_API_BASE", "https://api.groq.com/openai/v1")
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
