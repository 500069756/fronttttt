"""Data preprocessor for cleaning and normalizing restaurant data."""
import logging
import re
from typing import List, Optional, Set
from pathlib import Path
import pandas as pd
import numpy as np

import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from config.settings import BUDGET_CATEGORIES, RATING_THRESHOLDS

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Cleans and preprocesses restaurant data for recommendation.
    
    This class handles all data cleaning and normalization tasks:
    - Handling missing values
    - Standardizing column names
    - Cleaning text fields
    - Parsing and normalizing cuisines
    - Processing ratings and costs
    - Creating derived features
    
    Attributes:
        processed_df: DataFrame after preprocessing
        available_locations: Set of unique locations
        available_cuisines: Set of unique cuisines
    """
    
    def __init__(self):
        """Initialize the preprocessor."""
        self.processed_df: Optional[pd.DataFrame] = None
        self.available_locations: Set[str] = set()
        self.available_cities: Set[str] = set()
        self.available_cuisines: Set[str] = set()
        self.city_locality_map: dict = {}
        
        # Load pre-built catalog if available
        self._load_location_catalog()
    
    def _load_location_catalog(self):
        """Load hierarchical mapping from cache file if it exists."""
        catalog_path = Path(__file__).parent.parent.parent.parent / "data_cache" / "location_catalog.json"
        if catalog_path.exists():
            try:
                import json
                with open(catalog_path, 'r') as f:
                    self.city_locality_map = json.load(f)
                    self.available_cities = set(self.city_locality_map.keys())
                    # Flatten localities for available_locations
                    all_locs = []
                    for locs in self.city_locality_map.values():
                        all_locs.extend(locs)
                    self.available_locations = set(all_locs)
                logger.info(f"Loaded {len(self.available_cities)} cities from location catalog")
            except Exception as e:
                logger.error(f"Error loading location catalog: {e}")
        
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the raw dataset.
        
        Executes the complete preprocessing pipeline:
        1. Handle missing values
        2. Standardize column names
        3. Clean text fields
        4. Parse cuisines
        5. Process ratings
        6. Process costs
        7. Create budget categories
        8. Remove duplicates
        
        Args:
            df: Raw DataFrame from data loader
            
        Returns:
            Cleaned and processed DataFrame
        """
        logger.info("Starting data preprocessing...")
        
        df = df.copy()
        initial_count = len(df)
        
        # Handle missing values
        df = self._handle_missing_values(df)
        
        # Standardize column names
        df = self._standardize_columns(df)
        
        # Clean and normalize text fields
        df = self._clean_text_fields(df)
        
        # Extract and normalize cuisines
        df = self._process_cuisines(df)
        
        # Process ratings
        df = self._process_ratings(df)
        
        # Process cost/pricing
        df = self._process_cost(df)
        
        # Create budget categories
        df = self._create_budget_categories(df)
        
        # Remove duplicates
        df = self._remove_duplicates(df)
        
        # Update available values
        self._update_available_values(df)
        
        self.processed_df = df
        final_count = len(df)
        
        logger.info(f"Preprocessing complete: {initial_count} → {final_count} restaurants")
        logger.info(f"Available locations: {len(self.available_locations)}")
        logger.info(f"Available cuisines: {len(self.available_cuisines)}")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset.
        
        Strategy:
        - Critical fields (name, location): Drop rows
        - Rating: Fill with 0
        - Cost: Fill with median
        - Votes: Fill with 0
        - Reviews: Fill with empty string
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with handled missing values
        """
        initial_count = len(df)
        
        # Drop rows with critical missing values
        critical_columns = ['name', 'location', 'cuisines']
        for col in critical_columns:
            if col in df.columns:
                df = df.dropna(subset=[col])
        
        dropped_count = initial_count - len(df)
        if dropped_count > 0:
            logger.debug(f"Dropped {dropped_count} rows with missing critical values")
        
        # Fill optional fields with defaults
        if 'rating' in df.columns:
            df['rating'] = df['rating'].fillna(0)
        if 'votes' in df.columns:
            df['votes'] = df['votes'].fillna(0)
        if 'cost' in df.columns:
            df['cost'] = df['cost'].fillna(df['cost'].median())
        if 'reviews' in df.columns:
            df['reviews'] = df['reviews'].fillna('')
            
        return df
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to consistent format.
        
        Maps various column name formats to standard names.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with standardized column names
        """
        column_mapping = {
            'restaurant_name': 'name',
            'restaurant_location': 'location',
            'restaurant_rating': 'rating',
            'restaurant_cost': 'cost',
            'restaurant_cuisines': 'cuisines',
            'restaurant_votes': 'votes',
            'restaurant_reviews': 'reviews',
            'restaurant_address': 'address',
            'restaurant_phone': 'phone',
            'restaurant_url': 'url',
            'restaurant_cost_for_two': 'cost',
            'listed_in(city)': 'city'
        }
        
        # Rename columns if they exist
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        return df
    
    def _clean_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize text fields.
        
        - Strip whitespace
        - Convert to Title Case
        - Remove extra spaces
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with cleaned text fields
        """
        text_columns = ['name', 'location', 'address']
        
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].str.title()
                # Remove extra spaces
                df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
                
        return df
    
    def _process_cuisines(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and normalize cuisine types.
        
        Parses cuisine strings and creates a list of cuisines
        for each restaurant.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with processed cuisine information
        """
        if 'cuisines' not in df.columns:
            df['cuisines'] = 'Unknown'
            df['cuisine_list'] = [['Unknown']]
            return df
        
        # Convert to string
        df['cuisines'] = df['cuisines'].astype(str)
        
        # Create list of cuisines for each restaurant
        df['cuisine_list'] = df['cuisines'].apply(self._parse_cuisines)
        
        # Normalize cuisine names
        df['cuisine_list'] = df['cuisine_list'].apply(
            lambda x: [self._normalize_cuisine(c) for c in x]
        )
        
        return df
    
    def _parse_cuisines(self, cuisines_str: str) -> List[str]:
        """Parse cuisine string into list.
        
        Splits cuisine string by common delimiters.
        
        Args:
            cuisines_str: String containing cuisines
            
        Returns:
            List of cuisine strings
        """
        if pd.isna(cuisines_str) or cuisines_str.lower() in ['nan', 'none', '']:
            return ['Unknown']
        
        # Split by common delimiters
        delimiters = [',', '|', '/', '&', ';']
        cuisines = [cuisines_str]
        
        for delim in delimiters:
            new_cuisines = []
            for c in cuisines:
                new_cuisines.extend([x.strip() for x in c.split(delim)])
            cuisines = new_cuisines
        
        # Filter out empty and invalid entries
        return [c for c in cuisines if c and c.lower() not in ['nan', 'none', '']]
    
    def _normalize_cuisine(self, cuisine: str) -> str:
        """Normalize cuisine name.
        
        Applies common normalizations and title case.
        
        Args:
            cuisine: Raw cuisine string
            
        Returns:
            Normalized cuisine string
        """
        cuisine = cuisine.strip().title()
        
        # Common normalizations
        normalizations = {
            'North Indian': 'North Indian',
            'South Indian': 'South Indian',
            'Fast Food': 'Fast Food',
            'Street Food': 'Street Food',
            'Ice Cream': 'Ice Cream',
            'Beverages': 'Beverages',
            'Bakery': 'Bakery',
            'Desserts': 'Desserts',
            'Cafe': 'Cafe',
        }
        
        return normalizations.get(cuisine, cuisine)
    
    def _process_ratings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process and normalize ratings.
        
        - Converts to numeric
        - Clips to 0-5 range
        - Creates rating categories
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with processed ratings
        """
        if 'rating' not in df.columns:
            df['rating'] = 0.0
            df['rating_category'] = 'Unknown'
            return df
        
        # Convert to numeric
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        
        # Clip ratings to valid range
        df['rating'] = df['rating'].clip(0, 5)
        
        # Create rating category
        def get_rating_category(rating):
            if rating >= RATING_THRESHOLDS['excellent']:
                return 'Excellent'
            elif rating >= RATING_THRESHOLDS['good']:
                return 'Good'
            elif rating >= RATING_THRESHOLDS['average']:
                return 'Average'
            else:
                return 'Poor'
        
        df['rating_category'] = df['rating'].apply(get_rating_category)
        
        return df
    
    def _process_cost(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process cost/pricing information.
        
        - Converts to numeric
        - Ensures non-negative values
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with processed cost
        """
        if 'cost' not in df.columns:
            df['cost'] = 0
            return df
        
        # Convert to numeric
        df['cost'] = pd.to_numeric(df['cost'], errors='coerce')
        df['cost'] = df['cost'].fillna(0)
        
        # Ensure non-negative
        df['cost'] = df['cost'].clip(lower=0)
        
        return df
    
    def _create_budget_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create budget categories based on cost.
        
        Categorizes restaurants into low/medium/high budget tiers.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with budget categories
        """
        def get_budget_category(cost):
            for category, (min_cost, max_cost) in BUDGET_CATEGORIES.items():
                if min_cost <= cost < max_cost if max_cost != float('inf') else min_cost <= cost:
                    return category
            return 'medium'
        
        df['budget_category'] = df['cost'].apply(get_budget_category)
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate restaurants.
        
        Identifies duplicates by name and location combination.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with duplicates removed
        """
        initial_count = len(df)
        
        # Identify duplicates by name and location
        if 'name' in df.columns and 'location' in df.columns:
            df = df.drop_duplicates(subset=['name', 'location'], keep='first')
        
        removed_count = initial_count - len(df)
        if removed_count > 0:
            logger.debug(f"Removed {removed_count} duplicate restaurants")
        
        return df
    
    def _update_available_values(self, df: pd.DataFrame):
        """Update sets of available locations and cuisines.
        
        Args:
            df: Processed DataFrame
        """
        if 'location' in df.columns:
            self.available_locations.update(set(df['location'].unique()))
        
        if 'city' in df.columns:
            self.available_cities.update(set(df['city'].unique()))
            
        if 'city' in df.columns and 'location' in df.columns:
            # Create a mapping of city -> localities
            mapping = df.groupby('city')['location'].unique().to_dict()
            for city, locs in mapping.items():
                if city not in self.city_locality_map:
                    self.city_locality_map[city] = sorted(list(locs))
                else:
                    # Merge and preserve sorted order
                    existing = set(self.city_locality_map[city])
                    existing.update(locs)
                    self.city_locality_map[city] = sorted(list(existing))
                
                # Ensure all localities are also in available_locations
                self.available_locations.update(locs)
        
        if 'cuisine_list' in df.columns:
            all_cuisines = []
            for cuisines in df['cuisine_list']:
                if isinstance(cuisines, list):
                    all_cuisines.extend(cuisines)
            self.available_cuisines = set(all_cuisines)
    
    def get_available_locations(self) -> List[str]:
        """Get list of available locations (localities).
        
        Returns:
            Sorted list of location names
        """
        return sorted(list(self.available_locations))
    
    def get_available_cities(self) -> List[str]:
        """Get list of available cities.
        
        Returns:
            Sorted list of city names
        """
        return sorted(list(self.available_cities))
    
    def get_city_locality_map(self) -> dict:
        """Get mapping of cities to their localities.
        
        Returns:
            Dictionary mapping city names to lists of locality names
        """
        return self.city_locality_map
    
    def get_available_cuisines(self) -> List[str]:
        """Get list of available cuisines.
        
        Returns:
            Sorted list of cuisine names
        """
        return sorted(list(self.available_cuisines))
    
    def get_processed_data(self) -> Optional[pd.DataFrame]:
        """Get processed data.
        
        Returns:
            Processed DataFrame or None if not processed
        """
        return self.processed_df
    
    def get_preprocessing_summary(self) -> dict:
        """Get summary of preprocessing results.
        
        Returns:
            Dictionary with preprocessing statistics
        """
        if self.processed_df is None:
            return {"status": "Not processed"}
        
        return {
            "total_restaurants": len(self.processed_df),
            "available_locations": len(self.available_locations),
            "available_cuisines": len(self.available_cuisines),
            "avg_rating": self.processed_df['rating'].mean() if 'rating' in self.processed_df.columns else None,
            "avg_cost": self.processed_df['cost'].mean() if 'cost' in self.processed_df.columns else None,
            "budget_distribution": self.processed_df['budget_category'].value_counts().to_dict() if 'budget_category' in self.processed_df.columns else None,
            "rating_distribution": self.processed_df['rating_category'].value_counts().to_dict() if 'rating_category' in self.processed_df.columns else None
        }
