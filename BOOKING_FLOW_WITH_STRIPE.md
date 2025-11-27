# Room Booking Flow with Stripe Integration

## Overview
Complete guide for implementing the room booking flow from the public hotel page through Stripe payment integration.

---

## 🎯 User Journey

1. **User views hotel public page** → Sees rooms section
2. **Clicks "Book Now"** on a room card → Redirects to booking wizard
3. **Selects dates & guests** → Checks availability
4. **Reviews pricing** → Gets quote with breakdown
5. **Enters guest details** → Prepares booking
6. **Proceeds to payment** → Creates Stripe checkout session
7. **Completes payment** → Booking confirmed

---

## 📍 Backend API Endpoints (Already Implemented)

### 1. Check Room Availability
**Endpoint:** `GET /api/hotel/{slug}/availability/`

**Query Parameters:**
```javascript
{
  check_in: "2025-12-01",      // YYYY-MM-DD
  check_out: "2025-12-03",     // YYYY-MM-DD
  adults: 2,
  children: 0
}
```

**Response:**
```json
{
  "available_rooms": [
    {
      "id": 1,
      "code": "DLX-KING",
      "name": "Deluxe King Room",
      "max_occupancy": 2,
      "bed_setup": "1 King Bed",
      "photo_url": "https://...",
      "base_rate": "129.00",
      "currency": "EUR",
      "is_available": true
    }
  ],
  "check_in": "2025-12-01",
  "check_out": "2025-12-03",
  "nights": 2,
  "adults": 2,
  "children": 0
}
```

---

### 2. Get Pricing Quote
**Endpoint:** `POST /api/hotel/{slug}/pricing/quote/`

**Request Body:**
```json
{
  "room_type_code": "DLX-KING",
  "check_in": "2025-12-01",
  "check_out": "2025-12-03",
  "adults": 2,
  "children": 0,
  "promo_code": "WINTER20"  // Optional
}
```

**Response:**
```json
{
  "quote_id": "QT-ABC123",
  "hotel": {
    "id": 2,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney"
  },
  "room_type": {
    "id": 1,
    "code": "DLX-KING",
    "name": "Deluxe King Room"
  },
  "check_in": "2025-12-01",
  "check_out": "2025-12-03",
  "nights": 2,
  "adults": 2,
  "children": 0,
  "nightly_rates": [
    {
      "date": "2025-12-01",
      "rate": "129.00",
      "currency": "EUR"
    },
    {
      "date": "2025-12-02",
      "rate": "129.00",
      "currency": "EUR"
    }
  ],
  "subtotal": "258.00",
  "promo_code": "WINTER20",
  "promo_discount": "51.60",
  "subtotal_after_promo": "206.40",
  "vat_rate": "0.09",
  "vat_amount": "18.58",
  "total_amount_incl_taxes": "225.00",
  "currency": "EUR",
  "valid_until": "2025-11-27T17:00:00Z",
  "created_at": "2025-11-27T16:30:00Z"
}
```

---

### 3. Create Booking
**Endpoint:** `POST /api/hotel/{slug}/bookings/`

**Request Body:**
```json
{
  "quote_id": "QT-ABC123",
  "room_type_code": "DLX-KING",
  "check_in": "2025-12-01",
  "check_out": "2025-12-03",
  "adults": 2,
  "children": 0,
  "guest": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+353871234567"
  },
  "promo_code": "WINTER20",
  "special_requests": "Late check-in please"
}
```

**Response:**
```json
{
  "booking_id": "BK-KIL-20251201-001",
  "confirmation_number": "CONF-ABC123",
  "status": "PENDING_PAYMENT",
  "hotel": {
    "id": 2,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney"
  },
  "room_type": {
    "id": 1,
    "code": "DLX-KING",
    "name": "Deluxe King Room"
  },
  "check_in": "2025-12-01",
  "check_out": "2025-12-03",
  "nights": 2,
  "adults": 2,
  "children": 0,
  "guest": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+353871234567"
  },
  "pricing": {
    "subtotal": "258.00",
    "promo_discount": "51.60",
    "vat_amount": "18.58",
    "total_amount": "225.00",
    "currency": "EUR"
  },
  "special_requests": "Late check-in please",
  "created_at": "2025-11-27T16:35:00Z"
}
```

---

### 4. Create Stripe Payment Session
**Endpoint:** `POST /api/hotel/{slug}/bookings/{booking_id}/payment/`

**Request Body:**
```json
{
  "success_url": "https://yourfrontend.com/booking/success?session_id={CHECKOUT_SESSION_ID}",
  "cancel_url": "https://yourfrontend.com/booking/cancelled"
}
```

