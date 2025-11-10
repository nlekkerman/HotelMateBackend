"""
Management command to generate test data for analytics dashboard.
Creates periods, stocktakes, movements (purchases, waste), and sales.

Usage:
    python manage.py generate_analytics_data --hotel hotel-killarney --months 3
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from hotel.models import Hotel
from staff.models import Staff
from stock_tracker.models import (
    StockPeriod,
    Stocktake,
    StocktakeLine,
    StockItem,
    StockCategory,
    StockMovement,
    StockSnapshot,
    Sale
)


class Command(BaseCommand):
    help = 'Generate test analytics data with periods, stocktakes, movements, and sales'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel',
            type=str,
            required=True,
            help='Hotel slug or subdomain'
        )
        parser.add_argument(
            '--months',
            type=int,
            default=3,
            help='Number of months to generate (default: 3)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data first'
        )

    def handle(self, *args, **options):
        hotel_identifier = options['hotel']
        months = options['months']
        clear_data = options['clear']

        # Get hotel
        try:
            hotel = Hotel.objects.get(slug=hotel_identifier)
        except Hotel.DoesNotExist:
            try:
                hotel = Hotel.objects.get(subdomain=hotel_identifier)
            except Hotel.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'Hotel "{hotel_identifier}" not found'
                ))
                return

        self.stdout.write(f'Generating analytics data for {hotel.name}...')

        # Clear existing data if requested
        if clear_data:
            self.stdout.write('Clearing existing data...')
            StockPeriod.objects.filter(hotel=hotel).delete()
            StockMovement.objects.filter(hotel=hotel).delete()
            Sale.objects.filter(stocktake__hotel=hotel).delete()
            Stocktake.objects.filter(hotel=hotel).delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared'))

        # Get or create a staff member
        staff = Staff.objects.filter(hotel=hotel).first()
        if not staff:
            self.stdout.write(self.style.WARNING(
                'No staff found, creating test staff member...'
            ))
            staff = Staff.objects.create(
                hotel=hotel,
                first_name='Test',
                last_name='Manager',
                email='test@hotel.com',
                role='manager'
            )

        # Get all stock items
        items = list(StockItem.objects.filter(hotel=hotel))
        if not items:
            self.stdout.write(self.style.ERROR(
                'No stock items found. Please create items first.'
            ))
            return

        self.stdout.write(f'Found {len(items)} stock items')

        # Generate data for each month
        today = timezone.now().date()
        
        for month_offset in range(months - 1, -1, -1):
            # Calculate period dates (going backwards from current month)
            period_start = (today.replace(day=1) - timedelta(days=month_offset * 30)).replace(day=1)
            
            # Get last day of month
            if period_start.month == 12:
                period_end = period_start.replace(year=period_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                period_end = period_start.replace(month=period_start.month + 1, day=1) - timedelta(days=1)

            period_name = period_start.strftime('%B %Y')
            
            self.stdout.write(f'\nGenerating data for {period_name}...')

            # Create or get period
            period, created = StockPeriod.objects.get_or_create(
                hotel=hotel,
                start_date=period_start,
                end_date=period_end,
                defaults={
                    'period_name': period_name,
                    'is_closed': True,
                    'closed_at': timezone.now(),
                    'closed_by': staff
                }
            )

            if not created:
                self.stdout.write(f'  Period already exists, updating...')
                period.is_closed = True
                period.closed_at = timezone.now()
                period.closed_by = staff
                period.save()

            # Create opening stocktake
            opening_stocktake = self._create_stocktake(
                hotel, staff, period, period_start, 'opening', items
            )
            
            # Generate movements (purchases and waste)
            self._generate_movements(hotel, staff, period, items, period_start, period_end)
            
            # Create closing stocktake
            closing_stocktake = self._create_stocktake(
                hotel, staff, period, period_end, 'closing', items
            )
            
            # Generate sales
            self._generate_sales(closing_stocktake, items)
            
            # Create snapshots
            self._create_snapshots(hotel, period, items)
            
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ Created period {period_name} with stocktakes, movements, and sales'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Successfully generated {months} months of analytics data!'
        ))
        self.stdout.write(self.style.SUCCESS(
            '\nYou can now view the analytics dashboard with real data.'
        ))

    def _create_stocktake(self, hotel, staff, period, date, stocktake_type, items):
        """Create a stocktake with lines for all items"""
        stocktake = Stocktake.objects.create(
            hotel=hotel,
            period=period,
            stocktake_type=stocktake_type,
            stocktake_date=date,
            is_approved=True,
            approved_by=staff,
            approved_at=timezone.now(),
            created_by=staff
        )

        # Create lines for each item with realistic values
        for item in items:
            # Generate realistic stock levels
            base_stock = random.uniform(10, 100)
            if stocktake_type == 'closing':
                # Closing stock is typically lower than opening
                base_stock *= random.uniform(0.5, 0.9)

            quantity = round(Decimal(str(base_stock)), 2)
            unit_cost = item.unit_cost or Decimal('5.00')
            
            StocktakeLine.objects.create(
                stocktake=stocktake,
                item=item,
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=quantity * unit_cost
            )

        return stocktake

    def _generate_movements(self, hotel, staff, period, items, start_date, end_date):
        """Generate purchase and waste movements"""
        days_in_period = (end_date - start_date).days
        
        for item in items:
            # Generate 2-5 purchases per item
            num_purchases = random.randint(2, 5)
            for _ in range(num_purchases):
                days_offset = random.randint(0, days_in_period)
                movement_date = start_date + timedelta(days=days_offset)
                
                quantity = Decimal(str(random.uniform(10, 50)))
                unit_cost = item.unit_cost or Decimal('5.00')
                
                StockMovement.objects.create(
                    hotel=hotel,
                    item=item,
                    period=period,
                    movement_type=StockMovement.PURCHASE,
                    quantity=quantity,
                    unit_cost=unit_cost,
                    staff=staff,
                    timestamp=timezone.make_aware(
                        datetime.combine(movement_date, datetime.min.time())
                    ),
                    reference=f'PO-{random.randint(1000, 9999)}'
                )

            # Generate 1-3 waste movements per item (10-20% of purchases)
            num_waste = random.randint(1, 3)
            for _ in range(num_waste):
                days_offset = random.randint(0, days_in_period)
                movement_date = start_date + timedelta(days=days_offset)
                
                quantity = Decimal(str(random.uniform(1, 5)))
                unit_cost = item.unit_cost or Decimal('5.00')
                
                StockMovement.objects.create(
                    hotel=hotel,
                    item=item,
                    period=period,
                    movement_type=StockMovement.WASTE,
                    quantity=quantity,
                    unit_cost=unit_cost,
                    staff=staff,
                    timestamp=timezone.make_aware(
                        datetime.combine(movement_date, datetime.min.time())
                    ),
                    notes=random.choice([
                        'Breakage',
                        'Expired',
                        'Quality issue',
                        'Spillage'
                    ])
                )

    def _generate_sales(self, stocktake, items):
        """Generate sales for closing stocktake"""
        # Generate sales for 70-90% of items
        items_with_sales = random.sample(items, int(len(items) * random.uniform(0.7, 0.9)))
        
        for item in items_with_sales:
            # Generate realistic sales
            quantity_sold = Decimal(str(random.uniform(20, 100)))
            unit_cost = item.unit_cost or Decimal('5.00')
            
            # Selling price is typically 2-4x cost for hospitality
            markup = Decimal(str(random.uniform(2.0, 4.0)))
            unit_price = unit_cost * markup
            
            Sale.objects.create(
                stocktake=stocktake,
                item=item,
                quantity=quantity_sold,
                unit_cost=unit_cost,
                unit_price=unit_price,
                total_cost=quantity_sold * unit_cost,
                total_revenue=quantity_sold * unit_price
            )

    def _create_snapshots(self, hotel, period, items):
        """Create stock snapshots for analytics"""
        for item in items:
            # Get movements for this item in this period
            movements = StockMovement.objects.filter(
                hotel=hotel,
                item=item,
                period=period
            )
            
            purchases = movements.filter(
                movement_type=StockMovement.PURCHASE
            ).aggregate(
                total_qty=Sum('quantity'),
                total_cost=Sum(F('quantity') * F('unit_cost'))
            )
            
            waste = movements.filter(
                movement_type=StockMovement.WASTE
            ).aggregate(
                total_qty=Sum('quantity'),
                total_cost=Sum(F('quantity') * F('unit_cost'))
            )
            
            # Calculate values
            purchase_qty = purchases['total_qty'] or Decimal('0')
            waste_qty = waste['total_qty'] or Decimal('0')
            closing_qty = purchase_qty - waste_qty
            
            if closing_qty < 0:
                closing_qty = Decimal('0')
            
            unit_cost = item.unit_cost or Decimal('5.00')
            closing_value = closing_qty * unit_cost
            
            StockSnapshot.objects.update_or_create(
                hotel=hotel,
                period=period,
                item=item,
                defaults={
                    'opening_stock': Decimal('0'),
                    'purchases': purchase_qty,
                    'sales': Decimal('0'),
                    'waste': waste_qty,
                    'closing_stock': closing_qty,
                    'unit_cost': unit_cost,
                    'closing_stock_value': closing_value,
                    'total_servings': closing_qty
                }
            )


# Import for aggregation
from django.db.models import Sum, F
