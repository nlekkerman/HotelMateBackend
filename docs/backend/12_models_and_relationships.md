# 12. Models and Relationships

## Core Entity Models

### 1. Hotel Entity (Multi-Tenant Root)

**Model:** `hotel.Hotel`
**Purpose:** Root entity for multi-tenant architecture

**Key Fields:**
```python
class Hotel(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)  # URL identifier
    subdomain = models.SlugField(unique=True, null=True, blank=True)  # Custom subdomain
    logo = CloudinaryField("logo", blank=True, null=True)
    hero_image = CloudinaryField("hero_image", blank=True, null=True)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    tags = models.JSONField(default=list, blank=True)  # Filtering tags
    hotel_type = models.CharField(max_length=50, choices=HOTEL_TYPE_CHOICES)
    timezone = models.CharField(max_length=50, default='Europe/Dublin')
    default_cancellation_policy = models.ForeignKey('CancellationPolicy', ...)
```

**Relationships:**
- **1:1** → `HotelAccessConfig` (operational settings)
- **1:1** → `HotelPrecheckinConfig` (form configuration)
- **1:1** → `HotelSurveyConfig` (survey automation)
- **1:1** → `BookingOptions` (CTA configuration)
- **1:Many** → All hotel-scoped entities (rooms, bookings, staff, etc.)

**Evidence:** `hotel/models.py` lines 83-310

### 2. Room Management Models

#### Room Types (Bookable Inventory)
**Model:** `rooms.RoomType`
```python
class RoomType(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)  # Unique identifier
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    max_occupancy = models.IntegerField()
    photo = CloudinaryField('room_photo', blank=True, null=True)
```

#### Physical Rooms (Property Units)
**Model:** `rooms.Room`
```python
class Room(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    room_number = models.IntegerField()
    room_type = models.ForeignKey('RoomType', on_delete=models.PROTECT, 
                                  related_name='physical_rooms')
    is_occupied = models.BooleanField(default=False)
    guest_fcm_token = models.CharField(max_length=255, blank=True, null=True)
    
    # Status workflow fields
    room_status = models.CharField(max_length=20, choices=ROOM_STATUS_CHOICES,
                                  default='READY_FOR_GUEST')
    last_cleaned_at = models.DateTimeField(null=True, blank=True)
    cleaned_by_staff = models.ForeignKey('staff.Staff', ...)
    maintenance_required = models.BooleanField(default=False)
    turnover_notes = models.TextField(blank=True)
```

**Unique Constraint:** `(hotel, room_number)` - Room numbers unique per hotel
**Evidence:** `rooms/models.py` lines 1-150

### 3. Booking Management Models

#### Room Bookings (Guest Reservations)
**Model:** `hotel.RoomBooking`
**Purpose:** Guest room reservations with comprehensive workflow

**Key Fields:**
```python
class RoomBooking(models.Model):
    # Identifiers
    booking_id = models.CharField(max_length=50, unique=True)  # BK-2025-0001
    confirmation_number = models.CharField(max_length=50, unique=True)  # HTL-2025-0001
    
    # Hotel context
    hotel = models.ForeignKey('Hotel', on_delete=models.PROTECT)
    room_type = models.ForeignKey('rooms.RoomType', on_delete=models.PROTECT)
    
    # Dates and occupancy
    check_in = models.DateField()
    check_out = models.DateField()
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    
    # Booker vs Primary Guest separation
    booker_type = models.CharField(max_length=20, choices=BookerType.choices())
    booker_first_name = models.CharField(max_length=100, blank=True)
    booker_last_name = models.CharField(max_length=100, blank=True)
    booker_email = models.EmailField(blank=True)
    primary_first_name = models.CharField(max_length=100)
    primary_last_name = models.CharField(max_length=100)
    primary_email = models.EmailField(blank=True)
    
    # Financial
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Workflow status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                            default='PENDING_PAYMENT')
    
    # Payment authorization fields
    payment_intent_id = models.CharField(max_length=200, blank=True, null=True)
    payment_authorized_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Approval workflow
    approval_deadline_at = models.DateTimeField(null=True, blank=True)
    decision_by = models.ForeignKey('staff.Staff', null=True, blank=True)
    decision_at = models.DateTimeField(null=True, blank=True)
    
    # Expiry management
    expires_at = models.DateTimeField(null=True, blank=True)  # Unpaid booking cleanup
    expired_at = models.DateTimeField(null=True, blank=True)  # Auto-expiry timestamp
    auto_expire_reason_code = models.CharField(max_length=50, blank=True)
```

**Calculated Properties:**
- `nights` - Duration calculation
- `primary_guest_name` - Full name concatenation
- `party_complete` - Validation against expected occupancy

**Evidence:** `hotel/models.py` lines 624-1150

#### Restaurant Bookings (Separate Domain)
**Model:** `bookings.Booking`
**Purpose:** Restaurant table reservations (distinct from room bookings)

```python
class Booking(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    category = models.ForeignKey('BookingCategory', on_delete=models.CASCADE)
    restaurant = models.ForeignKey('Restaurant', on_delete=models.CASCADE)
    guest = models.ForeignKey('guests.Guest', on_delete=models.SET_NULL)
    room = models.ForeignKey('rooms.Room', on_delete=models.SET_NULL)
    
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    voucher_code = models.CharField(max_length=100, blank=True)
    seen = models.BooleanField(default=False)
```

