"""
Verification Script: Test Stocktake Calculations
Tests that all formulas in documentation match actual backend implementation
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake, StocktakeLine, StockItem
from hotel.models import Hotel
from decimal import Decimal

def test_formulas():
    """Test all stocktake formulas with real data"""
    print("=" * 80)
    print("STOCKTAKE FORMULA VERIFICATION")
    print("=" * 80)
    
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found")
        return
    
    print(f"✅ Testing with Hotel: {hotel.name}\n")
    
    # Get November stocktake
    nov_period = StockPeriod.objects.filter(
        hotel=hotel, 
        year=2025, 
        month=11
    ).first()
    
    if not nov_period:
        print("❌ November 2025 period not found")
        return
    
    print(f"✅ November 2025 Period: ID {nov_period.id}")
    print(f"   Dates: {nov_period.start_date} to {nov_period.end_date}\n")
    
    # Get or check stocktake
    stocktake = Stocktake.objects.filter(
        hotel=hotel,
        period_start=nov_period.start_date,
        period_end=nov_period.end_date
    ).first()
    
    if not stocktake:
        print("⚠️  No stocktake exists yet for November")
        print("   Creating test scenario with snapshots...\n")
        
        # Test with snapshots
        snapshots = StockSnapshot.objects.filter(period=nov_period)[:5]
        
        for snap in snapshots:
            print(f"\n{'='*70}")
            print(f"ITEM: {snap.item.sku} - {snap.item.name}")
            print(f"Category: {snap.item.category.code} ({snap.item.category.name})")
            print(f"UOM: {snap.item.uom}")
            print(f"{'='*70}")
            
            # Opening (from snapshot)
            opening_qty = snap.closing_full_units * snap.item.uom + snap.closing_partial_units
            print(f"\n📊 SNAPSHOT DATA:")
            print(f"   Closing Full Units: {snap.closing_full_units}")
            print(f"   Closing Partial Units: {snap.closing_partial_units}")
            print(f"   Closing Value: €{snap.closing_stock_value}")
            print(f"   → Total Servings: {opening_qty}")
            
        return
    
    print(f"✅ Stocktake Found: ID {stocktake.id}")
    print(f"   Status: {stocktake.status}")
    print(f"   Lines: {stocktake.lines.count()}\n")
    
    # Test with 5 different category items
    print("\n" + "="*80)
    print("TESTING FORMULAS WITH ACTUAL STOCKTAKE LINES")
    print("="*80)
    
    # Get one item from each category
    categories = ['B', 'D', 'S', 'W', 'M']
    test_lines = []
    
    for cat in categories:
        line = stocktake.lines.filter(item__category__code=cat).first()
        if line:
            test_lines.append(line)
    
    if not test_lines:
        print("⚠️  No lines found in stocktake")
        return
    
    for line in test_lines:
        print(f"\n{'='*70}")
        print(f"ITEM: {line.item.sku} - {line.item.name}")
        print(f"Category: {line.item.category.code} ({line.item.category.name})")
        print(f"Size: {line.item.size}")
        print(f"UOM: {line.item.uom}")
        print(f"Valuation Cost: €{line.valuation_cost} per serving")
        print(f"{'='*70}")
        
        # Test Formula 1: Expected Quantity
        print(f"\n📐 FORMULA 1: Expected Quantity")
        print(f"   Formula: expected = opening + purchases - waste")
        print(f"   Opening: {line.opening_qty}")
        print(f"   Purchases: {line.purchases}")
        print(f"   Waste: {line.waste}")
        
        manual_expected = line.opening_qty + line.purchases - line.waste
        model_expected = line.expected_qty
        
        print(f"   → Manual Calculation: {manual_expected}")
        print(f"   → Model Property: {model_expected}")
        print(f"   ✅ MATCH!" if manual_expected == model_expected else f"   ❌ MISMATCH!")
        
        # Test Formula 2: Counted Quantity
        print(f"\n📐 FORMULA 2: Counted Quantity")
        print(f"   Counted Full Units: {line.counted_full_units}")
        print(f"   Counted Partial Units: {line.counted_partial_units}")
        
        category = line.item.category_id
        size = line.item.size or ''
        is_dozen = 'DOZ' in size.upper()
        
        if category == 'D' or is_dozen:
            print(f"   Formula: (full × UOM) + partial  [Draught/Dozen logic]")
            manual_counted = (line.counted_full_units * line.item.uom) + line.counted_partial_units
        else:
            print(f"   Formula: (full × UOM) + (partial × UOM)  [Fractional logic]")
            manual_counted = (line.counted_full_units * line.item.uom) + (line.counted_partial_units * line.item.uom)
        
        model_counted = line.counted_qty
        
        print(f"   → Manual Calculation: {manual_counted}")
        print(f"   → Model Property: {model_counted}")
        print(f"   ✅ MATCH!" if manual_counted == model_counted else f"   ❌ MISMATCH!")
        
        # Test Formula 3: Variance
        print(f"\n📐 FORMULA 3: Variance")
        print(f"   Formula: variance = counted - expected")
        
        manual_variance = model_counted - model_expected
        model_variance = line.variance_qty
        
        print(f"   → Manual Calculation: {manual_variance}")
        print(f"   → Model Property: {model_variance}")
        print(f"   ✅ MATCH!" if manual_variance == model_variance else f"   ❌ MISMATCH!")
        
        # Test Formula 4: Values
        print(f"\n📐 FORMULA 4: Values")
        
        manual_expected_value = model_expected * line.valuation_cost
        manual_counted_value = model_counted * line.valuation_cost
        manual_variance_value = manual_counted_value - manual_expected_value
        
        print(f"   Expected Value: €{manual_expected_value:.2f} (manual) vs €{line.expected_value:.2f} (model)")
        print(f"   ✅ MATCH!" if abs(manual_expected_value - line.expected_value) < Decimal('0.01') else f"   ❌ MISMATCH!")
        
        print(f"   Counted Value: €{manual_counted_value:.2f} (manual) vs €{line.counted_value:.2f} (model)")
        print(f"   ✅ MATCH!" if abs(manual_counted_value - line.counted_value) < Decimal('0.01') else f"   ❌ MISMATCH!")
        
        print(f"   Variance Value: €{manual_variance_value:.2f} (manual) vs €{line.variance_value:.2f} (model)")
        print(f"   ✅ MATCH!" if abs(manual_variance_value - line.variance_value) < Decimal('0.01') else f"   ❌ MISMATCH!")
        
        # Test Display Unit Conversion
        print(f"\n📐 FORMULA 5: Display Unit Conversion")
        print(f"   Testing with expected_qty: {model_expected}")
        
        full_manual = int(model_expected / line.item.uom)
        partial_manual = model_expected % line.item.uom
        
        # Apply rounding based on category
        if line.item.category.code == 'B' or is_dozen:
            partial_manual = round(float(partial_manual))
        else:
            partial_manual = round(float(partial_manual), 2)
        
        print(f"   → Manual: {full_manual} full, {partial_manual} partial")
        
        # Get from serializer (need to import and test)
        from stock_tracker.stock_serializers import StocktakeLineSerializer
        serializer = StocktakeLineSerializer(line)
        
        print(f"   → Serializer: {serializer.data['expected_display_full_units']} full, {serializer.data['expected_display_partial_units']} partial")
        
        if str(full_manual) == serializer.data['expected_display_full_units']:
            print(f"   ✅ Full units MATCH!")
        else:
            print(f"   ❌ Full units MISMATCH!")
    
    # Test Category Totals
    print(f"\n\n{'='*80}")
    print("CATEGORY TOTALS VERIFICATION")
    print(f"{'='*80}")
    
    for category in categories:
        lines = stocktake.lines.filter(item__category__code=category)
        if not lines.exists():
            continue
        
        print(f"\n{category} - {lines.first().item.category.name}:")
        print(f"   Items: {lines.count()}")
        
        total_expected_value = sum(line.expected_value for line in lines)
        total_counted_value = sum(line.counted_value for line in lines)
        total_variance_value = sum(line.variance_value for line in lines)
        
        print(f"   Expected Value: €{total_expected_value:.2f}")
        print(f"   Counted Value: €{total_counted_value:.2f}")
        print(f"   Variance Value: €{total_variance_value:.2f}")
        
        if total_expected_value > 0:
            variance_pct = (abs(total_variance_value) / total_expected_value) * 100
            print(f"   Variance %: {variance_pct:.2f}%")
    
    # Grand Total
    print(f"\n{'='*80}")
    all_lines = stocktake.lines.all()
    grand_expected = sum(line.expected_value for line in all_lines)
    grand_counted = sum(line.counted_value for line in all_lines)
    grand_variance = sum(line.variance_value for line in all_lines)
    
    print(f"GRAND TOTALS:")
    print(f"   Total Items: {all_lines.count()}")
    print(f"   Expected Value: €{grand_expected:.2f}")
    print(f"   Counted Value: €{grand_counted:.2f}")
    print(f"   Variance Value: €{grand_variance:.2f}")
    
    print(f"\n{'='*80}")
    print("✅ VERIFICATION COMPLETE")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    test_formulas()
