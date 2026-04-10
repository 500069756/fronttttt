"""Test Grok LLM connection and functionality."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()  # Load .env file

from src.phase2_engine import LLMClient


def test_1_api_key_loaded():
    """Test 1: Verify API key is loaded from .env"""
    import os
    api_key = os.getenv("GROK_API_KEY", "")
    
    print("\n" + "=" * 60)
    print("TEST 1: API Key Loaded from .env")
    print("=" * 60)
    
    if api_key and api_key != "your_grok_api_key_here":
        print(f"✅ GROK_API_KEY found (length: {len(api_key)} chars)")
        print(f"   Key starts with: {api_key[:10]}...")
        return True
    else:
        print("❌ GROK_API_KEY not found or not set properly")
        print("   Please set GROK_API_KEY in .env file")
        return False


def test_2_client_initialization():
    """Test 2: Verify LLM client initializes correctly"""
    print("\n" + "=" * 60)
    print("TEST 2: LLM Client Initialization")
    print("=" * 60)
    
    try:
        client = LLMClient()
        info = client.get_client_info()
        
        print(f"✅ Client initialized successfully")
        print(f"   Model: {info['model']}")
        print(f"   API Base: {info['api_base']}")
        print(f"   Max Tokens: {info['max_tokens']}")
        print(f"   Temperature: {info['temperature']}")
        print(f"   Available: {info['available']}")
        return info['available']
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False


def test_3_simple_api_call():
    """Test 3: Make a simple API call to Grok"""
    print("\n" + "=" * 60)
    print("TEST 3: Simple API Call to Grok")
    print("=" * 60)
    
    try:
        client = LLMClient()
        
        # Simple test prompt
        response = client._make_request(
            "Reply with just 'Hello! Grok is working!' and nothing else."
        )
        
        if response:
            print(f"✅ API call successful!")
            print(f"   Response: {response[:100]}...")
            return True
        else:
            print("❌ API call returned no response")
            return False
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False


def test_4_restaurant_explanation():
    """Test 4: Generate a restaurant recommendation explanation"""
    print("\n" + "=" * 60)
    print("TEST 4: Restaurant Explanation Generation")
    print("=" * 60)
    
    try:
        client = LLMClient()
        
        # Test with sample restaurant
        restaurant = {
            "name": "Test Restaurant",
            "location": "Bangalore",
            "cuisines": "Italian, Continental",
            "rating": 4.5,
            "cost": 800,
            "budget_category": "medium"
        }
        
        preferences = {
            "location": "Bangalore",
            "budget": "medium",
            "cuisines": ["Italian"]
        }
        
        explanation = client.get_explanation(restaurant, preferences)
        
        print(f"✅ Explanation generated!")
        print(f"   Restaurant: {restaurant['name']}")
        print(f"   Explanation: {explanation[:150]}...")
        return True
    except Exception as e:
        print(f"❌ Explanation generation failed: {e}")
        return False


def main():
    """Run all connection tests."""
    print("\n" + "=" * 60)
    print("GROK LLM CONNECTION TESTS")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("API Key Loaded", test_1_api_key_loaded()))
    results.append(("Client Initialization", test_2_client_initialization()))
    
    # Only run API tests if client is available
    if results[1][1]:  # If client initialized successfully
        results.append(("Simple API Call", test_3_simple_api_call()))
        results.append(("Restaurant Explanation", test_4_restaurant_explanation()))
    else:
        print("\n⚠️ Skipping API tests - client not available")
        results.append(("Simple API Call", False))
        results.append(("Restaurant Explanation", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    
    print(f"\nTotal: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n🎉 All tests passed! Grok LLM is properly connected.")
    elif results[0][1] and results[1][1]:
        print("\n⚠️ Client connected but API calls failed. Check your API key validity.")
    else:
        print("\n❌ Connection failed. Please check your .env file configuration.")


if __name__ == "__main__":
    main()
