"""
One-time cleanup command for orphaned guests.

This command finds and fixes guests that are assigned to rooms but have no booking
(booking IS NULL). This is the exact corrupted state that causes the Room 337 ghost bug.

Usage:
    python manage.py cleanup_orphaned_guests --dry-run  # See what would be cleaned
    python manage.py cleanup_orphaned_guests --hotel-slug test-hotel  # Target specific hotel
    python manage.py cleanup_orphaned_guests  # Actually perform cleanup
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from guests.models import Guest


class Command(BaseCommand):
    help = 'Clean up orphaned guests (room assigned but no booking) - fixes Room 337 ghost bug'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel-slug',
            type=str,
            help='Target specific hotel by slug (optional)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without making changes'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about each orphaned guest'
        )
    
    def handle(self, *args, **options):
        """Execute the cleanup command."""
        
        # Target: Guests with room assigned but no booking (INVALID STATE)
        queryset = Guest.objects.filter(
            room__isnull=False,  # Has room assigned
            booking__isnull=True  # But no booking link (orphaned/ghost state)
        ).select_related('room', 'hotel')
        
        # Filter by hotel if specified
        if options['hotel_slug']:
            queryset = queryset.filter(hotel__slug=options['hotel_slug'])
            
        count = queryset.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ No orphaned guests found - all clean!')
            )
            return
            
        # Show what will be cleaned
        self.stdout.write(
            self.style.WARNING(f'🔍 Found {count} orphaned guests in rooms with booking=NULL')
        )
        
        if options['verbose'] or options['dry_run']:
            self._show_orphaned_guests_details(queryset)
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'🧪 DRY RUN: Would clean up {count} orphaned guests (no changes made)')
            )
            return
            
        # Confirm destructive action
        if count > 10:
            confirm = input(f'⚠️  This will detach {count} guests from their rooms. Continue? (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write('❌ Cleanup cancelled by user')
                return
        
        # Execute cleanup
        with transaction.atomic():
            updated = queryset.update(room=None)
            
        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully cleaned up {updated} orphaned guests')
        )
        
        # Log cleanup for audit trail
        self._log_cleanup_summary(updated, options['hotel_slug'])

    def _show_orphaned_guests_details(self, queryset):
        """Show detailed information about orphaned guests."""
        
        self.stdout.write('\n📋 Orphaned Guest Details:')
        self.stdout.write('-' * 80)
        
        for guest in queryset[:20]:  # Limit to first 20 for readability
            room_info = f"Room {guest.room.room_number}" if guest.room else "No Room"
            hotel_info = f"Hotel: {guest.hotel.slug}" if guest.hotel else "No Hotel"
            
            self.stdout.write(
                f'  👻 Guest #{guest.id}: {guest.first_name} {guest.last_name} '
                f'| {room_info} | {hotel_info} | Type: {guest.guest_type}'
            )
        
        if queryset.count() > 20:
            remaining = queryset.count() - 20
            self.stdout.write(f'  ... and {remaining} more orphaned guests')
        
        self.stdout.write('-' * 80)
        
    def _log_cleanup_summary(self, cleaned_count, hotel_slug):
        """Log cleanup summary for audit purposes."""
        import logging
        
        logger = logging.getLogger('hotel.management')
        
        hotel_filter = f" for hotel {hotel_slug}" if hotel_slug else " across all hotels"
        logger.info(
            f"CLEANUP: Detached {cleaned_count} orphaned guests from rooms{hotel_filter} "
            f"- fixed Room 337 ghost bug state"
        )

    def _get_affected_rooms_summary(self, queryset):
        """Get summary of affected rooms."""
        
        rooms_with_ghosts = queryset.values_list(
            'room__room_number', 
            'hotel__slug'
        ).distinct()
        
        return list(rooms_with_ghosts)