import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockPeriod, StockMovement
from hotel.models import Hotel
from decimal import Decimal
from datetime import datetime
import random

print("=" * 80)
print("CREATING MOCK PURCHASE DATA FOR OCTOBER 2024")
print("=" * 80)

# Get hotel and period
hotel = Hotel.objects.first()
october = StockPeriod.objects.get(period_name="October 2024")

print(f"\nHotel: {hotel.name}")
print(f"Period: {october.period_name}")

# Clear existing movements for October
existing = StockMovement.objects.filter(period=october).count()
if existing > 0:
    print(f"\nClearing {existing} existing movements...")
    StockMovement.objects.filter(period=october).delete()

# Mock delivery dates in October
delivery_dates = [
    datetime(2024, 10, 3, 10, 30),   # Week 1
    datetime(2024, 10, 10, 11, 15),  # Week 2
    datetime(2024, 10, 17, 9, 45),   # Week 3
    datetime(2024, 10, 24, 10, 0),   # Week 4
]

categories = {
    'D': {'name': 'Draught', 'items': [], 'deliveries': [0, 1, 2, 3]},  # Weekly
    'B': {'name': 'Bottled', 'items': [], 'deliveries': [0, 2]},        # Bi-weekly
    'S': {'name': 'Spirits', 'items': [], 'deliveries': [1]},           # Once/month
    'M': {'name': 'Minerals', 'items': [], 'deliveries': [0, 2]},       # Bi-weekly
    'W': {'name': 'Wine', 'items': [], 'deliveries': [1, 3]},           # Bi-weekly
}

# Get items by category
print("\nLoading items by category...")
for code in categories.keys():
    items = list(StockItem.objects.filter(
        hotel=hotel,
        category_id=code,
        active=True
    ))
    categories[code]['items'] = items
    print(f"  {categories[code]['name']}: {len(items)} items")

created_count = 0
total_purchase_value = Decimal('0.00')

print("\nCreating mock deliveries...")

for code, data in categories.items():
    category_name = data['name']
    items = data['items']
    delivery_weeks = data['deliveries']
    
    if not items:
        continue
    
    print(f"\n{category_name} Deliveries:")
    
    for week_idx in delivery_weeks:
        delivery_date = delivery_dates[week_idx]
        
        # Select random items for this delivery (60-90% of category for high volume)
        num_items = int(len(items) * random.uniform(0.6, 0.9))
        delivery_items = random.sample(items, min(num_items, len(items)))
        
        delivery_value = Decimal('0.00')
        
        for item in delivery_items:
            # Mock quantities based on category - INCREASED for €50k+ sales
            if code == 'D':
                # Kegs: 3-8 kegs per delivery (high volume)
                full_units = random.randint(3, 8)
                quantity_servings = full_units * item.uom
            elif code == 'B':
                # Cases: 8-20 cases per delivery (high volume)
                full_units = random.randint(8, 20)
                quantity_servings = full_units * item.uom
            elif code == 'S':
                # Spirits: 3-10 bottles per delivery (popular items)
                full_units = random.randint(3, 10)
                quantity_servings = full_units * item.uom
            elif code == 'M':
                # Minerals: 10-25 cases per delivery (high volume)
                full_units = random.randint(10, 25)
                quantity_servings = full_units * item.uom
            elif code == 'W':
                # Wine: 5-15 bottles per delivery (increased demand)
                full_units = random.randint(5, 15)
                quantity_servings = full_units * item.uom
            else:
                continue
            
            cost = item.cost_per_serving * quantity_servings
            delivery_value += cost
            
            # Create purchase movement
            StockMovement.objects.create(
                hotel=hotel,
                item=item,
                period=october,
                movement_type='PURCHASE',
                quantity=quantity_servings,
                unit_cost=item.cost_per_serving,
                reference=f"INV-OCT-{week_idx+1}-{random.randint(1000,9999)}",
                notes=f"Mock delivery - Week {week_idx+1}",
                timestamp=delivery_date
            )
            created_count += 1
        
        total_purchase_value += delivery_value
        date_str = delivery_date.strftime('%Y-%m-%d')
        print(f"  Week {week_idx+1} ({date_str}): {len(delivery_items)} items, €{delivery_value:,.2f}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total movements created: {created_count}")
print(f"Total purchase value: €{total_purchase_value:,.2f}")

# Calculate by category
print("\nPurchases by Category:")
print(f"{'Category':<20} {'Movements':<12} {'Value'}")
print("-" * 60)

for code, data in categories.items():
    movements = StockMovement.objects.filter(
        period=october,
        movement_type='PURCHASE',
        item__category_id=code
    )
    count = movements.count()
    value = sum(
        (m.quantity * m.unit_cost) for m in movements
    )
    print(f"{data['name']:<20} {count:<12} €{value:>12,.2f}")

print("\n" + "=" * 80)
print("✓ MOCK PURCHASE DATA CREATED")
print("=" * 80)
print("\nYou can now run the sales calculation to see:")
print("  Sales = (Sept Opening + Purchases) - Oct Closing")
print("\nThis will give you realistic revenue numbers to display")
print("until you get actual POS data.")
