"""
Quick check of stocktake #16 data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake

# Get stocktake
st = Stocktake.objects.get(id=16)
print(f"Stocktake #{st.id}: {st.period_start} to {st.period_end}")
print(f"Status: {st.status}")
print(f"Total lines: {st.lines.count()}")
print("\n" + "="*60)
print("FIRST 5 LINES:")
print("="*60)

for line in st.lines.all()[:5]:
    print(f"\nItem: {line.item.sku} - {line.item.name}")
    print(f"  Opening Qty: {line.opening_qty}")
    print(f"  Purchases: {line.purchases}")
    print(f"  Waste: {line.waste}")
    print(f"  Expected: {line.expected_qty}")
    print(f"  Counted: {line.counted_qty}")
    print(f"  Variance: {line.variance_qty}")
    print(f"  Item current stock: {line.item.total_stock_in_servings}")
