from django.db import models
from hotel.models import Hotel


class BookingSubcategory(models.Model):
    name = models.CharField(max_length=100)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='subcategories')

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
    created_at = models.DateTimeField(auto_now_add=True)

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
    
    