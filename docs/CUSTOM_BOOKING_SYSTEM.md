# Custom Booking System - Architecture & Implementation

## Overview
HotelMate will have its own **custom booking system** built into the platform. Guests will book rooms directly through the HotelMate interface, not through external booking engines.

---

## System Components

### 1. **Booking Options (Database Configuration)**
Each hotel has booking configuration stored in the `BookingOptions` model:

```python
# Already in database
class BookingOptions(models.Model):
    hotel = OneToOneField(Hotel)
    primary_cta_label = "Book Now"           # Button text
    primary_cta_url = ""                      # NOT USED - we build our own
    secondary_cta_label = "Call to Book"     # Phone CTA text
    secondary_cta_phone = "+353 64 663 1555" # Hotel phone
    terms_url = "https://hotel.ie/terms"     # Terms & conditions
    policies_url = "https://hotel.ie/policies" # Booking policies
```

**Note**: `primary_cta_url` is in the database but **will NOT be used**. Instead, the frontend will route to our custom booking flow.

---

## Booking Flow Architecture

### Phase 1: Availability Check
**Endpoint**: `GET /api/hotels/<slug>/availability/`

**Purpose**: Check which room types are available for specific dates

**Frontend Flow**:
```
User enters dates → API checks availability → Show available rooms
```

**Request**:
```json
GET /api/hotels/killarney/availability/?check_in=2025-12-20&check_out=2025-12-22&adults=2&children=0
```

**Response**:
```json
{
  "hotel": "killarney",
  "check_in": "2025-12-20",
  "check_out": "2025-12-22",
  "nights": 2,
  "available_rooms": [
    {
      "room_type_code": "DLX-KING",
      "room_type_name": "Deluxe King Room",
      "is_available": true,
      "available_units": 3,
      "photo": "https://res.cloudinary.com/.../room.jpg",
      "max_occupancy": 2,
      "note": "Last 3 rooms remaining"
    },
    {
      "room_type_code": "SUP-SUITE",
      "room_type_name": "Superior Suite",
      "is_available": true,
      "available_units": 5,
      "photo": "https://res.cloudinary.com/.../suite.jpg",
      "max_occupancy": 4,
      "note": null
    }
  ]
}
```

---

### Phase 2: Pricing Quote
**Endpoint**: `POST /api/hotels/<slug>/pricing/quote/`

**Purpose**: Calculate exact price for selected room and dates

**Frontend Flow**:
```
User selects room → API calculates price → Show total breakdown
```

**Request**:
```json
POST /api/hotels/killarney/pricing/quote/
{
  "room_type_code": "DLX-KING",
  "check_in": "2025-12-20",
  "check_out": "2025-12-22",
  "adults": 2,
  "children": 0,
  "promo_code": "WINTER20"  // optional
}
```

**Response**:
```json
{
  "quote_id": "QT-2025-001234",
  "valid_until": "2025-11-23T16:30:00Z",
  "currency": "EUR",
  "breakdown": {
    "base_price_per_night": "150.00",
    "number_of_nights": 2,
    "subtotal": "300.00",
    "taxes": "27.00",
    "fees": "0.00",
    "discount": "-60.00",  // from WINTER20 promo
    "total": "267.00"
  },
  "applied_promo": {
    "code": "WINTER20",
    "description": "20% off winter bookings",
    "discount_percentage": "20.00"
  }
}
```

---

### Phase 3: Create Booking
**Endpoint**: `POST /api/hotels/<slug>/bookings/`

**Purpose**: Create reservation record in system

**Frontend Flow**:
```
User fills guest info → API creates booking → Returns booking ID → Redirect to payment
```

**Request**:
```json
POST /api/hotels/killarney/bookings/
{
  "quote_id": "QT-2025-001234",
  "room_type_code": "DLX-KING",
  "check_in": "2025-12-20",
  "check_out": "2025-12-22",
  "adults": 2,
  "children": 0,
  "guest": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+353 87 123 4567"
  },
  "special_requests": "Late check-in after 10pm",
  "promo_code": "WINTER20"
}
```

**Response**:
```json
{
  "booking_id": "BK-2025-5678",
  "confirmation_number": "KIL-2025-5678",
  "status": "PENDING_PAYMENT",
  "hotel": {
    "name": "Hotel Killarney",
    "slug": "killarney"
  },
  "room": {
    "type": "Deluxe King Room",
    "code": "DLX-KING"
  },
  "dates": {
    "check_in": "2025-12-20",
    "check_out": "2025-12-22",
    "nights": 2
  },
  "guest": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+353 87 123 4567"
  },
  "pricing": {
    "total": "267.00",
    "currency": "EUR"
  },
  "created_at": "2025-11-23T15:45:00Z",
  "payment_required": true,
  "payment_url": "/api/bookings/BK-2025-5678/payment/session/"
}
```

