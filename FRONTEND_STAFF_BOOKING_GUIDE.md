# Frontend Implementation Guide - Staff Booking Management

## Overview
Staff booking management system with list, filter, confirm, and cancel functionality for Hotel Killarney bookings.

## API Base URL
```
Base: http://localhost:8000/api/staff/hotel/hotel-killarney
```

## Authentication Setup

### 1. Login Staff User
```javascript
// Login endpoint
const loginResponse = await fetch('/api/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'staff@hotelkillarney.com',
    password: 'password'
  })
});

const { access_token } = await loginResponse.json();

// Store token for all requests
const authHeaders = {
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
};
```

## Booking Management Components

### 1. Booking List Component

```javascript
// BookingList.jsx
import React, { useState, useEffect } from 'react';

const BookingList = () => {
  const [bookings, setBookings] = useState([]);
  const [filters, setFilters] = useState({
    status: '',
    start_date: '',
    end_date: ''
  });
  const [loading, setLoading] = useState(false);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      // Build query params
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);

      const response = await fetch(
        `/api/staff/hotel/hotel-killarney/bookings/?${params}`,
        {
          headers: authHeaders
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setBookings(data);
      } else {
        console.error('Failed to fetch bookings');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, [filters]);

  return (
    <div className="booking-list">
      <FilterControls filters={filters} setFilters={setFilters} />
      {loading ? (
        <div>Loading bookings...</div>
      ) : (
        <BookingTable bookings={bookings} onUpdate={fetchBookings} />
      )}
    </div>
  );
};
```

### 2. Filter Controls Component

```javascript
// FilterControls.jsx
const FilterControls = ({ filters, setFilters }) => {
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({ status: '', start_date: '', end_date: '' });
  };

  return (
    <div className="filter-controls">
      <div className="filter-group">
        <label>Status:</label>
        <select
          value={filters.status}
          onChange={(e) => handleFilterChange('status', e.target.value)}
        >
          <option value="">All Statuses</option>
          <option value="PENDING_PAYMENT">Pending Payment</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="CANCELLED">Cancelled</option>
          <option value="COMPLETED">Completed</option>
          <option value="NO_SHOW">No Show</option>
        </select>
      </div>

      <div className="filter-group">
        <label>Check-in From:</label>
        <input
          type="date"
          value={filters.start_date}
          onChange={(e) => handleFilterChange('start_date', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>Check-out Until:</label>
        <input
          type="date"
          value={filters.end_date}
          onChange={(e) => handleFilterChange('end_date', e.target.value)}
        />
      </div>

      <button onClick={clearFilters} className="btn-clear">
        Clear Filters
      </button>
    </div>
  );
};
```

### 3. Booking Table Component

