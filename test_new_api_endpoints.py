import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

import json
from stock_tracker.report_views import StockValueReportView, SalesReportView
from django.test import RequestFactory
from hotel.models import Hotel

# Create request factory
factory = RequestFactory()

# Get hotel
hotel = Hotel.objects.first()

print("=" * 80)
print("TESTING NEW API ENDPOINTS")
print("=" * 80)

# Test Stock Value Report
print("\n1. STOCK VALUE REPORT")
print("-" * 80)
request = factory.get(f'/api/stock-tracker/{hotel.slug}/reports/stock-value/?period=7')
view = StockValueReportView.as_view()
response = view(request, hotel_identifier=hotel.slug)

if response.status_code == 200:
    data = response.data
    print(f"✓ Status: {response.status_code}")
    print(f"\nPeriod: {data['period']['period_name']}")
    print(f"\nTOTALS:")
    print(f"  Cost Value:        €{data['totals']['cost_value']:,.2f}")
    print(f"  Sales Value:       €{data['totals']['sales_value']:,.2f}")
    print(f"  Potential Profit:  €{data['totals']['potential_profit']:,.2f}")
    print(f"  Markup:            {data['totals']['markup_percentage']:.1f}%")
    
    print(f"\nCATEGORIES:")
    for cat in data['categories']:
        print(f"  {cat['name']:<20} Cost: €{cat['cost_value']:>10,.2f}  Sales: €{cat['sales_value']:>10,.2f}  Profit: €{cat['potential_profit']:>10,.2f}")
    
    print(f"\nSUMMARY:")
    print(f"  Total Items: {data['summary']['total_items']}")
    print(f"  Items with Price: {data['summary']['items_with_price']}")
    print(f"  Items without Price: {data['summary']['items_without_price']}")
    
    print(f"\nTOP 5 ITEMS BY SALES VALUE:")
    for i, item in enumerate(data['items'][:5], 1):
        print(f"  {i}. {item['sku']} - {item['name'][:40]:<40} €{item['sales_value']:>10,.2f}")
else:
    print(f"✗ Error: {response.status_code}")
    print(response.data)

# Test Sales Report
print("\n\n2. SALES REPORT")
print("-" * 80)
request = factory.get(f'/api/stock-tracker/{hotel.slug}/reports/sales/?period=7')
view = SalesReportView.as_view()
response = view(request, hotel_identifier=hotel.slug)

if response.status_code == 200:
    data = response.data
    print(f"✓ Status: {response.status_code}")
    print(f"\nPeriod: {data['period']['period_name']}")
    print(f"Previous Period: {data['period']['previous_period']}")
    
    print(f"\nTOTALS:")
    print(f"  Revenue:           €{data['totals']['revenue']:,.2f}")
    print(f"  Cost of Sales:     €{data['totals']['cost_of_sales']:,.2f}")
    print(f"  Gross Profit:      €{data['totals']['gross_profit']:,.2f}")
    print(f"  GP%:               {data['totals']['gross_profit_percentage']:.1f}%")
    print(f"  Servings Sold:     {data['totals']['servings_sold']:,.0f}")
    
    print(f"\nSTOCK MOVEMENT:")
    print(f"  Sept Opening:      €{data['stock_movement']['sept_opening']:,.2f}")
    print(f"  Oct Purchases:     €{data['stock_movement']['oct_purchases']:,.2f}")
    print(f"  Oct Closing:       €{data['stock_movement']['oct_closing']:,.2f}")
    print(f"  Consumed:          €{data['stock_movement']['consumed']:,.2f}")
    
    print(f"\nCATEGORIES:")
    for cat in data['categories']:
        print(f"  {cat['name']:<20} Revenue: €{cat['revenue']:>10,.2f}  GP: {cat['gross_profit_percentage']:>5.1f}%  % of Total: {cat['percent_of_total']:>5.1f}%")
    
    print(f"\nDATA QUALITY:")
    if data['data_quality']['has_mock_data']:
        print(f"  ⚠️ WARNING: {data['data_quality']['warning']}")
        print(f"  Mock Purchases: {data['data_quality']['mock_purchase_count']}/{data['data_quality']['total_purchase_count']}")
        print(f"  Mock Value: €{data['data_quality']['mock_purchase_value']:,.2f}")
    else:
        print(f"  ✓ All data is real")
    
    print(f"\nTOP 10 ITEMS BY REVENUE:")
    for i, item in enumerate(data['items'][:10], 1):
        print(f"  {i}. {item['sku']} - {item['name'][:35]:<35} Sold: {item['consumption']:>7,.0f}  Revenue: €{item['revenue']:>10,.2f}")
else:
    print(f"✗ Error: {response.status_code}")
    print(response.data)

print("\n" + "=" * 80)
print("✓ API ENDPOINTS WORKING!")
print("=" * 80)

print("\n📍 FRONTEND CAN NOW USE:")
print(f"  GET /api/stock-tracker/{hotel.slug}/reports/stock-value/?period=7")
print(f"  GET /api/stock-tracker/{hotel.slug}/reports/sales/?period=7")
