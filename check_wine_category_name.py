"""
Check Wine category name in database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockCategory

# Check Wine category
wine_cat = StockCategory.objects.filter(code='W').first()

if wine_cat:
    print(f"Wine Category (W):")
    print(f"  Code: {wine_cat.code}")
    print(f"  Name: {wine_cat.name}")
else:
    print("Wine category not found!")

# Show all categories
print("\nAll Categories:")
print("-" * 40)
for cat in StockCategory.objects.all():
    print(f"  {cat.code}: {cat.name}")
