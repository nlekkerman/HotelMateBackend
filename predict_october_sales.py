import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from decimal import Decimal, ROUND_HALF_UP

print("=" * 80)
print("OCTOBER 2024 PREDICTED SALES ANALYSIS")
print("Based on Net Stock Change (Sept Closing - Oct Closing)")
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
print("CATEGORY SUMMARY")
print("=" * 80)
print(f"{'Category':<20} {'Sept Close':<15} {'Oct Close':<15} {'Stock Change':<15}")
print("-" * 80)

category_data = {}
grand_totals = {
    'sept_value': Decimal('0.00'),
    'oct_value': Decimal('0.00'),
    'stock_change': Decimal('0.00'),
    'consumption_servings': Decimal('0.00'),
    'predicted_revenue': Decimal('0.00')
}

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
    
    # Create lookup dict for October
    oct_lookup = {s.item_id: s for s in oct_snapshots}
    
    # Calculate totals and consumption
    sept_value = sum(s.closing_stock_value for s in sept_snapshots)
    oct_value = sum(s.closing_stock_value for s in oct_snapshots)
    stock_change = oct_value - sept_value
    
    category_data[code] = {
        'name': name,
        'sept_value': sept_value,
        'oct_value': oct_value,
        'stock_change': stock_change,
        'items': []
    }
    
    grand_totals['sept_value'] += sept_value
    grand_totals['oct_value'] += oct_value
    grand_totals['stock_change'] += stock_change
    
    print(f"{name:<20} €{sept_value:>13,.2f} €{oct_value:>13,.2f} €{stock_change:>13,.2f}")
    
    # Calculate per-item consumption
    for sept_snap in sept_snapshots:
        oct_snap = oct_lookup.get(sept_snap.item_id)
        if not oct_snap:
            continue
        
        item = sept_snap.item
        
        # Calculate servings consumed (negative = net increase)
        if code in ['D', 'B', 'M']:
            # Full units converted + partial units
            sept_servings = (sept_snap.closing_full_units * item.uom) + sept_snap.closing_partial_units
            oct_servings = (oct_snap.closing_full_units * item.uom) + oct_snap.closing_partial_units
        else:  # S, W
            # Bottles + percentage
            sept_servings = (sept_snap.closing_full_units * item.uom) + (sept_snap.closing_partial_units * item.uom)
            oct_servings = (oct_snap.closing_full_units * item.uom) + (oct_snap.closing_partial_units * item.uom)
        
        consumption = sept_servings - oct_servings
        
        # Calculate predicted revenue (only for positive consumption)
        predicted_revenue = Decimal('0.00')
        if consumption > 0:
            if code == 'W' and item.bottle_price:
                # Wine sold by bottle
                bottles_consumed = consumption / item.uom if item.uom > 0 else Decimal('0.00')
                predicted_revenue = bottles_consumed * item.bottle_price
            elif item.menu_price:
                # Sold by serving
                predicted_revenue = consumption * item.menu_price
        
        category_data[code]['items'].append({
            'sku': item.sku,
            'name': item.name,
            'sept_servings': sept_servings,
            'oct_servings': oct_servings,
            'consumption': consumption,
            'menu_price': item.menu_price,
            'bottle_price': item.bottle_price,
            'predicted_revenue': predicted_revenue
        })

print("-" * 80)
print(f"{'TOTAL':<20} €{grand_totals['sept_value']:>13,.2f} €{grand_totals['oct_value']:>13,.2f} €{grand_totals['stock_change']:>13,.2f}")

print("\n" + "=" * 80)
print("PREDICTED SALES BY CATEGORY")
print("=" * 80)

for code in ['D', 'B', 'S', 'M', 'W']:
    data = category_data[code]
    name = data['name']
    
    # Calculate totals for items with positive consumption
    items_sold = [item for item in data['items'] if item['consumption'] > 0]
    items_purchased = [item for item in data['items'] if item['consumption'] < 0]
    
    total_consumption = sum(item['consumption'] for item in items_sold)
    total_revenue = sum(item['predicted_revenue'] for item in items_sold)
    
    items_with_price = [item for item in items_sold if item['predicted_revenue'] > 0]
    items_no_price = [item for item in items_sold if item['predicted_revenue'] == 0]
    
    grand_totals['consumption_servings'] += total_consumption
    grand_totals['predicted_revenue'] += total_revenue
    
    print(f"\n{name}")
    print("-" * 80)
    print(f"Stock Change: €{data['stock_change']:,.2f}")
    print(f"Items with net sales: {len(items_sold)}")
    print(f"Items with net purchases: {len(items_purchased)}")
    print(f"Total servings consumed: {total_consumption:,.2f}")
    print(f"Items with menu price: {len(items_with_price)}")
    print(f"Items without price: {len(items_no_price)}")
    print(f"PREDICTED REVENUE: €{total_revenue:,.2f}")
    
    # Show top 10 sellers
    if items_with_price:
        sorted_items = sorted(items_with_price, key=lambda x: x['predicted_revenue'], reverse=True)
        print(f"\nTop 10 Revenue Items:")
        print(f"{'SKU':<10} {'Name':<35} {'Sold':<12} {'Price':<10} {'Revenue':<12}")
        print("-" * 80)
        for item in sorted_items[:10]:
            sold_display = f"{item['consumption']:.2f}"
            price_display = f"€{item['menu_price'] or item['bottle_price'] or 0:.2f}"
            revenue_display = f"€{item['predicted_revenue']:,.2f}"
            print(f"{item['sku']:<10} {item['name'][:35]:<35} {sold_display:<12} {price_display:<10} {revenue_display:<12}")

print("\n" + "=" * 80)
print("OVERALL PREDICTED SALES")
print("=" * 80)
print(f"Total Servings Consumed: {grand_totals['consumption_servings']:,.2f}")
print(f"TOTAL PREDICTED REVENUE: €{grand_totals['predicted_revenue']:,.2f}")

print("\n" + "=" * 80)
print("INTERPRETATION & VALIDATION")
print("=" * 80)
print("\n⚠ IMPORTANT NOTES:")
print("  - This is NET consumption (Sales - Purchases)")
print("  - Negative stock change = More purchased than sold")
print("  - Predicted revenue is MINIMUM (doesn't include purchases)")
print("\nTo get ACTUAL SALES, compare this with:")
print("  1. Your POS/Till data for October")
print("  2. Your delivery invoices (what was purchased)")
print("\nExpected pattern:")
print("  Actual Sales = Predicted Revenue + (Revenue from purchased stock)")
print("\nCategories with negative change (Bottled, Minerals):")
print("  → Heavy restocking during October")
print("  → Actual sales higher than predicted revenue")

print("\n" + "=" * 80)
print("WHAT TO COMPARE:")
print("=" * 80)
print(f"\n1. Compare predicted revenue (€{grand_totals['predicted_revenue']:,.2f}) with POS total")
print("2. If POS total is HIGHER → You had deliveries during October")
print("3. If POS total is LOWER → Check for:")
print("   - Waste/breakage not recorded")
print("   - Staff drinks not recorded")
print("   - Pricing discrepancies")
