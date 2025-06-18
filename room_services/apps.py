from django.apps import AppConfig


class RoomServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'room_services'
    
    def ready(self):
        # Import signals to ensure they are registered
        import room_services.signals
