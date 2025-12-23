"""
Management command to send scheduled survey emails.

This command finds bookings that have scheduled survey send times that are due
and sends the survey emails. Designed to be run regularly via Heroku Scheduler
or cron.

Usage:
    python manage.py send_scheduled_surveys
    python manage.py send_scheduled_surveys --dry-run
    python manage.py send_scheduled_surveys --hotel-slug hotel-name
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from hotel.models import RoomBooking, HotelSurveyConfig, BookingSurveyToken
from django.conf import settings
from django.core.mail import send_mail
from datetime import timedelta
import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send scheduled survey emails that are due'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually sending emails'
        )
        parser.add_argument(
            '--hotel-slug',
            type=str,
            help='Target specific hotel by slug'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of surveys to send in one run'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hotel_slug = options['hotel_slug']
        limit = options['limit']
        
        now = timezone.now()
        
        # Build query for due bookings
        queryset = RoomBooking.objects.filter(
            survey_send_at__lte=now,  # Scheduled time has passed
            survey_sent_at__isnull=True,  # Not already sent
            status='COMPLETED'  # Only completed bookings
        ).select_related('hotel')
        
        if hotel_slug:
            queryset = queryset.filter(hotel__slug=hotel_slug)
            
        # Limit results to prevent overwhelming email systems
        due_bookings = queryset[:limit]
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN: Found {len(due_bookings)} bookings ready for survey emails')
            )
            for booking in due_bookings:
                self.stdout.write(f'  - {booking.booking_id} at {booking.hotel.name} (due: {booking.survey_send_at})')
            return
        
        success_count = 0
        error_count = 0
        
        for booking in due_bookings:
            try:
                self._send_scheduled_survey(booking)
                success_count += 1
                self.stdout.write(f'✓ Sent survey for booking {booking.booking_id}')
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to send survey for booking {booking.booking_id}: {e}')
                )
                logger.error(f'Failed to send scheduled survey for {booking.booking_id}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Survey sending complete: {success_count} sent, {error_count} errors'
            )
        )
    
    def _send_scheduled_survey(self, booking):
        """Send survey email for a single booking"""
        # Get hotel survey configuration
        hotel_config = HotelSurveyConfig.get_or_create_default(booking.hotel)
        
        # Check if survey should still be sent (config might have changed)
        if hotel_config.send_mode not in ['AUTO_DELAYED', 'AUTO_IMMEDIATE']:
            logger.info(f'Skipping survey for {booking.booking_id}: send_mode is {hotel_config.send_mode}')
            # Clear the schedule since it's no longer auto-send
            booking.survey_send_at = None
            booking.save(update_fields=['survey_send_at'])
            return
        
        # Determine target email
        target_email = booking.primary_email or booking.booker_email
        if not target_email:
            logger.warning(f'No email address found for booking {booking.booking_id}')
            # Mark as "sent" to prevent retry
            booking.survey_sent_at = timezone.now()
            booking.survey_send_at = None
            booking.save(update_fields=['survey_sent_at', 'survey_send_at'])
            return
        
        with transaction.atomic():
            # Generate secure token
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            expires_at = timezone.now() + timedelta(hours=hotel_config.token_expiry_hours)
            
            # Revoke any existing active tokens for this booking
            BookingSurveyToken.objects.filter(
                booking=booking,
                used_at__isnull=True,
                revoked_at__isnull=True
            ).update(revoked_at=timezone.now())
            
            # Create new token with config snapshot
            token = BookingSurveyToken.objects.create(
                booking=booking,
                token_hash=token_hash,
                expires_at=expires_at,
                sent_to_email=target_email,
                config_snapshot_enabled=hotel_config.fields_enabled.copy(),
                config_snapshot_required=hotel_config.fields_required.copy(),
                config_snapshot_send_mode=hotel_config.send_mode
            )
            
            # Send survey email
            base_domain = getattr(settings, 'FRONTEND_BASE_URL', 'https://hotelsmates.com')
            survey_url = f"{base_domain}/guest/hotel/{booking.hotel.slug}/survey?token={raw_token}"
            
            subject = hotel_config.email_subject_template or f\"Share your experience at {booking.hotel.name}\"
            
            if hotel_config.email_body_template:
                message = hotel_config.email_body_template.format(
                    guest_name=booking.primary_guest_name or 'Guest',
                    hotel_name=booking.hotel.name,
                    booking_id=booking.booking_id,
                    survey_url=survey_url,
                    expiry_days=hotel_config.token_expiry_hours // 24
                )
            else:
                message = f"""
Dear {booking.primary_guest_name or 'Guest'},

Thank you for staying with us at {booking.hotel.name}. We'd love to hear about your experience.

Booking: {booking.booking_id}
Dates: {booking.check_in} to {booking.check_out}

Please take a moment to share your feedback: {survey_url}

This survey takes less than a minute and helps us improve our service.

Your feedback link expires in {hotel_config.token_expiry_hours // 24} days.

Best regards,
{booking.hotel.name} Team
                """
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[target_email],
                    fail_silently=False,
                )
            except Exception as e:
                # If email fails, revoke the token for security
                token.revoked_at = timezone.now()
                token.save()
                raise e
            
            # Update booking audit fields
            booking.survey_sent_at = timezone.now()
            booking.survey_last_sent_to = target_email
            booking.survey_send_at = None  # Clear the schedule
            booking.save(update_fields=['survey_sent_at', 'survey_last_sent_to', 'survey_send_at'])