"""
Create Missing Items from Excel

This script creates the missing items that appear in Excel but not in database:
- Spirits: Sea Dog Rum, Dingle Whiskey, Tanquery 0.0%
- Wines: Various missing wines including MDC Prosecco, O&G wines, etc.
"""

import os
import sys
import django
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockPeriod, StockSnapshot, StockCategory
from hotel.models import Hotel


# Missing Spirits with their data from Excel
MISSING_SPIRITS = [
    {
        'sku': 'S_SEADOG',
        'name': 'Sea Dog Rum',
        'size': '70cl',
        'cost_price': Decimal('17.13'),
        'full': Decimal('3.00'),
        'partial': Decimal('0.90'),
        'value': Decimal('66.81')
    },
    {
        'sku': 'S_DINGLE_WHISKEY',
        'name': 'Dingle Whiskey',
        'size': '70cl',
        'cost_price': Decimal('37.50'),
        'full': Decimal('4.00'),
        'partial': Decimal('0.00'),
        'value': Decimal('150.00')
    },
    {
        'sku': 'S0638_00',
        'name': 'Tanquery 70cl 0.0%',
        'size': '70cl',
        'cost_price': Decimal('15.00'),
        'full': Decimal('5.00'),
        'partial': Decimal('0.30'),
        'value': Decimal('0.00')  # This seems to be a special case
    },
]

# Missing Wines with their data from Excel
MISSING_WINES = [
    {
        'sku': 'W_PACSAUD',
        'name': 'Pacsaud Bordeaux Superior',
        'size': '75cl',
        'cost_price': Decimal('0.00'),
        'full': Decimal('0.00'),
        'partial': Decimal('0.00'),
        'value': Decimal('0.00')
    },
    {
        'sku': 'W_PINOT_SNIPES',
        'name': 'Pinot Grigio Snipes',
        'size': '75cl',
        'cost_price': Decimal('0.00'),
        'full': Decimal('36.00'),
        'partial': Decimal('0.00'),
        'value': Decimal('0.00')
    },
    {
        'sku': 'W_PROSECCO_NA',
        'name': 'No Alcohol Prosecco',
        'size': '75cl',
        'cost_price': Decimal('0.00'),
        'full': Decimal('21.00'),
        'partial': Decimal('0.00'),
        'value': Decimal('0.00')
    },
    {
        'sku': 'W_MDC_PROSECCO',
        'name': 'MDC PROSECCO DOC TRE F 24X20CL',
        'size': '20cl',
        'cost_price': Decimal('3.23'),
        'full': Decimal('99.00'),
        'partial': Decimal('0.00'),
        'value': Decimal('319.77')
    },
    {
        'sku': 'W_OG_SHIRAZ_75',
        'name': 'O&G SHIRAZ 6X75CL',
        'size': '75cl',
        'cost_price': Decimal('8.50'),
        'full': Decimal('6.00'),
        'partial': Decimal('0.00'),
        'value': Decimal('51.00')
    },
    {
        'sku': 'W_OG_SHIRAZ_187',
        'name': 'O&G SHIRAZ 12X187ML',
        'size': '18cl',
        'cost_price': Decimal('0.00'),
        'full': Decimal('36.00'),
        'partial': Decimal('0.00'),
        'value': Decimal('0.00')
    },
    {
        'sku': 'W_OG_SAUV_187',
        'name': 'O&G SAUVIGNON BLANC 12X187ML',
        'size': '18cl',
        'cost_price': Decimal('3.00'),
        'full': Decimal('12.00'),
        'partial': Decimal('0.00'),
        'value': Decimal('36.00')
    },
]


