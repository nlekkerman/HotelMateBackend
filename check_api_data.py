"""
Check what API is sending to frontend
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from stock_tracker.stock_serializers import StocktakeLineSerializer

st = Stocktake.objects.filter(
    period_start__year=2025,
    period_start__month=2,
    hotel_id=2
).first()

if not st:
    print("No stocktake found!")
    exit()

lines = st.lines.filter(item__category__code='B').order_by('item__sku')

print("=" * 80)
print("API DATA FOR FRONTEND - BOTTLED BEERS")
print("=" * 80)

total_counted_value = Decimal('0')
total_opening_value = Decimal('0')

for line in lines[:5]:
    serializer = StocktakeLineSerializer(line)
    data = serializer.data
    
    print(f"\n{data['item_sku']} - {data['item_name']}")
    print(f"  opening_qty: {line.opening_qty}")
    print(f"  counted_full_units: {data['counted_full_units']}")
    print(f"  counted_partial_units: {data['counted_partial_units']}")
    print(f"  counted_qty: {data['counted_qty']}")
    print(f"  counted_value: €{data['counted_value']}")
    print(f"  expected_value: €{data['expected_value']}")
    print(f"  variance_value: €{data['variance_value']}")
    
    total_counted_value += Decimal(str(data['counted_value']))
    total_opening_value += Decimal(str(data['expected_value']))

print("\n" + "=" * 80)
print("CALCULATE FULL TOTALS")
print("=" * 80)

total_counted = Decimal('0')
total_expected = Decimal('0')

for line in lines:
    serializer = StocktakeLineSerializer(line)
    data = serializer.data
    total_counted += Decimal(str(data['counted_value']))
    total_expected += Decimal(str(data['expected_value']))

print(f"\nTotal counted_value (API sends): €{total_counted:.2f}")
print(f"Total expected_value (API sends): €{total_expected:.2f}")
print(f"Variance: €{total_counted - total_expected:.2f}")

print(f"\nExpected in UI: €754.36")
print(f"UI showing: €989.26")

print("\n" + "=" * 80)
