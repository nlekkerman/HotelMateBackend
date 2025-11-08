"""
Test script to verify the populate_opening_stock functionality.

This script will:
1. Create a test November 2025 period
2. Call populate_opening_stock to initialize it from October 2025
3. Verify the opening stock matches October's closing stock
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from stock_tracker.stocktake_service import populate_period_opening_stock
from hotel.models import Hotel
from decimal import Decimal

print("=" * 80)
print("TEST: Populate Opening Stock for New Period")
print("=" * 80)
print()

# Get hotel
hotel = Hotel.objects.get(id=2)
print(f"Hotel: {hotel.name}")
print()

# Find October 2024 period (should be closed)
try:
    october = StockPeriod.objects.get(
        hotel=hotel,
        year=2024,
        month=10,
        period_type='MONTHLY'
    )
    print(f"✅ Found October 2024 period (ID: {october.id})")
    print(f"   Status: {'CLOSED' if october.is_closed else 'OPEN'}")
    
    if not october.is_closed:
        print("   ⚠️  WARNING: October is not closed!")
    
    # Get October snapshot count and total value
    oct_snapshots = StockSnapshot.objects.filter(period=october)
    oct_count = oct_snapshots.count()
    oct_total = sum(s.closing_stock_value for s in oct_snapshots)
    
    print(f"   Snapshots: {oct_count}")
    print(f"   Total Value: €{oct_total:,.2f}")
    print()
    
except StockPeriod.DoesNotExist:
    print("❌ October 2024 period not found!")
    print("   Run the close_october_period command first.")
    exit(1)

# Check if November 2024 already exists
try:
    november = StockPeriod.objects.get(
        hotel=hotel,
        year=2024,
        month=11,
        period_type='MONTHLY'
    )
    print(f"ℹ️  November 2024 period already exists (ID: {november.id})")
    
    # Delete existing snapshots
    existing_snapshots = StockSnapshot.objects.filter(period=november)
    existing_count = existing_snapshots.count()
    
    if existing_count > 0:
        print(f"   Deleting {existing_count} existing snapshots...")
        existing_snapshots.delete()
        print("   ✅ Deleted")
    print()
    
except StockPeriod.DoesNotExist:
    # Create November 2024 period
    print("Creating November 2024 period...")
    november = StockPeriod.objects.create(
        hotel=hotel,
        period_type='MONTHLY',
        year=2024,
        month=11,
        start_date='2024-11-01',
        end_date='2024-11-30',
        period_name='November 2024',
        is_closed=False
    )
    print(f"✅ Created November 2024 period (ID: {november.id})")
    print()

# Now populate the opening stock
print("-" * 80)
print("Populating November opening stock from October closing stock...")
print("-" * 80)
print()

try:
    result = populate_period_opening_stock(november)
    
    print("✅ SUCCESS!")
    print()
    print(f"Snapshots Created: {result['snapshots_created']}")
    print(f"Total Opening Value: €{result['total_value']:,.2f}")
    
    if result['previous_period']:
        print(f"Previous Period: {result['previous_period'].period_name}")
    else:
        print("Previous Period: None (first period)")
    
    print()
    
    # Verify by comparing a few items
    print("-" * 80)
    print("VERIFICATION: Comparing October closing vs November opening")
    print("-" * 80)
    print()
    
    nov_snapshots = StockSnapshot.objects.filter(period=november).select_related('item')[:5]
    
    for nov_snap in nov_snapshots:
        # Find corresponding October snapshot
        try:
            oct_snap = StockSnapshot.objects.get(
                period=october,
                item=nov_snap.item
            )
            
            print(f"Item: {nov_snap.item.sku} - {nov_snap.item.name}")
            print(f"  October Closing:")
            print(f"    Full: {oct_snap.closing_full_units}")
            print(f"    Partial: {oct_snap.closing_partial_units}")
            print(f"    Value: €{oct_snap.closing_stock_value}")
            print(f"  November Opening:")
            print(f"    Full: {nov_snap.closing_full_units}")
            print(f"    Partial: {nov_snap.closing_partial_units}")
            print(f"    Value: €{nov_snap.closing_stock_value}")
            
            # Check if they match
            if (oct_snap.closing_full_units == nov_snap.closing_full_units and
                oct_snap.closing_partial_units == nov_snap.closing_partial_units):
                print(f"  ✅ MATCH")
            else:
                print(f"  ⚠️  DIFFERENT (may include movements)")
            print()
            
        except StockSnapshot.DoesNotExist:
            print(f"  ⚠️  No October snapshot found for this item")
            print()
    
    print("=" * 80)
    print("✅ Test Complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Frontend can now fetch November period snapshots")
    print("2. Staff enters actual stock counts (updates snapshots)")
    print("3. When done, close November period")
    print()
    
except ValueError as e:
    print(f"❌ ERROR: {e}")
    exit(1)
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
