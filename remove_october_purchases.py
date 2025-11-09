"""
Remove purchases and sales data from October 2025 stocktake
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake, StockMovement
from hotel.models import Hotel

print("=" * 80)
print("REMOVE OCTOBER 2025 PURCHASES AND SALES")
print("=" * 80)
print()

# Get hotel
hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print()

# Find October 2025 Period
oct_period = StockPeriod.objects.filter(
    hotel=hotel,
    period_name="October 2025"
).first()

if not oct_period:
    print("❌ October 2025 Period not found!")
    exit(1)

print(f"✓ Found October 2025 Period (ID: {oct_period.id})")

# Find October stocktake
stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start=oct_period.start_date,
    period_end=oct_period.end_date
).first()

if not stocktake:
    print("❌ October 2025 Stocktake not found!")
    exit(1)

print(f"✓ Found October 2025 Stocktake (ID: {stocktake.id})")
print()

# Count what will be deleted
purchase_movements = StockMovement.objects.filter(
    hotel=hotel,
    period=oct_period,
    movement_type='PURCHASE'
).count()

lines_with_purchases = stocktake.lines.exclude(purchases=0).count()

print(f"Found:")
print(f"  - {purchase_movements} purchase movements")
print(f"  - {lines_with_purchases} stocktake lines with purchases")
print()

response = input("Remove all purchases data? (yes/no): ")
if response.lower() != 'yes':
    print("❌ Cancelled")
    exit(0)

print()
print("Removing data...")
print()

# Delete purchase movements
deleted = StockMovement.objects.filter(
    hotel=hotel,
    period=oct_period,
    movement_type='PURCHASE'
).delete()
print(f"✓ Deleted {deleted[0]} purchase movements")

# Reset purchases in stocktake lines
updated = 0
for line in stocktake.lines.all():
    if line.purchases != 0:
        line.purchases = 0
        line.save()
        updated += 1

print(f"✓ Reset purchases in {updated} stocktake lines")
print()

print("=" * 80)
print("✅ COMPLETED - All purchases data removed")
print("=" * 80)
