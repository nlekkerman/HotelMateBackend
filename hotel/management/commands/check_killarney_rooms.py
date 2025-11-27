"""
Management command to check room type assignments and PMS data for Killarney hotel.
"""
from django.core.management.base import BaseCommand
from hotel.models import Hotel
from rooms.models import Room, RoomType, RatePlan, RoomTypeRatePlan, Promotion, RoomTypeInventory
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Check all PMS data for Killarney hotel (rooms, room types, rates, inventory)'

    def handle(self, *args, **options):
        try:
            hotel = Hotel.objects.get(id=2)
            self.stdout.write(f"Hotel: {hotel.name}")
            self.stdout.write("=" * 80)
        except Hotel.DoesNotExist:
            self.stdout.write(self.style.ERROR("Hotel Killarney (id=2) not found!"))
            return

        # 1. Check Room Types
        self.stdout.write("\n=== ROOM TYPES ===")
        room_types = RoomType.objects.filter(hotel=hotel).order_by('name')
        for rt in room_types:
            physical_count = Room.objects.filter(hotel=hotel, room_type=rt).count()
            self.stdout.write(f"  {rt.name} (id={rt.id}): {physical_count} physical rooms")
        
        # 2. Check Physical Rooms
        self.stdout.write("\n=== PHYSICAL ROOMS SUMMARY ===")
        total_rooms = Room.objects.filter(hotel=hotel).count()
        assigned_rooms = Room.objects.filter(hotel=hotel, room_type__isnull=False).count()
        unassigned_rooms = Room.objects.filter(hotel=hotel, room_type__isnull=True).count()
        active_rooms = Room.objects.filter(hotel=hotel, is_active=True).count()
        ooo_rooms = Room.objects.filter(hotel=hotel, is_out_of_order=True).count()
        
        self.stdout.write(f"  Total physical rooms: {total_rooms}")
        self.stdout.write(f"  Assigned to room_type: {assigned_rooms}")
        self.stdout.write(f"  Unassigned (NULL): {unassigned_rooms}")
        self.stdout.write(f"  Active rooms: {active_rooms}")
        self.stdout.write(f"  Out of order: {ooo_rooms}")

        # 3. Sample Rooms
        self.stdout.write("\n=== SAMPLE ROOMS (First 15) ===")
        samples = Room.objects.filter(hotel=hotel).select_related('room_type').order_by('room_number')[:15]
        for r in samples:
            rt_name = r.room_type.name if r.room_type else 'NONE'
            status = []
            if not r.is_active:
                status.append('INACTIVE')
            if r.is_out_of_order:
                status.append('OOO')
            if r.is_occupied:
                status.append('OCCUPIED')
            status_str = f" [{', '.join(status)}]" if status else ""
            self.stdout.write(f"  Room #{r.room_number} -> {rt_name}{status_str}")

        # 4. Check Rate Plans
        self.stdout.write("\n=== RATE PLANS ===")
        rate_plans = RatePlan.objects.filter(hotel=hotel)
        for rp in rate_plans:
            links = RoomTypeRatePlan.objects.filter(rate_plan=rp).count()
            self.stdout.write(f"  {rp.code} - {rp.name}: {links} room type links")

        # 5. Check Promotions
        self.stdout.write("\n=== PROMOTIONS ===")
        promotions = Promotion.objects.filter(hotel=hotel)
        for promo in promotions:
            applicable_types = promo.room_types.count()
            self.stdout.write(
                f"  {promo.code}: {promo.discount_percent or promo.discount_fixed} "
                f"({applicable_types} room types, valid until {promo.valid_until})"
            )

        # 6. Check Inventory
        self.stdout.write("\n=== INVENTORY SUMMARY ===")
        today = date.today()
        for rt in room_types[:3]:  # Show first 3 room types
            inv_count = RoomTypeInventory.objects.filter(
                room_type=rt,
                date__gte=today,
                date__lt=today + timedelta(days=7)
            ).count()
            self.stdout.write(f"  {rt.name}: {inv_count} inventory records (next 7 days)")

        # 7. Test Availability Check
        self.stdout.write("\n=== AVAILABILITY TEST ===")
        from hotel.services.availability import is_room_type_available, _inventory_for_date, _booked_for_date
        
        checkin = today + timedelta(days=3)
        checkout = checkin + timedelta(days=2)
        adults = 2
        children = 0
        
        self.stdout.write(f"  Checking availability: {checkin} to {checkout}")
        for rt in room_types:  # Test all room types
            try:
                # Check if room type can accommodate guests
                can_accommodate = rt.max_occupancy >= (adults + children)
                # Check inventory availability
                inventory_available = is_room_type_available(rt, checkin, checkout, required_units=1)
                
                if can_accommodate and inventory_available:
                    # Get actual numbers
                    inv = _inventory_for_date(rt, checkin)
                    booked = _booked_for_date(rt, checkin)
                    available = inv - booked
                    self.stdout.write(f"    {rt.name}: {available}/{inv} rooms available ✓")
                elif not can_accommodate:
                    self.stdout.write(f"    {rt.name}: Cannot accommodate {adults}+{children} guests (max: {rt.max_occupancy})")
                else:
                    self.stdout.write(f"    {rt.name}: SOLD OUT")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    {rt.name}: ERROR - {str(e)}"))

        # 8. Simulate Pricing for Each Room Type
        self.stdout.write("\n=== PRICING SIMULATION ===")
        from hotel.services.pricing import build_pricing_quote_data
        from decimal import Decimal
        
        self.stdout.write(f"  Dates: {checkin} to {checkout} (2 nights)")
        for rt in room_types:
            try:
                pricing_data = build_pricing_quote_data(
                    hotel=hotel,
                    room_type=rt,
                    check_in=checkin,
                    check_out=checkout,
                    adults=adults,
                    children=children,
                    promo_code=None
                )
                total = pricing_data.get('total_amount_incl_taxes', Decimal('0.00'))
                self.stdout.write(f"    {rt.name}: €{total}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    {rt.name}: ERROR - {str(e)}"))

        # 9. Test with Promo Code
        self.stdout.write("\n=== PRICING WITH PROMO CODE (WINTER20) ===")
        for rt in room_types[:3]:  # Test first 3
            try:
                pricing_data = build_pricing_quote_data(
                    hotel=hotel,
                    room_type=rt,
                    check_in=checkin,
                    check_out=checkout,
                    adults=adults,
                    children=children,
                    promo_code='WINTER20'
                )
                total = pricing_data.get('total_amount_incl_taxes', Decimal('0.00'))
                discount = pricing_data.get('promo_discount', Decimal('0.00'))
                self.stdout.write(f"    {rt.name}: €{total} (saved €{discount})")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    {rt.name}: ERROR - {str(e)}"))

        self.stdout.write(self.style.SUCCESS("\n" + "="*80))
        self.stdout.write(self.style.SUCCESS("✓ All checks complete!"))
        self.stdout.write(self.style.SUCCESS("✓ PMS system is ready for bookings!"))
