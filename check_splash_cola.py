import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, StockItem

# Find BIB items
print("\n=== Finding BIB Items ===")
bib_items = StockItem.objects.filter(subcategory='BIB')
print(f"Found {bib_items.count()} BIB items")

for item in bib_items:
    print(f"  - {item.sku}: {item.name}")

# Get Splash Cola specifically
print("\n=== Checking M25 Splash Cola ===")
m25_items = StockItem.objects.filter(sku='M25')
if m25_items.exists():
    m25 = m25_items.first()
    print(f"SKU: {m25.sku}")
    print(f"Name: {m25.name}")
    print(f"Category: {m25.category.name if m25.category else 'None'}")
    print(f"Subcategory: {m25.subcategory or 'None'}")
    print(f"Size: {m25.size}")
    print(f"UOM: {m25.uom}")
    
    # Check stocktake line
    line = StocktakeLine.objects.filter(
        stocktake__id=3,
        item=m25
    ).first()
    
    if line:
        print(f"\n📊 February Stocktake Line:")
        print(f"  Counted Full: {line.counted_full_units} containers")
        print(f"  Counted Partial: {line.counted_partial_units} liters")
        print(f"  Counted Qty: {line.counted_qty:.2f}")
        print(f"  Valuation Cost: €{line.valuation_cost:.4f}")
        print(f"  Counted Value: €{line.counted_value:.2f}")
        print(f"  Variance Value: €{line.variance_value:.2f}")
        
        # Calculate what it should be
        total_liters = (float(line.counted_full_units or 0) * 18) + float(line.counted_partial_units or 0)
        excel_cost_per_liter = 2.50
        expected_value = total_liters * excel_cost_per_liter
        
        print(f"\n🧮 Excel Calculation:")
        print(f"  Total liters: {total_liters:.2f}L")
        print(f"  Cost per liter: €{excel_cost_per_liter:.2f}")
        print(f"  Expected value: {total_liters:.2f} × €{excel_cost_per_liter:.2f} = €{expected_value:.2f}")
        print(f"  System shows: €{line.counted_value:.2f}")
        print(f"  Difference: €{abs(float(line.counted_value) - expected_value):.2f}")
