# Booking System Implementation - Complete

## ✅ Implemented Endpoints

### 1. Availability Check
**URL**: `GET /api/hotel/<slug>/availability/`

**Query Parameters**:
- `check_in`: YYYY-MM-DD
- `check_out`: YYYY-MM-DD
- `adults`: number (default 2)
- `children`: number (default 0)

**Example**:
```
GET /api/hotel/hotel-killarney/availability/?check_in=2025-11-25&check_out=2025-11-27&adults=2&children=0
```

---

### 2. Pricing Quote
**URL**: `POST /api/hotel/<slug>/pricing/quote/`

**Request Body**:
```json
{
  "room_type_code": "DLX-KING",
  "check_in": "2025-12-20",
  "check_out": "2025-12-22",
  "adults": 2,
  "children": 0,
  "promo_code": "WINTER20"
}
```

**Promo Codes**:
- `WINTER20` - 20% off
- `SAVE10` - 10% off

---

### 3. Create Booking
**URL**: `POST /api/hotel/<slug>/bookings/`

**Request Body**:
```json
{
  "quote_id": "QT-2025-ABC123",
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
  "special_requests": "Late check-in",
  "promo_code": "WINTER20"
}
```

---

### 4. Create Payment Session (Stripe)
**URL**: `POST /api/hotel/bookings/<booking_id>/payment/session/`

**Request Body**:
```json
{
  "booking": { /* full booking object from create booking response */ },
  "success_url": "https://hotelsmates.com/booking/success",
  "cancel_url": "https://hotelsmates.com/booking/cancelled"
}
```

---

### 5. Verify Payment
**URL**: `GET /api/hotel/bookings/<booking_id>/payment/verify/?session_id=<stripe_session_id>`

---

### 6. Stripe Webhook
**URL**: `POST /api/hotel/bookings/stripe-webhook/`

---

## 📦 Dependencies Added

```txt
stripe==11.2.0
```

## 🔧 Configuration Required

### Environment Variables (.env)

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

### Heroku Config

```bash
heroku config:set STRIPE_SECRET_KEY=sk_test_...
heroku config:set STRIPE_PUBLISHABLE_KEY=pk_test_...
heroku config:set STRIPE_WEBHOOK_SECRET=whsec_...
```

## 📁 Files Modified/Created

### Modified:
- `hotel/views.py` - Added availability, pricing, and booking views
- `hotel/urls.py` - Added all booking and payment routes
- `requirements.txt` - Added stripe package
- `HotelMateBackend/settings.py` - Added Stripe configuration

### Created:
- `hotel/payment_views.py` - Stripe payment integration
- `docs/STRIPE_INTEGRATION.md` - Setup guide
- `docs/BOOKING_SYSTEM_SUMMARY.md` - This file

## 🚀 Deployment Steps

1. **Commit changes**:
```bash
git add .
git commit -m "Add booking system with Stripe payment integration"
```

2. **Push to Heroku**:
```bash
git push heroku main
```

3. **Set environment variables**:
```bash
heroku config:set STRIPE_SECRET_KEY=sk_test_...
heroku config:set STRIPE_PUBLISHABLE_KEY=pk_test_...
heroku config:set STRIPE_WEBHOOK_SECRET=whsec_...
```

4. **Configure Stripe webhook**:
- Go to https://dashboard.stripe.com/webhooks
- Add endpoint: `https://hotel-porter-d25ad83b12cf.herokuapp.com/api/hotel/bookings/stripe-webhook/`
- Select event: `checkout.session.completed`
- Copy webhook secret and update Heroku config

## 🧪 Testing

### Test Cards (Stripe Test Mode)
- **Success**: 4242 4242 4242 4242
- **Decline**: 4000 0000 0000 0002
- **3D Secure**: 4000 0027 6000 3184

Use any future expiry date and any 3-digit CVC.

## 📝 Phase 1 Limitations

- No database persistence for bookings
- No email confirmations
- No room inventory management
- Booking data passed via API (not stored)
- Webhook handler prints to console (no database update)

## 🔮 Phase 2 TODO

- Create RoomBooking database model
- Add booking status management
- Implement email confirmation system
- Add inventory/availability tracking
- Store booking history
- Add booking cancellation/modification
- Implement admin booking management
