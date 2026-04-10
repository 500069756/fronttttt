"""Tests for Phase 2: Core Recommendation Engine components.

Tests for:
- RestaurantFilter: Multi-criteria filtering
- RestaurantRanker: Scoring and ranking
- PromptTemplates: Prompt generation
- LLMClient: LLM integration (without actual API calls)
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.phase2_engine import RestaurantFilter, RestaurantRanker, LLMClient, PromptTemplates


# =============================================================================
# TEST DATA
# =============================================================================

@pytest.fixture
def sample_restaurants() -> pd.DataFrame:
    """Create sample restaurant data for testing."""
    return pd.DataFrame([
        {
            "name": "Restaurant A",
            "location": "Koramangala, Bangalore",
            "cuisines": "Italian, Continental",
            "cuisine_list": ["Italian", "Continental"],
            "rating": 4.5,
            "cost": 800,
            "votes": 1200,
            "budget_category": "medium",
            "reviews": "Great family place with quick service"
        },
        {
            "name": "Restaurant B",
            "location": "Indiranagar, Bangalore",
            "cuisines": "North Indian, Chinese",
            "cuisine_list": ["North Indian", "Chinese"],
            "rating": 4.0,
            "cost": 400,
            "votes": 800,
            "budget_category": "low",
            "reviews": "Quick bites and fast delivery"
        },
        {
            "name": "Restaurant C",
            "location": "MG Road, Bangalore",
            "cuisines": "Italian, Mexican",
            "cuisine_list": ["Italian", "Mexican"],
            "rating": 3.5,
            "cost": 2000,
            "votes": 500,
            "budget_category": "high",
            "reviews": "Upscale dining for celebrations"
        },
        {
            "name": "Restaurant D",
            "location": "Whitefield, Bangalore",
            "cuisines": "South Indian",
            "cuisine_list": ["South Indian"],
            "rating": 4.2,
            "cost": 300,
            "votes": 600,
            "budget_category": "low",
            "reviews": "Authentic South Indian food"
        },
        {
            "name": "Restaurant E",
            "location": "Koramangala, Bangalore",
            "cuisines": "Italian, Continental, Mexican",
            "cuisine_list": ["Italian", "Continental", "Mexican"],
            "rating": 4.8,
            "cost": 1200,
            "votes": 2000,
            "budget_category": "medium",
            "reviews": "Premium family restaurant"
        }
    ])


# =============================================================================
# RESTAURANT FILTER TESTS
# =============================================================================

class TestRestaurantFilter:
    """Test cases for RestaurantFilter."""
    
    def test_filter_initialization(self, sample_restaurants):
        """Test filter initializes correctly."""
        filter_obj = RestaurantFilter(sample_restaurants)
        
        assert len(filter_obj.original_df) == len(sample_restaurants)
        assert len(filter_obj.df) == len(sample_restaurants)
        assert len(filter_obj.filter_history) == 0
    
    def test_filter_by_location_exact(self, sample_restaurants):
        """Test location filtering with exact match."""
        filter_obj = RestaurantFilter(sample_restaurants)
        result = filter_obj.filter_by_location(
            "Koramangala, Bangalore", exact_match=True
        ).get_results()
        
        assert len(result) == 2
        assert all("Koramangala" in loc for loc in result["location"])
    
    def test_filter_by_location_partial(self, sample_restaurants):
        """Test location filtering with partial match."""
        filter_obj = RestaurantFilter(sample_restaurants)
        result = filter_obj.filter_by_location("Bangalore").get_results()
        
        assert len(result) == 5  # All are in Bangalore
    
    def test_filter_by_budget(self, sample_restaurants):
        """Test budget filtering."""
        filter_obj = RestaurantFilter(sample_restaurants)
        result = filter_obj.filter_by_budget(budget="medium").get_results()
        
        assert len(result) == 2
        assert all(bc == "medium" for bc in result["budget_category"])
    
    def test_filter_by_cuisine_any(self, sample_restaurants):
        """Test cuisine filtering with ANY mode."""
        filter_obj = RestaurantFilter(sample_restaurants)
        result = filter_obj.filter_by_cuisine(
            ["Italian"], match_mode="any"
        ).get_results()
        
        # Should match restaurants A, C, E (have Italian)
        assert len(result) == 3
    
    def test_filter_by_cuisine_all(self, sample_restaurants):
        """Test cuisine filtering with ALL mode."""
        filter_obj = RestaurantFilter(sample_restaurants)
        result = filter_obj.filter_by_cuisine(
            ["Italian", "Continental"], match_mode="all"
        ).get_results()
        
        # Should match only A and E (have both Italian and Continental)
        assert len(result) == 2
    
    def test_filter_by_rating(self, sample_restaurants):
        """Test rating filtering."""
        filter_obj = RestaurantFilter(sample_restaurants)
        result = filter_obj.filter_by_rating(min_rating=4.0).get_results()
        
        assert len(result) == 4  # A, B, D, E
        assert all(r >= 4.0 for r in result["rating"])
    
    def test_filter_chaining(self, sample_restaurants):
        """Test chaining multiple filters."""
        result = (RestaurantFilter(sample_restaurants)
            .filter_by_location("Koramangala")
            .filter_by_budget("medium")
            .filter_by_rating(min_rating=4.0)
            .get_results())
        
        assert len(result) == 2
        assert all("Koramangala" in loc for loc in result["location"])
        assert all(r["rating"] >= 4.0 for _, r in result.iterrows())
    
    def test_filter_reset(self, sample_restaurants):
        """Test filter reset."""
        filter_obj = RestaurantFilter(sample_restaurants)
        filter_obj.filter_by_budget("high")
        
        assert len(filter_obj.df) == 1
        
        filter_obj.reset()
        
        assert len(filter_obj.df) == 5
        assert len(filter_obj.filter_history) == 0
    
    def test_filter_summary(self, sample_restaurants):
        """Test filter summary."""
        filter_obj = RestaurantFilter(sample_restaurants)
        filter_obj.filter_by_location("Koramangala").filter_by_rating(min_rating=4.0)
        
        summary = filter_obj.get_filter_summary()
        
        assert summary["original_count"] == 5
        assert summary["total_filters"] == 2


# =============================================================================
# RESTAURANT RANKER TESTS
# =============================================================================

class TestRestaurantRanker:
    """Test cases for RestaurantRanker."""
    
    def test_ranker_initialization(self):
        """Test ranker initializes correctly."""
        ranker = RestaurantRanker()
        
        assert ranker.weights is not None
        assert "rating" in ranker.weights
        assert "popularity" in ranker.weights
    
    def test_ranker_custom_weights(self):
        """Test ranker with custom weights."""
        custom_weights = {
            "rating": 0.5,
            "popularity": 0.3,
            "value": 0.1,
            "location": 0.05,
            "diversity": 0.05
        }
        ranker = RestaurantRanker(weights=custom_weights)
        
        # Weights should be normalized
        total = sum(ranker.weights.values())
        assert abs(total - 1.0) < 0.001
    
    def test_rank_restaurants(self, sample_restaurants):
        """Test ranking restaurants."""
        ranker = RestaurantRanker()
        ranked = ranker.rank(sample_restaurants, top_n=5)
        
        assert len(ranked) == 5
        assert "total_score" in ranked.columns
        
        # Should be sorted by score descending
        scores = ranked["total_score"].tolist()
        assert scores == sorted(scores, reverse=True)
    
    def test_rank_with_user_context(self, sample_restaurants):
        """Test ranking with user context."""
        ranker = RestaurantRanker(
            user_location="Koramangala",
            user_cuisines=["Italian"]
        )
        ranked = ranker.rank(sample_restaurants, top_n=3)
        
        # Restaurant E (Koramangala + Italian + highest rating) should be top
        assert ranked.iloc[0]["name"] in ["Restaurant E", "Restaurant A"]
    
    def test_rank_return_scores(self, sample_restaurants):
        """Test ranking with score breakdown."""
        ranker = RestaurantRanker()
        ranked = ranker.rank(sample_restaurants, top_n=3, return_scores=True)
        
        score_cols = ["rating_score", "popularity_score", "value_score"]
        for col in score_cols:
            assert col in ranked.columns
    
    def test_explain_ranking(self, sample_restaurants):
        """Test ranking explanation."""
        ranker = RestaurantRanker()
        ranked = ranker.rank(sample_restaurants, return_scores=True)
        
        explanation = ranker.explain_ranking(ranked, "Restaurant A")
        
        assert "total_score" in explanation
        assert "score_breakdown" in explanation
        assert "rank" in explanation
    
    def test_empty_dataframe(self):
        """Test ranking with empty DataFrame."""
        ranker = RestaurantRanker()
        empty_df = pd.DataFrame()
        ranked = ranker.rank(empty_df)
        
        assert len(ranked) == 0


# =============================================================================
# PROMPT TEMPLATES TESTS
# =============================================================================

class TestPromptTemplates:
    """Test cases for PromptTemplates."""
    
    def test_ranking_prompt(self, sample_restaurants):
        """Test ranking prompt generation."""
        restaurants = sample_restaurants.head(3).to_dict("records")
        preferences = {"location": "Bangalore", "cuisines": ["Italian"]}
        
        prompt = PromptTemplates.ranking_prompt(restaurants, preferences)
        
        assert "Bangalore" in prompt
        assert "Italian" in prompt
        assert "Restaurant A" in prompt or "Restaurant" in prompt
    
    def test_explanation_prompt(self, sample_restaurants):
        """Test explanation prompt generation."""
        restaurant = sample_restaurants.iloc[0].to_dict()
        preferences = {"location": "Bangalore", "cuisines": ["Italian"]}
        
        prompt = PromptTemplates.explanation_prompt(restaurant, preferences)
        
        assert "USER PREFERENCES" in prompt
        assert "RESTAURANT" in prompt
    
    def test_summary_prompt(self, sample_restaurants):
        """Test summary prompt generation."""
        restaurants = sample_restaurants.head(3).to_dict("records")
        preferences = {"location": "Bangalore"}
        
        prompt = PromptTemplates.summary_prompt(restaurants, preferences)
        
        assert "TOP RECOMMENDATIONS" in prompt
        assert "Bangalore" in prompt
    
    def test_comparison_prompt(self, sample_restaurants):
        """Test comparison prompt generation."""
        restaurants = sample_restaurants.head(2).to_dict("records")
        preferences = {"location": "Bangalore"}
        
        prompt = PromptTemplates.comparison_prompt(restaurants, preferences)
        
        assert "COMPARE" in prompt
    
    def test_fallback_explanation(self, sample_restaurants):
        """Test fallback explanation."""
        restaurant = sample_restaurants.iloc[0].to_dict()
        
        explanation = PromptTemplates.fallback_explanation(restaurant)
        
        assert restaurant["name"] in explanation
        assert str(int(restaurant["rating"])) in explanation
    
    def test_fallback_summary(self, sample_restaurants):
        """Test fallback summary."""
        restaurants = sample_restaurants.to_dict("records")
        preferences = {"location": "Bangalore"}
        
        summary = PromptTemplates.fallback_summary(restaurants, preferences)
        
        assert "5" in summary or "restaurants" in summary
    
    def test_parse_ranking_response(self):
        """Test parsing ranking response."""
        response = "[0, 2, 1, 4, 3]"
        indices = PromptTemplates.parse_ranking_response(response)
        
        assert indices == [0, 2, 1, 4, 3]
    
    def test_parse_ranking_response_with_markdown(self):
        """Test parsing ranking response with markdown."""
        response = "```json\n[0, 1, 2]\n```"
        indices = PromptTemplates.parse_ranking_response(response)
        
        assert indices == [0, 1, 2]
    
    def test_parse_ranking_response_invalid(self):
        """Test parsing invalid ranking response."""
        response = "This is not valid JSON"
        indices = PromptTemplates.parse_ranking_response(response)
        
        assert indices == []


# =============================================================================
# LLM CLIENT TESTS
# =============================================================================

class TestLLMClient:
    """Test cases for LLMClient (without actual API calls)."""
    
    def test_client_initialization(self):
        """Test client initializes correctly."""
        client = LLMClient(api_key="test_key")
        
        assert client.model is not None
        assert client.fallback_enabled is True
    
    def test_client_without_api_key(self):
        """Test client without API key."""
        # Use empty string to explicitly override env var
        client = LLMClient(api_key="", fallback_enabled=True)
        
        # Should not be available without API key
        assert client.is_available() is False
    
    def test_client_info(self):
        """Test getting client info."""
        client = LLMClient(
            api_key="test_key",
            model="gpt-4",
            max_tokens=500
        )
        
        info = client.get_client_info()
        
        assert info["model"] == "gpt-4"
        assert info["max_tokens"] == 500
        assert info["fallback_enabled"] is True
    
    def test_fallback_explanation(self, sample_restaurants):
        """Test fallback explanation when LLM unavailable."""
        client = LLMClient(api_key="", fallback_enabled=True)
        restaurant = sample_restaurants.iloc[0].to_dict()
        preferences = {"location": "Bangalore"}
        
        explanation = client.get_explanation(restaurant, preferences)
        
        assert restaurant["name"] in explanation
        assert len(explanation) > 0
    
    def test_fallback_summary(self, sample_restaurants):
        """Test fallback summary when LLM unavailable."""
        client = LLMClient(api_key="", fallback_enabled=True)
        restaurants = sample_restaurants.to_dict("records")
        preferences = {"location": "Bangalore"}
        
        summary = client.get_summary(restaurants, preferences)
        
        assert len(summary) > 0
    
    def test_fallback_ranking(self, sample_restaurants):
        """Test fallback ranking when LLM unavailable."""
        # Use empty string to explicitly disable LLM and test fallback
        client = LLMClient(api_key="", fallback_enabled=True)
        restaurants = sample_restaurants.to_dict("records")
        preferences = {"location": "Bangalore"}
        
        indices = client.re_rank(restaurants, preferences, top_n=3)
        
        # Should return first 3 indices in order (fallback behavior)
        assert indices == [0, 1, 2]
    
    def test_enhance_recommendations(self, sample_restaurants):
        """Test enhancing recommendations."""
        client = LLMClient(api_key="", fallback_enabled=True)
        restaurants = sample_restaurants.head(2).to_dict("records")
        preferences = {"location": "Bangalore"}
        
        enhanced = client.enhance_recommendations(restaurants, preferences)
        
        assert len(enhanced) == 2
        assert all("ai_explanation" in r for r in enhanced)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestPhase2Integration:
    """Integration tests for Phase 2 components."""
    
    def test_full_recommendation_pipeline(self, sample_restaurants):
        """Test complete filtering and ranking pipeline."""
        # Step 1: Filter
        filtered = (RestaurantFilter(sample_restaurants)
            .filter_by_rating(min_rating=3.5)
            .filter_by_cuisine(["Italian"], match_mode="any")
            .get_results())
        
        # Step 2: Rank
        ranker = RestaurantRanker(
            user_location="Bangalore",
            user_cuisines=["Italian"]
        )
        ranked = ranker.rank(filtered, top_n=3)
        
        assert len(ranked) <= 3
        assert "total_score" in ranked.columns
        assert all(r >= 3.5 for r in ranked["rating"])
    
    def test_recommendation_with_fallback_llm(self, sample_restaurants):
        """Test recommendation with fallback LLM."""
        # Filter and rank
        filtered = RestaurantFilter(sample_restaurants).get_results()
        ranked = RestaurantRanker().rank(filtered, top_n=3)
        
        # Enhance with LLM
        client = LLMClient(api_key=None, fallback_enabled=True)
        enhanced = client.enhance_recommendations(
            ranked.to_dict("records"),
            {"location": "Bangalore"}
        )
        
        assert len(enhanced) == 3
        assert all("ai_explanation" in r for r in enhanced)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
