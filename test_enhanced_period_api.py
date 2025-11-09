"""
Test: Enhanced Period API with Stocktake Info
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod
from stock_tracker.stock_serializers import StockPeriodSerializer
import json

print("\n" + "=" * 80)
print("ENHANCED PERIOD API - WITH STOCKTAKE INFO")
print("=" * 80)

# Get September 2025 as example
period = StockPeriod.objects.get(id=8)
serializer = StockPeriodSerializer(period)
data = serializer.data

print(f"\n📅 {data['period_name']}")
print(f"Period ID: {data['id']}")
print(f"Dates: {data['start_date']} to {data['end_date']}")
print(f"Is Closed: {data['is_closed']}")

print("\n💰 Financial Values:")
if data['manual_sales_amount']:
    print(f"Manual Sales: €{float(data['manual_sales_amount']):,.2f}")
if data['manual_purchases_amount']:
    print(f"Manual Purchases: €{float(data['manual_purchases_amount']):,.2f}")

if data['stocktake']:
    st = data['stocktake']
    print(f"\n📊 Stocktake Information:")
    print(f"Stocktake ID: {st['id']}")
    print(f"Status: {st['status']}")
    print(f"Total Items: {st['total_lines']}")
    print(f"Items Counted: {st['lines_counted']}")
    print(f"Items at Zero: {st['lines_at_zero']}")
    
    if st['total_cogs']:
        print(f"\nCOGS: €{st['total_cogs']:,.2f}")
    if st['total_revenue']:
        print(f"Revenue: €{st['total_revenue']:,.2f}")
    if st['gross_profit_percentage']:
        print(f"GP%: {st['gross_profit_percentage']:.2f}%")
    if st['pour_cost_percentage']:
        print(f"Pour Cost%: {st['pour_cost_percentage']:.2f}%")
else:
    print("\n⚠️  No stocktake exists for this period")

print("\n" + "=" * 80)
print("FRONTEND USAGE")
print("=" * 80)
print("""
// Get period with embedded stocktake info
const response = await fetch('/api/stock_tracker/hotel-killarney/periods/8/');
const period = await response.json();

console.log(period);
""")

# Print JSON for frontend reference
print("\nJSON Response Example:")
print("=" * 80)
stocktake_data = data['stocktake'].copy() if data['stocktake'] else None
if stocktake_data and stocktake_data.get('approved_at'):
    stocktake_data['approved_at'] = str(stocktake_data['approved_at'])

print(json.dumps({
    'id': data['id'],
    'period_name': data['period_name'],
    'start_date': data['start_date'],
    'end_date': data['end_date'],
    'is_closed': data['is_closed'],
    'stocktake_id': data['stocktake_id'],
    'stocktake': stocktake_data
}, indent=2))

print("\n" + "=" * 80)
print("FRONTEND ACCESS PATTERNS")
print("=" * 80)
print("""
// Check if stocktake exists
if (period.stocktake) {
  console.log(`Stocktake ID: ${period.stocktake.id}`);
  console.log(`Status: ${period.stocktake.status}`);
  console.log(`Items: ${period.stocktake.lines_counted}/${period.stocktake.total_lines}`);
  console.log(`GP%: ${period.stocktake.gross_profit_percentage}%`);
  
  // Get full stocktake details if needed
  const fullStocktake = await fetch(
    `/api/stock_tracker/hotel-killarney/stocktakes/${period.stocktake.id}/`
  ).then(r => r.json());
}

// Quick reference to stocktake ID (backward compatible)
const stocktakeId = period.stocktake_id; // or period.stocktake?.id
""")
print("=" * 80 + "\n")
