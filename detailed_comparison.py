"""
Detailed Item-by-Item Comparison Between Excel and Database
Identifies specific items causing the discrepancies
"""

import os
import sys
import django
from decimal import Decimal
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel


# Excel data parsed from user's spreadsheet
EXCEL_DATA = {
    # Draught Beers
    'D2133': {'name': '20 Heineken 00%', 'full': 0, 'partial': 40.00, 'value': 68.25},
    'D0007': {'name': '30 Beamish', 'full': 0, 'partial': 79.00, 'value': 137.25},
    'D0004': {'name': '30 Coors', 'full': 0, 'partial': 0, 'value': 0},
    'D0030': {'name': '30 Heineken', 'full': 0, 'partial': 0, 'value': 0},
    'D0012': {'name': '30 Killarney Blonde', 'full': 0, 'partial': 0, 'value': 0},
    'D0011': {'name': '30 Lagunitas IPA', 'full': 0, 'partial': 5.00, 'value': 13.60},
    'D2354': {'name': '30 Moretti', 'full': 0, 'partial': 304.00, 'value': 763.73},
    'D1003': {'name': '30 Murphys', 'full': 0, 'partial': 198.00, 'value': 419.69},
    'D0008': {'name': '30 Murphys Red', 'full': 0, 'partial': 26.50, 'value': 57.34},
    'D1022': {'name': '30 Orchards', 'full': 0, 'partial': 296.00, 'value': 652.04},
    'D0006': {'name': '30 OT Wild Orchard', 'full': 0, 'partial': 93.00, 'value': 204.86},
    'D1258': {'name': '50 Coors', 'full': 6, 'partial': 39.75, 'value': 1265.44},
    'D0005': {'name': '50 Guinness', 'full': 0, 'partial': 246.00, 'value': 521.38},
    'D1004': {'name': '50 Heineken', 'full': 0, 'partial': 542.00, 'value': 1208.04},
}


def compare_draught_beers():
    """Compare each draught beer item"""
    print("\n" + "=" * 100)
    print("DRAUGHT BEERS - ITEM BY ITEM COMPARISON")
    print("=" * 100)
    
    hotel = Hotel.objects.first()
    period = StockPeriod.objects.filter(hotel=hotel, year=2024, month=10).first()
    
    snapshots = StockSnapshot.objects.filter(
        hotel=hotel,
        period=period,
        item__category_id='D'
    ).select_related('item')
    
    # Create lookup
    db_lookup = {s.item.sku: s for s in snapshots}
    
    print(f"\n{'SKU':<15} {'Name':<30} {'Excel Full':<12} {'DB Full':<12} {'Excel Part':<12} {'DB Part':<12} {'Excel Value':<12} {'DB Value':<12} {'Diff'}")
    print("-" * 140)
    
    total_diff = Decimal('0.00')
    
    for sku, excel_data in EXCEL_DATA.items():
        db_snapshot = db_lookup.get(sku)
        
        if db_snapshot:
            db_full = db_snapshot.closing_full_units
            db_partial = db_snapshot.closing_partial_units
            db_value = db_snapshot.closing_stock_value
        else:
            db_full = Decimal('0')
            db_partial = Decimal('0')
            db_value = Decimal('0')
        
        excel_full = Decimal(str(excel_data['full']))
        excel_partial = Decimal(str(excel_data['partial']))
        excel_value = Decimal(str(excel_data['value']))
        
        diff = excel_value - db_value
        total_diff += diff
        
        status = "✅" if abs(diff) < Decimal('0.01') else "❌"
        
        print(
            f"{sku:<15} {excel_data['name'][:28]:<30} "
            f"{excel_full:>11.2f} {db_full:>11.2f} "
            f"{excel_partial:>11.2f} {db_partial:>11.2f} "
            f"€{excel_value:>10.2f} €{db_value:>10.2f} "
            f"€{diff:>10.2f} {status}"
        )
    
    print("-" * 140)
    print(f"{'TOTAL DIFFERENCE':<115} €{total_diff:>10.2f}")
    
    # Check for items in DB but not in Excel
    print("\n\nItems in DATABASE but NOT in Excel:")
    for sku, snapshot in db_lookup.items():
        if sku not in EXCEL_DATA:
            print(f"  {sku}: {snapshot.item.name} - €{snapshot.closing_stock_value:.2f}")


