from django.db import models
from hotel.models import Hotel


class BookingSubcategory(models.Model):
    name = models.CharField(max_length=100)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='subcategories')
    slug = models.SlugField(unique=True, blank=True, null=True)
    
    def __str__(self):
        return self.name


class BookingCategory(models.Model):
    name = models.CharField(max_length=100)
    subcategory = models.ForeignKey(BookingSubcategory, on_delete=models.CASCADE, related_name='categories')
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return f"{self.name} → {self.subcategory.name}"


class Booking(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='bookings')
    category = models.ForeignKey(BookingCategory, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField()
    time = models.TimeField()
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
        'Restaurant',
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
        blank=True
    )
    guest = models.ForeignKey(  # 👈 NEW FIELD
        'guests.Guest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )
    voucher_code = models.CharField(  # 👈 NEW FIELD
        max_length=100,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.category.name} / {self.category.subcategory.name} @ {self.date}"


class Seats(models.Model):
    booking = models.OneToOneField('Booking', on_delete=models.CASCADE, related_name='seats')
    total = models.PositiveIntegerField(default=1, help_text="Total number of seats to reserve for this booking")
    adults = models.PositiveIntegerField(default=0)
    children = models.PositiveIntegerField(default=0)
    infants = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Seats for {self.booking} – Total: {self.total} | A:{self.adults} C:{self.children} I:{self.infants}"

class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Slug used in URLs (e.g., strawberry-tree)")
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='restaurants')
    capacity = models.PositiveIntegerField(default=30, help_text="Max number of guests")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    opening_time = models.TimeField()
    closing_time = models.TimeField()

    def __str__(self):
        return f"{self.name} at {self.hotel.name}"

    def is_open_now(self):
        from django.utils import timezone
        now = timezone.localtime().time()
        return self.opening_time <= now <= self.closing_time