"""
Test script to check variance calculation in stocktakes
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from hotel.models import Hotel

hotel = Hotel.objects.first()
print(f"Testing stocktakes for: {hotel.name}")
print("=" * 100)

# Get the most recent stocktake
stocktakes = Stocktake.objects.filter(hotel=hotel).order_by('-created_at')[:3]

for stocktake in stocktakes:
    print(f"\nStocktake ID: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"Status: {stocktake.status}")
    
    lines = stocktake.lines.all()
    print(f"\nTotal Lines: {lines.count()}")
    
    # Calculate totals
    total_expected = sum(line.expected_value for line in lines)
    total_counted = sum(line.counted_value for line in lines)
    total_variance = sum(line.variance_value for line in lines)
    
    print(f"\nCalculated from lines:")
    print(f"  Total Expected Value:  €{total_expected:,.2f}")
    print(f"  Total Counted Value:   €{total_counted:,.2f}")
    print(f"  Total Variance Value:  €{total_variance:,.2f}")
    
    # Get category totals
    category_totals = stocktake.get_category_totals()
    
    print(f"\nCategory Breakdown:")
    print("-" * 100)
    print(f"{'Category':<20} {'Expected':<15} {'Counted':<15} {'Variance':<15}")
    print("-" * 100)
    
    cat_total_variance = Decimal('0.00')
    for cat_code in ['D', 'B', 'S', 'W', 'M']:
        if cat_code in category_totals:
            cat = category_totals[cat_code]
            cat_total_variance += cat['variance_value']
            print(f"{cat['category_name']:<20} €{float(cat['expected_value']):>12,.2f}  "
                  f"€{float(cat['counted_value']):>12,.2f}  "
                  f"€{float(cat['variance_value']):>12,.2f}")
    
    print("-" * 100)
    print(f"{'TOTAL (from categories)':<20} {'':<15} {'':<15} €{float(cat_total_variance):>12,.2f}")
    print(f"{'TOTAL (from lines)':<20} {'':<15} {'':<15} €{float(total_variance):>12,.2f}")
    
    diff = abs(cat_total_variance - total_variance)
    if diff < Decimal('0.01'):
        print(f"\n✅ Totals match!")
    else:
        print(f"\n❌ Difference: €{float(diff):,.2f}")
    
    print("\n" + "=" * 100)
