"""
Test two different valuation calculation methods for draught beers:
1. Per-item method: Calculate value for each item, then sum
2. Aggregated method: Sum quantities, then calculate total value

This will help identify if calculation methodology causes the €6.59 difference.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from decimal import Decimal

# Fetch October 2025 stocktake
stocktake = Stocktake.objects.get(id=18)

print(f"\nOctober 2025 Stocktake Analysis")
print(f"=" * 80)
print(f"Stocktake ID: {stocktake.id}")
print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
print(f"Status: {stocktake.status}")
print(f"\n")

# Get all draught beer lines
draught_lines = stocktake.lines.filter(
    item__category__code='D'
).select_related('item').order_by('item__sku')

print(f"DRAUGHT BEERS - DETAILED CALCULATIONS")
print(f"=" * 80)
print(f"\n{'SKU':<10} {'Item Name':<30} {'Counted Qty':<15} {'Val Cost':<15} {'Line Value':<15}")
print(f"{'-'*10} {'-'*30} {'-'*15} {'-'*15} {'-'*15}")

# METHOD 1: Per-item calculation (current system method)
total_value_per_item = Decimal('0.00')
total_qty_all_items = Decimal('0.0000')

for line in draught_lines:
    counted_qty = line.counted_qty
    valuation_cost = line.valuation_cost
    line_value = counted_qty * valuation_cost
    
    total_value_per_item += line_value
    total_qty_all_items += counted_qty
    
    print(f"{line.item.sku:<10} {line.item.name[:28]:<30} {counted_qty:<15.4f} €{valuation_cost:<14.4f} €{line_value:<14.2f}")

print(f"\n{'='*80}")
print(f"METHOD 1: PER-ITEM CALCULATION (Current System Method)")
print(f"{'='*80}")
print(f"Total Counted Qty (all items): {total_qty_all_items:.4f} pints")
print(f"Total Value (sum of line values): €{total_value_per_item:.2f}")
print(f"\n")

# METHOD 2: Aggregated calculation (sum quantities first, then calculate)
# This method would use a single valuation_cost for all items - not realistic
# But let's see what happens if we calculate weighted average cost

print(f"METHOD 2: WEIGHTED AVERAGE VALUATION COST")
print(f"=" * 80)

# Calculate weighted average valuation cost
total_cost_weight = Decimal('0.0000')
for line in draught_lines:
    cost_weight = line.counted_qty * line.valuation_cost
    total_cost_weight += cost_weight

weighted_avg_cost = total_cost_weight / total_qty_all_items if total_qty_all_items > 0 else Decimal('0.0000')
aggregated_value = total_qty_all_items * weighted_avg_cost

print(f"Total Counted Qty: {total_qty_all_items:.4f} pints")
print(f"Weighted Avg Valuation Cost: €{weighted_avg_cost:.4f} per pint")
print(f"Total Value (qty × avg cost): €{aggregated_value:.2f}")
print(f"\n")

# COMPARISON
print(f"COMPARISON")
print(f"=" * 80)
print(f"Method 1 (Per-Item):        €{total_value_per_item:.2f}")
print(f"Method 2 (Weighted Avg):    €{aggregated_value:.2f}")
print(f"Difference:                 €{abs(total_value_per_item - aggregated_value):.2f}")
print(f"\n")

# Show Excel comparison
print(f"EXCEL COMPARISON")
print(f"=" * 80)
excel_total = Decimal('5311.62')
system_total = total_value_per_item
difference = system_total - excel_total

print(f"Excel Total:                €{excel_total:.2f}")
print(f"System Total (Method 1):    €{system_total:.2f}")
print(f"Difference:                 €{difference:.2f}")
print(f"\n")

# Check for rounding issues - show precision
print(f"PRECISION ANALYSIS")
print(f"=" * 80)
print(f"\nShowing full precision for each line value calculation:")
print(f"\n{'SKU':<10} {'Counted Qty':<20} {'Valuation Cost':<20} {'Line Value (full precision)':<30}")
print(f"{'-'*10} {'-'*20} {'-'*20} {'-'*30}")

precise_total = Decimal('0')
for line in draught_lines:
    counted_qty = line.counted_qty
    valuation_cost = line.valuation_cost
    line_value_precise = counted_qty * valuation_cost
    precise_total += line_value_precise
    
    print(f"{line.item.sku:<10} {str(counted_qty):<20} {str(valuation_cost):<20} {str(line_value_precise):<30}")

print(f"\n{'='*80}")
print(f"Precise Total (no rounding): {precise_total}")
print(f"Rounded Total:               €{float(precise_total):.2f}")
print(f"\n")
