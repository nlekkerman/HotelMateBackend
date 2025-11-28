# Frontend Booking Cancellation Data Fetching Guide

## 📡 **API Endpoints for Cancellation Data**

### **1. Staff Booking Detail Endpoint**
```javascript
GET /api/staff/hotel/{hotel_slug}/bookings/{booking_id}/
```

**Response includes structured cancellation data:**
```json
{
  "booking_id": "BK-2025-0002",
  "confirmation_number": "HOT-2025-0002",
  "status": "CANCELLED",
  "guest_name": "John Doe",
  "hotel": "Hotel Killarney",
  "room_type_name": "Deluxe Double Room",
  "check_in": "2025-11-28",
  "check_out": "2025-11-29",
  "total_amount": "163.50",
  "currency": "EUR",
  "created_at": "2025-11-28T08:04:00Z",
  "updated_at": "2025-11-28T08:45:00Z",
  
  "cancellation_details": {
    "cancelled_date": "2025-11-28 14:30:25",
    "cancelled_by": "Ivan Baricevic",
    "cancellation_reason": "Customer requested cancellation due to emergency"
  },
  
  "booking_summary": {
    "stay_duration": "1 night",
    "check_in_formatted": "November 28, 2025",
    "check_out_formatted": "November 29, 2025",
    "guest_count": "2 adults",
    "payment_status": "Pending",
    "total_formatted": "EUR 163.50",
    "created_formatted": "November 28, 2025 at 08:04 AM"
  },
  
  "room_photo_url": "https://cloudinary.../room_photo.jpg"
}
```

### **2. Staff Booking List Endpoint**
```javascript
GET /api/staff/hotel/{hotel_slug}/bookings/
```

**Each booking in the list includes cancellation data:**
```json
[
  {
    "booking_id": "BK-2025-0002",
    "status": "CANCELLED",
    "guest_name": "John Doe",
    "cancellation_details": {
      "cancelled_date": "2025-11-28 14:30:25", 
      "cancelled_by": "Ivan Baricevic",
      "cancellation_reason": "Customer emergency"
    }
  }
]
```

## 🎯 **Frontend Implementation Examples**

### **React Component - Booking Detail Modal**

```javascript
import React, { useState, useEffect } from 'react';

const BookingDetailModal = ({ bookingId, isOpen, onClose }) => {
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchBookingDetails = async () => {
    if (!bookingId) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `/api/staff/hotel/hotel-killarney/bookings/${bookingId}/`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setBooking(data);
      }
    } catch (error) {
      console.error('Failed to fetch booking:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && bookingId) {
      fetchBookingDetails();
    }
  }, [isOpen, bookingId]);

  if (!isOpen || !booking) return null;

  return (
    <div className="booking-detail-modal">
      <div className="modal-content">
        {/* Basic Booking Info */}
        <div className="booking-header">
          <h2>Booking {booking.booking_id}</h2>
          <span className={`status ${booking.status.toLowerCase()}`}>
            {booking.status}
          </span>
        </div>

        {/* Cancellation Details Section */}
        {booking.status === 'CANCELLED' && booking.cancellation_details && (
          <div className="cancellation-section">
            <h3>❌ Cancellation Information</h3>
            <div className="cancellation-grid">
              <div className="detail-item">
                <label>📅 Cancelled Date:</label>
                <span>{new Date(booking.cancellation_details.cancelled_date).toLocaleString()}</span>
              </div>
              <div className="detail-item">
                <label>👤 Cancelled By:</label>
                <span>{booking.cancellation_details.cancelled_by}</span>
              </div>
              <div className="detail-item">
                <label>📝 Reason:</label>
                <span className="reason">{booking.cancellation_details.cancellation_reason}</span>
              </div>
            </div>
          </div>
        )}

        {/* Other booking details */}
        <div className="booking-details">
          <h3>Booking Details</h3>
          <p><strong>Guest:</strong> {booking.guest_name}</p>
          <p><strong>Room:</strong> {booking.room_type_name}</p>
          <p><strong>Dates:</strong> {booking.booking_summary.check_in_formatted} - {booking.booking_summary.check_out_formatted}</p>
          <p><strong>Total:</strong> {booking.booking_summary.total_formatted}</p>
        </div>
      </div>
    </div>
  );
};

export default BookingDetailModal;
```

### **React Hook - Booking Data Management**

