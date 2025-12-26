# Frontend Guest Cancellation Integration Guide

**Updated:** December 26, 2025  
**Status:** Implementation Complete  
**API Version:** Latest with Stripe-safe cancellation

## Overview

The guest cancellation system has been enhanced with **Stripe-safe financial operations**, **idempotency protection**, and **expanded cancellation eligibility**. This guide covers frontend integration requirements.

---

## Key Changes for Frontend

### ✅ **Expanded Cancellation Eligibility**
**IMPORTANT:** Bookings with status `PENDING_APPROVAL` can now be cancelled!

**Previous:** Only `CONFIRMED` and `PENDING_PAYMENT` bookings could be cancelled  
**New:** `CONFIRMED`, `PENDING_PAYMENT`, and `PENDING_APPROVAL` bookings can be cancelled

```javascript
// Updated cancellation eligibility check
const canCancel = [
  'CONFIRMED', 
  'PENDING_PAYMENT', 
  'PENDING_APPROVAL'  // ← NEW: Now cancellable!
].includes(booking.status) && !booking.cancelled_at;
```

### ✅ **Enhanced API Response**
All booking GET endpoints now include:
```json
{
  "booking": {
    "status": "PENDING_APPROVAL",
    "cancelled_at": null
  },
  "can_cancel": true,           // ← Frontend should use this
  "cancellation_preview": {     // ← Fee calculation preview
    "fee_amount": "0.00",
    "refund_amount": "130.80", 
    "description": "Free cancellation available"
  }
}
```

---

## API Endpoints

### 1. **Get Booking Status (Updated)**
```http
GET /api/public/hotels/{hotel_slug}/booking/status/{booking_id}/?token={token}
```

**Response Structure:**
```json
{
  "booking": {
    "id": "BK-2025-0001",
    "status": "PENDING_APPROVAL",
    "total_amount": "130.80",
    "currency": "EUR",
    "cancelled_at": null
  },
  "hotel": {
    "name": "Hotel Killarney",
    "slug": "hotel-killarney"
  },
  "can_cancel": true,                    // ← Use this for UI logic
  "cancellation_preview": {              // ← Show fee breakdown  
    "fee_amount": "0.00",
    "refund_amount": "130.80",
    "description": "Free cancellation until 2 hours before check-in",
    "applied_rule": "HOURS_BEFORE_CHECKIN"
  }
}
```

### 2. **Cancel Booking (Enhanced)**
```http
POST /api/public/hotels/{hotel_slug}/booking/status/{booking_id}/
```

**Request Body:**
```json
{
  "token": "abc123def456...",
  "reason": "Change of plans"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Your booking has been successfully cancelled.",
  "cancellation": {
    "cancelled_at": "2025-12-26T15:30:00Z",
    "cancellation_fee": "0.00",
    "refund_amount": "130.80",
    "description": "Free cancellation - full refund",
    "refund_reference": "re_1ABC123def456"    // ← Stripe refund ID (if applicable)
  }
}
```

