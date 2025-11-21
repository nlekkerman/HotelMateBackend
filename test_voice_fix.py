"""
Test voice command parsing fixes for bottled products
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from voice_recognition.command_parser import parse_voice_command

print("=" * 70)
print("TESTING VOICE COMMAND PARSING FIXES")
print("=" * 70)

test_cases = [
    # Single bottle counts (should parse as simple value)
    {
        "input": "counted grenadine syrup, five and a half bottles",
        "expected": {"action": "count", "value": 5.5},
        "description": "5.5 bottles (single count)"
    },
    {
        "input": "count tito's vodka 7 bottles",
        "expected": {"action": "count", "value": 7},
        "description": "7 bottles (single count)"
    },
    {
        "input": "counted heineken 24 bottles",
        "expected": {"action": "count", "value": 24},
        "description": "24 bottles (single count)"
    },
    
    # Cases + bottles format (should parse as full + partial)
    {
        "input": "count budweiser 3 cases 5 bottles",
        "expected": {"action": "count", "full_units": 3, "partial_units": 5},
        "description": "3 cases 5 bottles (full + partial)"
    },
    {
        "input": "counted bulmers 4 cases 6 bottles",
        "expected": {"action": "count", "full_units": 4, "partial_units": 6},
        "description": "4 cases 6 bottles (full + partial)"
    },
    
    # Dozen format
    {
        "input": "count coca cola 2 dozen 3",
        "expected": {"action": "count", "value": 27},
        "description": "2 dozen 3 (27 total)"
    },
]

print("\n")
for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['description']}")
    print(f"  Input: \"{test['input']}\"")
    
    try:
        result = parse_voice_command(test['input'])
        
        # Check if all expected fields match
        success = True
        for key, expected_value in test['expected'].items():
            actual_value = result.get(key)
            if actual_value != expected_value:
                success = False
                print(f"  ❌ FAILED: {key} = {actual_value}, expected {expected_value}")
        
        if success:
            print(f"  ✅ PASSED")
            print(f"     Parsed: action={result['action']}, value={result.get('value')}, "
                  f"full={result.get('full_units')}, partial={result.get('partial_units')}")
        
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)}")
    
    print()

print("=" * 70)
