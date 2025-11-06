"""
Import MARKO stock data into database
Run: python import_marko_stock.py --dry-run
Run: python import_marko_stock.py --import
"""
import os
import django
import pandas as pd
from decimal import Decimal
import argparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockCategory, Stocktake, StocktakeLine
from hotel.models import Hotel

CSV_PATH = "marko_stock_cleaned.csv"


def parse_marko_csv():
    """Parse the CSV and extract meaningful data"""
    print("📂 Loading CSV...")
    
    # Read raw CSV
    df = pd.read_csv(CSV_PATH, skip_blank_lines=False)
    
    # Find section breaks (rows where first column is 'Code')
    sections = []
    current_section = []
    section_name = None
    
    for idx, row in df.iterrows():
        first_col = str(row.iloc[0])
        
        if first_col == 'Code' and idx > 0:
            # New section starting
            if current_section:
                sections.append((section_name, pd.DataFrame(current_section)))
            current_section = []
            section_name = "Unknown"
            continue
        
        if first_col.startswith('Total for'):
            # End of section
            if current_section:
                total_name = row.iloc[6] if pd.notna(row.iloc[6]) else "Unknown"
                sections.append((total_name, pd.DataFrame(current_section)))
            current_section = []
            continue
        
        if first_col not in ['Code', 'nan'] and pd.notna(first_col):
            # Data row
            current_section.append({
                'Code': row.iloc[0],
                'Description': row.iloc[1],
                'Size': row.iloc[2],
                'UOM': row.iloc[3],
                'Cost Price': row.iloc[4],
                'Full Units': row.iloc[5],
                'Partial Units': row.iloc[6],
                'Stock at Cost': row.iloc[7],
            })
    
    # Add last section
    if current_section:
        sections.append(("Bottled/Canned", pd.DataFrame(current_section)))
    
    return sections


def import_to_database(dry_run=True):
    """Import stock items and stocktake data"""
    print("=" * 80)
    print("MARKO STOCK IMPORT")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE IMPORT'}")
    print("=" * 80)
    
    # Get hotel
    hotel = Hotel.objects.get(name="Hotel Killarney")
    print(f"\n✅ Hotel: {hotel.name}")
    
    # Parse CSV
    sections = parse_marko_csv()
    print(f"\n✅ Found {len(sections)} sections")
    
    for section_name, df in sections:
        print(f"\n{'─' * 80}")
        print(f"📦 SECTION: {section_name} ({len(df)} items)")
        print(f"{'─' * 80}")
        
        for idx, row in df.head(10).iterrows():
            code = row['Code']
            desc = row['Description']
            size = row['Size']
            uom = row['UOM']
            cost = row['Cost Price']
            full = row['Full Units']
            partial = row['Partial Units']
            value = row['Stock at Cost']
            
            print(f"\n[{idx+1}] {code} - {desc}")
            print(f"    Size: {size}, UOM: {uom}, Cost: £{cost}")
            print(f"    Stock: {full} full + {partial} partial = £{value}")
    
    print(f"\n" + "=" * 80)
    print("📊 IMPORT SUMMARY")
    print("=" * 80)
    
    total_items = sum(len(df) for _, df in sections)
    print(f"Total items to import: {total_items}")
    
    if not dry_run:
        print("\n⚠️  LIVE IMPORT NOT YET IMPLEMENTED")
        print("   Review data first, then implement import logic")
    else:
        print("\n✅ Dry run complete - no database changes made")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--import', action='store_true', dest='do_import',
                       help='Actually import (default is dry-run)')
    parser.add_argument('--dry-run', action='store_true', dest='dry_run',
                       help='Dry run only (default)')
    args = parser.parse_args()
    
    dry_run = not args.do_import
    import_to_database(dry_run=dry_run)
    print("\n" + "=" * 80)
