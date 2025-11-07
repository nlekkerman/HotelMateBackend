import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from stock_tracker.stock_serializers import (
    StockPeriodSerializer, 
    StockSnapshotSerializer
)

# Fetch Period 2 (October 2025)
try:
    period = StockPeriod.objects.get(id=2)
    period_serializer = StockPeriodSerializer(period)
    
    # Get all snapshots for this period
    snapshots = StockSnapshot.objects.filter(
        period=period
    ).select_related('item', 'item__category')
    snapshot_serializer = StockSnapshotSerializer(snapshots, many=True)
    
    # Combine into single response (like API does)
    data = period_serializer.data
    data['snapshots'] = snapshot_serializer.data
    
    print("=" * 80)
    print("📊 OCTOBER 2025 PERIOD - COMPLETE ANALYTICS")
    print("=" * 80)
    print(f"\n✅ Period: {data['period_name']}")
    print(f"📅 Date Range: {data['start_date']} to {data['end_date']}")
    print(f"🔒 Status: {'CLOSED' if data['is_closed'] else 'OPEN'}")
    print(f"📦 Total Items: {len(data['snapshots'])}")
    
    # Calculate totals
    total_value = sum(
        float(s['closing_stock_value']) for s in data['snapshots']
    )
    total_quantity = sum(
        float(s['total_servings']) for s in data['snapshots']
    )
    
    print(f"💰 Total Stock Value: €{total_value:,.2f}")
    print(f"📊 Total Quantity: {total_quantity:,.2f} units")
    
    print("\n" + "=" * 80)
    print("📋 SAMPLE ITEMS (First 10)")
    print("=" * 80)
    
    for i, snapshot in enumerate(data['snapshots'][:10], 1):
        item = snapshot['item']
        print(f"\n{i}. {item['name']} ({item['sku']})")
        print(f"   Category: {item['category_display']}")
        print(f"   Size: {item['size']}")
        print(f"   Cost: €{item['unit_cost']} | Price: €{item['menu_price']}")
        full = snapshot['closing_full_units']
        partial = snapshot['closing_partial_units']
        total = snapshot['total_servings']
        print(f"   Stock: {full} full + {partial} partial = {total} total")
        print(f"   Value: €{snapshot['closing_stock_value']}")
        gp = snapshot['gp_percentage']
        markup = snapshot['markup_percentage']
        pour = snapshot['pour_cost_percentage']
        print(f"   GP: {gp}% | Markup: {markup}% | Pour Cost: {pour}%")
    
    print("\n" + "=" * 80)
    print("📊 ANALYTICS BY CATEGORY")
    print("=" * 80)
    
    # Group by category
    from collections import defaultdict
    by_category = defaultdict(lambda: {'count': 0, 'value': 0, 'qty': 0})
    
    for snapshot in data['snapshots']:
        cat = snapshot['item']['category_display']
        by_category[cat]['count'] += 1
        by_category[cat]['value'] += float(snapshot['closing_stock_value'])
        by_category[cat]['qty'] += float(snapshot['total_quantity'])
    
    for cat, stats in sorted(by_category.items()):
        print(f"\n{cat}:")
        print(f"  Items: {stats['count']}")
        print(f"  Total Quantity: {stats['qty']:,.2f}")
        print(f"  Total Value: €{stats['value']:,.2f}")
    
    print("\n" + "=" * 80)
    print("💎 TOP 10 HIGHEST VALUE ITEMS")
    print("=" * 80)
    
    top_items = sorted(data['snapshots'], 
                      key=lambda x: float(x['closing_stock_value']), 
                      reverse=True)[:10]
    
    for i, snapshot in enumerate(top_items, 1):
        item = snapshot['item']
        qty = snapshot['total_servings']
        val = snapshot['closing_stock_value']
        print(f"{i}. {item['name'][:30]:30} | Qty: {qty:>8.2f} | €{val:>10}")
    
    print("\n" + "=" * 80)
    print("📈 PROFITABILITY INSIGHTS")
    print("=" * 80)
    
    # Calculate average GP%
    avg_gp = sum(float(s['gp_percentage']) for s in data['snapshots']) / len(data['snapshots'])
    avg_markup = sum(float(s['markup_percentage']) for s in data['snapshots']) / len(data['snapshots'])
    
    print(f"\nAverage GP%: {avg_gp:.2f}%")
    print(f"Average Markup%: {avg_markup:.2f}%")
    
    # Find best/worst GP
    best_gp = max(data['snapshots'], key=lambda x: float(x['gp_percentage']))
    worst_gp = min(data['snapshots'], key=lambda x: float(x['gp_percentage']))
    
    print(f"\n✅ Best GP: {best_gp['item']['name']} ({best_gp['gp_percentage']}%)")
    print(f"❌ Worst GP: {worst_gp['item']['name']} ({worst_gp['gp_percentage']}%)")
    
    print("\n" + "=" * 80)
    print("✅ ALL DATA AVAILABLE IN API RESPONSE")
    print("=" * 80)
    
except StockPeriod.DoesNotExist:
    print("❌ Period 2 not found!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
