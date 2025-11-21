"""
Test PURCHASE validation - must be full units only (no partial)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from voice_recognition.command_parser import parse_voice_command

# Test purchase commands
test_cases = [
    # VALID purchases (full units only)
    {
        "cmd": "purchase 3 kegs of guinness",
        "expected_valid": True,
        "expected_value": 3.0,
        "description": "✅ Valid: 3 whole kegs"
    },
    {
        "cmd": "purchase 5 cases of budweiser",
        "expected_valid": True,
        "expected_value": 5.0,
        "description": "✅ Valid: 5 whole cases"
    },
    {
        "cmd": "purchase 2 bottles of jameson",
        "expected_valid": True,
        "expected_value": 2.0,
        "description": "✅ Valid: 2 whole bottles"
    },
    
    # INVALID purchases (partial units)
    {
        "cmd": "purchase 3 cases 5 bottles of budweiser",
        "expected_valid": False,
        "description": "❌ Invalid: 3 cases + 5 bottles (has partial)"
    },
    {
        "cmd": "purchase 2 kegs 20 pints of guinness",
        "expected_valid": False,
        "description": "❌ Invalid: 2 kegs + 20 pints (has partial)"
    },
    {
        "cmd": "purchase 3.5 kegs of carlsberg",
        "expected_valid": True,  # Parser will accept, backend will reject
        "expected_value": 3.5,
        "description": "⚠️  Parser accepts (backend will reject non-integer)"
    },
]

# Test count commands (should accept full+partial)
count_cases = [
    {
        "cmd": "count budweiser 5 cases 5 bottles",
        "expected_valid": True,
        "expected_full": 5,
        "expected_partial": 5.0,
        "description": "✅ Valid: COUNT with full + partial"
    },
    {
        "cmd": "count guinness 2 kegs 20 pints",
        "expected_valid": True,
        "expected_full": 2,
        "expected_partial": 20.0,
        "description": "✅ Valid: COUNT with full + partial"
    },
]

print("\n" + "="*80)
print("TESTING: PURCHASE Commands (Must be Full Units ONLY)")
print("="*80 + "\n")

passed = 0
failed = 0

for test in test_cases:
    print(f"\nTest: {test['description']}")
    print(f"Command: '{test['cmd']}'")
    
    try:
        result = parse_voice_command(test['cmd'])
        
        if test['expected_valid']:
            # Should succeed
            print(f"  ✓ Parsed successfully")
            print(f"  Action: {result['action']}")
            print(f"  Value: {result['value']}")
            
            if 'expected_value' in test and result['value'] == test['expected_value']:
                print(f"  ✓ Value matches expected: {test['expected_value']}")
                passed += 1
            else:
                print(f"  ✗ Value mismatch!")
                failed += 1
        else:
            # Should have failed but didn't
            print(f"  ✗ FAIL: Should have been rejected!")
            print(f"  Got: {result}")
            failed += 1
            
    except ValueError as e:
        if not test['expected_valid']:
            # Should fail and did fail
            print(f"  ✓ Correctly rejected: {e}")
            passed += 1
        else:
            # Should succeed but failed
            print(f"  ✗ FAIL: Unexpected error: {e}")
            failed += 1

print("\n" + "="*80)
print("TESTING: COUNT Commands (Can have Full + Partial)")
print("="*80 + "\n")

for test in count_cases:
    print(f"\nTest: {test['description']}")
    print(f"Command: '{test['cmd']}'")
    
    try:
        result = parse_voice_command(test['cmd'])
        
        print(f"  ✓ Parsed successfully")
        print(f"  Action: {result['action']}")
        print(f"  Full Units: {result.get('full_units', 'N/A')}")
        print(f"  Partial Units: {result.get('partial_units', 'N/A')}")
        
        if (result.get('full_units') == test['expected_full'] and 
            result.get('partial_units') == test['expected_partial']):
            print(f"  ✓ Values match expected")
            passed += 1
        else:
            print(f"  ✗ Value mismatch!")
            failed += 1
            
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        failed += 1

print("\n" + "="*80)
print(f"RESULTS: {passed} passed, {failed} failed")
print("="*80 + "\n")

if failed == 0:
    print("🎉 ALL TESTS PASSED!")
else:
    print(f"⚠️  {failed} TESTS FAILED")
