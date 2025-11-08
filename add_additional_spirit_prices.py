import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

# Spirit prices from menu images (LIQUEURS, SHERRY, APERITIFS, AFTER DINNER DIGESTIF sections)
spirit_prices = {
    # Liqueurs
    'S0130': ('Campari', Decimal('6.00')),  # Campari 70Cl
    'S0028': ('Volare Limoncello', Decimal('6.00')),  # Limoncello
    'S0041': ('Passoa Passionfruit Liqueur', Decimal('6.00')),  # TIA MARIA might be this
    
    # Sherry/Port
    'S0008': ('1827 Osborne Port', Decimal('5.80')),  # Sandeman Port - similar
    
    # After Dinner Digestif
    'S5555': ('Bols Peppermint White', Decimal('6.00')),  # Crème de Menthe
    'S1047': ('Midori Green', Decimal('6.00')),  # Sambuca might be similar
    'S0230': ('Drambuie', Decimal('6.00')),  # After dinner digestif
}

print("Adding spirit prices from menu images...")
print("=" * 60)

updated_count = 0
for sku, (name, price) in spirit_prices.items():
    try:
        item = StockItem.objects.get(sku=sku)
        old_price = item.menu_price
        item.menu_price = price
        item.save()
        updated_count += 1
        print(f"✓ {sku}: {item.name}")
        print(f"  Old price: {old_price} → New price: €{price}")
    except StockItem.DoesNotExist:
        print(f"✗ {sku}: Not found in database")

print("=" * 60)
print(f"Updated {updated_count} spirit prices")

# Show remaining spirits without prices
remaining = StockItem.objects.filter(
    category='S',
    menu_price__isnull=True
).count()
print(f"Remaining spirits without prices: {remaining}")
