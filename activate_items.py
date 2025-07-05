import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")

import django
django.setup()

from stock_tracker.models import Stock, StockItem, StockInventory

def add_all_items_to_stock(hotel_id, category_slug):
    try:
        stock = Stock.objects.get(hotel_id=hotel_id, category__slug=category_slug)
    except Stock.DoesNotExist:
        print(f"❌ No stock found for hotel_id={hotel_id} and category_slug='{category_slug}'")
        return

    items = StockItem.objects.filter(hotel_id=hotel_id)

    count = 0
    for item in items:
        inventory, created = StockInventory.objects.get_or_create(
            stock=stock,
            item=item,
            defaults={"quantity": item.quantity}
        )
        if created:
            print(f"✔️ Added '{item.name}' to stock")
            count += 1

    print(f"\n✅ Done. {count} items added to inventory for stock '{stock}'.")

if __name__ == "__main__":
    # Adjust hotel_id and slug as needed
    add_all_items_to_stock(hotel_id=2, category_slug="bar-stock-category")
