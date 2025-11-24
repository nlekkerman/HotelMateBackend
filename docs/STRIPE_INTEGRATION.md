# Stripe Payment Integration Setup

## Environment Variables

Add these to your `.env` file:

```env
# Stripe API Keys (get from https://dashboard.stripe.com/apikeys)
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here

# Stripe Webhook Secret (get from https://dashboard.stripe.com/webhooks)
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

## Getting Stripe Keys

### 1. Create Stripe Account
- Go to https://stripe.com
- Sign up for a free account

### 2. Get API Keys
- Go to https://dashboard.stripe.com/apikeys
- Copy your **Secret key** (starts with `sk_test_`)
- Copy your **Publishable key** (starts with `pk_test_`)

### 3. Set Up Webhook
- Go to https://dashboard.stripe.com/webhooks
- Click "Add endpoint"
- Endpoint URL: `https://hotel-porter-d25ad83b12cf.herokuapp.com/api/hotel/bookings/stripe-webhook/`
- Events to listen: Select `checkout.session.completed`
- Copy the **Signing secret** (starts with `whsec_`)

## Heroku Configuration

Set environment variables on Heroku:

```bash
heroku config:set STRIPE_SECRET_KEY=sk_test_your_secret_key_here
heroku config:set STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
heroku config:set STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

## API Endpoints

### 1. Create Booking
`POST /api/hotel/<slug>/bookings/`

Returns booking with `payment_url` field.

### 2. Create Payment Session
`POST /api/hotel/bookings/<booking_id>/payment/session/`

**Request:**
```json
{
  "booking": {
    "hotel": {
      "name": "Hotel Killarney",
      "slug": "hotel-killarney"
    },
    "room": {
      "type": "Deluxe King Room",
      "photo": "https://..."
    },
    "dates": {
      "check_in": "2025-12-20",
      "check_out": "2025-12-22",
      "nights": 2
    },
    "guest": {
      "name": "John Doe",
      "email": "john@example.com"
    },
    "pricing": {
      "total": "267.00",
      "currency": "EUR"
    }
  },
  "success_url": "https://hotelsmates.com/booking/success",
  "cancel_url": "https://hotelsmates.com/booking/cancelled"
}
```

**Response:**
```json
{
  "session_id": "cs_test_a1b2c3d4e5f6",
  "payment_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "status": "created",
  "amount": "267.00",
  "currency": "EUR"
}
```

### 3. Verify Payment
`GET /api/hotel/bookings/<booking_id>/payment/verify/?session_id=<session_id>`

**Response:**
```json
{
  "booking_id": "BK-2025-ABC123",
  "payment_status": "paid",
  "amount_total": 267.0,
  "currency": "EUR",
  "customer_email": "john@example.com",
  "metadata": {
    "booking_id": "BK-2025-ABC123",
    "hotel_slug": "hotel-killarney"
  }
}
```

## Frontend Integration

### Basic Flow

```javascript
// 1. Create booking
const bookingResponse = await fetch('/api/hotel/hotel-killarney/bookings/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    room_type_code: 'DLX-KING',
    check_in: '2025-12-20',
    check_out: '2025-12-22',
    adults: 2,
    children: 0,
    guest: {
      first_name: 'John',
      last_name: 'Doe',
      email: 'john@example.com',
      phone: '+353 87 123 4567'
    }
  })
});

const booking = await bookingResponse.json();

// 2. Create payment session
const paymentResponse = await fetch(
  `/api/hotel/bookings/${booking.booking_id}/payment/session/`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      booking: booking,
      success_url: `${window.location.origin}/booking/success`,
      cancel_url: `${window.location.origin}/booking/cancelled`
    })
  }
);

const payment = await paymentResponse.json();

// 3. Redirect to Stripe Checkout
window.location.href = payment.payment_url;
```

### Success Page

```javascript
// On success page, verify payment
const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get('session_id');

if (sessionId) {
  const verifyResponse = await fetch(
    `/api/hotel/bookings/${bookingId}/payment/verify/?session_id=${sessionId}`
  );
  
  const result = await verifyResponse.json();
  
  if (result.payment_status === 'paid') {
    // Show success message
    console.log('Payment successful!');
  }
}
```

## Testing

Use Stripe test cards:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0027 6000 3184`

Any future date for expiry, any 3-digit CVC.

## Notes

- Currently in Phase 1 - no database persistence
- Booking data passed in payment session request
- Phase 2 will add database models and email notifications
- Webhook endpoint ready for payment confirmation
