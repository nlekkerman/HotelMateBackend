# HotelMate Notifications Documentation

This document provides a comprehensive overview of all Pusher (real-time) and FCM (push) notifications in the HotelMate system, including their triggers, receivers, and data structures.

## Table of Contents
- [Pusher Notifications (Real-time)](#pusher-notifications-real-time)
- [FCM Notifications (Push)](#fcm-notifications-push)
- [Channel Patterns](#channel-patterns)
- [Notification Triggers](#notification-triggers)
- [Future Notification Possibilities](#future-notification-possibilities)

---

## Pusher Notifications (Real-time)

### 1. Guest Chat Notifications

#### 1.1 New Guest Message
- **Event**: `new-guest-message`
- **Channel**: `{hotel_slug}-staff-{staff_id}-chat`
- **Receivers**: All staff members (reception/front-office)
- **Triggered by**: Guest sends message to hotel
- **Data**:
  ```json
  {
    "conversation_id": "123",
    "message_id": "456",
    "room_number": "101",
    "sender_type": "guest",
    "message_text": "Message content",
    "timestamp": "2025-11-30T10:00:00Z"
  }
  ```

#### 1.2 New Staff Message to Guest
- **Event**: `new-staff-message`
- **Channel**: `{hotel_slug}-room-{room_number}-chat`
- **Receivers**: Guest in specific room
- **Triggered by**: Staff sends message to guest
- **Data**:
  ```json
  {
    "conversation_id": "123",
    "message_id": "456",
    "staff_name": "John Doe",
    "message_text": "Response message",
    "timestamp": "2025-11-30T10:00:00Z"
  }
  ```

#### 1.3 Staff Assignment
- **Event**: `staff-assigned`
- **Channel**: `{hotel_slug}-room-{room_number}-chat`
- **Receivers**: Guest in specific room
- **Triggered by**: New staff member handles guest conversation
- **Data**:
  ```json
  {
    "staff_name": "Jane Smith",
    "staff_role": "Receptionist",
    "conversation_id": "123"
  }
  ```

#### 1.4 Message Updates
- **Events**: 
  - `message-updated` 
  - `message-deleted`
  - `message-removed`
- **Channels**: 
  - `{hotel_slug}-conversation-{conversation_id}-chat`
  - `{hotel_slug}-room-{room_number}-chat` (guests)
  - `{hotel_slug}-staff-{staff_id}-chat` (staff)
- **Receivers**: All conversation participants
- **Triggered by**: Message editing/deletion operations

#### 1.5 Conversation Management
- **Event**: `conversation-unread`
- **Channel**: `{hotel_slug}-conversation-{conversation_id}-chat`
- **Receivers**: Staff handling conversation
- **Triggered by**: Guest sends new message (badge update)
- **Data**:
  ```json
  {
    "conversation_id": "123",
    "room_number": "101"
  }
  ```

#### 1.6 Message Delivery Status
- **Event**: `message-delivered`
- **Channel**: `{hotel_slug}-conversation-{conversation_id}-chat`
- **Receivers**: All conversation participants
- **Triggered by**: Message successfully processed

#### 1.7 Attachment Management
- **Events**: 
  - `attachment-deleted`
- **Channels**: 
  - `{hotel_slug}-conversation-{conversation_id}-chat`
  - `{hotel_slug}-deletions-{conversation_id}`
- **Receivers**: All conversation participants
- **Triggered by**: File attachment deletion

### 2. Staff Chat Notifications

#### 2.1 Staff Conversation Messages
- **Event**: `new-message`
- **Channel**: `{hotel_slug}-staff-conversation-{conversation_id}`
- **Receivers**: All staff participants in conversation
- **Triggered by**: Staff sends message in staff chat
- **Data**:
  ```json
  {
    "message_id": "789",
    "sender_id": "123",
    "sender_name": "John Doe",
    "message_text": "Staff message content",
    "conversation_id": "456",
    "timestamp": "2025-11-30T10:00:00Z"
  }
  ```

#### 2.2 Staff Message Management
- **Events**: 
  - `message-edited`
  - `message-deleted`
  - `message-reaction`
- **Channel**: `{hotel_slug}-staff-conversation-{conversation_id}`
- **Receivers**: All staff participants in conversation
- **Triggered by**: Staff message editing/deletion/reactions

#### 2.3 Staff Personal Notifications
- **Events**: 
  - `message-mention` (when @mentioned)
  - `new-conversation` (added to conversation)
- **Channel**: `{hotel_slug}-staff-{staff_id}-notifications`
- **Receivers**: Individual staff member
- **Triggered by**: Being mentioned or added to conversation

#### 2.4 Conversation Utilities
- **Events**: 
  - `typing-indicator`
  - `read-receipt`
  - `conversation-updated`
  - `attachment-uploaded`
  - `attachment-deleted`
- **Channel**: `{hotel_slug}-staff-conversation-{conversation_id}`
- **Receivers**: All staff participants in conversation
- **Triggered by**: Various conversation interactions

### 3. Staff Management Notifications

#### 3.1 Clock Status Updates
- **Event**: `clock-status-updated`
- **Channel**: `hotel-{hotel_slug}`
- **Receivers**: All staff in hotel
- **Triggered by**: Staff clock in/out operations
- **Data**:
  ```json
  {
    "user_id": "123",
    "staff_id": "456",
    "is_on_duty": true,
    "clock_time": "2025-11-30T09:00:00Z",
    "first_name": "John",
    "last_name": "Doe",
    "action": "clock_in",
    "department": "Reception",
    "department_slug": "reception"
  }
  ```

#### 3.2 Staff Profile Updates
- **Event**: `staff-updated`
- **Channel**: `hotel-{hotel_slug}`
- **Receivers**: All staff in hotel
- **Triggered by**: Staff profile changes (role, department, etc.)
- **Data**:
  ```json
  {
    "action": "updated",
    "staff_id": "456",
    "user_id": "123",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "department": "Reception",
    "department_slug": "reception",
    "role": "Receptionist",
    "role_slug": "receptionist",
    "is_active": true,
    "is_on_duty": true,
    "access_level": "standard",
    "timestamp": "2025-11-30T10:00:00Z"
  }
  ```

#### 3.3 Registration Updates
- **Event**: `staff-registration-updated`
- **Channel**: `hotel-{hotel_slug}`
- **Receivers**: All staff in hotel (managers)
- **Triggered by**: Staff registration approval/rejection
- **Data**:
  ```json
  {
    "action": "approved",
    "user_id": "123",
    "username": "john.doe",
    "registration_code": "REG123",
    "staff_id": "456",
    "timestamp": "2025-11-30T10:00:00Z"
  }
  ```

#### 3.4 Department/Role Updates
- **Events**: 
  - `department-updated`
  - `role-updated`
- **Channel**: `hotel-{hotel_slug}`
- **Receivers**: All staff in hotel
- **Triggered by**: Department/role creation, updates, deletion

### 4. Attendance & Roster Notifications

#### 4.1 Attendance Events
- **Event**: `attendance-logged`
- **Channel**: `attendance-{hotel_slug}`
- **Receivers**: Managers and attendance viewers
- **Triggered by**: Clock in/out operations
- **Data**:
  ```json
  {
    "id": "789",
    "staff_id": "456",
    "staff_name": "John Doe",
    "department": "Reception",
    "time": "2025-11-30T09:00:00Z",
    "verified_by_face": true,
    "is_unrostered": false,
    "is_approved": true
  }
  ```

#### 4.2 Roster Management
- **Event**: `roster-updated`
- **Channel**: `attendance-{hotel_slug}`
- **Receivers**: Managers and roster viewers
- **Triggered by**: Roster period/shift changes

#### 4.3 Period Finalization
- **Event**: `period-finalized`
- **Channel**: `attendance-{hotel_slug}-managers`
- **Receivers**: Managers only
- **Triggered by**: Roster period finalization
- **Data**:
  ```json
  {
    "period_id": "123",
    "period_title": "Week of Nov 25",
    "finalized_by": "Manager Name",
    "message": "Roster period 'Week of Nov 25' has been finalized.",
    "timestamp": "2025-11-30T15:30:00Z"
  }
  ```

#### 4.4 Unrostered Requests
- **Event**: `unrostered-clockin-request`
- **Channel**: `attendance-{hotel_slug}-managers`
- **Receivers**: Managers only
- **Triggered by**: Staff clocking in without scheduled shift
- **Data**:
  ```json
  {
    "type": "unrostered_clockin_request",
    "clock_log_id": "789",
    "staff_id": "456",
    "staff_name": "John Doe",
    "department": "Reception",
    "message": "John Doe requests approval for unrostered shift",
    "actions": [
      {
        "label": "Approve",
        "action": "approve",
        "endpoint": "/api/hotels/grand-hotel/clock-logs/789/approve/",
        "style": "success"
      },
      {
        "label": "Reject",
        "action": "reject",
        "endpoint": "/api/hotels/grand-hotel/clock-logs/789/reject/",
        "style": "danger"
      }
    ],
    "timestamp": "2025-11-30T09:00:00Z"
  }
  ```

#### 4.5 Break Warnings
- **Event**: `break-warning`
- **Channels**: 
  - `attendance-{hotel_slug}-staff-{staff_id}` (individual)
  - `attendance-{hotel_slug}-managers` (oversight)
- **Receivers**: Individual staff member and managers
- **Triggered by**: Long shift duration (break reminder system)
- **Data**:
  ```json
  {
    "type": "break_warning",
    "clock_log_id": "789",
    "staff_id": "456",
    "staff_name": "John Doe",
    "duration_hours": 6.5,
    "message": "Break reminder: You've been working for 6.5 hours. Consider taking a break.",
    "timestamp": "2025-11-30T15:30:00Z"
  }
  ```

### 5. Room Service Notifications

#### 5.1 New Orders (Pusher)
- **Event**: `new-room-service-order`
- **Channel**: `{hotel_slug}-staff-{staff_id}-porter`
- **Receivers**: On-duty porters
- **Triggered by**: New room service order creation
- **Data**:
  ```json
  {
    "order_id": "123",
    "room_number": "101",
    "total_price": 45.99,
    "created_at": "2025-11-30T12:00:00Z",
    "status": "pending"
  }
  ```

#### 5.2 Breakfast Orders (Pusher)
- **Event**: `new-breakfast-order`
- **Channel**: `{hotel_slug}-staff-{staff_id}-porter`
- **Receivers**: On-duty porters
- **Triggered by**: New breakfast order creation
- **Data**:
  ```json
  {
    "order_id": "456",
    "room_number": "102",
    "delivery_time": "2025-11-30T08:00:00Z",
    "created_at": "2025-11-30T20:00:00Z",
    "status": "pending"
  }
  ```

#### 5.3 Kitchen Staff Orders (Pusher)
- **Event**: `new-room-service-order`
- **Channel**: `{hotel_slug}-staff-{staff_id}-kitchen`
- **Receivers**: On-duty kitchen staff
- **Triggered by**: New room service order creation (food items)

### 6. Stock Tracker Notifications

#### 6.1 Stocktake Management
- **Events**: 
  - `stocktake-created`
  - `stocktake-deleted`
  - `stocktake-status-changed`
- **Channel**: `{hotel_slug}-stocktakes`
- **Receivers**: All staff viewing stocktakes list
- **Triggered by**: Stocktake lifecycle operations

#### 6.2 Individual Stocktake Updates
- **Events**: 
  - `line-updated`
  - `line-deleted`
  - `stocktake-status-changed`
  - `user-joined`
  - `user-left`
  - `user-editing-line`
- **Channel**: `{hotel_slug}-stocktake-{stocktake_id}`
- **Receivers**: All staff viewing specific stocktake
- **Triggered by**: Real-time stocktake editing operations

### 7. Guest Notifications (to rooms)

#### 7.1 Room-specific Notifications
- **Events**: Custom events (depends on implementation)
- **Channel**: `{hotel_slug}-room-{room_number}`
- **Receivers**: Guest in specific room
- **Triggered by**: Hotel-specific notifications to guests
- **Usage**: Generic guest notification system

---

## FCM Notifications (Push)

### 1. Guest Chat FCM

#### 1.1 Staff Message to Guest
- **Title**: `💬 {staff_name}`
- **Body**: Message preview (first 100 characters)
- **Recipients**: Guest in room (via `room.guest_fcm_token`)
- **Triggered by**: Staff sends message to guest
- **Data**:
  ```json
  {
    "type": "new_chat_message",
    "conversation_id": "123",
    "room_number": "101",
    "message_id": "456",
    "sender_type": "staff",
    "staff_name": "John Doe",
    "hotel_slug": "grand-hotel",
    "click_action": "/chat/grand-hotel/room/101",
    "url": "https://hotelsmates.com/chat/grand-hotel/room/101"
  }
  ```

#### 1.2 Staff File Upload to Guest
- **Title**: Varies by file type:
  - `📷 Staff sent 2 image(s) - Room 101`
  - `📄 Staff sent document(s) - Room 102`
  - `📎 Staff sent file(s) - Room 103`
- **Body**: `Check the attached files`
- **Recipients**: Guest in room
- **Triggered by**: Staff uploads files to guest conversation

### 2. Staff Chat FCM

#### 2.1 New Staff Message
- **Title**: 
  - Group: `💬 {sender_name} in {group_title}`
  - Direct: `💬 {sender_name}`
- **Body**: Message preview (first 100 characters)
- **Recipients**: All staff participants (excluding sender)
- **Triggered by**: Staff sends message in staff chat
- **Data**:
  ```json
  {
    "type": "staff_chat_message",
    "conversation_id": "123",
    "sender_id": "456",
    "sender_name": "John Doe",
    "is_group": "true",
    "hotel_slug": "grand-hotel",
    "click_action": "/staff-chat/grand-hotel/conversation/123",
    "url": "https://hotelsmates.com/staff-chat/grand-hotel/conversation/123"
  }
  ```

#### 2.2 Staff Mention
- **Title**: `@️⃣ {sender_name} mentioned you in {conversation_title}`
- **Body**: Message containing mention (first 100 characters)
- **Recipients**: Mentioned staff member
- **Triggered by**: Staff mentions another staff member (@username)
- **Data**:
  ```json
  {
    "type": "staff_chat_mention",
    "conversation_id": "123",
    "sender_id": "456",
    "sender_name": "John Doe",
    "mentioned_staff_id": "789",
    "hotel_slug": "grand-hotel",
    "click_action": "/staff-chat/grand-hotel/conversation/123",
    "url": "https://hotelsmates.com/staff-chat/grand-hotel/conversation/123"
  }
  ```

#### 2.3 New Conversation
- **Title**: 
  - Group: `👥 New Group Chat: {group_title}`
  - Direct: `💬 New Chat with {creator_name}`
- **Body**: 
  - Group: `{creator_name} added you to a group conversation`
  - Direct: `You can now start chatting`
- **Recipients**: Staff added to new conversation
- **Triggered by**: Staff creates new conversation and adds participants
- **Data**:
  ```json
  {
    "type": "staff_chat_new_conversation",
    "conversation_id": "123",
    "creator_id": "456",
    "creator_name": "John Doe",
    "is_group": "true",
    "hotel_slug": "grand-hotel",
    "click_action": "/staff-chat/grand-hotel/conversation/123",
    "url": "https://hotelsmates.com/staff-chat/grand-hotel/conversation/123"
  }
  ```

#### 2.4 Staff File Attachments
- **Title**: Varies by file type:
  - `📷 {sender_name} sent 2 image(s)`
  - `📄 {sender_name} sent document(s)`
  - `📎 {sender_name} sent file(s)`
- **Body**: `Check the attached files`
- **Recipients**: All conversation participants (excluding sender)
- **Triggered by**: Staff uploads files to staff conversation

### 3. Room Service FCM

#### 3.1 Porter - Room Service Order
- **Title**: `🔔 New Room Service Order`
- **Body**: `Room {room_number} - €{total_price}`
- **Recipients**: On-duty porters with FCM tokens
- **Triggered by**: New room service order creation
- **Data**:
  ```json
  {
    "type": "room_service_order",
    "order_id": "123",
    "room_number": "101",
    "total_price": "45.99",
    "status": "pending",
    "click_action": "FLUTTER_NOTIFICATION_CLICK",
    "route": "/orders/room-service"
  }
  ```

#### 3.2 Porter - Breakfast Order
- **Title**: `🍳 New Breakfast Order`
- **Body**: `Room {room_number} - Delivery: {delivery_time}`
- **Recipients**: On-duty porters with FCM tokens
- **Triggered by**: New breakfast order creation
- **Data**:
  ```json
  {
    "type": "breakfast_order",
    "order_id": "456",
    "room_number": "102",
    "delivery_time": "08:00",
    "status": "pending",
    "click_action": "FLUTTER_NOTIFICATION_CLICK",
    "route": "/orders/breakfast"
  }
  ```

#### 3.3 Porter - Order Count Updates
- **Title**: 
  - Room Service: `📋 Room Service Updates`
  - Breakfast: `📋 Breakfast Updates`
- **Body**: `{pending_count} pending order(s)`
- **Recipients**: On-duty porters
- **Triggered by**: Order count changes (periodic updates)
- **Data**:
  ```json
  {
    "type": "order_count_update",
    "pending_count": "5",
    "order_type": "room_service_orders",
    "click_action": "FLUTTER_NOTIFICATION_CLICK"
  }
  ```

#### 3.4 Kitchen Staff - Room Service Orders
- **Title**: `🔔 New Room Service Order`
- **Body**: `Room {room_number} - €{total_price}`
- **Recipients**: On-duty kitchen staff with FCM tokens
- **Triggered by**: New room service order with food items
- **Data**: Same as porter room service notification

### 4. Booking FCM

#### 4.1 Booking Confirmation
- **Title**: `✅ Booking Confirmed!`
- **Body**: `Your reservation at {hotel_name} has been confirmed`
- **Recipients**: Guest (via `guest_fcm_token` if available)
- **Triggered by**: Booking confirmation process
- **Data**:
  ```json
  {
    "type": "booking_confirmation",
    "booking_id": "BK123456",
    "confirmation_number": "CONF789",
    "hotel_name": "Grand Hotel",
    "room_type": "Deluxe Room",
    "check_in": "2025-12-01",
    "check_out": "2025-12-03",
    "click_action": "FLUTTER_NOTIFICATION_CLICK",
    "route": "/bookings/details"
  }
  ```

#### 4.2 Booking Cancellation
- **Title**: `❌ Booking Cancelled`
- **Body**: `Your reservation at {hotel_name} has been cancelled`
- **Recipients**: Guest (via `guest_fcm_token` if available)
- **Triggered by**: Booking cancellation (staff or system)
- **Data**:
  ```json
  {
    "type": "booking_cancellation",
    "booking_id": "BK123456",
    "confirmation_number": "CONF789",
    "hotel_name": "Grand Hotel",
    "cancellation_reason": "Request by guest",
    "click_action": "FLUTTER_NOTIFICATION_CLICK",
    "route": "/bookings/cancelled"
  }
  ```

### 5. Guest Room Service FCM

#### 5.1 Order Status Updates (Future)
- **Title**: `📋 Order Update`
- **Body**: `Your room service order is {status}`
- **Recipients**: Guest who placed order
- **Triggered by**: Order status changes (preparing, ready, delivered)
- **Status**: Not yet implemented but structure prepared

---

## Channel Patterns

### Pusher Channels

1. **Hotel-wide**: `hotel-{hotel_slug}`
2. **Guest Chat**: `{hotel_slug}-room-{room_number}-chat`
3. **Staff Chat**: 
   - Personal: `{hotel_slug}-staff-{staff_id}-notifications`
   - Conversation: `{hotel_slug}-staff-conversation-{conversation_id}`
4. **Staff Notifications**: `{hotel_slug}-staff-{staff_id}-{department/role}`
5. **Conversation**: `{hotel_slug}-conversation-{conversation_id}-chat`
6. **Attendance**: 
   - General: `attendance-{hotel_slug}`
   - Managers: `attendance-{hotel_slug}-managers`
   - Individual: `attendance-{hotel_slug}-staff-{staff_id}`
7. **Stock Tracker**: 
   - List: `{hotel_slug}-stocktakes`
   - Detail: `{hotel_slug}-stocktake-{stocktake_id}`
8. **Deletions**: `{hotel_slug}-deletions-{conversation_id}`

### FCM Token Storage

- **Staff**: `staff.fcm_token` (Staff model)
- **Guests**: `room.guest_fcm_token` (Room model, temporary)
- **Token Management**: `/api/staff/save-fcm-token/` endpoint

---

## Notification Triggers

### Database Signals
- **Order Creation**: `post_save` on `Order` and `BreakfastOrder` models
- **Clock Operations**: Manual triggers in attendance views
- **Staff Changes**: Manual triggers in staff management views

### View Actions
- **Message Sending**: Direct triggers in chat views
- **File Uploads**: Direct triggers in upload views
- **Roster Changes**: Direct triggers in attendance views
- **Status Updates**: Direct triggers in various management views

### Background Tasks
- **Break Warnings**: Periodic checks on long shifts
- **Order Count Updates**: Periodic updates for porter dashboards
- **Cleanup**: Periodic cleanup of expired tokens

---

## Future Notification Possibilities

### 1. Enhanced Guest Notifications
- **Room Ready**: Notify guest when room is ready for check-in
- **Housekeeping Updates**: Notify guest about room service completion
- **Hotel Amenities**: Notify guest about pool hours, restaurant specials
- **Weather Updates**: Local weather for guest area
- **Transportation**: Notify about shuttle services, taxi arrivals

### 2. Advanced Staff Notifications
- **Shift Reminders**: 30-minute before shift notifications
- **Break Reminders**: Automated break suggestions based on labor laws
- **Training Alerts**: Mandatory training deadline reminders
- **Emergency Broadcasts**: Hotel-wide emergency notifications
- **Maintenance Alerts**: Equipment issues requiring immediate attention

### 3. Management Dashboard Notifications
- **Revenue Alerts**: Daily/weekly revenue milestone notifications
- **Occupancy Updates**: Real-time occupancy rate changes
- **Staff Performance**: Attendance rate, customer satisfaction alerts
- **Inventory Alerts**: Low stock notifications from stock tracker
- **Security Alerts**: Integration with security systems

### 4. Guest Experience Enhancements
- **Pre-arrival**: Welcome message with check-in instructions
- **During Stay**: Personalized service recommendations
- **Post-departure**: Thank you message and feedback request
- **Loyalty Program**: Points earned, special offers
- **Event Notifications**: Hotel events, local attractions

### 5. Integration Notifications
- **PMS Integration**: Sync with property management systems
- **Payment Alerts**: Payment processing status updates
- **Review Alerts**: New online review notifications
- **Channel Manager**: Booking updates from external platforms
- **IoT Integration**: Room sensor alerts (temperature, occupancy)

### 6. Advanced Operational Notifications
- **Predictive Maintenance**: Equipment failure predictions
- **Energy Management**: High consumption alerts
- **Compliance Reminders**: Health department inspection dates
- **Vendor Notifications**: Delivery schedules, service appointments
- **Guest Preference Alerts**: VIP guest arrival notifications

### 7. Real-time Analytics Notifications
- **Live Dashboard Updates**: Real-time metrics via Pusher
- **Performance Thresholds**: Automated alerts when KPIs change
- **Comparative Analysis**: Week-over-week performance changes
- **Anomaly Detection**: Unusual patterns in bookings or operations

---

## Implementation Guidelines

### For New Pusher Notifications:
1. Create channel pattern following existing conventions
2. Add event to appropriate `pusher_utils.py` file
3. Call from relevant view/signal/task
4. Document channel, event, data structure, and receivers

### For New FCM Notifications:
1. Add function to `notifications/fcm_service.py`
2. Ensure FCM token availability for recipients
3. Follow existing data structure patterns
4. Include appropriate `click_action` and routing
5. Test with both Android and iOS if applicable

### Testing Considerations:
- Mock Pusher client in unit tests
- Test FCM token validation
- Verify notification delivery in integration tests
- Check channel naming consistency
- Validate data structure completeness

---

## Contact & Support

For questions about notifications implementation:
- Check existing `*_utils.py` files for patterns
- Review test files for usage examples
- Ensure proper error handling for all notification calls
- Follow channel naming conventions strictly
- Document any new notification types in this file

Last Updated: November 30, 2025