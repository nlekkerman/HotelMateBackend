"""
Script to analyze the MARKO Beverage Stock Excel file
Run: python analyze_marko_excel.py
"""
import os
import django
import pandas as pd
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

EXCEL_PATH = r"C:\Users\nlekk\Downloads\MARKO Beverage Stock Valuation 30 Sep'25.xlsx"


def analyze_excel():
    print("=" * 80)
    print("MARKO BEVERAGE STOCK EXCEL ANALYSIS")
    print("=" * 80)
    
    try:
        # Load Excel file
        print(f"\n📂 Loading: {EXCEL_PATH}")
        
        # Read all sheets
        excel_file = pd.ExcelFile(EXCEL_PATH)
        print(f"\n✅ File loaded successfully!")
        print(f"📋 Found {len(excel_file.sheet_names)} sheet(s):")
        for idx, sheet in enumerate(excel_file.sheet_names, 1):
            print(f"   {idx}. {sheet}")
        
        # Analyze each sheet
        for sheet_name in excel_file.sheet_names:
            print("\n" + "=" * 80)
            print(f"ANALYZING SHEET: {sheet_name}")
            print("=" * 80)
            
            df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
            
            print(f"\n📊 Rows: {len(df)}")
            print(f"📊 Columns: {len(df.columns)}")
            
            print(f"\n📋 Column Names:")
            for idx, col in enumerate(df.columns, 1):
                print(f"   {idx:2d}. {col}")
            
            print(f"\n👀 First 5 rows preview:")
            print("-" * 80)
            print(df.head().to_string())
            
            print(f"\n📈 Data Types:")
            print(df.dtypes.to_string())
            
            # Check for empty rows
            non_empty_rows = df.dropna(how='all')
            if len(non_empty_rows) < len(df):
                print(f"\n⚠️  Found {len(df) - len(non_empty_rows)} empty rows")
            
            # Look for key columns that might map to our database
            print(f"\n🔍 DETECTED POTENTIAL DATABASE MAPPINGS:")
            print("-" * 80)
            
            col_lower = [col.lower() for col in df.columns]
            
            mappings = {
                'SKU/Code': ['sku', 'code', 'item code', 'product code'],
                'Name/Description': ['name', 'description', 'item', 'product', 'product name'],
                'Category': ['category', 'type', 'product type'],
                'Size': ['size', 'volume', 'quantity'],
                'UOM': ['uom', 'unit', 'units', 'pack size', 'case'],
                'Unit Cost': ['cost', 'unit cost', 'price', 'unit price'],
                'Quantity': ['qty', 'quantity', 'stock', 'on hand'],
                'Value': ['value', 'total value', 'stock value'],
            }
            
            for field, keywords in mappings.items():
                matches = [col for col, col_l in zip(df.columns, col_lower) 
                          if any(kw in col_l for kw in keywords)]
                if matches:
                    print(f"   {field:20s} -> {matches[0]}")
                    # Show sample values
                    sample = df[matches[0]].dropna().head(3).tolist()
                    print(f"                          Samples: {sample}")
            
            # Statistics
            print(f"\n📊 STATISTICS:")
            print("-" * 80)
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                print(f"\n   {col}:")
                print(f"      Count: {df[col].count()}")
                print(f"      Min: {df[col].min()}")
                print(f"      Max: {df[col].max()}")
                print(f"      Mean: {df[col].mean():.2f}")
                print(f"      Sum: {df[col].sum():.2f}")
        
        # Suggest import strategy
        print("\n" + "=" * 80)
        print("💡 IMPORT STRATEGY SUGGESTIONS")
        print("=" * 80)
        print("""
1. Map Excel columns to StockItem fields
2. Handle missing data (None/empty values)
3. Convert units (cl to ml, cases to bottles)
4. Calculate derived fields (cost_per_base, etc.)
5. Link to existing categories in database
6. Validate data before import
7. Create import script with dry-run option
        """)
        
    except FileNotFoundError:
        print(f"\n❌ File not found: {EXCEL_PATH}")
        print("   Make sure the file exists at this location")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_excel()
    print("\n" + "=" * 80)
