"""
Comprehensive Product Name Updates
Removes numbers, acronyms, and abbreviations for better voice recognition
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem


def preview_updates():
    """Show all proposed changes before applying"""
    
    # BOTTLED BEER UPDATES
    bottled_updates = [
        ('B0114', 'Killarney Brewing Co GF Lager', 'Killarney Gluten Free Lager'),
        ('B0096', 'Killarney Brewing Co Lager', 'Killarney Lager'),
        ('B0124', 'Killarney Brewing Co Pale Ale', 'Killarney Pale Ale'),
    ]
    
    # DRAUGHT BEER UPDATES
    draught_updates = [
        ('D001', 'Guinness Draught (30Lt)', 'Guinness Draught'),
        ('D002', 'Heineken Draught (50Lt)', 'Heineken Draught'),
        ('D003', 'Heineken Draught (20Lt)', 'Heineken Draught'),
        ('D004', 'Bulmers Original Draught (30Lt)', 'Bulmers Original Draught'),
        ('D005', 'Birra Moretti Draught (30Lt)', 'Birra Moretti Draught'),
        ('D023', 'Lagunitas IPA', 'Lagunitas India Pale Ale'),
        ('D0006', 'OT Wild Orchard Draught', 'Orchard Thieves Wild Draught'),
    ]
    
    # MINERALS & SYRUPS - REMOVE "SPLIT" PREFIX
    split_removals = [
        ('M0007', 'Split 7up', 'Seven Up'),
        ('M0008', 'Split 7UP Diet', 'Seven Up Diet'),
        ('M0009', 'Split Coke', 'Coca Cola'),
        ('M0213', 'Split Coke 330ML', 'Coca Cola'),
        ('M0010', 'Split Coke Diet', 'Coca Cola Diet'),
        ('M0114', 'Split Fanta Lemon', 'Fanta Lemon'),
        ('M0012', 'Split Fanta Orange', 'Fanta Orange'),
        ('M0013', 'Split Friuce Juices', 'Fruit Juices'),
        ('M0014', 'Split Lucozade', 'Lucozade'),
        ('M0015', 'Split Pepsi', 'Pepsi'),
        ('M0016', 'Split Poachers Ginger Beer', 'Ginger Beer'),
        ('M0255', 'Split Sch', 'Schweppes'),
        ('M0122', 'Split Sch Elderflower', 'Schweppes Elderflower'),
        ('M0120', 'Split Sprite/Zero', 'Sprite Zero'),
        ('M0246', 'Splits Britvic Juices', 'Britvic Juices'),
    ]
    
    # MINERALS & SYRUPS - EXPAND ACRONYMS AND REMOVE SIZES
    acronym_expansions = [
        ('M0195', 'Baby SCH Mims', 'Baby Schweppes Miniatures'),
        ('M0258', 'Mixer Lemon Juice 700ML', 'Mixer Lemon Juice'),
        ('M0264', 'Mixer Lime Juice 700ML', 'Mixer Lime Juice'),
        ('M0265', 'Riverrock 750ml', 'Riverrock Water'),
    ]
    
    # MINERALS & SYRUPS - REMOVE "LTR"/"Lt" AND SIZES
    size_removals = [
        ('M0028', 'Monin Agave Syrup 700ml', 'Monin Agave Syrup'),
        ('M0035', 'Monin Chocolate Cookie LTR', 'Monin Chocolate Cookie Litre'),
        ('M0192', 'Monin Coconut Syrup 700ML', 'Monin Coconut Syrup'),
        ('M0038', 'Monin Elderflower Syrup 700ML', 'Monin Elderflower Syrup'),
        ('M0189', 'Monin Passionfruit Puree Ltr', 'Monin Passionfruit Puree Litre'),
        ('M0191', 'Monin Passionfruit Syrup 700ML', 'Monin Passionfruit Syrup'),
        ('M0227', 'Monin Pink Grapefruit 700ML', 'Monin Pink Grapefruit'),
        ('M0039', 'Monin Puree Coconut LTR', 'Monin Coconut Puree Litre'),
        ('M0040', 'Monin Strawberry Puree Ltr', 'Monin Strawberry Puree Litre'),
        ('M0041', 'Monin Strawberry Syrup 700ml', 'Monin Strawberry Syrup'),
        ('M0222', 'Monin Vanilla Syrup Ltr', 'Monin Vanilla Syrup Litre'),
        ('M0044', 'Monin Watermelon Syrup 700ML', 'Monin Watermelon Syrup'),
    ]
    
    # BIB - SIMPLIFY NAMES
    bib_updates = [
        ('M25', 'Splash Cola 18LTR', 'Splash Cola'),
        ('M24', 'Splash Energy18LTR', 'Splash Energy'),
        ('M23', 'Splash White18LTR', 'Splash White'),
    ]
    
    print("\n" + "="*80)
    print("COMPREHENSIVE PRODUCT NAME UPDATES")
    print("="*80)
    
    all_updates = [
        ("BOTTLED BEER", bottled_updates),
        ("DRAUGHT BEER", draught_updates),
        ("MINERALS - SPLIT REMOVALS", split_removals),
        ("MINERALS - ACRONYM EXPANSIONS", acronym_expansions),
        ("MINERALS - SIZE REMOVALS", size_removals),
        ("BIB - SIMPLIFIED NAMES", bib_updates),
    ]
    
    total_changes = 0
    for category, updates in all_updates:
        print(f"\n{category} ({len(updates)} items):")
        print("-" * 80)
        for sku, old_name, new_name in updates:
            print(f"  {sku}: {old_name}")
            print(f"       → {new_name}")
            total_changes += 1
    
    print("\n" + "="*80)
    print(f"TOTAL UPDATES: {total_changes} items")
    print("="*80)
    
    return all_updates


def apply_updates(all_updates):
    """Apply all name changes to database"""
    
    success_count = 0
    error_count = 0
    
    print("\n" + "="*80)
    print("APPLYING UPDATES...")
    print("="*80 + "\n")
    
    for category, updates in all_updates:
        print(f"\nProcessing {category}...")
        
        for sku, old_name, new_name in updates:
            try:
                item = StockItem.objects.get(sku=sku)
                
                if item.name != old_name:
                    print(f"  ⚠️  {sku}: Expected '{old_name}' but found '{item.name}'")
                    print(f"      Updating anyway to: {new_name}")
                
                item.name = new_name
                item.save()
                
                print(f"  ✓ {sku}: {new_name}")
                success_count += 1
                
            except StockItem.DoesNotExist:
                print(f"  ✗ {sku}: NOT FOUND - {old_name}")
                error_count += 1
            except Exception as e:
                print(f"  ✗ {sku}: ERROR - {str(e)}")
                error_count += 1
    
    print("\n" + "="*80)
    print(f"COMPLETE: {success_count} updated, {error_count} errors")
    print("="*80)


def main():
    all_updates = preview_updates()
    
    print("\n" + "="*80)
    response = input("Apply these changes? (yes/no): ").strip().lower()
    
    if response == 'yes':
        apply_updates(all_updates)
    else:
        print("\nNo changes made.")


if __name__ == '__main__':
    main()
