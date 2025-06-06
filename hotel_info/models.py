from django.db import models

class HotelInfo(models.Model):
    CATEGORY_CHOICES = [
        ('info_board', 'Info Board'),
        ('kid_entertainment', 'Kid Entertainment'),
        ('dining', 'Dining'),
        ('offers', 'Offers'),
    ]

    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    extra_info = models.JSONField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Updated field names with "info"
    info_qr_board = models.URLField(blank=True, null=True)
    info_qr_kids = models.URLField(blank=True, null=True)
    info_qr_dining = models.URLField(blank=True, null=True)
    info_qr_offers = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"

    def generate_info_qr(self):
        import qrcode
        from io import BytesIO
        import cloudinary.uploader

        if not self.hotel:
            return None

        hotel_slug = self.hotel.slug or str(self.hotel.id)
        category_slug = self.category

        url = f"https://dashing-klepon-d9f0c6.netlify.app/hotel_info/{hotel_slug}/category/{category_slug}/"

        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, "PNG")
        img_io.seek(0)

        upload_result = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=f"hotel_info_qr/{hotel_slug}_{category_slug}"
        )

        qr_url = upload_result.get("secure_url")

        field_map = {
            'info_board': 'info_qr_board',
            'kid_entertainment': 'info_qr_kids',
            'dining': 'info_qr_dining',
            'offers': 'info_qr_offers',
        }

        setattr(self, field_map[self.category], qr_url)
        self.save()
        return qr_url
