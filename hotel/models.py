from django.db import models
from cloudinary.models import CloudinaryField

class Hotel(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, help_text="Used in URLs, e.g., hotel-name")
    subdomain = models.SlugField(
        unique=True,
        null=True,  # TEMPORARY
        blank=True,
        help_text="Used as the subdomain, e.g., 'hilton' → hilton.example.com"
    )
    # ↓ New logo field
    # ↓ replaced:
    logo = CloudinaryField(
        "logo",
        
        blank=True,
        null=True,
        help_text="Upload a logo for this hotel (PNG recommended)."
    )

    def __str__(self):
        return self.name
