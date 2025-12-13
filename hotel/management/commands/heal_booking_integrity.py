"""
Management command to heal booking integrity issues.

Usage:
    python manage.py heal_booking_integrity --hotel hotel-slug
    python manage.py heal_booking_integrity --all-hotels
    python manage.py heal_booking_integrity --hotel hotel-slug --dry-run
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from hotel.models import Hotel
from hotel.services.booking_integrity import heal_all_bookings_for_hotel, check_hotel_integrity
from notifications.notification_manager import NotificationManager


class Command(BaseCommand):
    help = 'Heal booking integrity issues for hotels'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel',
            type=str,
            help='Hotel slug to heal (e.g., hotel-killarney)'
        )
        
        parser.add_argument(
            '--all-hotels',
            action='store_true',
            help='Heal all hotels'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each booking'
        )
    
    def handle(self, *args, **options):
        hotel_slug = options.get('hotel')
        all_hotels = options.get('all_hotels')
        dry_run = options.get('dry_run')
        verbose = options.get('verbose')
        
        if not hotel_slug and not all_hotels:
            raise CommandError('Must specify either --hotel <slug> or --all-hotels')
        
        if hotel_slug and all_hotels:
            raise CommandError('Cannot specify both --hotel and --all-hotels')
        
        # Determine which hotels to process
        if all_hotels:
            hotels = Hotel.objects.filter(is_active=True)
            self.stdout.write(f"Processing all {hotels.count()} active hotels...")
        else:
            try:
                hotels = [Hotel.objects.get(slug=hotel_slug)]
                self.stdout.write(f"Processing hotel: {hotels[0].name}")
            except Hotel.DoesNotExist:
                raise CommandError(f'Hotel with slug "{hotel_slug}" not found')
        
        # Initialize notification manager (but don't send notifications in dry-run mode)
        notification_manager = NotificationManager() if not dry_run else None
        
        total_stats = {
            "hotels_processed": 0,
            "bookings_processed": 0,
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "demoted": 0
        }
        
        for hotel in hotels:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Processing Hotel: {hotel.name} ({hotel.slug})")
            self.stdout.write(f"{'='*60}")
            
            if dry_run:
                # In dry-run mode, just check for issues
                issues = check_hotel_integrity(hotel)
                
                if not issues:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ No integrity issues found for {hotel.name}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠ Found {len(issues)} integrity issues for {hotel.name}")
                    )
                    
                    if verbose:
                        for issue in issues:
                            self.stdout.write(f"  - Booking {issue['booking_id']}: {issue['error']}")
                    
                    total_stats["bookings_processed"] += len(issues)
            
            else:
                # Actually perform the healing
                try:
                    with transaction.atomic():
                        # Disable notifications in dry-run mode
                        report = heal_all_bookings_for_hotel(hotel, notify=True)
                        
                        # Update totals
                        total_stats["hotels_processed"] += 1
                        total_stats["bookings_processed"] += report["bookings_processed"]
                        total_stats["created"] += report["created"]
                        total_stats["updated"] += report["updated"]
                        total_stats["deleted"] += report["deleted"]
                        total_stats["demoted"] += report["demoted"]
                        
                        # Print summary for this hotel
                        self.stdout.write(f"Bookings processed: {report['bookings_processed']}")
                        self.stdout.write(f"Records created: {report['created']}")
                        self.stdout.write(f"Records updated: {report['updated']}")
                        self.stdout.write(f"Records deleted: {report['deleted']}")
                        self.stdout.write(f"Records demoted: {report['demoted']}")
                        
                        # Show notes if verbose or if there were changes
                        if verbose or any(report[k] > 0 for k in ["created", "updated", "deleted", "demoted"]):
                            if report["notes"]:
                                self.stdout.write(f"\nChanges made:")
                                for note in report["notes"]:
                                    self.stdout.write(f"  - {note}")
                        
                        # Send notifications if changes were made
                        if notification_manager and any(report[k] > 0 for k in ["created", "updated", "deleted", "demoted"]):
                            self._send_healing_notifications(notification_manager, hotel, report)
                        
                        if report["created"] + report["updated"] + report["deleted"] + report["demoted"] == 0:
                            self.stdout.write(
                                self.style.SUCCESS(f"✓ No issues found - {hotel.name} is healthy")
                            )
                        else:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✓ Healed {hotel.name} - "
                                    f"{sum(report[k] for k in ['created', 'updated', 'deleted', 'demoted'])} fixes applied"
                                )
                            )
                
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Error healing {hotel.name}: {str(e)}")
                    )
                    continue
        
        # Print final summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"FINAL SUMMARY ({'DRY RUN' if dry_run else 'COMPLETED'})")
        self.stdout.write(f"{'='*60}")
        
        if dry_run:
            if total_stats["bookings_processed"] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"Found {total_stats['bookings_processed']} bookings with integrity issues across {len(hotels)} hotels"
                    )
                )
                self.stdout.write("Re-run without --dry-run to fix these issues")
            else:
                self.stdout.write(
                    self.style.SUCCESS("No integrity issues found across all hotels")
                )
        else:
            self.stdout.write(f"Hotels processed: {total_stats['hotels_processed']}")
            self.stdout.write(f"Bookings processed: {total_stats['bookings_processed']}")
            self.stdout.write(f"Total records created: {total_stats['created']}")
            self.stdout.write(f"Total records updated: {total_stats['updated']}")
            self.stdout.write(f"Total records deleted: {total_stats['deleted']}")
            self.stdout.write(f"Total records demoted: {total_stats['demoted']}")
            
            if total_stats["created"] + total_stats["updated"] + total_stats["deleted"] + total_stats["demoted"] == 0:
                self.stdout.write(
                    self.style.SUCCESS("All hotels are healthy - no fixes needed")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Healing complete - {sum(total_stats[k] for k in ['created', 'updated', 'deleted', 'demoted'])} total fixes applied"
                    )
                )
    
    def _send_healing_notifications(self, notification_manager, hotel, report):
        """
        Send realtime notifications for significant healing changes.
        Only sends notifications for changes that affect user-visible state.
        """
        try:
            # Count significant changes (creation of guests, major updates)
            significant_changes = report["created"] + report["demoted"]
            
            if significant_changes > 0:
                # Send a general integrity healing notification
                # This is a new event type we'll add to notification_manager
                notification_data = {
                    "hotel_slug": hotel.slug,
                    "changes_applied": {
                        "created": report["created"],
                        "updated": report["updated"],
                        "deleted": report["deleted"],
                        "demoted": report["demoted"]
                    },
                    "bookings_affected": report["bookings_processed"]
                }
                
                # For now, we'll use a generic realtime event
                # In a full implementation, we'd add this to NotificationManager
                self.stdout.write(
                    f"Would send healing notification for {hotel.name} "
                    f"(created: {report['created']}, updated: {report['updated']}, "
                    f"deleted: {report['deleted']}, demoted: {report['demoted']})"
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Failed to send healing notification: {str(e)}")
            )