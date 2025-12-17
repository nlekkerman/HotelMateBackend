# Comprehensive Room Booking System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Models Architecture](#models-architecture)
3. [Serializers](#serializers)
4. [Views and Business Logic](#views-and-business-logic)
5. [URL Routing](#url-routing)
6. [Room Assignment System](#room-assignment-system)
7. [Booking Flow Diagrams](#booking-flow-diagrams)
8. [API Contracts](#api-contracts)

## System Overview

The HotelMate room booking system is a comprehensive solution for managing hotel reservations with three main zones:
- **Public/Guest Zone**: Guest-facing booking endpoints
- **Staff Zone**: Hotel staff management interfaces
- **Admin Zone**: System administration

### Key Features
- Multi-hotel support with hotel-scoped operations
- Dual booker/guest model (corporate bookings support)
- Safe room assignment with conflict detection
- Real-time updates via Pusher channels
- Payment integration (Stripe)
- Booking party management
- Comprehensive audit trails

## Models Architecture

### Core Models

#### 1. RoomBooking Model
**Location**: `hotel/models.py` (lines 405-650)

The central booking entity that stores all reservation information.

```python
class RoomBooking(models.Model):
    # Unique Identifiers
    booking_id = models.CharField(max_length=50, unique=True, editable=False)
    confirmation_number = models.CharField(max_length=50, unique=True, editable=False)
    
    # Hotel and Room
    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT, related_name='room_bookings')
    room_type = models.ForeignKey('rooms.RoomType', on_delete=models.PROTECT, related_name='bookings')
    
    # Dates
    check_in = models.DateField()
    check_out = models.DateField()
    
    # Booker vs Primary Staying Guest (Phase 2)
    booker_type = models.CharField(max_length=20, choices=BookerType.choices(), default=BookerType.SELF)
    
    # Booker Information (may not stay)
    booker_first_name = models.CharField(max_length=100, blank=True)
    booker_last_name = models.CharField(max_length=100, blank=True)
    booker_email = models.EmailField(blank=True)
    booker_phone = models.CharField(max_length=30, blank=True)
    booker_company = models.CharField(max_length=150, blank=True)
    
    # Primary Staying Guest (REQUIRED)
    primary_first_name = models.CharField(max_length=100)
    primary_last_name = models.CharField(max_length=100)
    primary_email = models.EmailField(blank=True)
    primary_phone = models.CharField(max_length=30, blank=True)
    
    # Occupancy
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    
    # Pricing
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Status
    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_PAYMENT')
    
    # Room Assignment Fields (Safe Assignment System)
    assigned_room = models.ForeignKey('rooms.Room', null=True, blank=True, on_delete=models.SET_NULL)
    room_assigned_at = models.DateTimeField(null=True, blank=True)
    room_assigned_by = models.ForeignKey('staff.Staff', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Check-in/out timestamps
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    
    # Audit and tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assignment_version = models.PositiveIntegerField(default=0)
```

**Key Methods**:
- `save()`: Auto-generates booking_id and confirmation_number
- `_sync_primary_booking_guest()`: Maintains consistency with BookingGuest model
- `primary_guest_name`: Property returning full name
- `nights`: Property calculating stay duration

#### 2. BookingGuest Model
**Location**: `hotel/models.py`

Manages booking party members (companions, additional guests).

```python
class BookingGuest(models.Model):
    booking = models.ForeignKey(RoomBooking, on_delete=models.CASCADE, related_name='party')
    role = models.CharField(max_length=20, choices=GuestRole.choices(), default=GuestRole.COMPANION)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_staying = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 3. PricingQuote Model
**Location**: `hotel/models.py`

Temporary pricing calculations for booking flow.

```python
class PricingQuote(models.Model):
    quote_id = models.CharField(max_length=50, unique=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    room_type = models.ForeignKey('rooms.RoomType', on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    adults = models.PositiveIntegerField()
    children = models.PositiveIntegerField(default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    taxes = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
```

## Serializers

### Public/Guest Serializers
**Location**: `hotel/booking_serializers.py`

#### 1. RoomTypeSerializer
Used for displaying available room types to guests.

```python
class RoomTypeSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = RoomType
        fields = [
            'id', 'code', 'name', 'short_description', 'max_occupancy',
            'bed_setup', 'photo_url', 'starting_price_from', 'currency',
            'booking_code', 'booking_url', 'availability_message'
        ]
```

#### 2. PricingQuoteSerializer
Returns pricing calculations for booking requests.

```python
class PricingQuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingQuote
        fields = [
            'quote_id', 'room_type', 'check_in', 'check_out',
            'adults', 'children', 'subtotal', 'taxes', 'total',
            'currency', 'expires_at', 'created_at'
        ]
```

#### 3. RoomBookingListSerializer
Compact booking information for list views.

```python
class RoomBookingListSerializer(serializers.ModelSerializer):
    guest_name = serializers.SerializerMethodField()
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    nights = serializers.SerializerMethodField()
    assigned_room_number = serializers.SerializerMethodField()

    class Meta:
        model = RoomBooking
        fields = [
            'id', 'booking_id', 'confirmation_number', 'hotel_name',
            'room_type_name', 'guest_name', 'primary_email', 'assigned_room_number',
            'check_in', 'check_out', 'nights', 'adults', 'children',
            'total_amount', 'currency', 'status', 'created_at'
        ]
```

#### 4. RoomBookingDetailSerializer
Complete booking information for detail views.

```python
class RoomBookingDetailSerializer(serializers.ModelSerializer):
    guest_name = serializers.SerializerMethodField()
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    nights = serializers.SerializerMethodField()
    cancellation_details = serializers.SerializerMethodField()
    room_photo_url = serializers.SerializerMethodField()
    booking_summary = serializers.SerializerMethodField()
    party = serializers.SerializerMethodField()

    class Meta:
        model = RoomBooking
        fields = [
            'id', 'booking_id', 'confirmation_number', 'hotel_name',
            'room_type_name', 'guest_name', 'primary_first_name', 'primary_last_name',
            'primary_email', 'primary_phone', 'booker_type', 'assigned_room',
            'check_in', 'check_out', 'nights', 'adults', 'children',
            'total_amount', 'currency', 'status', 'special_requests',
            'created_at', 'party', 'booking_summary', 'room_photo_url'
        ]
```

### Staff Serializers
**Location**: `hotel/canonical_serializers.py`

#### 1. StaffRoomBookingListSerializer
Staff-optimized booking list with additional management fields.

#### 2. StaffRoomBookingDetailSerializer
Complete staff view with internal notes and audit information.

#### 3. BookingPartyGuestSerializer
Individual booking party member management.

#### 4. BookingPartyGroupedSerializer
Grouped booking party display (primary guest, companions, etc.).

## Views and Business Logic

### Public/Guest Views
**Location**: `hotel/booking_views.py`

#### 1. HotelAvailabilityView
**Endpoint**: `GET /api/public/hotel/{hotel_slug}/availability/`

Checks room availability for given dates and occupancy.

```python
class HotelAvailabilityView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, hotel_slug):
        # Validates dates
        # Calculates availability by room type
        # Returns available room types with pricing
```

**Parameters**:
- `check_in`: ISO date string
- `check_out`: ISO date string
- `adults`: Number of adults (default: 2)
- `children`: Number of children (default: 0)

#### 2. HotelPricingQuoteView
**Endpoint**: `POST /api/public/hotel/{hotel_slug}/pricing-quote/`

Generates temporary pricing quote for booking flow.

```python
class HotelPricingQuoteView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, hotel_slug):
        # Validates room type and dates
        # Calculates pricing (subtotal, taxes, total)
        # Creates temporary PricingQuote record
        # Returns quote_id for booking creation
```

#### 3. HotelBookingCreateView
**Endpoint**: `POST /api/public/hotel/{hotel_slug}/room-bookings/`

Creates new room booking from guest request.

```python
class HotelBookingCreateView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, hotel_slug):
        # Validates quote_id (if provided)
        # Creates RoomBooking record
        # Handles booker vs primary guest logic
        # Returns booking confirmation
```

**Request Body**:
```json
{
    "room_type_code": "DBL",
    "check_in": "2025-01-15",
    "check_out": "2025-01-17",
    "adults": 2,
    "children": 0,
    "primary_first_name": "John",
    "primary_last_name": "Doe",
    "primary_email": "john@example.com",
    "primary_phone": "+1234567890",
    "quote_id": "QUOTE-2025-001",
    "special_requests": "Late check-in requested"
}
```

### Staff Views
**Location**: `hotel/staff_views.py`

#### 1. StaffBookingsListView
**Endpoint**: `GET /api/staff/hotel/{hotel_slug}/room-bookings/`**

Lists all bookings for hotel with filtering and pagination.

```python
class StaffBookingsListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get(self, request, hotel_slug):
        # Hotel-scoped booking list
        # Supports filtering by status, date range, guest name
        # Paginated results
        # Real-time updates via Pusher
```

**Query Parameters**:
- `status`: Filter by booking status
- `date_from`: Start date filter
- `date_to`: End date filter
- `guest_name`: Guest name search
- `page`: Page number for pagination

#### 2. StaffBookingDetailView
**Endpoint**: `GET /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/`

Detailed booking information for staff management.

#### 3. StaffBookingConfirmView
**Endpoint**: `POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/confirm/`

Confirms pending bookings (status change to CONFIRMED).

#### 4. StaffBookingCancelView
**Endpoint**: `POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/cancel/`

Cancels bookings with reason tracking.

#### 5. BookingAssignmentView
**Endpoint**: `POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/assign-room/`

Assigns physical room to booking using safe assignment system.

```python
class BookingAssignmentView(APIView):
    def post(self, request, hotel_slug, booking_id):
        # Validates room availability
        # Uses RoomAssignmentService for atomic assignment
        # Handles conflict detection
        # Updates booking status and audit trail
```

#### 6. BookingPartyManagementView
**Endpoint**: `GET/POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/party/`

Manages booking party members (companions, additional guests).

## URL Routing

### Guest Zone URLs
**Location**: `guest_urls.py`

```python
urlpatterns = [
    path('guest/<str:hotel_slug>/', guest_home, name='guest-home'),
    path('guest/<str:hotel_slug>/rooms/', guest_rooms, name='guest-rooms'),
    path('guest/<str:hotel_slug>/availability/', check_availability, name='check-availability'),
    path('guest/<str:hotel_slug>/pricing-quote/', get_pricing_quote, name='pricing-quote'),
    path('guest/<str:hotel_slug>/book/', create_booking, name='create-booking'),
]
```

### Public API URLs
**Location**: `hotel/urls.py`

```python
urlpatterns = [
    # Availability and pricing
    path('public/hotel/<str:hotel_slug>/availability/', HotelAvailabilityView.as_view()),
    path('public/hotel/<str:hotel_slug>/pricing-quote/', HotelPricingQuoteView.as_view()),
    
    # Booking creation and lookup
    path('public/hotel/<str:hotel_slug>/room-bookings/', HotelBookingCreateView.as_view()),
    path('public/hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/', PublicRoomBookingDetailView.as_view()),
]
```

### Staff Zone URLs
**Location**: `room_bookings/staff_urls.py`

```python
urlpatterns = [
    # Booking management
    path('', StaffBookingsListView.as_view(), name='room-bookings-staff-list'),
    path('<str:booking_id>/', StaffBookingDetailView.as_view(), name='room-bookings-staff-detail'),
    path('<str:booking_id>/confirm/', StaffBookingConfirmView.as_view(), name='room-bookings-staff-confirm'),
    path('<str:booking_id>/cancel/', StaffBookingCancelView.as_view(), name='room-bookings-staff-cancel'),
    
    # Room assignment
    path('<str:booking_id>/assign-room/', BookingAssignmentView.as_view(), name='room-bookings-staff-assign-room'),
    path('<str:booking_id>/checkout/', BookingAssignmentView.as_view(), {'action': 'checkout'}),
    
    # Party management
    path('<str:booking_id>/party/', BookingPartyManagementView.as_view(), name='room-bookings-staff-party'),
    
    # Safe assignment system
    path('available-rooms/', AvailableRoomsView.as_view(), name='available-rooms'),
    path('safe-assign/', SafeAssignRoomView.as_view(), name='safe-assign-room'),
    path('unassign-room/', UnassignRoomView.as_view(), name='unassign-room'),
]
```

## Room Assignment System

### Safe Assignment Service
**Location**: `room_bookings/services/room_assignment.py`

The room assignment system prevents double-booking through atomic operations and conflict detection.

#### Key Components:

1. **RoomAssignmentService.find_available_rooms_for_booking()**
   - Finds rooms available for a specific booking
   - Considers room type matching
   - Checks for overlap conflicts
   - Uses inventory blocking status logic

2. **RoomAssignmentService.assert_room_can_be_assigned()**
   - Validates hotel scope matching
   - Checks booking status eligibility
   - Prevents assignment to in-house guests
   - Validates room type compatibility
   - Detects overlap conflicts

3. **RoomAssignmentService.assign_room_atomic()**
   - Atomic assignment with database locking
   - Full conflict validation inside transaction
   - Audit trail logging
   - Handles reassignment scenarios

#### Inventory Blocking Logic:

```python
# A booking blocks room inventory if:
blocking_filter = models.Q(
    status='CONFIRMED',          # Confirmed booking
    checked_out_at__isnull=True  # Not checked out yet
) | models.Q(
    checked_in_at__isnull=False,  # Guest is checked in
    checked_out_at__isnull=True   # But not checked out
)
```

#### Assignment States:

- **ASSIGNABLE_BOOKING_STATUSES**: `['CONFIRMED']`
- **INVENTORY_BLOCKING_STATUSES**: `['CONFIRMED']`
- **NON_BLOCKING_STATUSES**: `['CANCELLED', 'COMPLETED', 'NO_SHOW']`

### Assignment Flow:

1. **Room Selection**: Staff selects available room from filtered list
2. **Validation**: System validates assignment eligibility
3. **Atomic Assignment**: Database transaction with locking
4. **Audit Logging**: Timestamp and staff member tracking
5. **Real-time Updates**: Pusher broadcast to connected clients

## Booking Flow Diagrams

### Guest Booking Flow

```
Guest Request → Availability Check → Pricing Quote → Booking Creation → Payment → Confirmation
     ↓              ↓                  ↓              ↓            ↓         ↓
   Validate     Check Room         Generate         Create      Process   Send Email
    Dates      Availability         Quote         Booking      Payment   & SMS
     ↓              ↓                  ↓              ↓            ↓         ↓
   Return      Return Available    Store Quote    Store in DB   Update    Return
   Results        Room Types       (15 min TTL)    (PENDING)    Status   Booking ID
```

### Staff Management Flow

```
Staff Login → Hotel Dashboard → Booking List → Booking Detail → Room Assignment → Check-in
     ↓             ↓              ↓             ↓                ↓              ↓
  Authenticate  Load Hotel      Filter &      View Complete   Select Room   Update Status
      ↓         Bookings        Search        Information        ↓              ↓
  Set Hotel        ↓              ↓             ↓             Validate      Set Timestamps
   Context    Real-time         Pagination   Party Mgmt      Assignment         ↓
      ↓       Updates              ↓             ↓                ↓         Real-time
  Load Staff      ↓           Export CSV    Add/Remove       Atomic DB      Updates
  Profile    Pusher Channel                  Guests         Transaction
```

### Room Assignment Flow

```
Booking Confirmed → Available Rooms → Room Selection → Validation → Assignment → Audit Log
      ↓                 ↓                ↓              ↓             ↓           ↓
  Status Check     Query Inventory   Staff Choice   Check Status   Update DB   Log Action
      ↓                 ↓                ↓              ↓             ↓           ↓
  In-house?       Filter Conflicts  Validate Room  Conflict Check  Lock Tables  Track Staff
      ↓                 ↓                ↓              ↓             ↓           ↓
  Block if Yes    Room Type Match   Hotel Match    Atomic Txn     Set Room    Timestamp
```

## API Contracts

### Booking Creation Request
```json
{
  "room_type_code": "DBL",
  "check_in": "2025-01-15",
  "check_out": "2025-01-17",
  "adults": 2,
  "children": 0,
  "primary_first_name": "John",
  "primary_last_name": "Doe",
  "primary_email": "john@example.com",
  "primary_phone": "+1234567890",
  "booker_type": "SELF",
  "quote_id": "QUOTE-2025-001",
  "special_requests": "Late check-in requested",
  "promo_code": "WINTER2025"
}
```

### Booking Creation Response
```json
{
  "booking_id": "BK-2025-0001",
  "confirmation_number": "HTL-2025-0001",
  "status": "PENDING_PAYMENT",
  "hotel": {
    "name": "Grand Hotel",
    "slug": "grand-hotel"
  },
  "room": {
    "type": "Double Room",
    "code": "DBL"
  },
  "dates": {
    "check_in": "2025-01-15",
    "check_out": "2025-01-17",
    "nights": 2
  },
  "guests": {
    "adults": 2,
    "children": 0,
    "primary_name": "John Doe"
  },
  "pricing": {
    "total_amount": "150.00",
    "currency": "EUR"
  },
  "created_at": "2025-01-10T14:30:00Z"
}
```

### Staff Booking List Response
```json
{
  "count": 25,
  "next": "?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "booking_id": "BK-2025-0001",
      "confirmation_number": "HTL-2025-0001",
      "guest_name": "John Doe",
      "room_type_name": "Double Room",
      "assigned_room_number": "201",
      "check_in": "2025-01-15",
      "check_out": "2025-01-17",
      "nights": 2,
      "adults": 2,
      "children": 0,
      "total_amount": "150.00",
      "currency": "EUR",
      "status": "CONFIRMED",
      "created_at": "2025-01-10T14:30:00Z",
      "checked_in_at": null,
      "checked_out_at": null
    }
  ]
}
```

### Room Assignment Request
```json
{
  "room_id": 15,
  "notes": "Guest requested quiet room away from elevator"
}
```

### Room Assignment Response
```json
{
  "success": true,
  "booking": {
    "booking_id": "BK-2025-0001",
    "assigned_room": {
      "id": 15,
      "room_number": "201",
      "room_type": "Double Room"
    },
    "room_assigned_at": "2025-01-10T16:45:00Z",
    "room_assigned_by": "staff@hotel.com",
    "assignment_notes": "Guest requested quiet room away from elevator"
  }
}
```

## Error Handling

### Room Assignment Errors
```json
{
  "error": {
    "code": "ROOM_OVERLAP_CONFLICT",
    "message": "Room 201 has overlapping bookings",
    "details": {
      "conflicting_booking_ids": [123, 124]
    }
  }
}
```

### Validation Errors
```json
{
  "error": {
    "code": "INVALID_DATE_RANGE",
    "message": "Check-out date must be after check-in date",
    "field": "check_out"
  }
}
```

## Real-time Updates

### Pusher Channels
- **Hotel Channel**: `hotel-{hotel_slug}`
- **Booking Updates**: `booking-updated`, `booking-created`, `room-assigned`
- **Room Updates**: `room-status-changed`, `room-assignment-changed`

### Event Payloads
```javascript
// Booking update event
{
  event: 'booking-updated',
  data: {
    booking_id: 'BK-2025-0001',
    status: 'CONFIRMED',
    assigned_room_number: '201',
    timestamp: '2025-01-10T16:45:00Z'
  }
}
```

## Security and Permissions

### Permission Classes
- **Public Endpoints**: `AllowAny`
- **Staff Endpoints**: `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`
- **Hotel Scoping**: All operations scoped to staff's assigned hotel

### Data Privacy
- Guest personal data encrypted at rest
- PII access logged and audited
- GDPR compliance for data export/deletion
- Payment data handled via PCI-compliant processors

## Performance Considerations

### Database Optimizations
- Indexed fields: hotel, booking_id, status, check_in/out dates
- Select_related for room_type and hotel joins
- Prefetch_related for booking party data
- Database-level constraints for data integrity

### Caching Strategy
- Room availability cached for 5 minutes
- Pricing quotes cached for 15 minutes
- Hotel configuration cached for 1 hour
- Redis for session and real-time data

### Monitoring and Logging
- Booking creation/modification audit trails
- Room assignment conflict logging
- Performance metrics for API endpoints
- Real-time dashboard for booking statistics

---

*This documentation covers the complete room booking system as implemented in the HotelMate backend. All URLs, models, and serializers are production-ready and actively used in the system.*