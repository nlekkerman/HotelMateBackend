# 🔄 Frontend API Migration Guide - Phase 3 Public Hotel Cleanup

## Overview
**All public hotel endpoints have been moved and restructured.** This document explains what changed and how to update your frontend code.

## 🚨 BREAKING CHANGES

### URL Pattern Changes
- **OLD Pattern:** `/api/hotel/{slug}/...` 
- **NEW Pattern:** `/api/public/hotel/{hotel_slug}/...`

### Parameter Changes
- **OLD:** URL parameter is `slug`
- **NEW:** URL parameter is `hotel_slug` (same value, different name)

---

## 📋 Complete Endpoint Migration Map

### Hotel Public Page
```diff
- OLD: GET /api/hotel/{slug}/page/
+ NEW: GET /api/public/hotel/{hotel_slug}/page/
```

### Availability Check
```diff
- OLD: GET /api/hotel/{slug}/availability/?check_in=2025-12-20&check_out=2025-12-22
+ NEW: GET /api/public/hotel/{hotel_slug}/availability/?check_in=2025-12-20&check_out=2025-12-22
```

### Pricing Quote
```diff
- OLD: POST /api/hotel/{slug}/pricing/quote/
+ NEW: POST /api/public/hotel/{hotel_slug}/pricing/quote/
```

### Booking Creation
```diff
- OLD: POST /api/hotel/{slug}/bookings/
+ NEW: POST /api/public/hotel/{hotel_slug}/bookings/
```

### Payment Session Creation
```diff
- OLD: POST /api/hotel/{slug}/bookings/{booking_id}/payment/session/
+ NEW: POST /api/public/hotel/{hotel_slug}/room-bookings/{booking_id}/payment/session/
```

### Payment Verification
```diff
- OLD: GET /api/hotel/{slug}/bookings/{booking_id}/payment/verify/?session_id=xxx
+ NEW: GET /api/public/hotel/{hotel_slug}/room-bookings/{booking_id}/payment/verify/?session_id=xxx
```

### Stripe Webhook *(Backend Only)*
```diff
- OLD: POST /api/hotel/bookings/stripe-webhook/
+ NEW: POST /api/public/hotel/room-bookings/stripe-webhook/
```

---

## 🔧 Frontend Code Changes Required

### 1. Update Base URLs

**Before:**
```javascript
const API_BASE = '/api/hotel';

// Hotel page
const hotelPageUrl = `${API_BASE}/${hotelSlug}/page/`;

// Availability check
const availabilityUrl = `${API_BASE}/${hotelSlug}/availability/`;

// Booking creation
const bookingUrl = `${API_BASE}/${hotelSlug}/bookings/`;
```

**After:**
```javascript
const API_BASE = '/api/public/hotel';

// Hotel page
const hotelPageUrl = `${API_BASE}/${hotelSlug}/page/`;

// Availability check  
const availabilityUrl = `${API_BASE}/${hotelSlug}/availability/`;

// Booking creation
const bookingUrl = `${API_BASE}/${hotelSlug}/bookings/`;
```

### 2. Update Payment URLs

**Before:**
```javascript
// Payment session
const paymentUrl = `/api/hotel/${hotelSlug}/bookings/${bookingId}/payment/session/`;

// Payment verification
const verifyUrl = `/api/hotel/${hotelSlug}/bookings/${bookingId}/payment/verify/`;
```

**After:**
```javascript
// Payment session  
const paymentUrl = `/api/public/hotel/${hotelSlug}/room-bookings/${bookingId}/payment/session/`;

// Payment verification
const verifyUrl = `/api/public/hotel/${hotelSlug}/room-bookings/${bookingId}/payment/verify/`;
```

### 3. Update API Response Handling

**Payment URLs in booking responses have changed:**

**Before:**
```javascript
// Booking creation response contained:
{
  "payment_url": "/api/hotel/demo-hotel/bookings/123/payment/session/"
}
```

**After:**
```javascript
// Booking creation response now contains:
{
  "payment_url": "/api/public/hotel/demo-hotel/room-bookings/123/payment/session/"
}
```

---

## 🧪 Testing Your Changes

### Quick Test Checklist

1. **Hotel Page Loading:**
   ```bash
   curl -X GET "http://localhost:8000/api/public/hotel/demo-hotel/page/"
   ```

2. **Availability Check:**
   ```bash
   curl -X GET "http://localhost:8000/api/public/hotel/demo-hotel/availability/?check_in=2025-12-20&check_out=2025-12-22"
   ```

3. **Pricing Quote:**
   ```bash
   curl -X POST "http://localhost:8000/api/public/hotel/demo-hotel/pricing/quote/" \
     -H "Content-Type: application/json" \
     -d '{"room_type_code":"standard","check_in":"2025-12-20","check_out":"2025-12-22","adults":2}'
   ```

4. **Booking Creation:**
   ```bash
   curl -X POST "http://localhost:8000/api/public/hotel/demo-hotel/bookings/" \
     -H "Content-Type: application/json" \
     -d '{"room_type_code":"standard","check_in":"2025-12-20","check_out":"2025-12-22","guest":{"first_name":"John","last_name":"Doe","email":"john@example.com","phone":"+1234567890"}}'
   ```

### Verify Old URLs Return 404
```bash
# These should all return 404:
curl -X GET "http://localhost:8000/api/hotel/demo-hotel/page/"
curl -X GET "http://localhost:8000/api/hotel/demo-hotel/availability/"
curl -X POST "http://localhost:8000/api/hotel/demo-hotel/bookings/"
```

---

## 📝 Migration Checklist

**Frontend Updates Required:**

- [ ] Update all API base URLs from `/api/hotel/` to `/api/public/hotel/`
- [ ] Update payment URLs to use `/room-bookings/` instead of `/bookings/`
- [ ] Test hotel page loading with new URL structure
- [ ] Test availability checking with new endpoints
- [ ] Test booking flow end-to-end
- [ ] Test payment session creation and verification
- [ ] Verify error handling still works correctly
- [ ] Update any hardcoded URLs in configuration files
- [ ] Update documentation and API client libraries
- [ ] Test in staging environment before production deployment

**Backend Confirmation:**

- [x] All new public endpoints resolve correctly
- [x] All old endpoints return 404 (no legacy support)
- [x] Django check passes with no errors
- [x] URL patterns use consistent `{hotel_slug}` parameter
- [x] Payment URLs updated in booking responses

---

## 🆘 Troubleshooting

### Common Issues

**404 Errors:**
- Make sure you're using `/api/public/hotel/` instead of `/api/hotel/`
- Verify hotel slug is correct in the URL

**Payment Flow Broken:**
- Check that payment URLs use `/room-bookings/` instead of `/bookings/`
- Verify booking ID parameter is passed correctly

**Parameter Errors:**
- Hotel slug parameter name remains the same (`hotel_slug`)
- Only the URL structure changed, not parameter values

### Support

If you encounter issues during migration:
1. Check the complete endpoint URL structure
2. Verify all URL parameters are correctly formatted
3. Test with a known working hotel slug (e.g., `demo-hotel`)
4. Check browser network tab for exact request URLs

---

**✅ Migration Complete When:**
- All frontend API calls use new `/api/public/hotel/` endpoints
- Payment flow works end-to-end with new URLs
- No references to old `/api/hotel/` endpoints remain
- All automated tests pass with new endpoint structure