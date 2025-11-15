# Generated migration
from django.db import migrations
from decimal import Decimal


def fix_minerals_uom(apps, schema_editor):
    """
    Fix UOM values for minerals items based on subcategory.
    
    According to specification:
    - SOFT_DRINKS: UOM = 12 (bottles per case) ✓ already correct
    - BIB: UOM = 18 (liters per box) - FIX from 500!
    - SYRUPS: UOM = bottle size in ml (700 or 1000)
    - JUICES: UOM = bottle size in ml (1000 or 1500)
    - CORDIALS: UOM = 12 (bottles per case)
    """
    StockItem = apps.get_model('stock_tracker', 'StockItem')
    
    # 1) SOFT_DRINKS: already 12, but ensure it
    soft_drinks = StockItem.objects.filter(
        category_id='M',
        subcategory='SOFT_DRINKS'
    )
    count_soft = soft_drinks.update(uom=Decimal('12.00'))
    print(f"  → SOFT_DRINKS: {count_soft} items set to UOM=12")
    
    # 2) BIB: FIX from 500 to 18 liters per box
    bib = StockItem.objects.filter(
        category_id='M',
        subcategory='BIB'
    )
    count_bib = bib.update(uom=Decimal('18.00'))
    print(f"  → BIB: {count_bib} items set to UOM=18 (was 500!)")
    
    # 3) SYRUPS: Set to bottle size in ml
    # 70cl = 700ml
    syrups_70cl = StockItem.objects.filter(
        category_id='M',
        subcategory='SYRUPS',
        size__icontains='70cl'
    )
    count_70cl = syrups_70cl.update(uom=Decimal('700.00'))
    print(f"  → SYRUPS (70cl): {count_70cl} items set to UOM=700ml")
    
    # 1L = 1000ml
    syrups_1l = StockItem.objects.filter(
        category_id='M',
        subcategory='SYRUPS',
        size__icontains='1L'
    )
    count_1l = syrups_1l.update(uom=Decimal('1000.00'))
    print(f"  → SYRUPS (1L): {count_1l} items set to UOM=1000ml")
    
    # 4) JUICES: Set to bottle size in ml
    # 1L = 1000ml
    juices_1l = StockItem.objects.filter(
        category_id='M',
        subcategory='JUICES',
        size__icontains='1L'
    )
    count_juices_1l = juices_1l.update(uom=Decimal('1000.00'))
    print(f"  → JUICES (1L): {count_juices_1l} items set to UOM=1000ml")
    
    # 1.5L = 1500ml
    juices_15l = StockItem.objects.filter(
        category_id='M',
        subcategory='JUICES',
        size__icontains='1.5L'
    )
    count_juices_15l = juices_15l.update(uom=Decimal('1500.00'))
    print(f"  → JUICES (1.5L): {count_juices_15l} items set to UOM=1500ml")
    
    # 5) CORDIALS: UOM = 12 (bottles per case)
    cordials = StockItem.objects.filter(
        category_id='M',
        subcategory='CORDIALS'
    )
    count_cordials = cordials.update(uom=Decimal('12.00'))
    print(f"  → CORDIALS: {count_cordials} items set to UOM=12")
    
    print("\n✅ UOM values fixed for all minerals subcategories")


def reverse_uom_fix(apps, schema_editor):
    """
    Reverse: No safe way to restore old values.
    Old BIB value (500) was incorrect.
    """
    print("⚠ Cannot reverse UOM changes - old values were incorrect")
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('stock_tracker', '0020_populate_minerals_subcategory'),
    ]

    operations = [
        migrations.RunPython(
            fix_minerals_uom,
            reverse_uom_fix
        ),
    ]
