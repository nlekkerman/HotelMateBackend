"""
Test why "Boomer's pint bottle" matched Jameson instead of Bulmers
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from voice_recognition.item_matcher import find_best_match, score_item

# Get relevant items
bulmers_pint = StockItem.objects.filter(sku='B0085').first()
bulmers_bottle = StockItem.objects.filter(sku='B0075').first()
jameson = StockItem.objects.filter(sku='S0405').first()

print("=" * 80)
print("TESTING: 'Boomer's pint bottle' Voice Command")
print("=" * 80)

search_phrase = "Boomer's pint bottle"

print(f"\nSearch phrase: '{search_phrase}'")
print("\n" + "-" * 80)

items_to_test = [
    (bulmers_pint, "B0085"),
    (bulmers_bottle, "B0075"),
    (jameson, "S0405")
]

scores = []
for item, sku in items_to_test:
    if item:
        score = score_item(item.name, search_phrase)
        scores.append((score, item.name, sku))
        print(f"\n{sku}: {item.name}")
        print(f"  Score: {score:.4f}")
    else:
        print(f"\n{sku}: NOT FOUND")

print("\n" + "=" * 80)
print("RANKING:")
print("=" * 80)

scores.sort(reverse=True, key=lambda x: x[0])
for i, (score, name, sku) in enumerate(scores, 1):
    indicator = "✓ WINNER" if i == 1 else ""
    print(f"{i}. [{score:.4f}] {sku}: {name} {indicator}")

print("\n" + "=" * 80)

# Now test with all beer items
print("\nTESTING AGAINST ALL BEER ITEMS:")
print("=" * 80)

beer_items = StockItem.objects.filter(
    category__name='B - Bottled Beer',
    active=True
)

print(f"Found {beer_items.count()} beer items")
print("First 5 items:")
for item in beer_items[:5]:
    print(f"  - {item.sku}: {item.name}")

result = find_best_match(search_phrase, list(beer_items), min_score=0.55)

if result:
    print(f"\n✓ MATCH FOUND:")
    print(f"  Item: {result['item'].name}")
    print(f"  SKU: {result['item'].sku}")
    print(f"  Confidence: {result['confidence']:.4f}")
else:
    print("\n✗ NO MATCH FOUND (all scores below 0.55)")
