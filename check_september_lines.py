"""
Check September 2025 Stocktake Lines
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine

# Get September 2025 stocktake
september = Stocktake.objects.get(id=8)

print(f"\n📅 {september.period_start} to {september.period_end}")
print(f"Status: {september.status}")
print(f"\n📊 Stocktake Lines:")

lines = september.lines.all().select_related('item', 'item__category')
print(f"Total lines: {lines.count()}")

if lines.count() > 0:
    print(f"\nFirst 10 lines:")
    for line in lines[:10]:
        print(f"  {line.item.sku} - {line.item.name}")
        print(f"    Counted: {line.counted_full_units} full + "
              f"{line.counted_partial_units} partial")
        print()
else:
    print("\n⚠️  No stocktake lines found!")
    print("   The stocktake needs to be populated with items.")

print(f"\n💰 Financial Summary:")
print(f"   Total COGS: €{september.total_cogs:,.2f}")
print(f"   Total Revenue: €{september.total_revenue:,.2f}")
if september.gross_profit_percentage:
    print(f"   GP%: {september.gross_profit_percentage}%")
