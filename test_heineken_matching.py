"""
Test Heineken draft vs bottle matching
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from voice_recognition.item_matcher import score_item
from voice_recognition.command_parser import parse_voice_command

print("=" * 70)
print("TEST: Heineken Draft vs Bottle Matching")
print("=" * 70)

# Test items
test_items = [
    "Heineken Bottle",
    "Heineken Draught",
    "Heineken Keg",
    "Heineken Draft 50L",
]

# Test searches
searches = [
    "heineken draft",
    "heineken draught", 
    "heineken bottle",
    "heineken keg",
]

print("\n1. MATCHING SCORES\n")
for search in searches:
    print(f"Search: '{search}'")
    for item in test_items:
        score = score_item(item, search)
        print(f"  → {item:25} : {score:.4f}")
    print()

print("\n2. COMMAND PARSING\n")
test_command = "Heineken draft counted three kegs, three pints"
print(f"Input: '{test_command}'")
try:
    result = parse_voice_command(test_command)
    print(f"✅ Parsed successfully:")
    print(f"   Action: {result['action']}")
    print(f"   Item: {result['item_identifier']}")
    print(f"   Full units: {result.get('full_units')}")
    print(f"   Partial units: {result.get('partial_units')}")
    print(f"   Value: {result.get('value')}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
