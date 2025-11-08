import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from decimal import Decimal

print("=" * 80)
print("OCTOBER 2024 CLOSING STOCK - DUAL VALUATION")
print("=" * 80)

# Get October period (most recent closed period)
october = StockPeriod.objects.get(period_name="October 2024")
print(f"\nPeriod: {october.period_name}")
print(f"Status: {'CLOSED' if october.is_closed else 'OPEN'}")
print(f"Date Range: {october.start_date} to {october.end_date}")

categories = {
    'D': 'Draught Beers',
    'B': 'Bottled Beers',
    'S': 'Spirits',
    'M': 'Minerals/Syrups',
    'W': 'Wine'
}

print("\n" + "=" * 80)
print("CURRENT STOCK VALUATION (As of Oct 31, 2024)")
print("=" * 80)
print(f"{'Category':<20} {'Cost Value':<15} {'Sales Value':<15} {'Potential Profit':<15}")
print("-" * 80)

grand_cost_value = Decimal('0.00')
grand_sales_value = Decimal('0.00')
category_data = {}

for code, name in categories.items():
    snapshots = list(StockSnapshot.objects.filter(
        period=october,
        item__category_id=code
    ).select_related('item'))
    
    cost_value = Decimal('0.00')
    sales_value = Decimal('0.00')
    items_with_price = 0
    items_without_price = 0
    
    for snapshot in snapshots:
        item = snapshot.item
        
        # Cost value (what we paid)
        cost_value += snapshot.closing_stock_value
        
        # Calculate servings in stock
        if code in ['D', 'B', 'M']:
            servings = (snapshot.closing_full_units * item.uom) + snapshot.closing_partial_units
        else:  # S, W
            servings = (snapshot.closing_full_units * item.uom) + (snapshot.closing_partial_units * item.uom)
        
        # Sales value (what we can sell it for)
        if code == 'W' and item.bottle_price:
            # Wine by bottle
            bottles = snapshot.closing_full_units + (snapshot.closing_partial_units if snapshot.closing_partial_units < 1 else 0)
            sales_value += bottles * item.bottle_price
            items_with_price += 1
        elif item.menu_price:
            # By serving
            sales_value += servings * item.menu_price
            items_with_price += 1
        else:
            items_without_price += 1
    
    potential_profit = sales_value - cost_value
    
    category_data[code] = {
        'name': name,
        'cost_value': cost_value,
        'sales_value': sales_value,
        'potential_profit': potential_profit,
        'items_with_price': items_with_price,
        'items_without_price': items_without_price
    }
    
    grand_cost_value += cost_value
    grand_sales_value += sales_value
    
    print(f"{name:<20} €{cost_value:>13,.2f} €{sales_value:>13,.2f} €{potential_profit:>13,.2f}")

grand_potential_profit = grand_sales_value - grand_cost_value

print("-" * 80)
print(f"{'TOTAL':<20} €{grand_cost_value:>13,.2f} €{grand_sales_value:>13,.2f} €{grand_potential_profit:>13,.2f}")

print("\n" + "=" * 80)
print("WHAT THESE NUMBERS MEAN")
print("=" * 80)

print(f"\n1. COST VALUE (Storage Value): €{grand_cost_value:,.2f}")
print("   - This is what you PAID for the current stock")
print("   - Shows your investment in inventory")
print("   - This is the closing stock value from October")

print(f"\n2. SALES VALUE (Potential Revenue): €{grand_sales_value:,.2f}")
print("   - This is what you can SELL the current stock for")
print("   - Shows potential revenue if you sold everything")
print("   - Based on your menu prices")

print(f"\n3. POTENTIAL PROFIT: €{grand_potential_profit:,.2f}")
print("   - This is your markup on current inventory")
print("   - Difference between what you paid vs what you'll sell for")
if grand_cost_value > 0:
    markup = (grand_potential_profit / grand_cost_value) * 100
    print(f"   - Markup: {markup:.1f}%")

print("\n" + "=" * 80)
print("CATEGORY BREAKDOWN")
print("=" * 80)

for code in ['D', 'B', 'S', 'M', 'W']:
    data = category_data[code]
    
    if data['cost_value'] > 0:
        markup = (data['potential_profit'] / data['cost_value']) * 100
    else:
        markup = Decimal('0.00')
    
    print(f"\n{data['name']}:")
    print(f"  Cost Value:        €{data['cost_value']:>12,.2f}")
    print(f"  Sales Value:       €{data['sales_value']:>12,.2f}")
    print(f"  Potential Profit:  €{data['potential_profit']:>12,.2f}")
    print(f"  Markup:            {markup:>12.1f}%")
    print(f"  Items with price:  {data['items_with_price']}")
    print(f"  Items w/o price:   {data['items_without_price']}")

print("\n" + "=" * 80)
print("FOR FRONTEND DISPLAY")
print("=" * 80)

print("\nShow TWO main numbers:")
print(f"\n  📦 CURRENT STOCK VALUE (Cost):     €{grand_cost_value:,.2f}")
print(f"  💰 POTENTIAL SALES VALUE (Retail): €{grand_sales_value:,.2f}")
print(f"  📈 POTENTIAL PROFIT (Markup):      €{grand_potential_profit:,.2f}")

print("\nThis tells you:")
print("  - How much money is 'locked up' in inventory")
print("  - How much revenue you'll generate when it sells")
print("  - Your markup/profit margin")

print("\n⚠ Note: Minerals category has low sales value because")
print("   most items are missing menu prices!")
