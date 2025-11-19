"""
Calculate total counted value for Minerals & Syrups category in April 2025.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

print("=" * 100)
print("APRIL 2025 MINERALS & SYRUPS - TOTAL COUNTED VALUE")
print("=" * 100)
print()

# Get hotel
hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print()

# Find April 2025 stocktake
april_stocktakes = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=4
).order_by('-period_start')

if not april_stocktakes.exists():
    print("❌ No April 2025 stocktake found!")
    exit(1)

april_stocktake = april_stocktakes.first()
print(f"Stocktake ID: {april_stocktake.id}")
print(f"Period: {april_stocktake.period_start} to {april_stocktake.period_end}")
print(f"Status: {april_stocktake.status}")
print()

# Get all Minerals lines (category M)
minerals_lines = StocktakeLine.objects.filter(
    stocktake=april_stocktake,
    item__category__code='M'
).select_related('item')

print(f"Total Minerals & Syrups items: {minerals_lines.count()}")
print()

# Break down by subcategory
subcategories = {}
for line in minerals_lines:
    subcat = line.item.subcategory or 'OTHER'
    if subcat not in subcategories:
        subcategories[subcat] = {
            'count': 0,
            'counted_value': Decimal('0.00'),
            'expected_value': Decimal('0.00'),
            'variance_value': Decimal('0.00')
        }
    
    subcategories[subcat]['count'] += 1
    subcategories[subcat]['counted_value'] += line.counted_value
    subcategories[subcat]['expected_value'] += line.expected_value
    subcategories[subcat]['variance_value'] += line.variance_value

# Display by subcategory
print("=" * 100)
print("BREAKDOWN BY SUBCATEGORY")
print("=" * 100)
print()

total_counted = Decimal('0.00')
total_expected = Decimal('0.00')
total_variance = Decimal('0.00')

for subcat in sorted(subcategories.keys()):
    data = subcategories[subcat]
    print(f"{subcat}:")
    print(f"  Items: {data['count']}")
    print(f"  Counted Value: €{data['counted_value']:,.2f}")
    print(f"  Expected Value: €{data['expected_value']:,.2f}")
    print(f"  Variance: €{data['variance_value']:,.2f}")
    print()
    
    total_counted += data['counted_value']
    total_expected += data['expected_value']
    total_variance += data['variance_value']

# Total summary
print("=" * 100)
print("MINERALS & SYRUPS CATEGORY TOTALS")
print("=" * 100)
print(f"Total Items: {minerals_lines.count()}")
print(f"Total Counted Value: €{total_counted:,.2f}")
print(f"Total Expected Value: €{total_expected:,.2f}")
print(f"Total Variance: €{total_variance:,.2f}")
print()

# Calculate percentage
if total_expected > 0:
    variance_pct = (total_variance / total_expected) * 100
    print(f"Variance %: {variance_pct:.2f}%")
print()
print("=" * 100)
