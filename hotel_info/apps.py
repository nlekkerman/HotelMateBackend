from django.apps import AppConfig


class HotelInfoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hotel_info'
    def ready(self):
        import hotel_info.signals
