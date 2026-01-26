"""
Auto-expire overdue bookings management command.

This command finds bookings in PENDING_APPROVAL status that have passed their 
approval deadline and automatically expires them with refund processing.

Run as a scheduled job (e.g., every 5-15 minutes) to enforce booking time controls.
"""
import stripe
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from hotel.models import RoomBooking
from apps.booking.services.booking_deadlines import compute_approval_cutoff


class Command(BaseCommand):
    help = 'Auto-expire overdue bookings that have passed their approval deadline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be expired without making changes',
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
        
        self.stdout.write(f"🔍 Checking for overdue bookings to expire...")
        if dry_run:
            self.stdout.write("🔥 DRY RUN MODE - No changes will be made")
        
        # Find bookings that have passed their hotel-configured approval cutoff
        # This is the hard expiry rule - SLA deadline is for warnings only
        now = timezone.now()
        
        # Get all PENDING_APPROVAL bookings and check their cutoff time
        candidate_bookings = RoomBooking.objects.filter(
            status='PENDING_APPROVAL',
            approval_deadline_at__isnull=False,
            expired_at__isnull=True  # Not already expired
        ).order_by('approval_deadline_at')
        
        # Filter by hotel-configured approval cutoff
        overdue_bookings = []
        for booking in candidate_bookings[:max_bookings * 2]:  # Check more to account for filtering
            approval_cutoff = compute_approval_cutoff(booking)
            if now > approval_cutoff:
                overdue_bookings.append(booking)
            if len(overdue_bookings) >= max_bookings:
                break
        
        if not overdue_bookings:
            self.stdout.write(self.style.SUCCESS("✅ No bookings past approval cutoff"))
            return
        
        # Convert to queryset for compatibility with existing code
        overdue_ids = [b.id for b in overdue_bookings]
        overdue_qs = RoomBooking.objects.filter(id__in=overdue_ids)
        
        if not overdue_qs.exists():
            self.stdout.write(self.style.SUCCESS("✅ No overdue bookings found"))
            return
        
        # Convert to list for iteration
        overdue_bookings = list(overdue_qs)
        
        self.stdout.write(f"📋 Found {len(overdue_bookings)} overdue booking(s)")
        
        expired_count = 0
        refunded_count = 0
        error_count = 0
        
        for booking in overdue_bookings:
            try:
                with transaction.atomic():
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
                    
                    # Double-check it still needs expiring (race condition protection)
                    if booking.expired_at is not None or booking.status != 'PENDING_APPROVAL':
                        continue
                    
                    # Recompute now inside transaction for precision
                    now = timezone.now()
                    approval_cutoff = compute_approval_cutoff(booking)
                    cutoff_overdue_minutes = int((now - approval_cutoff).total_seconds() / 60)
                    
                    # Show SLA vs cutoff for transparency
                    sla_overdue_minutes = int((now - booking.approval_deadline_at).total_seconds() / 60) if booking.approval_deadline_at else 0
                    
                    self.stdout.write(
                        f"⏰ Expiring booking {booking.booking_id} [{booking.hotel.slug}] "
                        f"(SLA overdue: {sla_overdue_minutes}min, cutoff overdue: {cutoff_overdue_minutes}min)"
                    )
                    
                    if not dry_run:
                        # Process refund if payment was made
                        refund_processed = False
                        if (booking.paid_at and 
                            booking.payment_intent_id and 
                            booking.refunded_at is None and
                            booking.payment_provider == 'stripe'):
                            
                            try:
                                # Configure Stripe
                                stripe.api_key = settings.STRIPE_SECRET_KEY
                                
                                # Create idempotent refund in Stripe
                                idempotency_key = f"autoexpire:{booking.booking_id}:{booking.payment_intent_id}"
                                refund = stripe.Refund.create(
                                    payment_intent=booking.payment_intent_id,
                                    reason='expired',
                                    idempotency_key=idempotency_key,
                                    metadata={
                                        'booking_id': booking.booking_id,
                                        'hotel_slug': booking.hotel.slug,
                                        'auto_expired': 'true',
                                        'cutoff_overdue_minutes': str(cutoff_overdue_minutes),
                                        'sla_overdue_minutes': str(sla_overdue_minutes)
                                    }
                                )
                                
                                # Record refund details
                                booking.refunded_at = now
                                booking.refund_reference = refund.id
                                refund_processed = True
                                refunded_count += 1
                                
                                self.stdout.write(f"💰 Refund processed: {refund.id}")
                                
                            except stripe.error.StripeError as e:
                                self.stdout.write(
                                    self.style.WARNING(f"⚠️ Refund failed for {booking.booking_id}: {e}")
                                )
                                # Continue with expiry even if refund fails
                        
                        # Expire the booking
                        booking.status = 'EXPIRED'
                        booking.expired_at = now
                        booking.auto_expire_reason_code = 'APPROVAL_TIMEOUT'
                        booking.save(update_fields=[
                            'status', 'expired_at', 'auto_expire_reason_code',
                            'refunded_at', 'refund_reference'
                        ])
                        
                        # Send real-time notification to staff
                        try:
                            from notifications.notification_manager import notification_manager
                            notification_manager.realtime_booking_updated(booking)
                            self.stdout.write(f"📡 Staff notification sent for {booking.booking_id}")
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"⚠️ Notification failed: {e}")
                            )
                        
                        # TODO: Send guest email notification about expiry and refund
                        
                        expired_count += 1
                        self.stdout.write(f"✅ Expired booking {booking.booking_id}")
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ Error processing {booking.booking_id}: {e}")
                )
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"🔥 DRY RUN: Would expire {len(overdue_bookings)} booking(s)")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Processed {expired_count} expired bookings, "
                    f"{refunded_count} refunds, {error_count} errors"
                )
            )