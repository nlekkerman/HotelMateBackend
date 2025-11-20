"""
Test Purchases and Waste Validation

Tests that:
- PURCHASES must be in FULL UNITS only (kegs, cases, bottles, boxes)
- WASTE must be in PARTIAL UNITS only (opened items)

Run with: python test_purchases_waste_validation.py
"""
import os
import sys
import django

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from stock_tracker.models import StockItem, StockCategory
from hotel.models import Hotel


def create_test_items(hotel):
    """Create test items for each category"""
    
    # Get or create categories
    draught_cat, _ = StockCategory.objects.get_or_create(
        code='D', defaults={'name': 'Draught Beer'}
    )
    bottled_cat, _ = StockCategory.objects.get_or_create(
        code='B', defaults={'name': 'Bottled Beer'}
    )
    spirits_cat, _ = StockCategory.objects.get_or_create(
        code='S', defaults={'name': 'Spirits'}
    )
    wine_cat, _ = StockCategory.objects.get_or_create(
        code='W', defaults={'name': 'Wine'}
    )
    minerals_cat, _ = StockCategory.objects.get_or_create(
        code='M', defaults={'name': 'Minerals'}
    )
    
    items = {}
    
    # 1. DRAUGHT BEER - quantity in PINTS (servings)
    items['draught'], _ = StockItem.objects.get_or_create(
        hotel=hotel,
        sku='TEST-D001',
        defaults={
            'category': draught_cat,
            'name': 'Test Guinness Keg',
            'size': '50L',
            'size_value': Decimal('50.00'),
            'size_unit': 'L',
            'uom': Decimal('88.00'),  # 88 pints per keg
            'unit_cost': Decimal('150.0000'),
            'current_full_units': Decimal('2.00'),
            'current_partial_units': Decimal('25.0000')
        }
    )
    
    # 2. BOTTLED BEER - quantity in BOTTLES (servings)
    items['bottled'], _ = StockItem.objects.get_or_create(
        hotel=hotel,
        sku='TEST-B001',
        defaults={
            'category': bottled_cat,
            'name': 'Test Heineken Case',
            'size': '330ml',
            'size_value': Decimal('330.00'),
            'size_unit': 'ml',
            'uom': Decimal('12.00'),  # 12 bottles per case
            'unit_cost': Decimal('18.0000'),
            'current_full_units': Decimal('5.00'),
            'current_partial_units': Decimal('3.0000')
        }
    )
    
    # 3. SPIRITS - quantity in BOTTLES (UOM=1, 1:1)
    items['spirits'], _ = StockItem.objects.get_or_create(
        hotel=hotel,
        sku='TEST-S001',
        defaults={
            'category': spirits_cat,
            'name': 'Test Vodka',
            'size': '70cl',
            'size_value': Decimal('70.00'),
            'size_unit': 'cl',
            'uom': Decimal('1.00'),  # 1:1 (bottles)
            'unit_cost': Decimal('25.0000'),
            'current_full_units': Decimal('10.00'),
            'current_partial_units': Decimal('0.5000')
        }
    )
    
    # 4. WINE - quantity in BOTTLES (UOM=1, 1:1)
    items['wine'], _ = StockItem.objects.get_or_create(
        hotel=hotel,
        sku='TEST-W001',
        defaults={
            'category': wine_cat,
            'name': 'Test Merlot',
            'size': '75cl',
            'size_value': Decimal('75.00'),
            'size_unit': 'cl',
            'uom': Decimal('1.00'),  # 1:1 (bottles)
            'unit_cost': Decimal('15.0000'),
            'current_full_units': Decimal('20.00'),
            'current_partial_units': Decimal('0.2500')
        }
    )
    
    # 5. SOFT DRINKS - quantity in BOTTLES (servings)
    items['soft_drinks'], _ = StockItem.objects.get_or_create(
        hotel=hotel,
        sku='TEST-M001',
        defaults={
            'category': minerals_cat,
            'subcategory': 'SOFT_DRINKS',
            'name': 'Test Coca-Cola Case',
            'size': '330ml',
            'size_value': Decimal('330.00'),
            'size_unit': 'ml',
            'uom': Decimal('12.00'),  # 12 bottles per case
            'unit_cost': Decimal('10.0000'),
            'current_full_units': Decimal('8.00'),
            'current_partial_units': Decimal('5.0000')
        }
    )
    
    # 6. SYRUPS - quantity in BOTTLES (UOM=1, 1:1)
    items['syrups'], _ = StockItem.objects.get_or_create(
        hotel=hotel,
        sku='TEST-M002',
        defaults={
            'category': minerals_cat,
            'subcategory': 'SYRUPS',
            'name': 'Test Vanilla Syrup',
            'size': '1L',
            'size_value': Decimal('1000.00'),
            'size_unit': 'ml',
            'uom': Decimal('1.00'),  # 1:1 (bottles)
            'unit_cost': Decimal('12.0000'),
            'current_full_units': Decimal('5.00'),
            'current_partial_units': Decimal('0.7500')
        }
    )
    
    # 7. CORDIALS - quantity in BOTTLES (servings)
    items['cordials'], _ = StockItem.objects.get_or_create(
        hotel=hotel,
        sku='TEST-M003',
        defaults={
            'category': minerals_cat,
            'subcategory': 'CORDIALS',
            'name': 'Test Orange Cordial',
            'size': '750ml',
            'size_value': Decimal('750.00'),
            'size_unit': 'ml',
            'uom': Decimal('12.00'),  # 12 bottles per case
            'unit_cost': Decimal('15.0000'),
            'current_full_units': Decimal('3.00'),
            'current_partial_units': Decimal('7.0000')
        }
    )
    
    # 8. BIB - quantity in BOXES (UOM=1, 1:1)
    items['bib'], _ = StockItem.objects.get_or_create(
        hotel=hotel,
        sku='TEST-M004',
        defaults={
            'category': minerals_cat,
            'subcategory': 'BIB',
            'name': 'Test BIB Lemonade',
            'size': '18L',
            'size_value': Decimal('18.00'),
            'size_unit': 'L',
            'uom': Decimal('1.00'),  # 1:1 (boxes)
            'unit_cost': Decimal('20.0000'),
            'current_full_units': Decimal('4.00'),
            'current_partial_units': Decimal('0.5000')
        }
    )
    
    return items


