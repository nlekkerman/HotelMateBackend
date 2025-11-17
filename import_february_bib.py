"""
Import February BIB counted values from Excel data.
Excel shows counted stock in LITERS and cost per LITER.

M25 Splash Cola 18LTR: 171.16L @ €2.50/L = €427.90
M24 Splash Energy 18LTR: 182.64L @ €1.50/L = €273.96
M23 Splash White 18LTR: 173.06L @ €1.50/L = €259.59
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, Stocktake, StocktakeLine

# Excel data: SKU -> (counted_liters, cost_per_liter)
# Stock Value = Closing Liters × Cost Per Liter
excel_bib_data = {
    'M25': {'liters': Decimal('171.16'), 'cost_per_liter': Decimal('2.50')},
    'M24': {'liters': Decimal('182.64'), 'cost_per_liter': Decimal('1.50')},
    'M23': {'liters': Decimal('173.06'), 'cost_per_liter': Decimal('1.50')},
}

def main():
    print("\n" + "="*80)
    print("IMPORT FEBRUARY BIB DATA FROM EXCEL")
    print("="*80)
    
    # Get February stocktake (hotel_id=2 is bogans)
    stocktake = Stocktake.objects.filter(
        hotel_id=2,
        period_start__year=2025,
        period_start__month=2
    ).first()
    
    if not stocktake:
        print("❌ February stocktake not found!")
        return
    
    print(f"\n✅ Found stocktake ID: {stocktake.id}")
    print(f"   Period: {stocktake.period_start} to {stocktake.period_end}")
    
    updated_count = 0
    
    for sku, data in excel_bib_data.items():
        # Get item (hotel_id=2 is bogans)
        item = StockItem.objects.filter(sku=sku, hotel_id=2).first()
        if not item:
            print(f"\n❌ Item {sku} not found")
            continue
        
        # Get or create stocktake line
        line = StocktakeLine.objects.filter(
            stocktake=stocktake,
            item=item
        ).first()
        
        if not line:
            print(f"\n❌ No stocktake line for {sku}")
            continue
        
        # Excel shows counted LITERS total
        # Convert to full containers + partial liters
        total_liters = float(data['liters'])
        full_containers = int(total_liters // 18)  # 18L per container
        partial_liters = Decimal(str(total_liters % 18))  # Remainder
        
        expected_value = data['liters'] * data['cost_per_liter']
        
        print(f"\n{sku} - {item.name}")
        print(f"  Excel: {data['liters']}L @ €{data['cost_per_liter']}/L")
        print(f"  Split: {full_containers} containers + {partial_liters:.2f}L")
        print(f"  Expected stock value: €{expected_value:.2f}")
        
        # Update line
        line.counted_full_units = full_containers
        line.counted_partial_units = partial_liters
        
        # Cost per serving (250ml = 0.25L)
        cost_per_serving = data['cost_per_liter'] * Decimal('0.25')
        line.valuation_cost = cost_per_serving
        
        print(f"  Cost: €{data['cost_per_liter']}/L = €{cost_per_serving:.4f}/serving")
        
        line.save()
        
        print(f"  ✅ Updated: {line.counted_full_units} containers + {line.counted_partial_units} liters")
        print(f"  Counted qty: {line.counted_qty:.2f} servings")
        print(f"  Counted value: €{line.counted_value:.2f}")
        print(f"  Variance value: €{line.variance_value:.2f}")
        
        updated_count += 1
    
    print(f"\n{'='*80}")
    print(f"✅ Updated {updated_count} BIB items")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
