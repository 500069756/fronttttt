"""Streamlit UI for Restaurant Recommendation System (with API backend)."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import streamlit as st
import requests
import pandas as pd

import os

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001/api/v1")

# Page configuration
st.set_page_config(
    page_title="Restaurant Recommender",
    page_icon="🍽️",
    layout="wide"
)

# Initialize session state
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False


def check_api():
    """Check if API is available."""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_locations():
    """Fetch cities from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/cities", timeout=10)
        if response.status_code == 200:
            return response.json().get("cities", [])
    except:
        pass
    return []


def get_localities(city: str):
    """Fetch localities from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/localities", params={"city": city}, timeout=10)
        if response.status_code == 200:
            return response.json().get("localities", [])
    except:
        pass
    return []


def get_cuisines():
    """Fetch cuisines from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/cuisines", timeout=10)
        if response.status_code == 200:
            return response.json().get("cuisines", [])
    except:
        pass
    return []


def get_recommendations(preferences):
    """Get recommendations from API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/recommend",
            json=preferences,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"API Error: {e}")
    return None


def main():
    """Main UI application."""
    st.title("🍽️ Restaurant Recommendation System")
    st.markdown("*Find the perfect restaurant based on your preferences*")
    
    # Check API connection
    if not st.session_state.api_connected:
        with st.spinner("Connecting to backend API..."):
            if check_api():
                st.session_state.api_connected = True
                st.success("✅ Connected to backend API!")
            else:
                st.error("❌ Cannot connect to backend API at http://localhost:8000")
                st.info("Please make sure the backend is running: `python -m uvicorn src.phase3_api.main:app --host 0.0.0.0 --port 8000`")
                return
    
    # Fetch data from API
    with st.spinner("Loading data from API..."):
        available_locations = get_locations()
        available_cuisines = get_cuisines()
    
    # Sidebar - User Preferences
    st.sidebar.header("Your Preferences")
    
    # City selector
    city_options = ["Any"] + available_locations if available_locations else ["Any"]
    selected_city = st.sidebar.selectbox("🏙️ Area (City)", city_options, index=0)
    
    # Locality selector
    available_localities = []
    if selected_city != "Any":
        available_localities = get_localities(selected_city)
        
    locality_options = ["Any"] + available_localities if available_localities else ["Any"]
    selected_locality = st.sidebar.selectbox("📍 Neighborhood", locality_options, index=0)
    
    # Budget filter
    budget = st.sidebar.selectbox(
        "💰 Budget",
        ["Any", "low", "medium", "high"],
        index=0
    )
    
    # Cuisine filter
    cuisines = st.sidebar.multiselect(
        "🍽️ Cuisines",
        available_cuisines[:30] if available_cuisines else [],
        default=[]
    )
    
    # Rating filter
    min_rating = st.sidebar.slider("⭐ Minimum Rating", 0.0, 5.0, 0.0, 0.5)
    
    # Number of results
    top_n = st.sidebar.slider("📊 Number of Recommendations", 1, 10, 5)
    
    # AI Enhancement toggle
    use_ai = st.sidebar.checkbox("🤖 Use AI Explanations", value=True)
    
    # Get Recommendations button
    if st.sidebar.button("🔍 Get Recommendations", type="primary"):
        with st.spinner("Fetching recommendations from API..."):
            # Prepare request
            preferences = {
                "city": selected_city if selected_city != "Any" else None,
                "location": selected_locality if selected_locality != "Any" else None,
                "budget": budget if budget != "Any" else None,
                "cuisines": cuisines,
                "min_rating": min_rating,
                "top_n": top_n,
                "use_ai": use_ai
            }
            
            # Call API
            result = get_recommendations(preferences)
            
            if result is None:
                st.error("Failed to get recommendations from API")
                return
            
            if not result.get("items"):
                st.warning("No restaurants match your criteria. Try broadening your search.")
                return
            
            # Display results
            st.header(f"🎯 Top {len(result['items'])} Recommendations")
            
            # Show filter summary
            st.caption(f"Found {result['total_filtered']} matching restaurants")
            
            # AI Summary
            if result.get("summary"):
                st.info(f"💬 {result['summary']}")
            
            # Display restaurant cards
            for idx, restaurant in enumerate(result["items"], 1):
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.subheader(f"#{idx} {restaurant['name']}")
                        
                        st.write(f"📍 {restaurant['locality']}")
                        st.write(f"🍽️ {restaurant['cuisines']}")
                        st.write(f"⭐ Rating: {restaurant['rating']:.1f}/5 | 💰 Cost: ₹{restaurant['cost']:,.0f} for two")
                        
                        # Match score
                        match_score = restaurant.get('match_score', 0)
                        st.progress(match_score / 100, text=f"Match Score: {match_score:.1f}%")
                        
                        # AI Explanation
                        if restaurant.get("explanation"):
                            st.write(f"💡 *{restaurant['explanation']}*")
                    
                    with col2:
                        # Budget category badge
                        budget_cat = restaurant.get('budget_category', 'medium')
                        budget_emoji = {"low": "💚", "medium": "💛", "high": "❤️"}.get(budget_cat, "💛")
                        st.metric("Budget", f"{budget_emoji} {budget_cat.title()}")
                        
                        # Rating badge
                        rating = restaurant.get('rating', 0)
                        if rating >= 4.0:
                            st.success(f"⭐ {rating:.1f}")
                        elif rating >= 3.0:
                            st.info(f"⭐ {rating:.1f}")
                        else:
                            st.warning(f"⭐ {rating:.1f}")
                    
                    st.divider()
    
    # API Status
    with st.expander("🔌 API Status"):
        if check_api():
            st.success("✅ Backend API is running")
            try:
                response = requests.get(f"{API_BASE_URL}/", timeout=5)
                st.json(response.json())
            except:
                pass
        else:
            st.error("❌ Backend API is not available")


if __name__ == "__main__":
    main()
