import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel
from stock_tracker.models import StockItem

hotel = Hotel.objects.first()
if not hotel:
    print('No hotel')
    exit(1)

items = StockItem.objects.filter(hotel=hotel)

errors = []
for it in items:
    if it.menu_price and it.menu_price > 0:
        try:
            _ = float(it.unit_cost)
            _ = float(it.menu_price)
            _ = float(it.cost_per_serving)
            _ = float(it.gross_profit_per_serving)
            _ = float(it.gross_profit_percentage)
            _ = float(it.markup_percentage)
            _ = float(it.pour_cost_percentage)
            _ = float(it.total_stock_value)
        except Exception as e:
            errors.append((it.sku, str(e)))
            # print and continue
            print('Error on', it.sku, repr(e))

print('\nChecked', items.count(), 'items')
print('Errors found:', len(errors))
if errors:
    for sku, err in errors[:20]:
        print(sku, err)
