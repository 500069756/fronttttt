"""Streamlit UI for Restaurant Recommendation System.

Basic UI for end-to-end testing of the recommendation engine.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

from src.phase1_foundation import DataLoader, DataPreprocessor, setup_logging
from src.phase2_engine import RestaurantFilter, RestaurantRanker, LLMClient

# Page configuration
st.set_page_config(
    page_title="Restaurant Recommender",
    page_icon="🍽️",
    layout="wide"
)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.processed_data = None
    st.session_state.preprocessor = None


def load_data():
    """Load and preprocess restaurant data."""
    with st.spinner("Loading restaurant data..."):
        loader = DataLoader(max_restaurants=200)
        raw_data = loader.load()
        
        preprocessor = DataPreprocessor()
        processed_data = preprocessor.preprocess(raw_data)
        
        st.session_state.processed_data = processed_data
        st.session_state.preprocessor = preprocessor
        st.session_state.data_loaded = True
        
        return processed_data, preprocessor


def main():
    """Main UI application."""
    st.title("🍽️ Restaurant Recommendation System")
    st.markdown("*Find the perfect restaurant based on your preferences*")
    
    # Load data on first run
    if not st.session_state.data_loaded:
        processed_data, preprocessor = load_data()
        st.success(f"✅ Loaded {len(processed_data)} restaurants!")
    else:
        processed_data = st.session_state.processed_data
        preprocessor = st.session_state.preprocessor
    
    # Sidebar - User Preferences
    st.sidebar.header("Your Preferences")
    
    # Location filter
    available_locations = preprocessor.get_available_locations()
    location = st.sidebar.selectbox(
        "📍 Location",
        ["Any"] + available_locations[:20],
        index=0
    )
    
    # Budget filter
    budget = st.sidebar.selectbox(
        "💰 Budget",
        ["Any", "low", "medium", "high"],
        index=0
    )
    
    # Cuisine filter
    available_cuisines = preprocessor.get_available_cuisines()
    cuisines = st.sidebar.multiselect(
        "🍽️ Cuisines",
        available_cuisines[:30],
        default=[]
    )
    
    # Rating filter
    min_rating = st.sidebar.slider(
        "⭐ Minimum Rating",
        0.0, 5.0, 0.0, 0.5
    )
    
    # Number of results
    top_n = st.sidebar.slider(
        "📊 Number of Recommendations",
        1, 10, 5
    )
    
    # AI Enhancement toggle
    use_ai = st.sidebar.checkbox(
        "🤖 Use AI Explanations",
        value=True,
        help="Generate personalized explanations using LLM"
    )
    
    # Get Recommendations button
    if st.sidebar.button("🔍 Get Recommendations", type="primary"):
        with st.spinner("Finding the best restaurants for you..."):
            # Apply filters
            filter_obj = RestaurantFilter(processed_data)
            
            if location != "Any":
                filter_obj.filter_by_location(location)
            if budget != "Any":
                filter_obj.filter_by_budget(budget=budget)
            if cuisines:
                filter_obj.filter_by_cuisine(cuisines, match_mode="any")
            if min_rating > 0:
                filter_obj.filter_by_rating(min_rating=min_rating)
            
            filtered_data = filter_obj.get_results()
            
            if filtered_data.empty:
                st.warning("No restaurants match your criteria. Try broadening your search.")
                return
            
            # Rank results
            ranker = RestaurantRanker(
                user_location=location if location != "Any" else None,
                user_cuisines=cuisines if cuisines else None
            )
            
            ranked_data = ranker.rank(filtered_data, top_n=top_n, return_scores=True)
            
            # Display results
            st.header(f"🎯 Top {len(ranked_data)} Recommendations")
            
            # Show filter summary
            filter_summary = filter_obj.get_filter_summary()
            st.caption(
                f"Filtered from {filter_summary['original_count']} to "
                f"{filter_summary['filtered_count']} restaurants, "
                f"showing top {len(ranked_data)}"
            )
            
            # AI Summary
            if use_ai:
                try:
                    llm_client = LLMClient()
                    if llm_client.is_available():
                        summary = llm_client.get_summary(
                            ranked_data.head(3).to_dict("records"),
                            {
                                "location": location if location != "Any" else None,
                                "budget": budget if budget != "Any" else None,
                                "cuisines": cuisines
                            }
                        )
                        st.info(f"💬 {summary}")
                except Exception as e:
                    st.warning(f"AI summary unavailable: {e}")
            
            # Display restaurant cards
            for idx, (_, row) in enumerate(ranked_data.iterrows(), 1):
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.subheader(f"#{idx} {row['name']}")
                        
                        # Location and cuisines
                        st.write(f"📍 {row['location']}")
                        
                        cuisines_display = row.get('cuisines', 'Various')
                        if isinstance(cuisines_display, list):
                            cuisines_display = ', '.join(cuisines_display)
                        st.write(f"🍽️ {cuisines_display}")
                        
                        # Rating and cost
                        rating = row.get('rating', 0)
                        cost = row.get('cost', 0)
                        st.write(f"⭐ Rating: {rating:.1f}/5 | 💰 Cost: ₹{cost:,.0f} for two")
                        
                        # Match score
                        match_score = row.get('total_score', 0)
                        st.progress(match_score / 100, text=f"Match Score: {match_score:.1f}%")
                        
                        # AI Explanation
                        if use_ai:
                            try:
                                llm_client = LLMClient()
                                if llm_client.is_available():
                                    with st.spinner("Generating explanation..."):
                                        explanation = llm_client.get_explanation(
                                            row.to_dict(),
                                            {
                                                "location": location if location != "Any" else None,
                                                "budget": budget if budget != "Any" else None,
                                                "cuisines": cuisines
                                            }
                                        )
                                        st.write(f"💡 *{explanation}*")
                            except Exception:
                                pass
                    
                    with col2:
                        # Budget category badge
                        budget_cat = row.get('budget_category', 'medium')
                        budget_emoji = {"low": "💚", "medium": "💛", "high": "❤️"}.get(budget_cat, "💛")
                        st.metric("Budget", f"{budget_emoji} {budget_cat.title()}")
                        
                        # Rating badge
                        if rating >= 4.0:
                            st.success(f"⭐ {rating:.1f}")
                        elif rating >= 3.0:
                            st.info(f"⭐ {rating:.1f}")
                        else:
                            st.warning(f"⭐ {rating:.1f}")
                    
                    st.divider()
    
    # Data Exploration Section
    with st.expander("📊 Explore Dataset"):
        st.write(f"**Total Restaurants:** {len(processed_data)}")
        st.write(f"**Locations:** {len(preprocessor.available_locations)}")
        st.write(f"**Cuisines:** {len(preprocessor.available_cuisines)}")
        
        # Show sample data
        st.subheader("Sample Restaurants")
        sample_cols = ['name', 'location', 'cuisines', 'rating', 'cost', 'budget_category']
        available_cols = [c for c in sample_cols if c in processed_data.columns]
        st.dataframe(processed_data[available_cols].head(10))


if __name__ == "__main__":
    main()
