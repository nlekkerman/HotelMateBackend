"""
Update Monin syrup names and stock data with complete information.

This script:
1. Updates syrup names to complete versions
2. Sets correct bottle counts and ml values
3. Ensures all syrups are properly categorized as SYRUPS subcategory
4. Sets correct UOM (bottle size in ml)

Data format from spreadsheet:
Name | Size | UOM | Unit Cost | Bottles (decimal) | ? | Total Value

Example: Monin Agave Syrup 700ml | Ind | 1.0 | 9.98 | 2.70 | | 26.95
- Name: Monin Agave Syrup 700ml
- Size: Ind (individual bottle)
- UOM: 1.0 (not used for SYRUPS, we use bottle size ml)
- Unit Cost: 9.98
- Stock: 2.70 bottles = 2 bottles + 0.7*700ml = 2 bottles + 490ml
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

# Syrup data: (sku, full_name, bottle_size_ml, bottles_decimal, unit_cost)
# bottles_decimal format: 2.70 = 2 bottles + 0.70*700ml = 2 bottles + 490ml
syrup_data = [
    # Mixer Juices (SYRUPS subcategory)
    ('M0008', 'Mixer Lemon Juice 700ML', 700, Decimal('18.00'),
     Decimal('5.88')),
    ('M0009', 'Mixer Lime Juice 700ML', 700, Decimal('12.00'),
     Decimal('5.88')),
    
    # Monin Syrups and Purees
    ('M3', 'Monin Agave Syrup 700ml', 700, Decimal('2.70'),
     Decimal('9.98')),
    ('M0006', 'Monin Chocolate Cookie LTR', 1000, Decimal('2.20'),
     Decimal('9.33')),
    ('M13', 'Monin Coconut Syrup 700ML', 700, Decimal('15.70'),
     Decimal('9.15')),
    ('M04', 'Monin Elderflower Syrup 700ML', 700, Decimal('4.50'),
     Decimal('10.38')),
    ('M0014', 'Monin Ginger Syrup', 700, Decimal('8.40'),
     Decimal('10.25')),
    ('M2', 'Monin Passionfruit Puree Ltr', 1000, Decimal('6.50'),
     Decimal('15.37')),
    ('M03', 'Monin Passionfruit Syrup 700ML', 700, Decimal('13.40'),
     Decimal('9.15')),
    ('M05', 'Monin Pink Grapefruit 700ML', 700, Decimal('5.40'),
     Decimal('10.25')),
    ('M06', 'Monin Puree Coconut LTR', 1000, Decimal('0.00'),
     Decimal('14.64')),
    ('M1', 'Monin Strawberry Puree Ltr', 1000, Decimal('10.00'),
     Decimal('12.13')),
    ('M01', 'Monin Strawberry Syrup 700ml', 700, Decimal('6.00'),
     Decimal('10.31')),
    ('M5', 'Monin Strawberry Syrup 700ml', 700, Decimal('0.00'),
     Decimal('10.31')),
    ('M9', 'Monin Vanilla Syrup Ltr', 1000, Decimal('3.00'),
     Decimal('8.83')),
    ('M02', 'Monin Watermelon Syrup 700ML', 700, Decimal('5.10'),
     Decimal('8.95')),
]

print("=" * 80)
print("UPDATING MONIN SYRUPS - Complete Names and Stock Data")
print("=" * 80)

updated_count = 0
not_found = []

for sku, full_name, bottle_size_ml, bottles_decimal, unit_cost in syrup_data:
    try:
        # Find item by exact SKU
        try:
            item = StockItem.objects.get(sku=sku, category_id='M')
        except StockItem.DoesNotExist:
            not_found.append(sku)
            print(f"\n❌ NOT FOUND: {sku}")
            continue
        
        print(f"\n✓ Updating {item.sku}: {item.name}")
        print(f"  New name: {full_name}")
        
        # Split bottles_decimal into bottles + ml
        # Example: 2.70 bottles of 700ml = 2 bottles + 0.70*700ml = 490ml
        full_bottles = int(bottles_decimal)
        ml_fraction = bottles_decimal - full_bottles
        ml = int(ml_fraction * bottle_size_ml)
        
        print(f"  Stock: {bottles_decimal} = {full_bottles} btl + {ml}ml")
        print(f"  Bottle size: {bottle_size_ml}ml")
        print(f"  Unit cost: €{unit_cost}")
        
        # Update item
        item.name = full_name
        item.subcategory = 'SYRUPS'
        item.uom = Decimal(str(bottle_size_ml))  # bottle size in ml
        item.unit_cost = unit_cost
        item.current_full_units = Decimal(str(full_bottles))  # bottles
        item.current_partial_units = Decimal(str(ml))  # ml
        item.save()
        
        # Calculate servings
        servings = item.total_stock_in_servings
        print(f"  Total servings: {servings:.2f} (35ml each)")
        
        updated_count += 1
        
    except Exception as e:
        print(f"\n❌ ERROR with '{sku}': {e}")
        not_found.append(sku)

print("\n" + "=" * 80)
print(f"SUMMARY: Updated {updated_count} out of {len(syrup_data)} syrups")

if not_found:
    print(f"\n⚠️  Items not found or had errors:")
    for name in not_found:
        print(f"  - {name}")

print("\n✓ All Monin syrups have been updated!")
print("=" * 80)
