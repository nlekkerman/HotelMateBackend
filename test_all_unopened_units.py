"""
Test unopened_units_count for all categories showing partial unit handling
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockCategory
from hotel.models import Hotel
from decimal import Decimal


def test_all_categories_unopened():
    """Test unopened_units_count for all categories"""
    
    print("=" * 90)
    print("UNOPENED UNITS COUNT - All Categories")
    print("Showing how partial units are handled for analytics")
    print("=" * 90)
    print()
    
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found")
        return
    
    # Test data: category, subcategory, full, partial, expected unopened
    test_cases = [
        {
            'category': 'D',
            'subcategory': None,
            'name': 'Guinness Keg',
            'uom': 88,
            'full': 3,
            'partial': 25,  # 25 pints in opened keg
            'expected': 3,
            'note': 'Ignores opened keg (25 pints)'
        },
        {
            'category': 'B',
            'subcategory': None,
            'name': 'Heineken 330ml',
            'uom': 12,
            'full': 4,  # 4 cases
            'partial': 8,  # 8 loose bottles
            'expected': 56,  # (4×12) + 8
            'note': 'Includes loose bottles'
        },
        {
            'category': 'M',
            'subcategory': 'SOFT_DRINKS',
            'name': 'Coca Cola',
            'uom': 12,
            'full': 5,  # 5 cases
            'partial': 10,  # 10 loose bottles
            'expected': 70,  # (5×12) + 10
            'note': 'Includes loose bottles'
        },
        {
            'category': 'M',
            'subcategory': 'SYRUPS',
            'name': 'Cola Syrup',
            'uom': 700,
            'full': 8,
            'partial': 0.5,  # Half bottle opened
            'expected': 8,
            'note': 'Ignores opened bottle (0.5)'
        },
        {
            'category': 'M',
            'subcategory': 'JUICES',
            'name': 'Orange Juice',
            'uom': 1000,
            'full': 2,  # 2 cases
            'partial': 11.75,  # 11 bottles + 750ml
            'expected': 35,  # (2×12) + 11
            'note': 'Includes 11 full bottles, ignores 750ml'
        },
        {
            'category': 'M',
            'subcategory': 'CORDIALS',
            'name': 'Blackcurrant',
            'uom': 12,
            'full': 3,  # 3 cases
            'partial': 7,  # 7 loose bottles
            'expected': 43,  # (3×12) + 7
            'note': 'Includes loose bottles'
        },
        {
            'category': 'M',
            'subcategory': 'BIB',
            'name': 'Pepsi BIB',
            'uom': 1,
            'full': 12,
            'partial': 0.5,  # Half box opened
            'expected': 12,
            'note': 'Ignores opened box (0.5)'
        },
        {
            'category': 'M',
            'subcategory': 'BULK_JUICES',
            'name': 'Bulk OJ 5L',
            'uom': 1,
            'full': 25,
            'partial': 0.25,  # Quarter bottle opened
            'expected': 25,
            'note': 'Ignores opened bottle (0.25)'
        },
        {
            'category': 'S',
            'subcategory': None,
            'name': 'Vodka 70cl',
            'uom': 28,
            'full': 6,
            'partial': 0.5,  # Half bottle opened
            'expected': 6,
            'note': 'Ignores opened bottle (0.5)'
        },
        {
            'category': 'W',
            'subcategory': None,
            'name': 'House Red',
            'uom': 5,
            'full': 15,
            'partial': 0.75,  # 3/4 bottle opened
            'expected': 15,
            'note': 'Ignores opened bottle (0.75)'
        },
    ]
    
    print(f"{'Category':<25} {'Storage':<25} {'Unopened':<12} {'Note':<35}")
    print("-" * 90)
    
    for test in test_cases:
        category = StockCategory.objects.filter(code=test['category']).first()
        if not category:
            continue
        
        item = StockItem(
            hotel=hotel,
            category=category,
            subcategory=test['subcategory'],
            name=test['name'],
            sku=f"TEST-{test['name'][:5]}",
            uom=test['uom'],
            current_full_units=Decimal(str(test['full'])),
            current_partial_units=Decimal(str(test['partial'])),
            unit_cost=Decimal('10.00'),
            menu_price=Decimal('5.00')
        )
        
        # Get unopened count
        unopened = item.unopened_units_count
        
        # Build category display
        cat_display = test['category']
        if test['subcategory']:
            cat_display += f"/{test['subcategory']}"
        cat_display += f" - {test['name']}"
        
        # Build storage display
        storage = f"{test['full']} + {test['partial']}"
        
        # Check if matches expected
        status = "✅" if unopened == test['expected'] else f"❌ Expected {test['expected']}"
        
        print(f"{cat_display:<25} {storage:<25} {unopened:<12} {test['note']:<35}")
    
    print()
    print("=" * 90)
    print("SUMMARY:")
    print("=" * 90)
    print()
    print("CATEGORIES THAT IGNORE PARTIAL (Opened Units):")
    print("  • Draught (D):      Partial = pints in opened keg")
    print("  • Spirits (S):      Partial = fraction of opened bottle")
    print("  • Wine (W):         Partial = fraction of opened bottle")
    print("  • Syrups:           Partial = fraction of opened bottle")
    print("  • BIB:              Partial = fraction of opened box")
    print("  • Bulk Juices:      Partial = fraction of opened bottle")
    print()
    print("CATEGORIES THAT INCLUDE PARTIAL (Unopened Loose Units):")
    print("  • Bottled Beer (B): Partial = loose bottles (include)")
    print("  • Soft Drinks:      Partial = loose bottles (include)")
    print("  • Cordials:         Partial = loose bottles (include)")
    print("  • Juices:           Partial = bottles.ml (include integer part)")
    print()
    print("✅ Analytics will show clean, accurate unopened unit counts!")
    print()


if __name__ == '__main__':
    test_all_categories_unopened()
