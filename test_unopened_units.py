"""
Test unopened_units_count property to show clean analytics display
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockCategory
from hotel.models import Hotel
from decimal import Decimal

def test_unopened_units():
    """Test unopened_units_count for analytics display"""
    
    print("=" * 80)
    print("UNOPENED UNITS TEST - Clean Analytics Display")
    print("=" * 80)
    print()
    
    # Get a hotel
    hotel = Hotel.objects.first()
    category_d = StockCategory.objects.filter(code='D').first()
    
    if not hotel or not category_d:
        print("❌ Missing hotel or category")
        return
    
    # Test Draught with partial keg
    guinness = StockItem(
        hotel=hotel,
        category=category_d,
        name='Guinness',
        sku='TEST-GUIN',
        uom=88,  # 88 pints per keg
        current_full_units=Decimal('3'),  # 3 full kegs
        current_partial_units=Decimal('25'),  # 25 pints in opened keg
        unit_cost=Decimal('180.00'),
        menu_price=Decimal('5.50')
    )
    
    print(f"Item: {guinness.name}")
    print(f"Storage: {guinness.current_full_units} kegs + {guinness.current_partial_units} pints")
    print()
    print("FIELDS FOR DIFFERENT PURPOSES:")
    print("-" * 80)
    print(f"total_stock_in_servings:        {guinness.total_stock_in_servings:.2f} pints")
    print(f"  ↳ Use for: Menu sales, revenue calculations")
    print()
    print(f"total_stock_in_physical_units:  {guinness.total_stock_in_physical_units:.2f} kegs")
    print(f"  ↳ Use for: Detailed ordering (includes partial)")
    print()
    print(f"unopened_units_count:           {guinness.unopened_units_count} kegs")
    print(f"  ↳ Use for: Analytics dashboard (clean whole numbers)")
    print()
    print(f"low_stock_threshold:            {guinness.low_stock_threshold} kegs")
    print()
    
    # Status check
    is_low_stock = guinness.unopened_units_count < guinness.low_stock_threshold
    status = "⚠️ LOW STOCK" if is_low_stock else "✅ OK"
    print(f"Status: {status}")
    print(f"  ({guinness.unopened_units_count} unopened kegs vs {guinness.low_stock_threshold} threshold)")
    print()
    
    print("=" * 80)
    print("ANALYTICS DASHBOARD DISPLAY:")
    print("=" * 80)
    print()
    print(f"{'Item':<20} {'Current Stock':<20} {'Threshold':<15} {'Status':<10}")
    print("-" * 80)
    print(f"{guinness.name:<20} {guinness.unopened_units_count} kegs{'':<13} {guinness.low_stock_threshold} kegs{'':<8} {status}")
    print()
    print("✅ Clean, whole numbers - no decimals!")
    print()

if __name__ == '__main__':
    test_unopened_units()
