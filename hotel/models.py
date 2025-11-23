from django.db import models
from cloudinary.models import CloudinaryField


class Hotel(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(
        unique=True,
        help_text="Used in URLs, e.g., hotel-name"
    )
    subdomain = models.SlugField(
        unique=True,
        null=True,
        blank=True,
        help_text="Used as the subdomain, e.g., 'hilton' → hilton.example.com"
    )
    # Logo stored on Cloudinary
    logo = CloudinaryField(
        "logo",
        blank=True,
        null=True,
        help_text="Upload a logo for this hotel (PNG recommended)."
    )

    # New fields for landing / ordering / visibility
    is_active = models.BooleanField(
        default=True,
        help_text="If false, the hotel is hidden from public/guest listings."
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Controls ordering on HotelsMate landing page."
    )
    city = models.CharField(
        max_length=120,
        blank=True,
        default=''
    )
    country = models.CharField(
        max_length=120,
        blank=True,
        default=''
    )
    short_description = models.TextField(
        blank=True,
        help_text="Short marketing blurb for the hotel."
    )

    # Public page marketing fields (Issue #9)
    tagline = models.CharField(
        max_length=200,
        blank=True,
        help_text="Catchy tagline for hotel marketing (e.g., 'Luxury in the heart of the city')"
    )
    hero_image = CloudinaryField(
        "hero_image",
        blank=True,
        null=True,
        help_text="Hero/banner image for public hotel page"
    )
    long_description = models.TextField(
        blank=True,
        help_text="Detailed description for the hotel public page"
    )

    # Location fields (Issue #9)
    address_line_1 = models.CharField(
        max_length=255,
        blank=True,
        help_text="Street address line 1"
    )
    address_line_2 = models.CharField(
        max_length=255,
        blank=True,
        help_text="Street address line 2 (optional)"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="Postal/ZIP code"
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude coordinate for map display"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude coordinate for map display"
    )

    # Contact fields (Issue #9)
    phone = models.CharField(
        max_length=30,
        blank=True,
        help_text="Main contact phone number"
    )
    email = models.EmailField(
        blank=True,
        help_text="Main contact email address"
    )
    website_url = models.URLField(
        blank=True,
        help_text="Hotel's official website URL"
    )
    booking_url = models.URLField(
        blank=True,
        help_text="Primary booking URL (external or internal)"
    )

    def __str__(self):
        return self.name

    # ----- Helper paths / URLs -----

    @property
    def guest_base_path(self) -> str:
        """
        Base path for guest-facing frontend.
        Example: /guest/hotels/hotel-slug/
        """
        return f"/guest/hotels/{self.slug}/"

    @property
    def staff_base_path(self) -> str:
        """
        Base path for staff-facing frontend.
        Example: /staff/hotels/hotel-slug/
        """
        return f"/staff/hotels/{self.slug}/"

    @property
    def full_guest_url(self) -> str:
        """
        If subdomain is configured:
            https://<subdomain>.hotelsmates.com/guest/hotels/<slug>/
        Otherwise just returns guest_base_path.
        """
        if self.subdomain:
            return f"https://{self.subdomain}.hotelsmates.com{self.guest_base_path}"
        return self.guest_base_path

    @property
    def full_staff_url(self) -> str:
        """
        If subdomain is configured:
            https://<subdomain>.hotelsmates.com/staff/hotels/<slug>/
        Otherwise just returns staff_base_path.
        """
        if self.subdomain:
            return f"https://{self.subdomain}.hotelsmates.com{self.staff_base_path}"
        return self.staff_base_path


class HotelAccessConfig(models.Model):
    """
    Per-hotel configuration for guest & staff portal behaviour.

    This is where we control:
    - Whether guest/staff portals are enabled
    - PIN rules for room access
    - How many devices/people can be active per room
    """
    hotel = models.OneToOneField(
        Hotel,
        on_delete=models.CASCADE,
        related_name="access_config"
    )

    # Portal toggles
    guest_portal_enabled = models.BooleanField(
        default=True,
        help_text="If false, guest portal features are disabled for this hotel."
    )
    staff_portal_enabled = models.BooleanField(
        default=True,
        help_text="If false, staff portal login/features are disabled for this hotel."
    )

    # Room PIN behaviour
    requires_room_pin = models.BooleanField(
        default=True,
        help_text="If disabled, the magic link alone grants guest access."
    )
    room_pin_length = models.PositiveSmallIntegerField(
        default=4,
        help_text="Number of digits in room PIN (e.g. 4 or 6)."
    )
    rotate_pin_on_checkout = models.BooleanField(
        default=True,
        help_text="Regenerate a fresh PIN when the room is checked out."
    )

    # Multi-user / multi-device access per room
    allow_multiple_guest_sessions = models.BooleanField(
        default=True,
        help_text="Allow multiple devices/people in the same room to share access."
    )
    max_active_guest_devices_per_room = models.PositiveSmallIntegerField(
        default=5,
        help_text="Hard limit of concurrent guest sessions per room."
    )

    def __str__(self):
        return f"Access config for {self.hotel.name}"


class BookingOptions(models.Model):
    """
    Booking call-to-action configuration for hotel public pages.
    """
    hotel = models.OneToOneField(
        Hotel,
        on_delete=models.CASCADE,
        related_name="booking_options"
    )
    primary_cta_label = models.CharField(
        max_length=100,
        default="Book a Room",
        help_text="Label for primary booking button"
    )
    primary_cta_url = models.URLField(
        blank=True,
        help_text="URL for primary booking action"
    )
    secondary_cta_label = models.CharField(
        max_length=100,
        blank=True,
        help_text="Label for secondary action (e.g., 'Call to Book')"
    )
    secondary_cta_phone = models.CharField(
        max_length=30,
        blank=True,
        help_text="Phone number for secondary CTA"
    )
    terms_url = models.URLField(
        blank=True,
        help_text="URL to terms and conditions"
    )
    policies_url = models.URLField(
        blank=True,
        help_text="URL to booking policies"
    )

    class Meta:
        verbose_name = "Booking Options"
        verbose_name_plural = "Booking Options"

    def __str__(self):
        return f"Booking options for {self.hotel.name}"


class Offer(models.Model):
    """
    Marketing offers, packages, and deals for hotel public pages.
    """
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="offers"
    )
    title = models.CharField(
        max_length=200,
        help_text="e.g., 'Weekend Getaway Package'"
    )
    short_description = models.TextField(
        help_text="Brief description of the offer"
    )
    details_text = models.TextField(
        blank=True,
        help_text="Plain text details"
    )
    details_html = models.TextField(
        blank=True,
        help_text="Rich HTML for detailed description"
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        help_text="Offer valid from this date"
    )
    valid_to = models.DateField(
        null=True,
        blank=True,
        help_text="Offer valid until this date"
    )
    tag = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., 'Family Deal', 'Weekend Offer'"
    )
    book_now_url = models.URLField(
        blank=True,
        help_text="Direct link to book this offer"
    )
    photo = CloudinaryField(
        "offer_photo",
        blank=True,
        null=True,
        help_text="Promotional image for the offer"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this offer is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', '-created_at']
        verbose_name = "Offer"
        verbose_name_plural = "Offers"

    def __str__(self):
        return f"{self.hotel.name} - {self.title}"

    def is_valid(self):
        """Check if offer is currently valid based on dates."""
        from django.utils import timezone
        today = timezone.now().date()
        
        if self.valid_from and today < self.valid_from:
            return False
        if self.valid_to and today > self.valid_to:
            return False
        return True


class LeisureActivity(models.Model):
    """
    Hotel facilities, amenities, and activities for public pages.
    """
    CATEGORY_CHOICES = [
        ('Wellness', 'Wellness'),
        ('Family', 'Family'),
        ('Dining', 'Dining'),
        ('Sports', 'Sports'),
        ('Entertainment', 'Entertainment'),
        ('Business', 'Business'),
        ('Other', 'Other'),
    ]

    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="leisure_activities"
    )
    name = models.CharField(
        max_length=200,
        help_text="e.g., 'Indoor Pool', 'Spa & Wellness'"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        help_text="Activity category"
    )
    short_description = models.TextField(
        help_text="Brief description of the activity/facility"
    )
    details_html = models.TextField(
        blank=True,
        help_text="Detailed HTML description"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon name or CSS class"
    )
    image = CloudinaryField(
        "activity_image",
        blank=True,
        null=True,
        help_text="Image for the activity/facility"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within category"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this activity is currently available"
    )

    class Meta:
        ordering = ['category', 'sort_order', 'name']
        verbose_name = "Leisure Activity"
        verbose_name_plural = "Leisure Activities"

    def __str__(self):
        return f"{self.hotel.name} - {self.name}"
