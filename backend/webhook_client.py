import os
import httpx
from typing import Dict
import json


def send_webhook(data: Dict):
    """Send webhook POST request with report data to Relay/Google Sheet"""
    webhook_url = os.getenv("WEBHOOK_URL")
    
    if not webhook_url:
        print("Warning: WEBHOOK_URL not set. Webhook not sent.")
        return False
    
    # Prepare payload with field names matching Google Sheet columns
    # Google Sheet expects: Location, Issue, Severity, Department
    payload = {
        "Location": str(data.get("location", "")),
        "Issue": str(data.get("issue_description", "")),
        "Severity": int(data.get("severity_level", 0)),
        "Department": str(data.get("department", "")).title()  # Capitalize department name
    }
    
    # Ensure severity is between 1-10
    if not (1 <= payload["Severity"] <= 10):
        payload["Severity"] = 5
    
    try:
        response = httpx.post(
            webhook_url, 
            json=payload, 
            timeout=10.0,
            headers={"Content-Type": "application/json"}
        )
        
        # Check if successful
        if response.status_code in [200, 201, 202, 204]:
            print(f"Webhook sent successfully (Status: {response.status_code})")
            return True
        else:
            print(f"Webhook returned status {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"Webhook request failed: {str(e)}")
        return False


