"""
Test: Verify stocktake_id is included in Period API responses
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod
from stock_tracker.stock_serializers import StockPeriodSerializer

print("\n" + "=" * 80)
print("TEST: stocktake_id in Period API Response")
print("=" * 80)

# Get some periods
periods = StockPeriod.objects.all().order_by('-start_date')[:3]

for period in periods:
    serializer = StockPeriodSerializer(period)
    data = serializer.data
    
    print(f"\n{period.period_name}")
    print(f"   Period ID:    {data['id']}")
    print(f"   Stocktake ID: {data['stocktake_id']}")
    print(f"   Dates:        {data['start_date']} to {data['end_date']}")
    
    if data['stocktake_id']:
        print(f"   ✅ Stocktake exists")
    else:
        print(f"   ⚠️  No stocktake for this period")

print("\n" + "=" * 80)
print("FRONTEND USAGE:")
print("=" * 80)
print("""
Now frontend can simply do:

const period = await fetch('/api/stock_tracker/hotel-killarney/periods/8/')
  .then(r => r.json());

console.log(period.stocktake_id); // Returns: 8

if (period.stocktake_id) {
  const stocktake = await fetch(
    `/api/stock_tracker/hotel-killarney/stocktakes/${period.stocktake_id}/`
  ).then(r => r.json());
  
  console.log(`COGS: €${stocktake.total_cogs}`);
  console.log(`Revenue: €${stocktake.total_revenue}`);
  console.log(`GP%: ${stocktake.gross_profit_percentage}%`);
}
""")
print("=" * 80 + "\n")
