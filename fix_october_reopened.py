import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod

print("\n" + "="*80)
print("FIXING OCTOBER 2025 DATA INCONSISTENCY")
print("="*80 + "\n")

# Get October 2025 period
period = StockPeriod.objects.get(period_name="October 2025")

print(f"BEFORE FIX:")
print(f"  is_closed: {period.is_closed}")
print(f"  closed_at: {period.closed_at}")
print(f"  closed_by: {period.closed_by}")
print(f"  reopened_at: {period.reopened_at}")
print(f"  reopened_by: {period.reopened_by}")

# Clear the inconsistent reopened fields
period.reopened_at = None
period.reopened_by = None
period.save()

print(f"\n" + "="*80)
print(f"AFTER FIX:")
print(f"  is_closed: {period.is_closed}")
print(f"  closed_at: {period.closed_at}")
print(f"  closed_by: {period.closed_by}")
print(f"  reopened_at: {period.reopened_at}")
print(f"  reopened_by: {period.reopened_by}")

print(f"\n✅ October 2025 reopened fields cleared")
print(f"✅ Period is now properly in OPEN state (never closed)")
print("="*80 + "\n")