**Error Responses:**
- `400` - Business logic error (booking can't be cancelled)
- `401` - Missing token
- `403` - Invalid/expired token  
- `502` - Payment processing failed (contact hotel)

---

## Frontend Implementation

### **1. Cancellation Button Logic**

```javascript
// ✅ UPDATED: Use API-provided can_cancel field
function shouldShowCancelButton(bookingResponse) {
  // Always trust the API's can_cancel field
  return bookingResponse.can_cancel === true;
}

// ❌ OLD: Don't rely on frontend status checks  
// const canCancel = ['CONFIRMED', 'PENDING_PAYMENT'].includes(booking.status);
```

### **2. Cancellation Preview Display**

```javascript
// Show cancellation fees before user confirms
function displayCancellationPreview(cancellationPreview) {
  if (!cancellationPreview) return null;
  
  return (
    <div className="cancellation-preview">
      <h3>Cancellation Summary</h3>
      <div className="fee-breakdown">
        <div>Cancellation Fee: {cancellationPreview.fee_amount} EUR</div>
        <div>Refund Amount: {cancellationPreview.refund_amount} EUR</div>
        <div className="description">{cancellationPreview.description}</div>
      </div>
    </div>
  );
}
```

### **3. Enhanced Error Handling**

```javascript
async function cancelBooking(hotelSlug, bookingId, token, reason) {
  try {
    const response = await fetch(
      `/api/public/hotels/${hotelSlug}/booking/status/${bookingId}/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, reason })
      }
    );
    
    const data = await response.json();
    
    if (response.ok) {
      // ✅ Success - booking cancelled
      return {
        success: true,
        cancellation: data.cancellation
      };
    }
    
    // Handle specific error cases
    switch (response.status) {
      case 400:
        return { 
          success: false, 
          error: data.error || 'This booking cannot be cancelled' 
        };
      case 401:
        return { 
          success: false, 
          error: 'Invalid access link. Please check your email for the correct link.' 
        };
      case 403:
        return { 
          success: false, 
          error: 'This cancellation link has expired or been used.' 
        };
      case 502:
        return { 
          success: false, 
          error: 'Payment processing failed. Please contact the hotel directly.' 
        };
      default:
        return { 
          success: false, 
          error: 'Unable to cancel booking. Please contact the hotel.' 
        };
    }
  } catch (error) {
    return { 
      success: false, 
      error: 'Network error. Please check your connection and try again.' 
    };
  }
}
```

---

## Token Support

The cancellation endpoint accepts tokens from **both** locations:

### **Option 1: Request Body (Recommended)**
```json
{
  "token": "abc123def456...",
  "reason": "Change of plans"  
}
```

### **Option 2: Query Parameter**
```http
POST /api/public/hotels/hotel-killarney/booking/status/BK-2025-0001/?token=abc123def456
Content-Type: application/json

{
  "reason": "Change of plans"
}
```

---

## Financial Safety Features

### **Automatic Payment Processing**
The system automatically handles payment refunds/voids:

- **PENDING_APPROVAL** → Voids Stripe authorization (no refund object)
- **CONFIRMED** → Creates Stripe refund with proper amount
- **Non-Stripe** → Database-only cancellation

### **Idempotency Protection**
- Multiple cancellation attempts return success (no errors)
- No double-refunds or payment processing issues
- Safe for users to retry if unsure

### **Policy Compliance** 
- Always uses hotel's current cancellation policy
- Real-time fee calculations (never trust cached amounts)
- Supports all policy types automatically

---

## Testing Scenarios

### **Test Cases for Frontend**

1. **PENDING_APPROVAL Cancellation**
   - Status: `PENDING_APPROVAL`
   - Expected: Shows cancel button, processes successfully

2. **CONFIRMED Cancellation with Fee**
   - Status: `CONFIRMED` 
   - Expected: Shows fee breakdown, processes refund

3. **Already Cancelled Booking**
   - Status: `CANCELLED`
   - Expected: No cancel button, shows cancellation details

4. **Invalid Token**
   - Expected: 403 error, clear error message

5. **Payment Processing Error**
   - Expected: 502 error, instruction to contact hotel

---

## Migration Notes

### **Immediate Actions Required**

1. **Update Cancellation Logic**: Change status checks to use API's `can_cancel` field
2. **Add PENDING_APPROVAL Support**: Update UI to show cancel button for this status  
3. **Enhanced Error Handling**: Implement 502 error handling for payment failures
4. **Show Refund Reference**: Display Stripe refund ID when available

### **Backward Compatibility**
- All existing cancellation flows continue to work
- Response format is enhanced (no breaking changes)
- Token validation behavior unchanged

---

## Example Integration

```javascript
// Complete booking cancellation flow
async function handleBookingCancellation(booking, token) {
  // 1. Check if cancellation is allowed (trust API)
  if (!booking.can_cancel) {
    alert('This booking cannot be cancelled');
    return;
  }
  
  // 2. Show preview to user
  const preview = booking.cancellation_preview;
  const confirmed = confirm(`
    Cancellation Fee: ${preview.fee_amount} EUR
    Refund Amount: ${preview.refund_amount} EUR
    
    Are you sure you want to cancel?
  `);
  
  if (!confirmed) return;
  
  // 3. Process cancellation
  const result = await cancelBooking(
    booking.hotel.slug, 
    booking.id, 
    token,
    'Guest requested cancellation'
  );
  
  // 4. Handle result
  if (result.success) {
    alert(`Booking cancelled successfully! 
           Refund: ${result.cancellation.refund_amount} EUR`);
    // Refresh booking data or redirect
  } else {
    alert(result.error);
  }
}
```

This guide ensures your frontend properly integrates with the new financially-safe cancellation system! 🎉