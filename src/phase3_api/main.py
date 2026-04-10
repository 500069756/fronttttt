"""FastAPI backend for Restaurant Recommendation System."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.phase1_foundation import DataLoader, DataPreprocessor
from src.phase2_engine import RestaurantFilter, RestaurantRanker, LLMClient

app = FastAPI(
    title="Restaurant Recommendation API",
    description="AI-powered restaurant recommendations",
    version="1.0.0"
)

router = APIRouter(prefix="/api/v1")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data storage
data_store = {
    "processed_data": None,
    "preprocessor": None,
    "data_loaded": False
}


class RecommendationRequest(BaseModel):
    city: Optional[str] = None
    location: Optional[str] = None
    budget: Optional[str] = None
    cuisines: Optional[List[str]] = []
    min_rating: float = 0.0
    top_n: int = 5
    use_ai: bool = True


class RestaurantResponse(BaseModel):
    name: str
    locality: str
    cuisines: str
    rating: float
    cost: float
    budget_category: str
    match_score: float
    explanation: Optional[str] = None


class RecommendationResponse(BaseModel):
    total_filtered: int
    items: List[RestaurantResponse]
    summary: Optional[str] = None


def load_data():
    """Load and preprocess data on startup."""
    if not data_store["data_loaded"]:
        loader = DataLoader(max_restaurants=1000)
        raw_data = loader.load()
        preprocessor = DataPreprocessor()
        processed_data = preprocessor.preprocess(raw_data)
        
        data_store["processed_data"] = processed_data
        data_store["preprocessor"] = preprocessor
        data_store["data_loaded"] = True


@app.get("/")
def read_root():
    return {
        "name": "Restaurant Recommender API",
        "version": "1.0.0",
        "endpoints": ["/api/v1/recommend", "/api/v1/health", "/api/v1/cities", "/api/v1/location-hierarchy"]
    }


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "data_loaded": data_store["data_loaded"],
        "restaurants_count": len(data_store["processed_data"]) if data_store["processed_data"] is not None else 0
    }


@app.on_event("startup")
async def startup_event():
    """Initialize data on startup."""
    load_data()


@router.get("/")
async def root():
    """API health check."""
    return {
        "status": "online",
        "service": "Restaurant Recommendation API",
        "version": "1.0.0",
        "data_loaded": data_store["data_loaded"]
    }


@router.get("/cities")
async def get_cities():
    """Get available cities/areas."""
    if not data_store["data_loaded"]:
        load_data()
    return {"cities": data_store["preprocessor"].get_available_cities()}


@router.get("/localities")
async def get_localities(city: Optional[str] = None):
    """Get available localities, optionally filtered by city."""
    if not data_store["data_loaded"]:
        load_data()
    
    if city:
        mapping = data_store["preprocessor"].get_city_locality_map()
        return {"localities": mapping.get(city, [])}
    
    return {"localities": data_store["preprocessor"].get_available_locations()[:100]}


@router.get("/location-hierarchy")
async def get_location_hierarchy():
    """Get hierarchical mapping of cities to localities."""
    if not data_store["data_loaded"]:
        load_data()
    return {
        "cities": data_store["preprocessor"].get_available_cities(),
        "hierarchy": data_store["preprocessor"].get_city_locality_map()
    }


@router.get("/cuisines")
async def get_cuisines():
    """Get available cuisines."""
    if not data_store["data_loaded"]:
        load_data()
    return {"cuisines": data_store["preprocessor"].get_available_cuisines()[:50]}


@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """Get restaurant recommendations based on preferences."""
    if not data_store["data_loaded"]:
        load_data()
    
    processed_data = data_store["processed_data"]
    
    # Apply filters
    filter_obj = RestaurantFilter(processed_data)
    
    if request.city:
        filter_obj.filter_by_city(request.city)
    if request.location:
        filter_obj.filter_by_location(request.location)
    if request.budget:
        filter_obj.filter_by_budget(budget=request.budget)
    if request.cuisines:
        filter_obj.filter_by_cuisine(request.cuisines, match_mode="any")
    if request.min_rating > 0:
        filter_obj.filter_by_rating(min_rating=request.min_rating)
    
    filtered_data = filter_obj.get_results()
    
    if filtered_data.empty:
        return RecommendationResponse(
            total_filtered=0,
            recommendations=[],
            summary="No restaurants match your criteria."
        )
    
    # Rank results
    ranker = RestaurantRanker(
        user_location=request.location,
        user_cuisines=request.cuisines if request.cuisines else None
    )
    
    ranked_data = ranker.rank(filtered_data, top_n=request.top_n, return_scores=True)
    
    # Generate AI summary if requested
    summary = None
    if request.use_ai:
        try:
            llm_client = LLMClient()
            if llm_client.is_available():
                summary = llm_client.get_summary(
                    ranked_data.head(3).to_dict("records"),
                    {
                        "location": request.location,
                        "budget": request.budget,
                        "cuisines": request.cuisines
                    }
                )
        except Exception:
            pass
    
    # Generate explanations for each restaurant
    recommendations = []
    for _, row in ranked_data.iterrows():
        explanation = None
        if request.use_ai:
            try:
                llm_client = LLMClient()
                if llm_client.is_available():
                    explanation = llm_client.get_explanation(
                        row.to_dict(),
                        {
                            "location": request.location,
                            "budget": request.budget,
                            "cuisines": request.cuisines
                        }
                    )
            except Exception:
                pass
        
        cuisines_display = row.get('cuisines', 'Various')
        if isinstance(cuisines_display, list):
            cuisines_display = ', '.join(cuisines_display)
        
        recommendations.append(RestaurantResponse(
            name=row['name'],
            locality=row['location'],
            cuisines=cuisines_display,
            rating=row.get('rating', 0),
            cost=row.get('cost', 0),
            budget_category=row.get('budget_category', 'medium'),
            match_score=row.get('total_score', 0),
            explanation=explanation
        ))
    
    return RecommendationResponse(
        total_filtered=len(filtered_data),
        items=recommendations,
        summary=summary
    )


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
