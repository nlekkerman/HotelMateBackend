# ar_navigation/models.py

from io import BytesIO

import cloudinary.uploader
import qrcode
from django.db import models

from bookings.models import Restaurant
from hotel.models import Hotel


class ARAnchor(models.Model):
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="ar_anchors"
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="ar_anchors",
        null=True,
        blank=True,
    )

    # NEW: on-screen hint shown above the QR scanner
    instruction = models.CharField(
        max_length=100,
        default="Hold device about 20 cm above the QR code to open the menu.",
        help_text="Instruction shown to guests when scanning this QR code."
    )

    qr_code_url = models.URLField(
        blank=True,
        null=True,
        help_text="Cloudinary URL of the generated QR code image."
    )

    class Meta:
        unique_together = ("hotel", "restaurant")
        verbose_name_plural = "AR Anchors"

    def __str__(self):
        return f"{self.hotel.slug} – {self.restaurant.slug} AR menu"

    @property
    def url(self) -> str:
        """
        The menu URL that the QR code points to.
        """
        h = self.hotel.slug or str(self.hotel.id)
        r = self.restaurant.slug or str(self.restaurant.id)
        return (
            f"https://hotelsmates.com/"
            f"{h}/restaurant/{r}/ar/menu/"
        )

    def generate_qr_code(self) -> None:
        """
        Create a QR code for `self.url`, upload it to Cloudinary,
        and store the resulting secure URL in `qr_code_url`.
        """
        buffer = BytesIO()
        img = qrcode.make(self.url)
        img.save(buffer, "PNG")
        buffer.seek(0)

        upload = cloudinary.uploader.upload(
            buffer,
            resource_type="image",
            public_id=f"ar_anchor/{self.hotel.slug}_{self.restaurant.slug}"
        )
        self.qr_code_url = upload["secure_url"]
        # Save only the field that changed
        self.save(update_fields=["qr_code_url"])
