# FCM & Pusher Notifications - Current Usage Analysis

## Overview
This document maps all current FCM (Firebase Cloud Messaging) and Pusher notifications in the HotelMate backend, showing where they're implemented and how the new unified `NotificationManager` consolidates them.

## Current FCM Locations

### 1. Core FCM Service (`notifications/fcm_service.py`)
```python
# Main FCM functions:
- send_fcm_notification(token, title, body, data=None)
- send_fcm_multicast(tokens, title, body, data=None)
- send_porter_order_notification(staff, order)
- send_porter_breakfast_notification(staff, order)
- send_kitchen_staff_order_notification(staff, order)
- send_booking_confirmation_notification(guest_fcm_token, booking)
- send_booking_cancellation_notification(guest_fcm_token, booking, reason=None)
```

### 2. Chat Views (`chat/views.py`)
**Lines 14, 287-301:** FCM for guest messages to staff
```python
from notifications.fcm_service import send_fcm_notification

# In notify_assigned_staff_of_guest_message()
if staff.fcm_token:
    fcm_title = f"💬 New Message - Room {room.room_number}"
    fcm_body = message_text[:100]
    send_fcm_notification(staff.fcm_token, fcm_title, fcm_body, data=fcm_data)
```

**Lines 347, 1733, 1797:** FCM for staff replies to guests
```python
send_fcm_notification(room.guest_fcm_token, fcm_title, fcm_body, data=fcm_data)
```

### 3. Hotel Staff Views (`hotel/staff_views.py`)
**Lines 1068-1084:** Booking confirmation FCM
```python
from notifications.fcm_service import send_booking_confirmation_notification
if guest_fcm_token:
    send_booking_confirmation_notification(guest_fcm_token, booking)
```

**Lines 1167-1183:** Booking cancellation FCM
```python
from notifications.fcm_service import send_booking_cancellation_notification
if guest_fcm_token:
    send_booking_cancellation_notification(guest_fcm_token, booking, cancellation_reason)
```

## Current Pusher Locations

### 1. Core Pusher Client (`chat/utils.py`)
```python
pusher_client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
    ssl=True
)
```

### 2. Notifications Pusher Utils (`notifications/pusher_utils.py`)
```python
# Department-based notifications:
- notify_staff_by_department(hotel, department_slug, event, data)
- notify_kitchen_staff(hotel, event, data)
- notify_maintenance_staff(hotel, event, data)
- notify_fnb_staff(hotel, event, data)

# Role-based notifications:
- notify_staff_by_role(hotel, role_slug, event, data)
- notify_porters(hotel, event, data)
- notify_receptionists(hotel, event, data)
- notify_room_service_waiters(hotel, event, data)

# Guest notifications:
- notify_guest_in_room(hotel, room_number, event, data)
```

### 3. Staff Pusher Utils (`staff/pusher_utils.py`)
**Lines 1-308:** Attendance and clock status updates
```python
- trigger_clock_status_update(hotel_slug, staff, action)
- trigger_face_attendance_update(hotel_slug, staff_id, attendance_data)
- trigger_duty_status_change(hotel_slug, staff_data)
- trigger_roster_notifications(hotel_slug, event_type, data)
```

### 4. Staff Chat Pusher Utils (`staff_chat/pusher_utils.py`)
```python
- get_conversation_channel(hotel_slug, conversation_id)
- get_staff_personal_channel(hotel_slug, staff_id)
- broadcast_new_message(hotel_slug, conversation_id, message_data)
- broadcast_message_edited(hotel_slug, conversation_id, message_data)
- broadcast_typing_indicator(hotel_slug, conversation_id, typing_data)
```

### 5. Stock Tracker Pusher Utils (`stock_tracker/pusher_utils.py`)
```python
- get_stocktake_channel(hotel_identifier, stocktake_id)
- trigger_stocktake_event(hotel_identifier, stocktake_id, event, data)
- broadcast_stock_item_update(hotel_identifier, stocktake_id, item_data)
```

### 6. Chat Views (`chat/views.py`)
**Multiple locations:** Direct pusher_client.trigger calls
```python
# Line 147: Staff assignment
pusher_client.trigger(f"{hotel.slug}-staff-{staff.id}", "staff-assigned", data)

# Line 188: Message delivery
pusher_client.trigger(message_channel, "message-delivered", data)

# Line 212: Guest notifications
pusher_client.trigger(guest_channel, "new-staff-message", message_data)

# Line 230: Badge updates
pusher_client.trigger(badge_channel, "conversation-unread", data)

# Line 264: Staff notifications
pusher_client.trigger(staff_channel, "new-guest-message", message_data)
```

