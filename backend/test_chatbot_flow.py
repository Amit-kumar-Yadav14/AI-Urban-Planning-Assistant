#!/usr/bin/env python3
"""
Test script to verify the chatbot flow works correctly with the exact sequence.
Test scenario: Waste reporting with severity and location.
"""

import asyncio
import sys
sys.path.insert(0, '.')

from langgraph_workflow import process_message

async def test_chatbot_flow():
    """Test the complete chatbot flow"""
    print("=" * 60)
    print("TESTING CSR WASTE REPORTING CHATBOT FLOW")
    print("=" * 60)
    
    session_id = "test_session_001"
    
    # Step 1: Initial greeting
    print("\n[STEP 1] User: hi")
    response = await process_message("hi", session_id)
    print(f"Bot: {response['response']}")
    print(f"Status: {response['status']}")
    assert "help" in response['response'].lower(), "Should offer to help"
    
    # Step 2: Report issue
    print("\n[STEP 2] User: there is garbage overflowing")
    response = await process_message("there is garbage overflowing", session_id)
    print(f"Bot: {response['response']}")
    print(f"Status: {response['status']}")
    assert "scale" in response['response'].lower(), "Should ask for severity"
    assert response['status'] == "awaiting_severity", f"Status should be 'awaiting_severity', got '{response['status']}'"
    
    # Step 3: Severity (numeric answer)
    print("\n[STEP 3] User: 7")
    response = await process_message("7", session_id)
    print(f"Bot: {response['response']}")
    print(f"Status: {response['status']}")
    assert "location" in response['response'].lower(), f"Should ask for location, but got: {response['response']}"
    assert response['status'] == "awaiting_location", f"Status should be 'awaiting_location', got '{response['status']}'"
    
    # Step 4: Location
    print("\n[STEP 4] User: near railway station")
    response = await process_message("near railway station", session_id)
    print(f"Bot: {response['response']}")
    print(f"Status: {response['status']}")
    assert "submitted" in response['response'].lower(), "Should confirm submission"
    assert response['status'] == "complete", f"Status should be 'complete', got '{response['status']}'"
    assert response['department'], "Should have department set"
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nExpected conversation flow verified:")
    print("1. Greeting accepted ✓")
    print("2. Issue description → asks for severity ✓")
    print("3. Severity (7) → asks for location (no repeat!) ✓")
    print("4. Location provided → confirms submission ✓")


async def test_severity_extraction():
    """Test severity extraction directly"""
    print("\n" + "=" * 60)
    print("TESTING SEVERITY EXTRACTION")
    print("=" * 60)
    
    from langgraph_workflow import extract_severity
    
    test_cases = [
        ("7", 7, "Standalone number"),
        ("7/10", 7, "Fraction format"),
        ("severity 8", 8, "With keyword"),
        ("level 5", 5, "Level keyword"),
        ("10", 10, "Max severity"),
        ("1", 1, "Min severity"),
    ]
    
    for message, expected, description in test_cases:
        result = extract_severity(message)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{message}' → {result} (expected {expected}) - {description}")
        assert result == expected, f"Failed for '{message}'"
    
    print("\n✓ ALL SEVERITY EXTRACTION TESTS PASSED!")


async def test_location_extraction():
    """Test location extraction"""
    print("\n" + "=" * 60)
    print("TESTING LOCATION EXTRACTION")
    print("=" * 60)
    
    from langgraph_workflow import extract_location
    
    test_cases = [
        ("near railway station", "near railway station", "Landmark with preposition"),
        ("downtown", "downtown", "Simple location"),
        ("main street", "main street", "Street name"),
        ("highway 101", "highway 101", "Highway"),
    ]
    
    for message, expected_substring, description in test_cases:
        result = extract_location(message)
        status = "✓" if result and expected_substring.lower() in result.lower() else "✗"
        print(f"{status} '{message}' → '{result}' - {description}")
        assert result and expected_substring.lower() in result.lower(), f"Failed for '{message}'"
    
    print("\n✓ ALL LOCATION EXTRACTION TESTS PASSED!")


async def main():
    """Run all tests"""
    try:
        await test_severity_extraction()
        await test_location_extraction()
        await test_chatbot_flow()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
