# 🛡️ Phase 3 Public Hotel Cleanup - Implementation Plan

## Overview
Move all public hotel endpoints from `hotel/urls.py` to `public_urls.py` using consistent `{hotel_slug}` patterns, eliminating legacy `<slug:slug>` routes and duplicate endpoints.

## STRICT REQUIREMENTS
- **Replace ALL `<slug:slug>` with `<str:hotel_slug>`** - both URL converter and kwarg name
- **All public hotel endpoints ONLY under `/api/public/hotel/{hotel_slug}/`**
- **Paths in public_urls.py start with `hotel/...`** (root includes `/api/public/`)
- **Public booking creation stays at `/api/public/hotel/{hotel_slug}/bookings/`** - do NOT rename
- **Delete legacy routes completely** - no aliases, no redirects, old routes must 404
- **URLs + view kwargs updated in SAME commit**
- **Do NOT touch `/api/guest/` or `/api/staff/` routing**

## Current State Analysis

### Root Routing Structure
```
/api/public/  → public_urls.py  (✅ already configured)
/api/staff/   → staff_urls.py   (✅ Phase 1 complete)  
/api/guest/   → guest_urls.py   (✅ Phase 2 complete)
/api/hotel/   → hotel/urls.py   (🔧 needs cleanup)
```

### Routes to Migrate from hotel/urls.py → public_urls.py

**Payment Routes (currently missing in public_urls.py):**
```python
# From hotel/urls.py:
path("<slug:slug>/bookings/<str:booking_id>/payment/", CreatePaymentSessionView)
path("<slug:slug>/bookings/<str:booking_id>/payment/session/", CreatePaymentSessionView) 
path("<slug:slug>/bookings/<str:booking_id>/payment/verify/", VerifyPaymentView)

# Will become in public_urls.py:
path("hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/payment/", CreatePaymentSessionView)
path("hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/payment/session/", CreatePaymentSessionView)
path("hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/payment/verify/", VerifyPaymentView)
```

**Stripe Webhook (no hotel identification needed):**
```python
# From hotel/urls.py:
path("bookings/stripe-webhook/", StripeWebhookView)

# Will become in public_urls.py:
path("hotel/room-bookings/stripe-webhook/", StripeWebhookView)
```

### Routes to Remove from hotel/urls.py (duplicates)

**Already exist in public_urls.py:**
```python
# DELETE from hotel/urls.py:
path("<slug:slug>/availability/", HotelAvailabilityView)
path("<slug:slug>/pricing/quote/", HotelPricingQuoteView) 
path("<slug:slug>/bookings/", HotelBookingCreateView)
path("public/page/<slug:slug>/", HotelPublicPageView)  # legacy route
```

## Implementation Steps

### Step 1: Update public_urls.py
Add missing payment and webhook endpoints with proper URL structure:

**Important:** All paths in public_urls.py must start with `hotel/...`, not `api/public/...` since root routing already includes `path("api/public/", include("public_urls"))`.

```python
# Current public_urls.py patterns:
path("hotel/<slug:slug>/page/", HotelPublicPageView)                    # Change to hotel_slug
path("hotel/<slug:slug>/availability/", HotelAvailabilityView)          # Change to hotel_slug
path("hotel/<slug:slug>/pricing/quote/", HotelPricingQuoteView)         # Change to hotel_slug  
path("hotel/<slug:slug>/bookings/", HotelBookingCreateView)             # Change to hotel_slug

# ADD these new patterns:
path("hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/payment/", CreatePaymentSessionView)
path("hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/payment/session/", CreatePaymentSessionView)
path("hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/payment/verify/", VerifyPaymentView)
path("hotel/room-bookings/stripe-webhook/", StripeWebhookView)
```

### Step 2: Update View Parameter Access
Change views to use `hotel_slug` instead of `slug`:

