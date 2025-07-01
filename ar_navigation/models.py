from django.db import models
from cloudinary.models import CloudinaryField

class ARAnchor(models.Model):
    name = models.CharField(max_length=100)
    hotel = models.ForeignKey("hotel.Hotel", on_delete=models.CASCADE)
    floor = models.PositiveIntegerField()

    image = CloudinaryField(
        "marker image",
        blank=True,
        null=True,
        help_text="Upload the image guests will scan (Cloudinary-hosted)."
    )

    position_hint = models.CharField(max_length=100, help_text="e.g., next to elevator")

    marker_type = models.CharField(
        max_length=20,
        choices=[("pattern", "Pattern"), ("image", "Image")],
        default="image"
    )
    next_anchor = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    instruction = models.TextField(help_text="Instruction shown to user at this point.")
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} (Floor {self.floor})"

    @property
    def image_url(self):
        return self.image.url if self.image else ""
