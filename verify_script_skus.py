"""
Verify all SKUs in update script exist in database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem


# All SKUs from update_all_product_names.py
all_skus = [
    # BOTTLED BEER
    ('BB0114', 'Killarney Brewing Co GF Lager'),
    ('BB096', 'Killarney Brewing Co Lager'),
    ('BB124', 'Killarney Brewing Co Pale Ale'),
    
    # DRAUGHT BEER
    ('DB001', 'Guinness Draught (30Lt)'),
    ('DB002', 'Heineken Draught (50Lt)'),
    ('DB003', 'Heineken Draught (20Lt)'),
    ('DB004', 'Bulmers Original Draught (30Lt)'),
    ('DB005', 'Birra Moretti Draught (30Lt)'),
    ('DB023', 'Lagunitas IPA'),
    ('DB026', 'Orchard Thieves Draught'),
    
    # MINERALS - SPLITS
    ('M0007', 'Split 7up'),
    ('M0008', 'Split 7UP Diet'),
    ('M0009', 'Split Coke'),
    ('M0213', 'Split Coke 330ML'),
    ('M0010', 'Split Coke Diet'),
    ('M0114', 'Split Fanta Lemon'),
    ('M0012', 'Split Fanta Orange'),
    ('M0013', 'Split Friuce Juices'),
    ('M0014', 'Split Lucozade'),
    ('M0015', 'Split Pepsi'),
    ('M0016', 'Split Poachers Ginger Beer'),
    ('M0255', 'Split Sch'),
    ('M0122', 'Split Sch Elderflower'),
    ('M0120', 'Split Sprite/Zero'),
    ('M0246', 'Splits Britvic Juices'),
    
    # MINERALS - ACRONYMS
    ('M0195', 'Baby SCH Mims'),
    ('M0258', 'Mixer Lemon Juice 700ML'),
    ('M0264', 'Mixer Lime Juice 700ML'),
    ('M0265', 'Riverrock 750ml'),
    
    # MINERALS - SIZES
    ('M0028', 'Monin Agave Syrup 700ml'),
    ('M0035', 'Monin Chocolate Cookie LTR'),
    ('M0192', 'Monin Coconut Syrup 700ML'),
    ('M0038', 'Monin Elderflower Syrup 700ML'),
    ('M0189', 'Monin Passionfruit Puree Ltr'),
    ('M0191', 'Monin Passionfruit Syrup 700ML'),
    ('M0227', 'Monin Pink Grapefruit 700ML'),
    ('M0039', 'Monin Puree Coconut LTR'),
    ('M0040', 'Monin Strawberry Puree Ltr'),
    ('M0041', 'Monin Strawberry Syrup 700ml'),
    ('M0222', 'Monin Vanilla Syrup Ltr'),
    ('M0044', 'Monin Watermelon Syrup 700ML'),
    
    # BIB
    ('M25', 'Splash Cola 18LTR'),
    ('M24', 'Splash Energy18LTR'),
    ('M23', 'Splash White18LTR'),
]

print("="*80)
print("SKU VERIFICATION")
print("="*80)

found = []
not_found = []
name_mismatch = []

for sku, expected_name in all_skus:
    try:
        item = StockItem.objects.get(sku=sku)
        
        if item.name == expected_name:
            found.append((sku, item.name))
            print(f"✓ {sku}: {item.name}")
        else:
            name_mismatch.append((sku, expected_name, item.name))
            print(f"⚠️  {sku}: Expected '{expected_name}'")
            print(f"       Found '{item.name}'")
    
    except StockItem.DoesNotExist:
        not_found.append((sku, expected_name))
        print(f"✗ {sku}: NOT FOUND IN DATABASE - {expected_name}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"✓ Found with exact name: {len(found)}")
print(f"⚠️  Found with different name: {len(name_mismatch)}")
print(f"✗ Not found in database: {len(not_found)}")
print(f"Total SKUs checked: {len(all_skus)}")

if name_mismatch:
    print("\n" + "="*80)
    print("NAME MISMATCHES (will still be updated)")
    print("="*80)
    for sku, expected, actual in name_mismatch:
        print(f"\n{sku}:")
        print(f"  Script expects: {expected}")
        print(f"  Database has:   {actual}")

if not_found:
    print("\n" + "="*80)
    print("MISSING SKUs (need to fix script)")
    print("="*80)
    for sku, name in not_found:
        print(f"  {sku}: {name}")
