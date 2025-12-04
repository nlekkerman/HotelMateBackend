# Migration Guide: Using Unified NotificationManager

## Quick Start

Replace scattered notification calls with the unified manager:

```python
# Import the unified manager
from notifications.notification_manager import notification_manager

# Or use individual functions (backward compatible)
from notifications.notification_manager import (
    notify_porters_of_room_service_order,
    notify_kitchen_staff_of_room_service_order
)
```

## Example Migrations

### 1. Room Service Order Notifications

**BEFORE (multiple files and imports):**
```python
# room_services/views.py
from notifications.utils import (
    notify_porters_of_room_service_order,
    notify_kitchen_staff_of_room_service_order
)

def create_order(request):
    order = Order.objects.create(...)
    
    # Separate calls to different systems
    notify_porters_of_room_service_order(order)
    notify_kitchen_staff_of_room_service_order(order)
```

**AFTER (unified approach):**
```python
# room_services/views.py
from notifications.notification_manager import notification_manager

def create_order(request):
    order = Order.objects.create(...)
    
    # Single manager handles both FCM and Pusher automatically
    porter_results = notification_manager.notify_porters_new_room_service_order(order)
    kitchen_results = notification_manager.notify_kitchen_staff_new_order(order)
    
    # Optional: Log results
    logger.info(f"Notified {porter_results['fcm_sent']} porters via FCM, {porter_results['pusher_sent']} via Pusher")
```

### 2. Guest Chat Messages

**BEFORE (chat/views.py):**
```python
from notifications.fcm_service import send_fcm_notification
from chat.utils import pusher_client

def notify_staff_of_guest_message(message, staff_list):
    for staff in staff_list:
        # FCM notification
        if staff.fcm_token:
            send_fcm_notification(staff.fcm_token, title, body, data)
        
        # Pusher notification
        staff_channel = f"{hotel.slug}-staff-{staff.id}"
        pusher_client.trigger(staff_channel, "new-guest-message", message_data)
```

**AFTER:**
```python
from notifications.notification_manager import notification_manager

def notify_staff_of_guest_message(message, staff_list):
    results = notification_manager.notify_staff_new_guest_message(message, staff_list)
    return results  # Contains detailed success/failure counts
```

### 3. Booking Confirmations

**BEFORE (hotel/staff_views.py):**
```python
from notifications.fcm_service import send_booking_confirmation_notification
from notifications.email_service import send_booking_confirmation_email

def confirm_booking(request, booking_id):
    booking = get_object_or_404(RoomBooking, id=booking_id)
    
    # Email
    send_booking_confirmation_email(booking)
    
    # FCM
    if guest_fcm_token:
        send_booking_confirmation_notification(guest_fcm_token, booking)
    
    # Manual Pusher (if needed)
    # ... custom pusher code
```

**AFTER:**
```python
from notifications.notification_manager import notification_manager
from notifications.email_service import send_booking_confirmation_email

def confirm_booking(request, booking_id):
    booking = get_object_or_404(RoomBooking, id=booking_id)
    
    # Email (unchanged)
    send_booking_confirmation_email(booking)
    
    # FCM + Pusher handled automatically
    results = notification_manager.notify_guest_booking_confirmed(booking)
```

### 4. Staff Attendance Updates

**BEFORE (staff/views.py):**
```python
from staff.pusher_utils import trigger_clock_status_update

def clock_in(request):
    staff = request.user.staff
    # ... clock in logic
    
    # Manual Pusher trigger
    trigger_clock_status_update(hotel.slug, staff, 'clock_in')
```

**AFTER:**
```python
from notifications.notification_manager import notification_manager

def clock_in(request):
    staff = request.user.staff
    # ... clock in logic
    
    # Unified notification
    notification_manager.notify_attendance_status_change(staff, 'clock_in')
```

## Advanced Usage Examples

### Custom Staff Notifications by Role/Department

```python
# Notify all on-duty kitchen staff about urgent order
results = notification_manager.notify_staff_by_role_and_department(
    hotel=hotel,
    department_slug='kitchen',
    event='urgent-order',
    data={'order_id': order.id, 'priority': 'high'},
    fcm_title='🚨 Urgent Kitchen Order',
    fcm_body=f'Priority order for room {order.room_number}',
    only_on_duty=True
)

print(f"Notified {results['total_staff']} kitchen staff")
```

### Multi-Role Notifications

```python
# Notify both porters and receptionists about special request
for role in ['porter', 'receptionist']:
    results = notification_manager.notify_staff_by_role_and_department(
        hotel=hotel,
        role_slug=role,
        event='special-request',
        data={'request_type': 'vip_arrival', 'room': room_number},
        fcm_title='VIP Guest Arrival',
        fcm_body=f'VIP guest arriving at room {room_number}',
        only_on_duty=True
    )
```

## Testing Your Migration

### 1. Check Notification Results
```python
results = notification_manager.notify_porters_new_room_service_order(order)

# Results structure:
{
    'fcm_sent': 2,          # Number of FCM notifications sent successfully
    'fcm_failed': 0,        # Number of FCM notifications that failed
    'pusher_sent': 3,       # Number of Pusher notifications sent
    'pusher_failed': 0,     # Number of Pusher notifications that failed  
    'total_porters': 3      # Total number of porters found
}
```

### 2. Enable Debug Logging
```python
import logging
logging.getLogger('notifications.notification_manager').setLevel(logging.DEBUG)
```

### 3. Check Notification Summary
```python
summary = notification_manager.get_notification_summary()
print(summary)
# Shows FCM/Pusher enabled status, supported events, roles, departments
```

## Gradual Migration Steps

### Step 1: Start with High-Impact Areas
1. Room service orders (`room_services/views.py`)
2. Guest chat messages (`chat/views.py`)
3. Booking confirmations (`hotel/staff_views.py`)

### Step 2: Replace Utility Functions
Update imports in:
- `room_services/signals.py`
- `notifications/utils.py` 
- Any custom notification code

### Step 3: Consolidate Direct pusher_client.trigger Calls
Look for direct `pusher_client.trigger()` calls and replace with manager methods.

### Step 4: Remove Old Imports
Once migration is complete, remove old imports:
```python
# Remove these:
from notifications.fcm_service import send_fcm_notification
from notifications.pusher_utils import notify_porters
from chat.utils import pusher_client

# Keep only:
from notifications.notification_manager import notification_manager
```

## Backward Compatibility

The new system maintains backward compatibility:

```python
# These still work during migration:
from notifications.notification_manager import (
    notify_porters_of_room_service_order,  # ✅ Works
    notify_kitchen_staff_of_room_service_order,  # ✅ Works
    notify_staff_new_message,  # ✅ Works
)

# But prefer the new manager approach:
from notifications.notification_manager import notification_manager
notification_manager.notify_porters_new_room_service_order(order)
```

This allows you to migrate gradually without breaking existing functionality.