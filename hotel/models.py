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
    landing_page_image = CloudinaryField(
        "landing_page_image",
        blank=True,
        null=True,
        help_text="Image displayed on landing page hotel card"
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
    
    # Gallery images for public hotel page
    gallery = models.JSONField(
        default=list,
        blank=True,
        help_text="List of image URLs for public hotel gallery"
    )
    
    # Tags for filtering (Issue #46 enhancement)
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="List of tags for filtering (e.g., ['Family', 'Spa', 'Business'])"
    )
    
    # Hotel type classification (Issue #47 enhancement)
    HOTEL_TYPE_CHOICES = [
        ('Resort', 'Resort'),
        ('SpaHotel', 'Spa Hotel'),
        ('WellnessHotel', 'Wellness Hotel'),
        ('FamilyHotel', 'Family Hotel'),
        ('BusinessHotel', 'Business Hotel'),
        ('LuxuryHotel', 'Luxury Hotel'),
        ('BoutiqueHotel', 'Boutique Hotel'),
        ('BudgetHotel', 'Budget Hotel'),
        ('Hostel', 'Hostel'),
        ('Aparthotel', 'Aparthotel'),
        ('EcoHotel', 'Eco Hotel'),
        ('ConferenceHotel', 'Conference Hotel'),
        ('BeachHotel', 'Beach Hotel'),
        ('MountainHotel', 'Mountain Hotel'),
        ('CasinoHotel', 'Casino Hotel'),
        ('GolfHotel', 'Golf Hotel'),
        ('AirportHotel', 'Airport Hotel'),
        ('AdventureHotel', 'Adventure Hotel'),
        ('CityHotel', 'City Hotel'),
        ('HistoricHotel', 'Historic Hotel'),
    ]
    
    hotel_type = models.CharField(
        max_length=50,
        choices=HOTEL_TYPE_CHOICES,
        blank=True,
        default='',
        help_text="Primary hotel type classification"
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided"""
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

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


class HotelPublicSettings(models.Model):
    """
    Public page settings for each hotel including content, branding,
    and contact info. OneToOne relationship ensures one settings
    row per hotel.
    """
    THEME_MODE_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('custom', 'Custom'),
    ]

    hotel = models.OneToOneField(
        Hotel,
        on_delete=models.CASCADE,
        related_name="public_settings",
        help_text="Hotel this settings configuration belongs to"
    )

    # Hotel model override fields - customize what appears on public page
    name_override = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Custom hotel name for public display"
    )
    tagline_override = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Custom tagline for public display"
    )
    city_override = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        help_text="Custom city for public display"
    )
    country_override = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        help_text="Custom country for public display"
    )
    
    # Location overrides
    address_line_1_override = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Custom address line 1"
    )
    address_line_2_override = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Custom address line 2"
    )
    postal_code_override = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Custom postal code"
    )
    latitude_override = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Custom latitude"
    )
    longitude_override = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Custom longitude"
    )
    
    # Contact overrides
    phone_override = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Custom phone number"
    )
    email_override = models.EmailField(
        blank=True,
        null=True,
        help_text="Custom email address"
    )
    website_url_override = models.URLField(
        blank=True,
        null=True,
        help_text="Custom website URL"
    )
    booking_url_override = models.URLField(
        blank=True,
        null=True,
        help_text="Custom booking URL"
    )

    # Content fields
    short_description = models.TextField(
        blank=True,
        default='',
        help_text="Brief description for the hotel"
    )
    long_description = models.TextField(
        blank=True,
        default='',
        help_text="Detailed description for the public page"
    )
    welcome_message = models.TextField(
        blank=True,
        default='',
        help_text="Welcome message for guests (optional)"
    )
    hero_image = CloudinaryField(
        "settings_hero_image",
        blank=True,
        null=True,
        help_text="Hero/banner image for public page (customizable)"
    )
    landing_page_image = CloudinaryField(
        "settings_landing_page_image",
        blank=True,
        null=True,
        help_text="Image for hotel card on landing page (customizable)"
    )
    gallery = models.JSONField(
        default=list,
        blank=True,
        help_text="List of image URLs for gallery"
    )
    amenities = models.JSONField(
        default=list,
        blank=True,
        help_text="List of amenity strings"
    )

    # Contact information
    contact_email = models.EmailField(
        blank=True,
        default='',
        help_text="Public contact email"
    )
    contact_phone = models.CharField(
        max_length=30,
        blank=True,
        default='',
        help_text="Public contact phone number"
    )
    contact_address = models.TextField(
        blank=True,
        default='',
        help_text="Full contact address"
    )
    website = models.URLField(
        blank=True,
        default='',
        help_text="Hotel website URL"
    )
    google_maps_link = models.URLField(
        blank=True,
        default='',
        help_text="Google Maps embed/link URL"
    )

    # Branding fields
    logo = models.URLField(
        blank=True,
        default='',
        help_text="Hotel logo URL"
    )
    favicon = models.URLField(
        blank=True,
        default='',
        help_text="Favicon URL (16x16 or 32x32px)"
    )
    slogan = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Hotel slogan/tagline"
    )
    primary_color = models.CharField(
        max_length=7,
        blank=True,
        default='#3B82F6',
        help_text="Primary brand color (HEX format)"
    )
    secondary_color = models.CharField(
        max_length=7,
        blank=True,
        default='#10B981',
        help_text="Secondary brand color (HEX format)"
    )
    accent_color = models.CharField(
        max_length=7,
        blank=True,
        default='#F59E0B',
        help_text="Accent color (HEX format)"
    )
    background_color = models.CharField(
        max_length=7,
        blank=True,
        default='#FFFFFF',
        help_text="Background color (HEX format)"
    )
    button_color = models.CharField(
        max_length=7,
        blank=True,
        default='#3B82F6',
        help_text="Button color (HEX format)"
    )
    button_text_color = models.CharField(
        max_length=7,
        blank=True,
        default='#FFFFFF',
        help_text="Button text color (HEX format)"
    )
    button_hover_color = models.CharField(
        max_length=7,
        blank=True,
        default='#0066CC',
        help_text="Button hover state color (HEX format)"
    )
    text_color = models.CharField(
        max_length=7,
        blank=True,
        default='#333333',
        help_text="Main text color (HEX format)"
    )
    border_color = models.CharField(
        max_length=7,
        blank=True,
        default='#E5E7EB',
        help_text="Border color (HEX format)"
    )
    link_color = models.CharField(
        max_length=7,
        blank=True,
        default='#007BFF',
        help_text="Link color (HEX format)"
    )
    link_hover_color = models.CharField(
        max_length=7,
        blank=True,
        default='#0056B3',
        help_text="Link hover color (HEX format)"
    )
    theme_mode = models.CharField(
        max_length=10,
        choices=THEME_MODE_CHOICES,
        default='light',
        help_text="Theme mode for the public page"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hotel Public Settings"
        verbose_name_plural = "Hotel Public Settings"

    def __str__(self):
        return f"Public settings for {self.hotel.name}"


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


class RoomBooking(models.Model):
    """
    Guest room reservations/bookings for hotels.
    """
    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
    ]

    # Unique identifiers
    booking_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Auto-generated booking ID (e.g., BK-2025-5678)"
    )
    confirmation_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Guest-facing confirmation number"
    )

    # Hotel and room
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.PROTECT,
        related_name='room_bookings'
    )
    room_type = models.ForeignKey(
        'rooms.RoomType',
        on_delete=models.PROTECT,
        related_name='bookings'
    )

    # Dates
    check_in = models.DateField(
        help_text="Check-in date"
    )
    check_out = models.DateField(
        help_text="Check-out date"
    )

    # Guest information
    guest_first_name = models.CharField(
        max_length=100,
        help_text="Guest first name"
    )
    guest_last_name = models.CharField(
        max_length=100,
        help_text="Guest last name"
    )
    guest_email = models.EmailField(
        help_text="Guest email for confirmation"
    )
    guest_phone = models.CharField(
        max_length=30,
        blank=True,
        help_text="Guest contact phone"
    )

    # Occupancy
    adults = models.PositiveIntegerField(
        default=1,
        help_text="Number of adults"
    )
    children = models.PositiveIntegerField(
        default=0,
        help_text="Number of children"
    )

    # Pricing
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total amount charged"
    )
    currency = models.CharField(
        max_length=3,
        default='EUR',
        help_text="Currency code (ISO 4217)"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING_PAYMENT'
    )

    # Optional fields
    special_requests = models.TextField(
        blank=True,
        help_text="Guest special requests"
    )
    promo_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Applied promotional code"
    )

    # Payment information
    payment_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Payment processor reference ID"
    )
    payment_provider = models.CharField(
        max_length=50,
        blank=True,
        help_text="Payment provider (stripe, paypal, etc.)"
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of successful payment"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Booking creation timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )

    # Admin notes
    internal_notes = models.TextField(
        blank=True,
        help_text="Internal staff notes (not visible to guest)"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Room Booking"
        verbose_name_plural = "Room Bookings"
        indexes = [
            models.Index(fields=['hotel', 'check_in', 'check_out']),
            models.Index(fields=['booking_id']),
            models.Index(fields=['guest_email']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if not self.booking_id:
            from datetime import datetime
            year = datetime.now().year
            count = RoomBooking.objects.filter(
                booking_id__startswith=f'BK-{year}-'
            ).count()
            self.booking_id = f'BK-{year}-{count + 1:04d}'

        if not self.confirmation_number:
            hotel_code = self.hotel.slug.upper()[:3]
            from datetime import datetime
            year = datetime.now().year
            count = RoomBooking.objects.filter(
                hotel=self.hotel,
                confirmation_number__startswith=f'{hotel_code}-{year}-'
            ).count()
            self.confirmation_number = f'{hotel_code}-{year}-{count + 1:04d}'

        super().save(*args, **kwargs)

    @property
    def nights(self):
        """Calculate number of nights"""
        return (self.check_out - self.check_in).days

    @property
    def guest_name(self):
        """Full guest name"""
        return f"{self.guest_first_name} {self.guest_last_name}"

    def __str__(self):
        return f"{self.booking_id} - {self.guest_name} @ {self.hotel.name}"


class PricingQuote(models.Model):
    """
    Temporary pricing quotes for booking flow.
    Expires after a set time to prevent stale pricing.
    """
    quote_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False
    )
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name='pricing_quotes'
    )
    room_type = models.ForeignKey(
        'rooms.RoomType',
        on_delete=models.CASCADE
    )
    check_in = models.DateField()
    check_out = models.DateField()
    adults = models.PositiveIntegerField()
    children = models.PositiveIntegerField(default=0)

    # Pricing breakdown
    base_price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    number_of_nights = models.PositiveIntegerField()
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    taxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    currency = models.CharField(
        max_length=3,
        default='EUR'
    )

    # Promo/offer info
    promo_code = models.CharField(
        max_length=50,
        blank=True
    )
    applied_offer = models.ForeignKey(
        'hotel.Offer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Validity
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(
        help_text="Quote expiration timestamp"
    )

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.quote_id:
            import uuid
            self.quote_id = f'QT-{uuid.uuid4().hex[:10].upper()}'
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if quote is still valid"""
        from django.utils import timezone
        return timezone.now() < self.valid_until

    def __str__(self):
        return f"{self.quote_id} - €{self.total}"


class Gallery(models.Model):
    """
    Gallery collections for organizing hotel images by category.
    Examples: 'Rooms', 'Facilities', 'Restaurant', 'Spa', etc.
    """
    CATEGORY_CHOICES = [
        ('rooms', 'Rooms'),
        ('facilities', 'Facilities'),
        ('dining', 'Dining & Restaurant'),
        ('spa', 'Spa & Wellness'),
        ('events', 'Events & Conferences'),
        ('exterior', 'Exterior & Grounds'),
        ('activities', 'Activities'),
        ('other', 'Other'),
    ]
    
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name='galleries'
    )
    name = models.CharField(
        max_length=100,
        help_text="Gallery name (e.g., 'Luxury Rooms', 'Pool Area')"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other',
        help_text="Category for organizing galleries"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description for this gallery"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Show this gallery on public page"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order in which galleries are displayed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Gallery"
        verbose_name_plural = "Galleries"
        ordering = ['display_order', 'name']
        unique_together = [['hotel', 'name']]

    def __str__(self):
        return f"{self.hotel.name} - {self.name}"


class GalleryImage(models.Model):
    """
    Individual images within a gallery with captions and ordering.
    """
    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = CloudinaryField(
        "gallery_image",
        help_text="Gallery image stored on Cloudinary"
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        help_text="Description/caption for this image"
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alternative text for accessibility"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order within the gallery"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Feature this image (e.g., as gallery thumbnail)"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"
        ordering = ['display_order', 'uploaded_at']

    def __str__(self):
        return f"{self.gallery.name} - Image {self.display_order}"
    
    @property
    def image_url(self):
        """Return the Cloudinary URL for the image"""
        if self.image:
            return self.image.url
        return None
