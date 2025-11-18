"""
Fix Minerals with Doz size in September - auto-convert bottles to cases+bottles
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod

sept = StockPeriod.objects.get(hotel_id=2, year=2025, month=9)

# Get all Minerals with Doz size
snaps = StockSnapshot.objects.filter(
    period=sept,
    item__category_id='M',
    item__size__icontains='Doz'
).select_related('item')

print(f"Found {snaps.count()} Minerals with Doz size")
print("=" * 80)

fixed = 0
for snap in snaps:
    if snap.closing_full_units == 0 and snap.closing_partial_units > 0:
        before_bottles = snap.closing_partial_units
        snap.save()  # Triggers auto-conversion
        print(f"{snap.item.sku}: {before_bottles} bottles → "
              f"{snap.closing_full_units} cases + {snap.closing_partial_units} bottles")
        fixed += 1

print("=" * 80)
print(f"✅ Fixed {fixed} Minerals Doz items")
print(f"⚬ Skipped {snaps.count() - fixed} items (already correct)")
