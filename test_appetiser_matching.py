"""
Test fuzzy matching for Appetiser Apple
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from voice_recognition.item_matcher import score_item, find_best_match
from stock_tracker.models import StockItem

# Test scoring
search_phrase = "appetizer apple"

# Create mock items for testing
test_items = [
    ("Appletisier Apple", "M2236"),
    ("Bulmers Pint Bottle", "B0085"),
    ("Appletiser", "M0001"),
]

print("=" * 60)
print(f"Search phrase: '{search_phrase}'")
print("=" * 60)

for item_name, sku in test_items:
    score = score_item(item_name, search_phrase)
    print(f"{item_name:30} (SKU: {sku:6}) → Score: {score:.4f}")

print("\n" + "=" * 60)
print("Now testing with real database items from Minerals category...")
print("=" * 60)

# Get real minerals items
minerals_items = StockItem.objects.filter(
    category__code='M',
    active=True
).order_by('name')[:20]

if minerals_items.exists():
    for item in minerals_items:
        score = score_item(item.name, search_phrase)
        if score > 0.3:  # Only show relevant matches
            print(f"{item.name:40} (SKU: {item.sku:6}) → Score: {score:.4f}")

print("\n" + "=" * 60)
print("Testing find_best_match function...")
print("=" * 60)

result = find_best_match(search_phrase, minerals_items, min_score=0.55)
if result:
    print(f"✓ Best match: {result['item'].name} (SKU: {result['item'].sku})")
    print(f"  Confidence: {result['confidence']:.4f}")
else:
    print("✗ No match found above threshold")
