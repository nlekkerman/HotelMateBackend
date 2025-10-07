from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from cloudinary.models import CloudinaryField

User = get_user_model()


class Game(models.Model):
    """
    Metadata for a game (global, not tied to any hotel)
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    thumbnail = CloudinaryField('image', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class GameHighScore(models.Model):
    """
    Persistent highscore per user/game, optionally tied to a hotel.
    Supports anonymous players via player_name.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    player_name = models.CharField(max_length=50, blank=True, null=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='highscores')
    hotel = models.ForeignKey(
        'hotel.Hotel', on_delete=models.SET_NULL, null=True, blank=True
    )
    score = models.IntegerField()
    achieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score']

    def __str__(self):
        name = self.player_name or (self.user.username if self.user else "Anonymous")
        hotel_str = self.hotel.slug if self.hotel else "No Hotel"
        return f"{name} - {self.game.title} @ {hotel_str}: {self.score}"


class GameQRCode(models.Model):
    """
    Optional QR codes for accessing specific games.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    hotel = models.ForeignKey(
        'hotel.Hotel', on_delete=models.SET_NULL, null=True, blank=True
    )
    qr_url = models.URLField(blank=True, null=True)
    generated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('game', 'hotel')

    def __str__(self):
        hotel_str = self.hotel.slug if self.hotel else "Global"
        return f"{hotel_str} / {self.game.slug}"

    def generate_qr(self):
        """
        Generate and upload QR code for this game (optionally for a hotel)
        """
        import qrcode
        from io import BytesIO
        import cloudinary.uploader

        hotel_slug = self.hotel.slug if self.hotel else "global"
        url = f"https://hotelsmates.com/games/{hotel_slug}/{self.game.slug}"

        # Build QR code
        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, "PNG")
        img_io.seek(0)

        # Upload to Cloudinary
        upload = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=f"games_qr/{hotel_slug}_{self.game.slug}"
        )
        self.qr_url = upload.get('secure_url')
        self.generated_at = timezone.now()
        self.save()
        return True
