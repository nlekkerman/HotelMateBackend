"""
Management command to simulate bookings for all room types in Killarney hotel.
Tests the complete booking flow: availability -> pricing -> booking creation.
"""
from django.core.management.base import BaseCommand
from hotel.models import Hotel
from rooms.models import RoomType
from hotel.services.availability import is_room_type_available, _inventory_for_date, _booked_for_date
from hotel.services.pricing import build_pricing_quote_data
from datetime import date, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Simulate booking flow for all Killarney room types'

    def handle(self, *args, **options):
        try:
            hotel = Hotel.objects.get(id=2)
            self.stdout.write(f"Hotel: {hotel.name}")
            self.stdout.write("=" * 80)
        except Hotel.DoesNotExist:
            self.stdout.write(self.style.ERROR("Hotel Killarney (id=2) not found!"))
            return

        # Get all room types
        room_types = RoomType.objects.filter(hotel=hotel).order_by('name')
        
        # Test scenarios
        scenarios = [
            {
                'name': 'Weekday Booking (2 nights)',
                'checkin': date.today() + timedelta(days=10),  # Next Wednesday
                'nights': 2,
                'adults': 2,
                'children': 0,
                'promo_code': None
            },
            {
                'name': 'Weekend Booking (3 nights, Fri-Sun)',
                'checkin': date.today() + timedelta(days=12),  # Next Friday
                'nights': 3,
                'adults': 2,
                'children': 1,
                'promo_code': 'WINTER20'
            },
            {
                'name': 'Long Stay (5 nights with LONGSTAY promo)',
                'checkin': date.today() + timedelta(days=20),
                'nights': 5,
                'adults': 2,
                'children': 0,
                'promo_code': 'LONGSTAY'
            }
        ]

        for scenario in scenarios:
            self.stdout.write(f"\n\n{'='*80}")
            self.stdout.write(f"SCENARIO: {scenario['name']}")
            self.stdout.write(f"{'='*80}")
            self.stdout.write(f"Check-in: {scenario['checkin']}")
            self.stdout.write(f"Check-out: {scenario['checkin'] + timedelta(days=scenario['nights'])}")
            self.stdout.write(f"Guests: {scenario['adults']} adults, {scenario['children']} children")
            self.stdout.write(f"Promo code: {scenario['promo_code'] or 'None'}")
            
            self.stdout.write(f"\n{'-'*80}")
            self.stdout.write("Room Type".ljust(25) + "Available".ljust(12) + "Base Price".ljust(15) + "Final Price")
            self.stdout.write(f"{'-'*80}")
            
            for rt in room_types:
                try:
                    # 1. Check capacity
                    total_guests = scenario['adults'] + scenario['children']
                    can_accommodate = rt.max_occupancy >= total_guests
                    
                    if not can_accommodate:
                        self.stdout.write(
                            f"{rt.name[:24].ljust(25)}"
                            f"{'N/A'.ljust(12)}"
                            f"{'-'.ljust(15)}"
                            f"Cannot accommodate {scenario['adults']}+{scenario['children']} guests"
                        )
                        continue
                    
                    # 2. Check availability
                    checkout = scenario['checkin'] + timedelta(days=scenario['nights'])
                    is_available = is_room_type_available(
                        rt,
                        scenario['checkin'],
                        checkout,
                        required_units=1
                    )
                    
                    if is_available:
                        # Get available count for first night
                        inv = _inventory_for_date(rt, scenario['checkin'])
                        booked = _booked_for_date(rt, scenario['checkin'])
                        available = inv - booked
                        # 2. Get pricing quote
                        quote_data = build_pricing_quote_data(
                            hotel=hotel,
                            room_type=rt,
                            check_in=scenario['checkin'],
                            check_out=scenario['checkin'] + timedelta(days=scenario['nights']),
                            adults=scenario['adults'],
                            children=scenario['children'],
                            promo_code=scenario['promo_code']
                        )
                        
                        base_total = quote_data.get('subtotal', quote_data.get('subtotal_before_discount', 0))
                        final_total = quote_data.get('grand_total', quote_data.get('total_amount_incl_taxes', 0))
                        promo_discount = quote_data.get('promo_discount', quote_data.get('promotion_discount', 0))
                        discount_info = ""
                        
                        if promo_discount > 0:
                            discount_info = f" (saved €{promo_discount})"
                        
                        self.stdout.write(
                            f"{rt.name[:24].ljust(25)}"
                            f"{str(available) + ' rooms'.ljust(12)}"
                            f"{('€' + str(base_total)).ljust(15)}"
                            f"€{final_total}{discount_info}"
                        )
                        
                        # Show nightly breakdown for first room type
                        if rt == room_types[0]:
                            self.stdout.write(f"\n  Nightly rates for {rt.name}:")
                            for night_date, rate in quote_data['nightly_rates']:
                                day_name = night_date.strftime('%a')
                                self.stdout.write(f"    {night_date} ({day_name}): €{rate}")
                            
                            promo_used = quote_data.get('promo_code_used', quote_data.get('promotion_code'))
                            if promo_used:
                                self.stdout.write(f"  Promotion applied: {promo_used}")
                            vat = quote_data.get('vat_amount', quote_data.get('tax_amount', 0))
                            self.stdout.write(f"  VAT (9%): €{vat}")
                            self.stdout.write("")
                    
                    else:
                        self.stdout.write(
                            f"{rt.name[:24].ljust(25)}"
                            f"{'SOLD OUT'.ljust(12)}"
                            f"{'-'.ljust(15)}"
                            f"-"
                        )
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"{rt.name[:24].ljust(25)}"
                        f"{'ERROR'.ljust(12)}"
                        f"{str(e)}"
                    ))

        # Summary
        self.stdout.write(f"\n\n{'='*80}")
        self.stdout.write(self.style.SUCCESS("✓ Booking simulation complete!"))
        self.stdout.write("=" * 80)
        self.stdout.write("\nNOTE: This is a simulation - no actual bookings were created.")
        self.stdout.write("To create real bookings, use the booking API endpoints.")
