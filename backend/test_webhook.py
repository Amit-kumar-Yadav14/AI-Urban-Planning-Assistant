#!/usr/bin/env python3
"""
Test webhook to Relay/Google Sheet
"""
import os
from dotenv import load_dotenv
from webhook_client import send_webhook

load_dotenv()

print("Testing Webhook to Relay/Google Sheet...")
print("=" * 60)

# Test data
test_report = {
    "location": "near railway station",
    "issue_description": "garbage overflowing",
    "severity_level": 7,
    "department": "waste"
}

print(f"Webhook URL: {os.getenv('WEBHOOK_URL')[:50]}...")
print(f"Sending test data: {test_report}")
print()

result = send_webhook(test_report)

print()
print("=" * 60)
if result:
    print("SUCCESS! Check your Google Sheet - the row should appear there")
else:
    print("FAILED - Check webhook URL and Relay configuration")
