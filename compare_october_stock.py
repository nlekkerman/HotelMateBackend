"""
Compare Excel October 2024 Stock Data with Database

This script compares the Excel data provided by the user with the current
database calculations to identify discrepancies.
"""

import os
import sys
import django
from decimal import Decimal
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from hotel.models import Hotel


def get_database_totals():
    """Get totals from database for October 2024"""
    hotel = Hotel.objects.first()
    
    # Find October 2024 period
    period = StockPeriod.objects.filter(
        hotel=hotel,
        year=2024,
        month=10
    ).first()
    
    if not period:
        print("❌ October 2024 period not found in database!")
        return None
    
    print(f"✅ Found period: {period.period_name} (ID: {period.id})")
    print(f"   Date range: {period.start_date} to {period.end_date}")
    print(f"   Status: {'Closed' if period.is_closed else 'Open'}\n")
    
    # Get all snapshots
    snapshots = StockSnapshot.objects.filter(
        hotel=hotel,
        period=period
    ).select_related('item', 'item__category')
    
    # Calculate totals by category
    totals = {
        'D': Decimal('0.00'),  # Draught Beers
        'B': Decimal('0.00'),  # Bottled Beers
        'S': Decimal('0.00'),  # Spirits
        'M': Decimal('0.00'),  # Minerals/Syrups
        'W': Decimal('0.00'),  # Wine
    }
    
    item_details = {
        'D': [],
        'B': [],
        'S': [],
        'M': [],
        'W': []
    }
    
    for snapshot in snapshots:
        category = snapshot.item.category_id
        value = snapshot.closing_stock_value
        
        totals[category] += value
        
        item_details[category].append({
            'sku': snapshot.item.sku,
            'name': snapshot.item.name,
            'full': snapshot.closing_full_units,
            'partial': snapshot.closing_partial_units,
            'value': value,
            'unit_cost': snapshot.unit_cost,
            'uom': snapshot.item.uom
        })
    
    return {
        'period': period,
        'totals': totals,
        'items': item_details,
        'snapshots_count': snapshots.count()
    }


def print_comparison():
    """Print detailed comparison between Excel and Database"""
    
    # Excel totals from user's data
    excel_totals = {
        'D': Decimal('5311.62'),   # Draught Beers
        'B': Decimal('2288.46'),   # Bottled Beers
        'S': Decimal('11063.66'),  # Spirits
        'M': Decimal('3062.43'),   # Minerals/Syrups
        'W': Decimal('5580.35'),   # Wine
    }
    
    # Database totals (calculated from user's summary)
    database_totals = {
        'D': Decimal('5303.15'),
        'B': Decimal('3079.04'),
        'S': Decimal('10406.35'),
        'M': Decimal('4185.61'),
        'W': Decimal('4466.13'),
    }
    
    category_names = {
        'D': 'Draught Beers',
        'B': 'Bottled Beers',
        'S': 'Spirits',
        'M': 'Minerals/Syrups',
        'W': 'Wine'
    }
    
    print("=" * 80)
    print("COMPARISON: EXCEL vs DATABASE")
    print("=" * 80)
    print()
    
    total_excel = Decimal('0.00')
    total_db = Decimal('0.00')
    total_diff = Decimal('0.00')
    
    print(f"{'Category':<20} {'Excel':<15} {'Database':<15} {'Difference':<15} {'Status'}")
    print("-" * 80)
    
    for code in ['D', 'B', 'S', 'M', 'W']:
        excel = excel_totals[code]
        db = database_totals[code]
        diff = excel - db
        
        total_excel += excel
        total_db += db
        total_diff += diff
        
        status = "✅ Match" if abs(diff) < Decimal('0.01') else "❌ DIFF"
        
        print(f"{category_names[code]:<20} €{excel:>12,.2f} €{db:>12,.2f} €{diff:>12,.2f} {status}")
    
    print("-" * 80)
    print(f"{'TOTAL':<20} €{total_excel:>12,.2f} €{total_db:>12,.2f} €{total_diff:>12,.2f}")
    print("=" * 80)
    print()
    
    # Now fetch actual database data to verify
    print("\n📊 Fetching actual database data...\n")
    db_data = get_database_totals()
    
    if db_data:
        print("\n" + "=" * 80)
        print("ACTUAL DATABASE TOTALS")
        print("=" * 80)
        print()
        
        for code in ['D', 'B', 'S', 'M', 'W']:
            actual_db = db_data['totals'][code]
            excel = excel_totals[code]
            diff = excel - actual_db
            
            status = "✅" if abs(diff) < Decimal('0.01') else "❌"
            
            print(f"{category_names[code]:<20} €{actual_db:>12,.2f} (Excel: €{excel:>12,.2f}, Diff: €{diff:>12,.2f}) {status}")
        
        actual_total = sum(db_data['totals'].values())
        print(f"\n{'TOTAL':<20} €{actual_total:>12,.2f}")
        print(f"{'Snapshots Count':<20} {db_data['snapshots_count']}")


