"""
Housekeeping App Configuration

Django app configuration for the housekeeping workflow management system.
"""

from django.apps import AppConfig


class HousekeepingConfig(AppConfig):
    """Configuration for the housekeeping app"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'housekeeping'
    verbose_name = 'Housekeeping Management'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        # Future: Import signal handlers for checkout/checkin hooks
        # from . import signals
        pass