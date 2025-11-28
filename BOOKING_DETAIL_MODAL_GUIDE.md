# Full-Screen Booking Detail Modal - Frontend Implementation

## Enhanced Booking Detail Component

```javascript
// BookingDetailModal.jsx
import React, { useState, useEffect } from 'react';
import './BookingDetailModal.css';

const BookingDetailModal = ({ bookingId, isOpen, onClose, onUpdate }) => {
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBookingDetail = async () => {
    if (!bookingId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/staff/hotel/hotel-killarney/bookings/${bookingId}/`,
        {
          headers: authHeaders
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setBooking(data);
      } else {
        setError('Failed to load booking details');
      }
    } catch (err) {
      setError('Error loading booking details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && bookingId) {
      fetchBookingDetail();
    }
  }, [isOpen, bookingId]);

  const handleConfirm = async () => {
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
        fetchBookingDetail(); // Refresh data
        onUpdate(); // Update parent list
      } else {
        const error = await response.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error('Error confirming booking:', error);
      alert('Failed to confirm booking');
    }
  };

  const handleCancel = async () => {
    // Enhanced cancellation dialog
    const reasons = [
      'Guest requested cancellation',
      'No-show',
      'Overbooking',
      'Room maintenance required',
      'Payment failed',
      'Other'
    ];
    
    const CancellationDialog = () => {
      const [selectedReason, setSelectedReason] = useState('');
      const [customReason, setCustomReason] = useState('');
      const [showCustom, setShowCustom] = useState(false);

      const submitCancellation = async () => {
        const finalReason = showCustom ? customReason : selectedReason;
        if (!finalReason) {
          alert('Please select or enter a cancellation reason');
          return;
        }

        try {
          const response = await fetch(
            `/api/staff/hotel/hotel-killarney/bookings/${bookingId}/cancel/`,
            {
              method: 'POST',
              headers: authHeaders,
              body: JSON.stringify({ reason: finalReason })
            }
          );

          if (response.ok) {
            const result = await response.json();
            alert(`${result.message}\\nReason: ${result.cancellation_reason}`);
            fetchBookingDetail(); // Refresh data
            onUpdate(); // Update parent list
          } else {
            const error = await response.json();
            alert(`Error: ${error.error}`);
          }
        } catch (error) {
          console.error('Error cancelling booking:', error);
          alert('Failed to cancel booking');
        }
      };

      // For now, using simple prompts - you can replace with proper modal
      const reasonChoice = prompt(
        `Select cancellation reason:\\n` +
        reasons.map((r, i) => `${i + 1}. ${r}`).join('\\n') +
        `\\n\\nEnter number (1-${reasons.length}) or custom reason:`
      );
      
      if (reasonChoice === null) return;
      
      const reasonIndex = parseInt(reasonChoice) - 1;
      let finalReason = '';
      
      if (reasonIndex >= 0 && reasonIndex < reasons.length) {
        finalReason = reasons[reasonIndex];
        
        if (finalReason === 'Other') {
          const custom = prompt('Please enter the cancellation reason:');
          if (custom === null) return;
          finalReason = custom || 'Cancelled by staff';
        }
      } else {
        finalReason = reasonChoice || 'Cancelled by staff';
      }

      if (!confirm(`Cancel booking with reason: "${finalReason}"?`)) return;

      // Submit the cancellation
      fetch(`/api/staff/hotel/hotel-killarney/bookings/${bookingId}/cancel/`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify({ reason: finalReason })
      }).then(response => response.json())
        .then(result => {
          alert(`${result.message}\\nReason: ${result.cancellation_reason}`);
          fetchBookingDetail();
          onUpdate();
        });
    };

    CancellationDialog();
  };

  const getStatusColor = (status) => {
    const colors = {
      'PENDING_PAYMENT': '#ffc107',
      'CONFIRMED': '#28a745',
      'CANCELLED': '#dc3545',
      'COMPLETED': '#17a2b8',
      'NO_SHOW': '#6c757d'
    };
    return colors[status] || '#6c757d';
  };

  if (!isOpen) return null;

  return (
    <div className="booking-detail-overlay">
      <div className="booking-detail-modal">
        {/* Header */}
        <div className="modal-header">
          <div className="header-left">
            <h2>Booking Details</h2>
            {booking && (
              <div className="booking-id-header">
                <span className="booking-id">{booking.booking_id}</span>
                <span 
                  className="status-badge" 
                  style={{ backgroundColor: getStatusColor(booking.status) }}
                >
                  {booking.status.replace('_', ' ')}
                </span>
              </div>
            )}
          </div>
          <div className="header-actions">
            {booking && booking.status === 'PENDING_PAYMENT' && (
              <>
                <button 
                  onClick={handleConfirm}
                  className="btn btn-success"
                >
                  ✅ Confirm Booking
                </button>
                <button 
                  onClick={handleCancel}
                  className="btn btn-danger"
                >
                  ❌ Cancel Booking
                </button>
              </>
            )}
            <button onClick={onClose} className="btn-close">✕</button>
          </div>
        </div>

        {/* Content */}
        <div className="modal-content">
          {loading && <div className="loading">Loading booking details...</div>}
          {error && <div className="error">{error}</div>}
          
          {booking && (
            <div className="booking-details-grid">
              
              {/* Room Information */}
              <div className="detail-section">
                <h3>Room Information</h3>
                <div className="room-info">
                  {booking.room_photo_url && (
                    <img 
                      src={booking.room_photo_url} 
                      alt={booking.room_type_name}
                      className="room-photo"
                    />
                  )}
                  <div className="room-details">
                    <h4>{booking.room_type_name}</h4>
                    <p className="room-description">{booking.booking_summary.room_description}</p>
                    <div className="occupancy">
                      <strong>Guests:</strong> {booking.booking_summary.guest_count}
                    </div>
                  </div>
                </div>
              </div>

              {/* Guest Information */}
              <div className="detail-section">
                <h3>Guest Information</h3>
                <div className="guest-info-grid">
                  <div className="info-item">
                    <label>Full Name</label>
                    <span>{booking.guest_name}</span>
                  </div>
                  <div className="info-item">
                    <label>Email</label>
                    <span>{booking.guest_email}</span>
                  </div>
                  <div className="info-item">
                    <label>Phone</label>
                    <span>{booking.guest_phone || 'Not provided'}</span>
                  </div>
                  <div className="info-item">
                    <label>Confirmation Number</label>
                    <span className="confirmation-number">{booking.confirmation_number}</span>
                  </div>
                </div>
              </div>

              {/* Stay Information */}
              <div className="detail-section">
                <h3>Stay Information</h3>
                <div className="stay-info-grid">
                  <div className="info-item">
                    <label>Check-in</label>
                    <span className="date">{booking.booking_summary.check_in_formatted}</span>
                  </div>
                  <div className="info-item">
                    <label>Check-out</label>
                    <span className="date">{booking.booking_summary.check_out_formatted}</span>
                  </div>
                  <div className="info-item">
                    <label>Duration</label>
                    <span>{booking.booking_summary.stay_duration}</span>
                  </div>
                  <div className="info-item">
                    <label>Adults</label>
                    <span>{booking.adults}</span>
                  </div>
                  <div className="info-item">
                    <label>Children</label>
                    <span>{booking.children}</span>
                  </div>
                </div>
              </div>

              {/* Payment Information */}
              <div className="detail-section">
                <h3>Payment Information</h3>
                <div className="payment-info-grid">
                  <div className="info-item">
                    <label>Total Amount</label>
                    <span className="total-amount">{booking.booking_summary.total_formatted}</span>
                  </div>
                  <div className="info-item">
                    <label>Payment Status</label>
                    <span className={`payment-status ${booking.paid_at ? 'paid' : 'pending'}`}>
                      {booking.booking_summary.payment_status}
                    </span>
                  </div>
                  {booking.payment_reference && (
                    <div className="info-item">
                      <label>Payment Reference</label>
                      <span>{booking.payment_reference}</span>
                    </div>
                  )}
                  {booking.promo_code && (
                    <div className="info-item">
                      <label>Promo Code</label>
                      <span className="promo-code">{booking.promo_code}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Booking Timeline */}
              <div className="detail-section">
                <h3>Booking Timeline</h3>
                <div className="timeline">
                  <div className="timeline-item">
                    <div className="timeline-marker created"></div>
                    <div className="timeline-content">
                      <strong>Booking Created</strong>
                      <span>{booking.booking_summary.created_formatted}</span>
                    </div>
                  </div>
                  
                  {booking.paid_at && (
                    <div className="timeline-item">
                      <div className="timeline-marker paid"></div>
                      <div className="timeline-content">
                        <strong>Payment Received</strong>
                        <span>{new Date(booking.paid_at).toLocaleString()}</span>
                      </div>
                    </div>
                  )}
                  
                  {booking.status === 'CONFIRMED' && (
                    <div className="timeline-item">
                      <div className="timeline-marker confirmed"></div>
                      <div className="timeline-content">
                        <strong>Booking Confirmed</strong>
                        <span>Confirmed by staff</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Cancellation Details (if cancelled) */}
              {booking.status === 'CANCELLED' && booking.cancellation_details && (
                <div className="detail-section cancellation-section">
                  <h3>Cancellation Details</h3>
                  <div className="cancellation-info">
                    <div className="info-item">
                      <label>Cancelled Date</label>
                      <span>{booking.cancellation_details.cancelled_date}</span>
                    </div>
                    <div className="info-item">
                      <label>Cancelled By</label>
                      <span>{booking.cancellation_details.cancelled_by}</span>
                    </div>
                    <div className="info-item">
                      <label>Cancellation Reason</label>
                      <span className="cancellation-reason">
                        {booking.cancellation_details.cancellation_reason}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Special Requests */}
              {booking.special_requests && (
                <div className="detail-section full-width">
                  <h3>Special Requests & Notes</h3>
                  <div className="special-requests">
                    <pre>{booking.special_requests}</pre>
                  </div>
                </div>
              )}

              {/* Internal Notes */}
              {booking.internal_notes && (
                <div className="detail-section full-width">
                  <h3>Internal Notes</h3>
                  <div className="internal-notes">
                    <pre>{booking.internal_notes}</pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BookingDetailModal;
```

## CSS Styles for Full-Screen Modal

```css
/* BookingDetailModal.css */
.booking-detail-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.booking-detail-modal {
  background: white;
  width: 100vw;
  height: 100vh;
  max-width: none;
  max-height: none;
  border-radius: 0;
  display: flex;
  flex-direction: column;
  position: relative;
}

.modal-header {
  padding: 20px 30px;
  border-bottom: 2px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
  flex-shrink: 0;
}

.header-left h2 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 28px;
}

.booking-id-header {
  display: flex;
  align-items: center;
  gap: 15px;
}

.booking-id {
  font-family: monospace;
  font-size: 16px;
  font-weight: bold;
  color: #666;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  color: white;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
}

.header-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover {
  background: #218838;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 50%;
  transition: background 0.2s;
}

.btn-close:hover {
  background: #eee;
}

.modal-content {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
}

.booking-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.detail-section {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.detail-section.full-width {
  grid-column: 1 / -1;
}

.detail-section.cancellation-section {
  border-left: 4px solid #dc3545;
  background: #fff5f5;
}

.detail-section h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 20px;
  border-bottom: 2px solid #f0f0f0;
  padding-bottom: 10px;
}

.room-info {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.room-photo {
  width: 120px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}

.room-details h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 18px;
}

.room-description {
  color: #666;
  margin: 0 0 15px 0;
  line-height: 1.5;
}

.occupancy {
  color: #333;
  font-size: 14px;
}

.guest-info-grid,
.stay-info-grid,
.payment-info-grid,
.cancellation-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.info-item label {
  font-weight: 600;
  color: #666;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-item span {
  font-size: 16px;
  color: #333;
}

.date {
  font-weight: 500;
}

.total-amount {
  font-size: 24px;
  font-weight: bold;
  color: #28a745;
}

.confirmation-number {
  font-family: monospace;
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #dee2e6;
}

.payment-status.paid {
  color: #28a745;
  font-weight: bold;
}

.payment-status.pending {
  color: #ffc107;
  font-weight: bold;
}

.promo-code {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: bold;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.timeline-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.timeline-marker {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}

.timeline-marker.created {
  background: #17a2b8;
}

.timeline-marker.paid {
  background: #28a745;
}

.timeline-marker.confirmed {
  background: #28a745;
}

.timeline-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.timeline-content strong {
  color: #333;
  font-size: 16px;
}

.timeline-content span {
  color: #666;
  font-size: 14px;
}

.cancellation-reason {
  background: #f8d7da;
  padding: 10px;
  border-radius: 6px;
  border-left: 4px solid #dc3545;
  font-style: italic;
}

.special-requests,
.internal-notes {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 15px;
  max-height: 200px;
  overflow-y: auto;
}

.special-requests pre,
.internal-notes pre {
  margin: 0;
  font-family: inherit;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.5;
}

.loading,
.error {
  text-align: center;
  padding: 50px;
  font-size: 18px;
}

.error {
  color: #dc3545;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .booking-details-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-content {
    padding: 20px;
  }
}

@media (max-width: 768px) {
  .modal-header {
    padding: 15px 20px;
  }
  
  .header-left h2 {
    font-size: 24px;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 10px;
  }
  
  .booking-detail-overlay {
    padding: 0;
  }
  
  .room-info {
    flex-direction: column;
  }
  
  .guest-info-grid,
  .stay-info-grid,
  .payment-info-grid {
    grid-template-columns: 1fr;
  }
}
```

## Integration with Booking Table

```javascript
// Update BookingTable.jsx to include detail modal
const [selectedBookingId, setSelectedBookingId] = useState(null);
const [showDetailModal, setShowDetailModal] = useState(false);

const openBookingDetail = (bookingId) => {
  setSelectedBookingId(bookingId);
  setShowDetailModal(true);
};

// Add click handler to booking row
<tr key={booking.id} onClick={() => openBookingDetail(booking.booking_id)} className="booking-row">
  {/* existing row content */}
</tr>

// Add modal to render
{showDetailModal && (
  <BookingDetailModal
    bookingId={selectedBookingId}
    isOpen={showDetailModal}
    onClose={() => setShowDetailModal(false)}
    onUpdate={onUpdate}
  />
)}
```

## API Endpoints

- **GET** `/api/staff/hotel/hotel-killarney/bookings/{booking_id}/` - Get detailed booking info
- **POST** `/api/staff/hotel/hotel-killarney/bookings/{booking_id}/confirm/` - Confirm booking  
- **POST** `/api/staff/hotel/hotel-killarney/bookings/{booking_id}/cancel/` - Cancel with reason

## Data Structure

The enhanced API now provides:

```json
{
  "booking_summary": {
    "stay_duration": "1 night",
    "check_in_formatted": "November 28, 2025", 
    "check_out_formatted": "November 29, 2025",
    "guest_count": "2 adults",
    "payment_status": "Pending",
    "total_formatted": "EUR 163.50",
    "created_formatted": "November 28, 2025 at 08:04 AM"
  },
  "cancellation_details": {
    "cancelled_date": "2025-11-28 14:30:25",
    "cancelled_by": "John Smith", 
    "cancellation_reason": "Guest requested cancellation due to emergency"
  },
  "room_photo_url": "https://cloudinary.../room_photo.jpg"
}
```

✅ **Full-screen modal** - No scrolling issues, all data visible at once
✅ **Real cancellation data** - Parsed from special_requests with date, staff name, reason  
✅ **Enhanced UI** - Professional layout with proper sections
✅ **Complete booking info** - Guest, room, payment, timeline, notes
✅ **Action buttons** - Confirm/cancel directly from modal
✅ **Responsive design** - Works on all screen sizes