# Complete Booking & Payment Flow Documentation

## Overview
This document provides a comprehensive guide to the hotel booking lifecycle, payment processing, status updates, API endpoints, and real-time events in the HotelMate system.

## Booking Status Flow

### Status Progression
```
DRAFT → PENDING_PAYMENT → PENDING_APPROVAL → CONFIRMED/DECLINED
```

### Status Definitions
- **DRAFT**: Booking created but not yet submitted for payment
- **PENDING_PAYMENT**: Awaiting guest payment authorization
- **PENDING_APPROVAL**: Payment authorized, awaiting staff decision
- **CONFIRMED**: Staff approved booking, payment captured
- **DECLINED**: Staff declined booking, payment authorization released

## Complete Payment Flow

### Phase 1: Payment Session Creation
**Endpoint**: `POST /api/public/hotel/<hotel_slug>/room-bookings/<booking_id>/payment/session/`
**File**: `hotel/payment_views.py` → `CreatePaymentSessionView`

**Process**:
1. Validate booking status is `PENDING_PAYMENT`
2. Generate idempotency key for duplicate prevention
3. Create Stripe checkout session with `capture_method: 'manual'` (authorize-capture)
4. Store session data in cache
5. Update booking with payment reference

**Status Updates**:
- Booking: `payment_provider = "stripe"`, `payment_reference = session.id`

**Response**:
```json
{
    "session_id": "cs_test_...",
    "payment_url": "https://checkout.stripe.com/...",
    "status": "created",
    "amount": "150.00",
    "currency": "EUR"
}
```

### Phase 2: Guest Payment Authorization
**External Process**: Guest completes payment on Stripe Checkout page

**Result**: Payment authorized but NOT captured (manual capture mode)

### Phase 3: Webhook Processing (Authorization)
**Endpoint**: `POST /api/public/hotel/room-bookings/stripe-webhook/`
**File**: `hotel/payment_views.py` → `StripeWebhookView.process_checkout_completed()`

**Stripe Event**: `checkout.session.completed`

**Process**:
1. Verify webhook signature
2. Check idempotency (prevent duplicate processing)
3. Validate PaymentIntent status is `requires_capture`
4. Atomic database update:
   - `status = 'PENDING_APPROVAL'`
   - `payment_authorized_at = now()`
   - `payment_intent_id = payment_intent_id`
   - `payment_reference = payment_intent_id`

**Email Notification**: Authorization confirmation to guest

**⚠️ MISSING**: Pusher event emission should happen here but doesn't currently

### Phase 4: Staff Decision (Approve/Decline)

