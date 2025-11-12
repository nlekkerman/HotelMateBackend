import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake

print("Deleting stocktake #22 and its lines...")

try:
    stocktake = Stocktake.objects.get(id=22)
    line_count = stocktake.lines.count()
    stocktake.delete()
    print(f"✅ Deleted stocktake #22 and {line_count} lines")
    print("\nNow recreate the stocktake via API and populate again!")
    print("The new populate will use the FIXED code and correct opening balances.")
except Stocktake.DoesNotExist:
    print("❌ Stocktake #22 not found")
