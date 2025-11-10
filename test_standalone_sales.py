"""
Test Script: Standalone Sales (No Stocktake Link) + Optional Merge
Tests the updated sales entry system with optional stocktake linking.

Run with: python test_standalone_sales.py
"""

import os
import django
import random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from datetime import date
from django.contrib.auth import get_user_model
from hotel.models import Hotel
from stock_tracker.models import StockItem, Stocktake, Sale, StockPeriod

User = get_user_model()


def test_standalone_sales():
    """
    Test sales entry with optional stocktake linking:
    1. Save standalone sales (NO stocktake)
    2. Save sales linked to stocktake
    3. Update standalone sales to link later
    4. Verify separation and merging
    """
    
    print("\n" + "="*80)
    print("🔓 TESTING OPTIONAL STOCKTAKE LINKING")
    print("="*80 + "\n")
    
    # Setup
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found!")
        return
    
    print(f"🏨 Hotel: {hotel.name}\n")
    
    # Get some items
    items = list(StockItem.objects.filter(
        hotel=hotel,
        active=True,
        available_on_menu=True
    )[:5])
    
    if len(items) < 5:
        print("❌ Not enough items for test")
        return
    
    # Create stocktake for later linking
    period_start = date(2025, 11, 1)
    period_end = date(2025, 11, 10)
    
    stocktake, _ = Stocktake.objects.get_or_create(
        hotel=hotel,
        period_start=period_start,
        period_end=period_end,
        defaults={'status': Stocktake.DRAFT}
    )
    
    print(f"📊 Stocktake created: ID {stocktake.id}\n")
    
    # Clear any existing sales
    Sale.objects.filter(item__hotel=hotel).delete()
    print("✅ Cleared existing sales\n")
    
    # =========================================================================
    # TEST 1: Create STANDALONE Sales (No Stocktake Link)
    # =========================================================================
    
    print("="*80)
    print("TEST 1: Create Standalone Sales (NO Stocktake)")
    print("="*80)
    
    standalone_sales = []
    for item in items[:3]:
        qty = Decimal(str(random.randint(10, 50)))
        sale = Sale(
            item=item,
            # NO stocktake field!
            quantity=qty,
            unit_cost=item.cost_per_serving,
            unit_price=item.menu_price,
            sale_date=period_end
        )
        sale.save()
        standalone_sales.append(sale)
        
        print(f"Created: {item.sku} - Qty: {qty} - NO STOCKTAKE LINK")
    
    print(f"\n✅ Created {len(standalone_sales)} standalone sales\n")
    
    # Verify they're NOT linked
    for sale in standalone_sales:
        sale.refresh_from_db()
        if sale.stocktake:
            print(f"❌ FAIL: Sale {sale.id} has stocktake link!")
            return False
        else:
            print(f"✅ Sale {sale.id}: No stocktake (as expected)")
    
    print()
    
    # =========================================================================
    # TEST 2: Stocktake Should NOT Include Standalone Sales
    # =========================================================================
    
    print("="*80)
    print("TEST 2: Verify Stocktake EXCLUDES Standalone Sales")
    print("="*80)
    
    stocktake.refresh_from_db()
    stocktake_sales_count = stocktake.sales.count()
    stocktake_revenue = stocktake.total_revenue
    
    print(f"Stocktake sales count: {stocktake_sales_count}")
    print(f"Stocktake total revenue: €{stocktake_revenue}\n")
    
    if stocktake_sales_count == 0:
        print("✅ PASS: Stocktake has 0 sales (standalone not included)")
    else:
        print("❌ FAIL: Stocktake should have 0 sales!")
        return False
    
    print()
    
    # =========================================================================
    # TEST 3: Create Sales LINKED to Stocktake
    # =========================================================================
    
    print("="*80)
    print("TEST 3: Create Sales WITH Stocktake Link")
    print("="*80)
    
    linked_sales = []
    for item in items[3:5]:
        qty = Decimal(str(random.randint(20, 60)))
        sale = Sale(
            item=item,
            stocktake=stocktake,  # LINKED!
            quantity=qty,
            unit_cost=item.cost_per_serving,
            unit_price=item.menu_price,
            sale_date=period_end
        )
        sale.save()
        linked_sales.append(sale)
        
        print(f"Created: {item.sku} - Qty: {qty} - LINKED to Stocktake {stocktake.id}")
    
    print(f"\n✅ Created {len(linked_sales)} linked sales\n")
    
    # =========================================================================
    # TEST 4: Verify Stocktake NOW Includes Linked Sales ONLY
    # =========================================================================
    
    print("="*80)
    print("TEST 4: Verify Stocktake Includes ONLY Linked Sales")
    print("="*80)
    
    stocktake.refresh_from_db()
    stocktake_sales_count = stocktake.sales.count()
    stocktake_revenue = stocktake.total_revenue
    
    print(f"Standalone sales: {len(standalone_sales)}")
    print(f"Linked sales: {len(linked_sales)}")
    print(f"Stocktake sales count: {stocktake_sales_count}")
    print(f"Stocktake total revenue: €{stocktake_revenue}\n")
    
    if stocktake_sales_count == len(linked_sales):
        print(f"✅ PASS: Stocktake has {len(linked_sales)} sales (linked only)")
    else:
        print(f"❌ FAIL: Expected {len(linked_sales)}, got {stocktake_sales_count}")
        return False
    
    # Calculate expected revenue from linked sales
    expected_revenue = sum(s.total_revenue or Decimal('0') for s in linked_sales)
    print(f"Expected revenue: €{expected_revenue}")
    print(f"Actual revenue:   €{stocktake_revenue}")
    
    if abs(expected_revenue - stocktake_revenue) < Decimal('0.02'):
        print("✅ PASS: Revenue matches\n")
    else:
        print("❌ FAIL: Revenue mismatch\n")
        return False
    
    # =========================================================================
    # TEST 5: Link Standalone Sales to Stocktake (Update)
    # =========================================================================
    
    print("="*80)
    print("TEST 5: Link Standalone Sales to Stocktake (Later)")
    print("="*80)
    
    # Update first standalone sale to link it
    sale_to_link = standalone_sales[0]
    print(f"Updating Sale {sale_to_link.id} to link to Stocktake {stocktake.id}...")
    
    sale_to_link.stocktake = stocktake
    sale_to_link.save()
    sale_to_link.refresh_from_db()
    
    if sale_to_link.stocktake == stocktake:
        print("✅ Sale linked successfully\n")
    else:
        print("❌ FAIL: Sale not linked\n")
        return False
    
    # =========================================================================
    # TEST 6: Verify Stocktake NOW Includes the Newly Linked Sale
    # =========================================================================
    
    print("="*80)
    print("TEST 6: Verify Stocktake Includes Newly Linked Sale")
    print("="*80)
    
    stocktake.refresh_from_db()
    new_sales_count = stocktake.sales.count()
    new_revenue = stocktake.total_revenue
    
    expected_count = len(linked_sales) + 1  # Original linked + 1 newly linked
    
    print(f"Expected sales count: {expected_count}")
    print(f"Actual sales count: {new_sales_count}")
    print(f"New total revenue: €{new_revenue}\n")
    
    if new_sales_count == expected_count:
        print("✅ PASS: Stocktake updated with newly linked sale")
    else:
        print("❌ FAIL: Sales count incorrect")
        return False
    
    # =========================================================================
    # TEST 7: Count Total Standalone vs Linked Sales
    # =========================================================================
    
    print("="*80)
    print("TEST 7: Final Count - Standalone vs Linked")
    print("="*80)
    
    all_sales = Sale.objects.filter(item__hotel=hotel)
    standalone_count = all_sales.filter(stocktake__isnull=True).count()
    linked_count = all_sales.filter(stocktake__isnull=False).count()
    
    print(f"Total sales in database: {all_sales.count()}")
    print(f"Standalone (no stocktake): {standalone_count}")
    print(f"Linked to stocktake: {linked_count}")
    print(f"Stocktake {stocktake.id} sales: {stocktake.sales.count()}\n")
    
    # We should have 2 standalone (3 created - 1 linked later)
    # and 3 linked (2 originally + 1 updated)
    if standalone_count == 2 and linked_count == 3:
        print("✅ PASS: Correct distribution of standalone vs linked sales")
    else:
        print(f"❌ FAIL: Expected 2 standalone, 3 linked")
        return False
    
    # =========================================================================
    # TEST 8: Summary
    # =========================================================================
    
    print("\n" + "="*80)
    print("🎉 TEST SUMMARY")
    print("="*80)
    
    print("✅ Standalone sales can be created WITHOUT stocktake")
    print("✅ Stocktake excludes standalone sales (as expected)")
    print("✅ Sales can be created WITH stocktake link")
    print("✅ Stocktake includes ONLY linked sales")
    print("✅ Standalone sales can be linked to stocktake later")
    print("✅ Stocktake totals update when sales are linked")
    print("✅ Separation between standalone and linked sales maintained")
    
    print(f"\n📊 Final State:")
    print(f"   Total sales: {all_sales.count()}")
    print(f"   Standalone: {standalone_count}")
    print(f"   Linked to Stocktake {stocktake.id}: {linked_count}")
    print(f"   Stocktake Revenue: €{new_revenue}")
    
    print("\n" + "="*80)
    print("✅ OPTIONAL STOCKTAKE LINKING TEST PASSED!")
    print("="*80 + "\n")
    
    return True


if __name__ == '__main__':
    try:
        success = test_standalone_sales()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