def analyze_spirits_discrepancy():
    """Deep dive into Spirits category to find discrepancies"""
    print("\n" + "=" * 80)
    print("SPIRITS CATEGORY - DETAILED ANALYSIS")
    print("=" * 80)
    
    hotel = Hotel.objects.first()
    period = StockPeriod.objects.filter(hotel=hotel, year=2024, month=10).first()
    
    if not period:
        print("❌ Period not found")
        return
    
    # Get all spirits snapshots
    snapshots = StockSnapshot.objects.filter(
        hotel=hotel,
        period=period,
        item__category_id='S'
    ).select_related('item').order_by('item__sku')
    
    print(f"\nTotal Spirits Items: {snapshots.count()}")
    print(f"\nShowing items with significant stock value (>€10.00):\n")
    
    total_value = Decimal('0.00')
    
    print(f"{'SKU':<25} {'Name':<40} {'Full':<8} {'Partial':<10} {'Value':<12}")
    print("-" * 100)
    
    for snapshot in snapshots:
        if snapshot.closing_stock_value > 10:
            print(
                f"{snapshot.item.sku:<25} "
                f"{snapshot.item.name[:38]:<40} "
                f"{snapshot.closing_full_units:>7.2f} "
                f"{snapshot.closing_partial_units:>9.4f} "
                f"€{snapshot.closing_stock_value:>10.2f}"
            )
        total_value += snapshot.closing_stock_value
    
    print("-" * 100)
    print(f"{'TOTAL':<75} €{total_value:>10.2f}")
    print(f"\nExpected from Excel: €11,063.66")
    print(f"Difference: €{Decimal('11063.66') - total_value:,.2f}")


def analyze_category(category_code, category_name, excel_total):
    """Analyze a specific category in detail"""
    print("\n" + "=" * 80)
    print(f"{category_name.upper()} - DETAILED ANALYSIS")
    print("=" * 80)
    
    hotel = Hotel.objects.first()
    period = StockPeriod.objects.filter(hotel=hotel, year=2024, month=10).first()
    
    if not period:
        print("❌ Period not found")
        return
    
    snapshots = StockSnapshot.objects.filter(
        hotel=hotel,
        period=period,
        item__category_id=category_code
    ).select_related('item').order_by('item__sku')
    
    print(f"\nTotal Items: {snapshots.count()}")
    print(f"\nTop 20 items by value:\n")
    
    # Get top 20 by value
    top_items = sorted(snapshots, key=lambda s: s.closing_stock_value, reverse=True)[:20]
    
    total_value = Decimal('0.00')
    
    print(f"{'SKU':<25} {'Name':<35} {'Full':<8} {'Partial':<10} {'Value':<12}")
    print("-" * 95)
    
    for snapshot in top_items:
        print(
            f"{snapshot.item.sku:<25} "
            f"{snapshot.item.name[:33]:<35} "
            f"{snapshot.closing_full_units:>7.2f} "
            f"{snapshot.closing_partial_units:>9.2f} "
            f"€{snapshot.closing_stock_value:>10.2f}"
        )
    
    # Calculate total for all items
    for snapshot in snapshots:
        total_value += snapshot.closing_stock_value
    
    print("-" * 95)
    print(f"{'TOTAL (all items)':<80} €{total_value:>10.2f}")
    print(f"Expected from Excel: €{excel_total:,.2f}")
    diff = excel_total - total_value
    print(f"Difference: €{diff:,.2f} {'✅' if abs(diff) < 1 else '❌'}")


def main():
    print("=" * 80)
    print("OCTOBER 2024 STOCK COMPARISON ANALYSIS")
    print("=" * 80)
    print()
    
    # Overall comparison
    print_comparison()
    
    # Detailed analysis for each category with significant differences
    print("\n\n")
    analyze_category('B', 'Bottled Beers', Decimal('2288.46'))
    
    print("\n\n")
    analyze_category('S', 'Spirits', Decimal('11063.66'))
    
    print("\n\n")
    analyze_category('M', 'Minerals/Syrups', Decimal('3062.43'))
    
    print("\n\n")
    analyze_category('W', 'Wine', Decimal('5580.35'))
    
    print("\n\n")
    analyze_category('D', 'Draught Beers', Decimal('5311.62'))


if __name__ == '__main__':
    main()
