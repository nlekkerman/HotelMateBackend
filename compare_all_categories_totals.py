import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

# Excel expected totals
excel_totals = {
    'D': {'name': 'Draught Beers', 'total': Decimal('2436.33')},
    'B': {'name': 'Bottled Beers', 'total': Decimal('1097.25')},
    'S': {'name': 'Spirits', 'total': Decimal('11282.39')},
    'M': {'name': 'Minerals/Syrups', 'total': Decimal('2986.95')},
    'W': {'name': 'Wine', 'total': Decimal('1355.87')},
}

print("=" * 100)
print("APRIL 2025 CATEGORY TOTALS COMPARISON: SYSTEM vs EXCEL")
print("=" * 100)

# Get April 2025 stocktake
hotel = Hotel.objects.first()

stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=4
).first()

if not stocktake:
    print("❌ No April 2025 stocktake found!")
    exit()

print(f"\nStocktake: {stocktake.period_start.strftime('%B %Y')}")
print(f"Status: {stocktake.status}")

print(f"\n{'CATEGORY TOTALS':-^100}")
print(f"{'Category':<20} {'Items':<8} {'Excel Total':>15} {'System Total':>15} {'Difference':>15} {'Status':<10}")
print("-" * 100)

grand_total_excel = Decimal('0.00')
grand_total_system = Decimal('0.00')
all_match = True

for category_code in ['D', 'B', 'S', 'M', 'W']:
    category_info = excel_totals[category_code]
    
    # Get system total for this category
    lines = StocktakeLine.objects.filter(
        stocktake=stocktake,
        item__category__code=category_code
    ).select_related('item', 'item__category')
    
    item_count = lines.count()
    system_total = sum(line.counted_value for line in lines)
    excel_total = category_info['total']
    
    difference = system_total - excel_total
    
    grand_total_excel += excel_total
    grand_total_system += system_total
    
    # Determine status
    if abs(difference) < Decimal('0.05'):
        status = "✓ MATCH"
    elif abs(difference) < Decimal('1.00'):
        status = "⚠ CLOSE"
    else:
        status = "✗ DIFF"
        all_match = False
    
    print(f"{category_info['name']:<20} {item_count:<8} €{excel_total:>13,.2f} €{system_total:>13,.2f} €{difference:>+13,.2f} {status:<10}")

print("-" * 100)
print(f"{'GRAND TOTALS':<20} {'':<8} €{grand_total_excel:>13,.2f} €{grand_total_system:>13,.2f} €{grand_total_system - grand_total_excel:>+13,.2f}")

# Detailed breakdown for categories with differences
print(f"\n{'DETAILED ANALYSIS':-^100}")

for category_code in ['D', 'B', 'S', 'M', 'W']:
    category_info = excel_totals[category_code]
    
    lines = StocktakeLine.objects.filter(
        stocktake=stocktake,
        item__category__code=category_code
    ).select_related('item', 'item__category')
    
    system_total = sum(line.counted_value for line in lines)
    excel_total = category_info['total']
    difference = system_total - excel_total
    
    if abs(difference) >= Decimal('0.05'):
        print(f"\n{category_info['name']} ({category_code}):")
        print(f"  Excel:  €{excel_total:,.2f}")
        print(f"  System: €{system_total:,.2f}")
        print(f"  Diff:   €{difference:+,.2f}")
        
        # For Minerals, show subcategory breakdown
        if category_code == 'M':
            print(f"\n  Subcategory Breakdown:")
            subcategories = ['SOFT_DRINKS', 'SYRUPS', 'BIB', 'BULK_JUICES', 'JUICES', 'CORDIALS']
            for subcat in subcategories:
                subcat_lines = lines.filter(item__subcategory=subcat)
                if subcat_lines.exists():
                    subcat_total = sum(line.counted_value for line in subcat_lines)
                    subcat_count = subcat_lines.count()
                    print(f"    {subcat:<15} {subcat_count:>3} items  €{subcat_total:>10,.2f}")

print("\n" + "=" * 100)

if all_match:
    print("✅ ALL CATEGORIES MATCH!")
else:
    print("⚠️  Some categories have differences - see details above")

print("=" * 100)
