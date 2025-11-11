"""
Step 4: Create September 2025 StocktakeLine items
Lines will have ZERO opening_qty - to be populated from snapshots later
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockItem
from hotel.models import Hotel

print("=" * 80)
print("STEP 4: CREATE SEPTEMBER 2025 STOCKTAKE LINES")
print("=" * 80)
print()

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print()

# Get September stocktake
stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
).first()

if not stocktake:
    print("❌ No September stocktake found!")
    print("   Run step3 first to create the stocktake")
    exit(1)

print(f"✓ September Stocktake found (ID: {stocktake.id})")
print()

# Check for existing lines
existing = StocktakeLine.objects.filter(stocktake=stocktake).count()
if existing > 0:
    print(f"⚠️  Found {existing} existing lines")
    response = input("Delete and recreate? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        exit(0)
    StocktakeLine.objects.filter(stocktake=stocktake).delete()
    print("✓ Deleted existing lines")
    print()

# Get all active stock items
stock_items = StockItem.objects.filter(hotel=hotel, active=True)
print(f"Found {stock_items.count()} active stock items")
print()

# Create stocktake lines
print("Creating stocktake lines...")
print("-" * 80)

created_count = 0
category_counts = {}

for item in stock_items:
    cat = item.category_id
    
    # Create line with ZERO values
    # opening_qty will be populated after snapshots are filled
    StocktakeLine.objects.create(
        stocktake=stocktake,
        item=item,
        opening_qty=Decimal('0.0000'),
        purchases=Decimal('0.0000'),
        waste=Decimal('0.0000'),
        transfers_in=Decimal('0.0000'),
        transfers_out=Decimal('0.0000'),
        adjustments=Decimal('0.0000'),
        counted_full_units=Decimal('0.00'),
        counted_partial_units=Decimal('0.00'),
        valuation_cost=item.unit_cost or Decimal('0.0000')
    )
    
    # Count by category
    if cat not in category_counts:
        category_counts[cat] = 0
    category_counts[cat] += 1
    
    created_count += 1
    
    if created_count % 50 == 0:
        print(f"  Created {created_count} lines...")

print(f"✓ Created {created_count} total lines")
print()

# Summary by category
print("=" * 80)
print("LINES BY CATEGORY")
print("=" * 80)
print()

category_names = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer',
    'S': 'Spirits',
    'W': 'Wine',
    'M': 'Minerals/Syrups'
}

for cat_code in ['D', 'B', 'S', 'M', 'W']:
    count = category_counts.get(cat_code, 0)
    cat_name = category_names.get(cat_code, cat_code)
    print(f"  {cat_code} - {cat_name:<20}: {count:>3} lines")

print()
print("=" * 80)
print("✅ STEP 4 COMPLETE - StocktakeLine items created")
print("=" * 80)
print()
print("SUMMARY:")
print(f"  Period: {stocktake.period_start} to {stocktake.period_end}")
print(f"  Stocktake ID: {stocktake.id}")
print(f"  Status: {stocktake.status}")
print(f"  Lines: {created_count}")
print()
print("ALL SETUP COMPLETE!")
print()
print("NEXT STEPS:")
print("1. Fill in StockSnapshot data from Excel (category by category)")
print("2. After snapshots are filled, populate opening_qty in lines")
print("3. Close the stocktake when ready")
