"""
Create 5 test periods (January - May 2025) and populate January closing stock
with simple draught beer data to monitor how opening stock flows to next periods.

Only creates periods and January closing - no stocktakes.
"""
import os
import django
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from hotel.models import Hotel

print(f"\n{'='*100}")
print("CREATE TEST PERIODS (JANUARY - MAY 2025)")
print(f"{'='*100}\n")

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"🏨 Hotel: {hotel.name}\n")

# Define periods to create (January - May 2025)
periods_data = [
    {
        'period_name': 'January 2025',
        'start_date': date(2025, 1, 1),
        'end_date': date(2025, 1, 31),
        'year': 2025,
        'month': 1,
        'period_type': 'MONTHLY'
    },
    {
        'period_name': 'February 2025',
        'start_date': date(2025, 2, 1),
        'end_date': date(2025, 2, 28),
        'year': 2025,
        'month': 2,
        'period_type': 'MONTHLY'
    },
    {
        'period_name': 'March 2025',
        'start_date': date(2025, 3, 1),
        'end_date': date(2025, 3, 31),
        'year': 2025,
        'month': 3,
        'period_type': 'MONTHLY'
    },
    {
        'period_name': 'April 2025',
        'start_date': date(2025, 4, 1),
        'end_date': date(2025, 4, 30),
        'year': 2025,
        'month': 4,
        'period_type': 'MONTHLY'
    },
    {
        'period_name': 'May 2025',
        'start_date': date(2025, 5, 1),
        'end_date': date(2025, 5, 31),
        'year': 2025,
        'month': 5,
        'period_type': 'MONTHLY'
    }
]

# Create periods
print("📅 Creating periods...")
print("-" * 100)

created_periods = []
for period_data in periods_data:
    period, created = StockPeriod.objects.get_or_create(
        hotel=hotel,
        year=period_data['year'],
        month=period_data['month'],
        period_type=period_data['period_type'],
        defaults={
            'period_name': period_data['period_name'],
            'start_date': period_data['start_date'],
            'end_date': period_data['end_date'],
            'is_closed': False
        }
    )
    status = "✅ Created" if created else "✓ Already exists"
    print(f"{status}: {period.period_name} (ID: {period.id})")
    created_periods.append(period)

print()

# Get January period
january_period = created_periods[0]
print(f"📦 Populating January closing stock with simple draught beer data...")
print("-" * 100)

# Get all draught beer items (category D)
draught_items = StockItem.objects.filter(
    hotel=hotel,
    category__code='D',
    active=True
).select_related('category')

print(f"Found {draught_items.count()} draught beer items\n")

if draught_items.count() == 0:
    print("❌ No draught beer items found!")
    exit(1)

# Check if snapshots already exist for January
existing_snaps = StockSnapshot.objects.filter(period=january_period).count()
if existing_snaps > 0:
    print(f"⚠️  {existing_snaps} snapshots already exist for January")
    response = input("Delete and recreate? (yes/no): ")
    if response.lower() == 'yes':
        StockSnapshot.objects.filter(period=january_period).delete()
        print(f"  ✓ Deleted {existing_snaps} existing snapshots\n")
    else:
        print("  Skipping January snapshot creation")
        print(f"\n{'='*100}")
        print("PERIODS CREATED - JANUARY SNAPSHOTS NOT UPDATED")
        print(f"{'='*100}\n")
        exit(0)

# Create simple closing stock for January draught beers
# 1 keg and 20 pints for each item
print("Creating January closing stock snapshots...")
print("Setting each draught beer to: 1 keg + 20 pints\n")

created_count = 0
total_value = Decimal('0.00')

for item in draught_items:
    # Simple values: 1 keg + 20 pints
    closing_full_units = Decimal('1.00')  # 1 keg
    closing_partial_units = Decimal('20.00')  # 20 pints (servings)
    
    # Calculate value
    # Full units (kegs): keg_count * unit_cost
    full_value = closing_full_units * item.unit_cost
    
    # Partial units (pints): pints * cost_per_serving
    partial_value = closing_partial_units * item.cost_per_serving
    
    # Total value
    closing_stock_value = full_value + partial_value
    
    # Create snapshot
    StockSnapshot.objects.create(
        hotel=hotel,
        item=item,
        period=january_period,
        closing_full_units=closing_full_units,
        closing_partial_units=closing_partial_units,
        unit_cost=item.unit_cost,
        cost_per_serving=item.cost_per_serving,
        closing_stock_value=closing_stock_value,
        menu_price=item.menu_price or Decimal('0.00')
    )
    
    created_count += 1
    total_value += closing_stock_value
    
    print(f"  ✓ {item.sku} - {item.name}")
    print(f"    Closing: 1 keg + 20 pints = €{closing_stock_value:.2f}")

print()
print(f"✅ Created {created_count} January closing stock snapshots")
print(f"💰 Total January closing value: €{total_value:.2f}")

print(f"\n{'='*100}")
print("SUMMARY")
print(f"{'='*100}")
print(f"✅ Created 5 periods (January - May 2025)")
print(f"✅ Populated January closing stock:")
print(f"   - {created_count} draught beer items")
print(f"   - Each item: 1 keg + 20 pints")
print(f"   - Total value: €{total_value:.2f}")
print()
print("📌 NEXT STEPS:")
print("   1. View how opening stock is calculated for February")
print("   2. Monitor how January closing becomes February opening")
print("   3. Test the opening stock population logic")
print(f"{'='*100}\n")
