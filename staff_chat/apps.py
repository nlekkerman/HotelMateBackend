from django.apps import AppConfig


class StaffChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'staff_chat'
    verbose_name = 'Staff Chat'
    
    def ready(self):
        """Import signals when app is ready"""
        import staff_chat.models  # This loads the signal handlers
