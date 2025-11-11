"""
Test sales filtering by date range
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Sale, Stocktake
from hotel.models import Hotel
from django.db.models import Count, Sum
from decimal import Decimal
from datetime import date

print("=" * 80)
print("TEST: SALES DATE FILTERING")
print("=" * 80)

# Get a hotel to test with
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found in database")
    exit()

print(f"\n🏨 Testing with hotel: {hotel.name}")
print(f"   Identifier: {hotel.slug or hotel.subdomain}\n")

# Get all sales - filter by item's hotel to include standalone sales
all_sales = Sale.objects.filter(item__hotel=hotel)
total_count = all_sales.count()

print(f"📊 Total sales for this hotel: {total_count}\n")

if total_count == 0:
    print("❌ No sales found for this hotel")
    exit()

# Show sales grouped by date
print("=" * 80)
print("SALES BY DATE")
print("=" * 80)

sales_by_date = all_sales.values('sale_date').annotate(
    count=Count('id'),
    total_revenue=Sum('total_revenue'),
    total_cost=Sum('total_cost')
).order_by('sale_date')

for idx, date_group in enumerate(sales_by_date, 1):
    sale_date = date_group['sale_date']
    count = date_group['count']
    revenue = date_group['total_revenue'] or Decimal('0.00')
    cost = date_group['total_cost'] or Decimal('0.00')
    profit = revenue - cost
    
    print(f"\n{idx}. 📅 {sale_date}")
    print(f"   Sales Count: {count}")
    print(f"   Revenue: €{revenue:,.2f}")
    print(f"   Cost: €{cost:,.2f}")
    print(f"   Profit: €{profit:,.2f}")

# Test date range filtering
print("\n" + "=" * 80)
print("TEST: DATE RANGE FILTERING")
print("=" * 80)

# Get earliest and latest dates
earliest_sale = all_sales.order_by('sale_date').first()
latest_sale = all_sales.order_by('-sale_date').first()

if earliest_sale and latest_sale:
    earliest_date = earliest_sale.sale_date
    latest_date = latest_sale.sale_date
    
    print(f"\n📅 Date range in database:")
    print(f"   Earliest: {earliest_date}")
    print(f"   Latest: {latest_date}")
    
    # Test 1: Filter to get all sales
    print(f"\n🔍 Test 1: All sales (no filter)")
    filtered_all = Sale.objects.filter(item__hotel=hotel)
    print(f"   Result: {filtered_all.count()} sales")
    
    # Test 2: Filter by start_date only
    print(f"\n🔍 Test 2: Sales from {earliest_date} onwards")
    filtered_from = Sale.objects.filter(
        item__hotel=hotel,
        sale_date__gte=earliest_date
    )
    print(f"   Result: {filtered_from.count()} sales")
    
    # Test 3: Filter by end_date only
    print(f"\n🔍 Test 3: Sales up to {latest_date}")
    filtered_to = Sale.objects.filter(
        item__hotel=hotel,
        sale_date__lte=latest_date
    )
    print(f"   Result: {filtered_to.count()} sales")
    
    # Test 4: Filter by date range
    print(f"\n🔍 Test 4: Sales between {earliest_date} and {latest_date}")
    filtered_range = Sale.objects.filter(
        item__hotel=hotel,
        sale_date__gte=earliest_date,
        sale_date__lte=latest_date
    )
    print(f"   Result: {filtered_range.count()} sales")
    
    # Test 5: Filter for a specific month (if October 2025 exists)
    oct_start = date(2025, 10, 1)
    oct_end = date(2025, 10, 31)
    
    print(f"\n🔍 Test 5: Sales in October 2025")
    filtered_october = Sale.objects.filter(
        item__hotel=hotel,
        sale_date__gte=oct_start,
        sale_date__lte=oct_end
    )
    print(f"   Result: {filtered_october.count()} sales")
    
    if filtered_october.exists():
        oct_totals = filtered_october.aggregate(
            revenue=Sum('total_revenue'),
            cost=Sum('total_cost')
        )
        print(f"   Revenue: €{oct_totals['revenue']:,.2f}")
        print(f"   Cost: €{oct_totals['cost']:,.2f}")

print("\n" + "=" * 80)
print("✅ API ENDPOINT EXAMPLES")
print("=" * 80)

hotel_id = hotel.slug or hotel.subdomain

print(f"\n1. All sales for hotel:")
print(f"   GET /api/stock-tracker/{hotel_id}/sales/")

print(f"\n2. Sales from specific date:")
print(f"   GET /api/stock-tracker/{hotel_id}/sales/?start_date=2025-10-01")

print(f"\n3. Sales up to specific date:")
print(f"   GET /api/stock-tracker/{hotel_id}/sales/?end_date=2025-10-31")

print(f"\n4. Sales in date range:")
print(f"   GET /api/stock-tracker/{hotel_id}/sales/?start_date=2025-10-01&end_date=2025-10-31")

print(f"\n5. Sales for specific item in date range:")
print(f"   GET /api/stock-tracker/{hotel_id}/sales/?item=123&start_date=2025-10-01&end_date=2025-10-31")

print(f"\n6. Sales by category in date range:")
print(f"   GET /api/stock-tracker/{hotel_id}/sales/?category=D&start_date=2025-10-01&end_date=2025-10-31")

print("\n" + "=" * 80)
