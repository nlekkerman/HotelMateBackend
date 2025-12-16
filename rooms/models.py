from django.db import models
from cloudinary.models import CloudinaryField
import cloudinary.uploader
import random
import string
import qrcode
from io import BytesIO


class Room(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    room_number = models.IntegerField()
    guest_id_pin = models.CharField(max_length=4, unique=True, null=True, blank=True)
    is_occupied = models.BooleanField(default=False)

    room_service_qr_code = models.URLField(blank=True, null=True)
    in_room_breakfast_qr_code = models.URLField(blank=True, null=True)
    dinner_booking_qr_code = models.URLField(blank=True, null=True)
    chat_pin_qr_code = models.URLField(blank=True, null=True)
    
    # FCM token for anonymous guest in this room
    guest_fcm_token = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Firebase Cloud Messaging token for push notifications to guest's device"
    )
    
    # PMS fields - link room to room type for inventory tracking
    room_type = models.ForeignKey(
        'rooms.RoomType',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='physical_rooms',
        help_text="Links physical room to a room type for PMS inventory tracking"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this room is available for booking (e.g., false during renovation)"
    )
    is_out_of_order = models.BooleanField(
        default=False,
        help_text="Temporarily out of service (maintenance, repair, etc.)"
    )
    
    # Room Turnover Workflow Status
    ROOM_STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('CHECKOUT_DIRTY', 'Checkout Dirty'),
        ('CLEANING_IN_PROGRESS', 'Cleaning in Progress'),
        ('CLEANED_UNINSPECTED', 'Cleaned Uninspected'), 
        ('MAINTENANCE_REQUIRED', 'Maintenance Required'),
        ('OUT_OF_ORDER', 'Out of Order'),
        ('READY_FOR_GUEST', 'Ready for Guest'),
    ]
    
    room_status = models.CharField(
        max_length=20,
        choices=ROOM_STATUS_CHOICES,
        default='AVAILABLE',
        help_text='Current turnover workflow status of the room'
    )
    
    # Cleaning tracking
    last_cleaned_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When room was last cleaned'
    )
    cleaned_by_staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cleaned_rooms',
        help_text='Staff member who cleaned the room'
    )
    
    # Inspection tracking  
    last_inspected_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When room was last inspected'
    )
    inspected_by_staff = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='inspected_rooms',
        help_text='Staff member who inspected the room'
    )
    
    # Notes and maintenance
    turnover_notes = models.TextField(
        blank=True,
        help_text='Internal turnover workflow notes and history'
    )
    maintenance_required = models.BooleanField(
        default=False,
        help_text='Room requires maintenance before next guest'
    )
    
    MAINTENANCE_PRIORITY_CHOICES = [
        ('LOW', 'Low Priority'),
        ('MED', 'Medium Priority'), 
        ('HIGH', 'High Priority'),
    ]
    maintenance_priority = models.CharField(
        max_length=4,
        choices=MAINTENANCE_PRIORITY_CHOICES,
        null=True, blank=True,
        help_text='Priority level for maintenance'
    )
    maintenance_notes = models.TextField(
        blank=True,
        help_text='Specific maintenance requirements and notes'
    )
    
    class Meta:
        unique_together = ('hotel', 'room_number')

    def __str__(self):
        hotel_name = self.hotel.name if self.hotel else "No Hotel"
        return f"Room {self.room_number} at {hotel_name}"
    
    def is_bookable(self):
        """Single source of truth for room availability"""
        # is_out_of_order is hard flag that overrides everything
        if self.is_out_of_order:
            return False
            
        return (
            self.room_status in {'AVAILABLE', 'READY_FOR_GUEST'} and
            self.is_active and
            not self.maintenance_required
        )
    
    def can_transition_to(self, new_status):
        """Validate state machine transitions"""
        valid_transitions = {
            'AVAILABLE': ['OCCUPIED', 'MAINTENANCE_REQUIRED', 'OUT_OF_ORDER'],
            'OCCUPIED': ['CHECKOUT_DIRTY'],
            'CHECKOUT_DIRTY': ['CLEANING_IN_PROGRESS', 'CLEANED_UNINSPECTED', 'MAINTENANCE_REQUIRED'],
            'CLEANING_IN_PROGRESS': ['CLEANED_UNINSPECTED', 'CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED'],
            'CLEANED_UNINSPECTED': ['READY_FOR_GUEST', 'CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED'],
            'MAINTENANCE_REQUIRED': ['CHECKOUT_DIRTY', 'OUT_OF_ORDER'],
            'OUT_OF_ORDER': ['CHECKOUT_DIRTY'],
            'READY_FOR_GUEST': ['OCCUPIED', 'MAINTENANCE_REQUIRED', 'OUT_OF_ORDER'],
        }
        return new_status in valid_transitions.get(self.room_status, [])
    
    def add_turnover_note(self, note, staff_member=None):
        """Add timestamped note to turnover history"""
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        staff_info = f" by {staff_member.get_full_name()}" if staff_member else ""
        new_note = f"[{timestamp}]{staff_info}: {note}"
        
        if self.turnover_notes:
            self.turnover_notes += f"\n{new_note}"
        else:
            self.turnover_notes = new_note

    def generate_guest_pin(self):
        characters = string.ascii_lowercase + string.digits
        pin = ''.join(random.choices(characters, k=4))
        while Room.objects.filter(guest_id_pin=pin).exists():
            pin = ''.join(random.choices(characters, k=4))
        self.guest_id_pin = pin
        self.save()

    def generate_qr_code(self, qr_type="room_service"):
        if not self.hotel:
            return  # Can't generate QR without hotel

        # Use hotel slug or ID in URL path instead of subdomain
        hotel_identifier = self.hotel.slug if self.hotel.slug else str(self.hotel.id)

        path_map = {
            "room_service": f"https://hotelsmates.com/room_services/{hotel_identifier}/room/{self.room_number}/menu/",
            "in_room_breakfast": f"https://hotelsmates.com/room_services/{hotel_identifier}/room/{self.room_number}/breakfast/",
        }

        qr_field_map = {
            "room_service": "room_service_qr_code",
            "in_room_breakfast": "in_room_breakfast_qr_code",
        }

        url = path_map.get(qr_type)
        if not url:
            return

        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        upload_result = cloudinary.uploader.upload(img_io, resource_type="image")
        qr_url = upload_result['secure_url']

        setattr(self, qr_field_map[qr_type], qr_url)
        self.save()

    def generate_booking_qr_for_restaurant(self, restaurant):
        """
        Generates and uploads a QR code for a booking at a specific restaurant
        for this room. Saves the Cloudinary URL to dinner_booking_qr_code and returns it.
        """

        if not self.hotel or not restaurant:
            return None

        hotel_slug = self.hotel.slug or str(self.hotel.id)
        restaurant_slug = restaurant.slug

        url = f"https://hotelsmates.com/guest-booking/{hotel_slug}/restaurant/{restaurant_slug}/room/{self.room_number}/"

        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        upload_result = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=f"booking_qr/{hotel_slug}_room{self.room_number}_{restaurant_slug.replace('-', '_')}"
        )

        qr_url = upload_result['secure_url']

        # ✅ Save to the Room model
        self.dinner_booking_qr_code = qr_url
        self.save()

        return qr_url
    
    def generate_chat_pin_qr_code(self):
        if not self.hotel:
            return None

        hotel_slug = self.hotel.slug or str(self.hotel.id)
        url = f"https://hotelsmates.com/chat/{hotel_slug}/messages/room/{self.room_number}/validate-chat-pin/"

        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        # ✅ same public_id every time = Cloudinary overwrites old QR
        upload_result = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=f"chat_pin_qr/{hotel_slug}_room{self.room_number}",
            overwrite=True
        )

        qr_url = upload_result['secure_url']
        self.chat_pin_qr_code = qr_url
        self.save()

        return qr_url


