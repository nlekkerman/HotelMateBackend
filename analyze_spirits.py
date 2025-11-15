"""
Analyze Spirits (S) category in detail
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockItem, Sale

print("=" * 100)
print("SPIRITS CATEGORY ANALYSIS - OCTOBER 2025")
print("=" * 100)

# Get October 2025 stocktake
stocktake = Stocktake.objects.get(id=18)

print(f'\nStocktake ID: {stocktake.id}')
print(f'Period: {stocktake.period_start} to {stocktake.period_end}')
print(f'Status: {stocktake.status}')
print()

# Get spirits lines (category S)
spirits_lines = stocktake.lines.filter(
    item__category__code='S'
).select_related('item').order_by('item__name')

print(f'SPIRITS ITEMS ({spirits_lines.count()} items):')
print('=' * 100)

# Category totals
total_opening_value = Decimal('0.00')
total_purchases_value = Decimal('0.00')
total_expected_value = Decimal('0.00')
total_counted_value = Decimal('0.00')
total_variance_value = Decimal('0.00')
total_sales_value = Decimal('0.00')
total_sales_qty = Decimal('0.0000')

for line in spirits_lines:
    print(f'\n{line.item.sku} - {line.item.name}')
    print(f'  Size: {line.item.size} | UOM: {line.item.uom} shots/bottle')
    print(f'  Unit Cost: €{line.item.unit_cost:.4f}/bottle | Cost per Shot: €{line.item.cost_per_serving:.4f}')
    print(f'  Menu Price: €{line.item.menu_price:.2f}/shot' if line.item.menu_price else '  Menu Price: Not Set')
    
    if line.item.menu_price:
        print(f'  GP%: {line.item.gross_profit_percentage:.2f}% | Pour Cost%: {line.item.pour_cost_percentage:.2f}%')
    
    print(f'\n  INVENTORY:')
    print(f'  Opening: {line.opening_qty:.2f} shots (€{line.opening_value:.2f})')
    print(f'  Purchases: {line.purchases:.2f} shots (€{line.purchases_value:.2f})')
    
    if line.manual_purchases_value:
        print(f'  Manual Purchases: €{line.manual_purchases_value:.2f}')
    
    print(f'  Expected: {line.expected_qty:.2f} shots (€{line.expected_value:.2f})')
    print(f'  Counted: {line.counted_full_units} bottles + {line.counted_partial_units:.2f} bottles')
    print(f'  Counted Qty: {line.counted_qty:.2f} shots (€{line.counted_value:.2f})')
    print(f'  Variance: {line.variance_qty:.2f} shots (€{line.variance_value:.2f})')
    
    # Get sales for this item
    sales_qty = line.sales_qty
    print(f'\n  SALES:')
    print(f'  Sales Qty: {sales_qty:.2f} shots')
    
    if line.manual_sales_value:
        print(f'  Manual Sales Revenue: €{line.manual_sales_value:.2f}')
    
    # Get actual sales records
    item_sales = Sale.objects.filter(
        stocktake=stocktake,
        item=line.item
    )
    
    if item_sales.exists():
        total_sales_revenue = sum(s.total_revenue or 0 for s in item_sales)
        total_sales_cost = sum(s.total_cost for s in item_sales)
        print(f'  Sales Revenue: €{total_sales_revenue:.2f}')
        print(f'  Sales COGS: €{total_sales_cost:.2f}')
        
        if total_sales_revenue > 0:
            gp = ((total_sales_revenue - total_sales_cost) / total_sales_revenue) * 100
            print(f'  Sales GP%: {gp:.2f}%')
    
    # Accumulate totals
    total_opening_value += line.opening_value
    total_purchases_value += line.purchases_value
    total_expected_value += line.expected_value
    total_counted_value += line.counted_value
    total_variance_value += line.variance_value
    total_sales_qty += sales_qty
    
    print('-' * 100)

# Summary
print('\n' + '=' * 100)
print('SPIRITS CATEGORY SUMMARY')
print('=' * 100)

print(f'\nTotal Items: {spirits_lines.count()}')
print(f'\nINVENTORY TOTALS:')
print(f'  Opening Stock Value: €{total_opening_value:,.2f}')
print(f'  Purchases Value: €{total_purchases_value:,.2f}')
print(f'  Expected Stock Value: €{total_expected_value:,.2f}')
print(f'  Counted Stock Value: €{total_counted_value:,.2f}')
print(f'  Variance Value: €{total_variance_value:,.2f}')
print(f'  Variance %: {(total_variance_value / total_expected_value * 100):.2f}%' if total_expected_value else '  Variance %: N/A')

print(f'\nSALES TOTALS:')
print(f'  Total Sales Quantity: {total_sales_qty:,.2f} shots')

# Get all sales for spirits in this stocktake
spirits_sales = Sale.objects.filter(
    stocktake=stocktake,
    item__category__code='S'
)

if spirits_sales.exists():
    total_revenue = sum(s.total_revenue or 0 for s in spirits_sales)
    total_cogs = sum(s.total_cost for s in spirits_sales)
    
    print(f'  Total Sales Revenue: €{total_revenue:,.2f}')
    print(f'  Total Sales COGS: €{total_cogs:,.2f}')
    print(f'  Gross Profit: €{(total_revenue - total_cogs):,.2f}')
    
    if total_revenue > 0:
        gp_pct = ((total_revenue - total_cogs) / total_revenue) * 100
        pour_cost = (total_cogs / total_revenue) * 100
        print(f'  Gross Profit %: {gp_pct:.2f}%')
        print(f'  Pour Cost %: {pour_cost:.2f}%')
else:
    print('  No sales records found')

# Top movers/shakers
print('\n' + '=' * 100)
print('TOP 10 SPIRITS BY VARIANCE (Absolute Value)')
print('=' * 100)

top_variance = sorted(spirits_lines, key=lambda l: abs(l.variance_value), reverse=True)[:10]

for i, line in enumerate(top_variance, 1):
    print(f'{i}. {line.item.name}')
    print(f'   Variance: €{line.variance_value:.2f} ({line.variance_qty:.2f} shots)')
    print()

# Profitability analysis
print('=' * 100)
print('PROFITABILITY ANALYSIS (Items with Menu Prices)')
print('=' * 100)

priced_items = [line for line in spirits_lines if line.item.menu_price]

if priced_items:
    print(f'\n{len(priced_items)} spirits have menu prices set\n')
    
    # Sort by GP%
    by_gp = sorted(priced_items, key=lambda l: l.item.gross_profit_percentage or 0, reverse=True)
    
    print('TOP 5 MOST PROFITABLE (by GP%):')
    for i, line in enumerate(by_gp[:5], 1):
        print(f'{i}. {line.item.name}')
        print(f'   Cost: €{line.item.cost_per_serving:.4f}/shot | Price: €{line.item.menu_price:.2f}/shot')
        print(f'   GP%: {line.item.gross_profit_percentage:.2f}% | Pour Cost: {line.item.pour_cost_percentage:.2f}%')
        print()
    
    print('\nBOTTOM 5 LEAST PROFITABLE (by GP%):')
    for i, line in enumerate(by_gp[-5:], 1):
        print(f'{i}. {line.item.name}')
        print(f'   Cost: €{line.item.cost_per_serving:.4f}/shot | Price: €{line.item.menu_price:.2f}/shot')
        print(f'   GP%: {line.item.gross_profit_percentage:.2f}% | Pour Cost: {line.item.pour_cost_percentage:.2f}%')
        print()
else:
    print('\nNo spirits have menu prices set - cannot calculate profitability')

# Stock value distribution
print('=' * 100)
print('STOCK VALUE DISTRIBUTION')
print('=' * 100)

by_value = sorted(spirits_lines, key=lambda l: l.counted_value, reverse=True)

print('\nTOP 10 SPIRITS BY STOCK VALUE:')
for i, line in enumerate(by_value[:10], 1):
    pct = (line.counted_value / total_counted_value * 100) if total_counted_value else 0
    print(f'{i}. {line.item.name}')
    print(f'   Stock: {line.counted_qty:.2f} shots | Value: €{line.counted_value:.2f} ({pct:.1f}%)')
    print()

print('\n' + '=' * 100)
