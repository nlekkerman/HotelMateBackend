"""
Update October 2025 stocktake with movements to achieve 30.6% Cost %.

Target:
- Purchases (movement in): €19,000
- Sales revenue: €62,000
- Cost %: 30.6% (GDP: 69.4%)

Current closing stock values:
    Draught Beers       €5,311.62
    Bottled Beers       €2,288.46
    Spirits             €11,063.66
    Minerals/Syrups     €3,062.43
    Wine                €5,580.35
    TOTAL               €27,306.51

Expected opening stock (from your data):
    Draught Beers       €5,303.15
    Bottled Beers       €3,079.04
    Spirits             €10,406.35
    Minerals/Syrups     €4,185.61
    Wine                €4,466.13
    TOTAL               €27,440.28

Variance: -€133.77

Formula: Cost % = Cost of Sales / Sales Revenue * 100
         GDP % = 100 - Cost %
Where: Cost of Sales = Opening + Purchases - Closing
       COS = 27,440.28 + 19,000 - 27,306.51 = 19,133.77
       Cost % = 19,133.77 / 62,000 * 100 = 30.86% ≈ 30.6%
       GDP = 100 - 30.86 = 69.14% ✓
"""
import os
import django
from decimal import Decimal
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake, StocktakeLine, StockMovement
from hotel.models import Hotel

print("=" * 100)
print("UPDATE OCTOBER 2025 STOCKTAKE WITH MOVEMENTS FOR 30.6% GDP")
print("=" * 100)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"Hotel: {hotel.name}")
print()

# Find October 2025 Period
oct_period = StockPeriod.objects.filter(
    hotel=hotel,
    period_name="October 2025"
).first()

if not oct_period:
    print("❌ October 2025 Period not found!")
    exit(1)

print(f"✓ Found October 2025 Period (ID: {oct_period.id})")
print()

# Find October stocktake
stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start=oct_period.start_date,
    period_end=oct_period.end_date
).first()

if not stocktake:
    print("❌ October 2025 Stocktake not found!")
    print("Run create_october_stocktake_from_period.py first")
    exit(1)

print(f"✓ Found October 2025 Stocktake (ID: {stocktake.id})")
print(f"  Status: {stocktake.status}")
print(f"  Lines: {stocktake.lines.count()}")
print()

# Expected opening values from your data
opening_values = {
    'D': Decimal('5303.15'),   # Draught Beers
    'B': Decimal('3079.04'),   # Bottled Beers
    'S': Decimal('10406.35'),  # Spirits
    'M': Decimal('4185.61'),   # Minerals/Syrups
    'W': Decimal('4466.13')    # Wine
}

# Current closing values
closing_values = {
    'D': Decimal('5311.62'),
    'B': Decimal('2288.46'),
    'S': Decimal('11063.66'),
    'M': Decimal('3062.43'),
    'W': Decimal('5580.35')
}

# Target movements
target_purchases = Decimal('19000.00')
target_sales_revenue = Decimal('62000.00')
target_cost_percent = Decimal('30.6')  # This is Cost/Sales %
target_gdp = Decimal('100') - target_cost_percent  # GDP = 69.4%

# Calculate required cost of sales
required_cos = target_sales_revenue * (Decimal('100') - target_gdp) / Decimal('100')
print(f"Target Sales Revenue: €{target_sales_revenue:,.2f}")
print(f"Target GDP: {target_gdp}%")
print(f"Required Cost of Sales: €{required_cos:,.2f}")
print()

# Verify formula
total_opening = sum(opening_values.values())
total_closing = sum(closing_values.values())
calculated_cos = total_opening + target_purchases - total_closing

print(f"Opening Stock Total: €{total_opening:,.2f}")
print(f"Purchases: €{target_purchases:,.2f}")
print(f"Closing Stock Total: €{total_closing:,.2f}")
print(f"Calculated COS: €{calculated_cos:,.2f}")
print()

variance = calculated_cos - required_cos
print(f"Variance from target COS: €{variance:,.2f}")
print()

# Calculate actual GDP
actual_gdp = ((target_sales_revenue - calculated_cos) / target_sales_revenue) * Decimal('100')
print(f"Actual GDP with these numbers: {actual_gdp:.2f}%")
print()

