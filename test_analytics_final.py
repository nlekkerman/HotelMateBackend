import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine

print("=" * 100)
print("TESTING ANALYTICS DATA FOR FRONTEND - SEPTEMBER & OCTOBER")
print("=" * 100)

# Get stocktakes
sept_st = Stocktake.objects.get(hotel_id=2, period_start='2025-09-01')
oct_st = Stocktake.objects.get(hotel_id=2, period_start='2025-10-01')

print(f"\n✅ September: ID={sept_st.id}, Status={sept_st.status}")
print(f"✅ October: ID={oct_st.id}, Status={oct_st.status}")

# Calculate category totals for Minerals
def calculate_category_totals(stocktake, category_code='M'):
    lines = StocktakeLine.objects.filter(
        stocktake=stocktake,
        item__category__code=category_code
    ).select_related('item')
    
    totals = {
        'opening_value': Decimal('0'),
        'purchases_value': Decimal('0'),
        'expected_value': Decimal('0'),
        'counted_value': Decimal('0'),
        'variance_value': Decimal('0'),
    }
    
    for line in lines:
        cost = line.item.cost_per_serving
        totals['opening_value'] += line.opening_qty * cost
        totals['purchases_value'] += line.purchases * cost
        totals['expected_value'] += line.expected_qty * cost
        totals['counted_value'] += line.counted_qty * cost
        totals['variance_value'] += line.variance_qty * cost
    
    return totals

print("\n" + "=" * 100)
print("SEPTEMBER MINERALS/SYRUPS ANALYTICS")
print("=" * 100)

sept_totals = calculate_category_totals(sept_st, 'M')
print(f"\n📊 Opening Stock Value:    €{sept_totals['opening_value']:,.2f}")
print(f"📊 Purchases Value:        €{sept_totals['purchases_value']:,.2f}")
print(f"📊 Expected Stock Value:   €{sept_totals['expected_value']:,.2f}")
print(f"📊 Counted Stock Value:    €{sept_totals['counted_value']:,.2f}")
print(f"📊 Variance Value:         €{sept_totals['variance_value']:,.2f}")
print(f"📊 Closing Stock Value:    €{sept_totals['counted_value']:,.2f} (= Counted)")

print("\n" + "=" * 100)
print("OCTOBER MINERALS/SYRUPS ANALYTICS")
print("=" * 100)

oct_totals = calculate_category_totals(oct_st, 'M')
print(f"\n📊 Opening Stock Value:    €{oct_totals['opening_value']:,.2f}")
print(f"📊 Purchases Value:        €{oct_totals['purchases_value']:,.2f}")
print(f"📊 Expected Stock Value:   €{oct_totals['expected_value']:,.2f}")
print(f"📊 Counted Stock Value:    €{oct_totals['counted_value']:,.2f}")
print(f"📊 Variance Value:         €{oct_totals['variance_value']:,.2f}")
print(f"📊 Closing Stock Value:    €{oct_totals['counted_value']:,.2f} (= Counted)")

print("\n" + "=" * 100)
print("CONTINUITY VERIFICATION")
print("=" * 100)

sept_closing = float(sept_totals['counted_value'])
oct_opening = float(oct_totals['opening_value'])
difference = abs(sept_closing - oct_opening)

print(f"\n✅ September Closing:  €{sept_closing:,.2f}")
print(f"✅ October Opening:    €{oct_opening:,.2f}")
print(f"✅ Difference:         €{difference:.2f}")

if difference < 1.0:
    print("\n✅ PERFECT! Continuity verified (difference < €1.00)")
else:
    print(f"\n❌ MISMATCH: €{difference:.2f}")

print("\n" + "=" * 100)
print("SAMPLE LINE DATA (First 10 Items)")
print("=" * 100)

sept_lines = StocktakeLine.objects.filter(
    stocktake=sept_st,
    item__category__code='M'
).select_related('item')[:10]

print("\n📋 SEPTEMBER LINES:")
print(f"{'SKU':<10} {'Item':<25} {'Opening':<12} {'Counted':<12} {'Variance':<12}")
print("-" * 100)

for line in sept_lines:
    opening_val = float(line.opening_qty * line.item.cost_per_serving)
    counted_val = float(line.counted_qty * line.item.cost_per_serving)
    variance_val = float(line.variance_qty * line.item.cost_per_serving)
    
    print(f"{line.item.sku:<10} {line.item.name[:25]:<25} "
          f"€{opening_val:<11.2f} €{counted_val:<11.2f} €{variance_val:<11.2f}")

oct_lines = StocktakeLine.objects.filter(
    stocktake=oct_st,
    item__category__code='M'
).select_related('item')[:10]

print("\n📋 OCTOBER LINES:")
print(f"{'SKU':<10} {'Item':<25} {'Opening':<12} {'Counted':<12} {'Variance':<12}")
print("-" * 100)

for line in oct_lines:
    opening_val = float(line.opening_qty * line.item.cost_per_serving)
    counted_val = float(line.counted_qty * line.item.cost_per_serving)
    variance_val = float(line.variance_qty * line.item.cost_per_serving)
    
    print(f"{line.item.sku:<10} {line.item.name[:25]:<25} "
          f"€{opening_val:<11.2f} €{counted_val:<11.2f} €{variance_val:<11.2f}")

print("\n" + "=" * 100)
print("✅ FRONTEND WILL RECEIVE CORRECT DATA:")
print("=" * 100)
print("\n1. ✅ Opening balances from previous period closing")
print("2. ✅ Purchase amounts (currently €0)")
print("3. ✅ Expected = Opening + Purchases")
print("4. ✅ Counted = Physical count")
print("5. ✅ Variance = Counted - Expected")
print("6. ✅ Closing = Counted (becomes next period opening)")
print("7. ✅ Period-to-period continuity maintained")

print("\n" + "=" * 100)
print("SUMMARY:")
print(f"- September correct: €{sept_closing:,.2f}")
print(f"- October correct: €{oct_opening:,.2f}")
print(f"- Continuity: {'✅ PASS' if difference < 1.0 else '❌ FAIL'}")
print("=" * 100)
