from django.db import models
from django.utils import timezone
from cloudinary.models import CloudinaryField


class HotelInfoCategory(models.Model):
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Internal identifier (e.g. 'kid_entertainment')"
    )
    name = models.CharField(
        max_length=200,
        help_text="Human‐readable name (e.g. 'Kid Entertainment')"
    )

    class Meta:
        verbose_name = "Hotel Info Category"
        verbose_name_plural = "Hotel Info Categories"

    def __str__(self):
        return self.name


class CategoryQRCode(models.Model):
    hotel = models.ForeignKey(
        'hotel.Hotel', on_delete=models.CASCADE,
        related_name='category_qrcodes'
    )
    category = models.ForeignKey(
        'HotelInfoCategory', on_delete=models.CASCADE,
        related_name='qrcodes'
    )
    qr_url = models.URLField(blank=True, null=True)
    generated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('hotel', 'category')

    def __str__(self):
        return f"{self.hotel.slug} / {self.category.slug}"

    def generate_qr(self):
        """
        Generate and upload a QR code for this hotel+category combo.
        """
        import qrcode
        from io import BytesIO
        import cloudinary.uploader

        hotel_slug = self.hotel.slug or str(self.hotel.id)
        url = f"https://hotelsmates.com/hotel_info/{hotel_slug}/{self.category.slug}"

        # build QR
        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, "PNG")
        img_io.seek(0)

        # upload
        upload = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=f"hotel_info_qr/{hotel_slug}_{self.category.slug}"
        )
        self.qr_url = upload.get('secure_url')
        self.generated_at = timezone.now()
        self.save()
        return True


class HotelInfo(models.Model):
    hotel = models.ForeignKey(
        'hotel.Hotel', on_delete=models.CASCADE,
        null=True, blank=True
    )
    category = models.ForeignKey(
        HotelInfoCategory, on_delete=models.CASCADE,
        related_name="infos"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateField(null=True, blank=True)
    event_time = models.TimeField(null=True, blank=True)
    extra_info = models.JSONField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    image = CloudinaryField('image', blank=True, null=True)

    def __str__(self):
        return f"{self.category.name} – {self.title}"
