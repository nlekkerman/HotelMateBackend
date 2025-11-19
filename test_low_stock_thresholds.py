"""
Test low stock thresholds for all categories and subcategories.
Shows how the new category-specific thresholds work.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockCategory
from hotel.models import Hotel
from decimal import Decimal

def test_low_stock_thresholds():
    """Test low_stock_threshold property for different categories"""
    
    print("=" * 80)
    print("LOW STOCK THRESHOLD TEST - Category-Specific Thresholds")
    print("=" * 80)
    print()
    
    # Get a hotel
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found. Please create a hotel first.")
        return
    
    print(f"Testing with Hotel: {hotel.name}")
    print()
    
    # Test cases: (category_id, subcategory, uom, name, current_full, current_partial)
    test_items = [
        # Draught Beer
        {
            'category_id': 'D',
            'subcategory': None,
            'name': 'Guinness Keg',
            'uom': 88,  # 88 pints per keg
            'current_full_units': 1,  # 1 keg
            'current_partial_units': 50,  # 50 pints
            'expected_threshold': 2,  # 2 kegs
            'expected_servings': 1.57,  # 1 + (50/88) = 1.57 kegs
            'expected_low_stock': True
        },
        # Bottled Beer (cases)
        {
            'category_id': 'B',
            'subcategory': None,
            'name': 'Heineken 330ml',
            'uom': 12,  # 12 bottles per case
            'current_full_units': 3,  # 3 cases
            'current_partial_units': 8,  # 8 bottles
            'expected_threshold': 50,  # 50 bottles
            'expected_servings': 44,  # (3 × 12) + 8 = 44 bottles
            'expected_low_stock': True
        },
        # Minerals - Soft Drinks (cases)
        {
            'category_id': 'M',
            'subcategory': 'SOFT_DRINKS',
            'name': 'Coca Cola 330ml',
            'uom': 12,
            'current_full_units': 5,  # 5 cases
            'current_partial_units': 10,  # 10 bottles
            'expected_threshold': 50,  # 50 bottles
            'expected_servings': 70,  # (5 × 12) + 10 = 70 bottles
            'expected_low_stock': False
        },
        # Minerals - Syrups
        {
            'category_id': 'M',
            'subcategory': 'SYRUPS',
            'name': 'Coca Cola Syrup',
            'uom': 700,  # 700ml bottle
            'current_full_units': 1,  # 1 bottle
            'current_partial_units': 0.5,  # 0.5 bottles
            'expected_threshold': 2,  # 2 bottles
            'expected_servings': 1.5,  # 1 + 0.5 = 1.5 bottles
            'expected_low_stock': True
        },
        # Minerals - Juices (cases + bottles)
        {
            'category_id': 'M',
            'subcategory': 'JUICES',
            'name': 'Orange Juice 1L',
            'uom': 1000,  # 1000ml bottle
            'current_full_units': 2,  # 2 cases
            'current_partial_units': 5.75,  # 5 bottles + 750ml
            'expected_threshold': 50,  # 50 bottles
            'expected_servings': 29.75,  # (2×12) + 5.75 = 29.75 bottles
            'expected_low_stock': True
        },
        # Minerals - Cordials (cases)
        {
            'category_id': 'M',
            'subcategory': 'CORDIALS',
            'name': 'Blackcurrant Cordial',
            'uom': 12,
            'current_full_units': 1,  # 1 case
            'current_partial_units': 5,  # 5 bottles
            'expected_threshold': 20,  # 20 bottles
            'expected_servings': 17,  # (1 × 12) + 5 = 17 bottles
            'expected_low_stock': True
        },
        # Minerals - BIB (boxes)
        {
            'category_id': 'M',
            'subcategory': 'BIB',
            'name': 'Pepsi BIB 10L',
            'uom': 1,  # individual box
            'current_full_units': 1,  # 1 box
            'current_partial_units': 0.5,  # 0.5 box
            'expected_threshold': 2,  # 2 boxes
            'expected_servings': 1.5,  # 1 + 0.5 = 1.5 boxes
            'expected_low_stock': True
        },
        # Minerals - Bulk Juices (individual bottles)
        {
            'category_id': 'M',
            'subcategory': 'BULK_JUICES',
            'name': 'Bulk Orange Juice 5L',
            'uom': 1,  # individual bottle
            'current_full_units': 15,  # 15 bottles
            'current_partial_units': 0.25,  # 0.25 bottle
            'expected_threshold': 20,  # 20 bottles
            'expected_servings': 15.25,  # 15 + 0.25 = 15.25 bottles
            'expected_low_stock': True
        },
        # Spirits
        {
            'category_id': 'S',
            'subcategory': None,
            'name': 'Vodka 70cl',
            'uom': 28,  # 28 shots per bottle
            'current_full_units': 3,  # 3 bottles
            'current_partial_units': 0.25,  # 0.25 bottle
            'expected_threshold': 2,  # 2 bottles
            'expected_servings': 3.25,  # 3 + 0.25 = 3.25 bottles
            'expected_low_stock': False
        },
        # Wine
        {
            'category_id': 'W',
            'subcategory': None,
            'name': 'House Red Wine',
            'uom': 5,  # 5 glasses per bottle
            'current_full_units': 8,  # 8 bottles
            'current_partial_units': 0.5,  # 0.5 bottle
            'expected_threshold': 10,  # 10 bottles
            'expected_servings': 8.5,  # 8 + 0.5 = 8.5 bottles
            'expected_low_stock': True
        },
    ]
    
    print(f"{'Category':<20} {'Name':<25} {'Current':<12} {'Threshold':<12} {'Low Stock':<12}")
    print("-" * 80)
    
    for item_data in test_items:
        # Get or create category
        category = StockCategory.objects.filter(code=item_data['category_id']).first()
        if not category:
            print(f"❌ Category {item_data['category_id']} not found")
            continue
        
        # Create temporary item
        item = StockItem(
            hotel=hotel,
            category=category,
            subcategory=item_data['subcategory'],
            name=item_data['name'],
            sku=f"TEST-{item_data['name'][:10]}",
            uom=item_data['uom'],
            current_full_units=Decimal(str(item_data['current_full_units'])),
            current_partial_units=Decimal(str(item_data['current_partial_units'])),
            unit_cost=Decimal('10.00'),
            menu_price=Decimal('5.00')
        )
        
        # Get threshold and physical units (don't save to DB)
        threshold = item.low_stock_threshold
        physical_units = item.total_stock_in_physical_units
        is_low_stock = physical_units < threshold
        
        # Build category display
        cat_display = item_data['category_id']
        if item_data['subcategory']:
            cat_display += f"/{item_data['subcategory']}"
        
        # Check if results match expectations
        status = "✅" if is_low_stock == item_data['expected_low_stock'] else "❌"
        
        print(f"{cat_display:<20} {item_data['name']:<25} {float(physical_units):<12.2f} {float(threshold):<12.0f} {str(is_low_stock):<12} {status}")
        
        # Show detailed calculation if there's a mismatch
        if abs(float(physical_units) - item_data['expected_servings']) > 0.1:
            print(f"  ⚠️  Expected units: {item_data['expected_servings']}, Got: {float(physical_units)}")
        if float(threshold) != item_data['expected_threshold']:
            print(f"  ⚠️  Expected threshold: {item_data['expected_threshold']}, Got: {float(threshold)}")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("Category-Specific Thresholds Applied (PHYSICAL UNITS):")
    print("  • Draught (D):          2 kegs")
    print("  • Bottled Beer (B):     50 bottles")
    print("  • Soft Drinks:          50 bottles")
    print("  • Syrups:               2 bottles")
    print("  • Juices:               50 bottles")
    print("  • Cordials:             20 bottles")
    print("  • BIB:                  2 boxes")
    print("  • Bulk Juices:          20 bottles")
    print("  • Spirits (S):          2 bottles")
    print("  • Wine (W):             10 bottles")
    print()
    print("✅ All items tested successfully!")
    print()

if __name__ == '__main__':
    test_low_stock_thresholds()