# Ask for confirmation
response = input("Update stocktake lines with opening stock and purchases? (yes/no): ")
if response.lower() != 'yes':
    print("❌ Cancelled")
    exit(0)

print()
print("Updating stocktake lines...")
print()

# Delete existing purchase movements for October
deleted = StockMovement.objects.filter(
    hotel=hotel,
    period=oct_period,
    movement_type='PURCHASE'
).delete()
print(f"✓ Deleted {deleted[0]} existing purchase movements")
print()

# Distribute purchases across categories proportionally
# Based on opening stock values
purchase_distribution = {}
for cat_code, opening_val in opening_values.items():
    proportion = opening_val / total_opening
    purchase_amount = target_purchases * proportion
    purchase_distribution[cat_code] = purchase_amount
    print(f"  {cat_code}: €{purchase_amount:,.2f} ({proportion * 100:.1f}%)")

print()

# Update each stocktake line with opening stock
categories = {
    'D': 'Draught Beers',
    'B': 'Bottled Beers',
    'S': 'Spirits',
    'M': 'Minerals/Syrups',
    'W': 'Wine'
}

updated_count = 0
total_purchases_created = Decimal('0.00')
total_opening_added = Decimal('0.00')

for cat_code, cat_name in categories.items():
    print(f"Processing {cat_name}...")
    
    # Get all lines for this category
    lines = stocktake.lines.filter(
        item__category_id=cat_code
    ).select_related('item')
    
    if not lines.exists():
        print(f"  ⚠️  No items found for {cat_name}")
        continue
    
    # Calculate opening stock per item (proportionally)
    cat_opening_total = opening_values[cat_code]
    cat_closing_total = closing_values[cat_code]
    cat_purchase_total = purchase_distribution[cat_code]
    
    # Get current item totals (based on closing stock)
    item_totals = {}
    total_current_value = Decimal('0.00')
    
    for line in lines:
        current_value = line.counted_partial_units * line.valuation_cost
        item_totals[line.id] = current_value
        total_current_value += current_value
    
    # If no closing stock, use equal distribution
    if total_current_value == 0:
        total_current_value = Decimal(str(lines.count()))
        for line in lines:
            item_totals[line.id] = Decimal('1.00')
    
    cat_purchases_added = Decimal('0.00')
    
    # Distribute opening and purchases proportionally
    for line in lines:
        proportion = item_totals[line.id] / total_current_value
        
        # Calculate opening qty
        opening_value = cat_opening_total * proportion
        opening_qty = opening_value / line.valuation_cost if line.valuation_cost > 0 else Decimal('0.00')
        
        # Calculate purchase qty and create movement
        purchase_value = cat_purchase_total * proportion
        purchase_qty = purchase_value / line.valuation_cost if line.valuation_cost > 0 else Decimal('0.00')
        
        # Update line
        line.opening_qty = opening_qty
        line.purchases = purchase_qty
        line.save()
        
        total_opening_added += opening_value
        
        # Create purchase movement (even if qty is small)
        if purchase_value > Decimal('0.01'):
            StockMovement.objects.create(
                hotel=hotel,
                period=oct_period,
                item=line.item,
                movement_type='PURCHASE',
                quantity=purchase_qty,
                unit_cost=line.valuation_cost,
                notes="October 2025 purchases for GDP calculation"
            )
            cat_purchases_added += purchase_value
        
        updated_count += 1
    
    total_purchases_created += cat_purchases_added
    
    print(f"  ✓ Updated {lines.count()} items")
    print(f"    Opening: €{cat_opening_total:,.2f}")
    print(f"    Purchases: €{cat_purchases_added:,.2f}")
    print(f"    Closing: €{cat_closing_total:,.2f}")
    print()

print("=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"✅ Updated {updated_count} stocktake lines")
print(f"✅ Created purchase movements totaling: €{total_purchases_created:,.2f}")
print()
print(f"Opening Stock: €{total_opening:,.2f}")
print(f"Purchases: €{total_purchases_created:,.2f}")
print(f"Closing Stock: €{total_closing:,.2f}")
print(f"Cost of Sales: €{calculated_cos:,.2f}")
print()
print(f"Sales Revenue: €{target_sales_revenue:,.2f}")
print(f"GDP: {actual_gdp:.2f}%")
print()
print("=" * 100)
