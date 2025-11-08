import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockMovement
from decimal import Decimal

print("=" * 80)
print("OCTOBER 2024 SALES REPORT WITH PURCHASES")
print("=" * 80)

# Get periods
october = StockPeriod.objects.get(period_name="October 2024")
september = StockPeriod.objects.get(period_name="September 2024")

categories = {
    'D': 'Draught Beers',
    'B': 'Bottled Beers',
    'S': 'Spirits',
    'M': 'Minerals/Syrups',
    'W': 'Wine'
}

print("\n" + "=" * 80)
print("FULL OCTOBER CALCULATION")
print("Formula: Sales = (Sept Opening + Purchases) - Oct Closing")
print("=" * 80)

grand_totals = {
    'sept_opening': Decimal('0.00'),
    'purchases': Decimal('0.00'),
    'oct_closing': Decimal('0.00'),
    'consumption_cost': Decimal('0.00'),
    'consumption_servings': Decimal('0.00'),
    'predicted_revenue': Decimal('0.00')
}

category_results = {}

for code, name in categories.items():
    # Get snapshots
    sept_snapshots = list(StockSnapshot.objects.filter(
        period=september,
        item__category_id=code
    ).select_related('item'))
    
    oct_snapshots = list(StockSnapshot.objects.filter(
        period=october,
        item__category_id=code
    ).select_related('item'))
    
    # Get purchases
    purchases = StockMovement.objects.filter(
        period=october,
        movement_type='PURCHASE',
        item__category_id=code
    )
    
    # Calculate values
    sept_value = sum(s.closing_stock_value for s in sept_snapshots)
    oct_value = sum(s.closing_stock_value for s in oct_snapshots)
    purchase_value = sum(
        (p.quantity * p.unit_cost) for p in purchases
    )
    
    # Consumption = Opening + Purchases - Closing
    consumption_cost = sept_value + purchase_value - oct_value
    
    # Create lookup for October
    oct_lookup = {s.item_id: s for s in oct_snapshots}
    
    # Calculate servings and revenue
    total_servings = Decimal('0.00')
    total_revenue = Decimal('0.00')
    
    for sept_snap in sept_snapshots:
        oct_snap = oct_lookup.get(sept_snap.item_id)
        if not oct_snap:
            continue
        
        item = sept_snap.item
        
        # Get purchases for this item
        item_purchases = purchases.filter(item=item)
        purchased_servings = sum(p.quantity for p in item_purchases)
        
        # Calculate opening + purchases
        if code in ['D', 'B', 'M']:
            sept_servings = (
                (sept_snap.closing_full_units * item.uom) +
                sept_snap.closing_partial_units
            )
            oct_servings = (
                (oct_snap.closing_full_units * item.uom) +
                oct_snap.closing_partial_units
            )
        else:  # S, W
            sept_servings = (
                (sept_snap.closing_full_units * item.uom) +
                (sept_snap.closing_partial_units * item.uom)
            )
            oct_servings = (
                (oct_snap.closing_full_units * item.uom) +
                (oct_snap.closing_partial_units * item.uom)
            )
        
        # Consumption = Opening + Purchases - Closing
        consumption = sept_servings + purchased_servings - oct_servings
        
        if consumption > 0:
            total_servings += consumption
            
            # Calculate revenue
            if code == 'W' and item.bottle_price:
                bottles = consumption / item.uom if item.uom > 0 else Decimal('0.00')
                total_revenue += bottles * item.bottle_price
            elif item.menu_price:
                total_revenue += consumption * item.menu_price
    
    category_results[code] = {
        'name': name,
        'sept_value': sept_value,
        'purchase_value': purchase_value,
        'oct_value': oct_value,
        'consumption_cost': consumption_cost,
        'servings': total_servings,
        'revenue': total_revenue
    }
    
    grand_totals['sept_opening'] += sept_value
    grand_totals['purchases'] += purchase_value
    grand_totals['oct_closing'] += oct_value
    grand_totals['consumption_cost'] += consumption_cost
    grand_totals['consumption_servings'] += total_servings
    grand_totals['predicted_revenue'] += total_revenue

# Display results
print(f"\n{'Category':<20} {'Sept Open':<15} {'Purchases':<15} {'Oct Close':<15}")
print("-" * 80)
for code in ['D', 'B', 'S', 'M', 'W']:
    data = category_results[code]
    print(f"{data['name']:<20} €{data['sept_value']:>13,.2f} "
          f"€{data['purchase_value']:>13,.2f} €{data['oct_value']:>13,.2f}")

print("-" * 80)
print(f"{'TOTAL':<20} €{grand_totals['sept_opening']:>13,.2f} "
      f"€{grand_totals['purchases']:>13,.2f} €{grand_totals['oct_closing']:>13,.2f}")

print("\n" + "=" * 80)
print("OCTOBER SALES BY CATEGORY")
print("=" * 80)
print(f"{'Category':<20} {'Consumed':<15} {'Servings':<15} {'Revenue':<15}")
print("-" * 80)

for code in ['D', 'B', 'S', 'M', 'W']:
    data = category_results[code]
    print(f"{data['name']:<20} €{data['consumption_cost']:>13,.2f} "
          f"{data['servings']:>13,.2f} €{data['revenue']:>13,.2f}")

print("-" * 80)
print(f"{'TOTAL':<20} €{grand_totals['consumption_cost']:>13,.2f} "
      f"{grand_totals['consumption_servings']:>13,.2f} €{grand_totals['predicted_revenue']:>13,.2f}")

print("\n" + "=" * 80)
print("PROFITABILITY ANALYSIS")
print("=" * 80)

gross_profit = grand_totals['predicted_revenue'] - grand_totals['consumption_cost']
if grand_totals['predicted_revenue'] > 0:
    gp_percentage = (gross_profit / grand_totals['predicted_revenue']) * 100
else:
    gp_percentage = Decimal('0.00')

print(f"\nTotal Sales Revenue:      €{grand_totals['predicted_revenue']:>15,.2f}")
print(f"Total Cost of Sales:      €{grand_totals['consumption_cost']:>15,.2f}")
print(f"Gross Profit:             €{gross_profit:>15,.2f}")
print(f"Gross Profit %:           {gp_percentage:>15,.2f}%")

print("\n" + "=" * 80)
print("CATEGORY PERFORMANCE")
print("=" * 80)
print(f"{'Category':<20} {'Revenue':<15} {'GP%':<10} {'% of Total':<15}")
print("-" * 80)

for code in ['D', 'B', 'S', 'M', 'W']:
    data = category_results[code]
    
    if data['revenue'] > 0:
        cat_gp = ((data['revenue'] - data['consumption_cost']) / data['revenue']) * 100
        pct_total = (data['revenue'] / grand_totals['predicted_revenue']) * 100
    else:
        cat_gp = Decimal('0.00')
        pct_total = Decimal('0.00')
    
    print(f"{data['name']:<20} €{data['revenue']:>13,.2f} "
          f"{cat_gp:>8,.1f}% {pct_total:>13,.1f}%")

print("\n" + "=" * 80)
print("✓ OCTOBER 2024 SALES CALCULATED")
print("=" * 80)
print(f"\nTotal Revenue: €{grand_totals['predicted_revenue']:,.2f}")
print(f"Gross Profit %: {gp_percentage:.1f}%")
print("\n⚠ This is MOCK DATA - Replace with actual POS figures when available")
