"""
Fix S45 (Primitivo Giola Colle wine) - Change SKU to W45
"""

import os
import sys
import django
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockCategory, StockSnapshot, StockPeriod
from hotel.models import Hotel


def main():
    print("=" * 60)
    print("FIX S45 -> W45 (Primitivo Giola Colle)")
    print("=" * 60)
    
    hotel = Hotel.objects.first()
    
    # Get the item
    try:
        item = StockItem.objects.get(hotel=hotel, sku='S45')
        print(f"\n✅ Found item:")
        print(f"   Current SKU: {item.sku}")
        print(f"   Name: {item.name}")
        print(f"   Current Category: {item.category.code} - {item.category.name}")
        
        # Get Wine category (no hotel filter)
        wine_cat = StockCategory.objects.get(code='W')
        
        # Update SKU and category
        old_sku = item.sku
        item.sku = 'W45'
        item.category = wine_cat
        item.save()
        
        print(f"\n✅ Updated:")
        print(f"   New SKU: {item.sku}")
        print(f"   New Category: {item.category.code} - {item.category.name}")
        
        # Check if snapshot exists
        period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)
        snapshot = StockSnapshot.objects.filter(
            hotel=hotel,
            item=item,
            period=period
        ).first()
        
        if snapshot:
            print(f"\n📊 October 2024 Snapshot:")
            print(f"   Full units: {snapshot.closing_full_units}")
            print(f"   Partial: {snapshot.closing_partial_units}")
            print(f"   Value: €{snapshot.closing_stock_value}")
        
        print(f"\n🎉 SUCCESS! S45 changed to W45 and moved to Wines category")
        
    except StockItem.DoesNotExist:
        print(f"\n❌ Item S45 not found!")
        print(f"   Maybe it was already changed to W45?")
        
        # Check for W45
        try:
            item = StockItem.objects.get(hotel=hotel, sku='W45')
            print(f"\n✅ Found W45:")
            print(f"   SKU: {item.sku}")
            print(f"   Name: {item.name}")
            print(f"   Category: {item.category.code} - {item.category.name}")
        except StockItem.DoesNotExist:
            print(f"   W45 also not found.")


if __name__ == '__main__':
    main()
