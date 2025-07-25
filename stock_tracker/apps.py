from django.apps import AppConfig


class StockTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stock_tracker'
    
    def ready(self):
        import stock_tracker.signals
