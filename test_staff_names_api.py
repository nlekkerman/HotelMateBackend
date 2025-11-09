import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod
from stock_tracker.stock_serializers import StockPeriodSerializer
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

print("\n" + "="*80)
print("TESTING STAFF NAME SERIALIZATION")
print("="*80 + "\n")

# Get October period
period = StockPeriod.objects.get(period_name="October 2025")

# Create fake request for context
factory = RequestFactory()
request = factory.get('/')
request.user = AnonymousUser()

# Serialize
serializer = StockPeriodSerializer(period, context={'request': request})
data = serializer.data

print("API Response Fields for Staff:")
print("-" * 80)
print(f"\nclosed_by (ID): {data.get('closed_by')}")
print(f"closed_by_name: {data.get('closed_by_name')}")
print(f"\nreopened_by (ID): {data.get('reopened_by')}")
print(f"reopened_by_name: {data.get('reopened_by_name')}")

print("\n" + "="*80)
print("FRONTEND USAGE")
print("="*80)
print("""
// Fetch period
const period = await fetch('/api/periods/7/').then(r => r.json());

// Display who closed it
if (period.closed_by_name) {
  console.log(`Closed by: ${period.closed_by_name}`);
  // Shows: "Nikola Simic - Front Office - Porter"
}

// Display who reopened it
if (period.reopened_by_name) {
  console.log(`Reopened by: ${period.reopened_by_name}`);
  // Shows: "Nikola Simic - Front Office - Porter"
}

// Example in UI:
<div>
  <p>Closed: {formatDate(period.closed_at)}</p>
  <p>By: {period.closed_by_name}</p>
</div>
""")
print("="*80 + "\n")
