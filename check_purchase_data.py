import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockMovement, StockPeriod
from decimal import Decimal

print("=" * 80)
print("CHECKING FOR PURCHASE/DELIVERY DATA")
print("=" * 80)

# Get October period
october = StockPeriod.objects.get(period_name="October 2024")
print(f"\nOctober Period: {october.start_date} to {october.end_date}")

# Check for any stock movements
all_movements = StockMovement.objects.filter(period=october)
print(f"\nTotal movements in October: {all_movements.count()}")

if all_movements.count() > 0:
    print("\nMovement Types:")
    for movement_type in StockMovement.MOVEMENT_TYPES:
        code, label = movement_type
        count = all_movements.filter(movement_type=code).count()
        if count > 0:
            print(f"  {label}: {count} records")
    
    # Show sample
    print("\nSample movements:")
    for movement in all_movements[:10]:
        print(f"  {movement.timestamp.strftime('%Y-%m-%d')} - "
              f"{movement.movement_type} - {movement.item.sku} - "
              f"{movement.quantity} servings")
else:
    print("\n⚠ NO STOCK MOVEMENTS RECORDED IN DATABASE")

# Check for purchases specifically
purchases = StockMovement.objects.filter(
    period=october,
    movement_type='PURCHASE'
)

print(f"\n" + "=" * 80)
print(f"PURCHASE RECORDS IN OCTOBER: {purchases.count()}")
print("=" * 80)

if purchases.count() > 0:
    # Calculate total purchases by category
    categories = {
        'D': 'Draught Beers',
        'B': 'Bottled Beers',
        'S': 'Spirits',
        'M': 'Minerals/Syrups',
        'W': 'Wine'
    }
    
    print(f"\n{'Category':<20} {'Purchases (€)'}")
    print("-" * 50)
    
    for code, name in categories.items():
        cat_purchases = purchases.filter(item__category_id=code)
        total_cost = sum(
            (p.quantity * p.unit_cost) if p.unit_cost else Decimal('0.00')
            for p in cat_purchases
        )
        count = cat_purchases.count()
        print(f"{name:<20} €{total_cost:>12,.2f} ({count} deliveries)")
else:
    print("\n⚠ NO PURCHASE RECORDS FOUND")
    print("\nWithout purchase data, we can only calculate NET CHANGE:")
    print("  Net Change = Opening Stock - Closing Stock")
    print("  This shows consumption minus purchases")
    print("\nTo get ACTUAL SALES, you need to:")
    print("  1. Enter delivery/purchase records for October, OR")
    print("  2. Accept net change as approximate consumption")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print("\nOption 1: Do you have delivery invoices for October?")
print("  → We can create purchase records from invoices")
print("\nOption 2: Calculate based on net change only")
print("  → Shows what was consumed vs what came in")
print("  → Negative values = more purchases than sales")
print("  → Positive values = more sales than purchases")
print("\nOption 3: Assume minimal purchases for certain categories")
print("  → e.g., Spirits/Wine rarely restocked mid-month")
print("  → Bottled/Minerals purchased weekly")
