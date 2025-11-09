import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod

print("\n" + "="*80)
print("CHECKING PERIOD STAFF FIELDS")
print("="*80 + "\n")

period = StockPeriod.objects.get(period_name="October 2025")

print(f"Period: {period.period_name}")
print(f"Is Closed: {period.is_closed}")
print(f"\nClosed By (object): {period.closed_by}")
print(f"Closed By (type): {type(period.closed_by)}")
if period.closed_by:
    print(f"Closed By (name): {period.closed_by.user.get_full_name() or period.closed_by.user.username}")
    print(f"Closed By (username): {period.closed_by.user.username}")

print(f"\nReopened By (object): {period.reopened_by}")
if period.reopened_by:
    print(f"Reopened By (name): {period.reopened_by.user.get_full_name() or period.reopened_by.user.username}")
    print(f"Reopened By (username): {period.reopened_by.user.username}")

print("\n" + "="*80)
print("WHAT SERIALIZER SHOULD RETURN")
print("="*80)
print("""
Instead of:
  "closed_by": 1  (just ID)
  "reopened_by": 1  (just ID)

Should return:
  "closed_by": "Nikola Simic"
  "reopened_by": "Nikola Simic"

Or:
  "closed_by": {
    "id": 1,
    "username": "nikola",
    "full_name": "Nikola Simic"
  }
""")
print("="*80 + "\n")