**Files to Update:**
- `hotel/payment_views.py` - CreatePaymentSessionView, VerifyPaymentView
- `hotel/booking_views.py` - HotelBookingCreateView  
- `hotel/views.py` - HotelAvailabilityView, HotelPricingQuoteView, HotelPublicPageView

**Parameter Change:**
```python
# FROM:
hotel_slug = self.kwargs["slug"]

# TO:  
hotel_slug = self.kwargs["hotel_slug"]
```

### Step 3: Remove Duplicate Routes from hotel/urls.py
Delete these route patterns completely:

```python
# DELETE THESE:
path("<slug:slug>/availability/", HotelAvailabilityView.as_view(), name="hotel-availability"),
path("<slug:slug>/pricing/quote/", HotelPricingQuoteView.as_view(), name="hotel-pricing-quote"), 
path("<slug:slug>/bookings/", HotelBookingCreateView.as_view(), name="hotel-booking-create"),
path("<slug:slug>/bookings/<str:booking_id>/payment/", CreatePaymentSessionView.as_view(), name="hotel-booking-payment"),
path("<slug:slug>/bookings/<str:booking_id>/payment/session/", CreatePaymentSessionView.as_view(), name="hotel-booking-payment-session"),
path("<slug:slug>/bookings/<str:booking_id>/payment/verify/", VerifyPaymentView.as_view(), name="hotel-booking-payment-verify"),
path("bookings/stripe-webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
path("public/page/<slug:slug>/", HotelPublicPageView.as_view(), name="hotel-legacy-public-page"),
```

### Step 4: Update Import Statements
Ensure all required views are imported in public_urls.py:

```python
# Required imports:
from hotel.booking_views import HotelBookingCreateView
from hotel.payment_views import CreatePaymentSessionView, VerifyPaymentView, StripeWebhookView  
from hotel.views import HotelAvailabilityView, HotelPricingQuoteView, HotelPublicPageView
```

## Final URL Structure

**After completion, all public hotel endpoints will be:**

```
/api/public/hotel/{hotel_slug}/page/                                    → HotelPublicPageView
/api/public/hotel/{hotel_slug}/availability/                            → HotelAvailabilityView  
/api/public/hotel/{hotel_slug}/pricing/quote/                           → HotelPricingQuoteView
/api/public/hotel/{hotel_slug}/bookings/                                → HotelBookingCreateView
/api/public/hotel/{hotel_slug}/room-bookings/{booking_id}/payment/      → CreatePaymentSessionView
/api/public/hotel/{hotel_slug}/room-bookings/{booking_id}/payment/session/ → CreatePaymentSessionView
/api/public/hotel/{hotel_slug}/room-bookings/{booking_id}/payment/verify/  → VerifyPaymentView
/api/public/hotel/room-bookings/stripe-webhook/                         → StripeWebhookView
```

**Note:** Public booking creation remains at `/bookings/` for backward compatibility with frontend; staff booking management uses `/room-bookings/`.

## Validation Tests

1. **Django Check:** `python manage.py check` must pass
2. **URL Resolution:** All new public endpoints resolve correctly
3. **404 Verification:** Old `/api/hotel/<slug>/...` routes return 404
4. **Parameter Access:** Views correctly access `hotel_slug` from kwargs
5. **Webhook Functionality:** Stripe webhook works without hotel identification

## Success Criteria

✅ All public hotel endpoints live ONLY under `/api/public/hotel/{hotel_slug}/`  
✅ No `<slug:slug>` patterns remain in public routing  
✅ Root `urls.py` remains unchanged  
✅ Old routes under `/api/hotel/...` return 404  
✅ All views use consistent `hotel_slug` parameter naming  
✅ Django check passes without errors  

## Risk Mitigation

- **Atomic Changes:** Update URLs + view kwargs in single commit to avoid broken states
- **No Legacy Support:** Immediate 404 for old routes (no redirects/aliases)
- **Import Verification:** Ensure all view imports are correct before deployment
- **Parameter Consistency:** Verify all views consistently use `hotel_slug` pattern

---

**Ready for implementation. Waiting for go cue.**