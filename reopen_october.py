"""
Reopen October 2025 stocktake
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake

# Reopen October 2025 stocktake
stocktake = Stocktake.objects.get(id=5)

print(f"\nCurrent Status: {stocktake.status}")
print(f"Approved At: {stocktake.approved_at}")

stocktake.status = Stocktake.DRAFT
stocktake.approved_at = None
stocktake.approved_by = None
stocktake.save()

print(f"\n✅ New Status: {stocktake.status}")
print(f"✅ Approved At: {stocktake.approved_at}")
print(f"\n✅ October 2025 is now reopened and editable!\n")
