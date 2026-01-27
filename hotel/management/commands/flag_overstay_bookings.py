"""
Detect overstay incidents using configurable checkout deadline management command.

This command finds IN_HOUSE bookings that have passed their checkout deadline 
and creates OverstayIncident records for staff attention.

Run as a scheduled job (e.g., every 15-30 minutes) to monitor overstay situations.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from hotel.models import Hotel
from room_bookings.services.overstay import detect_overstays


class Command(BaseCommand):
    help = 'Detect overstay incidents using configurable checkout deadline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be detected without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🔍 Detecting overstay incidents using configurable checkout deadline...")
        if dry_run:
            self.stdout.write("🔥 DRY RUN MODE - No changes will be made")
        
        now_utc = timezone.now()
        
        # Get all hotels
        hotels = Hotel.objects.all()
        
        if not hotels.exists():
            self.stdout.write(self.style.ERROR("❌ No hotels found"))
            return
        
        hotels_processed = 0
        incidents_created_total = 0
        hotels_with_incidents = []
        error_count = 0
        
        for hotel in hotels:
            try:
                self.stdout.write(f"🏨 Processing hotel: {hotel.slug}")
                
                if not dry_run:
                    incidents_created = detect_overstays(hotel, now_utc)
                else:
                    # For dry run, we'll simulate by checking what would be detected
                    # without actually creating incidents
                    incidents_created = self._count_potential_overstays(hotel, now_utc)
                
                hotels_processed += 1
                incidents_created_total += incidents_created
                
                if incidents_created > 0:
                    hotels_with_incidents.append({
                        'slug': hotel.slug,
                        'count': incidents_created
                    })
                    self.stdout.write(f"  ✅ Created {incidents_created} overstay incident(s)")
                else:
                    self.stdout.write(f"  ℹ️ No new overstay incidents")
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Error processing hotel {hotel.slug}: {e}")
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"🔥 DRY RUN SUMMARY:\n"
                    f"   Hotels processed: {hotels_processed}\n"
                    f"   Potential incidents: {incidents_created_total}\n"
                    f"   Errors: {error_count}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ PROCESSING COMPLETE:\n"
                    f"   Hotels processed: {hotels_processed}\n"
                    f"   Incidents created: {incidents_created_total}\n"
                    f"   Errors: {error_count}"
                )
            )
        
        if hotels_with_incidents:
            self.stdout.write("\n📊 INCIDENTS BY HOTEL:")
            for hotel_info in hotels_with_incidents:
                self.stdout.write(f"   {hotel_info['slug']}: {hotel_info['count']} incidents")
                
    def _count_potential_overstays(self, hotel, now_utc):
        """Count bookings that would trigger overstay incidents (for dry run)."""
        from room_bookings.services.overstay import compute_checkout_deadline_at
        from hotel.models import RoomBooking, OverstayIncident
        
        count = 0
        current_date_utc = now_utc.date()
        
        # Find IN_HOUSE bookings that should have checked out
        # IN_HOUSE = checked_in_at is not null AND checked_out_at is null
        in_house_bookings = RoomBooking.objects.filter(
            hotel=hotel,
            checked_in_at__isnull=False,  # Must be checked in
            checked_out_at__isnull=True,  # Still checked in (not checked out)
            assigned_room__isnull=False,  # Must have assigned room
            check_out__lte=current_date_utc  # Checkout date has passed (today or earlier)
        ).select_related('assigned_room', 'hotel')
        
        for booking in in_house_bookings:
            # Check if checkout deadline has passed using hotel configuration
            checkout_deadline_utc = compute_checkout_deadline_at(booking)
            
            if now_utc >= checkout_deadline_utc:
                # Check if already has active incident
                existing_incident = OverstayIncident.objects.filter(
                    booking=booking,
                    status__in=['OPEN', 'ACKED']
                ).first()
                
                if not existing_incident:
                    count += 1
        
        return count