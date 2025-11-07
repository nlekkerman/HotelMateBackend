"""
Fix Draught Beer Stock - Convert Excel pints to proper full kegs + partial pints

The Excel shows total pints, but we need to split them into full kegs + partial pints.
Example: 542 pints in a 50L keg (88 pints) = 6 full kegs + 14 pints
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


# Excel data - showing TOTAL PINTS from your spreadsheet
# NOTE: Excel shows ALL stock as TOTAL PINTS in single column
EXCEL_DRAUGHT_DATA = {
    'D2133': {'name': '20 Heineken 00%', 'total_pints': Decimal('40.00'),
              'value': Decimal('68.25')},
    'D0007': {'name': '30 Beamish', 'total_pints': Decimal('79.00'),
              'value': Decimal('137.25')},
    'D1004': {'name': '30 Coors', 'total_pints': Decimal('0.00'),
              'value': Decimal('0.00')},
    # There is no "30 Heineken" - D0030 is "50 Heineken"
    'D0012': {'name': '30 Killarney Blonde', 'total_pints': Decimal('0.00'),
              'value': Decimal('0.00')},
    'D0011': {'name': '30 Lagunitas IPA', 'total_pints': Decimal('5.00'),
              'value': Decimal('13.60')},
    'D2354': {'name': '30 Moretti', 'total_pints': Decimal('304.00'),
              'value': Decimal('763.73')},
    'D1003': {'name': '30 Murphys', 'total_pints': Decimal('198.00'),
              'value': Decimal('419.69')},
    'D0008': {'name': '30 Murphys Red', 'total_pints': Decimal('26.50'),
              'value': Decimal('57.34')},
    'D1022': {'name': '30 Orchards', 'total_pints': Decimal('296.00'),
              'value': Decimal('652.04')},
    'D0006': {'name': '30 OT Wild Orchard', 'total_pints': Decimal('93.00'),
              'value': Decimal('204.86')},
    # 50L kegs = 88.03 pints per keg
    'D1258': {'name': '50 Coors', 'total_pints': Decimal('567.75'),
              'value': Decimal('1265.44')},
    'D0005': {'name': '50 Guinness', 'total_pints': Decimal('246.00'),
              'value': Decimal('521.38')},
    'D0030': {'name': '50 Heineken', 'total_pints': Decimal('542.00'),
              'value': Decimal('1208.04')},
}


def convert_pints_to_kegs_and_partial(total_pints, pints_per_keg):
    """
    Convert total pints to full kegs + partial pints
    
    Example: 542 pints, 88.03 pints/keg
    = 6 full kegs + 14.82 pints
    """
    if total_pints == 0:
        return Decimal('0'), Decimal('0')
    
    full_kegs = int(total_pints / pints_per_keg)
    partial_pints = total_pints - (Decimal(full_kegs) * pints_per_keg)
    
    return Decimal(full_kegs), partial_pints


def fix_draught_beer_stock():
    """Update all draught beer snapshots with correct values from Excel"""
    
    hotel = Hotel.objects.first()
    period = StockPeriod.objects.filter(hotel=hotel, year=2024, month=10).first()
    
    if not period:
        print("❌ October 2024 period not found!")
        return
    
    print("=" * 80)
    print("FIXING DRAUGHT BEER STOCK - CONVERTING EXCEL PINTS TO KEGS + PINTS")
    print("=" * 80)
    print()
    
    for sku, data in EXCEL_DRAUGHT_DATA.items():
        # Get the stock item
        item = StockItem.objects.filter(hotel=hotel, sku=sku).first()
        
        if not item:
            print(f"⚠️  {sku} not found in database, skipping...")
            continue
        
        # Get or create snapshot
        snapshot, created = StockSnapshot.objects.get_or_create(
            hotel=hotel,
            item=item,
            period=period,
            defaults={
                'unit_cost': item.unit_cost,
                'cost_per_serving': item.cost_per_serving,
            }
        )
        
        # Convert total pints to kegs + partial pints
        total_pints = data['total_pints']
        pints_per_keg = item.uom
        
        full_kegs, partial_pints = convert_pints_to_kegs_and_partial(total_pints, pints_per_keg)
        
        # Calculate value from Excel (use Excel value directly)
        excel_value = data['value']
        
        # Update snapshot
        snapshot.closing_full_units = full_kegs
        snapshot.closing_partial_units = partial_pints
        snapshot.closing_stock_value = excel_value
        snapshot.save()
        
        print(f"✅ {sku}: {data['name'][:30]:<30}")
        print(f"   Total Pints: {total_pints:>8.2f} → {full_kegs} kegs + {partial_pints:.2f} pints")
        print(f"   Value: €{excel_value:.2f}")
        print()
    
    # Calculate new total
    snapshots = StockSnapshot.objects.filter(
        hotel=hotel,
        period=period,
        item__category_id='D'
    )
    
    total_value = sum(s.closing_stock_value for s in snapshots)
    
    print("=" * 80)
    print(f"✅ DRAUGHT BEERS FIXED!")
    print(f"   New Total Value: €{total_value:,.2f}")
    print(f"   Excel Expected: €5,311.62")
    print(f"   Difference: €{Decimal('5311.62') - total_value:,.2f}")
    print("=" * 80)


if __name__ == '__main__':
    fix_draught_beer_stock()
