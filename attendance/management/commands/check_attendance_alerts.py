"""
Management command to check and send break/overtime alerts for all hotels.
This command should be run periodically (e.g., every 5-10 minutes) via cron or Celery.

Usage:
    python manage.py check_attendance_alerts
    python manage.py check_attendance_alerts --hotel=hotel-slug  # Check specific hotel only
    python manage.py check_attendance_alerts --dry-run          # Don't send actual alerts
"""

from django.core.management.base import BaseCommand
from django.utils.timezone import now
from hotel.models import Hotel
from attendance.utils import check_open_log_alerts_for_hotel


class Command(BaseCommand):
    help = 'Check and send break/overtime alerts for open clock logs across all hotels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel',
            type=str,
            help='Check alerts for specific hotel slug only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be alerted but do not send actual notifications',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each hotel processed',
        )

    def handle(self, *args, **options):
        start_time = now()
        
        if options['hotel']:
            # Check specific hotel
            try:
                hotel = Hotel.objects.get(slug=options['hotel'])
                hotels = [hotel]
            except Hotel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Hotel with slug "{options["hotel"]}" not found.')
                )
                return
        else:
            # Check all hotels
            hotels = Hotel.objects.filter(is_active=True)

        total_alerts = {
            'break_warnings': 0,
            'overtime_warnings': 0,
            'hard_limit_warnings': 0,
        }

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE: No actual alerts will be sent')
            )

        self.stdout.write(f'Checking attendance alerts for {hotels.count()} hotel(s)...')

        for hotel in hotels:
            if options['verbose']:
                self.stdout.write(f'Processing {hotel.name} ({hotel.slug})...')

            try:
                if options['dry_run']:
                    # In dry run mode, we'd need to implement a dry-run version
                    # of the alert checker or modify the existing one
                    self.stdout.write(f'  Would check alerts for {hotel.name}')
                    continue

                alerts_sent = check_open_log_alerts_for_hotel(hotel)
                
                # Accumulate totals
                for alert_type, count in alerts_sent.items():
                    total_alerts[alert_type] += count

                if options['verbose'] or any(alerts_sent.values()):
                    self.stdout.write(
                        f'  {hotel.name}: '
                        f'{alerts_sent["break_warnings"]} break, '
                        f'{alerts_sent["overtime_warnings"]} overtime, '
                        f'{alerts_sent["hard_limit_warnings"]} hard limit alerts sent'
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing {hotel.name}: {str(e)}'
                    )
                )
                if options['verbose']:
                    import traceback
                    self.stdout.write(traceback.format_exc())

        # Summary
        end_time = now()
        duration = (end_time - start_time).total_seconds()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Alert check completed in {duration:.2f}s. '
                f'Total alerts sent: '
                f'{total_alerts["break_warnings"]} break, '
                f'{total_alerts["overtime_warnings"]} overtime, '
                f'{total_alerts["hard_limit_warnings"]} hard limit'
            )
        )

        if sum(total_alerts.values()) == 0:
            self.stdout.write('No alerts were necessary at this time.')
        
        # Return status for monitoring systems
        return 0 if sum(total_alerts.values()) < 100 else 1  # Warn if too many alerts