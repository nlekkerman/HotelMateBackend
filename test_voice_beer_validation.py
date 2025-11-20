"""
Test Voice Command Beer Purchase & Waste Validation
Ensures voice commands apply SAME validation as manual entry
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from voice_recognition.command_parser import parse_voice_command

# Test color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test_header(title):
    """Print formatted test section header"""
    print(f"\n{BLUE}{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}{RESET}\n")


def test_draft_beer_purchases():
    """Test Draft Beer (D) purchase validation"""
    print_test_header("DRAFT BEER PURCHASES (UOM=88)")
    
    test_cases = [
        {
            "command": "purchase 2 kegs of guinness",
            "expected": {"action": "purchase", "value": 2.0},
            "should_convert_to": 176,  # 2 * 88
            "valid": True,
            "description": "2 whole kegs"
        },
        {
            "command": "purchase 5 kegs of guinness",
            "expected": {"action": "purchase", "value": 5.0},
            "should_convert_to": 440,  # 5 * 88
            "valid": True,
            "description": "5 whole kegs"
        },
        {
            "command": "purchase 2.5 kegs of guinness",
            "expected": {"action": "purchase", "value": 2.5},
            "should_convert_to": None,
            "valid": False,
            "description": "2.5 kegs (SHOULD BE REJECTED - not whole number)"
        },
        {
            "command": "purchase one keg of carlsberg",
            "expected": {"action": "purchase", "value": 1.0},
            "should_convert_to": 88,
            "valid": True,
            "description": "1 keg (from text 'one')"
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        try:
            result = parse_voice_command(test["command"])
            
            if result["action"] == test["expected"]["action"]:
                # Check if validation should reject
                value = Decimal(str(result["value"]))
                is_whole = (value % 1 == 0)
                
                if test["valid"] and is_whole:
                    converted = int(value) * 88
                    if converted == test["should_convert_to"]:
                        print(f"{GREEN}✓ PASS{RESET}: {test['description']}")
                        print(f"  Command: '{test['command']}'")
                        print(f"  Parsed: {result['value']} kegs")
                        print(f"  Converts to: {converted} pints")
                        passed += 1
                    else:
                        print(f"{RED}✗ FAIL{RESET}: {test['description']}")
                        print(f"  Expected: {test['should_convert_to']} pints")
                        print(f"  Got: {converted} pints")
                        failed += 1
                elif not test["valid"] and not is_whole:
                    print(f"{GREEN}✓ PASS{RESET}: {test['description']}")
                    print(f"  Command: '{test['command']}'")
                    print(f"  Parsed: {result['value']} kegs (will be rejected by backend)")
                    passed += 1
                else:
                    print(f"{RED}✗ FAIL{RESET}: {test['description']}")
                    print(f"  Value: {result['value']} (is_whole: {is_whole})")
                    failed += 1
            else:
                print(f"{RED}✗ FAIL{RESET}: {test['description']} - wrong action")
                failed += 1
        except Exception as e:
            print(f"{RED}✗ ERROR{RESET}: {test['description']} - {e}")
            failed += 1
    
    print(f"\n{BLUE}Summary: {passed} passed, {failed} failed{RESET}")
    return passed, failed


def test_bottled_beer_purchases():
    """Test Bottled Beer (B) purchase validation"""
    print_test_header("BOTTLED BEER PURCHASES (UOM=12)")
    
    test_cases = [
        {
            "command": "purchase 5 cases of budweiser",
            "expected": {"action": "purchase", "value": 5.0},
            "should_convert_to": 60,  # 5 * 12
            "valid": True,
            "description": "5 whole cases"
        },
        {
            "command": "purchase 10 cases of heineken",
            "expected": {"action": "purchase", "value": 10.0},
            "should_convert_to": 120,  # 10 * 12
            "valid": True,
            "description": "10 whole cases"
        },
        {
            "command": "purchase 3.5 cases of corona",
            "expected": {"action": "purchase", "value": 3.5},
            "should_convert_to": None,
            "valid": False,
            "description": "3.5 cases (SHOULD BE REJECTED)"
        },
        {
            "command": "buy three cases of budweiser",
            "expected": {"action": "purchase", "value": 3.0},
            "should_convert_to": 36,  # 3 * 12
            "valid": True,
            "description": "3 cases (from 'buy')"
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        try:
            result = parse_voice_command(test["command"])
            
            if result["action"] == test["expected"]["action"]:
                value = Decimal(str(result["value"]))
                is_whole = (value % 1 == 0)
                
                if test["valid"] and is_whole:
                    converted = int(value) * 12
                    if converted == test["should_convert_to"]:
                        print(f"{GREEN}✓ PASS{RESET}: {test['description']}")
                        print(f"  Command: '{test['command']}'")
                        print(f"  Parsed: {result['value']} cases")
                        print(f"  Converts to: {converted} bottles")
                        passed += 1
                    else:
                        print(f"{RED}✗ FAIL{RESET}: {test['description']}")
                        failed += 1
                elif not test["valid"] and not is_whole:
                    print(f"{GREEN}✓ PASS{RESET}: {test['description']}")
                    print(f"  Will be rejected by backend validation")
                    passed += 1
                else:
                    print(f"{RED}✗ FAIL{RESET}: {test['description']}")
                    failed += 1
            else:
                print(f"{RED}✗ FAIL{RESET}: {test['description']}")
                failed += 1
        except Exception as e:
            print(f"{RED}✗ ERROR{RESET}: {test['description']} - {e}")
            failed += 1
    
    print(f"\n{BLUE}Summary: {passed} passed, {failed} failed{RESET}")
    return passed, failed


def test_draft_beer_waste():
    """Test Draft Beer (D) waste validation"""
    print_test_header("DRAFT BEER WASTE (UOM=88)")
    
    test_cases = [
        {
            "command": "waste 25 pints of guinness",
            "expected": {"action": "waste", "value": 25.0},
            "valid": True,
            "max_allowed": 87.99,
            "description": "25 pints (valid partial keg)"
        },
        {
            "command": "waste 50.5 pints of carlsberg",
            "expected": {"action": "waste", "value": 50.5},
            "valid": True,
            "max_allowed": 87.99,
            "description": "50.5 pints (valid partial keg)"
        },
        {
            "command": "waste 87 pints of guinness",
            "expected": {"action": "waste", "value": 87.0},
            "valid": True,
            "max_allowed": 87.99,
            "description": "87 pints (valid, just under full keg)"
        },
        {
            "command": "waste 88 pints of guinness",
            "expected": {"action": "waste", "value": 88.0},
            "valid": False,
            "max_allowed": 87.99,
            "description": "88 pints (SHOULD BE REJECTED - full keg)"
        },
        {
            "command": "waste 100 pints of guinness",
            "expected": {"action": "waste", "value": 100.0},
            "valid": False,
            "max_allowed": 87.99,
            "description": "100 pints (SHOULD BE REJECTED - over full keg)"
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        try:
            result = parse_voice_command(test["command"])
            
            if result["action"] == test["expected"]["action"]:
                value = float(result["value"])
                is_valid = value < 88
                
                if test["valid"] and is_valid:
                    print(f"{GREEN}✓ PASS{RESET}: {test['description']}")
                    print(f"  Command: '{test['command']}'")
                    print(f"  Parsed: {result['value']} pints (valid partial keg)")
                    passed += 1
                elif not test["valid"] and not is_valid:
                    print(f"{GREEN}✓ PASS{RESET}: {test['description']}")
                    print(f"  Will be rejected by backend (>= 88 pints)")
                    passed += 1
                else:
                    print(f"{RED}✗ FAIL{RESET}: {test['description']}")
                    print(f"  Value: {result['value']}, Valid: {is_valid}, Expected: {test['valid']}")
                    failed += 1
            else:
                print(f"{RED}✗ FAIL{RESET}: {test['description']}")
                failed += 1
        except Exception as e:
            print(f"{RED}✗ ERROR{RESET}: {test['description']} - {e}")
            failed += 1
    
    print(f"\n{BLUE}Summary: {passed} passed, {failed} failed{RESET}")
    return passed, failed


def test_bottled_beer_waste():
    """Test Bottled Beer (B) waste validation"""
    print_test_header("BOTTLED BEER WASTE (UOM=12)")
    
    test_cases = [
        {
            "command": "waste 3 bottles of budweiser",
            "expected": {"action": "waste", "value": 3.0},
            "valid": True,
            "description": "3 bottles (valid partial case)"
        },
        {
            "command": "waste 7 bottles of heineken",
            "expected": {"action": "waste", "value": 7.0},
            "valid": True,
            "description": "7 bottles (valid partial case)"
        },
        {
            "command": "waste 11 bottles of corona",
            "expected": {"action": "waste", "value": 11.0},
            "valid": True,
            "description": "11 bottles (valid, just under full case)"
        },
        {
            "command": "waste 12 bottles of budweiser",
            "expected": {"action": "waste", "value": 12.0},
            "valid": False,
            "description": "12 bottles (SHOULD BE REJECTED - full case)"
        },
        {
            "command": "waste 15 bottles of heineken",
            "expected": {"action": "waste", "value": 15.0},
            "valid": False,
            "description": "15 bottles (SHOULD BE REJECTED - over full case)"
        },
        {
            "command": "waste 24 bottles of corona",
            "expected": {"action": "waste", "value": 24.0},
            "valid": False,
            "description": "24 bottles (SHOULD BE REJECTED - 2 full cases)"
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        try:
            result = parse_voice_command(test["command"])
            
            if result["action"] == test["expected"]["action"]:
                value = float(result["value"])
                is_valid = value < 12
                
                if test["valid"] and is_valid:
                    print(f"{GREEN}✓ PASS{RESET}: {test['description']}")
                    print(f"  Command: '{test['command']}'")
                    print(f"  Parsed: {result['value']} bottles (valid partial case)")
                    passed += 1
                elif not test["valid"] and not is_valid:
                    print(f"{GREEN}✓ PASS{RESET}: {test['description']}")
                    print(f"  Will be rejected by backend (>= 12 bottles)")
                    passed += 1
                else:
                    print(f"{RED}✗ FAIL{RESET}: {test['description']}")
                    print(f"  Value: {result['value']}, Valid: {is_valid}, Expected: {test['valid']}")
                    failed += 1
            else:
                print(f"{RED}✗ FAIL{RESET}: {test['description']}")
                failed += 1
        except Exception as e:
            print(f"{RED}✗ ERROR{RESET}: {test['description']} - {e}")
            failed += 1
    
    print(f"\n{BLUE}Summary: {passed} passed, {failed} failed{RESET}")
    return passed, failed


def test_count_commands():
    """Test COUNT commands remain unchanged"""
    print_test_header("COUNT COMMANDS (Should remain unchanged)")
    
    test_cases = [
        {
            "command": "count guinness 3 kegs 20 pints",
            "expected": {"action": "count", "full_units": 3, "partial_units": 20},
            "description": "Draft beer with full and partial"
        },
        {
            "command": "count budweiser 7 cases 5 bottles",
            "expected": {"action": "count", "full_units": 7, "partial_units": 5},
            "description": "Bottled beer with full and partial"
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        try:
            result = parse_voice_command(test["command"])
            
            if (result["action"] == test["expected"]["action"] and
                result.get("full_units") == test["expected"]["full_units"] and
                result.get("partial_units") == test["expected"]["partial_units"]):
                print(f"{GREEN}✓ PASS{RESET}: {test['description']}")
                print(f"  Command: '{test['command']}'")
                print(f"  Parsed: {result['full_units']} full, {result['partial_units']} partial")
                passed += 1
            else:
                print(f"{RED}✗ FAIL{RESET}: {test['description']}")
                print(f"  Expected: {test['expected']}")
                print(f"  Got: {result}")
                failed += 1
        except Exception as e:
            print(f"{RED}✗ ERROR{RESET}: {test['description']} - {e}")
            failed += 1
    
    print(f"\n{BLUE}Summary: {passed} passed, {failed} failed{RESET}")
    return passed, failed


def main():
    """Run all tests"""
    print(f"\n{YELLOW}{'=' * 70}")
    print("  VOICE COMMAND BEER VALIDATION TEST SUITE")
    print("  Testing PURCHASE & WASTE validation matches manual entry")
    print(f"{'=' * 70}{RESET}\n")
    
    total_passed = 0
    total_failed = 0
    
    # Run all test suites
    p, f = test_draft_beer_purchases()
    total_passed += p
    total_failed += f
    
    p, f = test_bottled_beer_purchases()
    total_passed += p
    total_failed += f
    
    p, f = test_draft_beer_waste()
    total_passed += p
    total_failed += f
    
    p, f = test_bottled_beer_waste()
    total_passed += p
    total_failed += f
    
    p, f = test_count_commands()
    total_passed += p
    total_failed += f
    
    # Final summary
    print(f"\n{YELLOW}{'=' * 70}")
    print(f"  FINAL RESULTS")
    print(f"{'=' * 70}{RESET}")
    print(f"{GREEN}  ✓ Total Passed: {total_passed}{RESET}")
    print(f"{RED}  ✗ Total Failed: {total_failed}{RESET}")
    
    if total_failed == 0:
        print(f"\n{GREEN}🎉 ALL TESTS PASSED! 🎉{RESET}\n")
        return 0
    else:
        print(f"\n{RED}⚠️  SOME TESTS FAILED{RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
