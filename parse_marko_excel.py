"""
Script to properly parse and analyze MARKO Excel data
Run: python parse_marko_excel.py
"""
import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

EXCEL_PATH = r"C:\Users\nlekk\Downloads\MARKO Beverage Stock Valuation 30 Sep'25.xlsx"


def parse_marko_excel():
    print("=" * 80)
    print("MARKO BEVERAGE STOCK DATA PARSER")
    print("=" * 80)
    
    try:
        # Read the most recent sheet (Oct'25)
        print(f"\n📂 Reading sheet: Oct'25")
        
        # Row 0: Title, Row 1: Headers (Code, Description, etc)
        # Skip first row, use row 1 as headers
        df = pd.read_excel(EXCEL_PATH, sheet_name="Oct'25", skiprows=1)
        
        print(f"\n✅ Loaded {len(df)} rows")
        print(f"\n📋 Actual Column Names:")
        for idx, col in enumerate(df.columns, 1):
            print(f"   {idx:2d}. {col}")
        
        # Clean up - remove completely empty rows
        df = df.dropna(how='all')
        print(f"\n✅ After cleanup: {len(df)} rows")
        
        # Display first 10 items
        print(f"\n📦 FIRST 10 STOCK ITEMS:")
        print("=" * 80)
        
        for idx, row in df.head(10).iterrows():
            print(f"\n[{idx}] {row.get('Code', 'N/A')} - {row.get('Description', 'N/A')}")
            print(f"    Size: {row.get('Size', 'N/A')}")
            print(f"    UOM: {row.get('UOM', 'N/A')}")
            print(f"    Cost Price: £{row.get('Cost Price', 0)}")
            print(f"    Full Kegs/Cases: {row.get('Closing Stock - Full Kegs', 0)}")
            print(f"    Partial (Pints): {row.get('Closing Stock - Pints', 0)}")
            print(f"    Stock Value: £{row.get('Stock at Cost', 0)}")
        
        # Statistics
        print(f"\n" + "=" * 80)
        print("📊 SUMMARY STATISTICS")
        print("=" * 80)
        
        total_items = len(df)
        items_with_stock = df[df['Stock at Cost'] > 0].shape[0] if 'Stock at Cost' in df.columns else 0
        total_value = df['Stock at Cost'].sum() if 'Stock at Cost' in df.columns else 0
        
        print(f"\nTotal Items: {total_items}")
        print(f"Items with Stock: {items_with_stock}")
        print(f"Total Stock Value: £{total_value:,.2f}")
        
        # Categorize by size (rough category detection)
        print(f"\n📁 PRODUCT BREAKDOWN:")
        print("-" * 80)
        
        if 'Size' in df.columns:
            size_groups = df.groupby('Size').size().sort_values(ascending=False)
            for size, count in size_groups.head(10).items():
                print(f"   {size:20s}: {count:3d} items")
        
        # Show sample mappings to our database
        print(f"\n" + "=" * 80)
        print("🔗 MAPPING TO DATABASE FIELDS")
        print("=" * 80)
        print("""
Excel Column              -> Database Field
-----------------------------------------
Code                      -> sku
Description               -> name
Size                      -> size
UOM                       -> uom (units per keg/case)
Cost Price                -> unit_cost
Closing Stock - Full Kegs -> For stocktake: counted_full_units
Closing Stock - Pints     -> For stocktake: counted_partial_units
Stock at Cost             -> (calculated: qty × cost)

NOTES:
- UOM appears to be pints per keg (e.g., 35, 53)
- Need to convert to our base_unit system (ml or L)
- Full Kegs = complete kegs
- Pints = partial pints from open kegs
- Most items are draught beer (kegs)
        """)
        
        # Export clean CSV for review
        output_csv = "marko_stock_cleaned.csv"
        df.to_csv(output_csv, index=False)
        print(f"\n✅ Exported clean data to: {output_csv}")
        print(f"   Review this file to decide what to import")
        
        return df
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    df = parse_marko_excel()
    print("\n" + "=" * 80)
    
    if df is not None:
        print("\n💡 NEXT STEPS:")
        print("-" * 80)
        print("1. Review marko_stock_cleaned.csv")
        print("2. Decide which items to import")
        print("3. Map categories (all appear to be Beers/Draught)")
        print("4. Create import script with proper unit conversions")
        print("5. Import as StockItems + create Stocktake with counts")
