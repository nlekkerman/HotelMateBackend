"""
Test that action keywords work anywhere in the phrase, not just at the start
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from voice_recognition.command_parser import parse_voice_command


def test_flexible_action_positions():
    """Test action keywords can appear anywhere"""
    print("=" * 60)
    print("TEST: Flexible Action Keyword Positions")
    print("=" * 60)
    
    test_cases = [
        # Action at START
        {
            "input": "count budweiser bottle 7 cases 3 bottles",
            "expected_action": "count",
            "expected_item": "budweiser",
        },
        # Action in MIDDLE
        {
            "input": "budweiser bottle count 7 cases 3 bottles",
            "expected_action": "count",
            "expected_item": "budweiser",
        },
        # Action at END
        {
            "input": "budweiser bottle 7 cases 3 bottles count",
            "expected_action": "count",
            "expected_item": "budweiser",
        },
        # Using "I have" (implicit count)
        {
            "input": "I have budweiser 7 cases",
            "expected_action": "count",
            "expected_item": "budweiser",
        },
        # Using "there are" (implicit count)
        {
            "input": "budweiser there are 7 cases",
            "expected_action": "count",
            "expected_item": "budweiser",
        },
        # Using "got" (implicit count)
        {
            "input": "budweiser got 7",
            "expected_action": "count",
            "expected_item": "budweiser",
        },
        # Purchase in middle
        {
            "input": "heineken purchase 2 cases",
            "expected_action": "purchase",
            "expected_item": "heineken",
        },
        # Waste at end
        {
            "input": "corona 1.5 waste",
            "expected_action": "waste",
            "expected_item": "corona",
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        try:
            result = parse_voice_command(test["input"])
            
            action_match = result["action"] == test["expected_action"]
            item_contains = test["expected_item"].lower() in result["item_identifier"].lower()
            
            if action_match and item_contains:
                print(f"✓ PASS: '{test['input']}'")
                print(f"  → {result['action']} {result['item_identifier']} {result['value']}")
                passed += 1
            else:
                print(f"✗ FAIL: '{test['input']}'")
                if not action_match:
                    print(f"  Action: expected {test['expected_action']}, got {result['action']}")
                if not item_contains:
                    print(f"  Item: expected '{test['expected_item']}' in '{result['item_identifier']}'")
                failed += 1
        except Exception as e:
            print(f"✗ FAIL: '{test['input']}'")
            print(f"  Error: {e}")
            failed += 1
        
        print()
    
    print(f"Results: {passed} passed, {failed} failed\n")
    
    if failed == 0:
        print("🎉 All flexible action position tests passed!")
        print("✅ Action keywords work anywhere in the phrase")
        return 0
    else:
        print(f"⚠️ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(test_flexible_action_positions())