**Response:**
```json
{
  "session_id": "cs_test_a1b2c3d4e5f6...",
  "session_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "booking_id": "BK-KIL-20251201-001",
  "amount": "225.00",
  "currency": "EUR"
}
```

**Redirect user to:** `session_url` for Stripe checkout

---

### 5. Verify Payment (After Stripe Redirect)
**Endpoint:** `GET /api/hotel/{slug}/bookings/{booking_id}/verify-payment/?session_id={session_id}`

**Response:**
```json
{
  "booking_id": "BK-KIL-20251201-001",
  "status": "CONFIRMED",
  "payment_status": "PAID",
  "confirmation_number": "CONF-ABC123",
  "message": "Booking confirmed successfully"
}
```

---

## 🎨 Frontend Implementation

### Step 1: Room Card with Booking CTA

```jsx
// components/RoomsSection.jsx
import { useNavigate } from 'react-router-dom';

const RoomCard = ({ roomType, hotelSlug }) => {
  const navigate = useNavigate();

  const handleBookNow = () => {
    // Redirect to booking wizard with pre-selected room
    navigate(`/booking/${hotelSlug}`, {
      state: {
        roomTypeCode: roomType.code,
        roomTypeName: roomType.name,
        roomTypeId: roomType.id,
        startingPrice: roomType.starting_price_from
      }
    });
  };

  return (
    <div className="room-card">
      <img src={roomType.photo} alt={roomType.name} />
      <h3>{roomType.name}</h3>
      <p>{roomType.short_description}</p>
      <div className="pricing">
        <span>From €{roomType.starting_price_from}/night</span>
      </div>
      <button onClick={handleBookNow}>Book Now</button>
    </div>
  );
};
```

---

### Step 2: Booking Wizard Component

