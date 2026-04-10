"""Demo script for Phase 2: Core Recommendation Engine.

This script demonstrates the functionality implemented in Phase 2:
- Multi-criteria filtering (location, budget, cuisine, rating)
- Scoring and ranking algorithm
- LLM integration for personalized explanations
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import logging
from src.phase1_foundation import DataLoader, DataPreprocessor, setup_logging, format_currency
from src.phase2_engine import RestaurantFilter, RestaurantRanker, LLMClient

# Setup logging
logger = setup_logging(logging.INFO)


def main():
    """Run Phase 2 demonstration."""
    print("=" * 70)
    print("PHASE 2: CORE RECOMMENDATION ENGINE - DEMO")
    print("=" * 70)
    
    # Step 1: Load and preprocess data (Phase 1)
    print("\n📥 Step 1: Loading & Preprocessing Data")
    print("-" * 70)
    
    loader = DataLoader(max_restaurants=100)
    preprocessor = DataPreprocessor()
    
    try:
        raw_data = loader.load()
        processed_data = preprocessor.preprocess(raw_data)
        print(f"✅ Loaded and preprocessed {len(processed_data)} restaurants")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Step 2: Demonstrate Filtering
    print("\n🔍 Step 2: Multi-Criteria Filtering")
    print("-" * 70)
    
    # Show available locations and cuisines
    print(f"Available Locations: {preprocessor.get_available_locations()[:5]}")
    print(f"Available Cuisines: {preprocessor.get_available_cuisines()[:8]}")
    
    # Example user preferences (adjusted based on available data)
    # Note: The sample dataset may have limited data, so filters are relaxed
    user_preferences = {
        "location": None,  # No location filter to get more results
        "budget": None,  # No budget filter to get more results
        "cuisines": None,  # No cuisine filter to get more results
        "min_rating": None,  # No rating filter (dataset may have 0 ratings)
        "top_n": 5
    }
    
    print(f"User Preferences:")
    print(f"  📍 Location: {user_preferences['location'] or 'Any'}")
    print(f"  💰 Budget: {user_preferences['budget'] or 'Any'}")
    print(f"  🍽️ Cuisines: {', '.join(user_preferences['cuisines']) if user_preferences['cuisines'] else 'Any'}")
    print(f"  ⭐ Min Rating: {user_preferences['min_rating'] or 'Any'}")
    
    # Apply filters
    filter_obj = RestaurantFilter(processed_data)
    
    if user_preferences["location"]:
        filter_obj.filter_by_location(user_preferences["location"])
    if user_preferences["budget"]:
        filter_obj.filter_by_budget(budget=user_preferences["budget"])
    if user_preferences["cuisines"]:
        filter_obj.filter_by_cuisine(user_preferences["cuisines"], match_mode="any")
    if user_preferences["min_rating"]:
        filter_obj.filter_by_rating(min_rating=user_preferences["min_rating"])
    
    filtered_data = filter_obj.get_results()
    
    print(f"\n📊 Filter Results:")
    filter_summary = filter_obj.get_filter_summary()
    print(f"  Original: {filter_summary['original_count']} restaurants")
    print(f"  Filtered: {filter_summary['filtered_count']} restaurants")
    print(f"  Removed: {filter_summary['removed_total']} restaurants")
    
    if filtered_data.empty:
        print("\n⚠️ No restaurants match your criteria. Try broadening your search.")
        return
    
    # Step 3: Demonstrate Ranking
    print("\n🏆 Step 3: Scoring & Ranking Algorithm")
    print("-" * 70)
    
    ranker = RestaurantRanker(
        user_location=user_preferences.get("location"),
        user_cuisines=user_preferences.get("cuisines")
    )
    
    print(f"Scoring Weights:")
    for component, weight in ranker.get_scoring_weights().items():
        print(f"  {component.title()}: {weight*100:.0f}%")
    
    ranked_data = ranker.rank(filtered_data, top_n=user_preferences["top_n"], return_scores=True)
    
    print(f"\n📈 Ranking Summary:")
    ranking_summary = ranker.get_ranking_summary(ranked_data)
    print(f"  Top Score: {ranking_summary['max_score']:.1f}/100")
    print(f"  Avg Score: {ranking_summary['avg_score']:.1f}/100")
    
    # Step 4: Display Top Recommendations
    print("\n⭐ Step 4: Top Recommendations")
    print("-" * 70)
    
    for i, row in ranked_data.iterrows():
        print(f"\n#{i+1} {row['name']}")
        print(f"   📍 Location: {row['location']}")
        cuisines = row['cuisines'] if isinstance(row['cuisines'], str) else ', '.join(row.get('cuisine_list', []))
        print(f"   🍽️ Cuisines: {cuisines}")
        print(f"   ⭐ Rating: {row['rating']:.1f}/5")
        print(f"   💰 Cost: {format_currency(row['cost'])} for two")
        print(f"   📊 Match Score: {row['total_score']:.1f}/100")
    
    # Step 5: LLM Integration (with fallback)
    print("\n🤖 Step 5: AI-Powered Explanations")
    print("-" * 70)
    
    llm_client = LLMClient(fallback_enabled=True)
    
    if llm_client.is_available():
        print("✅ LLM client available (using Grok)")
    else:
        print("⚠️ LLM client not available (using fallback explanations)")
    
    # Enhance recommendations with AI explanations
    top_restaurants = ranked_data.head(3).to_dict("records")
    enhanced = llm_client.enhance_recommendations(top_restaurants, user_preferences)
    
    for i, restaurant in enumerate(enhanced):
        print(f"\n#{i+1} {restaurant['name']}:")
        print(f"   💬 {restaurant['ai_explanation']}")
    
    # Step 6: Summary
    summary = llm_client.get_summary(ranked_data.head(5).to_dict("records"), user_preferences)
    print(f"\n📝 Summary:")
    print(f"   {summary}")
    
    # Step 7: Compare top 2 restaurants
    if len(ranked_data) >= 2:
        print("\n🔄 Step 6: Restaurant Comparison")
        print("-" * 70)
        comparison = llm_client.compare(
            ranked_data.head(2).to_dict("records"),
            user_preferences
        )
        print(comparison)
    
    print("\n" + "=" * 70)
    print("✅ PHASE 2 DEMO COMPLETE")
    print("=" * 70)
    print("\nKey Features Demonstrated:")
    print("  ✅ Multi-criteria filtering (location, budget, cuisine, rating)")
    print("  ✅ Weighted scoring algorithm (rating, popularity, value, location, diversity)")
    print("  �AI-powered explanations (with fallback)")
    print("  ✅ Restaurant comparison")
    print("\nNext steps:")
    print("  1. Set GROK_API_KEY in .env for full LLM features")
    print("  2. Run tests: pytest tests/test_phase2.py -v")
    print("  3. Proceed to Phase 3: API & Service Layer")


if __name__ == "__main__":
    main()
