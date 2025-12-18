# Guest & Booking Architecture Analysis

**Date**: December 18, 2025  
**Analysis**: Complete system architecture for Guest, BookingGuest, and RoomBooking models

## Current System Architecture

### 1. **RoomBooking Model** (`hotel/models.py`)
**Purpose**: Pre-arrival reservation/booking management

```python
class RoomBooking(models.Model):
    # Core booking info
    booking_id = models.CharField(unique=True)  # "BK-2025-0001"
    hotel = models.ForeignKey(Hotel)
    room_type = models.ForeignKey(RoomType)
    check_in/check_out = models.DateField()
    
    # Primary guest (always stays)
    primary_first_name = models.CharField()
    primary_last_name = models.CharField()
    primary_email = models.EmailField()
    
    # Booker (may not stay - company bookings)
    booker_first_name = models.CharField()
    booker_email = models.EmailField()
    booker_type = models.CharField()  # SELF, COMPANY, AGENT
    
    # Room assignment & check-in tracking
    assigned_room = models.ForeignKey(Room, null=True)
    checked_in_at = models.DateTimeField(null=True)
    checked_out_at = models.DateTimeField(null=True)
    
    # Precheckin data (booking-level)
    precheckin_payload = models.JSONField()  # ETA, special_requests
    precheckin_submitted_at = models.DateTimeField(null=True)
```

**Status**: ✅ **Pre-arrival & Arrival Management**

---

### 2. **BookingGuest Model** (`hotel/models.py`)
**Purpose**: Booking party members (companions + primary)

```python
class BookingGuest(models.Model):
    booking = models.ForeignKey(RoomBooking, related_name='party')
    role = models.CharField()  # PRIMARY, COMPANION
    
    # Guest details
    first_name = models.CharField()
    last_name = models.CharField()
    email = models.EmailField(blank=True)
    phone = models.CharField(blank=True)
    is_staying = models.BooleanField(default=True)
    
    # Individual precheckin data (guest-level)
    precheckin_payload = models.JSONField()  # nationality, dietary_requirements
```

**Status**: ✅ **Booking Party Management**

---

### 3. **Guest Model** (`guests/models.py`)
**Purpose**: In-house guest management with room assignments

```python
class Guest(models.Model):
    # Basic info
    first_name = models.CharField()
    last_name = models.CharField()
    hotel = models.ForeignKey(Hotel)
    
    # Room assignment & stay tracking
    room = models.ForeignKey(Room, null=True)
    check_in_date = models.DateField(null=True)
    check_out_date = models.DateField(null=True)
    days_booked = models.PositiveIntegerField()
    id_pin = models.CharField(unique=True)  # Room access PIN
    
    # Booking connections
    booking = models.ForeignKey(RoomBooking, null=True, related_name='guests')
    booking_guest = models.ForeignKey(BookingGuest, null=True, related_name='in_house_guest')
    
    # Guest hierarchy
    guest_type = models.CharField()  # PRIMARY, COMPANION, WALKIN
    primary_guest = models.ForeignKey('self', null=True)
```

**Status**: ✅ **In-House Guest Management**

---

## Data Flow & Connection Points

### **Phase 1: Booking Creation**
```mermaid
RoomBooking Created
    ↓
PRIMARY BookingGuest Auto-Created
    ↓
Party Incomplete (missing companions)
```

### **Phase 2: Pre-check-in Submission**
```mermaid
Guest Submits Precheckin Form
    ↓
COMPANION BookingGuests Created/Updated
    ↓
precheckin_payload Stored (booking + individual level)
    ↓
Party Complete ✅
```

### **Phase 3: Check-in Process** 
```mermaid
Staff Assigns Room → RoomBooking.assigned_room
    ↓
Staff Checks In → RoomBooking.checked_in_at
    ↓
Guest Records Created → BookingGuest → Guest
    ↓
Room PINs Generated → Guest.id_pin
```

---

## Current Issues & Gaps

### ❌ **Missing Check-in Integration**
- No automated BookingGuest → Guest conversion
- Manual guest creation required
- Precheckin data not transferred to Guest records

### ❌ **Data Duplication**
- Guest info duplicated across BookingGuest and Guest
- No single source of truth after check-in

### ❌ **Precheckin Data Loss**
- BookingGuest.precheckin_payload not transferred to Guest
- Guest records missing nationality, dietary requirements, etc.

---

## Recommended Solution

### **1. Enhanced Check-in Process**

Create automated conversion in check-in endpoint:

