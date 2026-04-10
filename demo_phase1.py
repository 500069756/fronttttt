"""Demo script for Phase 1: Foundation & Data Layer.

This script demonstrates the functionality implemented in Phase 1:
- Data loading from HuggingFace
- Data preprocessing and cleaning
- Basic data exploration
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

import logging
from src.phase1_foundation import DataLoader, DataPreprocessor, setup_logging

# Setup logging
logger = setup_logging(logging.INFO)


def main():
    """Run Phase 1 demonstration."""
    print("=" * 60)
    print("PHASE 1: FOUNDATION & DATA LAYER - DEMO")
    print("=" * 60)
    
    # Step 1: Data Loading
    print("\n📥 Step 1: Loading Data from HuggingFace")
    print("-" * 60)
    
    loader = DataLoader(max_restaurants=100)  # Limit for demo
    
    try:
        raw_data = loader.load()
        print(f"✅ Successfully loaded {len(raw_data)} restaurants")
        print(f"📊 Columns: {list(raw_data.columns)}")
        print(f"💾 Cache file: {loader.cache_file}")
        print(f"💾 Cache exists: {loader.cache_file.exists()}")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Step 2: Data Summary
    print("\n📈 Step 2: Raw Data Summary")
    print("-" * 60)
    
    summary = loader.get_data_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Step 3: Data Preprocessing
    print("\n🔧 Step 3: Preprocessing Data")
    print("-" * 60)
    
    preprocessor = DataPreprocessor()
    processed_data = preprocessor.preprocess(raw_data)
    
    print(f"✅ Preprocessing complete")
    print(f"📊 Processed {len(processed_data)} restaurants")
    
    # Step 4: Preprocessing Summary
    print("\n📊 Step 4: Preprocessing Summary")
    print("-" * 60)
    
    prep_summary = preprocessor.get_preprocessing_summary()
    for key, value in prep_summary.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
    
    # Step 5: Sample Data Preview
    print("\n👀 Step 5: Sample Processed Data")
    print("-" * 60)
    
    sample_cols = ['name', 'location', 'cuisines', 'rating', 'cost', 'budget_category']
    available_cols = [c for c in sample_cols if c in processed_data.columns]
    
    if available_cols:
        sample = processed_data[available_cols].head(3)
        print(sample.to_string(index=False))
    
    # Step 6: Available Values
    print("\n📋 Step 6: Available Locations & Cuisines")
    print("-" * 60)
    
    locations = preprocessor.get_available_locations()[:5]
    cuisines = preprocessor.get_available_cuisines()[:10]
    
    print(f"📍 Sample Locations ({len(preprocessor.available_locations)} total):")
    for loc in locations:
        print(f"  - {loc}")
    
    print(f"\n🍽️ Sample Cuisines ({len(preprocessor.available_cuisines)} total):")
    for i, cuisine in enumerate(cuisines):
        if i % 5 == 0:
            print("  ", end="")
        print(f"{cuisine}", end="  ")
        if (i + 1) % 5 == 0:
            print()
    print()
    
    print("\n" + "=" * 60)
    print("✅ PHASE 1 DEMO COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Set up environment: copy .env.example to .env")
    print("  3. Run tests: pytest tests/")
    print("  4. Proceed to Phase 2: Core Recommendation Engine")


if __name__ == "__main__":
    main()
