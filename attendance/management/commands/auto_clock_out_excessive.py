"""
Auto Clock-Out Management Command for Heroku Scheduler
Forces clock-out for staff with excessive hours (24+ hours).

Usage on Heroku Scheduler (run every 30 minutes):
    python manage.py auto_clock_out_excessive

Usage with options:
    python manage.py auto_clock_out_excessive --max-hours=20 --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils.timezone import now
from hotel.models import Hotel
from attendance.models import ClockLog
from staff.pusher_utils import trigger_clock_status_update
from staff.pusher_utils import trigger_attendance_log


class Command(BaseCommand):
    help = 'Automatically clock-out staff with excessive hours (24+ by default)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-hours',
            type=float,
            default=24.0,
            help='Maximum allowed hours before auto clock-out (default: 24.0)',
        )
        parser.add_argument(
            '--hotel',
            type=str,
            help='Only process specific hotel slug',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be clocked out but do not actually do it',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force clock-out even if warnings were not sent',
        )

    def handle(self, *args, **options):
        max_hours = options['max_hours']
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(f"🤖 Auto Clock-Out System - Max Hours: {max_hours}")
        if dry_run:
            self.stdout.write("🧪 DRY RUN MODE - No actual changes will be made")
        
        # Get hotels to process
        if options['hotel']:
            try:
                hotels = [Hotel.objects.get(slug=options['hotel'])]
                self.stdout.write(f"🏨 Processing single hotel: {options['hotel']}")
            except Hotel.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Hotel "{options["hotel"]}" not found'))
                return
        else:
            hotels = Hotel.objects.all()
            self.stdout.write(f"🏨 Processing {hotels.count()} hotels")
        
        total_clocked_out = 0
        total_found = 0
        
        for hotel in hotels:
            clocked_out = self.process_hotel(hotel, max_hours, dry_run, force)
            total_clocked_out += clocked_out['clocked_out']
            total_found += clocked_out['found']
            
            if clocked_out['found'] > 0:
                self.stdout.write(
                    f"  {hotel.name}: {clocked_out['found']} excessive, "
                    f"{clocked_out['clocked_out']} auto-clocked-out"
                )
        
        if total_found == 0:
            self.stdout.write("✅ No excessive sessions found")
        else:
            self.stdout.write(
                f"🎯 TOTAL: {total_found} excessive sessions, "
                f"{total_clocked_out} auto-clocked-out"
            )

    def process_hotel(self, hotel, max_hours, dry_run, force):
        """Process excessive sessions for a specific hotel"""
        current_time = now()
        
        # Find open logs with excessive hours
        open_logs = ClockLog.objects.filter(
            hotel=hotel,
            time_out__isnull=True,
            is_approved=True,  # Only process approved logs
            is_rejected=False
        ).select_related('staff')
        
        excessive_logs = []
        for log in open_logs:
            duration_hours = (current_time - log.time_in).total_seconds() / 3600
            if duration_hours >= max_hours:
                # Only auto-clock-out if hard limit warning was sent OR force flag
                if log.hard_limit_warning_sent or force:
                    excessive_logs.append((log, duration_hours))
        
        results = {
            'found': len(excessive_logs),
            'clocked_out': 0
        }
        
        for log, duration_hours in excessive_logs:
            staff_name = f"{log.staff.first_name} {log.staff.last_name}"
            
            if dry_run:
                self.stdout.write(
                    f"    🔴 WOULD CLOCK OUT: {staff_name} - {duration_hours:.1f}h"
                )
                continue
            
            # FORCE CLOCK-OUT
            try:
                # Close the session
                log.time_out = current_time
                log.long_session_ack_mode = 'auto_clocked_out'
                log.auto_clock_out = True
                log.save(update_fields=['time_out', 'long_session_ack_mode', 'auto_clock_out'])
                
                # Update staff status
                log.staff.duty_status = 'off_duty'
                log.staff.is_on_duty = False
                log.staff.save(update_fields=['duty_status', 'is_on_duty'])
                
                # Send real-time notifications
                trigger_clock_status_update(hotel.slug, log.staff, "clock_out")
                
                # Log the attendance change
                trigger_attendance_log(
                    hotel.slug,
                    {
                        'id': log.id,
                        'staff_id': log.staff.id,
                        'staff_name': staff_name,
                        'department': log.staff.department.name if log.staff.department else None,
                        'time': log.time_out,
                        'verified_by_face': False,
                        'auto_clock_out': True,
                        'reason': f'Auto clock-out after {duration_hours:.1f} hours'
                    },
                    "auto_clock_out"
                )
                
                results['clocked_out'] += 1
                
                self.stdout.write(
                    f"    ✅ AUTO CLOCKED OUT: {staff_name} - {duration_hours:.1f}h"
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"    ❌ FAILED to clock out {staff_name}: {str(e)}"
                    )
                )
        
        return results