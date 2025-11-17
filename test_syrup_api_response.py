"""
Check what the API serializer returns for syrup stocktake lines
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, Stocktake
from stock_tracker.stock_serializers import StocktakeLineSerializer
import json

# Get February stocktake
february = Stocktake.objects.filter(
    hotel_id=2,
    period_start__month=2,
    period_start__year=2025
).first()

if not february:
    print("❌ February stocktake not found")
    exit()

# Get first syrup line
syrup_line = StocktakeLine.objects.filter(
    stocktake=february,
    item__subcategory='SYRUPS'
).select_related('item').first()

print("=" * 80)
print(f"SYRUP LINE: {syrup_line.item.sku} - {syrup_line.item.name}")
print("=" * 80)

print("\n📊 DATABASE VALUES:")
print(f"   counted_full_units: {syrup_line.counted_full_units}")
print(f"   counted_partial_units: {syrup_line.counted_partial_units}")
print(f"   item.uom (bottle size): {syrup_line.item.uom}ml")

print("\n📦 API SERIALIZED DATA:")
serializer = StocktakeLineSerializer(syrup_line)
data = serializer.data

# Pretty print relevant fields
print(json.dumps({
    'sku': data['item']['sku'],
    'name': data['item']['name'],
    'counted_full_units': str(data['counted_full_units']),
    'counted_partial_units': str(data['counted_partial_units']),
    'input_fields': data.get('input_fields', {}),
}, indent=2))

print("\n🔍 INPUT_FIELDS METADATA:")
input_fields = data.get('input_fields', {})
print(json.dumps(input_fields, indent=2))
