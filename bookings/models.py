from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField
from django.db.models import Q
class BookingSubcategory(models.Model):
    name = models.CharField(max_length=100)
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, related_name='subcategories')
    slug = models.SlugField(unique=True, blank=True, null=True)
    
    def __str__(self):
        return self.name


class BookingCategory(models.Model):
    name = models.CharField(max_length=100)
    subcategory = models.ForeignKey('bookings.BookingSubcategory', on_delete=models.CASCADE, related_name='categories')
    
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return f"{self.name} → {self.subcategory.name}"


class Booking(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, related_name='bookings')
    category = models.ForeignKey('bookings.BookingCategory', on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField()

    # Instead of a single "time" field
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    note = models.TextField(blank=True, null=True)
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    restaurant = models.ForeignKey(
        'bookings.Restaurant',
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
        blank=True
    )
    guest = models.ForeignKey(
        'guests.Guest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )
    voucher_code = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    def total_seats(self):
        return self.seats.total if hasattr(self, 'seats') else 0

    def clean(self):
        """Extra validation to ensure end_time is after start_time."""
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be later than start time.")

    def __str__(self):
        return f"{self.category.name} / {self.category.subcategory.name} @ {self.date} {self.start_time}–{self.end_time}"


class Seats(models.Model):
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='seats')
    total = models.PositiveIntegerField(default=1, help_text="Total number of seats to reserve for this booking")
    adults = models.PositiveIntegerField(default=0)
    children = models.PositiveIntegerField(default=0)
    infants = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Seats for {self.booking} – Total: {self.total} | A:{self.adults} C:{self.children} I:{self.infants}"

class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Slug used in URLs (e.g., strawberry-tree)")
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, related_name='restaurants')
    capacity = models.PositiveIntegerField(default=30, help_text="Max number of guests")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} at {self.hotel.name}"

    def is_open_now(self):
        from django.utils import timezone
        now = timezone.localtime().time()
        return self.opening_time <= now <= self.closing_time

class RestaurantBlueprint(models.Model):
    """
    Per-restaurant canvas (in pixels) for rendering an SVG floor plan.
    """
    restaurant = models.OneToOneField(
        'bookings.Restaurant',
        on_delete=models.CASCADE,
        related_name='blueprint'
    )
    width = models.PositiveIntegerField(default=1000, help_text="Canvas width in px")
    height = models.PositiveIntegerField(default=600, help_text="Canvas height in px")
    grid_size = models.PositiveIntegerField(default=25, help_text="Snap-to grid size")
    background_image = CloudinaryField(
        'image', null=True, blank=True, help_text="Optional background image of the floorplan"
    )

    def __str__(self):
        return f"Blueprint for {self.restaurant.name} ({self.width}×{self.height})"


class BlueprintArea(models.Model):
    """
    Optional zones like 'Main Hall', 'Window Row', 'Terrace'.
    """
    blueprint = models.ForeignKey(
        'bookings.RestaurantBlueprint', on_delete=models.CASCADE, related_name='areas'
    )
    name = models.CharField(max_length=100)
    x = models.PositiveIntegerField(default=0)
    y = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=200)
    height = models.PositiveIntegerField(default=200)
    z_index = models.IntegerField(default=0)

    class Meta:
        unique_together = (('blueprint', 'name'),)

    def __str__(self):
        return f"{self.name} @ {self.blueprint.restaurant.name}"


class TableShape(models.TextChoices):
    RECT = 'RECT', _('Rectangle')
    CIRCLE = 'CIRCLE', _('Circle')
    OVAL = 'OVAL', _('Oval')


