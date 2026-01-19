import requests
import json

# Test the chat endpoint
url = "http://localhost:8000/chat"

payload = {
    "message": "Hi, I want to report garbage overflowing near the railway station",
    "session_id": "test-session-123"
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    print("Make sure the backend is running on port 8000!")