```javascript
// useBookingData.js
import { useState, useCallback } from 'react';

export const useBookingData = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchBookings = useCallback(async (filters = {}) => {
    setLoading(true);
    try {
      const params = new URLSearchParams(filters);
      const response = await fetch(
        `/api/staff/hotel/hotel-killarney/bookings/?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setBookings(data.results || data);
      }
    } catch (error) {
      console.error('Failed to fetch bookings:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchBookingDetail = useCallback(async (bookingId) => {
    try {
      const response = await fetch(
        `/api/staff/hotel/hotel-killarney/bookings/${bookingId}/`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch booking detail:', error);
    }
    return null;
  }, []);

  return {
    bookings,
    loading,
    fetchBookings,
    fetchBookingDetail
  };
};
```

### **Booking List Component with Cancellation Info**

```javascript
const BookingsList = () => {
  const { bookings, loading, fetchBookings } = useBookingData();
  const [selectedBooking, setSelectedBooking] = useState(null);

  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  const getCancellationDisplay = (booking) => {
    if (booking.status !== 'CANCELLED' || !booking.cancellation_details) {
      return null;
    }

    const { cancelled_by, cancellation_reason } = booking.cancellation_details;
    return (
      <div className="cancellation-preview">
        <span className="cancelled-by">❌ by {cancelled_by}</span>
        <span className="reason-preview">"{cancellation_reason.substring(0, 50)}..."</span>
      </div>
    );
  };

  return (
    <div className="bookings-list">
      <h2>Hotel Bookings</h2>
      
      {loading ? (
        <div className="loading">Loading bookings...</div>
      ) : (
        <div className="bookings-grid">
          {bookings.map(booking => (
            <div 
              key={booking.booking_id} 
              className={`booking-card ${booking.status.toLowerCase()}`}
              onClick={() => setSelectedBooking(booking.booking_id)}
            >
              <div className="booking-header">
                <span className="booking-id">{booking.booking_id}</span>
                <span className="status">{booking.status}</span>
              </div>
              
              <div className="booking-info">
                <p><strong>{booking.guest_name}</strong></p>
                <p>{booking.room_type_name}</p>
                <p>{booking.check_in} - {booking.check_out}</p>
              </div>

              {/* Show cancellation info for cancelled bookings */}
              {getCancellationDisplay(booking)}
            </div>
          ))}
        </div>
      )}

      {/* Booking Detail Modal */}
      {selectedBooking && (
        <BookingDetailModal
          bookingId={selectedBooking}
          isOpen={!!selectedBooking}
          onClose={() => setSelectedBooking(null)}
        />
      )}
    </div>
  );
};
```

## 🎨 **CSS Styling for Cancellation Display**

```css
/* Cancellation section styling */
.cancellation-section {
  background: #fff5f5;
  border: 1px solid #fed7d7;
  border-left: 4px solid #e53e3e;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
}

.cancellation-section h3 {
  color: #e53e3e;
  margin-top: 0;
}

.cancellation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-item label {
  font-weight: 600;
  color: #666;
  font-size: 14px;
}

.detail-item span {
  color: #333;
  font-size: 16px;
}

.detail-item .reason {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 6px;
  border-left: 3px solid #e53e3e;
  font-style: italic;
}

/* Booking list cancellation preview */
.cancellation-preview {
  margin-top: 10px;
  padding: 8px 12px;
  background: #fed7d7;
  border-radius: 6px;
  font-size: 12px;
}

.cancelled-by {
  font-weight: 600;
  color: #e53e3e;
  display: block;
}

.reason-preview {
  color: #666;
  font-style: italic;
  display: block;
  margin-top: 4px;
}

/* Status styling */
.status.cancelled {
  background: #e53e3e;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}
```

## 🔄 **Data Flow Summary**

1. **Backend**: Staff cancels booking → saves structured data to `special_requests`
2. **Serializer**: Automatically parses cancellation data into `cancellation_details`
3. **API**: Returns structured JSON with cancellation info
4. **Frontend**: Fetches via existing booking endpoints
5. **UI**: Displays date, staff name, and reason in organized sections

## 📋 **Available Cancellation Fields**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `cancelled_date` | String | ISO datetime when cancelled | `"2025-11-28 14:30:25"` |
| `cancelled_by` | String | Staff member who cancelled | `"Ivan Baricevic"` |
| `cancellation_reason` | String | Reason provided by staff | `"Customer emergency"` |

## 🎯 **Key Benefits**

- ✅ **No additional API calls** - cancellation data included in existing endpoints
- ✅ **Automatic parsing** - backend handles all data extraction
- ✅ **Real staff names** - proper staff identification 
- ✅ **Structured format** - consistent JSON response
- ✅ **UI-ready data** - formatted for direct display

The frontend gets all cancellation information automatically through the existing booking APIs! 🎉