def create_missing_items():
    """Create missing items and their snapshots"""
    
    hotel = Hotel.objects.first()
    period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)
    
    print("=" * 60)
    print("CREATING MISSING ITEMS")
    print("=" * 60)
    
    # Create missing Spirits
    print("\n🥃 Creating Missing Spirits...")
    spirits_category = StockCategory.objects.get(code='S')
    spirits_total = Decimal('0.00')
    
    for item_data in MISSING_SPIRITS:
        # Parse size
        size_str = item_data['size']
        if size_str == '70cl':
            size_value = Decimal('700')
            size_unit = 'ml'
            uom = Decimal('700') / Decimal('35')  # 70cl / 35ml per shot = 20 shots
        else:
            size_value = Decimal('1')
            size_unit = 'unit'
            uom = Decimal('1')
        
        # Create StockItem
        item, created = StockItem.objects.update_or_create(
            hotel=hotel,
            sku=item_data['sku'],
            defaults={
                'name': item_data['name'],
                'category': spirits_category,
                'size': item_data['size'],
                'size_value': size_value,
                'size_unit': size_unit,
                'uom': uom,
                'unit_cost': item_data['cost_price'],
                'current_full_units': item_data['full'],
                'current_partial_units': item_data['partial'],
            }
        )
        
        # Create Snapshot
        StockSnapshot.objects.update_or_create(
            hotel=hotel,
            item=item,
            period=period,
            defaults={
                'closing_full_units': item_data['full'],
                'closing_partial_units': item_data['partial'],
                'closing_stock_value': item_data['value'],
                'unit_cost': item_data['cost_price'],
                'cost_per_serving': item_data['cost_price'] / uom if uom > 0 else Decimal('0'),
            }
        )
        
        spirits_total += item_data['value']
        status = "✅ Created" if created else "✅ Updated"
        print(f"  {status}: {item_data['sku']} - {item_data['name']} = €{item_data['value']}")
    
    print(f"\n  📊 Missing Spirits Added: €{spirits_total:,.2f}")
    
    # Create missing Wines
    print("\n🍷 Creating Missing Wines...")
    wines_category = StockCategory.objects.get(code='W')
    wines_total = Decimal('0.00')
    
    for item_data in MISSING_WINES:
        # Parse size
        size_str = item_data['size']
        if size_str == '75cl':
            size_value = Decimal('750')
            size_unit = 'ml'
        elif size_str == '20cl':
            size_value = Decimal('200')
            size_unit = 'ml'
        elif size_str == '18cl':
            size_value = Decimal('180')
            size_unit = 'ml'
        else:
            size_value = Decimal('1')
            size_unit = 'unit'
        
        uom = Decimal('1.0')  # Wine sold by bottle
        
        # Create StockItem
        item, created = StockItem.objects.update_or_create(
            hotel=hotel,
            sku=item_data['sku'],
            defaults={
                'name': item_data['name'],
                'category': wines_category,
                'size': item_data['size'],
                'size_value': size_value,
                'size_unit': size_unit,
                'uom': uom,
                'unit_cost': item_data['cost_price'],
                'current_full_units': item_data['full'],
                'current_partial_units': item_data['partial'],
            }
        )
        
        # Create Snapshot
        StockSnapshot.objects.update_or_create(
            hotel=hotel,
            item=item,
            period=period,
            defaults={
                'closing_full_units': item_data['full'],
                'closing_partial_units': item_data['partial'],
                'closing_stock_value': item_data['value'],
                'unit_cost': item_data['cost_price'],
                'cost_per_serving': item_data['cost_price'],
            }
        )
        
        wines_total += item_data['value']
        status = "✅ Created" if created else "✅ Updated"
        print(f"  {status}: {item_data['sku']} - {item_data['name']} = €{item_data['value']}")
    
    print(f"\n  📊 Missing Wines Added: €{wines_total:,.2f}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY OF MISSING ITEMS")
    print("=" * 60)
    print(f"\nSpirits Added: €{spirits_total:,.2f}")
    print(f"Wines Added:   €{wines_total:,.2f}")
    print(f"Total Added:   €{spirits_total + wines_total:,.2f}")
    
    # Calculate new grand total
    all_snapshots = StockSnapshot.objects.filter(hotel=hotel, period=period)
    grand_total = sum(s.closing_stock_value for s in all_snapshots)
    
    print(f"\n{'='*60}")
    print(f"NEW GRAND TOTAL: €{grand_total:,.2f}")
    print(f"Excel Total:     €27,306.51")
    print(f"Difference:      €{grand_total - Decimal('27306.51'):,.2f}")
    print(f"{'='*60}")
    
    excel_total = Decimal('27306.51')
    if abs(grand_total - excel_total) < Decimal('0.01'):
        print("\n🎉 SUCCESS! Database now matches Excel perfectly!")
    elif abs(grand_total - excel_total) < Decimal('1.00'):
        print("\n✅ SUCCESS! Database matches Excel (within €1)")
    else:
        print(f"\n⚠️  Remaining difference: €{abs(grand_total - excel_total):.2f}")


if __name__ == '__main__':
    create_missing_items()