#### Approve Booking
**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/approve/`
**File**: `hotel/staff_views.py` → `StaffBookingAcceptView`

**Process**:
1. Validate booking status is `PENDING_APPROVAL`
2. Idempotency check via `decision_made_at` field
3. Capture payment via Stripe API
4. Atomic database update:
   - `status = 'CONFIRMED'`
   - `decision_made_at = now()`
   - `paid_at = now()`
   - `decision_made_by = staff_user`

**Pusher Event**: `notification_manager.realtime_booking_updated(booking)`
**Email Notification**: Confirmation email to guest

#### Decline Booking
**Endpoint**: `POST /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/decline/`
**File**: `hotel/staff_views.py` → `StaffBookingDeclineView`

**Process**:
1. Validate booking status is `PENDING_APPROVAL`
2. Idempotency check via `decision_made_at` field
3. Cancel payment authorization via Stripe API
4. Atomic database update:
   - `status = 'DECLINED'`
   - `decision_made_at = now()`
   - `decision_made_by = staff_user`

**Pusher Event**: `notification_manager.realtime_booking_updated(booking)`
**Email Notification**: Decline notification to guest

## API Endpoints Summary

### Public (Guest) Endpoints
```
POST /api/public/hotel/<hotel_slug>/room-bookings/<booking_id>/payment/session/
GET  /api/public/hotel/<hotel_slug>/room-bookings/<booking_id>/payment/verify/
POST /api/public/hotel/room-bookings/stripe-webhook/
```

### Staff Endpoints
```
POST /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/approve/
POST /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/decline/
```

### URL Routing Files
- **Public URLs**: `public_urls.py`
- **Staff URLs**: `room_bookings/staff_urls.py`
- **Guest URLs**: `guest_urls.py`

## Database Updates by Phase

### Payment Session Creation
```python
# hotel/payment_views.py:CreatePaymentSessionView
booking.payment_provider = "stripe"
booking.payment_reference = session.id
booking.save(update_fields=['payment_provider', 'payment_reference'])
```

### Webhook Authorization Processing
```python
# hotel/payment_views.py:StripeWebhookView.process_checkout_completed()
booking.payment_provider = 'stripe'
booking.payment_intent_id = payment_intent_id
booking.payment_reference = payment_intent_id
booking.payment_authorized_at = timezone.now()
booking.status = 'PENDING_APPROVAL'
booking.save(update_fields=[
    'payment_provider', 'payment_intent_id', 'payment_reference',
    'payment_authorized_at', 'status'
])
```

### Staff Approval
```python
# hotel/staff_views.py:StaffBookingAcceptView
booking.status = RoomBooking.Status.CONFIRMED
booking.decision_made_at = timezone.now()
booking.decision_made_by = request.user
booking.paid_at = timezone.now()
booking.save(update_fields=['status', 'decision_made_at', 'decision_made_by', 'paid_at'])
```

### Staff Decline
```python
# hotel/staff_views.py:StaffBookingDeclineView
booking.status = RoomBooking.Status.DECLINED
booking.decision_made_at = timezone.now()
booking.decision_made_by = request.user
booking.save(update_fields=['status', 'decision_made_at', 'decision_made_by'])
```

## Pusher Real-time Events

### Current Implementation
**Function**: `notification_manager.realtime_booking_updated(booking)`
**File**: `common/notification_manager.py`

**Events Emitted**:
1. ✅ Staff approval → `notification_manager.realtime_booking_updated(booking)`
2. ✅ Staff decline → `notification_manager.realtime_booking_updated(booking)`
3. ❌ **MISSING**: Webhook authorization → Should emit but doesn't currently

### Event Structure
```python
def realtime_booking_updated(booking):
    """Emit Pusher event when booking status changes"""
    pusher_client.trigger(
        channel=f"hotel-{booking.hotel.slug}",
        event="booking-updated",
        data={
            "booking_id": booking.booking_id,
            "status": booking.status,
            "updated_at": booking.updated_at.isoformat()
        }
    )
```

## Email Notifications

### Authorization Email (Webhook)
**File**: `hotel/payment_views.py:process_checkout_completed()`
**Trigger**: Payment authorized, status → `PENDING_APPROVAL`
**Subject**: `"Payment authorized — awaiting hotel confirmation ({booking_id})"`

### Confirmation Email (Staff Approval)
**File**: `hotel/staff_views.py:StaffBookingAcceptView`
**Trigger**: Staff approves booking
**Subject**: `f"Booking Confirmed - {booking.booking_id}"`

### Decline Email (Staff Decline)
**File**: `hotel/staff_views.py:StaffBookingDeclineView`
**Trigger**: Staff declines booking
**Subject**: `f"Booking Update - {booking.booking_id}"`

## Critical Implementation Notes

### Authorize-Capture Configuration
```python
# Stripe session creation with manual capture
payment_intent_data={
    'capture_method': 'manual',
    'description': f"Hotel booking {booking_id} - {hotel_data['name']}",
}
```

### Idempotency Protection
1. **Payment Sessions**: Uses `generate_idempotency_key()` and cache storage
2. **Webhook Processing**: Database-level with `StripeWebhookEvent` model
3. **Staff Decisions**: Uses `decision_made_at` field to prevent duplicate processing

### Transaction Safety
All critical updates use `transaction.atomic()` and `select_for_update()` for race condition protection.

## Troubleshooting Guide

### Common Issues
1. **Duplicate webhook processing** → Check `StripeWebhookEvent` table
2. **Missing Pusher events** → Verify `notification_manager` import and call
3. **Payment not captured** → Check staff approval endpoint success
4. **Email not sent** → Verify SMTP configuration and email service status

### Key Log Messages
```
📍 CREATING PAYMENT SESSION - booking_id=XXX
✅ Payment session created: cs_test_XXX for booking XXX
📍 WEBHOOK PROCESSING - checkout.session.completed
✅ Booking XXX payment authorized (pending staff approval)
📧 send_mail returned True for guest@email.com
🎯 STAFF DECISION - APPROVE booking XXX
💳 Payment captured successfully: pi_XXX
```

## Missing Implementation

### Webhook Pusher Event
**Location**: `hotel/payment_views.py:process_checkout_completed()`
**Add after booking status update**:
```python
# TODO: Add missing Pusher event for webhook authorization
if booking_updated:
    from common import notification_manager
    notification_manager.realtime_booking_updated(booking)
```

This ensures real-time updates when bookings transition to `PENDING_APPROVAL` status.