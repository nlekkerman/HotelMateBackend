"""
Verify opening stock values match previous period's closing stock
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from decimal import Decimal

# Get stocktake #17 (Sept 2025)
stocktake = Stocktake.objects.get(id=17)

print("=" * 80)
print("STOCKTAKE #17 - OPENING STOCK VERIFICATION")
print("=" * 80)

# Calculate opening stock by category
categories = stocktake.get_category_totals()

print("\nOPENING STOCK BY CATEGORY:")
print("-" * 80)

for cat_code, cat_data in categories.items():
    opening_value = cat_data['opening_qty'] * Decimal('0')  # We need to calculate value
    
    # Get opening value from lines
    lines = stocktake.lines.filter(item__category__code=cat_code)
    opening_value = sum(line.opening_qty * line.valuation_cost for line in lines)
    
    print(f"{cat_data['category_name']:20} Opening Value: €{opening_value:,.2f}")

print("-" * 80)

# Calculate total opening stock value
total_opening = Decimal('0')
for line in stocktake.lines.all():
    opening_value = line.opening_qty * line.valuation_cost
    total_opening += opening_value

print(f"{'TOTAL':20} Opening Value: €{total_opening:,.2f}")

print("\n" + "=" * 80)
print("COMPARISON WITH YOUR PREVIOUS CLOSING:")
print("=" * 80)

previous_closing = {
    'Draught Beer': Decimal('5303.15'),
    'Bottled Beer': Decimal('3079.04'),
    'Spirits': Decimal('10406.35'),
    'Minerals & Syrups': Decimal('4185.61'),
    'Wine': Decimal('4466.13'),
}

print("\nCategory                Previous Closing    Current Opening     Difference")
print("-" * 80)

for cat_code, cat_data in categories.items():
    lines = stocktake.lines.filter(item__category__code=cat_code)
    opening_value = sum(line.opening_qty * line.valuation_cost for line in lines)
    
    cat_name = cat_data['category_name']
    prev_close = previous_closing.get(cat_name, Decimal('0'))
    diff = opening_value - prev_close
    
    status = "✅" if abs(diff) < 0.10 else "⚠️"
    print(f"{cat_name:20} €{prev_close:>10,.2f}   €{opening_value:>10,.2f}   €{diff:>10,.2f} {status}")

prev_total = sum(previous_closing.values())
diff_total = total_opening - prev_total

print("-" * 80)
print(f"{'TOTAL':20} €{prev_total:>10,.2f}   €{total_opening:>10,.2f}   €{diff_total:>10,.2f}")

print("\n" + "=" * 80)
print("CURRENT STOCKTAKE SUMMARY:")
print("=" * 80)
print(f"Opening Stock:  €{total_opening:,.2f}")
print(f"Expected Stock: €27,720.48")
print(f"Counted Stock:  €21,669.53")
print(f"Variance:       €-6,050.95")

print("\n💡 INSIGHT:")
if total_opening > 27720:
    print("   Opening stock is HIGHER than expected stock")
    print("   This means there were NEGATIVE movements (sales/waste/consumption)")
    print("   during the period that reduced the expected closing stock.")
else:
    print("   Opening stock is LOWER than expected stock") 
    print("   This would mean purchases were added during the period.")
