"""
Test October 2025 Stocktake Calculations
Simulates frontend calculations and compares with backend
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel


def test_line_calculations(line):
    """Test all calculations for a single line"""
    
    # Frontend calculation: Counted Qty
    frontend_counted = (
        float(line.counted_full_units) * float(line.item.uom)
    ) + float(line.counted_partial_units)
    
    # Backend calculation: Counted Qty
    backend_counted = float(line.counted_qty)
    
    # Frontend calculation: Expected Qty
    frontend_expected = (
        float(line.opening_qty) +
        float(line.purchases) -
        float(line.waste)
    )
    
    # Backend calculation: Expected Qty
    backend_expected = float(line.expected_qty)
    
    # Frontend calculation: Variance
    frontend_variance = frontend_counted - frontend_expected
    
    # Backend calculation: Variance
    backend_variance = float(line.variance_qty)
    
    # Check if they match (within 0.0001 tolerance)
    counted_match = abs(frontend_counted - backend_counted) < 0.0001
    expected_match = abs(frontend_expected - backend_expected) < 0.0001
    variance_match = abs(frontend_variance - backend_variance) < 0.0001
    
    return {
        'sku': line.item.sku,
        'name': line.item.name,
        'category': line.item.category.code,
        'counted_match': counted_match,
        'expected_match': expected_match,
        'variance_match': variance_match,
        'frontend_counted': frontend_counted,
        'backend_counted': backend_counted,
        'frontend_expected': frontend_expected,
        'backend_expected': backend_expected,
        'frontend_variance': frontend_variance,
        'backend_variance': backend_variance,
    }


def main():
    print("=" * 80)
    print("OCTOBER 2025 STOCKTAKE CALCULATION TEST")
    print("=" * 80)
    print()
    
    # Get October 2025 stocktake
    hotel = Hotel.objects.first()
    october_stocktake = Stocktake.objects.filter(
        hotel=hotel,
        period_start__year=2025,
        period_start__month=10
    ).first()
    
    if not october_stocktake:
        print("❌ October 2025 stocktake not found!")
        return
    
    print(f"✅ Found October 2025 Stocktake (ID: {october_stocktake.id})")
    print(f"   Period: {october_stocktake.period_start} to {october_stocktake.period_end}")
    print(f"   Status: {october_stocktake.status}")
    print(f"   Total Lines: {october_stocktake.lines.count()}")
    print()
    
    # Get all lines
    lines = october_stocktake.lines.all()
    
    # Test calculations
    print("Testing calculations for all items...")
    print()
    
    results = []
    for line in lines:
        result = test_line_calculations(line)
        results.append(result)
    
    # Summary by category
    categories = ['D', 'B', 'S', 'M', 'W']
    category_names = {
        'D': 'Draught Beer',
        'B': 'Bottled Beer',
        'S': 'Spirits',
        'M': 'Minerals/Syrups',
        'W': 'Wine'
    }
    
    print("=" * 80)
    print("RESULTS BY CATEGORY")
    print("=" * 80)
    print()
    
    total_items = 0
    total_pass = 0
    total_fail = 0
    
    for cat in categories:
        cat_results = [r for r in results if r['category'] == cat]
        if not cat_results:
            continue
        
        cat_pass = sum(
            1 for r in cat_results
            if r['counted_match'] and r['expected_match'] and r['variance_match']
        )
        cat_fail = len(cat_results) - cat_pass
        
        total_items += len(cat_results)
        total_pass += cat_pass
        total_fail += cat_fail
        
        status = "✅" if cat_fail == 0 else "⚠️"
        print(f"{status} {category_names[cat]} ({cat}):")
        print(f"   Total Items: {len(cat_results)}")
        print(f"   Pass: {cat_pass}")
        print(f"   Fail: {cat_fail}")
        print()
    
    # Overall summary
    print("=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Items Tested: {total_items}")
    print(f"✅ Passed: {total_pass}")
    print(f"❌ Failed: {total_fail}")
    
    if total_fail == 0:
        print()
        print("🎉 ALL CALCULATIONS MATCH! Frontend and Backend are in sync!")
    else:
        print()
        print("⚠️  Some calculations don't match. Details:")
        print()
        
        for result in results:
            if not (result['counted_match'] and result['expected_match'] and result['variance_match']):
                print(f"❌ {result['sku']} - {result['name']}")
                
                if not result['counted_match']:
                    print(f"   Counted: Frontend={result['frontend_counted']:.4f}, "
                          f"Backend={result['backend_counted']:.4f}")
                
                if not result['expected_match']:
                    print(f"   Expected: Frontend={result['frontend_expected']:.4f}, "
                          f"Backend={result['backend_expected']:.4f}")
                
                if not result['variance_match']:
                    print(f"   Variance: Frontend={result['frontend_variance']:.4f}, "
                          f"Backend={result['backend_variance']:.4f}")
                print()
    
    # Test specific examples
    print()
    print("=" * 80)
    print("DETAILED EXAMPLES (First 5 Items)")
    print("=" * 80)
    print()
    
    for i, result in enumerate(results[:5]):
        print(f"{i+1}. {result['name']} ({result['category']})")
        print(f"   SKU: {result['sku']}")
        print()
        print(f"   Counted Quantity:")
        print(f"     Frontend: {result['frontend_counted']:.4f}")
        print(f"     Backend:  {result['backend_counted']:.4f}")
        print(f"     Match: {'✅' if result['counted_match'] else '❌'}")
        print()
        print(f"   Expected Quantity:")
        print(f"     Frontend: {result['frontend_expected']:.4f}")
        print(f"     Backend:  {result['backend_expected']:.4f}")
        print(f"     Match: {'✅' if result['expected_match'] else '❌'}")
        print()
        print(f"   Variance:")
        print(f"     Frontend: {result['frontend_variance']:.4f}")
        print(f"     Backend:  {result['backend_variance']:.4f}")
        print(f"     Match: {'✅' if result['variance_match'] else '❌'}")
        print()
        print("-" * 80)
        print()
    
    # Test decimal rules by category
    print()
    print("=" * 80)
    print("DECIMAL VALIDATION TEST")
    print("=" * 80)
    print()
    
    for cat in categories:
        cat_lines = [line for line in lines if line.item.category.code == cat]
        if not cat_lines:
            continue
        
        sample_line = cat_lines[0]
        partial = float(sample_line.counted_partial_units)
        
        # Check if decimal rules are followed
        if cat == 'B':
            has_decimals = (partial % 1) != 0
            print(f"Bottled Beer ({cat}): {sample_line.item.name}")
            print(f"   Partial Units: {partial}")
            print(f"   Should be whole number: {'✅' if not has_decimals else '❌'}")
        elif cat == 'M' and 'Doz' in sample_line.item.size:
            has_decimals = (partial % 1) != 0
            print(f"Minerals Dozen ({cat}): {sample_line.item.name}")
            print(f"   Partial Units: {partial}")
            print(f"   Should be whole number: {'✅' if not has_decimals else '❌'}")
        else:
            decimals = len(str(partial).split('.')[-1]) if '.' in str(partial) else 0
            print(f"{category_names[cat]} ({cat}): {sample_line.item.name}")
            print(f"   Partial Units: {partial}")
            print(f"   Max 2 decimals: {'✅' if decimals <= 2 else '❌'}")
        print()


if __name__ == "__main__":
    main()
