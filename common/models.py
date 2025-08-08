from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models
from hotel.models import Hotel

class ThemePreference(models.Model):
    hotel = models.OneToOneField(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name="theme"
    )

    # Basic colors
    main_color = models.CharField(max_length=7, default="#3498db", help_text="Primary branding color")
    secondary_color = models.CharField(max_length=7, default="#2ecc71", help_text="Secondary accent color")

    # Extended palette
    background_color = models.CharField(max_length=7, default="#ffffff", help_text="Main background")
    text_color = models.CharField(max_length=7, default="#333333", help_text="Default text color")
    border_color = models.CharField(max_length=7, default="#dddddd", help_text="Default border color")

    # Buttons
    button_color = models.CharField(max_length=7, default="#2980b9", help_text="Button background")
    button_text_color = models.CharField(max_length=7, default="#ffffff", help_text="Button text color")
    button_hover_color = models.CharField(max_length=7, default="#1f6391", help_text="Hover color for buttons")

    # Links
    link_color = models.CharField(max_length=7, default="#2980b9", help_text="Default link color")
    link_hover_color = models.CharField(max_length=7, default="#1f6391", help_text="Hover color for links")

    def __str__(self):
        return f"Theme for {self.hotel.slug}"
  