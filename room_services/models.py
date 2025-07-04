from django.db import models
import cloudinary.uploader
from django.db.models import Sum, F, FloatField


# =========================
# Room Service Item
# =========================
class RoomServiceItem(models.Model):
    CATEGORY_CHOICES = [
        ('Starters', 'Starters'),
        ('Mains', 'Mains'),
        ('Desserts', 'Desserts'),
        ('Drinks', 'Drinks'),
        ('Others', 'Others'),
    ]
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='room_service_items/', null=True, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Others')
    is_on_stock = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.image and not str(self.image).startswith('http'):
            upload_result = cloudinary.uploader.upload(self.image)
            self.image = upload_result.get('secure_url', self.image.url)
        super().save(*args, **kwargs)


# =========================
# Room Service Order
# =========================
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
    ]
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, null=True, blank=True)
    room_number = models.IntegerField()
    items = models.ManyToManyField(RoomServiceItem, through='OrderItem')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        """
        Sum of (quantity * item.price) for all OrderItems
        """
        agg = self.orderitem_set.aggregate(
            total=Sum(F('quantity') * F('item__price'), output_field=FloatField())
        )
        return agg['total'] or 0.0
    
    
    def __str__(self):
        return f"Order {self.id} for Room {self.room_number} - Status: {self.status}"


class OrderItem(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(RoomServiceItem, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.item.name} for Order {self.order.id}"


# =========================
# In-Room Breakfast
# =========================
class BreakfastItem(models.Model):
    CATEGORY_CHOICES = [
        ('Mains', 'Mains'),
        ('Hot Buffet', 'Hot Buffet'),
        ('Cold Buffet', 'Cold Buffet'),
        ('Breads', 'Breads'),
        ('Condiments', 'Condiments'),
        ('Drinks', 'Drinks'),
    ]
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='breakfast_items/', null=True, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Mains')
    quantity = models.PositiveIntegerField(default=1)
    is_on_stock = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.image and not str(self.image).startswith('http'):
            upload_result = cloudinary.uploader.upload(self.image)
            self.image = upload_result.get('secure_url', self.image.url)
        super().save(*args, **kwargs)


class BreakfastOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
    ]
    TIME_SLOT_CHOICES = [
        ('7:00-8:00', '7:00 - 8:00'),
        ('8:00-8:30', '8:00 - 8:30'),
        ('8:30-9:00', '8:30 - 9:00'),
        ('9:00-9:30', '9:00 - 9:30'),
        ('9:30-10:00', '9:30 - 10:00'),
        ('10:00-10:30', '10:00 - 10:30'),
    ]
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, null=True, blank=True)
    room_number = models.IntegerField()
    items = models.ManyToManyField(BreakfastItem, through='BreakfastOrderItem')
    delivery_time = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Breakfast Order {self.id} for Room {self.room_number} - {self.status}"


class BreakfastOrderItem(models.Model):
    order = models.ForeignKey(BreakfastOrder, on_delete=models.CASCADE)
    item = models.ForeignKey(BreakfastItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.item.name} in Breakfast Order {self.order.id}"
