"""Prompt templates for LLM-powered restaurant recommendations.

Provides structured prompt templates for:
- Ranking: Re-rank filtered results with LLM intelligence
- Explanation: Generate personalized explanations for recommendations
- Summary: Summarize top recommendations
- Comparison: Compare multiple restaurant options
"""
from typing import Any, Dict, List, Optional
import json


class PromptTemplates:
    """Collection of prompt templates for LLM interactions.
    
    This class provides static methods to generate prompts for different
    LLM use cases in the recommendation system. Each method formats the
    prompt with relevant restaurant and user preference data.
    
    All prompts are designed to:
    - Produce structured, parseable outputs
    - Be concise yet informative
    - Handle edge cases gracefully
    """
    
    @staticmethod
    def ranking_prompt(
        restaurants: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        top_n: int = 5
    ) -> str:
        """Generate prompt for LLM-based re-ranking.
        
        Asks the LLM to re-rank restaurants based on user preferences,
        considering factors beyond the algorithmic scoring.
        
        Args:
            restaurants: List of restaurant dictionaries
            user_preferences: User's preferences (location, cuisines, etc.)
            top_n: Number of top recommendations to request
            
        Returns:
            Formatted prompt string
        """
        prefs_str = PromptTemplates._format_preferences(user_preferences)
        restaurants_str = PromptTemplates._format_restaurants_list(restaurants)
        
        return f"""You are a restaurant recommendation expert. Re-rank the following restaurants based on the user's preferences.

USER PREFERENCES:
{prefs_str}

RESTAURANTS:
{restaurants_str}

TASK:
1. Re-rank these restaurants from most to least recommended for this user
2. Return ONLY a JSON array of restaurant indices (0-based) in your recommended order
3. Select the top {top_n} restaurants

OUTPUT FORMAT (JSON array only, no markdown):
[0, 2, 1, 4, 3]"""
    
    @staticmethod
    def explanation_prompt(
        restaurant: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> str:
        """Generate prompt for personalized restaurant explanation.
        
        Creates a 2-3 sentence explanation of why this restaurant
        is a good match for the user's preferences.
        
        Args:
            restaurant: Restaurant dictionary with details
            user_preferences: User's preferences
            
        Returns:
            Formatted prompt string
        """
        prefs_str = PromptTemplates._format_preferences(user_preferences)
        rest_str = PromptTemplates._format_single_restaurant(restaurant)
        
        return f"""You are a friendly restaurant recommendation assistant. Explain why this restaurant is a great choice for the user.

USER PREFERENCES:
{prefs_str}

RESTAURANT:
{rest_str}

TASK:
Write a 2-3 sentence personalized explanation of why this restaurant matches the user's preferences. Be specific and enthusiastic.

OUTPUT (plain text, no markdown):
"""
    
    @staticmethod
    def summary_prompt(
        restaurants: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> str:
        """Generate prompt for recommendation summary.
        
        Creates an overall summary introducing the top recommendations.
        
        Args:
            restaurants: List of top restaurant recommendations
            user_preferences: User's preferences
            
        Returns:
            Formatted prompt string
        """
        prefs_str = PromptTemplates._format_preferences(user_preferences)
        restaurants_str = PromptTemplates._format_restaurants_list(restaurants[:5])
        
        return f"""You are a restaurant recommendation assistant. Create a brief, engaging summary of these restaurant recommendations.

USER PREFERENCES:
{prefs_str}

TOP RECOMMENDATIONS:
{restaurants_str}

TASK:
Write a 2-3 sentence summary introducing these recommendations. Highlight the variety and why they match the user's preferences. Be conversational and helpful.

OUTPUT (plain text, no markdown):
"""
    
    @staticmethod
    def comparison_prompt(
        restaurants: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> str:
        """Generate prompt for restaurant comparison.
        
        Creates a comparative analysis of 2-3 restaurants.
        
        Args:
            restaurants: List of 2-3 restaurants to compare
            user_preferences: User's preferences
            
        Returns:
            Formatted prompt string
        """
        prefs_str = PromptTemplates._format_preferences(user_preferences)
        restaurants_str = PromptTemplates._format_restaurants_list(restaurants)
        
        return f"""You are a restaurant recommendation expert. Compare these restaurants to help the user decide.

USER PREFERENCES:
{prefs_str}

RESTAURANTS TO COMPARE:
{restaurants_str}

TASK:
Compare these restaurants across key factors (cuisine quality, value, atmosphere). 
Highlight the strengths of each option.
Provide a recommendation on which to choose based on the user's preferences.

OUTPUT FORMAT:
## Quick Comparison
[Brief comparison table or summary]

## Best For
- Restaurant A: [what it's best for]
- Restaurant B: [what it's best for]

## Recommendation
[Your recommendation with reasoning]
"""
    
    @staticmethod
    def fallback_explanation(restaurant: Dict[str, Any]) -> str:
        """Generate a fallback explanation without LLM.
        
        Used when LLM is unavailable. Creates a simple explanation
        based on restaurant attributes.
        
        Args:
            restaurant: Restaurant dictionary
            
        Returns:
            Simple explanation string
        """
        name = restaurant.get("name", "This restaurant")
        rating = restaurant.get("rating", 0)
        cuisines = restaurant.get("cuisines", "various cuisines")
        location = restaurant.get("location", "a convenient location")
        
        rating_desc = "highly rated" if rating >= 4.0 else "well-rated" if rating >= 3.5 else "popular"
        
        return f"{name} is a {rating_desc} restaurant serving {cuisines} in {location}. With a rating of {rating:.1f}/5, it's a solid choice for your dining needs."
    
    @staticmethod
    def fallback_summary(
        restaurants: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> str:
        """Generate a fallback summary without LLM.
        
        Args:
            restaurants: List of restaurants
            user_preferences: User preferences
            
        Returns:
            Simple summary string
        """
        count = len(restaurants)
        location = user_preferences.get("location", "your area")
        cuisines = user_preferences.get("cuisines", [])
        
        cuisine_str = f" {', '.join(cuisines[:2])}" if cuisines else ""
        avg_rating = sum(r.get("rating", 0) for r in restaurants) / max(count, 1)
        
        return f"Here are {count} great{cuisine_str} restaurants in {location}, with an average rating of {avg_rating:.1f}/5. Each has been selected based on your preferences for quality, value, and convenience."
    
    # Helper methods for formatting
    
    @staticmethod
    def _format_preferences(preferences: Dict[str, Any]) -> str:
        """Format user preferences for prompt inclusion."""
        lines = []
        
        if preferences.get("location"):
            lines.append(f"- Location: {preferences['location']}")
        
        if preferences.get("budget"):
            lines.append(f"- Budget: {preferences['budget'].title()}")
        
        if preferences.get("cuisines"):
            cuisines = preferences["cuisines"]
            if isinstance(cuisines, list):
                lines.append(f"- Preferred Cuisines: {', '.join(cuisines)}")
            else:
                lines.append(f"- Preferred Cuisines: {cuisines}")
        
        if preferences.get("min_rating"):
            lines.append(f"- Minimum Rating: {preferences['min_rating']}")
        
        prefs = preferences.get("preferences", {})
        if prefs.get("family_friendly"):
            lines.append("- Family-friendly preferred")
        if prefs.get("quick_service"):
            lines.append("- Quick service preferred")
        
        return "\n".join(lines) if lines else "- No specific preferences stated"
    
    @staticmethod
    def _format_single_restaurant(restaurant: Dict[str, Any]) -> str:
        """Format a single restaurant for prompt inclusion."""
        lines = []
        
        lines.append(f"- Name: {restaurant.get('name', 'Unknown')}")
        lines.append(f"- Location: {restaurant.get('location', 'Unknown')}")
        
        cuisines = restaurant.get("cuisines", [])
        if isinstance(cuisines, list):
            lines.append(f"- Cuisines: {', '.join(cuisines)}")
        else:
            lines.append(f"- Cuisines: {cuisines}")
        
        lines.append(f"- Rating: {restaurant.get('rating', 0)}/5")
        lines.append(f"- Cost for Two: ₹{restaurant.get('cost', 0)}")
        
        if restaurant.get("budget_category"):
            lines.append(f"- Budget Category: {restaurant['budget_category'].title()}")
        
        if restaurant.get("total_score"):
            lines.append(f"- Match Score: {restaurant['total_score']:.1f}/100")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_restaurants_list(restaurants: List[Dict[str, Any]]) -> str:
        """Format a list of restaurants for prompt inclusion."""
        lines = []
        
        for i, rest in enumerate(restaurants):
            name = rest.get("name", "Unknown")
            cuisines = rest.get("cuisines", [])
            if isinstance(cuisines, list):
                cuisines_str = ", ".join(cuisines[:3])
            else:
                cuisines_str = str(cuisines)
            
            rating = rest.get("rating", 0)
            cost = rest.get("cost", 0)
            location = rest.get("location", "Unknown")
            
            lines.append(
                f"{i}. {name} | {cuisines_str} | Rating: {rating}/5 | "
                f"Cost: ₹{cost} | Location: {location}"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def parse_ranking_response(response: str) -> List[int]:
        """Parse LLM ranking response to extract indices.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            List of restaurant indices
        """
        try:
            # Try to find JSON array in response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if "```" in response:
                lines = response.split("\n")
                response = "\n".join(
                    line for line in lines 
                    if not line.startswith("```")
                ).strip()
            
            # Try direct JSON parse
            if response.startswith("["):
                return json.loads(response)
            
            # Try to find array in text
            import re
            match = re.search(r'\[[\d\s,]+\]', response)
            if match:
                return json.loads(match.group())
            
            return []
            
        except (json.JSONDecodeError, ValueError):
            return []