---

### Phase 4: Payment Processing
**Endpoint**: `POST /api/bookings/<booking_id>/payment/session/`

**Purpose**: Create Stripe/PayPal payment session

**Frontend Flow**:
```
Booking created → Create payment session → Redirect to Stripe → Webhook confirms → Send email
```

**Request**:
```json
POST /api/bookings/BK-2025-5678/payment/session/
{
  "payment_method": "stripe",  // or "paypal"
  "success_url": "https://hotelkillarney.ie/booking/success",
  "cancel_url": "https://hotelkillarney.ie/booking/cancel"
}
```

**Response**:
```json
{
  "session_id": "cs_test_a1b2c3d4e5f6",
  "payment_url": "https://checkout.stripe.com/pay/cs_test_a1b2c3d4e5f6",
  "expires_at": "2025-11-23T16:45:00Z"
}
```

**Payment Webhook**:
```
Stripe/PayPal sends webhook → Backend verifies → Updates booking to CONFIRMED → Triggers email
```

---

### Phase 5: Confirmation Email
**Automatic trigger after payment success**

**Email Content**:
- Booking confirmation number
- Hotel details
- Room type
- Check-in/check-out dates
- Guest information
- Total paid
- Cancellation policy link
- Contact information

---

## Frontend Integration

### Complete Booking Flow Component

```jsx
import { useState } from 'react';

function BookingFlow({ hotelSlug }) {
  const [step, setStep] = useState(1);
  const [availability, setAvailability] = useState(null);
  const [quote, setQuote] = useState(null);
  const [booking, setBooking] = useState(null);
  const [dates, setDates] = useState({ checkIn: '', checkOut: '' });
  const [guests, setGuests] = useState({ adults: 2, children: 0 });
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [guestInfo, setGuestInfo] = useState({});

  // Step 1: Check Availability
  const checkAvailability = async () => {
    const response = await fetch(
      `/api/hotels/${hotelSlug}/availability/?` +
      `check_in=${dates.checkIn}&check_out=${dates.checkOut}&` +
      `adults=${guests.adults}&children=${guests.children}`
    );
    const data = await response.json();
    setAvailability(data);
    setStep(2);
  };

  // Step 2: Get Price Quote
  const getPriceQuote = async (roomCode) => {
    const response = await fetch(
      `/api/hotels/${hotelSlug}/pricing/quote/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_type_code: roomCode,
          check_in: dates.checkIn,
          check_out: dates.checkOut,
          adults: guests.adults,
          children: guests.children
        })
      }
    );
    const data = await response.json();
    setQuote(data);
    setSelectedRoom(roomCode);
    setStep(3);
  };

  // Step 3: Create Booking
  const createBooking = async () => {
    const response = await fetch(
      `/api/hotels/${hotelSlug}/bookings/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quote_id: quote.quote_id,
          room_type_code: selectedRoom,
          check_in: dates.checkIn,
          check_out: dates.checkOut,
          adults: guests.adults,
          children: guests.children,
          guest: guestInfo
        })
      }
    );
    const data = await response.json();
    setBooking(data);
    setStep(4);
  };

  // Step 4: Process Payment
  const initiatePayment = async () => {
    const response = await fetch(
      `/api/bookings/${booking.booking_id}/payment/session/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          payment_method: 'stripe',
          success_url: `${window.location.origin}/booking/success`,
          cancel_url: `${window.location.origin}/booking/cancel`
        })
      }
    );
    const data = await response.json();
    
    // Redirect to Stripe
    window.location.href = data.payment_url;
  };

  return (
    <div className="booking-flow">
      {step === 1 && (
        <DateSelector 
          onSubmit={checkAvailability}
          dates={dates}
          setDates={setDates}
          guests={guests}
          setGuests={setGuests}
        />
      )}
      
      {step === 2 && (
        <RoomSelector 
          rooms={availability.available_rooms}
          onSelect={getPriceQuote}
        />
      )}
      
      {step === 3 && (
        <GuestInfoForm 
          quote={quote}
          guestInfo={guestInfo}
          setGuestInfo={setGuestInfo}
          onSubmit={createBooking}
        />
      )}
      
      {step === 4 && (
        <PaymentButton 
          booking={booking}
          onClick={initiatePayment}
        />
      )}
    </div>
  );
}
```

---

## Booking Options Integration

### Fetching Booking Options

The booking options are included in the hotel home endpoint:

```javascript
// Get hotel data with booking options
const response = await fetch(`/api/guest/hotels/${hotelSlug}/site/home/`);
const data = await response.json();

