import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake, StocktakeLine

print("=" * 100)
print("VERIFYING ANALYTICS DATA - SEPTEMBER & OCTOBER MINERALS/SYRUPS")
print("=" * 100)

# Get stocktakes
sept_stocktake = Stocktake.objects.get(hotel_id=2, period_start='2025-09-01')
oct_stocktake = Stocktake.objects.get(hotel_id=2, period_start='2025-10-01')

print(f"\n✅ September: ID={sept_stocktake.id}, Status={sept_stocktake.status}")
print(f"✅ October: ID={oct_stocktake.id}, Status={oct_stocktake.status}")

print("\n" + "=" * 100)
print("CALCULATING SEPTEMBER MINERALS/SYRUPS CATEGORY")
print("=" * 100)

sept_lines = StocktakeLine.objects.filter(
    stocktake=sept_stocktake,
    item__category__code='M'
).select_related('item')

sept_opening = Decimal('0')
sept_purchases = Decimal('0')
sept_expected = Decimal('0')
sept_counted = Decimal('0')
sept_closing = Decimal('0')
sept_variance = Decimal('0')

for line in sept_lines:
    cost = line.item.cost_per_serving
    sept_opening += line.opening_qty * cost
    sept_purchases += line.purchases * cost
    sept_expected += line.expected_qty * cost
    sept_counted += line.counted_qty * cost
    sept_closing += line.counted_qty * cost  # Closing = Counted
    sept_variance += (line.counted_qty - line.expected_qty) * cost

print(f"\n📦 SEPTEMBER MINERALS/SYRUPS:")
print(f"  Opening Stock:  €{sept_opening:,.2f}")
print(f"  Purchases:      €{sept_purchases:,.2f}")
print(f"  Expected Stock: €{sept_expected:,.2f}")
print(f"  Counted Stock:  €{sept_counted:,.2f}")
print(f"  Variance:       €{sept_variance:,.2f}")
print(f"  Closing Stock:  €{sept_closing:,.2f}")

print("\n" + "=" * 100)
print("CALCULATING OCTOBER MINERALS/SYRUPS CATEGORY")
print("=" * 100)

oct_lines = StocktakeLine.objects.filter(
    stocktake=oct_stocktake,
    item__category__code='M'
).select_related('item')

oct_opening = Decimal('0')
oct_purchases = Decimal('0')
oct_expected = Decimal('0')
oct_counted = Decimal('0')
oct_closing = Decimal('0')
oct_variance = Decimal('0')

for line in oct_lines:
    cost = line.item.cost_per_serving
    oct_opening += line.opening_qty * cost
    oct_purchases += line.purchases * cost
    oct_expected += line.expected_qty * cost
    oct_counted += line.counted_qty * cost
    oct_closing += line.counted_qty * cost  # Closing = Counted
    oct_variance += (line.counted_qty - line.expected_qty) * cost

print(f"\n📦 OCTOBER MINERALS/SYRUPS:")
print(f"  Opening Stock:  €{oct_opening:,.2f}")
print(f"  Purchases:      €{oct_purchases:,.2f}")
print(f"  Expected Stock: €{oct_expected:,.2f}")
print(f"  Counted Stock:  €{oct_counted:,.2f}")
print(f"  Variance:       €{oct_variance:,.2f}")
print(f"  Closing Stock:  €{oct_closing:,.2f}")

print("\n" + "=" * 100)
print("VERIFYING CONTINUITY: SEPTEMBER CLOSING → OCTOBER OPENING")
print("=" * 100)

sept_close_val = float(sept_closing)
oct_open_val = float(oct_opening)
difference = abs(sept_close_val - oct_open_val)

print(f"\nSeptember Closing:  €{sept_close_val:,.2f}")
print(f"October Opening:    €{oct_open_val:,.2f}")
print(f"Difference:         €{difference:,.2f}")

if difference < 0.01:
    print("\n✅ PERFECT MATCH! Continuity verified.")
else:
    print(f"\n❌ MISMATCH! Difference of €{difference:,.2f}")

print("\n" + "=" * 100)
print("CHECKING SAMPLE LINE DATA (First 5 Items)")
print("=" * 100)

print("\n📋 SEPTEMBER LINES:")
print(f"{'SKU':<10} {'Item':<30} {'Opening':<12} {'Purchases':<12} {'Counted':<12} {'Closing':<12}")
print("-" * 100)

for line in sept_lines[:5]:
    opening_val = float(line.opening_qty * line.item.cost_per_serving)
    purchase_val = float(line.purchases * line.item.cost_per_serving)
    counted_val = float(line.counted_qty * line.item.cost_per_serving)
    closing_val = float(line.counted_qty * line.item.cost_per_serving)
    
    print(f"{line.item.sku:<10} {line.item.name[:30]:<30} "
          f"€{opening_val:<11.2f} €{purchase_val:<11.2f} "
          f"€{counted_val:<11.2f} €{closing_val:<11.2f}")

print("\n📋 OCTOBER LINES:")
print(f"{'SKU':<10} {'Item':<30} {'Opening':<12} {'Purchases':<12} {'Counted':<12} {'Closing':<12}")
print("-" * 100)

for line in oct_lines[:5]:
    opening_val = float(line.opening_qty * line.item.cost_per_serving)
    purchase_val = float(line.purchases * line.item.cost_per_serving)
    counted_val = float(line.counted_qty * line.item.cost_per_serving)
    closing_val = float(line.counted_qty * line.item.cost_per_serving)
    
    print(f"{line.item.sku:<10} {line.item.name[:30]:<30} "
          f"€{opening_val:<11.2f} €{purchase_val:<11.2f} "
          f"€{counted_val:<11.2f} €{closing_val:<11.2f}")

print("\n" + "=" * 100)
print("VERIFYING LINE-BY-LINE CONTINUITY")
print("=" * 100)

# Create lookup
oct_dict = {line.item.sku: line for line in oct_lines}

matches = 0
mismatches = 0

for sept_line in sept_lines:
    oct_line = oct_dict.get(sept_line.item.sku)
    if oct_line:
        sept_close_qty = float(sept_line.counted_qty)  # Closing = Counted
        oct_open_qty = float(oct_line.opening_qty)
        
        if abs(sept_close_qty - oct_open_qty) < 0.01:
            matches += 1
        else:
            mismatches += 1
            print(f"❌ {sept_line.item.sku}: Sept Close={sept_close_qty:.2f}, Oct Open={oct_open_qty:.2f}")

print(f"\n✅ Matches: {matches}")
print(f"❌ Mismatches: {mismatches}")

if mismatches == 0:
    print("\n✅ PERFECT! All quantities match Sept closing → Oct opening")

print("\n" + "=" * 100)
print("FINAL SUMMARY")
print("=" * 100)

print("\n✅ VERIFIED FOR FRONTEND:")
print(f"  1. September opening balance: €{sept_opening:,.2f}")
print(f"  2. September closing balance: €{sept_closing:,.2f}")
print(f"  3. October opening balance: €{oct_opening:,.2f}")
print(f"  4. October closing balance: €{oct_closing:,.2f}")
print(f"  5. Continuity: {'✅ PASS' if difference < 0.01 else '❌ FAIL'}")
print(f"  6. Line continuity: {matches}/{matches + mismatches} matches")

print("\n📊 FRONTEND ANALYTICS WILL SHOW:")
print("  - Opening stock values (from previous period closing)")
print("  - Purchase amounts")
print("  - Expected stock = Opening + Purchases")
print("  - Counted stock (actual count)")
print("  - Variance = Counted - Expected")
print("  - Closing stock = Counted stock")

print("\n" + "=" * 100)
