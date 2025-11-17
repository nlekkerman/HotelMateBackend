"""
Create stock periods and snapshots with opening stock set to 0
This sets up the period structure for tracking stock
"""
import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from hotel.models import Hotel

print(f"\n{'='*80}")
print(f"CREATING STOCK PERIODS AND SNAPSHOTS")
print(f"{'='*80}\n")

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}\n")

# Define periods to create
periods_data = [
    {
        'period_name': 'September 2025',
        'start_date': date(2025, 9, 1),
        'end_date': date(2025, 9, 30),
        'year': 2025,
        'month': 9,
        'period_type': 'MONTHLY'
    },
    {
        'period_name': 'October 2025',
        'start_date': date(2025, 10, 1),
        'end_date': date(2025, 10, 31),
        'year': 2025,
        'month': 10,
        'period_type': 'MONTHLY'
    },
    {
        'period_name': 'November 2025',
        'start_date': date(2025, 11, 1),
        'end_date': date(2025, 11, 30),
        'year': 2025,
        'month': 11,
        'period_type': 'MONTHLY'
    }
]

# Create periods
print("Creating periods...")
print("-" * 80)

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
    status = "Created" if created else "Already exists"
    print(f"{status}: {period.period_name} ({period.start_date} to {period.end_date})")
    created_periods.append(period)

print()

# Get all active stock items
items = StockItem.objects.filter(hotel=hotel, active=True).select_related('category')
print(f"Found {items.count()} active stock items\n")

# Create snapshots for each period
print("Creating snapshots with ZERO opening stock...")
print("-" * 80)

for period in created_periods:
    print(f"\nCreating snapshots for {period.period_name}...")
    
    # Check if snapshots already exist
    existing = StockSnapshot.objects.filter(period=period).count()
    if existing > 0:
        print(f"  ⚠ {existing} snapshots already exist for this period")
        response = input(f"  Delete and recreate? (yes/no): ")
        if response.lower() == 'yes':
            StockSnapshot.objects.filter(period=period).delete()
            print(f"  ✓ Deleted {existing} existing snapshots")
        else:
            print(f"  Skipping {period.period_name}")
            continue
    
    created_count = 0
    
    for item in items:
        # Create snapshot with closing stock from current levels
        # Opening stock will be 0 for first period, then previous closing
        StockSnapshot.objects.create(
            hotel=hotel,
            item=item,
            period=period,
            closing_full_units=item.current_full_units,
            closing_partial_units=item.current_partial_units,
            unit_cost=item.unit_cost or Decimal('0.0000'),
            cost_per_serving=item.cost_per_serving or Decimal('0.0000'),
            closing_stock_value=item.total_stock_value,
            menu_price=item.menu_price or Decimal('0.00')
        )
        created_count += 1
        
        if created_count % 50 == 0:
            print(f"  Created {created_count} snapshots...")
    
    print(f"  ✓ Created {created_count} snapshots for {period.period_name}")

print(f"\n{'='*80}")
print("COMPLETE")
print(f"{'='*80}")
print(f"Created {len(created_periods)} periods")
print("Created snapshots for each period")
print("Note: Opening stock will be calculated from previous period's closing")
print("      For the first period (September), opening will be 0")
print(f"{'='*80}\n")
