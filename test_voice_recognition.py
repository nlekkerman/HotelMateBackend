"""
Test script for Voice Recognition system
Tests command parser and transcription setup
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from voice_recognition.command_parser import parse_voice_command, convert_number_words
from django.conf import settings


def test_number_word_conversion():
    """Test converting number words to digits"""
    print("=" * 60)
    print("TEST 1: Number Word Conversion")
    print("=" * 60)
    
    test_cases = [
        ("count heineken twenty four", "count heineken 24"),
        ("I have coca cola twelve", "i have coca cola 12"),
        ("purchase guinness three dozen six", "purchase guinness 3 dozen 6"),
        ("waste budweiser two", "waste budweiser 2"),
        ("count corona one dozen five", "count corona 1 dozen 5"),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected in test_cases:
        result = convert_number_words(input_text)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            
        print(f"{status}: '{input_text}'")
        print(f"  Expected: '{expected}'")
        print(f"  Got:      '{result}'")
        print()
    
    print(f"Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_command_parsing():
    """Test parsing voice commands"""
    print("=" * 60)
    print("TEST 2: Command Parsing")
    print("=" * 60)
    
    test_cases = [
        {
            "input": "count heineken 24",
            "expected": {
                "action": "count",
                "item_identifier": "heineken",
                "value": 24,
                "full_units": None,
                "partial_units": None,
            }
        },
        {
            "input": "I have coca cola 2 dozen 6",
            "expected": {
                "action": "count",
                "item_identifier": "coca cola",
                "value": 30,  # 2*12 + 6
                "full_units": 2,
                "partial_units": 6,
            }
        },
        {
            "input": "purchase guinness 3 dozen",
            "expected": {
                "action": "purchase",
                "item_identifier": "guinness",
                "value": 36,  # 3*12
                "full_units": 3,
                "partial_units": 0,
            }
        },
        {
            "input": "waste budweiser 2",
            "expected": {
                "action": "waste",
                "item_identifier": "budweiser",
                "value": 2,
                "full_units": None,
                "partial_units": None,
            }
        },
        {
            "input": "there are corona twelve",
            "expected": {
                "action": "count",
                "item_identifier": "corona",
                "value": 12,
                "full_units": None,
                "partial_units": None,
            }
        },
        {
            "input": "bought stella 1 dozen 3",
            "expected": {
                "action": "purchase",
                "item_identifier": "stella",
                "value": 15,  # 1*12 + 3
                "full_units": 1,
                "partial_units": 3,
            }
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        result = parse_voice_command(test["input"])
        expected = test["expected"]
        
        # Check if parsing succeeded
        if result is None:
            print(f"✗ FAIL: '{test['input']}'")
            print(f"  Could not parse command")
            print()
            failed += 1
            continue
        
        # Check each field
        all_match = True
        mismatches = []
        
        for key in ["action", "item_identifier", "value", "full_units", "partial_units"]:
            if result.get(key) != expected.get(key):
                all_match = False
                mismatches.append(f"  {key}: expected {expected.get(key)}, got {result.get(key)}")
        
        if all_match:
            print(f"✓ PASS: '{test['input']}'")
            print(f"  → {result['action']} {result['item_identifier']} {result['value']}")
            passed += 1
        else:
            print(f"✗ FAIL: '{test['input']}'")
            for mismatch in mismatches:
                print(mismatch)
            failed += 1
        
        print()
    
    print(f"Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_invalid_commands():
    """Test that invalid commands are rejected"""
    print("=" * 60)
    print("TEST 3: Invalid Command Handling")
    print("=" * 60)
    
    invalid_commands = [
        "hello world",
        "count",
        "heineken 24",
        "count heineken",
        "random text here",
        "",
        "count heineken abc",
    ]
    
    passed = 0
    failed = 0
    
    for cmd in invalid_commands:
        try:
            result = parse_voice_command(cmd)
            print(f"✗ FAIL: Should have rejected '{cmd}' but got {result}")
            failed += 1
        except (ValueError, Exception):
            print(f"✓ PASS: Correctly rejected '{cmd}'")
            passed += 1
    
    print()
    print(f"Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_openai_configuration():
    """Test OpenAI API key is configured"""
    print("=" * 60)
    print("TEST 4: OpenAI Configuration")
    print("=" * 60)
    
    try:
        api_key = settings.OPENAI_API_KEY
        
        if api_key and api_key.startswith('sk-'):
            print("✓ PASS: OpenAI API key is configured")
            print(f"  Key starts with: {api_key[:15]}...")
            print()
            return True
        else:
            print("✗ FAIL: OpenAI API key is not properly configured")
            print(f"  Current value: {api_key}")
            print()
            return False
    except AttributeError:
        print("✗ FAIL: OPENAI_API_KEY not found in settings")
        print()
        return False


def test_app_installation():
    """Test that voice_recognition app is properly installed"""
    print("=" * 60)
    print("TEST 5: App Installation")
    print("=" * 60)
    
    from django.apps import apps
    
    try:
        app_config = apps.get_app_config('voice_recognition')
        print(f"✓ PASS: voice_recognition app is installed")
        print(f"  App name: {app_config.name}")
        print()
        return True
    except LookupError:
        print("✗ FAIL: voice_recognition app is not installed in INSTALLED_APPS")
        print()
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n")
    print("*" * 60)
    print("VOICE RECOGNITION SYSTEM - TEST SUITE")
    print("*" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Number Word Conversion", test_number_word_conversion()))
    results.append(("Command Parsing", test_command_parsing()))
    results.append(("Invalid Command Handling", test_invalid_commands()))
    results.append(("OpenAI Configuration", test_openai_configuration()))
    results.append(("App Installation", test_app_installation()))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Overall: {total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! Voice recognition system is ready to use.")
        print("\nNext steps:")
        print("1. Deploy to Heroku (OPENAI_API_KEY is already in .env)")
        print("2. Test with actual audio files using the API endpoint")
        print("3. Implement frontend integration (see VOICE_RECOGNITION_FRONTEND_GUIDE.md)")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test suite(s) failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
