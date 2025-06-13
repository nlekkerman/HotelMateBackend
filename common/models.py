from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models
from hotel.models import Hotel

class ThemePreference(models.Model):
    hotel = models.OneToOneField(
        Hotel,
        on_delete=models.CASCADE,
        related_name="theme"
    )
    main_color = models.CharField(max_length=7, default="#3498db")
    secondary_color = models.CharField(max_length=7, default="#2ecc71")

    def __str__(self):
        return f"Theme for {self.hotel.slug}"
    