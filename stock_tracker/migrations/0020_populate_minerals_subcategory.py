# Generated migration
from django.db import migrations


def populate_subcategories(apps, schema_editor):
    """
    Populate subcategory field for Minerals items.
    NO auto-detection - based on explicit patterns from specification.
    """
    StockItem = apps.get_model('stock_tracker', 'StockItem')
    
    # 1) Soft Drinks: Size = "Doz"
    soft_drinks = StockItem.objects.filter(
        category_id='M',
        size__icontains='Doz'
    )
    count_soft_drinks = soft_drinks.update(subcategory='SOFT_DRINKS')
    print(f"  → SOFT_DRINKS: {count_soft_drinks} items")
    
    # 2) BIB: Size contains "18LT" or "18 LT"
    bib = StockItem.objects.filter(
        category_id='M',
        size__icontains='18LT'
    )
    count_bib = bib.update(subcategory='BIB')
    print(f"  → BIB: {count_bib} items")
    
    # 3) Syrups: Name contains "Monin", "Grenadine", "Syrup", "Agave"
    syrups_monin = StockItem.objects.filter(
        category_id='M',
        name__icontains='Monin'
    )
    syrups_monin.update(subcategory='SYRUPS')
    
    syrups_grenadine = StockItem.objects.filter(
        category_id='M',
        name__icontains='Grenadine'
    )
    syrups_grenadine.update(subcategory='SYRUPS')
    
    syrups_syrup = StockItem.objects.filter(
        category_id='M',
        name__icontains='Syrup'
    )
    syrups_syrup.update(subcategory='SYRUPS')
    
    syrups_agave = StockItem.objects.filter(
        category_id='M',
        name__icontains='Agave'
    )
    syrups_agave.update(subcategory='SYRUPS')
    
    count_syrups = StockItem.objects.filter(
        category_id='M',
        subcategory='SYRUPS'
    ).count()
    print(f"  → SYRUPS: {count_syrups} items")
    
    # 4) Cordials: Name contains "Miwadi" or "Cordial"
    cordials_miwadi = StockItem.objects.filter(
        category_id='M',
        name__icontains='Miwadi'
    )
    cordials_miwadi.update(subcategory='CORDIALS')
    
    cordials_cordial = StockItem.objects.filter(
        category_id='M',
        name__icontains='Cordial'
    )
    cordials_cordial.update(subcategory='CORDIALS')
    
    count_cordials = StockItem.objects.filter(
        category_id='M',
        subcategory='CORDIALS'
    ).count()
    print(f"  → CORDIALS: {count_cordials} items")
    
    # 5) Juices: Name contains "Juice", "Kulana", or "Lemonade"
    juices_juice = StockItem.objects.filter(
        category_id='M',
        name__icontains='Juice'
    )
    juices_juice.update(subcategory='JUICES')
    
    juices_kulana = StockItem.objects.filter(
        category_id='M',
        name__icontains='Kulana'
    )
    juices_kulana.update(subcategory='JUICES')
    
    juices_lemonade = StockItem.objects.filter(
        category_id='M',
        name__icontains='Lemonade'
    )
    juices_lemonade.update(subcategory='JUICES')
    
    count_juices = StockItem.objects.filter(
        category_id='M',
        subcategory='JUICES'
    ).count()
    print(f"  → JUICES: {count_juices} items")
    
    # Check for any uncategorized minerals
    uncategorized = StockItem.objects.filter(
        category_id='M',
        subcategory__isnull=True
    ).count()
    if uncategorized > 0:
        print(f"  ⚠ WARNING: {uncategorized} minerals items not categorized")
        print("    These need manual subcategory assignment!")


def reverse_population(apps, schema_editor):
    """Reverse: clear all subcategories"""
    StockItem = apps.get_model('stock_tracker', 'StockItem')
    StockItem.objects.filter(category_id='M').update(subcategory=None)


class Migration(migrations.Migration):

    dependencies = [
        ('stock_tracker', '0019_add_minerals_subcategory'),
    ]

    operations = [
        migrations.RunPython(
            populate_subcategories,
            reverse_population
        ),
    ]
