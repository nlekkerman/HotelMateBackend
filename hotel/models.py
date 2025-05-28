from django.db import models

class Hotel(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, help_text="Used in URLs, e.g., hotel-name")
    subdomain = models.SlugField(
        unique=True,
        null=True,  # TEMPORARY
        blank=True,
        help_text="Used as the subdomain, e.g., 'hilton' → hilton.example.com"
    )

    def __str__(self):
        return self.name
