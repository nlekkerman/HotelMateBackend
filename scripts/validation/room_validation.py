# Custom validation to prevent AVAILABLE status from being reintroduced
# This file should be imported in Django settings INSTALLED_APPS

from django.apps import AppConfig
from django.core.checks import Error, register

@register()
def check_no_available_status(app_configs, **kwargs):
    """
    Custom Django system check to prevent AVAILABLE status from being reintroduced
    """
    errors = []
    
    try:
        from rooms.models import Room
        
        # Check if AVAILABLE is in model choices
        status_choices = dict(Room.ROOM_STATUS_CHOICES)
        if 'AVAILABLE' in status_choices:
            errors.append(
                Error(
                    "AVAILABLE status found in Room.ROOM_STATUS_CHOICES",
                    hint="Remove AVAILABLE from Room model choices. Use READY_FOR_GUEST instead.",
                    obj=Room,
                    id='rooms.E001',
                )
            )
        
        # Check if default is AVAILABLE
        field = Room._meta.get_field('room_status')
        if field.default == 'AVAILABLE':
            errors.append(
                Error(
                    "Room.room_status field has default='AVAILABLE'",
                    hint="Change default to 'READY_FOR_GUEST'",
                    obj=Room,
                    id='rooms.E002',
                )
            )
            
        # Check database for any remaining AVAILABLE records
        if hasattr(Room, 'objects'):  # Only in Django runtime, not migrations
            available_count = Room.objects.filter(room_status='AVAILABLE').count()
            if available_count > 0:
                errors.append(
                    Error(
                        f"{available_count} rooms still have room_status='AVAILABLE' in database",
                        hint="Run data migration to convert AVAILABLE → READY_FOR_GUEST",
                        obj=Room,
                        id='rooms.E003',
                    )
                )
                
    except Exception as e:
        # Don't fail checks if models aren't loaded yet
        pass
        
    return errors

class RoomValidationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'room_validation'
    verbose_name = 'Room Status Validation'
    
    def ready(self):
        """Run validation when Django starts"""
        pass