"""LLM client for Groq API integration.

Provides a high-level interface for making LLM calls with:
- Configurable model and parameters
- Error handling and fallback mechanisms
- Timeout and retry logic
- Response caching (optional)

Uses OpenAI-compatible API client for Groq (supports Llama models).
"""
import logging
from typing import Any, Dict, List, Optional
import json

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from config import (
    GROQ_API_KEY,
    GROQ_API_BASE,
    LLM_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    LLM_TIMEOUT
)
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with Groq LLM API.
    
    This class provides a simplified interface for making LLM calls
    with proper error handling, fallback mechanisms, and configuration.
    
    Attributes:
        api_key: Groq API key
        model: Model identifier (e.g., 'llama-3.3-70b-versatile')
        max_tokens: Maximum tokens in response
        temperature: Response randomness (0-2)
        timeout: Request timeout in seconds
        fallback_enabled: Whether to use fallback when LLM fails
        
    Example:
        >>> client = LLMClient()
        >>> explanation = await client.get_explanation(restaurant, preferences)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        fallback_enabled: bool = True
    ):
        """Initialize the LLM client.
        
        Args:
            api_key: Groq API key (defaults to env var)
            api_base: Groq API base URL (defaults to env var)
            model: Model to use (defaults to config)
            max_tokens: Max response tokens (defaults to config)
            temperature: Response temperature (defaults to config)
            timeout: Request timeout (defaults to config)
            fallback_enabled: Enable fallback responses when LLM fails
        """
        self.api_key = api_key if api_key is not None else GROQ_API_KEY
        self.api_base = api_base if api_base is not None else GROQ_API_BASE
        self.model = model if model is not None else LLM_MODEL
        self.max_tokens = max_tokens if max_tokens is not None else LLM_MAX_TOKENS
        self.temperature = temperature if temperature is not None else LLM_TEMPERATURE
        self.timeout = timeout if timeout is not None else LLM_TIMEOUT
        self.fallback_enabled = fallback_enabled
        
        self._client = None
        self._available = None
        
    def _get_client(self):
        """Lazy initialization of Groq API client (OpenAI-compatible)."""
        if self._client is None:
            try:
                from openai import OpenAI
                if self.api_key:
                    self._client = OpenAI(
                        api_key=self.api_key,
                        base_url=self.api_base
                    )
                    self._available = True
                else:
                    logger.warning("No Groq API key provided. LLM features disabled.")
                    self._available = False
            except ImportError:
                logger.warning("OpenAI package not installed. LLM features disabled.")
                self._available = False
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self._available = False
        
        return self._client
    
    def is_available(self) -> bool:
        """Check if LLM is available.
        
        Returns:
            True if LLM can be used, False otherwise
        """
        if self._available is None:
            self._get_client()
        return self._available
    
    def _make_request(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """Make a request to the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            LLM response text or None if failed
        """
        if not self.is_available():
            return None
        
        client = self._get_client()
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            return None
    
    def get_explanation(
        self,
        restaurant: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> str:
        """Get personalized explanation for a restaurant recommendation.
        
        Args:
            restaurant: Restaurant details
            user_preferences: User preferences
            
        Returns:
            Explanation string
        """
        prompt = PromptTemplates.explanation_prompt(restaurant, user_preferences)
        
        response = self._make_request(prompt)
        
        if response:
            return response
        
        # Fallback explanation
        if self.fallback_enabled:
            logger.info("Using fallback explanation")
            return PromptTemplates.fallback_explanation(restaurant)
        
        return "This restaurant matches your preferences."
    
    def get_summary(
        self,
        restaurants: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> str:
        """Get summary of restaurant recommendations.
        
        Args:
            restaurants: List of restaurants
            user_preferences: User preferences
            
        Returns:
            Summary string
        """
        prompt = PromptTemplates.summary_prompt(restaurants, user_preferences)
        
        response = self._make_request(prompt)
        
        if response:
            return response
        
        # Fallback summary
        if self.fallback_enabled:
            logger.info("Using fallback summary")
            return PromptTemplates.fallback_summary(restaurants, user_preferences)
        
        return f"Here are {len(restaurants)} restaurant recommendations for you."
    
    def re_rank(
        self,
        restaurants: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        top_n: int = 5
    ) -> List[int]:
        """Re-rank restaurants using LLM intelligence.
        
        Args:
            restaurants: List of restaurants to rank
            user_preferences: User preferences
            top_n: Number of top restaurants to return
            
        Returns:
            List of indices in recommended order
        """
        if len(restaurants) <= 1:
            return list(range(len(restaurants)))
        
        prompt = PromptTemplates.ranking_prompt(
            restaurants, user_preferences, top_n
        )
        
        response = self._make_request(prompt)
        
        if response:
            indices = PromptTemplates.parse_ranking_response(response)
            if indices:
                return indices[:top_n]
        
        # Fallback: return original order
        if self.fallback_enabled:
            logger.info("Using fallback ranking (original order)")
            return list(range(min(top_n, len(restaurants))))
        
        return list(range(len(restaurants)))
    
    def compare(
        self,
        restaurants: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> str:
        """Compare multiple restaurants.
        
        Args:
            restaurants: List of 2-3 restaurants to compare
            user_preferences: User preferences
            
        Returns:
            Comparison string
        """
        if len(restaurants) < 2:
            return "Need at least 2 restaurants to compare."
        
        if len(restaurants) > 3:
            restaurants = restaurants[:3]
        
        prompt = PromptTemplates.comparison_prompt(restaurants, user_preferences)
        
        response = self._make_request(prompt)
        
        if response:
            return response
        
        # Fallback comparison
        if self.fallback_enabled:
            lines = ["## Quick Comparison"]
            for r in restaurants:
                name = r.get("name", "Unknown")
                rating = r.get("rating", 0)
                cost = r.get("cost", 0)
                lines.append(f"- **{name}**: Rating {rating}/5, Cost ₹{cost}")
            
            lines.append("\n## Recommendation")
            best = max(restaurants, key=lambda x: x.get("rating", 0))
            lines.append(f"Based on ratings, **{best.get('name')}** offers the best quality.")
            
            return "\n".join(lines)
        
        return "Unable to compare restaurants at this time."
    
    def enhance_recommendations(
        self,
        restaurants: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enhance restaurant recommendations with AI explanations.
        
        Adds 'ai_explanation' field to each restaurant.
        
        Args:
            restaurants: List of restaurants to enhance
            user_preferences: User preferences
            
        Returns:
            Enhanced restaurant list
        """
        enhanced = []
        
        for restaurant in restaurants:
            enhanced_rest = restaurant.copy()
            enhanced_rest["ai_explanation"] = self.get_explanation(
                restaurant, user_preferences
            )
            enhanced.append(enhanced_rest)
        
        return enhanced
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about the LLM client.
        
        Returns:
            Dictionary with client configuration
        """
        return {
            "model": self.model,
            "api_base": self.api_base,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "available": self.is_available(),
            "fallback_enabled": self.fallback_enabled
        }
