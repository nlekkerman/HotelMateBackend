#!/usr/bin/env python
"""
Populate real stocktake line items with purchases, waste, and sales data
for September, October, and November periods.
"""

import os
import django
import random
from decimal import Decimal
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockPeriod, Stocktake, StocktakeLine, StockItem, 
    StockMovement, Sale
)
from hotel.models import Hotel
from staff.models import Staff

def generate_sales_for_item(item, stocktake, period_start, period_end, 
                            target_revenue, staff):
    """
    Generate realistic sales data for an item throughout the period
    target_revenue: Total revenue to achieve for this item category
    """
    sales_created = []
    
    # Determine sales pattern based on category
    category = item.category.code
    
    # Generate sales for random days in the period
    days_in_period = (period_end - period_start).days + 1
    # 70-90% of days have sales
    num_sale_days = random.randint(
        int(days_in_period * 0.7), 
        int(days_in_period * 0.9)
    )
    
    sale_days = random.sample(range(days_in_period), num_sale_days)
    
    # Calculate total quantity needed to reach target revenue
    unit_price = item.menu_price or Decimal('5.00')
    if unit_price <= 0:
        unit_price = Decimal('5.00')
    
    total_quantity_needed = target_revenue / unit_price
    
    # Distribute quantity across sale days
    remaining_qty = total_quantity_needed
    
    for idx, day_offset in enumerate(sale_days):
        sale_date = period_start + timedelta(days=day_offset)
        
        # Weekend boost (Friday, Saturday get more sales)
        is_weekend = sale_date.weekday() in [4, 5]
        
        # Last day gets remaining quantity
        if idx == len(sale_days) - 1:
            quantity = remaining_qty
        else:
            # Random portion of remaining, with weekend boost
            if is_weekend:
                portion = random.uniform(0.03, 0.08)  # 3-8% on weekends
            else:
                portion = random.uniform(0.01, 0.04)  # 1-4% on weekdays
            
            quantity = remaining_qty * Decimal(str(portion))
            remaining_qty -= quantity
        
        quantity = max(quantity, Decimal('0.01'))  # Minimum 0.01
        quantity = Decimal(str(round(float(quantity), 2)))
        
        # Get current prices
        unit_cost = item.cost_per_serving
        
        # Create sale
        sale = Sale.objects.create(
            stocktake=stocktake,
            item=item,
            quantity=quantity,
            unit_cost=unit_cost,
            unit_price=unit_price,
            sale_date=sale_date,
            notes=f"Sales for {sale_date.strftime('%B %d')}",
            created_by=staff
        )
        sales_created.append(sale)
    
    return sales_created


def generate_purchases_for_item(item, period, period_start, period_end,
                                target_purchase_cost, staff):
    """
    Generate purchase movements for an item
    target_purchase_cost: Total cost to achieve for this item
    """
    purchases_created = []
    
    # Determine purchase frequency based on category
    category = item.category.code
    
    if category in ['D', 'B']:  # Draught/Bottled - frequent
        num_purchases = random.randint(3, 6)
    elif category == 'S':  # Spirits - less frequent
        num_purchases = random.randint(2, 4)
    elif category == 'M':  # Minerals - regular
        num_purchases = random.randint(3, 5)
    elif category == 'W':  # Wine - occasional
        num_purchases = random.randint(1, 3)
    else:
        num_purchases = random.randint(1, 3)
    
    days_in_period = (period_end - period_start).days + 1
    purchase_days = random.sample(
        range(days_in_period),
        min(num_purchases, days_in_period)
    )
    
    # Calculate quantity needed to reach target cost
    unit_cost = item.unit_cost
    if unit_cost <= 0:
        unit_cost = Decimal('10.00')
    
    total_quantity_needed = target_purchase_cost / unit_cost
    remaining_qty = total_quantity_needed
    
    for idx, day_offset in enumerate(purchase_days):
        purchase_date = period_start + timedelta(days=day_offset)
        
        # Last purchase gets remaining quantity
        if idx == len(purchase_days) - 1:
            quantity = remaining_qty
        else:
            # Random portion of remaining
            portion = random.uniform(0.15, 0.35)
            quantity = remaining_qty * Decimal(str(portion))
            remaining_qty -= quantity
        
        quantity = max(quantity, Decimal('0.01'))
        quantity = Decimal(str(round(float(quantity), 2)))
        
        # Create purchase movement
        movement = StockMovement.objects.create(
            hotel=period.hotel,
            period=period,
            item=item,
            movement_type='PURCHASE',
            quantity=quantity,
            unit_cost=unit_cost,
            notes=f"Purchase delivery {purchase_date.strftime('%B %d')}",
            staff=staff
        )
        purchases_created.append(movement)
    
    return purchases_created


def generate_waste_for_item(item, period, period_start, period_end, staff):
    """Generate waste movements for an item (sporadic)"""
    waste_created = []
    
    # Only generate waste for some items (30% chance)
    if random.random() > 0.3:
        return waste_created
    
    # Small waste quantities
    category = item.category.code
    
    if category == 'D':  # Draught - line cleaning, spillage (in pints)
        quantity = Decimal(str(round(random.uniform(2, 10), 2)))
    elif category in ['B', 'W']:  # Bottles - breakage
        quantity = Decimal(str(round(random.uniform(1, 3), 2)))
    elif category == 'S':  # Spirits - spillage (in shots)
        quantity = Decimal(str(round(random.uniform(5, 20), 2)))
    elif category == 'M':  # Minerals - spillage/expired
        quantity = Decimal(str(round(random.uniform(3, 12), 2)))
    else:
        quantity = Decimal(str(round(random.uniform(1, 5), 2)))
    
    # Random date in period
    days_in_period = (period_end - period_start).days + 1
    waste_day = random.randint(0, days_in_period - 1)
    waste_date = period_start + timedelta(days=waste_day)
    
    # Create waste movement
    movement = StockMovement.objects.create(
        hotel=period.hotel,
        period=period,
        item=item,
        movement_type='WASTE',
        quantity=quantity,
        unit_cost=item.unit_cost,
        notes=f"Waste on {waste_date.strftime('%B %d')} - spillage",
        staff=staff
    )
    waste_created.append(movement)
    
    return waste_created


