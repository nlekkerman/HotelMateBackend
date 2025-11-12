"""
Verify CLOSING (counted) stock values
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from decimal import Decimal

# Get stocktake #17 (Sept 2025)
stocktake = Stocktake.objects.get(id=17)

print("=" * 80)
print("STOCKTAKE #17 - CLOSING STOCK VERIFICATION")
print("=" * 80)

# Get category totals
categories = stocktake.get_category_totals()

print("\nCLOSING (COUNTED) STOCK BY CATEGORY:")
print("-" * 80)

for cat_code, cat_data in categories.items():
    counted_value = cat_data['counted_value']
    print(f"{cat_data['category_name']:20} €{counted_value:>10,.2f}")

print("-" * 80)

# Calculate total counted stock value
total_counted = sum(cat_data['counted_value'] for cat_data in categories.values())
print(f"{'TOTAL':20} €{total_counted:>10,.2f}")

print("\n" + "=" * 80)
print("COMPARISON WITH YOUR DATA:")
print("=" * 80)

your_closing = {
    'Draught Beer': Decimal('5311.62'),
    'Bottled Beer': Decimal('2288.46'),
    'Spirits': Decimal('11063.66'),
    'Minerals & Syrups': Decimal('3062.43'),
    'Wine': Decimal('5580.35'),
}

print("\nCategory             Your Closing    DB Counted      Difference")
print("-" * 80)

for cat_code, cat_data in categories.items():
    cat_name = cat_data['category_name']
    db_counted = cat_data['counted_value']
    your_close = your_closing.get(cat_name, Decimal('0'))
    diff = db_counted - your_close
    
    status = "✅" if abs(diff) < 0.10 else "⚠️"
    print(f"{cat_name:20} €{your_close:>10,.2f}  €{db_counted:>10,.2f}  €{diff:>10,.2f} {status}")

your_total = sum(your_closing.values())
diff_total = total_counted - your_total

print("-" * 80)
print(f"{'TOTAL':20} €{your_total:>10,.2f}  €{total_counted:>10,.2f}  €{diff_total:>10,.2f}")

print("\n" + "=" * 80)
print("ANALYSIS:")
print("=" * 80)

if abs(total_counted - Decimal('21669.53')) < 0.10:
    print("✅ Database counted value matches: €21,669.53")
else:
    print(f"⚠️  Database counted value: €{total_counted:,.2f}")

if abs(your_total - Decimal('27306.51')) < 0.10:
    print("✅ Your closing total matches: €27,306.51")
else:
    print(f"⚠️  Your closing total: €{your_total:,.2f}")

print("\n💡 INSIGHT:")
print("   If your data shows HIGHER closing values than database,")
print("   then the DATABASE values shown in the PDF are CORRECT.")
print("   The PDF is showing COUNTED stock, not EXPECTED stock.")
