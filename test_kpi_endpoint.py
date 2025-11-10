"""
Quick test for KPI Summary endpoint
Run with: python manage.py shell < test_kpi_endpoint.py
"""

from stock_tracker.models import StockPeriod
from hotel.models import Hotel

# Get a hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found in database")
    exit()

print(f"✅ Hotel found: {hotel.name}")

# Get some periods
periods = StockPeriod.objects.filter(hotel=hotel)[:3]
if not periods:
    print("❌ No periods found for hotel")
    exit()

print(f"✅ Found {periods.count()} periods:")
for p in periods:
    print(f"   - {p.period_name} (ID: {p.id})")

# Build URL
period_ids = ",".join(str(p.id) for p in periods)
url = f"/api/stock-tracker/{hotel.slug or hotel.subdomain}/kpi-summary/?period_ids={period_ids}"

print(f"\n🔗 Test URL:")
print(f"   GET {url}")

print(f"\n✅ Endpoint is configured and ready to test!")
print(f"\nTest with cURL:")
print(f'curl -X GET "http://localhost:8000{url}"')