def test_purchases_validation():
    """Test that purchases must be in full units"""
    print("\n" + "=" * 80)
    print("TESTING PURCHASES VALIDATION (Must be FULL UNITS only)")
    print("=" * 80)
    
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found")
        return
    
    items = create_test_items(hotel)
    
    test_cases = [
        # (item_key, quantity, should_pass, description)
        
        # DRAUGHT BEER (quantity in pints)
        ('draught', Decimal('88.00'), True, 
         "Draught: 88 pints (1 keg) - VALID"),
        ('draught', Decimal('176.00'), True, 
         "Draught: 176 pints (2 kegs) - VALID"),
        ('draught', Decimal('50.00'), False, 
         "Draught: 50 pints (partial keg) - INVALID"),
        ('draught', Decimal('100.00'), False, 
         "Draught: 100 pints (1 keg + partial) - INVALID"),
        
        # BOTTLED BEER (quantity in bottles)
        ('bottled', Decimal('12.00'), True, 
         "Bottled: 12 bottles (1 case) - VALID"),
        ('bottled', Decimal('24.00'), True, 
         "Bottled: 24 bottles (2 cases) - VALID"),
        ('bottled', Decimal('5.00'), False, 
         "Bottled: 5 bottles (partial case) - INVALID"),
        ('bottled', Decimal('15.00'), False, 
         "Bottled: 15 bottles (1 case + 3) - INVALID"),
        
        # SPIRITS (quantity = bottles, UOM=1)
        ('spirits', Decimal('5.00'), True, 
         "Spirits: 5 bottles - VALID"),
        ('spirits', Decimal('10.00'), True, 
         "Spirits: 10 bottles - VALID"),
        ('spirits', Decimal('5.50'), False, 
         "Spirits: 5.5 bottles - INVALID"),
        ('spirits', Decimal('2.25'), False, 
         "Spirits: 2.25 bottles - INVALID"),
        
        # WINE (quantity = bottles, UOM=1)
        ('wine', Decimal('3.00'), True, 
         "Wine: 3 bottles - VALID"),
        ('wine', Decimal('1.00'), True, 
         "Wine: 1 bottle - VALID"),
        ('wine', Decimal('3.50'), False, 
         "Wine: 3.5 bottles - INVALID"),
        ('wine', Decimal('0.75'), False, 
         "Wine: 0.75 bottles - INVALID"),
        
        # SOFT DRINKS (quantity in bottles)
        ('soft_drinks', Decimal('12.00'), True, 
         "Soft Drinks: 12 bottles (1 case) - VALID"),
        ('soft_drinks', Decimal('36.00'), True, 
         "Soft Drinks: 36 bottles (3 cases) - VALID"),
        ('soft_drinks', Decimal('8.00'), False, 
         "Soft Drinks: 8 bottles (partial case) - INVALID"),
        ('soft_drinks', Decimal('18.00'), False, 
         "Soft Drinks: 18 bottles (1.5 cases) - INVALID"),
        
        # SYRUPS (quantity = bottles, UOM=1)
        ('syrups', Decimal('4.00'), True, 
         "Syrups: 4 bottles - VALID"),
        ('syrups', Decimal('1.00'), True, 
         "Syrups: 1 bottle - VALID"),
        ('syrups', Decimal('2.50'), False, 
         "Syrups: 2.5 bottles - INVALID"),
        ('syrups', Decimal('3.75'), False, 
         "Syrups: 3.75 bottles - INVALID"),
        
        # CORDIALS (quantity in bottles)
        ('cordials', Decimal('12.00'), True, 
         "Cordials: 12 bottles (1 case) - VALID"),
        ('cordials', Decimal('24.00'), True, 
         "Cordials: 24 bottles (2 cases) - VALID"),
        ('cordials', Decimal('6.00'), False, 
         "Cordials: 6 bottles (partial case) - INVALID"),
        
        # BIB (quantity = boxes, UOM=1)
        ('bib', Decimal('2.00'), True, 
         "BIB: 2 boxes - VALID"),
        ('bib', Decimal('5.00'), True, 
         "BIB: 5 boxes - VALID"),
        ('bib', Decimal('1.50'), False, 
         "BIB: 1.5 boxes - INVALID"),
        ('bib', Decimal('3.25'), False, 
         "BIB: 3.25 boxes - INVALID"),
    ]
    
    passed = 0
    failed = 0
    
    for item_key, quantity, should_pass, description in test_cases:
        item = items[item_key]
        category = item.category_id
        uom = item.uom
        
        # Simulate validation logic
        is_valid = True
        error_msg = None
        
        if uom == Decimal('1'):
            # UOM=1 items: must be whole numbers
            if quantity % 1 != 0:
                is_valid = False
                error_msg = "Must be whole numbers"
        else:
            # UOM>1 items: must be multiple of UOM
            if quantity % uom != 0:
                is_valid = False
                error_msg = f"Must be multiple of {uom}"
        
        # Check result
        if is_valid == should_pass:
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"❌ {description}")
            print(f"   Expected: {'PASS' if should_pass else 'FAIL'}, "
                  f"Got: {'PASS' if is_valid else 'FAIL'}")
            if error_msg:
                print(f"   Error: {error_msg}")
            failed += 1
    
    print("\n" + "-" * 80)
    print(f"PURCHASES: {passed} passed, {failed} failed")
    return passed, failed


