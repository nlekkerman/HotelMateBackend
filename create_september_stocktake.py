"""
Create Stocktake for September 2025
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake
from hotel.models import Hotel
from datetime import date

# Get September 2025 period
september_period = StockPeriod.objects.get(id=8)
print(f"\n📅 Period: {september_period.period_name}")
print(f"   Dates: {september_period.start_date} to {september_period.end_date}")

# Get hotel
hotel = september_period.hotel
print(f"   Hotel: {hotel.name}")

# Check if stocktake already exists
existing = Stocktake.objects.filter(
    hotel=hotel,
    period_start=september_period.start_date,
    period_end=september_period.end_date
).first()

if existing:
    print(f"\n⚠️  Stocktake already exists (ID: {existing.id})")
    print(f"   Status: {existing.status}")
else:
    # Create new stocktake
    stocktake = Stocktake.objects.create(
        hotel=hotel,
        period_start=september_period.start_date,
        period_end=september_period.end_date,
        status=Stocktake.DRAFT,
        notes="September 2025 stocktake - Manual financial values entered"
    )
    
    print(f"\n✅ Created Stocktake ID: {stocktake.id}")
    print(f"   Status: {stocktake.status}")
    print(f"   Period: {stocktake.period_start} to {stocktake.period_end}")
    
    # Display financial summary (will use period manual values)
    print(f"\n📊 Financial Summary:")
    print(f"   Total COGS: €{stocktake.total_cogs:,.2f}")
    print(f"   Total Revenue: €{stocktake.total_revenue:,.2f}")
    
    if stocktake.gross_profit_percentage:
        print(f"   GP%: {stocktake.gross_profit_percentage}%")
    if stocktake.pour_cost_percentage:
        print(f"   Pour Cost%: {stocktake.pour_cost_percentage}%")
    
    print(f"\n✅ September 2025 Stocktake created successfully!\n")
