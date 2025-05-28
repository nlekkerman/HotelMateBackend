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
    extra_info = models.JSONField(blank=True, null=True)  # For flexible extra details like schedule, menu URL, etc.
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"
