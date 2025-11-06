"""
Update bin/location assignments for stock items
Run: python update_items_locations.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.db.models import Q
from stock_tracker.models import Location, StockItem
from hotel.models import Hotel


def update_stock_locations():
    """
    Update bin/location assignments for all stock items.
    
    NEW LOCATION STRUCTURE:
    1. "Spirit Storage" - Spirits, Whiskeys, Liqueurs, Fortified, Aperitifs
    2. "Keg Room" - All draught beers and ciders (kegs)
    3. "Mineral Storage" - Minerals, Bottled beers, Bottled ciders, RTDs
    4. "Wines" - All wine bottles
    """
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ No hotel found.")
            return
        print(f"✅ Using hotel: {hotel.name}\n")
    except Exception as e:
        print(f"❌ Error getting hotel: {e}")
        return

    # Create/Get new locations
    print("📍 Creating/updating locations...")
    spirit_storage, _ = Location.objects.get_or_create(
        hotel=hotel,
        name="Spirit Storage",
        defaults={'active': True}
    )
    print(f"  ✅ Spirit Storage")

    keg_room, _ = Location.objects.get_or_create(
        hotel=hotel,
        name="Keg Room",
        defaults={'active': True}
    )
    print(f"  ✅ Keg Room")

    mineral_storage, _ = Location.objects.get_or_create(
        hotel=hotel,
        name="Mineral Storage",
        defaults={'active': True}
    )
    print(f"  ✅ Mineral Storage")

    wines_location, _ = Location.objects.get_or_create(
        hotel=hotel,
        name="Wines",
        defaults={'active': True}
    )
    print(f"  ✅ Wines\n")

    # Update stock items
    print("📦 Updating stock item locations...\n")
    
    updated_count = 0
    error_count = 0

    # 1. Spirit Storage: SP (spirits/whiskey), LI (liqueurs), AP (aperitif), FO (fortified)
    print("🥃 Updating Spirit Storage items...")
    spirit_items = StockItem.objects.filter(
        hotel=hotel
    ).filter(
        Q(sku__startswith='SP') | 
        Q(sku__startswith='LI') | 
        Q(sku__startswith='AP') | 
        Q(sku__startswith='FO')
    )
    for item in spirit_items:
        try:
            item.bin = spirit_storage
            item.save()
            updated_count += 1
            print(f"  ✅ {item.sku} - {item.name}")
        except Exception as e:
            error_count += 1
            print(f"  ❌ Error updating {item.sku}: {e}")

    # 2. Keg Room: Draught beers and ciders (check for "Keg" in size)
    print("\n🍺 Updating Keg Room items...")
    keg_items = StockItem.objects.filter(
        hotel=hotel,
        size__icontains="Keg"
    )
    for item in keg_items:
        try:
            item.bin = keg_room
            item.save()
            updated_count += 1
            print(f"  ✅ {item.sku} - {item.name}")
        except Exception as e:
            error_count += 1
            print(f"  ❌ Error updating {item.sku}: {e}")

    # 3. Mineral Storage: MI (minerals), bottled BE/CI (check for "Btl"), RT (RTD)
    print("\n🥤 Updating Mineral Storage items...")
    
    # Get minerals
    mineral_items = StockItem.objects.filter(hotel=hotel, sku__startswith='MI')
    for item in mineral_items:
        try:
            item.bin = mineral_storage
            item.save()
            updated_count += 1
            print(f"  ✅ {item.sku} - {item.name}")
        except Exception as e:
            error_count += 1
            print(f"  ❌ Error updating {item.sku}: {e}")

    # Get bottled beers and ciders
    bottled_items = StockItem.objects.filter(
        hotel=hotel,
        name__istartswith='Btl'
    ).filter(
        Q(sku__startswith='BE') | Q(sku__startswith='CI')
    )
    for item in bottled_items:
        try:
            item.bin = mineral_storage
            item.save()
            updated_count += 1
            print(f"  ✅ {item.sku} - {item.name}")
        except Exception as e:
            error_count += 1
            print(f"  ❌ Error updating {item.sku}: {e}")

    # Get RTDs
    rtd_items = StockItem.objects.filter(hotel=hotel, sku__startswith='RT')
    for item in rtd_items:
        try:
            item.bin = mineral_storage
            item.save()
            updated_count += 1
            print(f"  ✅ {item.sku} - {item.name}")
        except Exception as e:
            error_count += 1
            print(f"  ❌ Error updating {item.sku}: {e}")

    # 4. Wines: WI items
    print("\n🍷 Updating Wines location...")
    wine_items = StockItem.objects.filter(hotel=hotel, sku__startswith='WI')
    for item in wine_items:
        try:
            item.bin = wines_location
            item.save()
            updated_count += 1
            print(f"  ✅ {item.sku} - {item.name}")
        except Exception as e:
            error_count += 1
            print(f"  ❌ Error updating {item.sku}: {e}")

    # Summary
    print(f"\n" + "="*60)
    print(f"📊 Summary:")
    print(f"   ✅ Updated: {updated_count}")
    print(f"   ❌ Errors: {error_count}")
    print("="*60)

    # Show location breakdown
    print(f"\n📍 Items per location:")
    print(f"   Spirit Storage: {StockItem.objects.filter(hotel=hotel, bin=spirit_storage).count()}")
    print(f"   Keg Room: {StockItem.objects.filter(hotel=hotel, bin=keg_room).count()}")
    print(f"   Mineral Storage: {StockItem.objects.filter(hotel=hotel, bin=mineral_storage).count()}")
    print(f"   Wines: {StockItem.objects.filter(hotel=hotel, bin=wines_location).count()}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("📍 Update Stock Item Locations")
    print("="*60 + "\n")
    update_stock_locations()
    print("\n✅ Script completed!\n")