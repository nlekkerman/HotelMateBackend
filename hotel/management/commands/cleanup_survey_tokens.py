"""
Token cleanup management command for survey system maintenance.

Deletes expired, used, and old survey tokens while preserving responses forever.
Designed to be run regularly via Heroku Scheduler or cron.

Usage:
    python manage.py cleanup_survey_tokens
    python manage.py cleanup_survey_tokens --dry-run
    python manage.py cleanup_survey_tokens --days-old 60
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction, models
from hotel.models import BookingSurveyToken, BookingSurveyResponse
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up expired, used, and old survey tokens (keeps responses forever)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--days-old',
            type=int,
            default=30,
            help='Delete tokens older than N days (default: 30)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Process tokens in batches of N (default: 1000)'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_old = options['days_old']
        batch_size = options['batch_size']
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Find tokens to delete: expired, used, or old
        tokens_to_delete = BookingSurveyToken.objects.filter(
            models.Q(expires_at__lt=timezone.now()) |  # Expired
            models.Q(used_at__isnull=False) |           # Used  
            models.Q(created_at__lt=cutoff_date)        # Old
        ).select_related('booking')
        
        total_count = tokens_to_delete.count()
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN: Would delete {total_count} survey tokens')
            )
            
            # Show breakdown
            expired_count = BookingSurveyToken.objects.filter(expires_at__lt=timezone.now()).count()
            used_count = BookingSurveyToken.objects.filter(used_at__isnull=False).count()
            old_count = BookingSurveyToken.objects.filter(created_at__lt=cutoff_date).count()
            
            self.stdout.write(f'  - Expired: {expired_count}')
            self.stdout.write(f'  - Used: {used_count}')
            self.stdout.write(f'  - Old (>{days_old} days): {old_count}')
            
            # Show sample tokens
            sample_tokens = tokens_to_delete[:5]
            self.stdout.write('\\nSample tokens to delete:')
            for token in sample_tokens:
                self.stdout.write(f'  - {token.booking.booking_id} (created: {token.created_at})')
            
            return
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No tokens to clean up'))
            return
        
        deleted_count = 0
        
        # Process in batches to avoid memory issues
        while True:
            batch = list(tokens_to_delete[:batch_size])
            if not batch:
                break
                
            batch_ids = [token.id for token in batch]
            
            with transaction.atomic():
                batch_deleted = BookingSurveyToken.objects.filter(id__in=batch_ids).delete()[0]
                deleted_count += batch_deleted
                
            self.stdout.write(f'Deleted batch: {batch_deleted} tokens (total: {deleted_count})')
        
        # Verify responses are intact
        response_count = BookingSurveyResponse.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Token cleanup complete: {deleted_count} tokens deleted, '
                f'{response_count} responses preserved'
            )
        )
        
        logger.info(f'Survey token cleanup: deleted {deleted_count} tokens, preserved {response_count} responses')