def populate_period_data(period_name, year=2025):
    """Populate a specific period with realistic data"""
    print(f"\n{'='*70}")
    print(f"POPULATING {period_name.upper()} {year} WITH REAL DATA")
    print(f"{'='*70}\n")
    
    # Get hotel and staff
    hotel = Hotel.objects.first()
    staff = Staff.objects.first()
    
    if not hotel or not staff:
        print("❌ Error: No hotel or staff found in database")
        return
    
    # Get the period
    try:
        period = StockPeriod.objects.get(
            hotel=hotel,
            period_name=f"{period_name} {year}"
        )
    except StockPeriod.DoesNotExist:
        print(f"❌ Error: Period '{period_name} {year}' not found")
        return
    
    print(f"✓ Found period: {period.period_name}")
    print(f"  Date range: {period.start_date} to {period.end_date}")
    print(f"  Manual Sales: €{period.manual_sales_amount}")
    print(f"  Manual Purchases: €{period.manual_purchases_amount}")
    
    # Get stocktake
    from stock_tracker.models import Stocktake
    try:
        stocktake = Stocktake.objects.get(
            hotel=hotel,
            period_start=period.start_date,
            period_end=period.end_date
        )
    except Stocktake.DoesNotExist:
        print("❌ Error: No stocktake found for period")
        return
    
    print(f"✓ Found stocktake (Status: {stocktake.status})")
    
    # Calculate target per category (distribute evenly by item count)
    total_sales_target = period.manual_sales_amount or Decimal('0.00')
    total_purchases_target = (
        period.manual_purchases_amount or Decimal('0.00')
    )
    
    total_sales_created = 0
    total_purchases_created = 0
    total_waste_created = 0
    
    total_sales_value = Decimal('0.00')
    total_purchases_value = Decimal('0.00')
    
    # Get all items
    all_items = list(StockItem.objects.filter(hotel=hotel, active=True))
    total_items = len(all_items)
    
    print(f"Total items to process: {total_items}\n")
    
    # Process each item
    for idx, item in enumerate(all_items, 1):
        category_name = item.category.name if item.category else 'Unknown'
        print(f"[{idx}/{total_items}] {item.sku} - {item.name} ({category_name})")
        
        # Calculate target for this item (equal distribution)
        item_sales_target = total_sales_target / Decimal(str(total_items))
        item_purchase_target = (
            total_purchases_target / Decimal(str(total_items))
        )
        
        # Generate sales
        sales = generate_sales_for_item(
            item, stocktake, period.start_date, period.end_date,
            item_sales_target, staff
        )
        total_sales_created += len(sales)
        
        # Calculate actual sales value
        sales_value = sum(s.total_revenue or Decimal('0') for s in sales)
        total_sales_value += sales_value
        
        print(f"  ✓ {len(sales)} sales = €{sales_value:.2f}")
        
        # Generate purchases
        purchases = generate_purchases_for_item(
            item, period, period.start_date, period.end_date,
            item_purchase_target, staff
        )
        total_purchases_created += len(purchases)
        
        # Calculate actual purchase value
        purchase_value = sum(
            p.quantity * p.unit_cost for p in purchases
        )
        total_purchases_value += purchase_value
        
        print(f"  ✓ {len(purchases)} purchases = €{purchase_value:.2f}")
        
        # Generate waste (occasional)
        waste = generate_waste_for_item(
            item, period, period.start_date, period.end_date, staff
        )
        total_waste_created += len(waste)
        if waste:
            print(f"  ✓ {len(waste)} waste entries")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY FOR {period_name.upper()} {year}")
    print(f"{'='*70}")
    print(f"Total Sales Entries: {total_sales_created}")
    print(f"Total Sales Value: €{total_sales_value:.2f}")
    print(f"Target Sales Value: €{total_sales_target:.2f}")
    print(f"Difference: €{(total_sales_value - total_sales_target):.2f}")
    print()
    print(f"Total Purchase Entries: {total_purchases_created}")
    print(f"Total Purchase Value: €{total_purchases_value:.2f}")
    print(f"Target Purchase Value: €{total_purchases_target:.2f}")
    print(f"Difference: €{(total_purchases_value - total_purchases_target):.2f}")
    print()
    print(f"Total Waste Entries: {total_waste_created}")
    print(f"{'='*70}\n")


def main():
    print("\n" + "="*70)
    print("STOCK TRACKER - POPULATE REAL DATA FOR PERIODS")
    print("="*70)
    
    # Clear existing sales and movements
    response = input("\n⚠️  Clear existing Sales and StockMovements? (yes/no): ")
    if response.lower() == 'yes':
        sale_count = Sale.objects.count()
        movement_count = StockMovement.objects.count()
        Sale.objects.all().delete()
        StockMovement.objects.all().delete()
        print(f"✓ Deleted {sale_count} sales and {movement_count} movements")
    
    # Populate each period
    periods = ['September', 'October', 'November']
    
    for period_name in periods:
        response = input(f"\nPopulate {period_name} 2025 with real data? (yes/no): ")
        if response.lower() == 'yes':
            populate_period_data(period_name, 2025)
    
    print("\n" + "="*70)
    print("DATA POPULATION COMPLETED")
    print("="*70)


if __name__ == '__main__':
    main()
