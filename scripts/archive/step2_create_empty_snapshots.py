"""
Step 2: Create September 2025 StockSnapshots with ZERO values
Just populate with items - data will be entered manually from Excel
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from hotel.models import Hotel

print("=" * 80)
print("STEP 2: CREATE EMPTY SEPTEMBER 2025 STOCK SNAPSHOTS")
print("=" * 80)
print()

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print()

# Get September period
sept_period = StockPeriod.objects.get(
    hotel=hotel,
    period_name="September 2025"
)
print(f"✓ September Period found (ID: {sept_period.id})")
print()

# Check for existing snapshots
existing = StockSnapshot.objects.filter(period=sept_period).count()
if existing > 0:
    print(f"⚠️  Found {existing} existing snapshots")
    response = input("Delete and recreate? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        exit(0)
    StockSnapshot.objects.filter(period=sept_period).delete()
    print("✓ Deleted existing snapshots")
    print()

# Get all active stock items
stock_items = StockItem.objects.filter(hotel=hotel, active=True)
print(f"Found {stock_items.count()} active stock items")
print()

# Create empty snapshots for each item
print("Creating empty snapshots...")
print("-" * 80)

created_count = 0
category_counts = {}

for item in stock_items:
    cat = item.category_id
    
    # Create snapshot with ZERO quantities
    StockSnapshot.objects.create(
        hotel=hotel,
        item=item,
        period=sept_period,
        closing_full_units=Decimal('0.00'),
        closing_partial_units=Decimal('0.0000'),
        unit_cost=item.unit_cost or Decimal('0.0000'),
        cost_per_serving=item.cost_per_serving or Decimal('0.0000'),
        closing_stock_value=Decimal('0.00'),
        menu_price=item.menu_price
    )
    
    # Count by category
    if cat not in category_counts:
        category_counts[cat] = 0
    category_counts[cat] += 1
    
    created_count += 1
    
    if created_count % 50 == 0:
        print(f"  Created {created_count} snapshots...")

print(f"✓ Created {created_count} total snapshots")
print()

# Summary by category
print("=" * 80)
print("SNAPSHOTS BY CATEGORY")
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
    print(f"  {cat_code} - {cat_name:<20}: {count:>3} items")

print()
print("=" * 80)
print("✅ STEP 2 COMPLETE - Empty snapshots created")
print("=" * 80)
print()
print("NEXT STEPS:")
print("1. Fill in snapshot data category by category from Excel")
print("2. Then run script to create Stocktake")
print("3. Then run script to create StocktakeLine items")
print()
print("All snapshots have ZERO values - ready for manual data entry!")
