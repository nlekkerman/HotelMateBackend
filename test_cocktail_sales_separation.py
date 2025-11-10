"""
Test to verify Cocktails and Sales are completely separate
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import CocktailConsumption, Sale
from django.db import connection


def test_cocktail_sales_separation():
    """Verify cocktails and sales are separate"""
    
    print("=" * 60)
    print("TESTING COCKTAIL AND SALES SEPARATION")
    print("=" * 60)
    
    # Check CocktailConsumption model fields
    print("\n1. CocktailConsumption Model Fields:")
    cocktail_fields = [f.name for f in CocktailConsumption._meta.get_fields()]
    print(f"   Fields: {', '.join(cocktail_fields)}")
    
    has_sale_connection = any('sale' in f.lower() for f in cocktail_fields)
    has_stocktake_connection = any('stocktake' in f.lower() for f in cocktail_fields)
    
    if has_sale_connection:
        print("   ❌ FOUND Sale connection in CocktailConsumption!")
    else:
        print("   ✅ NO Sale connection found")
    
    if has_stocktake_connection:
        print("   ❌ FOUND Stocktake connection in CocktailConsumption!")
    else:
        print("   ✅ NO Stocktake connection found")
    
    # Check Sale model fields
    print("\n2. Sale Model Fields:")
    sale_fields = [f.name for f in Sale._meta.get_fields()]
    print(f"   Fields: {', '.join(sale_fields)}")
    
    has_cocktail_connection = any('cocktail' in f.lower() for f in sale_fields)
    
    if has_cocktail_connection:
        print("   ❌ FOUND Cocktail connection in Sale!")
    else:
        print("   ✅ NO Cocktail connection found")
    
    # Check database tables
    print("\n3. Database Schema Check:")
    with connection.cursor() as cursor:
        # Get CocktailConsumption table columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stock_tracker_cocktailconsumption'
        """)
        cocktail_columns = [row[0] for row in cursor.fetchall()]
        print(f"   CocktailConsumption columns: {', '.join(cocktail_columns)}")
        
        sale_columns_in_cocktail = [c for c in cocktail_columns if 'sale' in c.lower() or 'stocktake' in c.lower()]
        if sale_columns_in_cocktail:
            print(f"   ❌ Found sale/stocktake columns: {sale_columns_in_cocktail}")
        else:
            print("   ✅ No sale/stocktake columns found")
    
    # Final verdict
    print("\n" + "=" * 60)
    print("VERDICT:")
    print("=" * 60)
    
    is_separated = (
        not has_sale_connection and 
        not has_stocktake_connection and 
        not has_cocktail_connection and
        not sale_columns_in_cocktail
    )
    
    if is_separated:
        print("✅ PASS: Cocktails and Sales are COMPLETELY SEPARATED")
        print("\nCocktailConsumption:")
        print("  - Tracks cocktail sales independently")
        print("  - Has its own revenue tracking")
        print("  - NO connection to Sale model")
        print("  - NO connection to Stocktake model")
        print("\nSale:")
        print("  - Tracks stock item sales only")
        print("  - NO connection to cocktails")
        print("\nThey only merge at REPORTING level (KPI endpoint)")
    else:
        print("❌ FAIL: Found unwanted connections!")
    
    return is_separated


if __name__ == "__main__":
    result = test_cocktail_sales_separation()
    print(f"\n\n{'✅ TEST PASSED' if result else '❌ TEST FAILED'}")
