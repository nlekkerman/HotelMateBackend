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
