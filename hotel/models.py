from django.db import models
from cloudinary.models import CloudinaryField


# ============================================================================
# PRESET SYSTEM
# ============================================================================

class Preset(models.Model):
    """
    Reusable preset for styling sections, cards, images, news blocks, footers, and page themes.
    Enables mix-and-match combinations across different element types.
    """
    TARGET_TYPES = [
        ("section", "Section"),
        ("card", "Card"),
        ("image", "Image"),
        ("news_block", "News Block"),
        ("footer", "Footer"),
        ("page_theme", "Page Theme"),
        ("room_card", "Room Card"),
        ("section_header", "Section Header"),
    ]

    SECTION_TYPES = [
        ("hero", "Hero"),
        ("gallery", "Gallery"),
        ("list", "List"),
        ("news", "News"),
        ("footer", "Footer"),
        ("rooms", "Rooms"),
    ]

    # What this preset applies to
    target_type = models.CharField(max_length=20, choices=TARGET_TYPES)

    # For section presets only
    section_type = models.CharField(
        max_length=20,
        choices=SECTION_TYPES,
        null=True,
        blank=True,
        help_text="Required when target_type='section'."
    )

    # Stable key used by frontend to pick layout
    key = models.CharField(max_length=50, unique=True)

    # Human readable info
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Mark one preset as default for each type
    is_default = models.BooleanField(default=False)

    # Optional JSON for future config (styles, spacing, animations, etc.)
    config = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['target_type', 'section_type', 'name']

    def __str__(self):
        if self.section_type:
            return f"{self.name} ({self.target_type}/{self.section_type})"
        return f"{self.name} ({self.target_type})"


# ============================================================================
# HOTEL MODEL
# ============================================================================

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


class HotelPublicPage(models.Model):
    """
    Represents the public page configuration for a hotel.
    Includes a global style preset that can be applied to all sections.
    """
    hotel = models.OneToOneField(
        Hotel,
        on_delete=models.CASCADE,
        related_name="public_page"
    )
    
    # Global page preset: 1–5
    global_style_variant = models.PositiveSmallIntegerField(
        choices=[(i, f"Page Preset {i}") for i in range(1, 6)],
        null=True,
        blank=True,
        help_text="Optional global style preset index (1–5) applied to all sections."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Hotel Public Page"
        verbose_name_plural = "Hotel Public Pages"
    
    def __str__(self):
        return f"Public Page for {self.hotel.name}"


class PublicSection(models.Model):
    """
    A container for ordering and visibility.
    Each section contains exactly one element.
    """
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name="public_sections"
    )
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=100, blank=True)
    
    # Style preset index for this section: 1..5
    style_variant = models.PositiveSmallIntegerField(
        choices=[(i, f"Preset {i}") for i in range(1, 6)],
        default=1,
        help_text="Section style preset index (1–5)."
    )
    
    # Preset for section layout
    layout_preset = models.ForeignKey(
        Preset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"target_type": "section"},
        help_text="Layout preset for this section"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.hotel} - section {self.position} ({self.name})"


class PublicElement(models.Model):
    """
    Defines WHAT the section is.
    """
    section = models.OneToOneField(
        PublicSection,
        on_delete=models.CASCADE,
        related_name="element"
    )
    element_type = models.CharField(max_length=64)
    title = models.CharField(max_length=255, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.section.hotel} - {self.element_type}"


class PublicElementItem(models.Model):
    """
    Used for cards, gallery images, review entries, features, etc.
    """
    element = models.ForeignKey(
        PublicElement,
        on_delete=models.CASCADE,
        related_name="items"
    )
    title = models.CharField(max_length=255, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    badge = models.CharField(max_length=50, blank=True)
    cta_label = models.CharField(max_length=100, blank=True)
    cta_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.element.element_type} item: {self.title or ''}"


# ============================================================================
# SECTION-SPECIFIC MODELS
# ============================================================================

