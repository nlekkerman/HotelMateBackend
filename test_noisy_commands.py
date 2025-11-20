"""
Test that noisy/conversational voice commands are cleaned properly
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from voice_recognition.command_parser import parse_voice_command


def test_noisy_commands():
    """Test parsing noisy/conversational voice commands"""
    print("=" * 60)
    print("TEST: Noisy/Conversational Voice Commands")
    print("=" * 60)
    
    test_cases = [
        {
            "input": "But why is it bottle, count? Three cases, two bottles.",
            "expected_item": "bottle",
            "expected_action": "count",
            "expected_value": 5,
        },
        {
            "input": "Umm, I think budweiser is count five cases",
            "expected_item": "budweiser",
            "expected_action": "count",
            "expected_value": 5,
        },
        {
            "input": "What is the heineken? Count seven bottles",
            "expected_item": "heineken",
            "expected_action": "count",
            "expected_value": 7,
        },
        {
            "input": "How many? guinness count twelve",
            "expected_item": "guinness",
            "expected_action": "count",
            "expected_value": 12,
        },
        {
            "input": "Ok so budweiser bottle count three cases six bottles",
            "expected_item": "budweiser bottle",
            "expected_action": "count",
            "expected_value": 9,
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        try:
            result = parse_voice_command(test["input"])
            
            action_match = result["action"] == test["expected_action"]
            item_clean = test["expected_item"] in result["item_identifier"]
            value_match = result["value"] == test["expected_value"]
            
            if action_match and item_clean and value_match:
                print(f"✓ PASS: '{test['input'][:50]}...'")
                print(f"  → {result['action']} | '{result['item_identifier']}' | {result['value']}")
                passed += 1
            else:
                print(f"✗ FAIL: '{test['input'][:50]}...'")
                if not action_match:
                    print(f"  Action: expected {test['expected_action']}, got {result['action']}")
                if not item_clean:
                    print(f"  Item: expected '{test['expected_item']}' in '{result['item_identifier']}'")
                if not value_match:
                    print(f"  Value: expected {test['expected_value']}, got {result['value']}")
                failed += 1
        except Exception as e:
            print(f"✗ FAIL: '{test['input'][:50]}...'")
            print(f"  Error: {e}")
            failed += 1
        
        print()
    
    print(f"Results: {passed} passed, {failed} failed\n")
    
    if failed == 0:
        print("🎉 All noisy command tests passed!")
        print("✅ Parser handles conversational/noisy input well")
        return 0
    else:
        print(f"⚠️ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(test_noisy_commands())
