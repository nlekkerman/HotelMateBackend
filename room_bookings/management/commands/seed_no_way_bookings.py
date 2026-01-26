"""
Management command to create deterministic test data for "no-way-hotel".

Creates realistic RoomBooking records across multiple booking lifecycle stages:
- PENDING_PAYMENT (not expired and expired)
- PENDING_APPROVAL (overdue)
- CONFIRMED upcoming with precheckin complete
- CONFIRMED checked-in scenarios (current, overdue, overstay incidents)
- NO_SHOW and CANCELLED bookings

Usage:
    python manage.py seed_no_way_bookings --count 1 --reset
    python manage.py seed_no_way_bookings --count 3  # Creates 3 sets of scenarios
"""
import hashlib
import secrets
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from hotel.models import (
    Hotel, HotelAccessConfig, RoomBooking, BookingGuest, OverstayIncident, 
    BookingExtension, GuestBookingToken, BookingPrecheckinToken, 
    BookingManagementToken
)
from rooms.models import Room, RoomType
from staff.models import Staff
from room_bookings.services.overstay import get_hotel_noon_utc
from hotel.services.booking import generate_booking_id


class Command(BaseCommand):
    help = 'Create deterministic test data for no-way-hotel with realistic booking scenarios'
    
    # Constant tag for idempotent operations
    SEED_TAG = "[SEED_NO_WAY_HOTEL]"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of complete scenario sets to create (default: 1)'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing seeded data before creating new records'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        reset = options['reset']
        
        self.stdout.write("🌱 Seeding test data for no-way-hotel...")
        
        try:
            with transaction.atomic():
                # Get or validate hotel
                hotel = self._get_hotel()
                
                # Reset if requested
                if reset:
                    self._reset_seeded_data(hotel)
                
                # Ensure hotel configuration
                self._ensure_hotel_config(hotel)
                
                # Get room type and room
                room_type, room = self._get_room_resources(hotel)
                
                # Create scenario sets
                scenarios_created = []
                for set_num in range(1, count + 1):
                    set_scenarios = self._create_scenario_set(hotel, room_type, room, set_num)
                    scenarios_created.extend(set_scenarios)
                
                # Print summary
                self._print_summary(scenarios_created)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Successfully created {len(scenarios_created)} booking scenarios "
                        f"for {hotel.name}"
                    )
                )
                
        except CommandError:
            raise
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error: {e}")
            )
            raise CommandError(f"Failed to seed data: {e}")
    
    def _get_hotel(self):
        """Get no-way-hotel or raise error if it doesn't exist."""
        try:
            hotel = Hotel.objects.get(slug="no-way-hotel")
            self.stdout.write(f"🏨 Found hotel: {hotel.name} (timezone: {hotel.timezone})")
            return hotel
        except Hotel.DoesNotExist:
            raise CommandError(
                "❌ Hotel with slug 'no-way-hotel' does not exist. "
                "Please create this hotel first."
            )
    
    def _reset_seeded_data(self, hotel):
        """Delete all seeded objects for this hotel in correct order."""
        self.stdout.write("🗑️  Resetting existing seeded data...")
        
        # Delete in dependency order to avoid foreign key constraints
        filter_kwargs = {
            'booking__internal_notes__contains': self.SEED_TAG,
            'booking__hotel': hotel
        }
        
        # BookingExtension
        extensions_count = BookingExtension.objects.filter(**filter_kwargs).count()
        if extensions_count > 0:
            BookingExtension.objects.filter(**filter_kwargs).delete()
            self.stdout.write(f"   Deleted {extensions_count} BookingExtension records")
        
        # OverstayIncident
        incidents_count = OverstayIncident.objects.filter(
            booking__internal_notes__contains=self.SEED_TAG,
            hotel=hotel
        ).count()
        if incidents_count > 0:
            OverstayIncident.objects.filter(
                booking__internal_notes__contains=self.SEED_TAG,
                hotel=hotel
            ).delete()
            self.stdout.write(f"   Deleted {incidents_count} OverstayIncident records")
        
        # Tokens
        token_models = [
            (GuestBookingToken, 'guest_tokens'),
            (BookingPrecheckinToken, 'precheckin_tokens'),  
            (BookingManagementToken, 'management_tokens')
        ]
        
        for token_model, related_name in token_models:
            tokens_count = token_model.objects.filter(**filter_kwargs).count()
            if tokens_count > 0:
                token_model.objects.filter(**filter_kwargs).delete()
                self.stdout.write(f"   Deleted {tokens_count} {token_model.__name__} records")
        
        # BookingGuest
        guests_count = BookingGuest.objects.filter(**filter_kwargs).count()
        if guests_count > 0:
            BookingGuest.objects.filter(**filter_kwargs).delete()
            self.stdout.write(f"   Deleted {guests_count} BookingGuest records")
        
        # RoomBooking
        bookings_count = RoomBooking.objects.filter(
            internal_notes__contains=self.SEED_TAG,
            hotel=hotel
        ).count()
        if bookings_count > 0:
            RoomBooking.objects.filter(
                internal_notes__contains=self.SEED_TAG,
                hotel=hotel
            ).delete()
            self.stdout.write(f"   Deleted {bookings_count} RoomBooking records")
    
    def _ensure_hotel_config(self, hotel):
        """Ensure HotelAccessConfig exists with reasonable defaults."""
        config, created = HotelAccessConfig.objects.get_or_create(
            hotel=hotel,
            defaults={
                'standard_checkout_time': time(11, 0),
                'late_checkout_grace_minutes': 30,
                'approval_sla_minutes': 30
            }
        )
        if created:
            self.stdout.write(f"   Created HotelAccessConfig with defaults")
        else:
            self.stdout.write(f"   Using existing HotelAccessConfig")
    
    def _get_room_resources(self, hotel):
        """Get room type and room, creating minimal ones if needed."""
        # Get or create room type
        room_type = RoomType.objects.filter(hotel=hotel).first()
        if not room_type:
            room_type = RoomType.objects.create(
                hotel=hotel,
                name="Standard Room",
                code="STD",
                max_occupancy=2,
                starting_price_from=Decimal('100.00'),
                currency='EUR'
            )
            self.stdout.write(f"   Created RoomType: {room_type.name}")
        else:
            self.stdout.write(f"   Using RoomType: {room_type.name}")
        
        # Get or create room
        room = Room.objects.filter(hotel=hotel, is_active=True).order_by('room_number').first()
        if not room:
            # Try to create a room if the Room model allows it
            try:
                room = Room.objects.create(
                    hotel=hotel,
                    room_number=101,
                    room_type=room_type,
                    is_active=True
                )
                self.stdout.write(f"   Created Room: {room.room_number}")
            except Exception as e:
                raise CommandError(
                    f"❌ No active rooms exist for {hotel.name} and couldn't create one: {e}. "
                    "Please create at least one active Room first."
                )
        else:
            self.stdout.write(f"   Using Room: {room.room_number}")
        
        return room_type, room
    
    def _create_scenario_set(self, hotel, room_type, room, set_num):
        """Create one complete set of booking scenarios."""
        scenarios = []
        
        # Get reference dates (hotel timezone aware)
        now = timezone.now()
        tz = hotel.timezone_obj
        now_local = now.astimezone(tz)
        
        today = now_local.date()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        tomorrow = today + timedelta(days=1)
        
        # Helper functions for timezone handling
        def make_local_dt(date_obj, hour, minute=0):
            """Create timezone-aware datetime in hotel timezone, converted to UTC."""
            naive_dt = datetime.combine(date_obj, time(hour, minute))
            local_dt = tz.localize(naive_dt)
            return local_dt.astimezone(timezone.utc)
        
        def hotel_noon_utc(date_obj):
            """Get noon UTC for given date in hotel timezone."""
            return get_hotel_noon_utc(hotel, date_obj)
        
        # Get staff member for attributions (optional)
        staff_member = Staff.objects.filter(hotel=hotel).first()
        
        # Get multiple rooms to avoid conflicts
        available_rooms = list(Room.objects.filter(hotel=hotel, is_active=True).order_by('room_number')[:10])
        if len(available_rooms) < 5:  # We need at least 5 for scenarios E,F,G,H,I
            # Create additional rooms if needed
            for i in range(len(available_rooms), 5):
                new_room = Room.objects.create(
                    hotel=hotel,
                    room_number=101 + i,
                    room_type=room_type,
                    is_active=True
                )
                available_rooms.append(new_room)
            self.stdout.write(f"   Created {5 - len(available_rooms) + len(available_rooms)} additional rooms")
        
        # Scenario definitions with unique seed keys per set
        scenario_configs = [
            # A) PENDING_PAYMENT (not expired)
            {
                'key': 'A',
                'seed_key': f'pending_payment_set{set_num}',
                'status': 'PENDING_PAYMENT',
                'check_in': today + timedelta(days=2),
                'check_out': today + timedelta(days=4),
                'expires_at': now + timedelta(hours=2),  # Future
                'adults': 2, 'children': 0,
                'description': 'PENDING_PAYMENT (not expired)'
            },
            
            # B) PENDING_PAYMENT but expired
            {
                'key': 'B',
                'seed_key': f'pending_payment_expired_set{set_num}',
                'status': 'EXPIRED',
                'check_in': today + timedelta(days=1),
                'check_out': today + timedelta(days=3),
                'expires_at': now - timedelta(hours=1),  # Past
                'expired_at': now - timedelta(minutes=30),
                'adults': 1, 'children': 1,
                'description': 'PENDING_PAYMENT expired -> EXPIRED'
            },
            
            # C) PENDING_APPROVAL (overdue)
            {
                'key': 'C',
                'seed_key': f'pending_approval_overdue_set{set_num}',
                'status': 'PENDING_APPROVAL',
                'check_in': today + timedelta(days=1),
                'check_out': today + timedelta(days=3),
                'approval_deadline_at': now - timedelta(minutes=15),  # Past
                'payment_authorized_at': now - timedelta(hours=1),
                'adults': 2, 'children': 1,
                'description': 'PENDING_APPROVAL (approval overdue)'
            },
            
            # D) CONFIRMED upcoming with precheckin complete
            {
                'key': 'D',
                'seed_key': f'confirmed_upcoming_set{set_num}',
                'status': 'CONFIRMED',
                'check_in': tomorrow,
                'check_out': tomorrow + timedelta(days=2),
                'paid_at': now - timedelta(hours=6),
                'precheckin_submitted_at': make_local_dt(today, 13, 0),
                'adults': 2, 'children': 0,
                'description': 'CONFIRMED upcoming (precheckin complete)'
            },
            
            # E) IN_HOUSE checked-in, not overdue  
            {
                'key': 'E',
                'seed_key': f'in_house_ok_set{set_num}',
                'status': 'IN_HOUSE',
                'check_in': yesterday,
                'check_out': tomorrow,
                'checked_in_at': make_local_dt(yesterday, 15, 0),
                'paid_at': now - timedelta(days=2),
                'room_index': 0,  # First available room
                'adults': 1, 'children': 0,
                'description': 'IN_HOUSE checked-in (not overdue)'
            },
            
            # F) IN_HOUSE checked-in, checkout TODAY but NO incident (stable scenario)
            {
                'key': 'F',  
                'seed_key': f'in_house_overdue_no_incident_set{set_num}',
                'status': 'IN_HOUSE',
                'check_in': yesterday,
                'check_out': today,
                'checked_in_at': make_local_dt(yesterday, 15, 0),
                'paid_at': now - timedelta(days=2),
                'room_index': 1,  # Second room
                'adults': 2, 'children': 1,
                'skip_overstay_detection': True,  # Explicitly skip detection
                'description': 'IN_HOUSE overdue but no incident (detection not run)'
            },
            
            # G) IN_HOUSE checked-in, checkout YESTERDAY, overstay incident OPEN
            {
                'key': 'G',
                'seed_key': f'overstay_open_set{set_num}',
                'status': 'IN_HOUSE',
                'check_in': two_days_ago,
                'check_out': yesterday,
                'checked_in_at': make_local_dt(two_days_ago, 15, 0),
                'paid_at': now - timedelta(days=3),
                'room_index': 2,  # Third room
                'adults': 2, 'children': 0,
                'create_overstay': 'OPEN',
                'description': 'IN_HOUSE overstay incident OPEN'
            },
            
            # H) Same as G but incident ACKED
            {
                'key': 'H',
                'seed_key': f'overstay_acked_set{set_num}',
                'status': 'IN_HOUSE', 
                'check_in': two_days_ago,
                'check_out': yesterday,
                'checked_in_at': make_local_dt(two_days_ago, 15, 0),
                'paid_at': now - timedelta(days=3),
                'room_index': 3,  # Fourth room
                'adults': 1, 'children': 1,
                'create_overstay': 'ACKED',
                'description': 'IN_HOUSE overstay incident ACKED'
            },
            
            # I) Same as G but incident RESOLVED and checked out
            {
                'key': 'I',
                'seed_key': f'overstay_resolved_set{set_num}',
                'status': 'COMPLETED',
                'check_in': two_days_ago,
                'check_out': yesterday,
                'checked_in_at': make_local_dt(two_days_ago, 15, 0),
                'checked_out_at': now - timedelta(hours=2),
                'paid_at': now - timedelta(days=3),
                'assigned_room': room,
                'adults': 2, 'children': 0,
                'create_overstay': 'RESOLVED',
                'description': 'COMPLETED overstay incident RESOLVED'
            },
            
            # J) NO_SHOW booking
            {
                'key': 'J',
                'seed_key': f'no_show_set{set_num}',
                'status': 'NO_SHOW',
                'check_in': yesterday,
                'check_out': today,
                'paid_at': now - timedelta(days=2),
                'adults': 2, 'children': 0,
                'description': 'NO_SHOW booking'
            },
            
            # K) CANCELLED booking  
            {
                'key': 'K',
                'seed_key': f'cancelled_set{set_num}',
                'status': 'CANCELLED',
                'check_in': today + timedelta(days=3),
                'check_out': today + timedelta(days=5),
                'paid_at': now - timedelta(hours=12),
                'cancelled_at': now - timedelta(hours=2),
                'refunded_at': now - timedelta(hours=1),
                'refund_reference': f"re_{secrets.token_hex(8)}",
                'adults': 1, 'children': 0,
                'description': 'CANCELLED booking with refund'
            }
        ]
        
        # Create bookings for each scenario
        for config in scenario_configs:
            booking = self._create_booking_scenario(
                hotel, room_type, config, staff_member, set_num, available_rooms
            )
            scenarios.append({
                'key': config['key'],
                'booking': booking,
                'description': config['description']
            })
        
        return scenarios
    
    def _create_booking_scenario(self, hotel, room_type, config, staff_member, set_num, available_rooms):
        """Create a single booking scenario with all related objects."""
        # Generate hotel-specific booking ID using imported function
        booking_id = generate_booking_id(hotel)
        confirmation_number = f"{config['key']}{set_num:02d}{secrets.randbelow(9999):04d}"
        
        # Base booking fields
        booking_data = {
            'hotel': hotel,
            'room_type': room_type,
            'booking_id': booking_id,
            'confirmation_number': confirmation_number,
            'check_in': config['check_in'],
            'check_out': config['check_out'],
            'adults': config['adults'],
            'children': config['children'],
            'total_amount': Decimal('120.00') + (Decimal('25.00') * config['adults']),
            'currency': 'EUR',
            'status': config['status'],
            'primary_first_name': f"Guest{config['key']}{set_num}",
            'primary_last_name': "TestSeed",
            'primary_email': f"guest{config['key'].lower()}{set_num}@example.com",
            'primary_phone': f"+353-1-{config['key']}{set_num:02d}-{secrets.randbelow(999):03d}",
            'payment_provider': 'STRIPE',
            'payment_reference': f"pi_{secrets.token_hex(12)}",
            'internal_notes': f"{self.SEED_TAG} Scenario {config['key']}: {config['seed_key']}",
        }
        
        # Handle room assignment from room_index
        if 'room_index' in config and config['room_index'] < len(available_rooms):
            booking_data['assigned_room'] = available_rooms[config['room_index']]
        
        # Add optional fields based on scenario (excluding room-related ones)
        optional_fields = [
            'expires_at', 'expired_at', 'approval_deadline_at', 'payment_authorized_at',
            'paid_at', 'checked_in_at', 'checked_out_at', 'assigned_room',
            'precheckin_submitted_at', 'cancelled_at', 'refunded_at', 'refund_reference'
        ]
        
        for field in optional_fields:
            if field in config and field != 'assigned_room':  # Room handled above
                booking_data[field] = config[field]
            elif field == 'assigned_room' and field in config:
                booking_data[field] = config[field]  # Direct room assignment
        
        # Add staff attribution if available
        if staff_member:
            booking_data['staff_seen_by'] = staff_member
            booking_data['staff_seen_at'] = timezone.now() - timedelta(minutes=30)
        
        # Create booking
        booking = RoomBooking.objects.create(**booking_data)
        
        # Add precheckin payload if needed
        if config.get('precheckin_submitted_at'):
            booking.precheckin_payload = {
                "eta": "11:22",
                "consent_checkbox": True,
                "special_requests": "Late checkout if possible",
                "nationality": "IE", 
                "country_of_residence": "Ireland"
            }
            booking.save()
        
        # Ensure primary guest exists (may be auto-created by signal, but make sure)
        primary_guest, created = BookingGuest.objects.get_or_create(
            booking=booking,
            role='PRIMARY',
            defaults={
                'first_name': booking.primary_first_name,
                'last_name': booking.primary_last_name,
                'email': booking.primary_email,
                'phone': booking.primary_phone,
                'is_staying': True,
                'precheckin_payload': booking.precheckin_payload if booking.precheckin_submitted_at else {}
            }
        )
        
        # Create party (BookingGuest records for companions)
        self._create_booking_party(booking, config)
        
        # Create tokens  
        self._create_booking_tokens(booking, config)
        
        # Create overstay incident if specified
        if config.get('create_overstay'):
            self._create_overstay_incident(booking, config, staff_member)
        
        # Create booking extension for one scenario  
        if config['key'] == 'E' and set_num == 1:
            self._create_booking_extension(booking, staff_member)
        
        return booking
    
    def _create_booking_party(self, booking, config):
        """Create companion BookingGuest records (primary already exists)."""
        total_guests = config['adults'] + config['children']
        
        # Create companions only (primary guest created in main method)
        companions_needed = total_guests - 1  # Minus primary
        
        for i in range(2, total_guests + 1):
            is_adult = i <= config['adults']
            
            guest_data = {
                'booking': booking,
                'role': 'COMPANION',
                'first_name': f"Companion{i}",
                'last_name': booking.primary_last_name,
                'email': f"comp{i}@example.com" if is_adult else '',
                'phone': f"+353-1-{i:03d}-{secrets.randbelow(999):03d}" if is_adult else '',
                'is_staying': True,
            }
            
            # Add precheckin payload for companions if precheckin is complete
            if booking.precheckin_submitted_at:
                guest_data['precheckin_payload'] = {
                    "nationality": "IE",
                    "country_of_residence": "Ireland"
                }
            
            BookingGuest.objects.create(**guest_data)
    
    def _create_booking_tokens(self, booking, config):
        """Create various token types for the booking."""
        
        def end_of_day_utc(date_obj):
            """Convert date to end-of-day timezone-aware datetime in UTC."""
            tz = booking.hotel.timezone_obj
            local_dt = tz.localize(datetime.combine(date_obj, time(23, 59, 59)))
            return local_dt.astimezone(timezone.utc)
        
        # GuestBookingToken for status access
        guest_token_data = {
            'booking': booking,
            'hotel': booking.hotel,
            'scopes': ['STATUS_READ'],
            'expires_at': end_of_day_utc(booking.check_out + timedelta(days=30)),
            'status': 'ACTIVE'
        }
        
        raw_token = secrets.token_urlsafe(32)
        guest_token_data['token_hash'] = hashlib.sha256(raw_token.encode()).hexdigest()
        GuestBookingToken.objects.create(**guest_token_data)
        
        # BookingManagementToken for all bookings
        mgmt_token_data = {
            'booking': booking,
            'expires_at': end_of_day_utc(booking.check_out + timedelta(days=7))
        }
        
        raw_mgmt_token = secrets.token_urlsafe(32) 
        mgmt_token_data['token_hash'] = hashlib.sha256(raw_mgmt_token.encode()).hexdigest()
        BookingManagementToken.objects.create(**mgmt_token_data)
        
        # BookingPrecheckinToken for precheckin scenarios
        if booking.status in ['CONFIRMED', 'PENDING_APPROVAL', 'IN_HOUSE'] or config.get('precheckin_submitted_at'):
            precheckin_token_data = {
                'booking': booking,
                'expires_at': end_of_day_utc(booking.check_in + timedelta(days=2)),
                'config_snapshot_enabled': {},
                'config_snapshot_required': {}
            }
            
            # Mark as used if precheckin is complete
            if booking.precheckin_submitted_at:
                precheckin_token_data['used_at'] = booking.precheckin_submitted_at
            
            raw_precheckin_token = secrets.token_urlsafe(32)
            precheckin_token_data['token_hash'] = hashlib.sha256(raw_precheckin_token.encode()).hexdigest()
            BookingPrecheckinToken.objects.create(**precheckin_token_data)
    
    def _create_overstay_incident(self, booking, config, staff_member):
        """Create OverstayIncident with specified status."""
        incident_status = config['create_overstay']
        
        # Calculate detected_at as noon UTC on the day AFTER checkout (the detection day)
        detection_date = booking.check_out + timedelta(days=1)
        detected_at = get_hotel_noon_utc(booking.hotel, detection_date)
        
        incident_data = {
            'hotel': booking.hotel,
            'booking': booking,
            'expected_checkout_date': booking.check_out,
            'detected_at': detected_at,
            'status': incident_status,
            'severity': 'MEDIUM',
            'meta': {
                'room_number': booking.assigned_room.room_number if booking.assigned_room else None,
                'primary_guest_name': f"{booking.primary_first_name} {booking.primary_last_name}",
                'room_type': booking.room_type.name if booking.room_type else None
            }
        }
        
        # Add status-specific fields
        now = timezone.now()
        
        if incident_status in ['ACKED', 'RESOLVED']:
            incident_data['acknowledged_at'] = now - timedelta(hours=1)
            incident_data['acknowledged_by'] = staff_member
            incident_data['acknowledged_note'] = f"Acknowledged overstay for {booking.booking_id}"
        
        if incident_status == 'RESOLVED':
            incident_data['resolved_at'] = now - timedelta(minutes=30)
            incident_data['resolved_by'] = staff_member  
            incident_data['resolution_note'] = f"Guest checked out, booking completed"
        
        OverstayIncident.objects.create(**incident_data)
    
    def _create_booking_extension(self, booking, staff_member):
        """Create a sample BookingExtension record."""
        old_checkout = booking.check_out - timedelta(days=1)
        
        extension_data = {
            'hotel': booking.hotel,
            'booking': booking,
            'old_checkout_date': old_checkout,
            'new_checkout_date': booking.check_out,
            'added_nights': 1,
            'pricing_snapshot': {
                'base_rate': '100.00',
                'taxes': '20.00',
                'total': '120.00'
            },
            'amount_delta': Decimal('120.00'),
            'currency': 'EUR',
            'idempotency_key': f"ext_{booking.booking_id}_{secrets.token_hex(4)}",
            'status': 'CONFIRMED',
            'created_by': staff_member
        }
        
        BookingExtension.objects.create(**extension_data)
    
    def _print_summary(self, scenarios):
        """Print a clean summary table of all created scenarios."""
        self.stdout.write("\n📊 BOOKING SCENARIOS SUMMARY")
        self.stdout.write("=" * 100)
        
        # Header
        header = f"{'ID':<3} | {'Booking ID':<15} | {'Status':<17} | {'Check-In':<10} | {'Check-Out':<10} | {'In-House':<8} | {'Room':<6} | {'Incident':<10} | {'Description'}"
        self.stdout.write(header)
        self.stdout.write("-" * 100)
        
        # Rows
        for scenario in scenarios:
            booking = scenario['booking']
            key = scenario['key']
            
            # Determine in-house status
            in_house = "Yes" if (booking.checked_in_at and not booking.checked_out_at) else "No"
            
            # Determine room assignment
            room_display = f"#{booking.assigned_room.room_number}" if booking.assigned_room else "None"
            
            # Check for overstay incident
            incident = OverstayIncident.objects.filter(booking=booking).first()
            incident_status = incident.status if incident else "None"
            
            row = (
                f"{key:<3} | {booking.booking_id:<15} | {booking.status:<17} | "
                f"{booking.check_in} | {booking.check_out} | {in_house:<8} | "
                f"{room_display:<6} | {incident_status:<10} | {scenario['description']}"
            )
            self.stdout.write(row)
        
        self.stdout.write("-" * 100)
        
        # Validation summary
        self.stdout.write("\n✅ VALIDATION SUMMARY")
        
        total_bookings = len(scenarios)
        hotel_count = len(set(s['booking'].hotel.slug for s in scenarios))
        
        # Properly validate party completeness
        party_complete_count = 0
        for s in scenarios:
            booking = s['booking']
            expected = booking.adults + booking.children
            actual = BookingGuest.objects.filter(booking=booking, is_staying=True).count()
            if actual == expected:
                party_complete_count += 1
        
        precheckin_complete_count = sum(1 for s in scenarios if s['booking'].precheckin_submitted_at)
        checked_in_count = sum(1 for s in scenarios if s['booking'].checked_in_at and s['booking'].assigned_room)
        incident_count = sum(1 for s in scenarios if OverstayIncident.objects.filter(booking=s['booking']).exists())
        
        self.stdout.write(f"• Total bookings created: {total_bookings}")
        self.stdout.write(f"• All belong to no-way-hotel: {'✓' if hotel_count == 1 else '✗'}")
        self.stdout.write(f"• Party complete: {party_complete_count}/{total_bookings}")
        self.stdout.write(f"• Precheckin complete: {precheckin_complete_count}")  
        self.stdout.write(f"• Checked-in with room: {checked_in_count}")
        self.stdout.write(f"• Have overstay incidents: {incident_count}")
        
        # Scenario F validation (no incident by design)
        scenario_f_bookings = [s['booking'] for s in scenarios if s['key'] == 'F']
        for booking in scenario_f_bookings:
            incident_exists = OverstayIncident.objects.filter(booking=booking).exists()
            self.stdout.write(f"• Scenario F (no incident): Incident exists = {'✗ FAIL' if incident_exists else '✓ OK'}")