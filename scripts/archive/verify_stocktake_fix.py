"""
Verify the fix for stocktake value calculation.
This should now show counted_value instead of expected_value.
"""
import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from stock_tracker.stock_serializers import StocktakeSerializer

def verify_fix():
    """Verify that the fix is working correctly"""
    
    # Get September stocktake (ID 17)
    try:
        stocktake = Stocktake.objects.get(id=17)
    except Stocktake.DoesNotExist:
        print("❌ Stocktake #17 not found")
        return
    
    print(f"🔍 Verifying Fix for Stocktake #{stocktake.id}")
    print(f"   Period: {stocktake.period_start} to {stocktake.period_end}")
    print("=" * 80)
    
    # Calculate totals manually
    total_expected = sum(line.expected_value for line in stocktake.lines.all())
    total_counted = sum(line.counted_value for line in stocktake.lines.all())
    total_variance = sum(line.variance_value for line in stocktake.lines.all())
    
    print("\n📊 MANUAL CALCULATIONS:")
    print(f"   Total Expected Value:  €{total_expected:,.2f}")
    print(f"   Total Counted Value:   €{total_counted:,.2f} ← Should match Excel")
    print(f"   Total Variance Value:  €{total_variance:,.2f}")
    
    # Check serializer output
    print("\n🔧 SERIALIZER OUTPUT:")
    serializer = StocktakeSerializer(stocktake)
    data = serializer.data
    
    print(f"   total_value (expected):       {data.get('total_value')}")
    print(f"   total_counted_value (NEW):    {data.get('total_counted_value')} ← NEW FIELD")
    print(f"   total_variance_value:         {data.get('total_variance_value')}")
    
    # Compare with Excel
    excel_total = Decimal('8382.19')
    
    print("\n✅ VERIFICATION:")
    if data.get('total_counted_value'):
        api_counted = Decimal(data.get('total_counted_value'))
        diff = api_counted - excel_total
        
        print(f"   Excel Total:          €{excel_total:,.2f}")
        print(f"   API Counted Value:    €{api_counted:,.2f}")
        print(f"   Difference:           €{diff:,.2f}")
        
        if abs(diff) < Decimal('1.00'):
            print("\n   ✅ SUCCESS! Values match within €1.00")
            print("   The fix is working correctly!")
        else:
            print(f"\n   ⚠️  Still a difference of €{diff:,.2f}")
    else:
        print("   ❌ total_counted_value field not found in serializer output")
    
    # Check category totals
    print("\n📋 CATEGORY TOTALS (from API):")
    totals = stocktake.get_category_totals()
    
    grand_counted = Decimal('0.00')
    grand_expected = Decimal('0.00')
    
    for cat_code, cat_data in totals.items():
        counted = cat_data['counted_value']
        expected = cat_data['expected_value']
        grand_counted += counted
        grand_expected += expected
        
        print(f"\n   {cat_code} - {cat_data['category_name']}:")
        print(f"      Expected Value:  €{expected:,.2f}")
        print(f"      Counted Value:   €{counted:,.2f} ← Use this")
        print(f"      Variance:        €{cat_data['variance_value']:,.2f}")
    
    print("\n" + "=" * 80)
    print(f"   Grand Total (Expected):  €{grand_expected:,.2f}")
    print(f"   Grand Total (Counted):   €{grand_counted:,.2f} ← Should be €8,382.19")
    print("=" * 80)

if __name__ == '__main__':
    verify_fix()