class HeroSection(models.Model):
    """
    Hero section with pre-populated placeholders.
    One per section, automatically created with defaults.
    """
    section = models.OneToOneField(
        PublicSection,
        on_delete=models.CASCADE,
        related_name='hero_data'
    )
    hero_title = models.CharField(
        max_length=255,
        default="Update your hero title here"
    )
    hero_text = models.TextField(
        default="Update your hero description text here."
    )
    hero_image = CloudinaryField(
        "hero_image",
        blank=True,
        null=True,
        help_text="Main hero background image"
    )
    hero_logo = CloudinaryField(
        "hero_logo",
        blank=True,
        null=True,
        help_text="Corner logo image"
    )
    
    # Style preset index for this hero section: 1..5
    style_variant = models.PositiveSmallIntegerField(
        choices=[(i, f"Preset {i}") for i in range(1, 6)],
        default=1,
        help_text="Hero style preset index (1–5)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Hero: {self.hero_title}"


class GalleryContainer(models.Model):
    """
    Container for a gallery (multiple galleries can exist per Gallery section).
    """
    section = models.ForeignKey(
        PublicSection,
        on_delete=models.CASCADE,
        related_name='galleries'
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional gallery name/title"
    )
    
    # Style preset index for this gallery: 1..5
    style_variant = models.PositiveSmallIntegerField(
        choices=[(i, f"Preset {i}") for i in range(1, 6)],
        default=1,
        help_text="Gallery style preset index (1–5)."
    )
    
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"Gallery: {self.name or f'#{self.id}'}"


class GalleryImage(models.Model):
    """
    Individual images within a gallery container.
    """
    gallery = models.ForeignKey(
        GalleryContainer,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = CloudinaryField(
        "gallery_image",
        help_text="Gallery image stored in Cloudinary"
    )
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    
    # Preset for image styling
    image_style_preset = models.ForeignKey(
        Preset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"target_type": "image"},
        help_text="Style preset for this image"
    )
    
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"Image in {self.gallery.name or 'Gallery'}"


class ListContainer(models.Model):
    """
    Container for a list of cards (multiple lists can exist per List section).
    """
    section = models.ForeignKey(
        PublicSection,
        on_delete=models.CASCADE,
        related_name='lists'
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional list title (e.g., 'Special Offers', 'Rooms & Suites')"
    )
    
    # Style preset index for this list: 1..5
    style_variant = models.PositiveSmallIntegerField(
        choices=[(i, f"Preset {i}") for i in range(1, 6)],
        default=1,
        help_text="List style preset index (1–5)."
    )
    
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"List: {self.title or f'#{self.id}'}"


class Card(models.Model):
    """
    Individual card within a list container.
    """
    list_container = models.ForeignKey(
        ListContainer,
        on_delete=models.CASCADE,
        related_name='cards'
    )
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image = CloudinaryField(
        "card_image",
        blank=True,
        null=True,
        help_text="Optional card image"
    )
    
    # Preset for card styling
    style_preset = models.ForeignKey(
        Preset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"target_type": "card"},
        help_text="Style preset for this card"
    )
    
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"Card: {self.title}"


class NewsItem(models.Model):
    """
    News item with title, date, summary, and ordered content blocks.
    """
    section = models.ForeignKey(
        PublicSection,
        on_delete=models.CASCADE,
        related_name='news_items'
    )
    title = models.CharField(max_length=255)
    date = models.DateField(
        blank=True,
        null=True,
        help_text="Publication date"
    )
    summary = models.CharField(
        max_length=500,
        blank=True,
        help_text="Short summary/excerpt"
    )
    
    # Style preset index for this news item: 1..5
    style_variant = models.PositiveSmallIntegerField(
        choices=[(i, f"Preset {i}") for i in range(1, 6)],
        default=1,
        help_text="News item style preset index (1–5)."
    )
    
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"News: {self.title}"


class ContentBlock(models.Model):
    """
    Individual content block within a news item.
    Can be text or image with positioning.
    """
    BLOCK_TYPE_CHOICES = [
        ('text', 'Text Block'),
        ('image', 'Image Block'),
    ]
    
    IMAGE_POSITION_CHOICES = [
        ('full_width', 'Full Width'),
        ('left', 'Left (text right)'),
        ('right', 'Right (text left)'),
        ('inline_grid', 'Inline Grid'),
    ]
    
    news_item = models.ForeignKey(
        NewsItem,
        on_delete=models.CASCADE,
        related_name='content_blocks'
    )
    block_type = models.CharField(
        max_length=20,
        choices=BLOCK_TYPE_CHOICES,
        default='text'
    )
    
    # For text blocks
    body = models.TextField(
        blank=True,
        help_text="Text content (supports rich text/markdown)"
    )
    
    # For image blocks
    image = CloudinaryField(
        "news_image",
        blank=True,
        null=True,
        help_text="Image for image blocks"
    )
    image_position = models.CharField(
        max_length=20,
        choices=IMAGE_POSITION_CHOICES,
        default='full_width',
        blank=True
    )
    image_caption = models.CharField(max_length=255, blank=True)
    
    # Preset for block styling
    block_preset = models.ForeignKey(
        Preset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"target_type": "news_block"},
        help_text="Style preset for this content block"
    )
    
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.block_type} block #{self.sort_order} in {self.news_item.title}"


class RoomsSection(models.Model):
    """
    Rooms section that dynamically displays RoomType data.
    RoomTypes are queried live from the PMS system - no data duplication.
    """
    section = models.OneToOneField(
        PublicSection,
        on_delete=models.CASCADE,
        related_name='rooms_data'
    )
    subtitle = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional subtitle for the rooms section"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description text"
    )
    
    # Style preset index for this rooms section: 1..5
    style_variant = models.PositiveSmallIntegerField(
        choices=[(i, f"Preset {i}") for i in range(1, 6)],
        default=1,
        help_text="Rooms section style preset index (1–5)."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rooms Section"
        verbose_name_plural = "Rooms Sections"

    def __str__(self):
        return f"Rooms Section: {self.section.name or f'#{self.id}'}"

