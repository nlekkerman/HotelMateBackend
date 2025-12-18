# Booking Serializers and Primary Guest Logic Documentation

## 📋 Overview

This document explains the booking serializers architecture and the comprehensive logic for handling when the booker is the primary guest in the HotelMate system.

## 🏗️ Booking Serializers Architecture

### 1. Core Serializers Location

**Primary File**: `hotel/booking_serializers.py`

The system includes several key serializers:

#### A) BookingGuestSerializer
```python
class BookingGuestSerializer(serializers.ModelSerializer):
    """Serializer for booking party members"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BookingGuest
        fields = [
            'id', 'role', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'is_staying', 'created_at'
        ]
```

#### B) RoomBookingDetailSerializer
```python
class RoomBookingDetailSerializer(serializers.ModelSerializer):
    """Complete booking information for detail views"""
    
    class Meta:
        fields = [
            'id', 'booking_id', 'confirmation_number', 'hotel_name',
            'room_type_name', 'guest_name', 'booker_type',
            'booker_first_name', 'booker_last_name', 'booker_email',
            'booker_phone', 'booker_company', 'assigned_room_number',
            'check_in', 'check_out', 'nights', 'total_amount',
            'currency', 'status', 'party', 'party_complete'
        ]
```

#### C) PublicRoomBookingDetailSerializer
```python
class PublicRoomBookingDetailSerializer(serializers.ModelSerializer):
    """Public-safe serializer for external systems"""
    
    def get_guest_info(self, obj):
        """Primary guest information (public-safe fields only)"""
        return {
            "name": obj.primary_guest_name,
            "email": obj.primary_email,
            "phone": obj.primary_phone
        }
```

### 2. Related Serializers

#### Restaurant/Entertainment Bookings
**File**: `bookings/serializers.py`
- Different booking system for restaurants/entertainment
- Uses `BookingSerializer` and `BookingCreateSerializer`
- Handles guest relationships differently

## 🤴 Booker vs Primary Guest System

### Core Concept

The system distinguishes between:
- **Booker**: Person/entity making payment (may not stay)
- **Primary Guest**: Person staying in the room (always required)

### BookerType Constants

```python
class BookerType:
    SELF = 'SELF'           # Booker is staying
    THIRD_PARTY = 'THIRD_PARTY'  # Third-party booking
    COMPANY = 'COMPANY'     # Corporate booking
```

## 🔄 Primary Guest Logic Flow

### 1. Model-Level Logic (`hotel/models.py`)

#### A) Field Structure
```python
class RoomBooking(models.Model):
    # Booker fields (may be empty for SELF bookings)
    booker_type = models.CharField(choices=BookerType.choices(), default=BookerType.SELF)
    booker_first_name = models.CharField(max_length=100, blank=True)
    booker_last_name = models.CharField(max_length=100, blank=True)
    booker_email = models.EmailField(blank=True)
    booker_phone = models.CharField(max_length=30, blank=True)
    booker_company = models.CharField(max_length=150, blank=True)
    
    # Primary guest fields (always required)
    primary_first_name = models.CharField(max_length=100)
    primary_last_name = models.CharField(max_length=100)
    primary_email = models.EmailField(blank=True)
    primary_phone = models.CharField(max_length=30, blank=True)
```

#### B) Validation Logic
```python
def clean(self):
    """Validation for booker vs primary guest fields"""
    # Primary guest fields are always required
    if not self.primary_first_name or not self.primary_last_name:
        raise ValidationError("Primary guest first name and last name are required.")
```

#### C) Auto-Sync with Party System
```python
def _sync_primary_booking_guest(self):
    """Ensure PRIMARY BookingGuest exists and matches booking primary_* fields"""
    if not self.primary_first_name or not self.primary_last_name:
        return
        
    primary_guest, created = self.party.get_or_create(
        role='PRIMARY',
        defaults={
            'first_name': self.primary_first_name,
            'last_name': self.primary_last_name,
            'email': self.primary_email or '',
            'phone': self.primary_phone or '',
            'is_staying': True,
        }
    )
```

### 2. API Validation Logic (`hotel/booking_views.py`)

