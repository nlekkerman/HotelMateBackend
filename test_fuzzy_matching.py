"""
Test fuzzy item matching
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from voice_recognition.item_matcher import score_item, expand_search_tokens


def test_fuzzy_matching():
    """Test that fuzzy matching works with partial/misspelled names"""
    print("=" * 60)
    print("TEST: Fuzzy Item Matching")
    print("=" * 60)
    
    # Mock item names from your stocktake
    items = [
        "Budweiser Bottle",
        "Bulmers Bottle",
        "Bulmers Pint Bottle",
        "Heineken Bottle",
        "Heineken Zero Bottle",
        "Smithwicks Bottle",
        "Guinness Draught",
        "Coors Draught",
    ]
    
    test_cases = [
        # Partial names
        ("bud", "Budweiser Bottle", 0.6),
        ("bud botle", "Budweiser Bottle", 0.7),
        ("budweiser", "Budweiser Bottle", 0.85),
        
        # Misspellings
        ("budwiser", "Budweiser Bottle", 0.7),
        ("budweisser", "Budweiser Bottle", 0.7),
        ("heiny", "Heineken Bottle", 0.6),
        ("heinikn", "Heineken Bottle", 0.6),
        ("smithix", "Smithwicks Bottle", 0.6),
        ("guiness draft", "Guinness Draught", 0.7),
        
        # Bottle variations
        ("budweiser botl", "Budweiser Bottle", 0.7),
        ("heineken bot", "Heineken Bottle", 0.7),
        
        # Zero/alcohol-free
        ("heiny zero", "Heineken Zero Bottle", 0.75),
        ("heineken zero", "Heineken Zero Bottle", 0.85),
        
        # Draught variations
        ("coors draft", "Coors Draught", 0.8),
        ("guinness tap", "Guinness Draught", 0.7),
    ]
    
    passed = 0
    failed = 0
    
    for search, expected_item, min_score in test_cases:
        # Score against all items
        scores = [(item, score_item(item, search)) for item in items]
        scores.sort(key=lambda x: x[1], reverse=True)
        
        best_match = scores[0][0]
        best_score = scores[0][1]
        
        matched_correctly = best_match == expected_item and best_score >= min_score
        
        if matched_correctly:
            print(f"✓ PASS: '{search}' → '{best_match}' ({best_score:.2f})")
            passed += 1
        else:
            print(f"✗ FAIL: '{search}'")
            print(f"  Expected: '{expected_item}' (min score: {min_score})")
            print(f"  Got: '{best_match}' (score: {best_score:.2f})")
            # Show top 3
            print(f"  Top matches:")
            for item, score in scores[:3]:
                print(f"    - {item}: {score:.2f}")
            failed += 1
    
    print()
    print(f"Results: {passed} passed, {failed} failed\n")
    
    if failed == 0:
        print("🎉 All fuzzy matching tests passed!")
        print("✅ Backend can recognize partial names like 'bud botle'")
        return 0
    else:
        print(f"⚠️ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(test_fuzzy_matching())
