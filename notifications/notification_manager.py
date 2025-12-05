"""
Unified Notification Manager for HotelMate
Consolidates FCM (Firebase Cloud Messaging) and Pusher real-time notifications
into a single, easy-to-use interface.

This manager handles:
- FCM push notifications (when app is closed/backgrounded)
- Pusher real-time events (when app is open)
- Staff role-based notifications
- Guest notifications
- Department-specific notifications
- Order notifications (room service, breakfast)
- Booking notifications
- Chat/message notifications
- Attendance notifications

Usage Example:
    from notifications.notification_manager import NotificationManager
    
    # Initialize
    nm = NotificationManager()
    
    # Send to all porters
    nm.notify_porters_new_order(order)
    
    # Send to specific staff
    nm.notify_staff_message(staff, message_data)
    
    # Send to guest
    nm.notify_guest_booking_confirmed(booking)
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Union
from django.utils import timezone
from django.conf import settings

# FCM imports
from .fcm_service import (
    send_fcm_notification, 
    send_fcm_multicast,
    send_porter_order_notification,
    send_porter_breakfast_notification,
    send_kitchen_staff_order_notification,
    send_booking_confirmation_notification,
    send_booking_cancellation_notification
)

# Pusher imports
from chat.utils import pusher_client
from .pusher_utils import (
    notify_staff_by_department,
    notify_staff_by_role,
    notify_porters,
    notify_kitchen_staff,
    notify_receptionists,
    notify_maintenance_staff,
    notify_guest_in_room
)

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Unified notification manager that handles both FCM and Pusher notifications
    with smart fallback and role-based targeting.
    
    Extended with realtime event handling for the 5 migrated frontend domains:
    - attendance
    - staff_chat  
    - guest_chat
    - room_service
    - booking
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # =============================================================================
    # UNIFIED REALTIME EVENT METHODS FOR 5 MIGRATED DOMAINS
    # =============================================================================
    
    def _create_normalized_event(self, category: str, event_type: str, payload: dict, hotel, scope: dict = None) -> dict:
        """
        Create normalized event structure for frontend domains.
        
        Returns:
        {
          "category": "attendance|staff_chat|guest_chat|room_service|booking",
          "type": "some_event_type", 
          "payload": { ... domain-specific data ... },
          "meta": {
            "hotel_slug": "hotel-killarney",
            "event_id": "uuid",
            "ts": "ISO-8601 timestamp",
            "scope": { ... optional targeting info ... }
          }
        }
        """
        return {
            "category": category,
            "type": event_type,
            "payload": payload,
            "meta": {
                "hotel_slug": hotel.slug if hotel else "unknown",
                "event_id": str(uuid.uuid4()),
                "ts": timezone.now().isoformat(),
                "scope": scope or {}
            }
        }
    
    def _safe_pusher_trigger(self, channel: str, event: str, data: dict) -> bool:
        """Safely trigger Pusher event with error handling."""
        try:
            pusher_client.trigger(channel, event, data)
            self.logger.info(f"✅ Pusher event sent: {channel} → {event}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Pusher failed: {channel} → {event}: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # ATTENDANCE REALTIME METHODS
    # -------------------------------------------------------------------------
    
    def realtime_attendance_clock_status_updated(self, staff, action: str, clock_log=None):
        """
        Emit normalized attendance event for clock status changes.
        
        Args:
            staff: Staff instance
            action: 'clock_in', 'clock_out', 'start_break', 'end_break'
            clock_log: Optional clock log instance
        """
        self.logger.info(f"🕐 Realtime attendance: {staff.id} - {action}")
        
        # Get current status
        current_status = staff.get_current_status() if hasattr(staff, 'get_current_status') else {}
        
        # Determine duty status from action
        duty_status = staff.duty_status
        if action == 'clock_in':
            duty_status = 'on_duty'
        elif action == 'clock_out':
            duty_status = 'off_duty' 
        elif action == 'start_break':
            duty_status = 'on_break'
        elif action == 'end_break':
            duty_status = 'on_duty'
        
        # Build complete payload for frontend store update
        payload = {
            'staff_id': staff.id,
            'staff_name': f"{staff.first_name} {staff.last_name}",
            'user_id': staff.user.id if staff.user else None,
            'department': staff.department.name if staff.department else None,
            'department_slug': staff.department.slug if staff.department else None,
            'role': staff.role.name if staff.role else None,
            'role_slug': staff.role.slug if staff.role else None,
            'duty_status': duty_status,
            'action': action,
            'timestamp': timezone.now().isoformat(),
            'source': clock_log.source if clock_log and hasattr(clock_log, 'source') else 'manual',
            'is_on_duty': duty_status in ['on_duty', 'on_break'],
            'is_on_break': duty_status == 'on_break',
            'current_status': current_status
        }
        
        # Create normalized event
        event_data = self._create_normalized_event(
            category="attendance",
            event_type="clock_status_updated",
            payload=payload,
            hotel=staff.hotel,
            scope={'staff_id': staff.id, 'department': staff.department.slug if staff.department else None}
        )
        
        # Send to hotel attendance channel
        channel = f"hotel-{staff.hotel.slug}.attendance"
        return self._safe_pusher_trigger(channel, "clock-status-updated", event_data)
    
    # -------------------------------------------------------------------------
    # STAFF CHAT REALTIME METHODS
    # -------------------------------------------------------------------------
    
    def realtime_staff_chat_message_created(self, message):
        """
        Emit normalized staff chat message created event.
        
        Args:
            message: Staff chat message instance
        """
        self.logger.info(f"💬 Realtime staff chat: message {message.id} created")
        
        # Build complete payload
        payload = {
            'conversation_id': message.conversation.id,
            'message_id': message.id,
            'sender_id': message.sender.id,
            'sender_name': f"{message.sender.first_name} {message.sender.last_name}",
            'text': message.text,
            'created_at': message.created_at.isoformat(),
            'updated_at': message.updated_at.isoformat() if hasattr(message, 'updated_at') else message.created_at.isoformat(),
            'attachments': getattr(message, 'attachments', []),
            'is_system_message': getattr(message, 'is_system_message', False)
        }
        
        # Create normalized event
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="message_created", 
            payload=payload,
            hotel=message.conversation.hotel if hasattr(message.conversation, 'hotel') else message.sender.hotel,
            scope={'conversation_id': message.conversation.id, 'sender_id': message.sender.id}
        )
        
        # Send to conversation channel
        hotel_slug = message.sender.hotel.slug
        channel = f"hotel-{hotel_slug}.staff-chat.{message.conversation.id}"
        return self._safe_pusher_trigger(channel, "message-created", event_data)
    
    def realtime_staff_chat_message_edited(self, message):
        """Emit normalized staff chat message edited event."""
        self.logger.info(f"✏️ Realtime staff chat: message {message.id} edited")
        
        payload = {
            'conversation_id': message.conversation.id,
            'message_id': message.id,
            'sender_id': message.sender.id,
            'sender_name': f"{message.sender.first_name} {message.sender.last_name}",
            'text': message.text,
            'created_at': message.created_at.isoformat(),
            'updated_at': message.updated_at.isoformat() if hasattr(message, 'updated_at') else timezone.now().isoformat(),
            'edited': True
        }
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="message_edited",
            payload=payload,
            hotel=message.sender.hotel,
            scope={'conversation_id': message.conversation.id, 'message_id': message.id}
        )
        
        hotel_slug = message.sender.hotel.slug
        channel = f"hotel-{hotel_slug}.staff-chat.{message.conversation.id}"
        return self._safe_pusher_trigger(channel, "message-edited", event_data)
    
    # -------------------------------------------------------------------------
    # GUEST CHAT REALTIME METHODS  
    # -------------------------------------------------------------------------
    
    def realtime_guest_chat_message_created(self, message):
        """
        Emit normalized guest chat message created event.
        
        Args:
            message: Guest chat message instance (could be from guest or staff)
        """
        self.logger.info(f"💬 Realtime guest chat: message {message.id} created")
        
        # Determine sender info based on RoomMessage model fields
        sender_role = message.sender_type  # "guest" or "staff"
        sender_id = None
        sender_name = "Guest"
        
        if sender_role == "staff" and message.staff:
            sender_id = message.staff.id
            sender_name = message.staff_display_name or f"{message.staff.first_name} {message.staff.last_name}"
        
        # Build complete payload
        payload = {
            'conversation_id': message.conversation.id if message.conversation else f"room-{message.room.room_number}",
            'message_id': message.id,
            'sender_role': sender_role,
            'sender_id': sender_id,
            'sender_name': sender_name,
            'text': message.message,
            'created_at': message.timestamp.isoformat(),
            'room_number': message.room.room_number,
            'is_staff_reply': sender_role == "staff",
            'attachments': getattr(message, 'attachments', []),
            'pin': getattr(message.room, 'pin', None)
        }
        
        # Create normalized event
        event_data = self._create_normalized_event(
            category="guest_chat",
            event_type="guest_message_created" if sender_role == "guest" else "staff_message_created",
            payload=payload,
            hotel=message.room.hotel,
            scope={
                'room_number': message.room.room_number,
                'conversation_id': payload['conversation_id'],
                'sender_role': sender_role
            }
        )
        
        # Send to guest chat channel (room-specific)
        hotel_slug = message.room.hotel.slug
        room_pin = message.room.pin if hasattr(message.room, 'pin') else message.room.room_number
        channel = f"hotel-{hotel_slug}.guest-chat.{room_pin}"
        
        # Also send FCM if appropriate
        if sender_role == "guest" and hasattr(message, 'assigned_staff') and message.assigned_staff and message.assigned_staff.fcm_token:
            # Notify staff of guest message
            fcm_title = f"💬 New Message - Room {message.room.room_number}"
            fcm_body = message.message[:100]
            fcm_data = {
                "type": "guest_message",
                "room_number": message.room.room_number,
                "conversation_id": payload['conversation_id']
            }
            send_fcm_notification(message.assigned_staff.fcm_token, fcm_title, fcm_body, fcm_data)
        elif sender_role == "staff" and message.room.guest_fcm_token:
            # Notify guest of staff reply
            fcm_title = f"Reply from {sender_name}"
            fcm_body = message.message[:100] 
            fcm_data = {
                "type": "staff_reply",
                "room_number": message.room.room_number,
                "conversation_id": payload['conversation_id']
            }
            send_fcm_notification(message.room.guest_fcm_token, fcm_title, fcm_body, fcm_data)
        
        return self._safe_pusher_trigger(channel, "message-created", event_data)
    
    def realtime_guest_chat_unread_updated(self, room, unread_count=None):
        """Emit normalized guest chat unread count update event."""
        self.logger.info(f"🔢 Realtime guest chat: unread updated for room {room.room_number}")
        
        payload = {
            'room_number': room.room_number,
            'conversation_id': f"room-{room.room_number}",
            'unread_count': unread_count or 0,
            'updated_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="guest_chat",
            event_type="unread_updated",
            payload=payload,
            hotel=room.hotel,
            scope={'room_number': room.room_number}
        )
        
        hotel_slug = room.hotel.slug
        room_pin = room.pin if hasattr(room, 'pin') else room.room_number  
        channel = f"hotel-{hotel_slug}.guest-chat.{room_pin}"
        
        return self._safe_pusher_trigger(channel, "unread-updated", event_data)
    
    # -------------------------------------------------------------------------
    # ROOM SERVICE REALTIME METHODS
    # -------------------------------------------------------------------------
    
    def realtime_room_service_order_created(self, order):
        """Emit normalized room service order created event."""
        self.logger.info(f"🍽️ Realtime room service: order {order.id} created")
        
        # Build complete payload
        payload = {
            'order_id': order.id,
            'room_number': order.room_number,
            'status': order.status,
            'total_price': float(order.total_price),
            'created_at': order.created_at.isoformat(),
            'updated_at': getattr(order, 'updated_at', order.created_at).isoformat(),
            'items': self._build_order_items_payload(order),
            'special_instructions': getattr(order, 'special_instructions', ''),
            'estimated_delivery': getattr(order, 'estimated_delivery', None),
            'priority': getattr(order, 'priority', 'normal')
        }
        
        event_data = self._create_normalized_event(
            category="room_service",
            event_type="order_created",
            payload=payload,
            hotel=order.hotel,
            scope={'order_id': order.id, 'room_number': order.room_number}
        )
        
        # Send to room service channel
        hotel_slug = order.hotel.slug
        channel = f"hotel-{hotel_slug}.room-service"
        
        # Send FCM + Pusher to relevant staff
        self._notify_room_service_staff_of_new_order(order, event_data)
        
        return self._safe_pusher_trigger(channel, "order-created", event_data)
    
    def realtime_room_service_order_updated(self, order):
        """Emit normalized room service order updated event."""
        self.logger.info(f"🔄 Realtime room service: order {order.id} updated")
        
        payload = {
            'order_id': order.id,
            'room_number': order.room_number,
            'status': order.status,
            'total_price': float(order.total_price),
            'created_at': order.created_at.isoformat(),
            'updated_at': getattr(order, 'updated_at', timezone.now()).isoformat(),
            'items': self._build_order_items_payload(order),
            'special_instructions': getattr(order, 'special_instructions', ''),
            'estimated_delivery': getattr(order, 'estimated_delivery', None)
        }
        
        event_data = self._create_normalized_event(
            category="room_service",
            event_type="order_updated",
            payload=payload,
            hotel=order.hotel,
            scope={'order_id': order.id, 'room_number': order.room_number, 'status': order.status}
        )
        
        hotel_slug = order.hotel.slug
        channel = f"hotel-{hotel_slug}.room-service"
        return self._safe_pusher_trigger(channel, "order-updated", event_data)
    
    # -------------------------------------------------------------------------
    # BOOKING REALTIME METHODS
    # -------------------------------------------------------------------------
    
    def realtime_booking_created(self, booking):
        """Emit normalized booking created event."""
        self.logger.info(f"🏨 Realtime booking: {booking.booking_id} created")
        
        payload = {
            'booking_id': booking.booking_id,
            'confirmation_number': getattr(booking, 'confirmation_number', None),
            'guest_name': f"{booking.first_name} {booking.last_name}",
            'guest_email': booking.email,
            'guest_phone': getattr(booking, 'phone', ''),
            'room': booking.room_number if hasattr(booking, 'room_number') else None,
            'room_type': getattr(booking, 'room_type', None),
            'check_in': booking.check_in.isoformat(),
            'check_out': booking.check_out.isoformat(),
            'nights': (booking.check_out - booking.check_in).days,
            'total_price': float(getattr(booking, 'total_price', 0)),
            'status': getattr(booking, 'status', 'pending'),
            'created_at': booking.created_at.isoformat() if hasattr(booking, 'created_at') else timezone.now().isoformat(),
            'special_requests': getattr(booking, 'special_requests', ''),
            'adults': getattr(booking, 'adults', 1),
            'children': getattr(booking, 'children', 0)
        }
        
        event_data = self._create_normalized_event(
            category="booking",
            event_type="booking_created",
            payload=payload,
            hotel=booking.hotel,
            scope={'booking_id': booking.booking_id, 'guest_email': booking.email}
        )
        
        # Send to booking channel
        hotel_slug = booking.hotel.slug
        channel = f"hotel-{hotel_slug}.booking"
        
        # Send FCM to guest if token available
        self._notify_guest_booking_confirmed(booking)
        
        return self._safe_pusher_trigger(channel, "booking-created", event_data)
    
    def realtime_booking_updated(self, booking):
        """Emit normalized booking updated event."""
        self.logger.info(f"🔄 Realtime booking: {booking.booking_id} updated")
        
        payload = {
            'booking_id': booking.booking_id,
            'confirmation_number': getattr(booking, 'confirmation_number', None),
            'guest_name': f"{booking.first_name} {booking.last_name}",
            'room': booking.room_number if hasattr(booking, 'room_number') else None,
            'check_in': booking.check_in.isoformat(),
            'check_out': booking.check_out.isoformat(),
            'status': getattr(booking, 'status', 'confirmed'),
            'updated_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="booking",
            event_type="booking_updated",
            payload=payload,
            hotel=booking.hotel,
            scope={'booking_id': booking.booking_id, 'status': payload['status']}
        )
        
        hotel_slug = booking.hotel.slug
        channel = f"hotel-{hotel_slug}.booking"
        return self._safe_pusher_trigger(channel, "booking-updated", event_data)
    
    def realtime_booking_cancelled(self, booking, reason=None):
        """Emit normalized booking cancelled event."""
        self.logger.info(f"❌ Realtime booking: {booking.booking_id} cancelled")
        
        payload = {
            'booking_id': booking.booking_id,
            'confirmation_number': getattr(booking, 'confirmation_number', None),
            'guest_name': f"{booking.first_name} {booking.last_name}",
            'room': booking.room_number if hasattr(booking, 'room_number') else None,
            'check_in': booking.check_in.isoformat(),
            'check_out': booking.check_out.isoformat(),
            'status': 'cancelled',
            'cancellation_reason': reason or 'No reason provided',
            'cancelled_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="booking",
            event_type="booking_cancelled",
            payload=payload,
            hotel=booking.hotel,
            scope={'booking_id': booking.booking_id, 'reason': reason}
        )
        
        # Send FCM cancellation to guest
        self._notify_guest_booking_cancelled(booking, reason)
        
        hotel_slug = booking.hotel.slug
        channel = f"hotel-{hotel_slug}.booking"
        return self._safe_pusher_trigger(channel, "booking-cancelled", event_data)
    
    # -------------------------------------------------------------------------
    # HELPER METHODS
    # -------------------------------------------------------------------------
    
    def _build_order_items_payload(self, order):
        """Build order items payload for room service orders."""
        try:
            if hasattr(order, 'items'):
                return [
                    {
                        'id': item.id,
                        'name': item.menu_item.name if hasattr(item, 'menu_item') else item.name,
                        'quantity': item.quantity,
                        'price': float(item.price),
                        'total': float(item.quantity * item.price)
                    }
                    for item in order.items.all()
                ]
        except Exception as e:
            self.logger.error(f"Error building order items: {e}")
        return []
    
    def _notify_room_service_staff_of_new_order(self, order, event_data):
        """Send FCM + Pusher to porters and kitchen staff for new orders."""
        # Notify porters
        from staff.models import Staff
        porters = Staff.objects.filter(
            hotel=order.hotel,
            role__slug='porter',
            is_active=True
        )
        
        for porter in porters:
            if porter.fcm_token:
                send_porter_order_notification(porter, order)
        
        # Notify kitchen staff
        kitchen_staff = Staff.objects.filter(
            hotel=order.hotel,
            department__slug='kitchen',
            is_active=True
        )
        
        for staff in kitchen_staff:
            if staff.fcm_token:
                send_kitchen_staff_order_notification(staff, order)
    
    def _notify_guest_booking_confirmed(self, booking):
        """Send FCM booking confirmation to guest if token available."""
        guest_fcm_token = None
        if hasattr(booking, 'room') and booking.room and booking.room.guest_fcm_token:
            guest_fcm_token = booking.room.guest_fcm_token
        
        if guest_fcm_token:
            send_booking_confirmation_notification(guest_fcm_token, booking)
    
    def _notify_guest_booking_cancelled(self, booking, reason=None):
        """Send FCM booking cancellation to guest if token available."""
        guest_fcm_token = None
        if hasattr(booking, 'room') and booking.room and booking.room.guest_fcm_token:
            guest_fcm_token = booking.room.guest_fcm_token
            
        if guest_fcm_token:
            send_booking_cancellation_notification(guest_fcm_token, booking, reason)
    
    # =============================================================================
    # EXISTING LEGACY ORDER NOTIFICATIONS (updated to use realtime methods)
    # =============================================================================
    
    def notify_porters_new_room_service_order(self, order):
        """
        Legacy method - now uses realtime method for unified event handling.
        Maintains existing FCM behavior while using new normalized events.
        
        Args:
            order: RoomService order instance
            
        Returns:
            dict: Summary of notification results
        """
        self.logger.info(f"🔔 Notifying porters of new room service order #{order.id} (via realtime)")
        
        results = {
            'fcm_sent': 0,
            'fcm_failed': 0,
            'pusher_sent': 0,
            'pusher_failed': 0,
            'total_porters': 0
        }
        
        # Get all active porters for this hotel
        from staff.models import Staff
        porters = Staff.objects.filter(
            hotel=order.hotel,
            role__slug='porter',
            is_active=True
        ).select_related('user', 'role')
        
        results['total_porters'] = porters.count()
        
        # Send FCM to porters
        for porter in porters:
            if porter.fcm_token:
                fcm_success = send_porter_order_notification(porter, order)
                if fcm_success:
                    results['fcm_sent'] += 1
                else:
                    results['fcm_failed'] += 1
        
        # Use new realtime method for Pusher events
        if self.realtime_room_service_order_created(order):
            results['pusher_sent'] = 1
        else:
            results['pusher_failed'] = 1
        
        self.logger.info(f"📊 Room service notification results: {results}")
        return results
    
    def notify_kitchen_staff_new_order(self, order):
        """Legacy method - maintains existing FCM behavior while using realtime for Pusher."""
        self.logger.info(f"🍳 Notifying kitchen staff of new order #{order.id}")
        
        results = {'fcm_sent': 0, 'fcm_failed': 0, 'pusher_sent': 0}
        
        # Get kitchen staff
        from staff.models import Staff
        kitchen_staff = Staff.objects.filter(
            hotel=order.hotel,
            department__slug='kitchen',
            is_active=True,
            is_on_duty=True
        )
        
        # Send FCM to kitchen staff
        for staff in kitchen_staff:
            if staff.fcm_token:
                fcm_success = send_kitchen_staff_order_notification(staff, order)
                if fcm_success:
                    results['fcm_sent'] += 1
                else:
                    results['fcm_failed'] += 1
        
        # Use realtime method for Pusher (already handled in realtime_room_service_order_created)
        # Maintain compatibility by calling old pusher utils for now
        pusher_count = notify_kitchen_staff(order.hotel, 'new-room-service-order', {
            'id': order.id,
            'room_number': order.room_number,
            'total_price': float(order.total_price),
            'status': order.status
        })
        results['pusher_sent'] = pusher_count
        
        return results
    
    def notify_porters_breakfast_order(self, breakfast_order):
        """Notify porters about new breakfast order."""
        self.logger.info(f"🥐 Notifying porters of breakfast order #{breakfast_order.id}")
        
        results = {'fcm_sent': 0, 'fcm_failed': 0, 'pusher_sent': 0}
        
        from staff.models import Staff
        porters = Staff.objects.filter(
            hotel=breakfast_order.hotel,
            role__slug='porter',
            is_active=True
        )
        
        order_data = {
            'id': breakfast_order.id,
            'room_number': breakfast_order.room_number,
            'delivery_time': str(breakfast_order.delivery_time) if breakfast_order.delivery_time else 'ASAP',
            'status': breakfast_order.status
        }
        
        for porter in porters:
            if porter.fcm_token:
                fcm_success = send_porter_breakfast_notification(porter, breakfast_order)
                if fcm_success:
                    results['fcm_sent'] += 1
                else:
                    results['fcm_failed'] += 1
        
        # Pusher
        pusher_count = notify_porters(breakfast_order.hotel, 'new-breakfast-order', order_data)
        results['pusher_sent'] = pusher_count
        
        return results
    
    # =============================================================================
    # BOOKING NOTIFICATIONS
    # =============================================================================
    
    def notify_guest_booking_confirmed(self, booking):
        """Notify guest about booking confirmation."""
        self.logger.info(f"✅ Notifying guest of booking confirmation {booking.booking_id}")
        
        # Try to get FCM token from room if guest is already checked in
        guest_fcm_token = None
        if hasattr(booking, 'room') and booking.room and booking.room.guest_fcm_token:
            guest_fcm_token = booking.room.guest_fcm_token
        
        results = {'fcm_sent': False, 'pusher_sent': False}
        
        # FCM notification
        if guest_fcm_token:
            results['fcm_sent'] = send_booking_confirmation_notification(guest_fcm_token, booking)
        
        # Pusher notification (if guest is connected to room channel)
        if booking.room_number:
            booking_data = {
                'booking_id': booking.booking_id,
                'confirmation_number': booking.confirmation_number,
                'hotel_name': booking.hotel.name,
                'check_in': str(booking.check_in),
                'check_out': str(booking.check_out),
                'status': 'confirmed'
            }
            results['pusher_sent'] = notify_guest_in_room(
                booking.hotel, booking.room_number, 'booking-confirmed', booking_data
            )
        
        return results
    
    def notify_guest_booking_cancelled(self, booking, reason=None):
        """Notify guest about booking cancellation."""
        self.logger.info(f"❌ Notifying guest of booking cancellation {booking.booking_id}")
        
        guest_fcm_token = None
        if hasattr(booking, 'room') and booking.room and booking.room.guest_fcm_token:
            guest_fcm_token = booking.room.guest_fcm_token
        
        results = {'fcm_sent': False, 'pusher_sent': False}
        
        # FCM notification
        if guest_fcm_token:
            results['fcm_sent'] = send_booking_cancellation_notification(guest_fcm_token, booking, reason)
        
        # Pusher notification
        if booking.room_number:
            cancellation_data = {
                'booking_id': booking.booking_id,
                'hotel_name': booking.hotel.name,
                'reason': reason or 'No reason provided',
                'status': 'cancelled'
            }
            results['pusher_sent'] = notify_guest_in_room(
                booking.hotel, booking.room_number, 'booking-cancelled', cancellation_data
            )
        
        return results
    
    # =============================================================================
    # CHAT/MESSAGE NOTIFICATIONS
    # =============================================================================
    
    def notify_staff_new_guest_message(self, message, assigned_staff_list):
        """
        Notify assigned staff about new guest message.
        Used when guest sends message to hotel staff.
        
        Args:
            message: ChatMessage instance
            assigned_staff_list: List of Staff instances assigned to the room
        """
        self.logger.info(f"💬 Notifying staff of guest message #{message.id}")
        
        results = {'fcm_sent': 0, 'fcm_failed': 0, 'pusher_sent': 0}
        
        message_data = {
            'id': message.id,
            'room_number': message.room.room_number,
            'sender': 'guest',
            'content': message.content[:100],  # Preview
            'timestamp': message.timestamp.isoformat(),
            'conversation_id': message.conversation_id
        }
        
        for staff in assigned_staff_list:
            # FCM notification
            if staff.fcm_token:
                title = f"💬 New Message - Room {message.room.room_number}"
                body = message.content[:100]
                data = {
                    'type': 'guest_message',
                    'message_id': str(message.id),
                    'room_number': str(message.room.room_number),
                    'conversation_id': str(message.conversation_id),
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                    'route': '/chat/room'
                }
                
                fcm_success = send_fcm_notification(staff.fcm_token, title, body, data)
                if fcm_success:
                    results['fcm_sent'] += 1
                else:
                    results['fcm_failed'] += 1
            
            # Pusher notification
            staff_channel = f"{message.room.hotel.slug}-staff-{staff.id}"
            try:
                pusher_client.trigger(staff_channel, "new-guest-message", message_data)
                results['pusher_sent'] += 1
                self.logger.info(f"✅ Pusher sent to staff {staff.id}")
            except Exception as e:
                self.logger.error(f"❌ Pusher failed for staff {staff.id}: {e}")
        
        return results
    
    def notify_guest_staff_reply(self, message):
        """Notify guest about staff reply to their message."""
        self.logger.info(f"💬 Notifying guest of staff reply #{message.id}")
        
        results = {'fcm_sent': False, 'pusher_sent': False}
        
        # FCM to guest (if they have token)
        if message.room.guest_fcm_token:
            title = f"💬 Staff Reply - Room {message.room.room_number}"
            body = message.content[:100]
            data = {
                'type': 'staff_reply',
                'message_id': str(message.id),
                'room_number': str(message.room.room_number),
                'staff_name': f"{message.sender_staff.first_name} {message.sender_staff.last_name}",
                'click_action': 'FLUTTER_NOTIFICATION_CLICK'
            }
            results['fcm_sent'] = send_fcm_notification(message.room.guest_fcm_token, title, body, data)
        
        # Pusher to guest room channel
        guest_channel = f"{message.room.hotel.slug}-room-{message.room.room_number}"
        message_data = {
            'id': message.id,
            'content': message.content,
            'sender_staff_name': f"{message.sender_staff.first_name} {message.sender_staff.last_name}",
            'timestamp': message.timestamp.isoformat()
        }
        
        try:
            pusher_client.trigger(guest_channel, "staff-reply", message_data)
            results['pusher_sent'] = True
            self.logger.info(f"✅ Guest notification sent to room {message.room.room_number}")
        except Exception as e:
            self.logger.error(f"❌ Guest notification failed: {e}")
        
        return results
    
    # =============================================================================
    # ATTENDANCE NOTIFICATIONS
    # =============================================================================
    
    def notify_attendance_status_change(self, staff, action):
        """
        Legacy method - now delegates to realtime attendance method.
        
        Args:
            staff: Staff instance
            action: 'clock_in', 'clock_out', 'start_break', 'end_break'
        """
        self.logger.info(f"⏰ Broadcasting attendance change: {staff.id} - {action} (via realtime)")
        
        # Use the new realtime method
        return self.realtime_attendance_clock_status_updated(staff, action)
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def notify_staff_by_role_and_department(
        self, 
        hotel, 
        role_slug: Optional[str] = None,
        department_slug: Optional[str] = None,
        event: str = "notification",
        data: Dict[str, Any] = None,
        fcm_title: Optional[str] = None,
        fcm_body: Optional[str] = None,
        only_on_duty: bool = True
    ):
        """
        Generic method to notify staff by role and/or department.
        Handles both FCM and Pusher notifications.
        
        Args:
            hotel: Hotel instance
            role_slug: Optional role slug filter
            department_slug: Optional department slug filter
            event: Pusher event name
            data: Event/FCM data payload
            fcm_title: FCM notification title
            fcm_body: FCM notification body
            only_on_duty: Filter to only on-duty staff
        """
        from staff.models import Staff
        
        # Build staff query
        staff_qs = Staff.objects.filter(hotel=hotel, is_active=True)
        
        if role_slug:
            staff_qs = staff_qs.filter(role__slug=role_slug)
        
        if department_slug:
            staff_qs = staff_qs.filter(department__slug=department_slug)
        
        if only_on_duty:
            staff_qs = staff_qs.filter(is_on_duty=True)
        
        results = {'fcm_sent': 0, 'fcm_failed': 0, 'pusher_sent': 0, 'total_staff': 0}
        results['total_staff'] = staff_qs.count()
        
        for staff in staff_qs.select_related('role', 'department'):
            # FCM notification
            if fcm_title and fcm_body and staff.fcm_token:
                fcm_success = send_fcm_notification(staff.fcm_token, fcm_title, fcm_body, data)
                if fcm_success:
                    results['fcm_sent'] += 1
                else:
                    results['fcm_failed'] += 1
            
            # Pusher notification
            role_or_dept = role_slug or department_slug or 'general'
            channel = f"{hotel.slug}-staff-{staff.id}-{role_or_dept}"
            
            try:
                pusher_client.trigger(channel, event, data or {})
                results['pusher_sent'] += 1
                self.logger.info(f"✅ Notification sent to staff {staff.id} ({channel})")
            except Exception as e:
                self.logger.error(f"❌ Failed to notify staff {staff.id}: {e}")
        
        return results
    
    # -------------------------------------------------------------------------
    # ADDITIONAL STAFF CHAT REALTIME METHODS
    # -------------------------------------------------------------------------
    
    def realtime_staff_chat_message_deleted(self, message_id, conversation_id, hotel):
        """Emit normalized staff chat message deleted event."""
        self.logger.info(f"🗑️ Realtime staff chat: message {message_id} deleted")
        
        payload = {
            'conversation_id': conversation_id,
            'message_id': message_id,
            'deleted_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="message_deleted",
            payload=payload,
            hotel=hotel,
            scope={'conversation_id': conversation_id, 'message_id': message_id}
        )
        
        hotel_slug = hotel.slug
        channel = f"hotel-{hotel_slug}.staff-chat.{conversation_id}"
        return self._safe_pusher_trigger(channel, "message-deleted", event_data)
    
    def realtime_staff_chat_typing_indicator(self, staff, conversation_id, is_typing=True):
        """Emit staff chat typing indicator (ephemeral event)."""
        self.logger.info(f"✍️ Realtime staff chat: typing indicator for staff {staff.id}")
        
        # Typing indicators are ephemeral and don't need full normalization
        # Use lightweight payload for performance
        payload = {
            'conversation_id': conversation_id,
            'staff_id': staff.id,
            'staff_name': f"{staff.first_name} {staff.last_name}",
            'is_typing': is_typing,
            'timestamp': timezone.now().isoformat()
        }
        
        hotel_slug = staff.hotel.slug
        channel = f"hotel-{hotel_slug}.staff-chat.{conversation_id}"
        return self._safe_pusher_trigger(channel, "typing", payload)
    
    def realtime_staff_chat_attachment_uploaded(self, attachment, message):
        """Emit staff chat attachment uploaded event."""
        self.logger.info(f"📎 Realtime staff chat: attachment {attachment.id} uploaded")
        
        payload = {
            'conversation_id': message.conversation.id,
            'message_id': message.id,
            'attachment_id': attachment.id,
            'attachment_name': getattr(attachment, 'name', 'Unknown'),
            'attachment_type': getattr(attachment, 'file_type', 'file'),
            'attachment_size': getattr(attachment, 'file_size', 0),
            'uploaded_by_staff_id': message.sender.id,
            'uploaded_by_staff_name': f"{message.sender.first_name} {message.sender.last_name}",
            'uploaded_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="attachment_uploaded",
            payload=payload,
            hotel=message.conversation.hotel if hasattr(message.conversation, 'hotel') else message.sender.hotel,
            scope={'conversation_id': message.conversation.id, 'attachment_id': attachment.id}
        )
        
        hotel_slug = message.sender.hotel.slug
        channel = f"hotel-{hotel_slug}.staff-chat.{message.conversation.id}"
        return self._safe_pusher_trigger(channel, "attachment-uploaded", event_data)
    
    def realtime_staff_chat_attachment_deleted(self, attachment_id, conversation, staff):
        """Emit staff chat attachment deleted event."""
        self.logger.info(f"🗑️ Realtime staff chat: attachment {attachment_id} deleted")
        
        payload = {
            'conversation_id': conversation.id,
            'attachment_id': attachment_id,
            'deleted_by_staff_id': staff.id,
            'deleted_by_staff_name': f"{staff.first_name} {staff.last_name}",
            'deleted_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="attachment_deleted",
            payload=payload,
            hotel=conversation.hotel if hasattr(conversation, 'hotel') else staff.hotel,
            scope={'conversation_id': conversation.id, 'attachment_id': attachment_id}
        )
        
        hotel_slug = staff.hotel.slug
        channel = f"hotel-{hotel_slug}.staff-chat.{conversation.id}"
        return self._safe_pusher_trigger(channel, "attachment-deleted", event_data)
    
    def realtime_staff_chat_mention(self, staff, message, conversation_id):
        """Emit staff chat mention notification."""
        self.logger.info(f"📢 Realtime staff chat: mention for staff {staff.id}")
        
        payload = {
            'conversation_id': conversation_id,
            'message_id': message.id,
            'mentioned_staff_id': staff.id,
            'mentioned_staff_name': f"{staff.first_name} {staff.last_name}",
            'sender_id': message.sender.id,
            'sender_name': f"{message.sender.first_name} {message.sender.last_name}",
            'text': message.text,
            'created_at': message.created_at.isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="staff_mentioned",
            payload=payload,
            hotel=staff.hotel,
            scope={'mentioned_staff_id': staff.id, 'conversation_id': conversation_id}
        )
        
        # Send to staff's personal notification channel
        hotel_slug = staff.hotel.slug
        channel = f"hotel-{hotel_slug}.staff-{staff.id}-notifications"
        return self._safe_pusher_trigger(channel, "mentioned", event_data)
    
    def realtime_staff_chat_message_read(self, conversation, staff, message_ids):
        """Emit staff chat message read receipt event."""
        self.logger.info(f"👀 Realtime staff chat: messages read by staff {staff.id}")
        
        payload = {
            'conversation_id': conversation.id,
            'message_ids': message_ids,
            'read_by_staff_id': staff.id,
            'read_by_staff_name': f"{staff.first_name} {staff.last_name}",
            'read_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="messages_read",
            payload=payload,
            hotel=conversation.hotel if hasattr(conversation, 'hotel') else staff.hotel,
            scope={'conversation_id': conversation.id, 'read_by_staff_id': staff.id}
        )
        
        # Send to conversation channel
        hotel_slug = staff.hotel.slug
        channel = f"hotel-{hotel_slug}.staff-chat.{conversation.id}"
        return self._safe_pusher_trigger(channel, "messages-read", event_data)
    
    def realtime_staff_chat_message_delivered(self, message, staff):
        """Emit staff chat message delivered status event."""
        self.logger.info(f"📬 Realtime staff chat: message {message.id} delivered to staff {staff.id}")
        
        payload = {
            'conversation_id': message.conversation.id,
            'message_id': message.id,
            'delivered_to_staff_id': staff.id,
            'delivered_to_staff_name': f"{staff.first_name} {staff.last_name}",
            'delivered_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="message_delivered",
            payload=payload,
            hotel=message.conversation.hotel if hasattr(message.conversation, 'hotel') else staff.hotel,
            scope={'conversation_id': message.conversation.id, 'message_id': message.id, 'delivered_to_staff_id': staff.id}
        )
        
        # Send to conversation channel
        hotel_slug = staff.hotel.slug
        channel = f"hotel-{hotel_slug}.staff-chat.{message.conversation.id}"
        return self._safe_pusher_trigger(channel, "message-delivered", event_data)

    def get_notification_summary(self):
        """Get summary of notification capabilities and configuration."""
        return {
            'fcm_enabled': hasattr(settings, 'FIREBASE_SERVICE_ACCOUNT_JSON') and settings.FIREBASE_SERVICE_ACCOUNT_JSON,
            'pusher_enabled': hasattr(settings, 'PUSHER_APP_ID') and settings.PUSHER_APP_ID,
            'supported_events': [
                'room_service_orders', 'breakfast_orders', 'booking_confirmations',
                'booking_cancellations', 'guest_messages', 'staff_replies',
                'attendance_changes', 'department_notifications', 'role_notifications'
            ],
            'supported_roles': ['porter', 'receptionist', 'kitchen', 'maintenance', 'room_service_waiter'],
            'supported_departments': ['kitchen', 'front-office', 'maintenance', 'housekeeping', 'food-and-beverage']
        }


# =============================================================================
# CONVENIENCE FUNCTIONS FOR BACKWARD COMPATIBILITY
# =============================================================================

# Global instance for easy access
_notification_manager = NotificationManager()

def notify_porters_of_room_service_order(order):
    """Backward compatibility function."""
    return _notification_manager.notify_porters_new_room_service_order(order)

def notify_kitchen_staff_of_room_service_order(order):
    """Backward compatibility function."""
    return _notification_manager.notify_kitchen_staff_new_order(order)

def notify_porters_of_breakfast_order(order):
    """Backward compatibility function."""
    return _notification_manager.notify_porters_breakfast_order(order)

def notify_staff_new_message(message, staff_list):
    """Backward compatibility function."""
    return _notification_manager.notify_staff_new_guest_message(message, staff_list)

def notify_guest_reply(message):
    """Backward compatibility function."""
    return _notification_manager.notify_guest_staff_reply(message)

def notify_attendance_change(staff, action):
    """Backward compatibility function."""
    return _notification_manager.realtime_attendance_clock_status_updated(staff, action)

# Export the manager instance for direct use
notification_manager = _notification_manager