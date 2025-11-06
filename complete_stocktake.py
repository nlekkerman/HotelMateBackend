"""
Complete stocktake by matching MARKO Excel data to existing DB items
Run: python complete_stocktake.py --dry-run
Run: python complete_stocktake.py --update
"""
import os
import django
import pandas as pd
from decimal import Decimal
import argparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockItem, 
    Stocktake, 
    StocktakeLine,
    StockMovement
)
from hotel.models import Hotel
from django.utils import timezone

CSV_PATH = "marko_stock_cleaned.csv"


def parse_marko_csv():
    """Parse CSV and return all items with their counts"""
    df = pd.read_csv(CSV_PATH, skip_blank_lines=False)
    
    items = []
    for idx, row in df.iterrows():
        code = str(row.iloc[0])
        
        # Skip headers and totals
        if code in ['Code', 'nan', 'Total for'] or pd.isna(row.iloc[0]):
            continue
        
        if code.startswith(('D', 'B', 'S', 'M', 'W')):
            items.append({
                'code': code,
                'description': row.iloc[1],
                'size': row.iloc[2],
                'uom': row.iloc[3],
                'cost': row.iloc[4],
                'full_units': row.iloc[5] if pd.notna(row.iloc[5]) else 0,
                'partial_units': row.iloc[6] if pd.notna(row.iloc[6]) else 0,
                'value': row.iloc[7] if pd.notna(row.iloc[7]) else 0,
            })
    
    return items


def match_items(excel_items, db_items):
    """Match Excel items to database items"""
    matches = []
    unmatched_excel = []
    
    for excel_item in excel_items:
        excel_code = excel_item['code']
        excel_desc = excel_item['description'].lower()
        
        # Try to find match by SKU or name
        matched = None
        
        for db_item in db_items:
            db_sku = db_item.sku.upper()
            db_name = db_item.name.lower()
            
            # Match by SKU
            if excel_code == db_sku:
                matched = db_item
                break
            
            # Match by name similarity
            if excel_desc in db_name or db_name in excel_desc:
                matched = db_item
                break
        
        if matched:
            matches.append({
                'excel': excel_item,
                'db_item': matched
            })
        else:
            unmatched_excel.append(excel_item)
    
    return matches, unmatched_excel


def complete_stocktake(dry_run=True):
    """Update stocktake with Excel counts"""
    print("=" * 80)
    print("COMPLETE STOCKTAKE FROM MARKO EXCEL")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print("=" * 80)
    
    # Get hotel
    hotel = Hotel.objects.get(name="Hotel Killarney")
    print(f"\n✅ Hotel: {hotel.name}")
    
    # Get existing stocktake
    stocktake = Stocktake.objects.filter(
        hotel=hotel,
        status='DRAFT'
    ).first()
    
    if not stocktake:
        print("\n❌ No DRAFT stocktake found!")
        print("   Create one first or the system already populated one")
        return
    
    print(f"✅ Found stocktake: {stocktake.period_start} to {stocktake.period_end}")
    print(f"   Status: {stocktake.status}")
    print(f"   Total lines: {stocktake.lines.count()}")
    
    # Parse Excel
    print(f"\n📂 Loading Excel data from CSV...")
    excel_items = parse_marko_csv()
    print(f"✅ Found {len(excel_items)} items in Excel")
    
    # Get DB items
    db_items = list(StockItem.objects.filter(hotel=hotel))
    print(f"✅ Found {len(db_items)} items in database")
    
    # Match items
    print(f"\n🔍 Matching Excel data to database items...")
    matches, unmatched = match_items(excel_items, db_items)
    print(f"✅ Matched: {len(matches)} items")
    print(f"⚠️  Unmatched: {len(unmatched)} items")
    
    # Show first 10 matches
    print(f"\n📋 FIRST 10 MATCHES:")
    print("=" * 80)
    for idx, match in enumerate(matches[:10], 1):
        excel = match['excel']
        db_item = match['db_item']
        print(f"\n[{idx}] Excel: {excel['code']} - {excel['description']}")
        print(f"    DB: {db_item.sku} - {db_item.name}")
        print(f"    Count: {excel['full_units']} full + "
              f"{excel['partial_units']} partial")
        print(f"    Value: £{excel['value']}")
    
    # Show unmatched
    if unmatched:
        print(f"\n⚠️  UNMATCHED EXCEL ITEMS (first 10):")
        print("-" * 80)
        for item in unmatched[:10]:
            print(f"   {item['code']} - {item['description']}")
    
    # Update stocktake lines
    print(f"\n" + "=" * 80)
    print("📝 UPDATING STOCKTAKE LINES")
    print("=" * 80)
    
    updates_made = 0
    
    for match in matches:
        excel = match['excel']
        db_item = match['db_item']
        
        # Get or create stocktake line
        line, created = StocktakeLine.objects.get_or_create(
            stocktake=stocktake,
            item=db_item,
            defaults={
                'opening_qty': Decimal('0'),
                'valuation_cost': db_item.unit_cost / db_item.uom if db_item.uom else Decimal('0'),
            }
        )
        
        # Update counts
        old_full = line.counted_full_units
        old_partial = line.counted_partial_units
        
        new_full = Decimal(str(excel['full_units']))
        new_partial = Decimal(str(excel['partial_units']))
        
        if not dry_run:
            line.counted_full_units = new_full
            line.counted_partial_units = new_partial
            line.save()
        
        if old_full != new_full or old_partial != new_partial:
            updates_made += 1
            if updates_made <= 10:  # Show first 10 updates
                print(f"\n✏️  {db_item.sku} - {db_item.name}")
                print(f"   Old: {old_full} full + {old_partial} partial")
                print(f"   New: {new_full} full + {new_partial} partial")
                print(f"   Variance: {line.variance_qty} {db_item.base_unit}")
    
    print(f"\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total Excel items: {len(excel_items)}")
    print(f"Matched to DB: {len(matches)}")
    print(f"Updates needed: {updates_made}")
    print(f"Unmatched: {len(unmatched)}")
    
    if dry_run:
        print(f"\n✅ Dry run complete - no changes made")
        print(f"   Run with --update to apply changes")
    else:
        print(f"\n✅ Stocktake updated successfully!")
        print(f"   Updated {updates_made} stocktake lines")
        print(f"\n💡 Next steps:")
        print(f"   1. Review stocktake in UI")
        print(f"   2. Check variances")
        print(f"   3. Approve stocktake to create adjustments")
        print(f"   POST /api/hotel-killarney/stocktakes/{stocktake.id}/approve/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', action='store_true',
                       help='Actually update stocktake')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run only (default)')
    args = parser.parse_args()
    
    dry_run = not args.update
    complete_stocktake(dry_run=dry_run)
    print("\n" + "=" * 80)