def analyze_specific_items():
    """Analyze specific problematic items"""
    hotel = Hotel.objects.first()
    period = StockPeriod.objects.filter(hotel=hotel, year=2024, month=10).first()
    
    # Check specific items
    items_to_check = [
        'D2133',  # 20 Heineken 00% - Excel: €68.25, DB shows €0
        'D0007',  # 30 Beamish - Excel: €137.25, DB: €30.69
        'D0004',  # 30 Coors - Excel: €0, DB: €411.95
        'D0030',  # 30 Heineken - Excel: €0, DB: €980.70
        'D2354',  # 30 Moretti - Excel: €763.73, DB: €299.59
    ]
    
    print("\n" + "=" * 100)
    print("SPECIFIC ITEM ANALYSIS - MAJOR DISCREPANCIES")
    print("=" * 100)
    
    for sku in items_to_check:
        snapshot = StockSnapshot.objects.filter(
            hotel=hotel,
            period=period,
            item__sku=sku
        ).select_related('item').first()
        
        if snapshot:
            excel = EXCEL_DATA.get(sku, {})
            
            print(f"\n{sku}: {snapshot.item.name}")
            print(f"  Category: {snapshot.item.category_id}")
            print(f"  Size: {snapshot.item.size} (Value: {snapshot.item.size_value} {snapshot.item.size_unit})")
            print(f"  UOM: {snapshot.item.uom}")
            print(f"  Unit Cost: €{snapshot.unit_cost:.4f}")
            print(f"  Cost per Serving: €{snapshot.cost_per_serving:.4f}")
            print(f"\n  EXCEL:")
            print(f"    Full Units: {excel.get('full', 'N/A')}")
            print(f"    Partial Units: {excel.get('partial', 'N/A')}")
            print(f"    Stock Value: €{excel.get('value', 'N/A')}")
            print(f"\n  DATABASE:")
            print(f"    Full Units: {snapshot.closing_full_units}")
            print(f"    Partial Units: {snapshot.closing_partial_units}")
            print(f"    Stock Value: €{snapshot.closing_stock_value:.2f}")
            
            # Calculate what the DB value should be based on Excel quantities
            if excel:
                excel_full = Decimal(str(excel['full']))
                excel_partial = Decimal(str(excel['partial']))
                
                # Calculate total servings using the model's logic
                if snapshot.item.category_id == 'D':
                    total_servings = (excel_full * snapshot.item.uom) + excel_partial
                    calculated_value = total_servings * snapshot.cost_per_serving
                    
                    print(f"\n  CALCULATION CHECK:")
                    print(f"    Excel Full: {excel_full} kegs × {snapshot.item.uom} pints = {excel_full * snapshot.item.uom} pints")
                    print(f"    Excel Partial: {excel_partial} pints")
                    print(f"    Total Servings: {total_servings} pints")
                    print(f"    Value (servings × cost): {total_servings} × €{snapshot.cost_per_serving:.4f} = €{calculated_value:.2f}")
                    print(f"    Excel Value: €{excel.get('value', 0)}")
                    print(f"    Difference: €{Decimal(str(excel.get('value', 0))) - calculated_value:.2f}")
            
            print("-" * 100)


def main():
    print("=" * 100)
    print("DETAILED OCTOBER 2024 STOCK COMPARISON")
    print("=" * 100)
    
    compare_draught_beers()
    analyze_specific_items()


if __name__ == '__main__':
    main()
