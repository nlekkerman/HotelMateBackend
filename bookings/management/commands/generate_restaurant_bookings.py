"""
Django management command to generate realistic restaurant bookings.

Usage:
    python manage.py generate_restaurant_bookings

This command creates 10 restaurant bookings per day for the next 30 days with:
- Different rooms and guests
- Varied party sizes (1-8 people)
- Distributed time slots throughout operating hours
- Full validation including capacity checks and time overlap prevention
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta, time
import random

from bookings.models import (
    Booking, BookingCategory, BookingSubcategory,
    Restaurant, Seats
)
from rooms.models import Room
from guests.models import Guest
from hotel.models import Hotel


class Command(BaseCommand):
    help = 'Generate restaurant bookings for the next month (10 per day)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to generate bookings for (default: 30)'
        )
        parser.add_argument(
            '--per-day',
            type=int,
            default=10,
            help='Number of bookings per day (default: 10)'
        )
        parser.add_argument(
            '--hotel-slug',
            type=str,
            help='Hotel slug (if not provided, uses first hotel)'
        )
        parser.add_argument(
            '--restaurant-slug',
            type=str,
            help='Restaurant slug (uses first active if not provided)'
        )

    def handle(self, *args, **options):
        days = options['days']
        per_day = options['per_day']
        hotel_slug = options.get('hotel_slug')
        restaurant_slug = options.get('restaurant_slug')

        self.stdout.write(self.style.WARNING(
            '\n=== Restaurant Booking Generator ==='
        ))
        self.stdout.write(f'Days: {days}')
        self.stdout.write(f'Bookings per day: {per_day}')
        self.stdout.write(f'Total bookings to create: {days * per_day}\n')

        # Get hotel
        if hotel_slug:
            try:
                hotel = Hotel.objects.get(slug=hotel_slug)
            except Hotel.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'Hotel with slug "{hotel_slug}" not found'
                ))
                return
        else:
            hotel = Hotel.objects.first()
            if not hotel:
                self.stdout.write(self.style.ERROR(
                    'No hotels found in database'
                ))
                return

        self.stdout.write(self.style.SUCCESS(
            f'Hotel: {hotel.name} ({hotel.slug})'
        ))

        # Get restaurant
        if restaurant_slug:
            try:
                restaurant = Restaurant.objects.get(
                    slug=restaurant_slug,
                    hotel=hotel,
                    is_active=True
                )
            except Restaurant.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'Restaurant "{restaurant_slug}" not found '
                    f'for hotel {hotel.name}'
                ))
                return
        else:
            restaurant = Restaurant.objects.filter(
                hotel=hotel,
                is_active=True
            ).first()
            if not restaurant:
                self.stdout.write(self.style.ERROR(
                    f'No active restaurants found for hotel {hotel.name}'
                ))
                return

        self.stdout.write(self.style.SUCCESS(
            f'Restaurant: {restaurant.name} (capacity: {restaurant.capacity})'
        ))

        # Get dinner category
        try:
            dinner_sub = BookingSubcategory.objects.get(
                name__iexact="dinner",
                hotel=hotel
            )
            dinner_cat = BookingCategory.objects.get(
                subcategory=dinner_sub,
                hotel=hotel
            )
        except (BookingSubcategory.DoesNotExist, BookingCategory.DoesNotExist):
            self.stdout.write(self.style.ERROR(
                f'Dinner booking category not configured '
                f'for hotel {hotel.name}'
            ))
            self.stdout.write(
                'Please create BookingSubcategory "dinner" '
                'and related BookingCategory first'
            )
            return

        # Get rooms
        rooms = list(Room.objects.filter(hotel=hotel))
        if not rooms:
            self.stdout.write(self.style.ERROR(
                f'No rooms found for hotel {hotel.name}'
            ))
            return

        self.stdout.write(f'Available rooms: {len(rooms)}\n')

        # Generate fake guest names
        first_names = [
            'James', 'Emma', 'Oliver', 'Sophia', 'William', 'Ava', 'Benjamin',
            'Isabella', 'Lucas', 'Mia', 'Henry', 'Charlotte', 'Alexander',
            'Amelia', 'Michael', 'Harper', 'Daniel', 'Evelyn', 'Matthew',
            'Abigail', 'David', 'Emily', 'Joseph', 'Elizabeth', 'Samuel',
            'Sofia', 'Sebastian', 'Avery', 'John', 'Ella'
        ]
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia',
            'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Wilson', 'Anderson',
            'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee', 'White',
            'Harris', 'Thompson', 'Clark', 'Lewis', 'Walker', 'Hall', 'Young'
        ]

        # Time slots throughout the day (18:00-22:00 typical dinner hours)
        time_slots = [
            time(18, 0), time(18, 30), time(19, 0), time(19, 30),
            time(20, 0), time(20, 30), time(21, 0), time(21, 30)
        ]

        # Statistics
        created_count = 0
        skipped_count = 0
        error_count = 0

        # Generate bookings
        start_date = timezone.now().date()

        for day_offset in range(days):
            booking_date = start_date + timedelta(days=day_offset)
            
            self.stdout.write(self.style.WARNING(
                f'\n--- {booking_date.strftime("%A, %B %d, %Y")} ---'
            ))

            # Track which rooms have already booked today
            rooms_used_today = set()
            
            # Track bookings per hour for this day
            hourly_bookings = {}

            daily_created = 0
            daily_skipped = 0
            daily_errors = 0

            attempts = 0
            max_attempts = per_day * 3  # Allow retries

            while daily_created < per_day and attempts < max_attempts:
                attempts += 1

                # Select random room not yet used today
                available_rooms = [
                    r for r in rooms if r.id not in rooms_used_today
                ]
                if not available_rooms:
                    self.stdout.write(
                        f'  All rooms used for {booking_date}, stopping'
                    )
                    break

                room = random.choice(available_rooms)

                # Random party size (1-8 people, weighted smaller)
                party_size_weights = [3, 4, 5, 4, 3, 2, 1, 1]
                adults = random.choices(
                    range(1, 9), weights=party_size_weights
                )[0]
                children = random.randint(0, 2) if adults <= 6 else 0
                # 10% chance of infant
                infants = 1 if random.random() < 0.1 else 0
                total_guests = adults + children + infants

                # Check max group size
                if total_guests > restaurant.max_group_size:
                    adults = min(adults, restaurant.max_group_size)
                    children = 0
                    infants = 0
                    total_guests = adults

                # Random time slot
                start_time = random.choice(time_slots)
                
                # Duration: 1.5 to 2 hours
                duration_hours = random.choice([1.5, 2.0])
                start_dt = datetime.combine(booking_date, start_time)
                end_dt = start_dt + timedelta(hours=duration_hours)
                end_time = end_dt.time()

                # Check hourly booking limit
                hour_key = start_time.hour
                current_hour_bookings = hourly_bookings.get(hour_key, 0)
                
                if current_hour_bookings >= restaurant.max_bookings_per_hour:
                    daily_skipped += 1
                    continue

                # Check for time overlap with existing bookings
                overlapping = Booking.objects.filter(
                    restaurant=restaurant,
                    date=booking_date,
                    category=dinner_cat,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                )

                # Check capacity constraint
                current_guests = sum(b.total_seats() for b in overlapping)
                if current_guests + total_guests > restaurant.capacity:
                    daily_skipped += 1
                    continue

                # Create or get guest
                guest = None
                if room.guests.exists():
                    guest = room.guests.first()
                else:
                    # Create temporary guest
                    first_name = random.choice(first_names)
                    last_name = random.choice(last_names)
                    guest, _ = Guest.objects.get_or_create(
                        first_name=first_name,
                        last_name=last_name,
                        hotel=hotel,
                        defaults={'room': room}
                    )

                # Create booking
                try:
                    booking = Booking.objects.create(
                        hotel=hotel,
                        category=dinner_cat,
                        restaurant=restaurant,
                        room=room,
                        guest=guest,
                        date=booking_date,
                        start_time=start_time,
                        end_time=end_time,
                        note=f'Auto-generated ({total_guests} guests)'
                    )

                    # Create seats
                    Seats.objects.create(
                        booking=booking,
                        total=total_guests,
                        adults=adults,
                        children=children,
                        infants=infants
                    )

                    # Mark room as used today
                    rooms_used_today.add(room.id)

                    # Update hourly count
                    hourly_bookings[hour_key] = current_hour_bookings + 1

                    # Success
                    daily_created += 1
                    created_count += 1

                    self.stdout.write(
                        f'  ✓ Booking #{daily_created}: '
                        f'Room {room.room_number} | '
                        f'{start_time.strftime("%H:%M")}→'
                        f'{end_time.strftime("%H:%M")} | '
                        f'{total_guests} guests '
                        f'(A:{adults}, C:{children}, I:{infants})'
                    )

                except Exception as e:
                    daily_errors += 1
                    error_count += 1
                    self.stdout.write(self.style.ERROR(
                        f'  ✗ Error creating booking: {str(e)}'
                    ))

            # Daily summary
            skipped_count += daily_skipped
            self.stdout.write(
                f'  Created: {daily_created}, Skipped: {daily_skipped}, '
                f'Errors: {daily_errors}'
            )

        # Final summary
        self.stdout.write(self.style.SUCCESS(
            '\n=== SUMMARY ==='
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Total bookings created: {created_count}'
        ))
        self.stdout.write(f'Skipped (constraints): {skipped_count}')
        self.stdout.write(f'Errors: {error_count}')
        self.stdout.write(self.style.SUCCESS(
            '\n✓ Booking generation complete!\n'
        ))