class RoomType(models.Model):
    """
    Marketing information about room categories (not live inventory).
    Used for public hotel pages to display available room types.
    """
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='room_types'
    )
    code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional identifier (e.g., 'STD', 'DLX')"
    )
    name = models.CharField(
        max_length=200,
        help_text="e.g., 'Deluxe Suite', 'Standard Room'"
    )
    short_description = models.TextField(
        blank=True,
        help_text="Brief marketing description"
    )
    max_occupancy = models.PositiveSmallIntegerField(
        default=2,
        help_text="Maximum number of guests"
    )
    bed_setup = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., 'King Bed', '2 Queen Beds'"
    )
    photo = CloudinaryField(
        "room_type_photo",
        blank=True,
        null=True,
        help_text="Room type photo"
    )
    starting_price_from = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Marketing 'from' price per night"
    )
    currency = models.CharField(
        max_length=3,
        default="EUR",
        help_text="Currency code (e.g., EUR, USD, GBP)"
    )
    booking_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Code for booking system integration"
    )
    booking_url = models.URLField(
        blank=True,
        help_text="Deep link to book this room type"
    )
    availability_message = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., 'High demand', 'Last rooms available'"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this room type is shown publicly"
    )

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = "Room Type"
        verbose_name_plural = "Room Types"

    def __str__(self):
        return f"{self.hotel.name} - {self.name}"


# ============================================================================
# PMS / RATE MANAGEMENT MODELS
# ============================================================================

