# Room Model & Frontend Display Guide

**Date**: December 18, 2025  
**Analysis**: Current Room model structure, serializers, and frontend display recommendations

## Current Room Model Structure

### **Room Model** (`rooms/models.py`)

```python
class Room(models.Model):
    # Basic Information
    hotel = models.ForeignKey('hotel.Hotel')
    room_number = models.IntegerField()
    room_type = models.ForeignKey('rooms.RoomType')  # Links to room category
    
    # Availability & Status
    room_status = models.CharField(max_length=20, choices=[
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('CHECKOUT_DIRTY', 'Checkout Dirty'),
        ('CLEANING_IN_PROGRESS', 'Cleaning in Progress'),
        ('CLEANED_UNINSPECTED', 'Cleaned Uninspected'),
        ('MAINTENANCE_REQUIRED', 'Maintenance Required'),
        ('OUT_OF_ORDER', 'Out of Order'),
        ('READY_FOR_GUEST', 'Ready for Guest')
    ])
    
    # Control Flags
    is_active = models.BooleanField()  # Available for booking
    is_occupied = models.BooleanField()  # Guest currently in room
    is_out_of_order = models.BooleanField()  # Hard flag - overrides everything
    maintenance_required = models.BooleanField()
    
    # Guest Management
    guest_id_pin = models.CharField(unique=True)  # Room access PIN
    guest_fcm_token = models.CharField()  # Push notifications
    
    # QR Codes for Services
    room_service_qr_code = models.URLField()
    in_room_breakfast_qr_code = models.URLField()
    dinner_booking_qr_code = models.URLField()
    chat_pin_qr_code = models.URLField()
    
    # Housekeeping Tracking
    last_cleaned_at = models.DateTimeField()
    cleaned_by_staff = models.ForeignKey('staff.Staff')
    last_inspected_at = models.DateTimeField()
    inspected_by_staff = models.ForeignKey('staff.Staff')
    turnover_notes = models.TextField()
    
    # Maintenance
    maintenance_priority = models.CharField(choices=[
        ('LOW', 'Low Priority'),
        ('MED', 'Medium Priority'),
        ('HIGH', 'High Priority')
    ])
    maintenance_notes = models.TextField()
```

**✅ Key Methods**:
```python
def is_bookable(self):
    """Single source of truth for room availability"""
    if self.is_out_of_order:
        return False
        
    return (
        self.room_status in {'AVAILABLE', 'READY_FOR_GUEST'} and
        self.is_active and
        not self.maintenance_required
    )
```

---

### **RoomType Model** (`rooms/models.py`)

```python
class RoomType(models.Model):
    # Basic Information
    hotel = models.ForeignKey('hotel.Hotel')
    code = models.CharField()  # 'STD', 'DLX', 'SUI'
    name = models.CharField()  # 'Standard Double', 'Deluxe Suite'
    short_description = models.TextField()
    
    # Room Specifications
    max_occupancy = models.PositiveSmallIntegerField()  # Maximum guests
    bed_setup = models.CharField()  # 'King Bed', '2 Queen Beds'
    photo = CloudinaryField()  # Room type image
    
    # Pricing
    starting_price_from = models.DecimalField()  # Marketing "from" price
    currency = models.CharField()  # 'EUR', 'USD'
    
    # Booking Integration
    booking_code = models.CharField()  # Integration code
    booking_url = models.URLField()  # Deep link to book
    availability_message = models.CharField()  # 'High demand'
    
    # Display Settings
    sort_order = models.PositiveIntegerField()  # Display order
    is_active = models.BooleanField()  # Show publicly
```

---

## Current Serializers

### **Room Serializer** (`rooms/serializers.py`)

```python
class RoomSerializer(serializers.ModelSerializer):
    guests_in_room = GuestSerializer(many=True, read_only=True)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    
    # Grouped guest output
    primary_guest = serializers.SerializerMethodField()
    companions = serializers.SerializerMethodField()
    walkins = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            'id', 'hotel', 'hotel_name', 'room_number', 'hotel_slug',
            'guests_in_room', 'primary_guest', 'companions', 'walkins',
            'guest_id_pin', 'is_occupied',
            'room_service_qr_code', 'in_room_breakfast_qr_code',
            'dinner_booking_qr_code', 'chat_pin_qr_code'
        ]
```

