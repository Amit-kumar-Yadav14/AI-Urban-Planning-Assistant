#!/usr/bin/env python3
"""Quick test to verify department stays correct"""
import asyncio
from langgraph_workflow import process_message

async def test():
    print("Testing waste report with location that could be misclassified...")
    print()
    
    # Step 1: Greeting
    r1 = await process_message("hi", "test_waste_001")
    print(f"[1] User: hi")
    print(f"    Bot: {r1['response'][:60]}...")
    print()
    
    # Step 2: Report garbage (should be waste dept)
    r2 = await process_message("garbage overflowing", "test_waste_001")
    print(f"[2] User: garbage overflowing")
    print(f"    Bot: {r2['response'][:60]}...")
    print(f"    Department: {r2['department']}")
    print()
    
    # Step 3: Severity
    r3 = await process_message("5", "test_waste_001")
    print(f"[3] User: 5")
    print(f"    Bot: {r3['response'][:60]}...")
    print(f"    Department: {r3['department']}")
    print()
    
    # Step 4: Location (words like "railway" should NOT change dept to traffic!)
    r4 = await process_message("near railway station", "test_waste_001")
    print(f"[4] User: near railway station")
    print(f"    Bot: {r4['response']}")
    print(f"    Department: {r4['department']}")
    print()
    
    # Verify
    if "waste" in r4['response'].lower():
        print("SUCCESS! Department is correctly identified as WASTE")
    else:
        print(f"FAILED! Expected 'waste' in response but got: {r4['response']}")

asyncio.run(test())
