"""
Test that "drough" (misspelled draught) is correctly recognized
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from voice_recognition.item_matcher import score_item, expand_search_tokens

print("=" * 70)
print("TEST: 'drough' (misspelled draught) recognition")
print("=" * 70)

# Test synonym expansion
print("\n1. SYNONYM EXPANSION TEST")
print("-" * 70)
search_phrase = "heineken drough"
expanded = expand_search_tokens(search_phrase)
print(f"Search phrase: '{search_phrase}'")
print(f"Expanded tokens: {expanded}")
print(f"Contains 'draught'? {('draught' in expanded)}")
print(f"Contains 'draft'? {('draft' in expanded)}")
print(f"Contains 'keg'? {('keg' in expanded)}")

# Test scoring
print("\n2. MATCHING SCORES TEST")
print("-" * 70)

test_items = [
    "Heineken Bottle",
    "Heineken Draught",
    "Heineken Draft",
    "Budweiser Bottle",
    "Budweiser Draught",
]

test_searches = [
    "heineken drough",
    "heineken draught",
    "heineken draft",
    "heineken bottle",
    "budweiser drough",
]

for search in test_searches:
    print(f"\nSearch: '{search}'")
    scores = []
    for item in test_items:
        score = score_item(item, search)
        scores.append((item, score))
        print(f"  {item:25} : {score:.4f}")
    
    # Check if draught items score higher than bottle for draught searches
    best = max(scores, key=lambda x: x[1])
    print(f"  ✓ Best match: {best[0]} ({best[1]:.4f})")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print("\nExpected Results:")
print("- 'drough' should expand to include 'draught', 'draft', 'keg'")
print("- 'heineken drough' should match 'Heineken Draught' with high score")
print("- 'heineken drough' should NOT match 'Heineken Bottle' (penalty applied)")
print("=" * 70)