class RatePlan(models.Model):
    """
    Rate plans for hotel rooms (e.g., Standard Rate, Non-Refundable, Early Bird).
    Each hotel can have multiple rate plans with different terms and pricing.
    """
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='rate_plans'
    )
    name = models.CharField(
        max_length=100,
        help_text="e.g., 'Standard Rate', 'Non-Refundable'"
    )
    code = models.CharField(
        max_length=30,
        help_text="Short code (e.g., 'STD', 'NRF', 'EB10')"
    )
    description = models.TextField(blank=True)
    is_refundable = models.BooleanField(
        default=True,
        help_text="Whether bookings under this rate plan can be refunded"
    )
    default_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Default discount percentage for this rate plan"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this rate plan is currently available"
    )

    class Meta:
        unique_together = ('hotel', 'code')
        ordering = ['hotel', 'name']
        verbose_name = "Rate Plan"
        verbose_name_plural = "Rate Plans"

    def __str__(self):
        return f"{self.hotel.name} - {self.code} ({self.name})"


class RoomTypeRatePlan(models.Model):
    """
    Links a room type to a rate plan, optionally overriding the base price.
    Allows different pricing for the same room type under different rate plans.
    """
    room_type = models.ForeignKey(
        'rooms.RoomType',
        on_delete=models.CASCADE,
        related_name='rate_plan_links'
    )
    rate_plan = models.ForeignKey(
        'rooms.RatePlan',
        on_delete=models.CASCADE,
        related_name='room_type_links'
    )
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Override base price for this room type + rate plan combo"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this rate plan is active for this room type"
    )

    class Meta:
        unique_together = ('room_type', 'rate_plan')
        verbose_name = "Room Type Rate Plan"
        verbose_name_plural = "Room Type Rate Plans"

    def __str__(self):
        return f"{self.room_type} - {self.rate_plan}"


class DailyRate(models.Model):
    """
    Daily pricing for a specific room type and rate plan combination.
    Allows per-day price adjustments (e.g., weekend premiums, seasonal rates).
    """
    room_type = models.ForeignKey(
        'rooms.RoomType',
        on_delete=models.CASCADE,
        related_name='daily_rates'
    )
    rate_plan = models.ForeignKey(
        'rooms.RatePlan',
        on_delete=models.CASCADE,
        related_name='daily_rates'
    )
    date = models.DateField(
        help_text="Specific date for this rate"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price per night for this date"
    )

    class Meta:
        unique_together = ('room_type', 'rate_plan', 'date')
        ordering = ['date']
        indexes = [
            models.Index(fields=['room_type', 'date']),
            models.Index(fields=['rate_plan', 'date']),
        ]
        verbose_name = "Daily Rate"
        verbose_name_plural = "Daily Rates"

    def __str__(self):
        return f"{self.date} - {self.room_type} [{self.rate_plan}]: {self.price}"


class Promotion(models.Model):
    """
    Promotional codes with advanced rules and restrictions.
    Supports percentage and/or fixed discounts with date ranges and constraints.
    """
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='promotions'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Promo code (case-insensitive)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Display name for the promotion"
    )
    description = models.TextField(
        blank=True,
        help_text="Internal description or terms"
    )

    # Discount configuration
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage discount (e.g., 20.00 for 20%)"
    )
    discount_fixed = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fixed amount discount"
    )

    # Date range
    valid_from = models.DateField(
        help_text="Promotion valid from this date"
    )
    valid_until = models.DateField(
        help_text="Promotion valid until this date"
    )

    # Restrictions
    room_types = models.ManyToManyField(
        'rooms.RoomType',
        blank=True,
        help_text="Limit to specific room types (empty = all room types)"
    )
    rate_plans = models.ManyToManyField(
        'rooms.RatePlan',
        blank=True,
        help_text="Limit to specific rate plans (empty = all rate plans)"
    )
    min_nights = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum nights required for promotion"
    )
    max_nights = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum nights allowed for promotion"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this promotion is currently available"
    )

    class Meta:
        ordering = ['-valid_until', 'code']
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['hotel', 'valid_from', 'valid_until']),
        ]
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"

    def __str__(self):
        return f"{self.code} - {self.name}"


class RoomTypeInventory(models.Model):
    """
    Daily inventory control for room types.
    Allows overriding physical room counts or stopping sales for specific dates.
    """
    room_type = models.ForeignKey(
        'rooms.RoomType',
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    date = models.DateField(
        help_text="Date for this inventory record"
    )
    total_rooms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="If set, overrides physical room count for this date. If null, use physical rooms."
    )
    stop_sell = models.BooleanField(
        default=False,
        help_text="If true, this room type cannot be booked for this date"
    )

    class Meta:
        unique_together = ('room_type', 'date')
        ordering = ['date']
        indexes = [
            models.Index(fields=['room_type', 'date']),
        ]
        verbose_name = "Room Type Inventory"
        verbose_name_plural = "Room Type Inventory"

    def __str__(self):
        return f"{self.date} - {self.room_type} (stop_sell={self.stop_sell}, total={self.total_rooms})"
