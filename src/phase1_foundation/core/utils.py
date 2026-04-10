"""Core utility functions for the restaurant recommendation system."""
import logging
from typing import Any, Dict, List, Optional


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Setup logging configuration.
    
    Args:
        level: Logging level
        
    Returns:
        Configured logger
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def validate_preferences(preferences: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate user preferences.
    
    Args:
        preferences: Dictionary of user preferences
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_budgets = ['low', 'medium', 'high']
    
    if 'budget' in preferences and preferences['budget'] not in valid_budgets:
        return False, f"Invalid budget. Must be one of: {valid_budgets}"
    
    if 'min_rating' in preferences:
        rating = preferences['min_rating']
        if not isinstance(rating, (int, float)) or rating < 0 or rating > 5:
            return False, "Invalid rating. Must be between 0 and 5"
    
    if 'top_n' in preferences:
        top_n = preferences['top_n']
        if not isinstance(top_n, int) or top_n < 1 or top_n > 50:
            return False, "Invalid top_n. Must be between 1 and 50"
    
    return True, None


def format_currency(amount: float) -> str:
    """Format amount as currency string.
    
    Args:
        amount: Amount to format
        
    Returns:
        Formatted currency string
    """
    return f"₹{amount:,.0f}"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