#### A) Rejection of Legacy Format
```python
# Hard rule: Reject legacy guest{} payload
if 'guest' in request.data:
    return Response({
        "detail": "Legacy guest payload is not supported. Use primary_* fields."
    }, status=status.HTTP_400_BAD_REQUEST)
```

#### B) Required Field Validation
```python
# Always required fields
required_fields = [
    room_type_code, check_in_str, check_out_str,
    primary_first_name, primary_last_name, primary_email,
    primary_phone, booker_type
]
```

#### C) Conditional Booker Field Validation
```python
# Validate conditional fields based on booker_type
if booker_type != BookerType.SELF:
    required_booker = [
        booker_first_name, booker_last_name, booker_email, booker_phone
    ]
    if not all(required_booker):
        return Response({
            "detail": "For THIRD_PARTY or COMPANY bookings, "
            "booker fields are required"
        }, status=status.HTTP_400_BAD_REQUEST)

if booker_type == BookerType.COMPANY:
    if not booker_company:
        return Response({
            "detail": "booker_company is required for COMPANY bookings"
        }, status=status.HTTP_400_BAD_REQUEST)
```

### 3. BookingGuest Model Validation (`hotel/models.py`)

#### A) PRIMARY Role Validation
```python
class BookingGuest(models.Model):
    def clean(self):
        """Validation for booking guest"""
        # For PRIMARY role, ensure it matches booking primary_* fields
        if self.role == 'PRIMARY' and self.booking_id:
            if (self.first_name != self.booking.primary_first_name or 
                self.last_name != self.booking.primary_last_name):
                raise ValidationError(
                    "PRIMARY guest name must match booking primary guest name. "
                    "Update booking primary fields instead."
                )
```

## 📊 Booker Type Handling Matrix

| Booker Type | Booker Fields Required | Primary Fields Required | Company Field Required | Logic |
|-------------|------------------------|--------------------------|------------------------|-------|
| `SELF` | ❌ No | ✅ Yes | ❌ No | Booker = Primary Guest |
| `THIRD_PARTY` | ✅ Yes | ✅ Yes | ❌ No | Different person paying |
| `COMPANY` | ✅ Yes | ✅ Yes | ✅ Yes | Corporate booking |

## 🔄 Data Flow for SELF Bookings

### 1. Request Processing
```json
{
  "booker_type": "SELF",
  "primary_first_name": "John",
  "primary_last_name": "Doe",
  "primary_email": "john@example.com",
  "primary_phone": "+353871234567"
}
```

### 2. Model Creation
```python
# No booker fields needed - they remain blank/null
booking = RoomBooking.objects.create(
    booker_type='SELF',
    booker_first_name='',  # Empty for SELF
    booker_last_name='',   # Empty for SELF
    booker_email='',       # Empty for SELF
    booker_phone='',       # Empty for SELF
    primary_first_name='John',
    primary_last_name='Doe',
    primary_email='john@example.com',
    primary_phone='+353871234567'
)
```

### 3. Auto Party Creation
```python
# System automatically creates PRIMARY BookingGuest
primary_guest = BookingGuest.objects.create(
    booking=booking,
    role='PRIMARY',
    first_name='John',  # From primary_first_name
    last_name='Doe',    # From primary_last_name
    email='john@example.com',
    phone='+353871234567',
    is_staying=True
)
```

## 🔄 Data Flow for THIRD_PARTY Bookings

### 1. Request Processing
```json
{
  "booker_type": "THIRD_PARTY",
  "booker_first_name": "Jane",
  "booker_last_name": "Smith",
  "booker_email": "jane@example.com",
  "booker_phone": "+353871111111",
  "primary_first_name": "John",
  "primary_last_name": "Doe",
  "primary_email": "john@example.com",
  "primary_phone": "+353872222222"
}
```

### 2. Model Creation
```python
# Both booker and primary fields populated
booking = RoomBooking.objects.create(
    booker_type='THIRD_PARTY',
    booker_first_name='Jane',    # Different person
    booker_last_name='Smith',
    booker_email='jane@example.com',
    booker_phone='+353871111111',
    primary_first_name='John',   # Person staying
    primary_last_name='Doe',
    primary_email='john@example.com',
    primary_phone='+353872222222'
)
```

## 📱 Serializer Response Examples