```python
# hotel/staff_views.py - CheckInBookingView
def post(self, request, hotel_slug, booking_id):
    booking = get_object_or_404(RoomBooking, booking_id=booking_id)
    
    # Check-in booking
    booking.checked_in_at = timezone.now()
    booking.save()
    
    # Convert BookingGuests to Guests
    for booking_guest in booking.party.all():
        guest, created = Guest.objects.get_or_create(
            booking_guest=booking_guest,
            defaults={
                'hotel': booking.hotel,
                'room': booking.assigned_room,
                'first_name': booking_guest.first_name,
                'last_name': booking_guest.last_name,
                'check_in_date': booking.check_in,
                'check_out_date': booking.check_out,
                'days_booked': booking.nights,
                'booking': booking,
                'guest_type': booking_guest.role,
                # Transfer precheckin data
                'precheckin_data': booking_guest.precheckin_payload
            }
        )
        
        # Generate PIN for room access
        if not guest.id_pin:
            guest.id_pin = generate_unique_pin()
            guest.save()
```

### **2. Add Precheckin Data to Guest Model**

```python
# guests/models.py
class Guest(models.Model):
    # ... existing fields ...
    
    # Add precheckin data storage
    precheckin_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Transferred precheckin data from BookingGuest"
    )
    
    # Add convenience properties
    @property
    def nationality(self):
        return self.precheckin_data.get('nationality', '')
    
    @property
    def dietary_requirements(self):
        return self.precheckin_data.get('dietary_requirements', '')
```

### **3. Update Admin Interface**

Show precheckin data in Guest admin:

```python
# guests/admin.py
@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'room_number', 
        'nationality_display', 'check_in_date', 'in_house'
    )
    
    def nationality_display(self, obj):
        return obj.nationality or '-'
    nationality_display.short_description = 'Nationality'
```

---

## Connection Timeline

### **When to Connect Models:**

#### ✅ **Booking Creation**
- `RoomBooking` created
- PRIMARY `BookingGuest` auto-created
- **Connection**: RoomBooking ←→ BookingGuest (party relationship)

#### ✅ **Precheckin Submission**
- COMPANION `BookingGuest` records created
- Precheckin data stored in `BookingGuest.precheckin_payload`
- **Connection**: Form data → BookingGuest records

#### 🔧 **Room Assignment** (Staff Action)
- `RoomBooking.assigned_room` set
- Room marked as occupied
- **Connection**: RoomBooking → Room

#### 🔧 **Check-in Process** (Staff Action)
- `RoomBooking.checked_in_at` set
- **NEW**: `Guest` records created from `BookingGuest`
- Precheckin data transferred
- PINs generated
- **Connection**: BookingGuest → Guest (1:1 idempotent)

#### 🔧 **Check-out Process** (Staff Action)
- `RoomBooking.checked_out_at` set
- `Guest` records marked as checked out
- Room marked as available

---

## Implementation Priority

### **Phase 1: Immediate (High Priority)**
1. ✅ Fix precheckin frontend format issue
2. ✅ Admin interface shows precheckin data
3. 🔧 Automated BookingGuest → Guest conversion on check-in

### **Phase 2: Enhancement (Medium Priority)**
1. 🔧 Add precheckin_data field to Guest model
2. 🔧 Update Guest admin to show precheckin data
3. 🔧 Guest API endpoints include precheckin data

### **Phase 3: Optimization (Low Priority)**
1. 🔧 Data cleanup scripts for existing guests
2. 🔧 Performance optimization for large guest datasets
3. 🔧 Advanced precheckin field validation

---

## Benefits of This Architecture

### ✅ **Clear Separation of Concerns**
- **RoomBooking**: Pre-arrival reservation management
- **BookingGuest**: Party composition & precheckin data
- **Guest**: In-house operations & room access

### ✅ **Data Integrity**
- Perfect 1:1 mapping BookingGuest → Guest
- Idempotent check-in process
- No data loss during transitions

### ✅ **Operational Efficiency**
- Staff see precheckin data during check-in
- Automated PIN generation
- Seamless booking → in-house transition

### ✅ **Future-Proof**
- Supports walk-in guests (Guest without BookingGuest)
- Handles company bookings (booker ≠ primary guest)
- Extensible for loyalty programs, preferences, etc.

---

## Conclusion

The current three-model architecture is **well-designed** but needs **better integration** at check-in. The key missing piece is automated data transfer from BookingGuest to Guest during the check-in process.

**Priority Action**: Implement the automated check-in conversion process to ensure precheckin data flows seamlessly from booking → in-house guest management.