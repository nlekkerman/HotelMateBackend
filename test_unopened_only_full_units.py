"""
Test that unopened_units_count only shows FULL units across all categories.
Partial units (decimals like 0.5, 0.25) represent opened items and should be IGNORED.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from stock_tracker.models import StockItem, StockCategory
from hotel.models import Hotel

def test_unopened_units_only_full():
    """Test that all categories ignore partial units for unopened_units_count"""
    
    # Get first hotel
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found")
        return
    
    print("=" * 70)
    print("Testing: unopened_units_count ONLY shows FULL units")
    print("All partial units should be IGNORED")
    print("=" * 70)
    
    # Test cases: (category, subcategory, full_units, partial_units, expected_unopened)
    test_cases = [
        # Draught: full kegs only (partial = opened keg)
        ('D', None, Decimal('3.00'), Decimal('25.00'), 3, "3 kegs (ignore 25 pints in opened keg)"),
        
        # Bottled Beer: full cases only (partial = opened case)
        ('B', None, Decimal('4.00'), Decimal('0.50'), 48, "4 cases × 12 = 48 bottles (ignore 0.5 opened case)"),
        
        # Soft Drinks: full cases only (partial = opened case)
        ('M', 'SOFT_DRINKS', Decimal('5.00'), Decimal('0.30'), 60, "5 cases × 12 = 60 bottles (ignore 0.3 opened case)"),
        
        # Syrups: full bottles only (partial = opened bottle)
        ('M', 'SYRUPS', Decimal('10.00'), Decimal('0.50'), 10, "10 full bottles (ignore 0.5 opened bottle)"),
        
        # Juices: full cases only (partial = opened bottles/ml)
        ('M', 'JUICES', Decimal('2.00'), Decimal('11.75'), 24, "2 cases × 12 = 24 bottles (ignore 11.75 opened)"),
        
        # Cordials: full cases only (partial = opened case)
        ('M', 'CORDIALS', Decimal('3.00'), Decimal('0.60'), 36, "3 cases × 12 = 36 bottles (ignore 0.6 opened case)"),
        
        # BIB: full boxes only (partial = opened box)
        ('M', 'BIB', Decimal('5.00'), Decimal('0.50'), 5, "5 full boxes (ignore 0.5 opened box)"),
        
        # Bulk Juices: full bottles only (partial = opened bottle)
        ('M', 'BULK_JUICES', Decimal('20.00'), Decimal('0.25'), 20, "20 full bottles (ignore 0.25 opened bottle)"),
        
        # Spirits: full bottles only (partial = opened bottle)
        ('S', None, Decimal('8.00'), Decimal('0.25'), 8, "8 full bottles (ignore 0.25 opened bottle)"),
        
        # Wine: full bottles only (partial = opened bottle)
        ('W', None, Decimal('12.00'), Decimal('0.50'), 12, "12 full bottles (ignore 0.5 opened bottle)"),
    ]
    
    all_passed = True
    
    for category_id, subcategory, full, partial, expected, description in test_cases:
        # Get or create category (code is primary key)
        category = StockCategory.objects.filter(code=category_id).first()
        if not category:
            print(f"❌ Category {category_id} not found")
            continue
        
        # Create test item
        item_name = f"Test {category.name}"
        if subcategory:
            item_name += f" - {subcategory}"
        
        # Clean up any existing test item
        StockItem.objects.filter(name=item_name, hotel=hotel).delete()
        
        item = StockItem.objects.create(
            name=item_name,
            sku=f"{category_id}-TEST-001",
            category=category,
            subcategory=subcategory,
            hotel=hotel,
            size="750ml",
            size_value=Decimal('750.00'),
            size_unit="ml",
            uom=Decimal('12.00'),  # Standard case size
            unit_cost=Decimal('10.00'),
            current_full_units=full,
            current_partial_units=partial
        )
        
        result = item.unopened_units_count
        
        if result == expected:
            print(f"✅ {category_id:2} | {description}")
            print(f"   Full: {full}, Partial: {partial} → {result} units")
        else:
            print(f"❌ {category_id:2} | {description}")
            print(f"   Full: {full}, Partial: {partial}")
            print(f"   Expected: {expected}, Got: {result}")
            all_passed = False
        
        # Clean up
        item.delete()
        print()
    
    print("=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED - All categories ignore partial units correctly!")
    else:
        print("❌ SOME TESTS FAILED - Check the output above")
    print("=" * 70)

if __name__ == '__main__':
    test_unopened_units_only_full()
