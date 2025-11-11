"""
Test creating sales with MONTH parameter
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Sale, StockItem
from hotel.models import Hotel
from django.db.models import Q

print("=" * 80)
print("TEST: CREATE SALES WITH MONTH PARAMETER")
print("=" * 80)

# Get hotel
hotel = Hotel.objects.filter(
    Q(slug='hotel-killarney') | Q(subdomain='hotel-killarney')
).first()

if not hotel:
    print("❌ Hotel not found")
    exit()

print(f"\n🏨 Hotel: {hotel.name}\n")

# Get a stock item to use
item = StockItem.objects.filter(hotel=hotel).first()

if not item:
    print("❌ No stock items found")
    exit()

print(f"📦 Using item: {item.sku} - {item.name}")
print(f"   Cost per serving: €{item.cost_per_serving}")
print(f"   Menu price: €{item.menu_price}\n")

# Test creating sale with month parameter
from stock_tracker.stock_serializers import SaleSerializer
from decimal import Decimal

print("=" * 80)
print("CREATING SALE FOR SEPTEMBER 2025")
print("=" * 80)

# Simulate creating a sale with month="2025-09"
sale_data = {
    'item': item.id,
    'quantity': Decimal('100.0000'),
    'unit_cost': item.cost_per_serving,
    'unit_price': item.menu_price,
    'notes': 'Test sale for September'
}

# Pass month in context
context = {'month': '2025-09'}
serializer = SaleSerializer(data=sale_data, context=context)

if serializer.is_valid():
    sale = serializer.save()
    print(f"\n✅ Sale created successfully!")
    print(f"   ID: {sale.id}")
    print(f"   Item: {sale.item.sku} - {sale.item.name}")
    print(f"   Quantity: {sale.quantity}")
    print(f"   Sale Date: {sale.sale_date}")  # Should be 2025-09-01
    print(f"   Total Cost: €{sale.total_cost}")
    print(f"   Total Revenue: €{sale.total_revenue}")
    print(f"   Created: {sale.created_at}")
else:
    print(f"\n❌ Validation errors: {serializer.errors}")

# Now test querying by month
print("\n" + "=" * 80)
print("QUERYING SALES FOR SEPTEMBER 2025")
print("=" * 80)

from datetime import datetime
from calendar import monthrange

month = "2025-09"
year, month_num = map(int, month.split('-'))
start_date = datetime(year, month_num, 1).date()
last_day = monthrange(year, month_num)[1]
end_date = datetime(year, month_num, last_day).date()

september_sales = Sale.objects.filter(
    item__hotel=hotel,
    sale_date__gte=start_date,
    sale_date__lte=end_date
)

print(f"\n📅 Date range: {start_date} to {end_date}")
print(f"✅ Found {september_sales.count()} sales for September\n")

for sale in september_sales:
    print(f"  - {sale.item.sku}: {sale.quantity} units on {sale.sale_date}")

print("\n" + "=" * 80)
print("API USAGE EXAMPLES")
print("=" * 80)

hotel_id = hotel.slug or hotel.subdomain

print(f"\n1. CREATE sale for September:")
print(f"   POST /api/stock_tracker/{hotel_id}/sales/")
print(f"   Body: {{\n     \"item\": {item.id},")
print(f"     \"quantity\": 100,")
print(f"     \"month\": \"2025-09\",  ← SELECT MONTH")
print(f"     \"notes\": \"September sales\"\n   }}")

print(f"\n2. GET sales for September:")
print(f"   GET /api/stock_tracker/{hotel_id}/sales/?month=2025-09")

print(f"\n3. GET sales summary for September:")
print(f"   GET /api/stock_tracker/{hotel_id}/sales/summary/?start_date=2025-09-01&end_date=2025-09-30")

print("\n" + "=" * 80)

# Clean up - delete test sale
if 'sale' in locals():
    sale_id = sale.id
    sale.delete()
    print(f"\n🧹 Cleaned up test sale (ID: {sale_id})")
