import asyncio
import sys
sys.path.insert(0, '.')
from langgraph_workflow import process_message

async def test():
    """Test the full conversation flow"""
    print("Testing Firebase Integration...\n")
    
    session_id = "test-firebase-session"
    
    # Test 1: Greeting
    result1 = await process_message("hi", session_id)
    print(f"[1] User: hi")
    print(f"    Bot: {result1['response'][:60]}...")
    print(f"    Status: {result1['status']}")
    print()
    
    # Test 2: Issue
    result2 = await process_message("traffic jam on highway", session_id)
    print(f"[2] User: traffic jam on highway")
    print(f"    Bot: {result2['response'][:60]}...")
    print(f"    Department: {result2['department']}")
    print()
    
    # Test 3: Severity
    result3 = await process_message("8", session_id)
    print(f"[3] User: 8")
    print(f"    Bot: {result3['response'][:60]}...")
    print()
    
    # Test 4: Location
    result4 = await process_message("highway 101", session_id)
    print(f"[4] User: highway 101")
    print(f"    Bot: {result4['response'][:60]}...")
    print()
    
    print("SUCCESS! All tests passed without state errors!")

asyncio.run(test())