class DiningTable(models.Model):
    """
    Physical table on the blueprint. Coordinates are px relative to blueprint top-left.
    A table can be 'joinable' with other tables that share the same 'join_group'.
    """
    restaurant = models.ForeignKey(
        'bookings.Restaurant', on_delete=models.CASCADE, related_name='tables'
    )
    area = models.ForeignKey(
        'bookings.BlueprintArea', on_delete=models.SET_NULL, null=True, blank=True, related_name='tables'
    )

    code = models.CharField(
        max_length=20,
        help_text="Human label like T12 / A3",
    )
    capacity = models.PositiveIntegerField(default=2)
    shape = models.CharField(max_length=10, choices=TableShape.choices, default=TableShape.RECT)

    # Geometry — choose width/height for RECT/OVAL, radius for CIRCLE
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    width = models.PositiveIntegerField(null=True, blank=True, help_text="For RECT/OVAL")
    height = models.PositiveIntegerField(null=True, blank=True, help_text="For RECT/OVAL")
    radius = models.PositiveIntegerField(null=True, blank=True, help_text="For CIRCLE")
    rotation = models.IntegerField(default=0, help_text="Degrees, clockwise")

    joinable = models.BooleanField(default=True, help_text="Can be combined with neighbors")
    join_group = models.CharField(
        max_length=50, blank=True, help_text="Tables with the same value are combinable"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (('restaurant', 'code'),)
        indexes = [
            models.Index(fields=['restaurant', 'area', 'join_group']),
        ]
        
    def is_available(self, date=None, time=None):
        """Check if the table is free at a given date/time."""
        qs = BookingTable.objects.filter(table=self)
        if date:
            qs = qs.filter(booking__date=date)
        if time:
            qs = qs.filter(booking__time=time)
        return not qs.exists()

    def bookings_for_date(self, date):
        return Booking.objects.filter(booking_tables__table=self, date=date)
    
    def __str__(self):
        return f"{self.code} ({self.capacity}) @ {self.restaurant.name}"


class TableSeatSpot(models.Model):
    """
    Optional: precise seat positions around a table (useful for fancy UIs).
    Skip if you don't need per-chair placement.
    """
    table = models.ForeignKey('bookings.DiningTable', on_delete=models.CASCADE, related_name='seat_spots')
    index = models.PositiveSmallIntegerField(help_text="Seat index starting at 1")
    # Relative offsets from table center (px). For circles these are super handy.
    offset_x = models.IntegerField(default=0)
    offset_y = models.IntegerField(default=0)
    angle_degrees = models.IntegerField(default=0)

    class Meta:
        unique_together = (('table', 'index'),)
        ordering = ['index']

    def __str__(self):
        return f"Seat {self.index} on {self.table.code}"

class BookingTable(models.Model):
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='booking_tables'
    )
    table = models.ForeignKey(
        'bookings.DiningTable',
        on_delete=models.CASCADE,
        related_name='booking_tables'
    )

    class Meta:
        unique_together = (('booking', 'table'),)
    
    def clean(self):
        # Validate seat capacity
        if self.booking.total_seats() > self.table.capacity:
            raise ValidationError(f"{self.table.code} only has {self.table.capacity} seats.")

        # Validate table availability
        overlapping = BookingTable.objects.filter(
            table=self.table,
            booking__date=self.booking.date
        ).exclude(pk=self.pk).filter(
            Q(booking__start_time__lt=self.booking.end_time) &
            Q(booking__end_time__gt=self.booking.start_time)
        )

        if overlapping.exists():
            raise ValidationError(f"{self.table.code} is already booked at this time.")
    def __str__(self):
        return f"{self.booking} → {self.table.code}"


class BlueprintObjectType(models.Model):
    """
    Dynamic object types for blueprints, e.g., Entrance, Window, Till, Decor.
    """
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=100, blank=True, help_text="Optional icon name or URL for frontend")
    default_width = models.PositiveIntegerField(default=50)
    default_height = models.PositiveIntegerField(default=50)

    def __str__(self):
        return self.name


class BlueprintObject(models.Model):
    blueprint = models.ForeignKey(
        'bookings.RestaurantBlueprint', on_delete=models.CASCADE, related_name='blueprint_objects'
    )
    type = models.ForeignKey(
        'bookings.BlueprintObjectType', on_delete=models.PROTECT, related_name='objects_type', null=True, blank=True
    )
    name = models.CharField(max_length=50, blank=True)  # Optional specific name
    
    x = models.PositiveIntegerField(default=0)
    y = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=50)
    height = models.PositiveIntegerField(default=50)
    rotation = models.IntegerField(default=0)
    z_index = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name or self.type.name} @ {self.blueprint.restaurant.name}"
