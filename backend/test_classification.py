import requests
import json

BASE_URL = "http://localhost:8000"

def test_classification():
    """Test the LLM-based classification endpoint"""
    
    test_cases = [
        "There's a traffic jam on highway 101",
        "Garbage is overflowing near my house",
        "The street lights are broken in the park",
        "Car accident on main street",
        "Too much pollution and litter",
        "Need solar panels installed"
    ]
    
    print("=" * 70)
    print("LLM CLASSIFICATION TEST - Three Departments")
    print("=" * 70)
    print()
    
    for message in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/classify",
                json={"message": message},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Message: {message}")
                print(f"  → Department: {data['department']}")
                print(f"  → Confidence: {data['confidence']}")
                print()
            else:
                print(f"Error for '{message}': {response.status_code}")
                print()
        except Exception as e:
            print(f"Error: {e}")
            print()

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("Health Check:")
        print(json.dumps(response.json(), indent=2))
        print()
    except Exception as e:
        print(f"Health check failed: {e}")

if __name__ == "__main__":
    print("\nTesting Backend API...\n")
    
    test_health()
    test_classification()
    
    print("=" * 70)
    print("All tests completed!")
    print("=" * 70)
