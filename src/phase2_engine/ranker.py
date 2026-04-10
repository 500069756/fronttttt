"""Scoring and ranking algorithm for restaurant recommendations.

Implements a weighted scoring system combining multiple factors:
- Rating Score (35%): Normalized rating
- Popularity Score (25%): Log-scaled votes
- Value Score (20%): Rating/Cost ratio
- Location Score (10%): Location match quality
- Diversity Score (10%): Cuisine preference match
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import DEFAULT_WEIGHTS

logger = logging.getLogger(__name__)


class RestaurantRanker:
    """Implements scoring and ranking for restaurants.
    
    This class calculates composite scores for restaurants based on
    multiple weighted factors. It supports custom weight configurations
    and provides detailed scoring breakdowns.
    
    Attributes:
        weights: Dictionary of scoring weights
        user_location: User's preferred location for location scoring
        user_cuisines: User's preferred cuisines for diversity scoring
        
    Example:
        >>> ranker = RestaurantRanker(weights={"rating": 0.5, "popularity": 0.5})
        >>> ranked_df = ranker.rank(filtered_df, top_n=10)
    """
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        user_location: Optional[str] = None,
        user_cuisines: Optional[List[str]] = None
    ):
        """Initialize the ranker with optional custom weights.
        
        Args:
            weights: Custom scoring weights (defaults to DEFAULT_WEIGHTS)
            user_location: User's location for location scoring
            user_cuisines: User's preferred cuisines for diversity scoring
        """
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self.user_location = user_location
        self.user_cuisines = user_cuisines or []
        
        # Normalize weights to sum to 1
        self._normalize_weights()
    
    def _normalize_weights(self) -> None:
        """Ensure weights sum to 1.0."""
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
    
    def set_user_context(
        self,
        location: Optional[str] = None,
        cuisines: Optional[List[str]] = None
    ) -> None:
        """Set user context for personalized scoring.
        
        Args:
            location: User's preferred location
            cuisines: User's preferred cuisines
        """
        self.user_location = location
        self.user_cuisines = cuisines or []
    
    def rank(
        self,
        df: pd.DataFrame,
        top_n: int = 10,
        return_scores: bool = False
    ) -> pd.DataFrame:
        """Rank restaurants by composite score.
        
        Args:
            df: DataFrame of restaurants to rank
            top_n: Number of top results to return (0 for all)
            return_scores: If True, include score breakdown columns
            
        Returns:
            DataFrame sorted by total_score (descending)
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for ranking")
            return df
        
        logger.info(f"Ranking {len(df)} restaurants...")
        
        # Calculate all component scores
        df = df.copy()
        df = self._calculate_rating_score(df)
        df = self._calculate_popularity_score(df)
        df = self._calculate_value_score(df)
        df = self._calculate_location_score(df)
        df = self._calculate_diversity_score(df)
        
        # Calculate total weighted score
        df["total_score"] = (
            df["rating_score"] * self.weights.get("rating", 0.35) +
            df["popularity_score"] * self.weights.get("popularity", 0.25) +
            df["value_score"] * self.weights.get("value", 0.20) +
            df["location_score"] * self.weights.get("location", 0.10) +
            df["diversity_score"] * self.weights.get("diversity", 0.10)
        )
        
        # Scale to 0-100 for readability
        df["total_score"] = df["total_score"] * 100
        
        # Sort by score
        df = df.sort_values("total_score", ascending=False)
        
        # Select top N
        if top_n > 0 and len(df) > top_n:
            df = df.head(top_n)
        
        # Clean up output
        if not return_scores:
            # Keep only essential score columns
            score_cols = ["total_score"]
            keep_cols = [c for c in df.columns if not c.endswith("_score") or c in score_cols]
            df = df[keep_cols]
        
        logger.info(f"Ranking complete. Top score: {df['total_score'].max():.2f}")
        return df.reset_index(drop=True)
    
    def _calculate_rating_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate normalized rating score.
        
        Linear normalization: rating / 5.0
        Range: 0.0 - 1.0
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with rating_score column
        """
        if "rating" not in df.columns:
            df["rating_score"] = 0.0
            return df
        
        df["rating_score"] = df["rating"].fillna(0) / 5.0
        df["rating_score"] = df["rating_score"].clip(0, 1)
        
        return df
    
    def _calculate_popularity_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate popularity score based on votes.
        
        Uses logarithmic scaling to handle wide vote ranges.
        Formula: log1p(votes) / max_log_votes
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with popularity_score column
        """
        if "votes" not in df.columns:
            df["popularity_score"] = 0.0
            return df
        
        votes = df["votes"].fillna(0)
        
        # Logarithmic scaling
        log_votes = np.log1p(votes)
        
        # Normalize by max
        max_log = log_votes.max()
        if max_log > 0:
            df["popularity_score"] = log_votes / max_log
        else:
            df["popularity_score"] = 0.0
        
        return df
    
    def _calculate_value_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate value score (rating/cost ratio).
        
        Higher rating with lower cost = better value.
        Normalized across the dataset.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with value_score column
        """
        if "rating" not in df.columns or "cost" not in df.columns:
            df["value_score"] = 0.0
            return df
        
        rating = df["rating"].fillna(0)
        cost = df["cost"].fillna(df["cost"].median())
        
        # Avoid division by zero
        cost = cost.replace(0, 1)
        
        # Calculate value ratio
        value_ratio = rating / cost
        
        # Normalize to 0-1 range
        max_value = value_ratio.max()
        if max_value > 0:
            df["value_score"] = value_ratio / max_value
        else:
            df["value_score"] = 0.0
        
        df["value_score"] = df["value_score"].clip(0, 1)
        
        return df
    
    def _calculate_location_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate location match score.
        
        Binary scoring:
        - 1.0 if user_location matches restaurant location
        - 0.3 otherwise (some base relevance)
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with location_score column
        """
        if "location" not in df.columns or not self.user_location:
            df["location_score"] = 0.5  # Neutral score
            return df
        
        user_loc_lower = self.user_location.lower()
        
        def score_location(restaurant_loc: str) -> float:
            """Score a single location match."""
            if pd.isna(restaurant_loc):
                return 0.3
            rest_loc_lower = str(restaurant_loc).lower()
            
            if user_loc_lower in rest_loc_lower or rest_loc_lower in user_loc_lower:
                return 1.0
            return 0.3
        
        df["location_score"] = df["location"].apply(score_location)
        
        return df
    
    def _calculate_diversity_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate cuisine diversity/preference match score.
        
        Proportional to number of cuisine matches:
        matches / len(preferred_cuisines)
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with diversity_score column
        """
        if not self.user_cuisines:
            df["diversity_score"] = 0.5  # Neutral score
            return df
        
        user_cuisines_lower = [c.lower() for c in self.user_cuisines]
        
        def score_diversity(row_cuisines: List[str]) -> float:
            """Score cuisine match for a single restaurant."""
            if not isinstance(row_cuisines, list) or not row_cuisines:
                return 0.3
            
            row_lower = [c.lower() for c in row_cuisines]
            matches = sum(1 for c in user_cuisines_lower if c in row_lower)
            
            return matches / len(user_cuisines_lower)
        
        if "cuisine_list" in df.columns:
            df["diversity_score"] = df["cuisine_list"].apply(score_diversity)
        elif "cuisines" in df.columns:
            df["diversity_score"] = df["cuisines"].apply(
                lambda x: score_diversity([str(x)]) if pd.notna(x) else 0.3
            )
        else:
            df["diversity_score"] = 0.3
        
        return df
    
    def get_scoring_weights(self) -> Dict[str, float]:
        """Get current scoring weights.
        
        Returns:
            Dictionary of current weights
        """
        return self.weights.copy()
    
    def set_scoring_weights(self, weights: Dict[str, float]) -> None:
        """Set custom scoring weights.
        
        Args:
            weights: Dictionary of new weights
        """
        self.weights = weights.copy()
        self._normalize_weights()
        logger.info(f"Updated scoring weights: {self.weights}")
    
    def get_ranking_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics of ranking results.
        
        Args:
            df: Ranked DataFrame
            
        Returns:
            Dictionary with ranking statistics
        """
        if df.empty or "total_score" not in df.columns:
            return {"error": "No ranking data available"}
        
        return {
            "total_restaurants": len(df),
            "avg_score": df["total_score"].mean(),
            "max_score": df["total_score"].max(),
            "min_score": df["total_score"].min(),
            "score_std": df["total_score"].std(),
            "top_3_avg": df.head(3)["total_score"].mean() if len(df) >= 3 else None,
            "weights_used": self.weights.copy()
        }
    
    def explain_ranking(self, df: pd.DataFrame, restaurant_name: str) -> Dict[str, Any]:
        """Explain why a specific restaurant received its score.
        
        Args:
            df: Ranked DataFrame with score breakdown
            restaurant_name: Name of restaurant to explain
            
        Returns:
            Dictionary with score breakdown and explanation
        """
        if df.empty or "total_score" not in df.columns:
            return {"error": "No ranking data available"}
        
        match = df[df["name"].str.lower() == restaurant_name.lower()]
        
        if match.empty:
            return {"error": f"Restaurant '{restaurant_name}' not found"}
        
        row = match.iloc[0]
        
        score_breakdown = {}
        for score_type in ["rating", "popularity", "value", "location", "diversity"]:
            col = f"{score_type}_score"
            if col in row:
                weighted = row[col] * self.weights.get(score_type, 0) * 100
                score_breakdown[score_type] = {
                    "raw_score": round(row[col], 3),
                    "weight": self.weights.get(score_type, 0),
                    "weighted_contribution": round(weighted, 2)
                }
        
        return {
            "restaurant": row["name"],
            "total_score": round(row["total_score"], 2),
            "rank": df.index.get_loc(match.index[0]) + 1,
            "score_breakdown": score_breakdown,
            "location": row.get("location", "Unknown"),
            "rating": row.get("rating", 0),
            "cost": row.get("cost", 0),
            "cuisines": row.get("cuisines", "Unknown")
        }
