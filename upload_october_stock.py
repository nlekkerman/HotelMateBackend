"""
Upload October 2024 Stock Data from JSON files

This script parses the JSON files and creates:
1. StockCategory entries (D, B, S, W, M)
2. StockItem entries with proper calculations
3. October 2024 StockPeriod
4. StockSnapshot entries for each item

Run from project root:
    python scripts/upload_october_stock.py
"""

import os
import sys
import django
import json
from decimal import Decimal
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockCategory, StockItem, StockPeriod, StockSnapshot
)
from hotel.models import Hotel
from datetime import date


# Category mappings from SKU prefix
CATEGORY_MAP = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer',
    'S': 'Spirits',
    'W': 'Wine',
    'M': 'Minerals & Syrups'
}


def parse_decimal(value, default=Decimal('0.00')):
    """Safely parse a value to Decimal"""
    if value is None or value == '':
        return default
    
    # Remove currency symbols
    if isinstance(value, str):
        value = value.replace('€', '').replace('£', '').strip()
    
    try:
        return Decimal(str(value))
    except:
        return default


def parse_size(size_str):
    """
    Parse size string into value and unit
    Examples:
        "70cl" -> (700, "ml")
        "50Lt" -> (50, "L")
        "Doz" -> (12, "bottles")
        "Ind" -> (1, "unit")
    """
    if not size_str:
        return Decimal('1'), 'unit'
    
    size_str = size_str.strip()
    
    # Handle special cases
    if size_str.lower() == 'doz':
        return Decimal('12'), 'bottles'
    if size_str.lower() == 'ind':
        return Decimal('1'), 'unit'
    
    # Extract number and unit
    import re
    match = re.match(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', size_str)
    
    if match:
        value = Decimal(match.group(1))
        unit = match.group(2).lower()
        
        # Convert cl to ml
        if unit == 'cl':
            return value * 10, 'ml'
        # Standardize liters
        elif unit in ['lt', 'ltr', 'litre', 'liter']:
            return value, 'L'
        else:
            return value, unit
    
    return Decimal('1'), 'unit'


def calculate_uom_for_draught(size_value, size_unit):
    """
    Calculate pints per keg for draught beer
    1 pint = 0.568 liters = 568ml
    """
    # Convert to liters
    if size_unit == 'L':
        liters = size_value
    else:
        return Decimal('35')  # Default fallback
    
    # Calculate pints
    pints = liters / Decimal('0.568')
    return pints.quantize(Decimal('0.01'))


def calculate_uom_for_spirits(size_value, size_unit):
    """
    Calculate shots per bottle for spirits
    Standard shot = 35ml (can be 25ml in some cases)
    """
    # Convert to ml
    if size_unit == 'ml':
        ml = size_value
    elif size_unit == 'L':
        ml = size_value * 1000
    else:
        return Decimal('20')  # Default fallback
    
    # Calculate 35ml shots
    shots = ml / Decimal('35')
    return shots.quantize(Decimal('0.1'))


def calculate_uom_for_wine(size_value, size_unit):
    """
    Calculate glasses per bottle for wine
    Standard glass = 175ml (can vary: 125ml, 175ml, 250ml)
    """
    # Convert to ml
    if size_unit == 'ml':
        ml = size_value
    elif size_unit == 'L':
        ml = size_value * 1000
    else:
        return Decimal('1')  # Sold by bottle
    
    # Calculate 175ml glasses
    glasses = ml / Decimal('175')
    return glasses.quantize(Decimal('0.1'))


def calculate_uom(category_code, size_value, size_unit, uom_from_json):
    """
    Calculate UOM based on category type
    
    For Draught (D): Calculate pints per keg
    For Bottled (B): Use 12 (dozen)
    For Spirits (S): Calculate shots per bottle
    For Wine (W): Calculate glasses per bottle or use 1
    For Minerals (M): Use value from JSON or default to 12 for dozens
    """
    if category_code == 'D':
        # Draught: calculate pints per keg
        return calculate_uom_for_draught(size_value, size_unit)
    
    elif category_code == 'B':
        # Bottled Beer: dozen = 12 bottles
        return Decimal('12')
    
    elif category_code == 'S':
        # Spirits: calculate shots per bottle
        return calculate_uom_for_spirits(size_value, size_unit)
    
    elif category_code == 'W':
        # Wine: calculate glasses per bottle, or 1 if sold by bottle
        if size_value >= 500:  # 750ml bottles
            return calculate_uom_for_wine(size_value, size_unit)
        else:
            return Decimal('1')  # Small bottles sold as single units
    
    elif category_code == 'M':
        # Minerals: use JSON value or default
        uom = parse_decimal(uom_from_json, Decimal('12'))
        return uom
    
    return Decimal('1')


def process_bottled_beers(file_path, hotel, period):
    """Process bottledbeers.json"""
    print("\n📦 Processing Bottled Beers...")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    category = StockCategory.objects.get(code='B')
    count = 0
    
    for item_data in data:
        sku = item_data.get('sku')
        if not sku:
            continue
        
        name = item_data['name']
        size = item_data['size']
        size_value, size_unit = parse_size(size)
        
        # UOM is always 12 for bottled beers (dozen)
        uom = Decimal('12')
        
        # Cost price per dozen
        unit_cost = parse_decimal(item_data['cost_price'])
        
        # Stock quantities
        closing_cases = parse_decimal(item_data.get('closing_stock_cases'), Decimal('0'))
        closing_bottles = parse_decimal(item_data.get('closing_stock_bottles'), Decimal('0'))
        
        # Create/Update StockItem
        stock_item, created = StockItem.objects.update_or_create(
            hotel=hotel,
            sku=sku,
            defaults={
                'name': name,
                'category': category,
                'size': size,
                'size_value': size_value,
                'size_unit': size_unit,
                'uom': uom,
                'unit_cost': unit_cost,
                'current_full_units': closing_cases,
                'current_partial_units': closing_bottles,
            }
        )
        
        # Create Snapshot for October
        closing_value = parse_decimal(item_data.get('stock_at_cost'))
        
        StockSnapshot.objects.update_or_create(
            hotel=hotel,
            item=stock_item,
            period=period,
            defaults={
                'closing_full_units': closing_cases,
                'closing_partial_units': closing_bottles,
                'unit_cost': unit_cost,
                'cost_per_serving': unit_cost / uom,
                'closing_stock_value': closing_value,
            }
        )
        
        count += 1
        print(f"  ✓ {sku}: {name}")
    
    print(f"✅ Imported {count} bottled beers")


def process_draught_beers(file_path, hotel, period):
    """Process draughtbeers.json"""
    print("\n🍺 Processing Draught Beers...")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    category = StockCategory.objects.get(code='D')
    count = 0
    
    for item_data in data:
        sku = item_data.get('sku')
        if not sku:
            continue
        
        name = item_data['name']
        size = item_data['size']
        size_value, size_unit = parse_size(size)
        
        # Calculate pints per keg
        uom = calculate_uom_for_draught(size_value, size_unit)
        
        # Cost price per keg
        unit_cost = parse_decimal(item_data['cost_price'])
        
        # Stock quantities
        closing_kegs = parse_decimal(item_data.get('closing_stock_full_kegs'), Decimal('0'))
        closing_pints = parse_decimal(item_data.get('closing_stock_pints'), Decimal('0'))
        
        # Create/Update StockItem
        stock_item, created = StockItem.objects.update_or_create(
            hotel=hotel,
            sku=sku,
            defaults={
                'name': name,
                'category': category,
                'size': size,
                'size_value': size_value,
                'size_unit': size_unit,
                'uom': uom,
                'unit_cost': unit_cost,
                'current_full_units': closing_kegs,
                'current_partial_units': closing_pints,
            }
        )
        
        # Create Snapshot for October
        closing_value = parse_decimal(item_data.get('stock_at_cost'))
        
        StockSnapshot.objects.update_or_create(
            hotel=hotel,
            item=stock_item,
            period=period,
            defaults={
                'closing_full_units': closing_kegs,
                'closing_partial_units': closing_pints,
                'unit_cost': unit_cost,
                'cost_per_serving': unit_cost / uom,
                'closing_stock_value': closing_value,
            }
        )
        
        count += 1
        print(f"  ✓ {sku}: {name} ({uom} pints/keg)")
    
    print(f"✅ Imported {count} draught beers")


def process_spirits(file_path, hotel, period):
    """Process spirits.json"""
    print("\n🥃 Processing Spirits...")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    category = StockCategory.objects.get(code='S')
    count = 0
    
    for item_data in data:
        sku = item_data.get('sku')
        if not sku:
            continue
        
        name = item_data['name']
        size = item_data['size']
        size_value, size_unit = parse_size(size)
        
        # Calculate shots per bottle
        uom = calculate_uom_for_spirits(size_value, size_unit)
        
        # Cost price per bottle
        unit_cost = parse_decimal(item_data['cost_price'])
        
        # Stock quantities
        closing_bottles = parse_decimal(item_data.get('closing_stock_bottles'), Decimal('0'))
        closing_partial = parse_decimal(item_data.get('closing_stock_individuals'), Decimal('0'))
        
        # Create/Update StockItem
        stock_item, created = StockItem.objects.update_or_create(
            hotel=hotel,
            sku=sku,
            defaults={
                'name': name,
                'category': category,
                'size': size,
                'size_value': size_value,
                'size_unit': size_unit,
                'uom': uom,
                'unit_cost': unit_cost,
                'current_full_units': closing_bottles,
                'current_partial_units': closing_partial,
            }
        )
        
        # Create Snapshot for October
        closing_value = parse_decimal(item_data.get('stock_at_cost'))
        
        StockSnapshot.objects.update_or_create(
            hotel=hotel,
            item=stock_item,
            period=period,
            defaults={
                'closing_full_units': closing_bottles,
                'closing_partial_units': closing_partial,
                'unit_cost': unit_cost,
                'cost_per_serving': unit_cost / uom if uom > 0 else Decimal('0'),
                'closing_stock_value': closing_value,
            }
        )
        
        count += 1
        print(f"  ✓ {sku}: {name} ({uom} shots/bottle)")
    
    print(f"✅ Imported {count} spirits")


def process_wines(file_path, hotel, period):
    """Process wines.json"""
    print("\n🍷 Processing Wines...")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    category = StockCategory.objects.get(code='W')
    count = 0
    
    for item_data in data:
        sku = item_data.get('sku')
        if not sku or sku.strip() == '':
            continue
        
        name = item_data['name']
        size = item_data.get('size', 'Ind')
        size_value, size_unit = parse_size(size)
        
        # Wine: UOM = 1.0 (sold by bottle, not by glass)
        uom = Decimal('1.0')
        
        # Cost price per bottle
        unit_cost = parse_decimal(item_data.get('cost_price'))
        
        # Stock quantities - wines track bottles (can have decimals)
        # Example: 3.80 bottles = 3 full + 0.80 partial
        closing_bottles_total = parse_decimal(item_data.get('closing_stock_bottles'), Decimal('0'))
        
        # Split into full and partial bottles
        closing_full = int(closing_bottles_total)  # Whole bottles
        closing_partial = closing_bottles_total - Decimal(closing_full)  # Fractional part
        
        # Create/Update StockItem
        stock_item, created = StockItem.objects.update_or_create(
            hotel=hotel,
            sku=sku,
            defaults={
                'name': name,
                'category': category,
                'size': size,
                'size_value': size_value,
                'size_unit': size_unit,
                'uom': uom,
                'unit_cost': unit_cost,
                'current_full_units': Decimal(closing_full),
                'current_partial_units': closing_partial,
            }
        )
        
        # Create Snapshot for October
        closing_value = parse_decimal(item_data.get('stock_at_cost'))
        
        StockSnapshot.objects.update_or_create(
            hotel=hotel,
            item=stock_item,
            period=period,
            defaults={
                'closing_full_units': Decimal(closing_full),
                'closing_partial_units': closing_partial,
                'unit_cost': unit_cost,
                'cost_per_serving': unit_cost,  # Cost per bottle
                'closing_stock_value': closing_value,
            }
        )
        
        count += 1
        print(f"  ✓ {sku}: {name}")
    
    print(f"✅ Imported {count} wines")


def process_minerals_syrups(file_path, hotel, period):
    """Process mineralsandsyrups.json"""
    print("\n🥤 Processing Minerals & Syrups...")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    category = StockCategory.objects.get(code='M')
    count = 0
    
    for item_data in data:
        sku = item_data.get('sku')
        if not sku:
            continue
        
        name = item_data['name']
        size = item_data['size']
        size_value, size_unit = parse_size(size)
        
        # UOM varies for minerals - use from JSON
        uom_json = parse_decimal(item_data.get('uom'), Decimal('12'))
        uom = uom_json
        
        # Cost price per unit
        unit_cost = parse_decimal(item_data['cost_price'])
        
        # Stock quantities
        closing_cases = parse_decimal(item_data.get('closing_stock_cases'), Decimal('0'))
        closing_bottles = parse_decimal(item_data.get('closing_stock_bottles'), Decimal('0'))
        
        # Create/Update StockItem
        stock_item, created = StockItem.objects.update_or_create(
            hotel=hotel,
            sku=sku,
            defaults={
                'name': name,
                'category': category,
                'size': size,
                'size_value': size_value,
                'size_unit': size_unit,
                'uom': uom,
                'unit_cost': unit_cost,
                'current_full_units': closing_cases,
                'current_partial_units': closing_bottles,
            }
        )
        
        # Create Snapshot for October
        closing_value = parse_decimal(item_data.get('stock_at_cost'))
        
        StockSnapshot.objects.update_or_create(
            hotel=hotel,
            item=stock_item,
            period=period,
            defaults={
                'closing_full_units': closing_cases,
                'closing_partial_units': closing_bottles,
                'unit_cost': unit_cost,
                'cost_per_serving': unit_cost / uom if uom > 0 else Decimal('0'),
                'closing_stock_value': closing_value,
            }
        )
        
        count += 1
        print(f"  ✓ {sku}: {name}")
    
    print(f"✅ Imported {count} minerals & syrups")


def main():
    """Main execution"""
    print("=" * 60)
    print("OCTOBER 2024 STOCK DATA UPLOAD")
    print("=" * 60)
    
    # Get hotel (adjust as needed)
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ No hotel found in database!")
            return
        print(f"\n🏨 Hotel: {hotel.name}")
    except Exception as e:
        print(f"❌ Error getting hotel: {e}")
        return
    
    # Create stock categories
    print("\n📁 Creating Stock Categories...")
    for code, name in CATEGORY_MAP.items():
        category, created = StockCategory.objects.get_or_create(
            code=code,
            defaults={'name': name}
        )
        status = "Created" if created else "Exists"
        print(f"  {status}: {code} - {name}")
    
    # Create October 2024 period
    print("\n📅 Creating October 2024 Period...")
    period, created = StockPeriod.create_monthly_period(hotel, 2024, 10)
    status = "Created" if created else "Already exists"
    print(f"  {status}: {period.period_name}")
    
    # Define JSON file paths (in HotelMateBackend/docs/)
    docs_dir = Path(__file__).parent / 'docs'
    
    json_files = {
        'bottledbeers': docs_dir / 'bottledbeers.json',
        'draughtbeers': docs_dir / 'draughtbeers.json',
        'spirits': docs_dir / 'spirits.json',
        'wines': docs_dir / 'wines.json',
        'minerals': docs_dir / 'mineralsandsyrups.json',
    }
    
    # Check all files exist
    for name, path in json_files.items():
        if not path.exists():
            print(f"❌ File not found: {path}")
            return
    
    # Process each file
    try:
        process_bottled_beers(json_files['bottledbeers'], hotel, period)
        process_draught_beers(json_files['draughtbeers'], hotel, period)
        process_spirits(json_files['spirits'], hotel, period)
        process_wines(json_files['wines'], hotel, period)
        process_minerals_syrups(json_files['minerals'], hotel, period)
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ UPLOAD COMPLETE!")
        print("=" * 60)
        
        total_items = StockItem.objects.filter(hotel=hotel).count()
        total_snapshots = StockSnapshot.objects.filter(hotel=hotel, period=period).count()
        total_value = sum(
            s.closing_stock_value for s in 
            StockSnapshot.objects.filter(hotel=hotel, period=period)
        )
        
        print(f"\n📊 Summary:")
        print(f"  Total Items: {total_items}")
        print(f"  Total Snapshots: {total_snapshots}")
        print(f"  Total Stock Value: €{total_value:,.2f}")
        print(f"  Period: {period.period_name}")
        print(f"  Date Range: {period.start_date} to {period.end_date}")
        
    except Exception as e:
        print(f"\n❌ Error during upload: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
