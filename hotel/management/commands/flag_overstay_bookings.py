"""
Flag overstay bookings management command.

This command finds bookings in IN_HOUSE status that have passed their checkout 
deadline and flags them for staff attention with real-time alerts.

Run as a scheduled job (e.g., every 15-30 minutes) to monitor overstay situations.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from hotel.models import RoomBooking
from apps.booking.services.stay_time_rules import should_flag_overstay, compute_checkout_deadline


class Command(BaseCommand):
    help = 'Flag bookings that are in overstay (past checkout deadline)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be flagged without making changes',
        )
        parser.add_argument(
            '--max-bookings',
            type=int,
            default=200,
            help='Maximum number of bookings to process in one run',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        max_bookings = options['max_bookings']
        
        self.stdout.write(f"🔍 Checking for overstay situations...")
        if dry_run:
            self.stdout.write("🔥 DRY RUN MODE - No changes will be made")
        
        now = timezone.now()
        
        # Find potentially overstaying bookings
        # Start with checked-in bookings on or past checkout date (cheap pre-filter)
        candidate_qs = RoomBooking.objects.filter(
            checked_in_at__isnull=False,  # Must be checked in
            checked_out_at__isnull=True,  # Still checked in
            check_out__lte=now.date(),    # Checkout date today or past
            overstay_flagged_at__isnull=True  # Not already flagged
        ).order_by('check_out')[:max_bookings]
        
        if not candidate_qs.exists():
            self.stdout.write(self.style.SUCCESS("✅ No potential overstay bookings found"))
            return
        
        # Convert to list for iteration
        candidate_bookings = list(candidate_qs)
        
        self.stdout.write(f"📋 Found {len(candidate_bookings)} candidate booking(s) to check")
        
        flagged_count = 0
        error_count = 0
        
        for booking in candidate_bookings:
            try:
                with transaction.atomic():
                    # Recompute now inside transaction for precision
                    now = timezone.now()
                    
                    # Lock the booking for update with skip_locked for concurrent job safety
                    booking = (
                        RoomBooking.objects
                        .select_for_update(skip_locked=True)
                        .filter(id=booking.id)
                        .first()
                    )
                    
                    # Skip if locked by another job instance
                    if not booking:
                        continue
                    
                    # Race protection: re-check if already flagged after lock
                    if booking.overstay_flagged_at is not None:
                        continue
                    
                    # Check if this booking should be flagged for overstay
                    if not should_flag_overstay(booking):
                        continue
                    
                    # Calculate how much they're overstaying
                    checkout_deadline = compute_checkout_deadline(booking)
                    overstay_minutes = int((now - checkout_deadline).total_seconds() / 60)
                    
                    self.stdout.write(
                        f"🚨 Flagging overstay: {booking.booking_id} "
                        f"[{booking.hotel.slug}] (overdue by {overstay_minutes} minutes)"
                    )
                    
                    if not dry_run:
                        # Flag the overstay
                        booking.overstay_flagged_at = now
                        booking.save(update_fields=['overstay_flagged_at'])
                        
                        # Send real-time alert to staff
                        try:
                            from notifications.notification_manager import notification_manager
                            
                            # Send booking update
                            notification_manager.realtime_booking_updated(booking)
                            
                            # Send specific overstay alert to relevant staff
                            alert_data = {
                                'type': 'overstay_alert',
                                'booking_id': booking.booking_id,
                                'room_number': booking.assigned_room.room_number if booking.assigned_room else None,
                                'guest_name': f"{booking.primary_first_name} {booking.primary_last_name}",
                                'overstay_minutes': overstay_minutes,
                                'checkout_deadline': checkout_deadline.isoformat(),
                                'hotel_slug': booking.hotel.slug,
                                'check_out_date': booking.check_out.isoformat(),
                            }
                            
                            # Send to hotel staff channel (receptionists, managers)
                            notification_manager.send_staff_notification(
                                hotel=booking.hotel,
                                title="Overstay Alert",
                                message=f"Room {booking.assigned_room.room_number if booking.assigned_room else '?'}: Guest {alert_data['guest_name']} is {overstay_minutes} minutes past checkout",
                                data=alert_data,
                                roles=['reception', 'manager']  # Target specific roles
                            )
                            
                            self.stdout.write(f"📡 Overstay alert sent for {booking.booking_id}")
                            
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"⚠️ Alert notification failed: {e}")
                            )
                        
                        flagged_count += 1
                        self.stdout.write(f"✅ Flagged overstay for {booking.booking_id}")
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Error processing {booking.booking_id}: {e}")
                )
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"🔥 DRY RUN: Found {len(candidate_bookings)} candidate bookings to check")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Processed {flagged_count} overstay flags, {error_count} errors"
                )
            )
            
        # Additional info: show bookings approaching overstay
        if not dry_run:
            approaching_bookings = RoomBooking.objects.filter(
                checked_in_at__isnull=False,  # Must be checked in
                checked_out_at__isnull=True,  # Still checked in
                check_out=now.date(),  # Checkout today
                overstay_flagged_at__isnull=True
            ).count()
            
            if approaching_bookings > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"ℹ️ {approaching_bookings} booking(s) have checkout today and may need attention"
                    )
                )