"""
Example: How to get Stocktake ID from Period ID
Demonstrates the relationship between StockPeriod and Stocktake
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake

print("\n" + "=" * 80)
print("PERIOD vs STOCKTAKE - ID RELATIONSHIP")
print("=" * 80)

# Get all periods
periods = StockPeriod.objects.all().order_by('-start_date')

print(f"\nShowing Period IDs and their corresponding Stocktake IDs:\n")

for period in periods:
    # Try to find matching stocktake by DATE RANGE (not by ID!)
    try:
        stocktake = Stocktake.objects.get(
            hotel=period.hotel,
            period_start=period.start_date,
            period_end=period.end_date
        )
        match_symbol = "✅" if period.id == stocktake.id else "⚠️"
        print(f"{match_symbol} {period.period_name}")
        print(f"   Period ID:    {period.id}")
        print(f"   Stocktake ID: {stocktake.id}")
        print(f"   Dates: {period.start_date} to {period.end_date}")
        print(f"   Status: {stocktake.status}")
        if period.id != stocktake.id:
            print(f"   ⚠️  IDs DON'T MATCH - Frontend must match by dates!")
        print()
    except Stocktake.DoesNotExist:
        print(f"❌ {period.period_name}")
        print(f"   Period ID: {period.id}")
        print(f"   Stocktake ID: None (no stocktake created yet)")
        print(f"   Dates: {period.start_date} to {period.end_date}")
        print()

print("=" * 80)
print("FRONTEND LESSON:")
print("=" * 80)
print("""
DON'T DO THIS:
  periodId = 8
  stocktakeId = 8  // WRONG! Just happened to match

DO THIS INSTEAD:
  1. Get Period by ID: /api/periods/8/
     Response: { id: 8, start_date: "2025-09-01", end_date: "2025-09-30" }
  
  2. Find Stocktake by dates: /api/stocktakes/
     Filter: period_start="2025-09-01" AND period_end="2025-09-30"
     Response: { id: 8, period_start: "2025-09-01", ... }
  
  3. Use the found Stocktake ID (which might not be 8!)
""")
print("=" * 80 + "\n")

# Show the correct Python way to do it
print("CORRECT CODE EXAMPLE:")
print("=" * 80)
print("""
# Given a period_id from frontend
period_id = 8

# Step 1: Get the period
period = StockPeriod.objects.get(id=period_id)

# Step 2: Find stocktake by DATES (not by ID!)
try:
    stocktake = Stocktake.objects.get(
        hotel=period.hotel,
        period_start=period.start_date,
        period_end=period.end_date
    )
    print(f"Found stocktake ID: {stocktake.id}")
    print(f"COGS: €{stocktake.total_cogs}")
    print(f"Revenue: €{stocktake.total_revenue}")
except Stocktake.DoesNotExist:
    print("No stocktake exists for this period")
""")
print("=" * 80 + "\n")
