"""
Update October 2024 Stock to Match Excel EXACTLY

This script updates the database to match the Excel spreadsheet you provided.
Uses the exact values from Excel: Stock at Cost, Full Units, Partial Units
"""

import os
import sys
import django
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from hotel.models import Hotel


# EXACT DATA FROM YOUR EXCEL SPREADSHEET - Date 31-10-25
EXCEL_DRAUGHT = [
    {'sku': 'D2133', 'name': '20 Heineken 00%', 'full': Decimal('0.00'), 
     'partial': Decimal('40.00'), 'value': Decimal('68.25')},
    {'sku': 'D0007', 'name': '30 Beamish', 'full': Decimal('0.00'), 
     'partial': Decimal('79.00'), 'value': Decimal('137.25')},
    {'sku': 'D1004', 'name': '30 Coors', 'full': Decimal('0.00'), 
     'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'D0004', 'name': '30 Heineken', 'full': Decimal('0.00'), 
     'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'D0012', 'name': '30 Killarney Blonde', 'full': Decimal('0.00'), 
     'partial': Decimal('0.00'), 'value': Decimal('0.00')},
    {'sku': 'D0011', 'name': '30 Lagunitas IPA', 'full': Decimal('0.00'), 
     'partial': Decimal('5.00'), 'value': Decimal('13.60')},
    {'sku': 'D2354', 'name': '30 Moretti', 'full': Decimal('0.00'), 
     'partial': Decimal('304.00'), 'value': Decimal('763.73')},
    {'sku': 'D1003', 'name': '30 Murphys', 'full': Decimal('0.00'), 
     'partial': Decimal('198.00'), 'value': Decimal('419.69')},
    {'sku': 'D0008', 'name': '30 Murphys Red', 'full': Decimal('0.00'), 
     'partial': Decimal('26.50'), 'value': Decimal('57.34')},
    {'sku': 'D1022', 'name': '30 Orchards', 'full': Decimal('0.00'), 
     'partial': Decimal('296.00'), 'value': Decimal('652.04')},
    {'sku': 'D0006', 'name': '30 OT Wild Orchard', 'full': Decimal('0.00'), 
     'partial': Decimal('93.00'), 'value': Decimal('204.86')},
    {'sku': 'D1258', 'name': '50 Coors', 'full': Decimal('6.00'), 
     'partial': Decimal('39.75'), 'value': Decimal('1265.44')},
    {'sku': 'D0005', 'name': '50 Guinness', 'full': Decimal('0.00'), 
     'partial': Decimal('246.00'), 'value': Decimal('521.38')},
    {'sku': 'D0030', 'name': '50 Heineken', 'full': Decimal('0.00'), 
     'partial': Decimal('542.00'), 'value': Decimal('1208.04')},
]


def update_october_stock():
    """Update all snapshots to match Excel exactly"""
    
    hotel = Hotel.objects.first()
    period = StockPeriod.objects.filter(hotel=hotel, year=2024, month=10).first()
    
    if not period:
        print("❌ October 2024 period not found!")
        return
    
    print("=" * 80)
    print("UPDATING OCTOBER 2024 TO MATCH EXCEL EXACTLY")
    print("=" * 80)
    print()
    
    # Update Draught Beers
    print("🍺 Updating Draught Beers...")
    draught_total = Decimal('0.00')
    
    for item_data in EXCEL_DRAUGHT:
        item = StockItem.objects.filter(
            hotel=hotel, 
            sku=item_data['sku']
        ).first()
        
        if not item:
            print(f"  ⚠️  {item_data['sku']} not found, skipping...")
            continue
        
        snapshot, created = StockSnapshot.objects.update_or_create(
            hotel=hotel,
            item=item,
            period=period,
            defaults={
                'closing_full_units': item_data['full'],
                'closing_partial_units': item_data['partial'],
                'unit_cost': item.unit_cost,
                'cost_per_serving': item.cost_per_serving,
                'closing_stock_value': item_data['value'],
            }
        )
        
        draught_total += item_data['value']
        action = "Created" if created else "Updated"
        print(f"  ✅ {action}: {item_data['sku']} = €{item_data['value']:.2f}")
    
    print(f"\n  📊 Draught Total: €{draught_total:.2f}")
    print(f"  📋 Excel Expected: €5,311.62")
    print(f"  🔍 Difference: €{Decimal('5311.62') - draught_total:.2f}\n")
    
    # Verify all categories
    print("\n" + "=" * 80)
    print("VERIFYING ALL CATEGORIES")
    print("=" * 80)
    
    categories = {
        'D': {'name': 'Draught Beers', 'excel': Decimal('5311.62')},
        'B': {'name': 'Bottled Beers', 'excel': Decimal('2288.46')},
        'S': {'name': 'Spirits', 'excel': Decimal('11063.66')},
        'M': {'name': 'Minerals/Syrups', 'excel': Decimal('3062.43')},
        'W': {'name': 'Wine', 'excel': Decimal('5580.35')},
    }
    
    grand_total = Decimal('0.00')
    
    for code, info in categories.items():
        snapshots = StockSnapshot.objects.filter(
            hotel=hotel,
            period=period,
            item__category_id=code
        )
        
        db_total = sum(s.closing_stock_value for s in snapshots)
        diff = info['excel'] - db_total
        grand_total += db_total
        
        status = "✅" if abs(diff) < Decimal('1.00') else "❌"
        
        print(f"\n{info['name']}:")
        print(f"  Database: €{db_total:,.2f}")
        print(f"  Excel:    €{info['excel']:,.2f}")
        print(f"  Diff:     €{diff:,.2f} {status}")
    
    print("\n" + "=" * 80)
    print(f"GRAND TOTAL: €{grand_total:,.2f}")
    print(f"Excel Total: €27,306.51")
    print(f"Difference:  €{Decimal('27306.51') - grand_total:,.2f}")
    print("=" * 80)


if __name__ == '__main__':
    update_october_stock()
