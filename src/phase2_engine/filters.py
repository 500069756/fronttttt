"""Multi-criteria filtering system for restaurant recommendations.

Implements chainable filtering operations supporting:
- Location-based filtering (exact match, partial match)
- Budget filtering (by category or range)
- Cuisine filtering (single or multiple, ANY or ALL mode)
- Rating filtering (minimum threshold)
- Preference-based filtering (family-friendly, quick service)
"""
import logging
from typing import Any, Dict, List, Optional, Set
import pandas as pd

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import BUDGET_CATEGORIES

logger = logging.getLogger(__name__)


class RestaurantFilter:
    """Implements chainable filtering operations for restaurants.
    
    This class provides a fluent interface for applying multiple filters
    to a DataFrame of restaurants. Filters can be chained together and
    results can be retrieved at any point.
    
    Attributes:
        df: Current filtered DataFrame
        original_df: Original unfiltered DataFrame
        filter_history: List of applied filters
        
    Example:
        >>> results = (filter
        ...     .filter_by_location("Bangalore")
        ...     .filter_by_budget("medium")
        ...     .filter_by_cuisine(["Italian", "Continental"])
        ...     .filter_by_rating(min_rating=4.0)
        ...     .get_results())
    """
    
    # Keywords for preference-based filtering
    FAMILY_FRIENDLY_KEYWORDS = [
        "family", "kids", "children", "spacious", "private dining",
        "group", "birthday", "celebration", "anniversary"
    ]
    
    QUICK_SERVICE_KEYWORDS = [
        "quick", "fast", "takeaway", "delivery", "express",
        "grab and go", "on the go", "busy"
    ]
    
    def __init__(self, df: pd.DataFrame):
        """Initialize the filter with a DataFrame.
        
        Args:
            df: DataFrame containing restaurant data
        """
        self.original_df = df.copy()
        self.df = df.copy()
        self.filter_history: List[Dict[str, Any]] = []
        
    def reset(self) -> "RestaurantFilter":
        """Reset to original unfiltered data.
        
        Returns:
            Self for method chaining
        """
        self.df = self.original_df.copy()
        self.filter_history = []
        logger.debug("Filter reset to original data")
        return self
    
    def filter_by_location(
        self, 
        location: str, 
        exact_match: bool = False
    ) -> "RestaurantFilter":
        """Filter restaurants by location.
        
        Args:
            location: Location string to filter by
            exact_match: If True, require exact match; otherwise partial match
            
        Returns:
            Self for method chaining
        """
        if not location or "location" not in self.df.columns:
            return self
        
        initial_count = len(self.df)
        
        if exact_match:
            self.df = self.df[
                self.df["location"].str.lower() == location.lower()
            ]
        else:
            self.df = self.df[
                self.df["location"].str.lower().str.contains(
                    location.lower(), na=False
                )
            ]
        
        final_count = len(self.df)
        self.filter_history.append({
            "type": "location",
            "value": location,
            "exact_match": exact_match,
            "removed": initial_count - final_count
        })
        
        logger.debug(f"Location filter '{location}': {initial_count} -> {final_count}")
        return self

    def filter_by_city(
        self, 
        city: str, 
        exact_match: bool = True
    ) -> "RestaurantFilter":
        """Filter restaurants by city category.
        
        Args:
            city: City string to filter by
            exact_match: If True, require exact match; otherwise partial match
            
        Returns:
            Self for method chaining
        """
        if not city or "city" not in self.df.columns:
            return self
        
        initial_count = len(self.df)
        
        if exact_match:
            self.df = self.df[
                self.df["city"].str.lower() == city.lower()
            ]
        else:
            self.df = self.df[
                self.df["city"].str.lower().str.contains(
                    city.lower(), na=False
                )
            ]
        
        final_count = len(self.df)
        self.filter_history.append({
            "type": "city",
            "value": city,
            "exact_match": exact_match,
            "removed": initial_count - final_count
        })
        
        logger.debug(f"City filter '{city}': {initial_count} -> {final_count}")
        return self
    
    def filter_by_budget(
        self,
        budget: Optional[str] = None,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None
    ) -> "RestaurantFilter":
        """Filter restaurants by budget category or cost range.
        
        Args:
            budget: Budget category ('low', 'medium', 'high')
            min_cost: Minimum cost threshold
            max_cost: Maximum cost threshold
            
        Returns:
            Self for method chaining
        """
        if "cost" not in self.df.columns:
            return self
        
        initial_count = len(self.df)
        
        if budget and budget in BUDGET_CATEGORIES:
            min_b, max_b = BUDGET_CATEGORIES[budget]
            if max_b == float("inf"):
                self.df = self.df[self.df["cost"] >= min_b]
            else:
                self.df = self.df[
                    (self.df["cost"] >= min_b) & (self.df["cost"] < max_b)
                ]
        elif budget and "budget_category" in self.df.columns:
            self.df = self.df[self.df["budget_category"] == budget]
        
        # Apply custom cost range if specified
        if min_cost is not None:
            self.df = self.df[self.df["cost"] >= min_cost]
        if max_cost is not None:
            self.df = self.df[self.df["cost"] <= max_cost]
        
        final_count = len(self.df)
        self.filter_history.append({
            "type": "budget",
            "budget": budget,
            "min_cost": min_cost,
            "max_cost": max_cost,
            "removed": initial_count - final_count
        })
        
        logger.debug(f"Budget filter: {initial_count} -> {final_count}")
        return self
    
    def filter_by_cuisine(
        self,
        cuisines: List[str],
        match_mode: str = "any"
    ) -> "RestaurantFilter":
        """Filter restaurants by cuisine types.
        
        Args:
            cuisines: List of cuisine types to filter by
            match_mode: 'any' (match any cuisine) or 'all' (match all cuisines)
            
        Returns:
            Self for method chaining
        """
        if not cuisines:
            return self
        
        if "cuisine_list" not in self.df.columns and "cuisines" not in self.df.columns:
            return self
        
        initial_count = len(self.df)
        cuisines_lower = [c.lower() for c in cuisines]
        
        def has_cuisine_match(row_cuisines: List[str], mode: str) -> bool:
            """Check if row cuisines match the filter criteria."""
            if not isinstance(row_cuisines, list):
                return False
            row_lower = [c.lower() for c in row_cuisines]
            
            if mode == "all":
                return all(c in row_lower for c in cuisines_lower)
            else:  # mode == "any"
                return any(c in row_lower for c in cuisines_lower)
        
        # Use cuisine_list if available, otherwise parse cuisines column
        if "cuisine_list" in self.df.columns:
            self.df = self.df[
                self.df["cuisine_list"].apply(
                    lambda x: has_cuisine_match(x, match_mode)
                )
            ]
        else:
            # Parse from string column
            self.df = self.df[
                self.df["cuisines"].str.lower().apply(
                    lambda x: any(c in str(x).lower() for c in cuisines_lower)
                )
            ]
        
        final_count = len(self.df)
        self.filter_history.append({
            "type": "cuisine",
            "cuisines": cuisines,
            "match_mode": match_mode,
            "removed": initial_count - final_count
        })
        
        logger.debug(f"Cuisine filter {cuisines}: {initial_count} -> {final_count}")
        return self
    
    def filter_by_rating(
        self,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None
    ) -> "RestaurantFilter":
        """Filter restaurants by rating range.
        
        Args:
            min_rating: Minimum rating threshold (0-5)
            max_rating: Maximum rating threshold (0-5)
            
        Returns:
            Self for method chaining
        """
        if "rating" not in self.df.columns:
            return self
        
        initial_count = len(self.df)
        
        if min_rating is not None:
            self.df = self.df[self.df["rating"] >= min_rating]
        if max_rating is not None:
            self.df = self.df[self.df["rating"] <= max_rating]
        
        final_count = len(self.df)
        self.filter_history.append({
            "type": "rating",
            "min_rating": min_rating,
            "max_rating": max_rating,
            "removed": initial_count - final_count
        })
        
        logger.debug(f"Rating filter: {initial_count} -> {final_count}")
        return self
    
    def filter_by_preferences(
        self,
        preferences: Dict[str, bool]
    ) -> "RestaurantFilter":
        """Filter restaurants by additional preferences.
        
        Uses keyword matching in reviews and other text fields to identify
        restaurants that match preference criteria.
        
        Args:
            preferences: Dictionary of preference flags:
                - family_friendly: Match family-friendly keywords
                - quick_service: Match quick service keywords
                
        Returns:
            Self for method chaining
        """
        if not preferences:
            return self
        
        initial_count = len(self.df)
        
        # Get text column for keyword matching
        text_col = None
        for col in ["reviews", "cuisines", "name"]:
            if col in self.df.columns:
                text_col = col
                break
        
        if text_col is None:
            return self
        
        def matches_preferences(row: pd.Series, prefs: Dict[str, bool]) -> bool:
            """Check if a row matches preference criteria."""
            text = str(row.get(text_col, "")).lower()
            
            if prefs.get("family_friendly"):
                if not any(kw in text for kw in self.FAMILY_FRIENDLY_KEYWORDS):
                    return False
            
            if prefs.get("quick_service"):
                if not any(kw in text for kw in self.QUICK_SERVICE_KEYWORDS):
                    return False
            
            return True
        
        self.df = self.df[
            self.df.apply(lambda row: matches_preferences(row, preferences), axis=1)
        ]
        
        final_count = len(self.df)
        self.filter_history.append({
            "type": "preferences",
            "preferences": preferences,
            "removed": initial_count - final_count
        })
        
        logger.debug(f"Preferences filter: {initial_count} -> {final_count}")
        return self
    
    def apply_all_filters(
        self,
        location: Optional[str] = None,
        budget: Optional[str] = None,
        cuisines: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        preferences: Optional[Dict[str, bool]] = None,
        match_mode: str = "any"
    ) -> "RestaurantFilter":
        """Apply all filters at once.
        
        Convenience method to apply multiple filters in a single call.
        
        Args:
            location: Location to filter by
            budget: Budget category
            cuisines: List of cuisines
            min_rating: Minimum rating threshold
            preferences: Dictionary of preference flags
            match_mode: Cuisine match mode ('any' or 'all')
            
        Returns:
            Self for method chaining
        """
        if location:
            self.filter_by_location(location)
        if budget:
            self.filter_by_budget(budget=budget)
        if cuisines:
            self.filter_by_cuisine(cuisines, match_mode=match_mode)
        if min_rating is not None:
            self.filter_by_rating(min_rating=min_rating)
        if preferences:
            self.filter_by_preferences(preferences)
        
        return self
    
    def get_results(self) -> pd.DataFrame:
        """Get the current filtered results.
        
        Returns:
            Filtered DataFrame
        """
        return self.df.copy()
    
    def get_count(self) -> int:
        """Get count of filtered restaurants.
        
        Returns:
            Number of restaurants in filtered results
        """
        return len(self.df)
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """Get summary of applied filters.
        
        Returns:
            Dictionary with filter history and statistics
        """
        return {
            "total_filters": len(self.filter_history),
            "original_count": len(self.original_df),
            "filtered_count": len(self.df),
            "removed_total": len(self.original_df) - len(self.df),
            "filter_history": self.filter_history
        }
    
    def get_available_filters(self) -> Dict[str, List[str]]:
        """Get available values for each filter type.
        
        Returns:
            Dictionary with available locations, cuisines, and budget categories
        """
        result = {}
        
        if "location" in self.df.columns:
            result["locations"] = sorted(
                self.df["location"].dropna().unique().tolist()
            )
        
        if "cuisine_list" in self.df.columns:
            all_cuisines = set()
            for cuisines in self.df["cuisine_list"]:
                if isinstance(cuisines, list):
                    all_cuisines.update(cuisines)
            result["cuisines"] = sorted(list(all_cuisines))
        elif "cuisines" in self.df.columns:
            result["cuisines"] = sorted(
                self.df["cuisines"].dropna().unique().tolist()
            )
        
        if "budget_category" in self.df.columns:
            result["budget_categories"] = sorted(
                self.df["budget_category"].dropna().unique().tolist()
            )
        else:
            result["budget_categories"] = list(BUDGET_CATEGORIES.keys())
        
        return result
