"""Data loader for Hugging Face Zomato dataset."""
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
from datasets import load_dataset

import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from config.settings import DATASET_NAME, DATA_CACHE_DIR, MAX_RESTAURANTS

logger = logging.getLogger(__name__)


class DataLoader:
    """Handles loading and caching of restaurant data from Hugging Face.
    
    This class manages the data ingestion pipeline, including:
    - Downloading data from Hugging Face datasets
    - Caching data locally for faster subsequent loads
    - Limiting dataset size for performance
    
    Attributes:
        cache_dir: Directory for local data cache
        max_restaurants: Maximum number of restaurants to load
        cache_file: Path to cached parquet file
        df: Loaded DataFrame
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, max_restaurants: int = MAX_RESTAURANTS):
        """Initialize the data loader.
        
        Args:
            cache_dir: Directory for caching data locally
            max_restaurants: Maximum number of restaurants to load
        """
        self.cache_dir = cache_dir or DATA_CACHE_DIR
        self.max_restaurants = max_restaurants
        self.cache_file = self.cache_dir / "zomato_restaurants.parquet"
        self.df: Optional[pd.DataFrame] = None
        
    def load(self, force_reload: bool = False) -> pd.DataFrame:
        """Load dataset from cache or Hugging Face.
        
        First checks for local cache, then downloads from Hugging Face
        if cache doesn't exist or force_reload is True.
        
        Args:
            force_reload: If True, reload from Hugging Face even if cache exists
            
        Returns:
            DataFrame with restaurant data
            
        Raises:
            Exception: If dataset loading fails
        """
        if not force_reload and self.cache_file.exists():
            logger.info("Loading data from cache...")
            self.df = pd.read_parquet(self.cache_file)
            logger.info(f"Loaded {len(self.df)} restaurants from cache")
            return self.df
        
        logger.info("Loading data from Hugging Face...")
        try:
            # Load dataset from Hugging Face
            dataset = load_dataset(DATASET_NAME, split="train")
            self.df = dataset.to_pandas()
            
            # Limit dataset size for performance
            if len(self.df) > self.max_restaurants:
                self.df = self.df.head(self.max_restaurants)
                logger.info(f"Limited dataset to {self.max_restaurants} restaurants")
                
            logger.info(f"Loaded {len(self.df)} restaurants from Hugging Face")
            
            # Save to cache
            self._save_cache()
            
            return self.df
            
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            raise
    
    def _save_cache(self):
        """Save loaded data to local cache.
        
        Stores the DataFrame as a Parquet file for efficient
        subsequent loading.
        """
        if self.df is not None:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.df.to_parquet(self.cache_file)
            logger.info(f"Data cached to {self.cache_file}")
    
    def get_data(self) -> pd.DataFrame:
        """Get loaded data, loading if necessary.
        
        Returns:
            DataFrame with restaurant data
        """
        if self.df is None:
            self.load()
        return self.df
    
    def clear_cache(self):
        """Clear local cache file.
        
        Removes the cached parquet file to force fresh download
        on next load.
        """
        if self.cache_file.exists():
            self.cache_file.unlink()
            logger.info("Cache cleared")
    
    def get_data_summary(self) -> dict:
        """Get summary statistics of loaded data.
        
        Returns:
            Dictionary with data summary
        """
        df = self.get_data()
        
        return {
            "total_restaurants": len(df),
            "columns": list(df.columns),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
            "has_cached": self.cache_file.exists()
        }
