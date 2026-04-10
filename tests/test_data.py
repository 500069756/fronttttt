"""Tests for data loading and preprocessing."""
import pytest
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.phase1_foundation import DataLoader, DataPreprocessor


class TestDataLoader:
    """Test cases for DataLoader."""
    
    def test_loader_initialization(self):
        """Test DataLoader initializes correctly."""
        loader = DataLoader()
        assert loader.df is None
        assert loader.max_restaurants > 0
    
    def test_get_data_summary(self):
        """Test data summary method."""
        loader = DataLoader()
        summary = loader.get_data_summary()
        assert "total_restaurants" in summary
        assert "columns" in summary


class TestDataPreprocessor:
    """Test cases for DataPreprocessor."""
    
    def test_preprocessor_initialization(self):
        """Test DataPreprocessor initializes correctly."""
        preprocessor = DataPreprocessor()
        assert preprocessor.processed_df is None
        assert len(preprocessor.available_locations) == 0
    
    def test_parse_cuisines(self):
        """Test cuisine parsing."""
        preprocessor = DataPreprocessor()
        
        # Test single cuisine
        result = preprocessor._parse_cuisines("Italian")
        assert result == ["Italian"]
        
        # Test multiple cuisines
        result = preprocessor._parse_cuisines("Italian, Chinese, Indian")
        assert "Italian" in result
        assert "Chinese" in result
        assert "Indian" in result
        
        # Test with different delimiters
        result = preprocessor._parse_cuisines("Italian | Chinese")
        assert len(result) == 2
    
    def test_normalize_cuisine(self):
        """Test cuisine normalization."""
        preprocessor = DataPreprocessor()
        
        assert preprocessor._normalize_cuisine("italian") == "Italian"
        assert preprocessor._normalize_cuisine("NORTH INDIAN") == "North Indian"
    
    def test_handle_missing_values(self):
        """Test missing value handling."""
        preprocessor = DataPreprocessor()
        
        df = pd.DataFrame({
            'name': ['Restaurant A', 'Restaurant B', None],
            'location': ['Location 1', None, 'Location 3'],
            'rating': [4.5, None, 3.5],
            'cost': [500, 800, None]
        })
        
        result = preprocessor._handle_missing_values(df)
        
        # Should drop rows with missing name or location
        assert len(result) < len(df)
        
        # Rating should be filled
        assert result['rating'].isna().sum() == 0
    
    def test_create_budget_categories(self):
        """Test budget category creation."""
        preprocessor = DataPreprocessor()
        
        df = pd.DataFrame({
            'cost': [300, 800, 2000, 500]
        })
        
        result = preprocessor._create_budget_categories(df)
        
        assert 'budget_category' in result.columns
        assert result.loc[0, 'budget_category'] == 'low'
        assert result.loc[1, 'budget_category'] == 'medium'
        assert result.loc[2, 'budget_category'] == 'high'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