```jsx
// pages/BookingWizard.jsx
import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { 
  checkAvailability, 
  getPricingQuote, 
  createBooking, 
  createPaymentSession 
} from '../api/bookingApi';

const BookingWizard = () => {
  const { hotelSlug } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  // Pre-selected room from rooms section
  const preSelectedRoom = location.state;
  
  // Wizard steps
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Booking data
  const [dates, setDates] = useState({
    checkIn: '',
    checkOut: ''
  });
  const [guests, setGuests] = useState({
    adults: 2,
    children: 0
  });
  const [selectedRoom, setSelectedRoom] = useState(preSelectedRoom || null);
  const [availableRooms, setAvailableRooms] = useState([]);
  const [quote, setQuote] = useState(null);
  const [guestDetails, setGuestDetails] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: ''
  });
  const [promoCode, setPromoCode] = useState('');
  const [specialRequests, setSpecialRequests] = useState('');

  // Step 1: Date & Guest Selection
  const handleCheckAvailability = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await checkAvailability(hotelSlug, {
        check_in: dates.checkIn,
        check_out: dates.checkOut,
        adults: guests.adults,
        children: guests.children
      });
      setAvailableRooms(response.available_rooms);
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Room Selection & Get Quote
  const handleSelectRoom = async (room) => {
    setSelectedRoom(room);
    setLoading(true);
    try {
      const quoteResponse = await getPricingQuote(hotelSlug, {
        room_type_code: room.code,
        check_in: dates.checkIn,
        check_out: dates.checkOut,
        adults: guests.adults,
        children: guests.children,
        promo_code: promoCode || undefined
      });
      setQuote(quoteResponse);
      setStep(3);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Guest Details & Create Booking
  const handleCreateBooking = async () => {
    setLoading(true);
    setError(null);
    try {
      const bookingResponse = await createBooking(hotelSlug, {
        quote_id: quote.quote_id,
        room_type_code: selectedRoom.code,
        check_in: dates.checkIn,
        check_out: dates.checkOut,
        adults: guests.adults,
        children: guests.children,
        guest: guestDetails,
        promo_code: promoCode || undefined,
        special_requests: specialRequests
      });
      
      // Create Stripe payment session
      const paymentResponse = await createPaymentSession(
        hotelSlug, 
        bookingResponse.booking_id,
        {
          success_url: `${window.location.origin}/booking/success?session_id={CHECKOUT_SESSION_ID}`,
          cancel_url: `${window.location.origin}/booking/cancelled`
        }
      );
      
      // Redirect to Stripe
      window.location.href = paymentResponse.session_url;
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="booking-wizard">
      {/* Step indicator */}
      <div className="steps">
        <div className={step >= 1 ? 'active' : ''}>1. Dates & Guests</div>
        <div className={step >= 2 ? 'active' : ''}>2. Select Room</div>
        <div className={step >= 3 ? 'active' : ''}>3. Guest Details</div>
        <div className={step >= 4 ? 'active' : ''}>4. Payment</div>
      </div>

      {error && <div className="error">{error}</div>}

      {/* Step 1: Date & Guest Selection */}
      {step === 1 && (
        <div className="step-content">
          <h2>Select Dates & Guests</h2>
          <input 
            type="date" 
            value={dates.checkIn}
            onChange={(e) => setDates({...dates, checkIn: e.target.value})}
            min={new Date().toISOString().split('T')[0]}
          />
          <input 
            type="date" 
            value={dates.checkOut}
            onChange={(e) => setDates({...dates, checkOut: e.target.value})}
            min={dates.checkIn}
          />
          <div>
            <label>Adults:</label>
            <input 
              type="number" 
              min="1" 
              value={guests.adults}
              onChange={(e) => setGuests({...guests, adults: parseInt(e.target.value)})}
            />
          </div>
          <div>
            <label>Children:</label>
            <input 
              type="number" 
              min="0" 
              value={guests.children}
              onChange={(e) => setGuests({...guests, children: parseInt(e.target.value)})}
            />
          </div>
          <button 
            onClick={handleCheckAvailability}
            disabled={!dates.checkIn || !dates.checkOut || loading}
          >
            {loading ? 'Checking...' : 'Check Availability'}
          </button>
        </div>
      )}

      {/* Step 2: Room Selection */}
      {step === 2 && (
        <div className="step-content">
          <h2>Select Your Room</h2>
          <div className="available-rooms">
            {availableRooms.map(room => (
              <div key={room.id} className="room-option">
                <img src={room.photo_url} alt={room.name} />
                <h3>{room.name}</h3>
                <p>€{room.base_rate}/night</p>
                <button onClick={() => handleSelectRoom(room)}>
                  Select This Room
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step 3: Guest Details & Summary */}
      {step === 3 && quote && (
        <div className="step-content">
          <h2>Guest Details</h2>
          
          {/* Booking Summary */}
          <div className="summary">
            <h3>Booking Summary</h3>
            <p>{selectedRoom.name}</p>
            <p>{dates.checkIn} to {dates.checkOut} ({quote.nights} nights)</p>
            <p>{guests.adults} adults, {guests.children} children</p>
            <div className="pricing-breakdown">
              <p>Subtotal: €{quote.subtotal}</p>
              {quote.promo_discount > 0 && (
                <p>Discount: -€{quote.promo_discount}</p>
              )}
              <p>VAT (9%): €{quote.vat_amount}</p>
              <p><strong>Total: €{quote.total_amount_incl_taxes}</strong></p>
            </div>
          </div>

          {/* Guest Form */}
          <form onSubmit={(e) => { e.preventDefault(); handleCreateBooking(); }}>
            <input 
              type="text" 
              placeholder="First Name"
              value={guestDetails.firstName}
              onChange={(e) => setGuestDetails({...guestDetails, firstName: e.target.value})}
              required
            />
            <input 
              type="text" 
              placeholder="Last Name"
              value={guestDetails.lastName}
              onChange={(e) => setGuestDetails({...guestDetails, lastName: e.target.value})}
              required
            />
            <input 
              type="email" 
              placeholder="Email"
              value={guestDetails.email}
              onChange={(e) => setGuestDetails({...guestDetails, email: e.target.value})}
              required
            />
            <input 
              type="tel" 
              placeholder="Phone"
              value={guestDetails.phone}
              onChange={(e) => setGuestDetails({...guestDetails, phone: e.target.value})}
              required
            />
            <input 
              type="text" 
              placeholder="Promo Code (Optional)"
              value={promoCode}
              onChange={(e) => setPromoCode(e.target.value)}
            />
            <textarea 
              placeholder="Special Requests (Optional)"
              value={specialRequests}
              onChange={(e) => setSpecialRequests(e.target.value)}
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Processing...' : 'Proceed to Payment'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

export default BookingWizard;
```

---

### Step 3: API Service Functions

```javascript
// api/bookingApi.js
const API_BASE = '/api';

export const checkAvailability = async (hotelSlug, params) => {
  const queryString = new URLSearchParams(params).toString();
  const response = await fetch(
    `${API_BASE}/hotel/${hotelSlug}/availability/?${queryString}`
  );
  if (!response.ok) throw new Error('Failed to check availability');
  return await response.json();
};

export const getPricingQuote = async (hotelSlug, data) => {
  const response = await fetch(
    `${API_BASE}/hotel/${hotelSlug}/pricing/quote/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }
  );
  if (!response.ok) throw new Error('Failed to get pricing quote');
  return await response.json();
};