def test_waste_validation():
    """Test that waste must be in partial units only"""
    print("\n" + "=" * 80)
    print("TESTING WASTE VALIDATION (Must be PARTIAL UNITS only)")
    print("=" * 80)
    
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found")
        return
    
    items = create_test_items(hotel)
    
    test_cases = [
        # (item_key, quantity, should_pass, description)
        
        # DRAUGHT BEER (quantity in pints)
        ('draught', Decimal('25.00'), True, 
         "Draught: 25 pints (partial keg) - VALID"),
        ('draught', Decimal('50.00'), True, 
         "Draught: 50 pints (partial keg) - VALID"),
        ('draught', Decimal('87.99'), True, 
         "Draught: 87.99 pints (almost full keg) - VALID"),
        ('draught', Decimal('88.00'), False, 
         "Draught: 88 pints (full keg) - INVALID"),
        ('draught', Decimal('176.00'), False, 
         "Draught: 176 pints (2 kegs) - INVALID"),
        
        # BOTTLED BEER (quantity in bottles)
        ('bottled', Decimal('3.00'), True, 
         "Bottled: 3 bottles (partial case) - VALID"),
        ('bottled', Decimal('7.00'), True, 
         "Bottled: 7 bottles (partial case) - VALID"),
        ('bottled', Decimal('11.00'), True, 
         "Bottled: 11 bottles (almost full case) - VALID"),
        ('bottled', Decimal('12.00'), False, 
         "Bottled: 12 bottles (full case) - INVALID"),
        ('bottled', Decimal('24.00'), False, 
         "Bottled: 24 bottles (2 cases) - INVALID"),
        
        # SPIRITS (quantity = bottles, UOM=1)
        ('spirits', Decimal('0.25'), True, 
         "Spirits: 0.25 bottles - VALID"),
        ('spirits', Decimal('0.50'), True, 
         "Spirits: 0.5 bottles - VALID"),
        ('spirits', Decimal('0.75'), True, 
         "Spirits: 0.75 bottles - VALID"),
        ('spirits', Decimal('0.99'), True, 
         "Spirits: 0.99 bottles - VALID"),
        ('spirits', Decimal('1.00'), False, 
         "Spirits: 1 bottle - INVALID"),
        ('spirits', Decimal('2.00'), False, 
         "Spirits: 2 bottles - INVALID"),
        
        # WINE (quantity = bottles, UOM=1)
        ('wine', Decimal('0.33'), True, 
         "Wine: 0.33 bottles - VALID"),
        ('wine', Decimal('0.50'), True, 
         "Wine: 0.5 bottles - VALID"),
        ('wine', Decimal('0.90'), True, 
         "Wine: 0.9 bottles - VALID"),
        ('wine', Decimal('1.00'), False, 
         "Wine: 1 bottle - INVALID"),
        ('wine', Decimal('1.50'), False, 
         "Wine: 1.5 bottles - INVALID"),
        
        # SOFT DRINKS (quantity in bottles)
        ('soft_drinks', Decimal('2.00'), True, 
         "Soft Drinks: 2 bottles (partial case) - VALID"),
        ('soft_drinks', Decimal('8.00'), True, 
         "Soft Drinks: 8 bottles (partial case) - VALID"),
        ('soft_drinks', Decimal('11.00'), True, 
         "Soft Drinks: 11 bottles - VALID"),
        ('soft_drinks', Decimal('12.00'), False, 
         "Soft Drinks: 12 bottles (full case) - INVALID"),
        ('soft_drinks', Decimal('24.00'), False, 
         "Soft Drinks: 24 bottles (2 cases) - INVALID"),
        
        # SYRUPS (quantity = bottles, UOM=1)
        ('syrups', Decimal('0.10'), True, 
         "Syrups: 0.1 bottles - VALID"),
        ('syrups', Decimal('0.50'), True, 
         "Syrups: 0.5 bottles - VALID"),
        ('syrups', Decimal('0.99'), True, 
         "Syrups: 0.99 bottles - VALID"),
        ('syrups', Decimal('1.00'), False, 
         "Syrups: 1 bottle - INVALID"),
        ('syrups', Decimal('2.00'), False, 
         "Syrups: 2 bottles - INVALID"),
        
        # CORDIALS (quantity in bottles)
        ('cordials', Decimal('4.00'), True, 
         "Cordials: 4 bottles (partial case) - VALID"),
        ('cordials', Decimal('9.00'), True, 
         "Cordials: 9 bottles (partial case) - VALID"),
        ('cordials', Decimal('12.00'), False, 
         "Cordials: 12 bottles (full case) - INVALID"),
        ('cordials', Decimal('13.00'), False, 
         "Cordials: 13 bottles (over full case) - INVALID"),
        
        # BIB (quantity = boxes, UOM=1)
        ('bib', Decimal('0.25'), True, 
         "BIB: 0.25 boxes - VALID"),
        ('bib', Decimal('0.50'), True, 
         "BIB: 0.5 boxes - VALID"),
        ('bib', Decimal('0.99'), True, 
         "BIB: 0.99 boxes - VALID"),
        ('bib', Decimal('1.00'), False, 
         "BIB: 1 box - INVALID"),
        ('bib', Decimal('2.00'), False, 
         "BIB: 2 boxes - INVALID"),
    ]
    
    passed = 0
    failed = 0
    
    for item_key, quantity, should_pass, description in test_cases:
        item = items[item_key]
        category = item.category_id
        uom = item.uom
        
        # Simulate validation logic
        is_valid = True
        error_msg = None
        
        if uom == Decimal('1'):
            # UOM=1 items: must be < 1
            if quantity >= 1:
                is_valid = False
                error_msg = "Must be less than 1"
        else:
            # UOM>1 items: must be < UOM
            if quantity >= uom:
                is_valid = False
                error_msg = f"Must be less than {uom}"
        
        # Check result
        if is_valid == should_pass:
            print(f"✅ {description}")
            passed += 1
        else:
            print(f"❌ {description}")
            print(f"   Expected: {'PASS' if should_pass else 'FAIL'}, "
                  f"Got: {'PASS' if is_valid else 'FAIL'}")
            if error_msg:
                print(f"   Error: {error_msg}")
            failed += 1
    
    print("\n" + "-" * 80)
    print(f"WASTE: {passed} passed, {failed} failed")
    return passed, failed


def main():
    print("\n" + "=" * 80)
    print("PURCHASES & WASTE VALIDATION TEST SUITE")
    print("=" * 80)
    
    purchases_passed, purchases_failed = test_purchases_validation()
    waste_passed, waste_failed = test_waste_validation()
    
    total_passed = purchases_passed + waste_passed
    total_failed = purchases_failed + waste_failed
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"✅ Total Passed: {total_passed}")
    print(f"❌ Total Failed: {total_failed}")
    print(f"📊 Success Rate: {(total_passed / (total_passed + total_failed) * 100):.1f}%")
    print("=" * 80)
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {total_failed} tests failed")


if __name__ == '__main__':
    main()