### SELF Booking Response
```json
{
  "booking_id": "BK-2025-001",
  "booker_type": "SELF",
  "guest_name": "John Doe",
  "primary_first_name": "John",
  "primary_last_name": "Doe",
  "booker_first_name": "",     // Empty for SELF
  "booker_last_name": "",      // Empty for SELF
  "party": {
    "primary": {
      "role": "PRIMARY",
      "first_name": "John",
      "last_name": "Doe",
      "is_staying": true
    }
  }
}
```

### THIRD_PARTY Booking Response
```json
{
  "booking_id": "BK-2025-002", 
  "booker_type": "THIRD_PARTY",
  "guest_name": "John Doe",
  "primary_first_name": "John",
  "primary_last_name": "Doe",
  "booker_first_name": "Jane",    // Different person
  "booker_last_name": "Smith",
  "party": {
    "primary": {
      "role": "PRIMARY", 
      "first_name": "John",
      "last_name": "Doe",
      "is_staying": true
    }
  }
}
```

## 🔧 Property Methods

### Model Properties for Easy Access
```python
@property
def primary_guest_name(self):
    """Full primary guest name"""
    return f"{self.primary_first_name} {self.primary_last_name}"

@property  
def booker_name(self):
    """Full booker name (if different from primary guest)"""
    if self.booker_first_name and self.booker_last_name:
        return f"{self.booker_first_name} {self.booker_last_name}"
    return ""

@property
def party_complete(self):
    """Check if all required staying guests have been provided"""
    expected = self.adults + self.children
    actual = self.party.filter(is_staying=True).count()
    return actual == expected
```

## 🛡️ Validation Rules Summary

### Always Required
- `primary_first_name`, `primary_last_name` (person staying)
- `booker_type` (relationship definition)
- `room_type_code`, `check_in`, `check_out` (booking basics)

### Conditionally Required
- **When `booker_type != SELF`**: All booker fields required
- **When `booker_type == COMPANY`**: `booker_company` required
- **Party validation**: Exactly one PRIMARY guest required

### Business Rules
1. **SELF bookings**: Booker fields remain empty, primary guest = booker
2. **Non-SELF bookings**: Both sets of fields required and populated
3. **Party sync**: PRIMARY BookingGuest automatically matches primary_* fields
4. **Name consistency**: PRIMARY party member must match booking primary fields

## 🔍 Migration History

### Field Evolution
- **Legacy**: Used `guest_*` fields for single guest concept
- **Phase 1**: Added `primary_*` and `booker_*` fields 
- **Phase 2**: Implemented `BookerType` enum and validation
- **Current**: Full booker/primary separation with party system

### Migration Logic
```python
def migrate_guest_fields_to_primary(apps, schema_editor):
    """Migrate existing guest_* fields to primary_* fields"""
    for booking in RoomBooking.objects.all():
        booking.primary_first_name = booking.guest_first_name or ''
        booking.primary_last_name = booking.guest_last_name or ''
        booking.primary_email = booking.guest_email or ''
        booking.primary_phone = booking.guest_phone or ''
        booking.booker_type = 'SELF'  # Existing bookings were self-bookings
        booking.save()
```

## 📚 Related Documentation

- `BOOKING_SERIALIZER_REFACTOR_PLAN.md` - Future refactoring plans
- `BOOKING_SERIALIZER_AUDIT.md` - Current serializer analysis
- `ROOM_BOOKING_DOMAIN.md` - Business domain definitions
- `ROOM_BOOKING_FIELD_DICTIONARY.md` - Complete field reference
- `NEW_BOOKING_CREATE_IMPLEMENTATION.md` - API implementation guide

## 🎯 Key Takeaways

1. **Clean Separation**: Booker (payer) vs Primary Guest (stayer) are distinct
2. **SELF Logic**: When booker_type='SELF', booker fields remain empty
3. **Automatic Sync**: PRIMARY BookingGuest records auto-sync with primary_* fields
4. **Validation**: Strong validation ensures data consistency
5. **Backwards Compatibility**: System handles legacy data through migrations
6. **Party System**: Modern party-based approach with role-based guest management

This architecture provides flexibility for different booking scenarios while maintaining data integrity and clear business logic separation.