const bookingOptions = data.hotel.booking_options;
// {
//   primary_cta_label: "Book Now",
//   secondary_cta_label: "Call to Book",
//   secondary_cta_phone: "+353 64 663 1555",
//   terms_url: "https://hotelkillarney.ie/terms",
//   policies_url: "https://hotelkillarney.ie/policies"
// }
```

### Using Booking Options in UI

```jsx
function HotelBookingSection({ hotelSlug, bookingOptions }) {
  const navigate = useNavigate();

  return (
    <div className="booking-section">
      {/* Primary CTA - Opens custom booking flow */}
      <button 
        className="btn-primary"
        onClick={() => navigate(`/hotels/${hotelSlug}/book`)}
      >
        {bookingOptions?.primary_cta_label || 'Book Now'}
      </button>

      {/* Secondary CTA - Call to book */}
      {bookingOptions?.secondary_cta_phone && (
        <a 
          href={`tel:${bookingOptions.secondary_cta_phone}`}
          className="btn-secondary"
        >
          {bookingOptions?.secondary_cta_label || 'Call Us'}
        </a>
      )}

      {/* Terms & Policies */}
      <div className="booking-links">
        {bookingOptions?.terms_url && (
          <a href={bookingOptions.terms_url} target="_blank" rel="noopener">
            Terms & Conditions
          </a>
        )}
        {bookingOptions?.policies_url && (
          <a href={bookingOptions.policies_url} target="_blank" rel="noopener">
            Booking Policies
          </a>
        )}
      </div>
    </div>
  );
}
```

---

## Database Models

### Booking Model (To Be Created)

```python
class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    
    booking_id = models.CharField(max_length=50, unique=True)
    confirmation_number = models.CharField(max_length=50, unique=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT)
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT)
    
    # Dates
    check_in = models.DateField()
    check_out = models.DateField()
    
    # Guest info
    guest_first_name = models.CharField(max_length=100)
    guest_last_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=30)
    
    # Occupancy
    adults = models.IntegerField()
    children = models.IntegerField(default=0)
    
    # Pricing
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Optional
    special_requests = models.TextField(blank=True)
    promo_code = models.CharField(max_length=50, blank=True)
    
    # Payment info
    payment_reference = models.CharField(max_length=200, blank=True)
    payment_provider = models.CharField(max_length=50, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## Implementation Roadmap

### ✅ Completed
- BookingOptions model in database
- Guest API endpoints for hotel data
- Image integration with Cloudinary

### 📋 Phase 1 (Current Sprint)
- [ ] Issue #20: Availability Checker API
- [ ] Issue #21: Real-Time Pricing API
- [ ] Issue #22: Booking Creation Endpoint
- [ ] Issue #23: Payment Processing Integration
- [ ] Issue #24: Email Confirmation System

### 🔮 Phase 2 (Future)
- Booking management dashboard (for guests)
- Cancellation/modification system
- Hotel admin booking management
- Reporting and analytics
- Multi-room bookings
- Package deals integration

---

## Key Differences from External Booking

| Aspect | External Booking | Custom System |
|--------|------------------|---------------|
| **URL** | Redirects to external site | Stays on HotelMate |
| **Data** | Lives in external PMS | Lives in HotelMate DB |
| **Branding** | Third-party branding | Full HotelMate branding |
| **Control** | Limited customization | Full control |
| **Commission** | Pay per booking | No commission fees |
| **Integration** | API limitations | Direct database access |

---

## Security Considerations

1. **Payment**: Never store credit card details directly
2. **Webhooks**: Verify all payment provider signatures
3. **Guest Data**: GDPR compliance for EU guests
4. **Rate Limiting**: Prevent booking spam/DOS
5. **Validation**: Server-side validation of all inputs
6. **HTTPS**: All booking endpoints must use HTTPS in production

---

## Testing Strategy

### Unit Tests
- Availability logic
- Pricing calculations
- Booking creation validation

### Integration Tests
- End-to-end booking flow
- Payment webhook handling
- Email delivery

### Manual Testing
- UI/UX flow testing
- Payment provider sandbox
- Email template review

---

## Support & Troubleshooting

**Issue**: Booking created but payment fails
**Solution**: Booking remains in PENDING_PAYMENT. Guest can retry payment or booking expires after 30 minutes.

**Issue**: Double booking
**Solution**: Availability check + database constraints prevent overbooking.

**Issue**: Email not received
**Solution**: Check spam folder, verify email service configuration, check retry queue.

---

**Related Issues**: #20, #21, #22, #23, #24
**Repository**: [HotelMateBackend](https://github.com/nlekkerman/HotelMateBackend)