### **RoomType Serializer** (`hotel/booking_serializers.py`)

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

    def get_photo_url(self, obj):
        return obj.photo.url if obj.photo else None
```

---

## Current Frontend API Responses

### **Availability API Response**
```json
GET /api/public/hotel/hotel-killarney/availability/
{
  "hotel": "hotel-killarney",
  "hotel_name": "Hotel Killarney",
  "check_in": "2025-01-15",
  "check_out": "2025-01-17",
  "nights": 2,
  "adults": 2,
  "children": 0,
  "available_rooms": [
    {
      "id": 123,
      "code": "STD",
      "name": "Standard Double",
      "short_description": "Comfortable room with city view",
      "max_occupancy": 2,
      "bed_setup": "King Bed",
      "photo_url": "https://res.cloudinary.com/...",
      "starting_price_from": "120.00",
      "currency": "EUR",
      "availability_message": "Popular choice",
      "available_units": 3,
      "base_price_per_night": "120.00"
    }
  ]
}
```

### **Room Status API Response** (Staff)
```json
GET /api/staff/hotel/hotel-killarney/rooms/
{
  "rooms": [
    {
      "id": 456,
      "room_number": 201,
      "room_status": "AVAILABLE",
      "is_occupied": false,
      "is_bookable": true,
      "room_type": {
        "id": 123,
        "name": "Standard Double",
        "code": "STD"
      },
      "guests_in_room": [],
      "primary_guest": null,
      "companions": [],
      "last_cleaned_at": "2025-12-18T10:30:00Z",
      "maintenance_required": false,
      "turnover_notes": ""
    }
  ]
}
```

---

## Frontend Display Components

### **1. Room Type Display (Public Booking)**

```jsx
// RoomTypeCard.jsx
const RoomTypeCard = ({ roomType, onSelect }) => {
  return (
    <div className="room-type-card">
      <div className="room-image">
        {roomType.photo_url && (
          <img src={roomType.photo_url} alt={roomType.name} />
        )}
      </div>
      
      <div className="room-info">
        <h3>{roomType.name}</h3>
        <p className="room-description">{roomType.short_description}</p>
        
        <div className="room-specs">
          <span className="bed-setup">{roomType.bed_setup}</span>
          <span className="occupancy">
            Max {roomType.max_occupancy} guests
          </span>
        </div>
        
        <div className="pricing">
          <span className="price">
            From {roomType.currency} {roomType.starting_price_from}
          </span>
          <span className="per-night">per night</span>
        </div>
        
        {roomType.availability_message && (
          <div className="availability-badge">
            {roomType.availability_message}
          </div>
        )}
        
        <button 
          onClick={() => onSelect(roomType)}
          className="select-room-btn"
        >
          Select Room
        </button>
      </div>
    </div>
  );
};
```

### **2. Room Status Display (Staff Dashboard)**

```jsx
// RoomStatusCard.jsx
const RoomStatusCard = ({ room }) => {
  const getStatusColor = (status) => {
    const colors = {
      'AVAILABLE': 'green',
      'OCCUPIED': 'blue',
      'CHECKOUT_DIRTY': 'orange',
      'CLEANING_IN_PROGRESS': 'yellow',
      'MAINTENANCE_REQUIRED': 'red',
      'OUT_OF_ORDER': 'red',
      'READY_FOR_GUEST': 'green'
    };
    return colors[status] || 'gray';
  };

  return (
    <div className="room-status-card">
      <div className="room-header">
        <h4>Room {room.room_number}</h4>
        <span 
          className={`status-badge ${getStatusColor(room.room_status)}`}
        >
          {room.room_status.replace('_', ' ')}
        </span>
      </div>
      
      <div className="room-type">
        {room.room_type.name} ({room.room_type.code})
      </div>
      
      {room.primary_guest && (
        <div className="current-guest">
          <strong>Guest:</strong> {room.primary_guest.first_name} {room.primary_guest.last_name}
        </div>
      )}
      
      {room.companions.length > 0 && (
        <div className="companions">
          <strong>Companions:</strong> {room.companions.length}
        </div>
      )}
      
      <div className="room-actions">
        {room.room_status === 'CHECKOUT_DIRTY' && (
          <button className="action-btn clean">Mark as Cleaning</button>
        )}
        
        {room.room_status === 'CLEANED_UNINSPECTED' && (
          <button className="action-btn inspect">Inspect Room</button>
        )}
        
        {room.maintenance_required && (
          <button className="action-btn maintenance">View Maintenance</button>
        )}
      </div>
      
      {room.turnover_notes && (
        <div className="notes">
          <small>{room.turnover_notes}</small>
        </div>
      )}
    </div>
  );
};
```

### **3. Room Assignment Component (Staff)**

```jsx
// RoomAssignmentSelector.jsx
const RoomAssignmentSelector = ({ booking, availableRooms, onAssign }) => {
  const [selectedRoom, setSelectedRoom] = useState(null);

  const filterSuitableRooms = (rooms) => {
    return rooms.filter(room => {
      // Party size check
      const partySize = booking.party.length;
      if (partySize > room.room_type.max_occupancy) {
        return false;
      }
      
      // Room type match
      if (room.room_type.id !== booking.room_type.id) {
        return false;
      }
      
      // Bookable status
      return room.is_bookable;
    });
  };

  const suitableRooms = filterSuitableRooms(availableRooms);

  return (
    <div className="room-assignment">
      <h3>Assign Room to Booking {booking.booking_id}</h3>
      
      <div className="booking-info">
        <p><strong>Guest:</strong> {booking.primary_guest_name}</p>
        <p><strong>Party Size:</strong> {booking.party.length} guests</p>
        <p><strong>Room Type:</strong> {booking.room_type.name}</p>
      </div>
      
      <div className="available-rooms">
        <h4>Available Rooms ({suitableRooms.length})</h4>
        
        {suitableRooms.map(room => (
          <div 
            key={room.id}
            className={`room-option ${selectedRoom?.id === room.id ? 'selected' : ''}`}
            onClick={() => setSelectedRoom(room)}
          >
            <div className="room-number">
              Room {room.room_number}
            </div>
            
            <div className="room-details">
              <span className="room-type">{room.room_type.name}</span>
              <span className="capacity">
                Max {room.room_type.max_occupancy} guests
              </span>
            </div>
            
            <div className="room-status">
              <span className={`status ${room.room_status.toLowerCase()}`}>
                {room.room_status.replace('_', ' ')}
              </span>
            </div>
            
            {room.last_cleaned_at && (
              <div className="cleaning-info">
                Last cleaned: {new Date(room.last_cleaned_at).toLocaleDateString()}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {selectedRoom && (
        <button 
          onClick={() => onAssign(booking.booking_id, selectedRoom.id)}
          className="assign-btn"
        >
          Assign Room {selectedRoom.room_number}
        </button>
      )}
    </div>
  );
};
```

### **4. Room Availability Display (Public)**

```jsx
// AvailabilityResults.jsx
const AvailabilityResults = ({ searchData, availableRooms, onSelectRoom }) => {
  return (
    <div className="availability-results">
      <div className="search-summary">
        <h2>Available Rooms</h2>
        <p>
          {searchData.check_in} - {searchData.check_out} 
          ({searchData.nights} nights)
        </p>
        <p>
          {searchData.adults} adults
          {searchData.children > 0 && `, ${searchData.children} children`}
        </p>
      </div>
      
      {availableRooms.length === 0 ? (
        <div className="no-availability">
          <h3>No rooms available</h3>
          <p>Please try different dates or contact the hotel directly.</p>
        </div>
      ) : (
        <div className="room-types-grid">
          {availableRooms.map(roomType => (
            <RoomTypeCard
              key={roomType.id}
              roomType={roomType}
              onSelect={onSelectRoom}
            />
          ))}
        </div>
      )}
    </div>
  );
};
```

---

## Enhanced Frontend API Requirements

### **1. Enhanced Room Serializer** (Recommended)

```python
class EnhancedRoomSerializer(serializers.ModelSerializer):
    room_type = RoomTypeSerializer(read_only=True)
    status_display = serializers.CharField(source='get_room_status_display', read_only=True)
    is_bookable = serializers.SerializerMethodField()
    guest_summary = serializers.SerializerMethodField()
    housekeeping_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = [
            'id', 'room_number', 'room_status', 'status_display',
            'is_occupied', 'is_bookable', 'is_active', 'is_out_of_order',
            'maintenance_required', 'maintenance_priority',
            'room_type', 'guest_summary', 'housekeeping_status',
            'last_cleaned_at', 'last_inspected_at'
        ]
    
    def get_is_bookable(self, obj):
        return obj.is_bookable()
    
    def get_guest_summary(self, obj):
        guests = obj.guests_in_room.all()
        return {
            'count': guests.count(),
            'primary': guests.filter(guest_type='PRIMARY').first(),
            'companions_count': guests.filter(guest_type='COMPANION').count()
        }
    
    def get_housekeeping_status(self, obj):
        return {
            'last_cleaned': obj.last_cleaned_at,
            'cleaned_by': obj.cleaned_by_staff.full_name if obj.cleaned_by_staff else None,
            'last_inspected': obj.last_inspected_at,
            'inspected_by': obj.inspected_by_staff.full_name if obj.inspected_by_staff else None,
            'notes': obj.turnover_notes
        }
```

### **2. Frontend State Management**

```javascript
// roomStore.js
export const roomStore = {
  // Room status management
  rooms: {
    items: [],
    loading: false,
    error: null,
    filters: {
      status: null,
      roomType: null,
      floor: null
    }
  },
  
  // Room assignment
  assignment: {
    availableRooms: [],
    selectedRoom: null,
    loading: false,
    error: null
  },
  
  // Room types for booking
  roomTypes: {
    items: [],
    loading: false,
    error: null
  }
};

// Actions
export const roomActions = {
  async fetchRooms(hotelSlug, filters = {}) {
    // GET /api/staff/hotel/{slug}/rooms/
  },
  
  async fetchAvailableRooms(hotelSlug, booking) {
    // GET /api/staff/hotel/{slug}/bookings/{id}/available-rooms/
  },
  
  async assignRoom(hotelSlug, bookingId, roomId) {
    // POST /api/staff/hotel/{slug}/bookings/{id}/assign-room/
  },
  
  async updateRoomStatus(hotelSlug, roomId, status) {
    // PATCH /api/staff/hotel/{slug}/rooms/{id}/status/
  }
};
```

---

## Missing Features for Enhanced Display

### **❌ Current Gaps:**

1. **No room preference matching** - bed type, floor, view preferences
2. **Limited guest requirement validation** - accessibility, special needs
3. **No intelligent room suggestions** - staff see all rooms, no smart filtering
4. **Missing guest journey context** - no connection to precheckin data

### **✅ Recommendations:**

1. **Add Guest Requirements to Display**
   - Show guest preferences from precheckin data
   - Highlight rooms that match requirements
   - Color-code suitability scores

2. **Enhanced Room Assignment UI**
   - Smart room suggestions based on guest needs
   - Preference matching indicators
   - Accessibility requirement flags

3. **Comprehensive Room Cards**
   - Show room amenities and features
   - Display recent guest feedback
   - Maintenance history summary

4. **Real-time Status Updates**
   - WebSocket updates for room status changes
   - Live occupancy tracking
   - Housekeeping progress indicators

**Priority**: Current room display is functional but needs enhancement for better guest experience and staff efficiency. Focus on adding guest requirement matching and intelligent room suggestions.