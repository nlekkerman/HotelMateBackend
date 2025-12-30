"""
Management command to expire unpaid room bookings.

This command safely expires bookings that are in PENDING_PAYMENT status
and have passed their expiration time. Uses database locking to avoid
race conditions and is safe to run frequently (every 1-5 minutes).

Usage:
    python manage.py expire_unpaid_bookings
    
Example cron/scheduler setup:
    */5 * * * * /usr/local/bin/python /app/manage.py expire_unpaid_bookings
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from hotel.models import RoomBooking
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Expire unpaid room bookings that have passed their expiration time'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be expired without making changes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of bookings to process per batch (default: 100)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        now = timezone.now()
        total_expired = 0
        
        # Process in batches to avoid holding locks too long
        while True:
            with transaction.atomic():
                # Find expired bookings with database locking
                # Use select_for_update(skip_locked=True) to avoid blocking other processes
                expired_bookings = list(
                    RoomBooking.objects.select_for_update(skip_locked=True).filter(
                        status__in=['PENDING_PAYMENT'],  # Only pending payment bookings
                        expires_at__isnull=False,        # Must have expiration time
                        expires_at__lt=now,              # Must be expired
                        paid_at__isnull=True             # Must not be paid
                    )[:batch_size]
                )
                
                if not expired_bookings:
                    break  # No more expired bookings to process
                
                batch_count = len(expired_bookings)
                
                if dry_run:
                    # In dry run, just show what would be expired
                    self.stdout.write(f'Would expire {batch_count} bookings:')
                    for booking in expired_bookings:
                        self.stdout.write(
                            f'  - {booking.booking_id} (expired: {booking.expires_at}, '
                            f'hotel: {booking.hotel.slug})'
                        )
                else:
                    # Actually expire the bookings
                    booking_ids = [booking.booking_id for booking in expired_bookings]
                    
                    # Bulk update for efficiency
                    RoomBooking.objects.filter(
                        id__in=[booking.id for booking in expired_bookings]
                    ).update(
                        status='CANCELLED_DRAFT',
                        cancelled_at=now
                    )
                    
                    # Log individual bookings for audit trail
                    for booking in expired_bookings:
                        logger.info(
                            f'Expired booking {booking.booking_id} '
                            f'(hotel: {booking.hotel.slug}, expired: {booking.expires_at})'
                        )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Expired {batch_count} bookings: {", ".join(booking_ids)}'
                        )
                    )
                
                total_expired += batch_count
                
                # Break if we processed fewer than the batch size (last batch)
                if batch_count < batch_size:
                    break
        
        # Summary message
        if total_expired == 0:
            self.stdout.write('No expired bookings found.')
        else:
            action = 'Would expire' if dry_run else 'Expired'
            self.stdout.write(
                self.style.SUCCESS(f'{action} {total_expired} total bookings.')
            )
            
            # Log summary for monitoring
            if not dry_run:
                logger.info(f'Booking expiration completed: {total_expired} bookings expired')