### 7. Hotel Staff Views (`hotel/staff_views.py`)
**Line 118:** Room assignment notifications
```python
pusher_client.trigger(f"hotel-{hotel.slug}", "room-assignment-updated", data)
```

### 8. Bookings Views (`bookings/views.py`)
**Lines 242, 518:** Booking updates
```python
pusher_client.trigger(f"hotel-{hotel.slug}", "new-booking", booking_data)
pusher_client.trigger(channel_name, "bookings-seen", {"updated": updated_count})
```

## Current Notification Utils (`notifications/utils.py`)

### Functions using both FCM and Pusher:
```python
- notify_porters_of_room_service_order(order)
- notify_kitchen_staff_of_room_service_order(order)  
- notify_porters_order_count(hotel)
- notify_porters_of_breakfast_order(order)
- notify_porters_breakfast_count(hotel)
```

## FCM Token Storage

### Staff Model (`staff/models.py`)
```python
class Staff(models.Model):
    fcm_token = models.TextField(blank=True, null=True)
```

### Room Model (`rooms/models.py`)
```python
class Room(models.Model):
    guest_fcm_token = models.TextField(blank=True, null=True)
```

## Current Usage Patterns by Module

### 1. Room Service Orders
- **Files:** `room_services/views.py`, `room_services/signals.py`
- **FCM:** Porter and kitchen staff notifications
- **Pusher:** Real-time order updates to staff dashboards
- **Triggers:** Order creation, status changes

### 2. Breakfast Orders  
- **Files:** `room_services/signals.py`
- **FCM:** Porter notifications
- **Pusher:** Real-time breakfast order updates
- **Triggers:** Order creation, delivery updates

### 3. Guest Chat Messages
- **Files:** `chat/views.py`
- **FCM:** Staff notifications when guest sends message
- **Pusher:** Real-time message delivery, read receipts, typing indicators
- **Triggers:** Message send, staff assignment

### 4. Staff Chat Messages
- **Files:** `chat/views.py`
- **FCM:** Guest notifications when staff replies
- **Pusher:** Real-time staff-to-guest communication
- **Triggers:** Staff reply, message status updates

### 5. Booking Management
- **Files:** `hotel/staff_views.py`, `bookings/views.py`
- **FCM:** Guest confirmation/cancellation notifications
- **Pusher:** Real-time booking updates to staff
- **Triggers:** Booking creation, cancellation, modifications

### 6. Staff Attendance
- **Files:** `staff/pusher_utils.py`, attendance modules
- **FCM:** Not currently used for attendance
- **Pusher:** Real-time attendance status, clock in/out, break status
- **Triggers:** Clock actions, duty status changes

### 7. Stock Management
- **Files:** `stock_tracker/pusher_utils.py`
- **FCM:** Not currently used for stock
- **Pusher:** Real-time stock updates, stocktake progress
- **Triggers:** Stock item updates, stocktake completion

## Migration to Unified NotificationManager

### Benefits of New System:
1. **Single Entry Point:** All notifications through one manager
2. **Smart Fallback:** Automatic FCM + Pusher for comprehensive coverage
3. **Role-Based Targeting:** Easy staff role and department filtering
4. **Consistent Logging:** Unified notification result tracking
5. **Backward Compatibility:** Old functions still work during migration

### Migration Strategy:
```python
# OLD WAY (scattered across multiple files):
from notifications.fcm_service import send_porter_order_notification
from notifications.pusher_utils import notify_porters
from chat.utils import pusher_client

send_porter_order_notification(porter, order)
notify_porters(hotel, 'new-order', order_data)
pusher_client.trigger(channel, event, data)

# NEW WAY (unified):
from notifications.notification_manager import notification_manager

notification_manager.notify_porters_new_room_service_order(order)
```

## Next Steps

1. **Phase 1:** Update existing notification calls to use NotificationManager
2. **Phase 2:** Migrate direct pusher_client.trigger calls to manager methods  
3. **Phase 3:** Consolidate similar notification patterns
4. **Phase 4:** Add notification preferences and rate limiting
5. **Phase 5:** Remove old individual notification functions

This unified approach will make notification management much more maintainable and provide better consistency across the application.