"""
Test what the sales endpoint returns
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Sale, StockItem
from hotel.models import Hotel
from django.db.models import Q

# Get hotel
hotel = Hotel.objects.filter(
    Q(slug='hotel-killarney') | Q(subdomain='hotel-killarney')
).first()

if not hotel:
    print("❌ Hotel 'hotel-killarney' not found")
    exit()

print(f"🏨 Hotel: {hotel.name} (ID: {hotel.id})")
print(f"   Slug: {hotel.slug}")
print(f"   Subdomain: {hotel.subdomain}\n")

# Test the query that the view uses
print("=" * 80)
print("TESTING SALES QUERY (same as API endpoint)")
print("=" * 80)

# This is exactly what the SaleViewSet.get_queryset() does
sales = Sale.objects.filter(
    item__hotel=hotel
).select_related('stocktake', 'item', 'created_by')

print(f"\n📊 Total sales found: {sales.count()}\n")

if sales.exists():
    print("Sample sales (first 5):\n")
    for sale in sales[:5]:
        print(f"ID: {sale.id}")
        print(f"  Item: {sale.item.sku} - {sale.item.name}")
        print(f"  Quantity: {sale.quantity}")
        print(f"  Sale Date: {sale.sale_date}")
        print(f"  Total Revenue: €{sale.total_revenue}")
        print(f"  Total Cost: €{sale.total_cost}")
        print(f"  Stocktake: {sale.stocktake.id if sale.stocktake else 'None (Standalone)'}")
        print(f"  Created: {sale.created_at}")
        print()
    
    # Show what the serializer would return
    print("=" * 80)
    print("SERIALIZED DATA (what API returns)")
    print("=" * 80)
    
    from stock_tracker.stock_serializers import SaleSerializer
    from rest_framework.request import Request
    from django.test import RequestFactory
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/api/stock_tracker/hotel-killarney/sales/')
    
    serializer = SaleSerializer(sales[:3], many=True, context={'request': request})
    
    import json
    print(json.dumps(serializer.data, indent=2, default=str))
    
else:
    print("❌ No sales found")
    print("\nChecking stock items for this hotel...")
    items = StockItem.objects.filter(hotel=hotel)
    print(f"   Stock items for hotel: {items.count()}")
    
    if items.exists():
        print("\nChecking if any sales exist for these items...")
        all_sales = Sale.objects.filter(item__in=items)
        print(f"   Sales for hotel's items: {all_sales.count()}")
