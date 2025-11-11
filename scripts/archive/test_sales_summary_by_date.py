"""
Test sales summary by DATE RANGE (not period)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Sale
from hotel.models import Hotel
from django.db.models import Q, Sum, Count
from datetime import date

print("=" * 80)
print("TEST: SALES SUMMARY BY DATE RANGE")
print("=" * 80)

# Get hotel
hotel = Hotel.objects.filter(
    Q(slug='hotel-killarney') | Q(subdomain='hotel-killarney')
).first()

if not hotel:
    print("❌ Hotel not found")
    exit()

print(f"\n🏨 Hotel: {hotel.name}\n")

# Get all sales for this hotel
all_sales = Sale.objects.filter(item__hotel=hotel)
print(f"📊 Total sales: {all_sales.count()}\n")

if not all_sales.exists():
    print("❌ No sales found")
    exit()

# Get date range from existing sales
earliest = all_sales.order_by('sale_date').first().sale_date
latest = all_sales.order_by('-sale_date').first().sale_date

print(f"📅 Date range in database:")
print(f"   From: {earliest}")
print(f"   To: {latest}\n")

# Test the query that the summary endpoint uses
print("=" * 80)
print(f"SALES SUMMARY: {earliest} to {latest}")
print("=" * 80)

# Filter by date range
sales_in_range = all_sales.filter(
    sale_date__gte=earliest,
    sale_date__lte=latest
)

print(f"\n✅ Sales in range: {sales_in_range.count()}\n")

# Group by category
sales_by_category = sales_in_range.values(
    'item__category__code',
    'item__category__name'
).annotate(
    total_quantity=Sum('quantity'),
    total_cost=Sum('total_cost'),
    total_revenue=Sum('total_revenue'),
    sale_count=Count('id')
).order_by('item__category__code')

print("BY CATEGORY:")
print("-" * 80)
for cat in sales_by_category:
    print(f"\n{cat['item__category__code']} - {cat['item__category__name']}")
    print(f"   Count: {cat['sale_count']}")
    print(f"   Quantity: {cat['total_quantity']}")
    print(f"   Revenue: €{cat['total_revenue']:,.2f}")
    print(f"   Cost: €{cat['total_cost']:,.2f}")
    
    profit = cat['total_revenue'] - cat['total_cost']
    print(f"   Profit: €{profit:,.2f}")
    
    if cat['total_revenue'] and cat['total_revenue'] > 0:
        gp_pct = (profit / cat['total_revenue']) * 100
        print(f"   GP%: {gp_pct:.2f}%")

# Overall totals
overall = sales_in_range.aggregate(
    total_quantity=Sum('quantity'),
    total_cost=Sum('total_cost'),
    total_revenue=Sum('total_revenue'),
    sale_count=Count('id')
)

print("\n" + "=" * 80)
print("OVERALL TOTALS")
print("=" * 80)
print(f"\nTotal Sales: {overall['sale_count']}")
print(f"Total Quantity: {overall['total_quantity']}")
print(f"Total Revenue: €{overall['total_revenue']:,.2f}")
print(f"Total Cost: €{overall['total_cost']:,.2f}")

profit = overall['total_revenue'] - overall['total_cost']
print(f"Gross Profit: €{profit:,.2f}")

if overall['total_revenue'] and overall['total_revenue'] > 0:
    gp_pct = (profit / overall['total_revenue']) * 100
    print(f"GP%: {gp_pct:.2f}%")

print("\n" + "=" * 80)
print("API ENDPOINT TO USE")
print("=" * 80)

hotel_id = hotel.slug or hotel.subdomain

print(f"\nGET /api/stock_tracker/{hotel_id}/sales/summary/")
print(f"    ?start_date={earliest}")
print(f"    &end_date={latest}")

print("\n" + "=" * 80)