export const createBooking = async (hotelSlug, data) => {
  const response = await fetch(
    `${API_BASE}/hotel/${hotelSlug}/bookings/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }
  );
  if (!response.ok) throw new Error('Failed to create booking');
  return await response.json();
};

export const createPaymentSession = async (hotelSlug, bookingId, urls) => {
  const response = await fetch(
    `${API_BASE}/hotel/${hotelSlug}/bookings/${bookingId}/payment/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(urls)
    }
  );
  if (!response.ok) throw new Error('Failed to create payment session');
  return await response.json();
};

export const verifyPayment = async (hotelSlug, bookingId, sessionId) => {
  const response = await fetch(
    `${API_BASE}/hotel/${hotelSlug}/bookings/${bookingId}/verify-payment/?session_id=${sessionId}`
  );
  if (!response.ok) throw new Error('Failed to verify payment');
  return await response.json();
};
```

---

### Step 4: Success & Cancel Pages

```jsx
// pages/BookingSuccess.jsx
import { useEffect, useState } from 'react';
import { useSearchParams, useParams } from 'react-router-dom';
import { verifyPayment } from '../api/bookingApi';

const BookingSuccess = () => {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const bookingId = searchParams.get('booking_id'); // You'll need to pass this
  const { hotelSlug } = useParams();
  
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verify = async () => {
      try {
        const result = await verifyPayment(hotelSlug, bookingId, sessionId);
        setBooking(result);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    if (sessionId && bookingId) verify();
  }, [sessionId, bookingId, hotelSlug]);

  if (loading) return <div>Verifying payment...</div>;

  return (
    <div className="booking-success">
      <h1>✅ Booking Confirmed!</h1>
      <p>Confirmation Number: {booking?.confirmation_number}</p>
      <p>Booking ID: {booking?.booking_id}</p>
      <p>A confirmation email has been sent to your email address.</p>
    </div>
  );
};

export default BookingSuccess;
```

```jsx
// pages/BookingCancelled.jsx
const BookingCancelled = () => {
  return (
    <div className="booking-cancelled">
      <h1>Booking Cancelled</h1>
      <p>Your booking was not completed.</p>
      <p>No charges have been made to your card.</p>
      <a href="/">Return to Home</a>
    </div>
  );
};

export default BookingCancelled;
```

---

## 🔐 Stripe Webhook (Backend Already Configured)

The backend automatically handles Stripe webhooks at:
```
POST /api/hotel/stripe/webhook/
```

When payment succeeds, it:
1. Updates booking status to `CONFIRMED`
2. Marks payment as `PAID`
3. Sends confirmation email to guest
4. Notifies hotel staff

---

## ✅ Testing Checklist

### Frontend Testing:
1. ✅ Click "Book Now" from rooms section
2. ✅ Wizard opens with room pre-selected
3. ✅ Select dates and check availability
4. ✅ View available rooms and pricing
5. ✅ Enter guest details
6. ✅ Apply promo code (optional)
7. ✅ Redirect to Stripe checkout
8. ✅ Complete test payment
9. ✅ Return to success page
10. ✅ Verify booking confirmation

### Test Credit Cards (Stripe Test Mode):
- **Success:** 4242 4242 4242 4242
- **Decline:** 4000 0000 0000 0002
- **3D Secure:** 4000 0025 0000 3155

---

## 🚀 Quick Start

1. **Add routes to your frontend:**
```javascript
// App.jsx or routes config
<Route path="/booking/:hotelSlug" element={<BookingWizard />} />
<Route path="/booking/success" element={<BookingSuccess />} />
<Route path="/booking/cancelled" element={<BookingCancelled />} />
```

2. **Update rooms section component:**
```javascript
// Use the booking_cta_url from API or build it manually
<button onClick={() => navigate(roomType.booking_cta_url)}>
  Book Now
</button>
```

3. **Configure Stripe public key:**
```javascript
// .env
VITE_STRIPE_PUBLIC_KEY=pk_test_...
```

---

## 📝 Backend Notes

✅ All backend endpoints are **already implemented**  
✅ Stripe integration is **configured and working**  
✅ PMS services handle **availability, pricing, and inventory**  
✅ Webhooks automatically **confirm bookings**  
✅ Email notifications are **sent on confirmation**

**No backend changes needed** - just implement the frontend flow!
