import pandas as pd
from pathlib import Path
import sys

# Add project root to path to use config
sys.path.append(str(Path(__file__).parent.parent))
from src.phase1_foundation.data.loader import DataLoader

def main():
    loader = DataLoader()
    try:
        df = loader.load()
        print("Raw Dataset Columns:", list(df.columns))
        print("\nFirst 5 rows (location-related):")
        loc_cols = [c for c in df.columns if any(x in c.lower() for x in ['loc', 'city', 'area', 'address'])]
        print(df[loc_cols].head())
        
        # Check specific columns we expect
        potential_city = ['city', 'restaurant_location', 'location', 'area']
        potential_locality = ['locality', 'subzone', 'address']
        
        for col in potential_city + potential_locality:
            if col in df.columns:
                print(f"\nUnique values in '{col}' (first 10):", df[col].unique()[:10])
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