```javascript
// BookingTable.jsx
const BookingTable = ({ bookings, onUpdate }) => {
  const handleConfirm = async (bookingId) => {
    if (!confirm('Confirm this booking?')) return;

    try {
      const response = await fetch(
        `/api/staff/hotel/hotel-killarney/bookings/${bookingId}/confirm/`,
        {
          method: 'POST',
          headers: authHeaders
        }
      );

      if (response.ok) {
        const result = await response.json();
        alert(result.message);
        onUpdate(); // Refresh booking list
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error confirming booking:', error);
      alert('Failed to confirm booking');
    }
  };

  const handleCancel = async (bookingId) => {
    const reason = prompt('Cancellation reason (optional):');
    if (reason === null) return; // User clicked cancel

    try {
      const response = await fetch(
        `/api/staff/hotel/hotel-killarney/bookings/${bookingId}/cancel/`,
        {
          method: 'POST',
          headers: authHeaders,
          body: JSON.stringify({ reason: reason || 'Cancelled by staff' })
        }
      );

      if (response.ok) {
        const result = await response.json();
        alert(result.message);
        onUpdate(); // Refresh booking list
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error cancelling booking:', error);
      alert('Failed to cancel booking');
    }
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      'PENDING_PAYMENT': 'badge-warning',
      'CONFIRMED': 'badge-success',
      'CANCELLED': 'badge-danger',
      'COMPLETED': 'badge-info',
      'NO_SHOW': 'badge-secondary'
    };
    
    return (
      <span className={`badge ${statusClasses[status]}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="booking-table-container">
      <table className="booking-table">
        <thead>
          <tr>
            <th>Booking ID</th>
            <th>Guest</th>
            <th>Room Type</th>
            <th>Dates</th>
            <th>Guests</th>
            <th>Total</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {bookings.map((booking) => (
            <tr key={booking.id}>
              <td>
                <div className="booking-id">
                  <strong>{booking.booking_id}</strong>
                  <small>{booking.confirmation_number}</small>
                </div>
              </td>
              <td>
                <div className="guest-info">
                  <div>{booking.guest_name}</div>
                  <small>{booking.guest_email}</small>
                  {booking.guest_phone && <small>{booking.guest_phone}</small>}
                </div>
              </td>
              <td>{booking.room_type_name}</td>
              <td>
                <div className="dates">
                  <div>{booking.check_in} → {booking.check_out}</div>
                  <small>{booking.nights} nights</small>
                </div>
              </td>
              <td>
                {booking.adults} adults
                {booking.children > 0 && `, ${booking.children} children`}
              </td>
              <td>
                <strong>{booking.currency} {booking.total_amount}</strong>
                {booking.paid_at && (
                  <div className="paid-indicator">✅ Paid</div>
                )}
              </td>
              <td>{getStatusBadge(booking.status)}</td>
              <td>
                <BookingActions
                  booking={booking}
                  onConfirm={() => handleConfirm(booking.booking_id)}
                  onCancel={() => handleCancel(booking.booking_id)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

### 4. Booking Actions Component

```javascript
// BookingActions.jsx
const BookingActions = ({ booking, onConfirm, onCancel }) => {
  const canConfirm = booking.status === 'PENDING_PAYMENT';
  const canCancel = ['PENDING_PAYMENT', 'CONFIRMED'].includes(booking.status);

  return (
    <div className="booking-actions">
      {canConfirm && (
        <button 
          onClick={onConfirm}
          className="btn btn-success btn-sm"
          title="Confirm Booking"
        >
          ✅ Confirm
        </button>
      )}
      
      {canCancel && (
        <button 
          onClick={onCancel}
          className="btn btn-danger btn-sm"
          title="Cancel Booking"
        >
          ❌ Cancel
        </button>
      )}
      
      {booking.status === 'CONFIRMED' && (
        <span className="text-success">✓ Confirmed</span>
      )}
      
      {booking.status === 'CANCELLED' && (
        <span className="text-danger">✗ Cancelled</span>
      )}
    </div>
  );
};
```

## CSS Styles

```css
/* BookingManagement.css */
.booking-list {
  padding: 20px;
}

.filter-controls {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-group label {
  font-weight: 600;
  font-size: 14px;
}

.filter-group input,
.filter-group select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn-clear {
  padding: 8px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  align-self: flex-end;
}

.booking-table-container {
  overflow-x: auto;
}

.booking-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.booking-table th,
.booking-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.booking-table th {
  background: #f8f9fa;
  font-weight: 600;
}

.booking-id strong {
  display: block;
  font-size: 14px;
}

.booking-id small {
  color: #6c757d;
  font-size: 12px;
}

.guest-info div {
  margin-bottom: 2px;
}

.guest-info small {
  display: block;
  color: #6c757d;
  font-size: 12px;
}

.dates small {
  color: #6c757d;
  font-size: 12px;
}

.badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-warning { background: #ffc107; color: #000; }
.badge-success { background: #28a745; color: white; }
.badge-danger { background: #dc3545; color: white; }
.badge-info { background: #17a2b8; color: white; }
.badge-secondary { background: #6c757d; color: white; }

.booking-actions {
  display: flex;
  gap: 8px;
}

.btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.btn-success { background: #28a745; color: white; }
.btn-danger { background: #dc3545; color: white; }
.btn-sm { padding: 4px 8px; }

.paid-indicator {
  color: #28a745;
  font-size: 12px;
  margin-top: 4px;
}
```

## Integration Example

```javascript
// App.jsx or BookingManagementPage.jsx
import React from 'react';
import BookingList from './components/BookingList';
import './styles/BookingManagement.css';

const BookingManagementPage = () => {
  return (
    <div className="booking-management-page">
      <header>
        <h1>Hotel Killarney - Booking Management</h1>
        <p>Manage room reservations and guest bookings</p>
      </header>
      
      <main>
        <BookingList />
      </main>
    </div>
  );
};

export default BookingManagementPage;
```

## Current Test Data

The system currently has **2 pending bookings** ready for testing:

1. **BK-20251128-0002** - Deluxe Double Room - €163.50
2. **BK-20251128-0001** - Standard Room - €1144.50

Both are in `PENDING_PAYMENT` status and can be confirmed or cancelled through the staff interface.

## Error Handling

All API calls include proper error handling with user-friendly messages. The interface gracefully handles:

- Authentication failures
- Network errors  
- Invalid booking states
- Permission errors

## Security

- All endpoints require staff authentication
- Staff can only manage bookings for their assigned hotel
- Actions are logged and traceable through booking status changes