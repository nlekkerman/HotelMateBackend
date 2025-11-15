"""
Update Teisseire Bubble Gum to SYRUPS subcategory
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

item = StockItem.objects.get(sku='M0012')

print(f'Item: {item.sku} - {item.name}')
print(f'Size: {item.size}')
print(f'Current UOM: {item.uom}')
print(f'Current Subcategory: {item.subcategory}')
print()

# Teisseire is a syrup brand - should be SYRUPS
# Assuming 700ml bottle (standard syrup size)
item.subcategory = 'SYRUPS'
item.uom = Decimal('700.00')  # 700ml per bottle
item.save()

print('✓ Updated:')
print(f'  Subcategory: {item.subcategory}')
print(f'  UOM: {item.uom}ml (bottle size)')
print()
print('Teisseire Bubble Gum is now properly categorized as SYRUPS!')