**Related Models:**
- `BookingSubcategory` - Booking classification
- `BookingCategory` - Hierarchical categorization
- `Restaurant` - Dining venue with capacity management
- `Seats` - Occupancy tracking (adults, children, infants)

**Evidence:** `bookings/models.py` lines 1-150

### 4. Staff Management Models

#### Staff Profiles
**Model:** `staff.Staff`
```python
class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL)
    role = models.ForeignKey('Role', on_delete=models.SET_NULL)
    
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    can_login = models.BooleanField(default=True)
```

#### Organizational Structure
**Models:** `staff.Department`, `staff.Role`
```python
class Department(models.Model):
    name = models.CharField(max_length=100)
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)

class Role(models.Model):
    name = models.CharField(max_length=100)
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    permissions = models.JSONField(default=list)
```

**Evidence:** `staff/models.py` organizational models

### 5. Service Management Models

#### Room Services
**Models:** `room_services.RoomServiceItem`, `room_services.Order`
```python
class RoomServiceItem(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=50)
    is_available = models.BooleanField(default=True)

class Order(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE)
    guest = models.ForeignKey('guests.Guest', on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Evidence:** `room_services/models.py` service order system

### 6. Inventory Management Models

#### Stock Tracking
**Complex Models:** `stock_tracker` app with recipe-based inventory

**Key Entities:**
```python
class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    unit = models.CharField(max_length=20)  # ml, grams, pieces
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=4)

class CocktailRecipe(models.Model):
    name = models.CharField(max_length=100)
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=8, decimal_places=2)

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey('CocktailRecipe', on_delete=models.CASCADE)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=4)  # Amount per cocktail

class CocktailConsumption(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    cocktail = models.ForeignKey('CocktailRecipe', on_delete=models.CASCADE)
    quantity_sold = models.PositiveIntegerField()
    consumed_at = models.DateTimeField()
```

**Complex Logic:** Automatic ingredient deduction based on recipe quantities
**Evidence:** `stock_tracker/models.py` extensive recipe system

### 7. Communication Models

#### Staff Chat System
**Models:** `staff_chat.StaffConversation`, `staff_chat.StaffChatMessage`
```python
class StaffConversation(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    participants = models.ManyToManyField('staff.Staff')
    title = models.CharField(max_length=200, blank=True)
    is_group_chat = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class StaffChatMessage(models.Model):
    conversation = models.ForeignKey('StaffConversation', on_delete=models.CASCADE)
    sender = models.ForeignKey('staff.Staff', on_delete=models.CASCADE)
    content = models.TextField()
    message_type = models.CharField(max_length=20, default='text')
    sent_at = models.DateTimeField(auto_now_add=True)
```

**Evidence:** `staff_chat/models.py` comprehensive messaging system

## Key Relationships and Constraints

### 1. Multi-Tenant Foreign Keys
**Pattern:** All major models have `hotel = models.ForeignKey('hotel.Hotel', ...)`
**Constraint:** Cross-hotel references are validated in model `clean()` methods

**Example Validation:**
```python
def clean(self):
    if self.category_id and self.category.hotel_id != self.hotel_id:
        raise ValidationError("Category belongs to a different hotel.")
```
**Evidence:** `bookings/models.py` lines 79-95

### 2. Unique Constraints
```python
# Hotel slug uniqueness
Hotel.slug = models.SlugField(unique=True)

# Room number per hotel
class Room:
    class Meta:
        unique_together = ('hotel', 'room_number')

# Restaurant slug per hotel  
class Restaurant:
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["hotel", "slug"], 
                                  name="uniq_restaurant_hotel_slug")
        ]
```

### 3. Booking ID Generation
**Auto-generated IDs:** Sequential generation with collision handling
```python
def _generate_unique_booking_id(self):
    year = datetime.now().year
    count = RoomBooking.objects.filter(
        booking_id__startswith=f'BK-{year}-'
    ).count()
    sequence = count + 1
    # Loop until available ID found
    while RoomBooking.objects.filter(booking_id=candidate_id).exists():
        sequence += 1
    return f'BK-{year}-{sequence:04d}'
```
**Evidence:** `hotel/models.py` booking ID generation logic

### 4. State Machine Constraints
**Room Status Transitions:** Validated state machine
```python
def can_transition_to(self, new_status):
    valid_transitions = {
        'OCCUPIED': ['CHECKOUT_DIRTY'],
        'CHECKOUT_DIRTY': ['CLEANING_IN_PROGRESS', 'CLEANED_UNINSPECTED', ...],
        # ... full state machine definition
    }
    return new_status in valid_transitions.get(self.room_status, [])
```

### 5. Configuration Model Relationships

**Hotel Configuration Stack:**
```
Hotel (1:1) → HotelAccessConfig (operational settings)
Hotel (1:1) → HotelPrecheckinConfig (form fields)  
Hotel (1:1) → HotelSurveyConfig (survey automation)
Hotel (1:1) → BookingOptions (CTA configuration)
```

**Default Creation Pattern:**
```python
@classmethod
def get_or_create_default(cls, hotel):
    config, created = cls.objects.get_or_create(
        hotel=hotel,
        defaults=DEFAULT_CONFIG
    )
    return config
```

This model architecture provides comprehensive hotel management with strong multi-tenancy, workflow state machines, and integrated service management.