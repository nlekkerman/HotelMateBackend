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
            print(f"🚨 ACTUALLY SENDING PUSHER EVENT: Channel={channel}, Event={event}", flush=True)
            pusher_client.trigger(channel, event, data)
            print(f"✅ Pusher event CONFIRMED SENT: {channel} → {event}", flush=True)
            self.logger.info(f"✅ Pusher event sent: {channel} → {event}")
            return True
        except Exception as e:
            print(f"❌ Pusher FAILED: {channel} → {event}: {e}", flush=True)
            self.logger.error(f"❌ Pusher failed: {channel} → {event}: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # GUEST BOOKING REALTIME METHODS
    # -------------------------------------------------------------------------
    
    def realtime_guest_booking_payment_required(self, booking, reason="Hotel accepted booking"):
        """
        Emit guest-scoped event when payment is required for booking.
        
        Args:
            booking: RoomBooking instance
            reason: Why payment is required
        """
        normalized_event = self._create_normalized_event(
            category="room_booking",
            type="booking_payment_required",
            payload={
                "booking_id": booking.booking_id,
                "status": "PENDING_PAYMENT",
                "payment_required": True,
                "reason": reason,
                "hotel_name": booking.hotel.name,
                "hotel_phone": booking.hotel.phone or "",
            },
            scope={
                "type": "guest_booking",
                "booking_id": booking.booking_id
            }
        )
        
        # Emit to guest booking channel
        channel = f"private-guest-booking.{booking.booking_id}"
        return self._safe_pusher_trigger(channel, "booking_payment_required", normalized_event)
    
    def realtime_guest_booking_confirmed(self, booking, confirmed_at=None):
        """
        Emit guest-scoped event when booking is confirmed.
        
        Args:
            booking: RoomBooking instance  
            confirmed_at: When booking was confirmed (defaults to now)
        """
        if not confirmed_at:
            confirmed_at = timezone.now()
            
        normalized_event = self._create_normalized_event(
            category="room_booking",
            type="booking_confirmed",
            payload={
                "booking_id": booking.booking_id,
                "status": "CONFIRMED",
                "confirmed_at": confirmed_at.isoformat(),
                "hotel_name": booking.hotel.name,
                "hotel_phone": booking.hotel.phone or "",
            },
            scope={
                "type": "guest_booking",
                "booking_id": booking.booking_id
            }
        )
        
        # Emit to guest booking channel
        channel = f"private-guest-booking.{booking.booking_id}"
        return self._safe_pusher_trigger(channel, "booking_confirmed", normalized_event)
    
    def realtime_guest_booking_cancelled(self, booking, cancelled_at=None, cancellation_reason=""):
        """
        Emit guest-scoped event when booking is cancelled.
        
        Args:
            booking: RoomBooking instance
            cancelled_at: When booking was cancelled (defaults to now)
            cancellation_reason: Reason for cancellation
        """
        if not cancelled_at:
            cancelled_at = timezone.now()
            
        normalized_event = self._create_normalized_event(
            category="room_booking",
            type="booking_cancelled", 
            payload={
                "booking_id": booking.booking_id,
                "status": "CANCELLED",
                "cancelled_at": cancelled_at.isoformat(),
                "cancellation_reason": cancellation_reason,
                "hotel_name": booking.hotel.name,
                "hotel_phone": booking.hotel.phone or "",
            },
            scope={
                "type": "guest_booking",
                "booking_id": booking.booking_id
            }
        )
        
        # Emit to guest booking channel
        channel = f"private-guest-booking.{booking.booking_id}"
        return self._safe_pusher_trigger(channel, "booking_cancelled", normalized_event)
    
    def realtime_guest_booking_checked_in(self, booking, room_number=None):
        """
        Emit guest-scoped event when booking is checked in.
        Uses the same PublicRoomBookingDetailSerializer to ensure consistency.
        
        Args:
            booking: RoomBooking instance
            room_number: Room number (optional, derived from booking if not provided)
        """
        from hotel.booking_serializers import PublicRoomBookingDetailSerializer
        
        # Use the same serializer that generates the API response
        serializer = PublicRoomBookingDetailSerializer(booking)
        booking_data = serializer.data.copy()
        
        # Override status to CHECKED_IN and add check-in timestamp
        booking_data["status"] = "CHECKED_IN"
        booking_data["checked_in_at"] = booking.checked_in_at.isoformat() if booking.checked_in_at else timezone.now().isoformat()
        
        # Add room number if checked in
        if room_number or booking.assigned_room:
            room_num = room_number or booking.assigned_room.room_number
            booking_data["room"]["number"] = room_num
            if booking.assigned_room:
                booking_data["room"]["floor"] = booking.assigned_room.floor
        
        print(f"🔄 Guest check-in payload: status={booking_data['status']}, room_number={booking_data.get('room', {}).get('number')}")
        
        normalized_event = self._create_normalized_event(
            category="room_booking",
            type="booking_checked_in",
            payload=booking_data,
            scope={
                "type": "guest_booking",
                "booking_id": booking.booking_id
            }
        )
        
        # Emit to guest booking channel
        channel = f"private-guest-booking.{booking.booking_id}"
        print(f"🔄 Emitting to channel: {channel}")
        result = self._safe_pusher_trigger(channel, "booking_checked_in", normalized_event)
        print(f"✅ Pusher trigger result: {result}")
        return result
    
    def realtime_guest_booking_checked_out(self, booking, room_number=None):
        """
        Emit guest-scoped event when booking is checked out.
        
        Args:
            booking: RoomBooking instance
            room_number: Room number (optional, derived from booking if not provided)
        """
        room_num = room_number or (booking.assigned_room.room_number if booking.assigned_room else None)
        
        normalized_event = self._create_normalized_event(
            category="room_booking",
            type="booking_checked_out",
            payload={
                "booking_id": booking.booking_id,
                "status": "COMPLETED",
                "checked_out_at": booking.checked_out_at.isoformat() if booking.checked_out_at else timezone.now().isoformat(),
                "room_number": room_num,
                "hotel_name": booking.hotel.name,
                "hotel_phone": booking.hotel.phone or "",
            },
            scope={
                "type": "guest_booking",
                "booking_id": booking.booking_id
            }
        )
        
        # Emit to guest booking channel
        channel = f"private-guest-booking.{booking.booking_id}"
        return self._safe_pusher_trigger(channel, "booking_checked_out", normalized_event)
    
    def realtime_guest_booking_room_assigned(self, booking, room_number=None):
        """
        Emit guest-scoped event when room is assigned to booking.
        
        Args:
            booking: RoomBooking instance
            room_number: Room number (optional, derived from booking if not provided)
        """
        room_num = room_number or (booking.assigned_room.room_number if booking.assigned_room else None)
        room = booking.assigned_room
        
        normalized_event = self._create_normalized_event(
            category="room_booking",
            type="booking_room_assigned",
            payload={
                "booking_id": booking.booking_id,
                "status": booking.status,
                "room_number": room_num,
                "room_type": room.room_type.name if room and room.room_type else None,
                "room_floor": room.floor if room else None,
                "room_assigned_at": booking.room_assigned_at.isoformat() if booking.room_assigned_at else timezone.now().isoformat(),
                "expected_checkin_date": booking.check_in_date.isoformat(),
                "expected_checkout_date": booking.check_out_date.isoformat(),
                "guest_name": booking.primary_guest_name,
                "party_size": booking.party_size,
                "hotel": {
                    "name": booking.hotel.name,
                    "phone": booking.hotel.phone or "",
                    "address": booking.hotel.address or "",
                    "city": booking.hotel.city or "",
                },
            },
            scope={
                "type": "guest_booking",
                "booking_id": booking.booking_id
            }
        )
        
        # Emit to guest booking channel
        channel = f"private-guest-booking.{booking.booking_id}"
        return self._safe_pusher_trigger(channel, "booking_room_assigned", normalized_event)
    
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
        channel = f"{staff.hotel.slug}.attendance"
        return self._safe_pusher_trigger(channel, "clock_status_updated", event_data)
    
    # -------------------------------------------------------------------------
    # STAFF CHAT REALTIME METHODS
    # -------------------------------------------------------------------------
    
    def realtime_staff_chat_message_created(self, message):
        """
        Emit normalized staff chat message created event.
        Enhanced with reply-to-attachment detection and specialized notifications.
        
        Args:
            message: Staff chat message instance
        """
        self.logger.info(f"💬 Realtime staff chat: message {message.id} created by staff {message.sender.id}")
        
        # Build image list for frontend display (images only)
        try:
            image_list = []
            if hasattr(message, 'attachments'):
                # Filter for images only
                for img in message.attachments.filter(file_type='image'):
                    img_data = {
                        'id': img.id,
                        'file_name': img.file_name,
                        'file_type': 'image',
                    }
                    # Get the Cloudinary image URL with multiple field variants
                    if hasattr(img, 'file') and img.file:
                        url = img.file.url
                        img_data['image_url'] = url
                        img_data['thumbnail_url'] = url
                        img_data['file_url'] = url  # Legacy compatibility
                        img_data['url'] = url  # Generic URL field
                    
                    image_list.append(img_data)
                    
                self.logger.info(f"🖼️ Built image list with {len(image_list)} items")
        except Exception as e:
            self.logger.error(f"Error building image list: {e}")
            image_list = []
        
        # Enhanced reply-to-attachment detection and data
        reply_to_data = None
        is_reply_to_attachment = False
        original_attachment_previews = []
        
        if message.reply_to:
            try:
                original_message = message.reply_to
                self.logger.info(f"🔗 Processing reply to message {original_message.id}")
                
                # Check if original message has image attachments (only handle images)
                if hasattr(original_message, 'attachments') and original_message.attachments.exists():
                    # Filter for images only
                    image_attachments = original_message.attachments.filter(file_type='image')
                    
                    if image_attachments.exists():
                        is_reply_to_attachment = True
                        self.logger.info(f"🖼️ Reply targets message with {image_attachments.count()} images")
                            
                        # Build image previews (limit to first 3 for performance)
                        for img in image_attachments[:3]:
                            preview_data = {
                                'id': img.id,
                                'file_name': img.file_name,
                                'file_type': 'image',
                                'is_image': True,
                            }
                            
                            # Add image URLs with multiple field variants
                            if hasattr(img, 'file') and img.file:
                                url = img.file.url
                                preview_data['image_url'] = url
                                preview_data['thumbnail_url'] = url
                                preview_data['file_url'] = url  # Legacy compatibility
                                preview_data['url'] = url  # Generic URL field
                            else:
                                self.logger.warning(f"⚠️ Image {img.id} has no file attribute")
                                
                            original_attachment_previews.append(preview_data)
                        else:
                            self.logger.info("🔍 No image attachments found (only non-image attachments)")
                    else:
                        self.logger.info("🔍 Original message has no attachments")
                else:
                    self.logger.warning("⚠️ Original message does not have attachments attribute")
                
                # Get original sender avatar
                original_sender_avatar = None
                if original_message.sender.profile_image and hasattr(original_message.sender.profile_image, 'url'):
                    original_sender_avatar = original_message.sender.profile_image.url
                
                # Build reply_to_data for images and text only
                original_message_text = original_message.message or ""
                
                reply_to_data = {
                    'id': original_message.id,
                    'message': original_message_text,  # Full text message content
                    'message_preview': original_message_text[:150] + ('...' if len(original_message_text) > 150 else ''),  # Text preview
                    'sender_id': original_message.sender.id,
                    'sender_name': f"{original_message.sender.first_name} {original_message.sender.last_name}",
                    'sender_avatar': original_sender_avatar,  # Include original sender's avatar
                    'timestamp': original_message.timestamp.isoformat(),
                    'is_deleted': getattr(original_message, 'is_deleted', False),
                    'is_edited': getattr(original_message, 'is_edited', False),
                    # New format (images only)
                    'has_images': is_reply_to_attachment,
                    'images': original_attachment_previews,
                    'image_count': len(original_attachment_previews),
                    # Legacy format for backward compatibility
                    'has_attachments': is_reply_to_attachment,
                    'attachments_preview': original_attachment_previews,
                    'attachment_count': len(original_attachment_previews)
                }
                
                self.logger.info(f"🔗 Built reply_to_data with {len(original_attachment_previews)} images")
                
            except Exception as e:
                self.logger.error(f"Error processing reply-to data: {e}")
                error_message = 'Error loading original message'
                reply_to_data = {
                    'id': message.reply_to.id,
                    'message': error_message,
                    'message_preview': error_message,
                    'sender_id': message.reply_to.sender.id if message.reply_to.sender else None,
                    'sender_name': 'Unknown User',
                    'sender_avatar': None,
                    'timestamp': None,
                    'is_deleted': True,  # Treat error as deleted for UI purposes
                    'is_edited': False,
                    # New format
                    'has_images': False,
                    'images': [],
                    'image_count': 0,
                    # Legacy format for backward compatibility
                    'has_attachments': False,
                    'attachments_preview': [],
                    'attachment_count': 0
                }
        
        # Get sender avatar URL
        sender_avatar_url = None
        if message.sender.profile_image and hasattr(message.sender.profile_image, 'url'):
            sender_avatar_url = message.sender.profile_image.url
        
        payload = {
            'id': message.id,  # Frontend expects 'id', not 'message_id'
            'conversation_id': message.conversation.id,
            'message': message.message,  # Match serializer field name: 'message'
            'sender_id': message.sender.id,
            'sender_name': message.sender.get_full_name() if hasattr(message.sender, 'get_full_name') else f"{message.sender.first_name} {message.sender.last_name}",
            'sender_avatar': sender_avatar_url,  # Include sender's profile image URL
            'timestamp': message.timestamp.isoformat(),  # Correct field name: 'timestamp' not 'created_at'
            # New format (images only)
            'images': image_list,
            'has_images': bool(image_list),
            'image_count': len(image_list),
            # Legacy format for backward compatibility
            'attachments': image_list,  # Same data, different field name
            'has_attachments': bool(image_list),
            'attachment_count': len(image_list),
            'is_system_message': getattr(message, 'is_system_message', False),
            'reply_to': reply_to_data,
            'is_reply_to_attachment': is_reply_to_attachment
        }
        
        # Create normalized event
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="realtime_staff_chat_message_created", 
            payload=payload,
            hotel=message.conversation.hotel if hasattr(message.conversation, 'hotel') else message.sender.hotel,
            scope={'conversation_id': message.conversation.id, 'sender_id': message.sender.id}
        )
        
        # Send to conversation channel with correct event name for frontend eventBus
        hotel_slug = message.sender.hotel.slug
        conversation_channel = f"{hotel_slug}.staff-chat.{message.conversation.id}"
        
        # Send to conversation channel (for message display)
        
        self.logger.info(f"🔥 PUSHER DEBUG: Sending to conversation channel: {conversation_channel}")
        self.logger.info(f"🔥 PUSHER DEBUG: Event data: {event_data}")
        conversation_sent = self._safe_pusher_trigger(conversation_channel, "realtime_staff_chat_message_created", event_data)
        
        # Send to all participants' notification channels (for unread count updates)
        notification_sent = 0
        participants = list(message.conversation.participants.exclude(id=message.sender.id))
        self.logger.info(f"🔥 PUSHER DEBUG: Found {len(participants)} participants to notify")
        
        for participant in participants:
            notification_channel = f"{hotel_slug}.staff-{participant.id}-notifications"
            
            # FCM is handled by staff_chat/fcm_utils.py, not here
            
            # Get current unread count for this conversation
            current_unread_count = message.conversation.get_unread_count_for_staff(participant) if hasattr(message.conversation, 'get_unread_count_for_staff') else 1
            
            # Check if this is creating a new conversation with unread messages (was 0, now > 0)
            # This happens when current count is 1 (meaning this is the first unread message in this conversation for this participant)
            is_new_conversation_with_unread = current_unread_count == 1
            
            # Create separate unread update event
            unread_payload = {
                'staff_id': participant.id,
                'conversation_id': message.conversation.id,
                'unread_count': current_unread_count,
                'updated_at': timezone.now().isoformat()
            }
            
            unread_event_data = self._create_normalized_event(
                category="staff_chat",
                event_type="realtime_staff_chat_unread_updated",
                payload=unread_payload,
                hotel=message.sender.hotel,
                scope={'staff_id': participant.id, 'conversation_id': message.conversation.id}
            )
            
            print(f"🔥 PUSHER DEBUG: Sending unread update to participant {participant.id} on channel: {notification_channel}", flush=True)
            print(f"🔥 PUSHER DEBUG: Unread event name: realtime_staff_chat_unread_updated", flush=True)
            print(f"🔥 PUSHER DEBUG: Unread count: {unread_payload['unread_count']}", flush=True)
            
            self.logger.info(f"🔥 PUSHER DEBUG: Sending unread update to participant {participant.id} on channel: {notification_channel}")
            if self._safe_pusher_trigger(notification_channel, "realtime_staff_chat_unread_updated", unread_event_data):
                notification_sent += 1
                
                # Send conversation count update only if this is a new conversation with unread messages
                if is_new_conversation_with_unread:
                    print(f"🔥 PUSHER DEBUG: Sending conversation count update for NEW conversation with unread to participant {participant.id}", flush=True)
                    self.logger.info(f"🔥 PUSHER DEBUG: Sending conversation count update for participant {participant.id} - new conversation with unread")
                    self.realtime_staff_chat_conversations_with_unread(participant)
        
        self.logger.info(f"🔥 PUSHER DEBUG: Final results - conversation={conversation_sent}, notifications={notification_sent}")
        return conversation_sent and notification_sent > 0
    
    def realtime_staff_chat_message_edited(self, message):
        """Emit normalized staff chat message edited event."""
        self.logger.info(f"✏️ Realtime staff chat: message {message.id} edited")
        
        # Get sender avatar URL
        sender_avatar_url = None
        if message.sender.profile_image and hasattr(message.sender.profile_image, 'url'):
            sender_avatar_url = message.sender.profile_image.url
        
        payload = {
            'id': message.id,  # Frontend expects 'id', not 'message_id'
            'conversation_id': message.conversation.id,
            'message': message.message,  # Match serializer field name: 'message'
            'sender_id': message.sender.id,
            'sender_name': message.sender.get_full_name() if hasattr(message.sender, 'get_full_name') else f"{message.sender.first_name} {message.sender.last_name}",
            'sender_avatar': sender_avatar_url,  # Include sender's profile image URL
            'timestamp': message.timestamp.isoformat(),  # Correct field name: 'timestamp' not 'created_at'
            'updated_at': message.edited_at.isoformat() if hasattr(message, 'edited_at') and message.edited_at else timezone.now().isoformat(),
            'edited': True
        }
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="realtime_staff_chat_message_edited",
            payload=payload,
            hotel=message.sender.hotel,
            scope={'conversation_id': message.conversation.id, 'sender_id': message.sender.id}
        )
        
        hotel_slug = message.sender.hotel.slug
        channel = f"{hotel_slug}.staff-chat.{message.conversation.id}"
        return self._safe_pusher_trigger(channel, "realtime_staff_chat_message_edited", event_data)
    
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
            'id': message.id,  # Match serializer field name: 'id'
            'sender_role': sender_role,
            'sender_id': sender_id,
            'sender_name': sender_name,
            'message': message.message,  # Match serializer field name: 'message'
            'timestamp': message.timestamp.isoformat(),  # Match serializer field name: 'timestamp'
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
        channel = f"{hotel_slug}.guest-chat.{room_pin}"
        
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
        
        return self._safe_pusher_trigger(channel, "message_created", event_data)
    
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
        channel = f"{hotel_slug}.guest-chat.{room_pin}"
        
        return self._safe_pusher_trigger(channel, "unread_updated", event_data)
    
    def realtime_staff_chat_unread_updated(self, staff, conversation=None, unread_count=None):
        """Emit normalized staff chat unread count update event."""
        self.logger.info(f"🔢 Realtime staff chat: unread updated for staff {staff.id}")
        
        # Always calculate BOTH conversation-specific AND total unread counts for consistency
        from staff_chat.models import StaffConversation
        
        # Get conversation-specific unread count
        conversation_unread = 0
        if conversation:
            conversation_unread = conversation.get_unread_count_for_staff(staff)
            if unread_count is None:
                unread_count = conversation_unread
        
        # ALWAYS calculate total unread across all conversations for consistency
        all_conversations = StaffConversation.objects.filter(participants=staff)
        total_unread_calculated = sum(conv.get_unread_count_for_staff(staff) for conv in all_conversations)
        
        # If no specific conversation, use the total
        if conversation is None and unread_count is None:
            unread_count = total_unread_calculated
        
        # Enhanced payload with explicit counts to prevent frontend confusion
        payload = {
            'staff_id': staff.id,
            'conversation_id': conversation.id if conversation else None,
            'unread_count': unread_count,  # Specific to this conversation OR total if no conversation
            'conversation_unread': conversation_unread,  # Always the conversation-specific count
            'total_unread': total_unread_calculated,  # Always the total across all conversations
            'is_total_update': conversation is None,  # Flag to indicate if this is a total count update
            'updated_at': timezone.now().isoformat(),
            'debug_info': {
                'conversation_provided': conversation is not None,
                'unread_count_provided': unread_count is not None,
                'calculation_source': 'conversation' if conversation else 'total'
            }
        }
        
        # Debug logging for troubleshooting
        self.logger.info(f"🔢 Pusher unread payload: staff={staff.id}, conv={conversation.id if conversation else 'ALL'}, conv_unread={conversation_unread}, total_unread={total_unread_calculated}")
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="realtime_staff_chat_unread_updated",
            payload=payload,
            hotel=staff.hotel,
            scope={'staff_id': staff.id, 'conversation_id': conversation.id if conversation else None}
        )
        
        # Send to staff's personal notification channel
        hotel_slug = staff.hotel.slug
        channel = f"{hotel_slug}.staff-{staff.id}-notifications"
        return self._safe_pusher_trigger(channel, "realtime_staff_chat_unread_updated", event_data)
    
    def realtime_staff_chat_conversations_with_unread(self, staff):
        """Emit normalized staff chat conversations with unread count event."""
        self.logger.info(f"🔢 Realtime staff chat: conversations with unread for staff {staff.id}")
        
        # Calculate number of conversations that have unread messages for this staff
        from staff_chat.models import StaffConversation
        
        all_conversations = StaffConversation.objects.filter(participants=staff)
        conversations_with_unread = sum(1 for conv in all_conversations if conv.get_unread_count_for_staff(staff) > 0)
        
        # Build payload for frontend conversation count badge
        payload = {
            'staff_id': staff.id,
            'conversations_with_unread': conversations_with_unread,
            'updated_at': timezone.now().isoformat()
        }
        
        # Debug logging for troubleshooting
        self.logger.info(f"🔢 Pusher conversations payload: staff={staff.id}, conversations_with_unread={conversations_with_unread}")
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="realtime_staff_chat_conversations_with_unread",
            payload=payload,
            hotel=staff.hotel,
            scope={'staff_id': staff.id}
        )
        
        # Send to staff's personal notification channel
        hotel_slug = staff.hotel.slug
        channel = f"{hotel_slug}.staff-{staff.id}-notifications"
        return self._safe_pusher_trigger(channel, "realtime_staff_chat_conversations_with_unread", event_data)
    
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
        channel = f"{hotel_slug}.room-service"
        
        # Send FCM + Pusher to relevant staff
        self._notify_room_service_staff_of_new_order(order, event_data)
        
        return self._safe_pusher_trigger(channel, "order_created", event_data)
    
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
        channel = f"{hotel_slug}.room-service"
        return self._safe_pusher_trigger(channel, "order_updated", event_data)
    
    def realtime_menu_item_updated(self, hotel, menu_type: str, item_data: dict, action: str):
        """Emit normalized menu item update event for staff dashboards."""
        self.logger.info(f"🍽️ Realtime menu: {menu_type} item {item_data.get('name')} {action}")
        
        payload = {
            'menu_type': menu_type,  # 'room_service' or 'breakfast'
            'item_id': item_data.get('id'),
            'name': item_data.get('name'),
            'category': item_data.get('category'),
            'price': item_data.get('price'),  # Only for room service
            'quantity': item_data.get('quantity'),  # Only for breakfast
            'is_on_stock': item_data.get('is_on_stock'),
            'action': action  # 'created', 'updated', 'deleted'
        }
        
        event_data = self._create_normalized_event(
            category="menu_management",
            event_type="menu_item_updated",
            payload=payload,
            hotel=hotel,
            scope={'menu_type': menu_type, 'item_id': item_data.get('id')}
        )
        
        # Send to staff management channel for real-time dashboard updates
        hotel_slug = hotel.slug
        channel = f"{hotel_slug}.staff-menu-management"
        
        return self._safe_pusher_trigger(channel, "menu_item_updated", event_data)
    
    # -------------------------------------------------------------------------
    # BOOKING REALTIME METHODS
    # -------------------------------------------------------------------------
    
    def realtime_booking_created(self, booking):
        """Emit normalized booking created event."""
        self.logger.info(f"🏨 Realtime booking: {booking.booking_id} created")
        
        payload = {
            'booking_id': booking.booking_id,
            'confirmation_number': getattr(booking, 'confirmation_number', None),
            'primary_guest_name': f"{booking.primary_first_name} {booking.primary_last_name}",
            'primary_email': booking.primary_email,
            'primary_phone': getattr(booking, 'primary_phone', ''),
            'booker_type': getattr(booking, 'booker_type', 'SELF'),
            'room_type': str(booking.room_type) if booking.room_type else None,
            'check_in': booking.check_in.isoformat(),
            'check_out': booking.check_out.isoformat(),
            'nights': (booking.check_out - booking.check_in).days,
            'total_amount': float(getattr(booking, 'total_amount', 0)),
            'status': getattr(booking, 'status', 'PENDING_PAYMENT'),
            'created_at': booking.created_at.isoformat() if hasattr(booking, 'created_at') else timezone.now().isoformat(),
            'special_requests': getattr(booking, 'special_requests', ''),
            'adults': getattr(booking, 'adults', 1),
            'children': getattr(booking, 'children', 0)
        }
        
        event_data = self._create_normalized_event(
            category="room_booking",
            event_type="booking_created",
            payload=payload,
            hotel=booking.hotel,
            scope={'booking_id': booking.booking_id, 'primary_email': booking.primary_email}
        )
        
        # Send to room booking channel
        hotel_slug = booking.hotel.slug
        channel = self._room_booking_channel(hotel_slug)
        
        # NOTE: Don't send guest confirmation here - booking may still be PENDING_PAYMENT
        # Guest confirmation should only be sent when booking is actually confirmed
        
        return self._safe_pusher_trigger(channel, "booking_created", event_data)
    
    def realtime_booking_updated(self, booking):
        """Emit normalized booking updated event."""
        self.logger.info(f"🔄 Realtime booking: {booking.booking_id} updated")
        
        payload = {
            'booking_id': booking.booking_id,
            'confirmation_number': getattr(booking, 'confirmation_number', None),
            'primary_guest_name': f"{booking.primary_first_name} {booking.primary_last_name}",
            'assigned_room_number': booking.assigned_room.room_number if booking.assigned_room else None,
            'check_in': booking.check_in.isoformat(),
            'check_out': booking.check_out.isoformat(),
            'status': getattr(booking, 'status', 'CONFIRMED'),
            'updated_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="room_booking",
            event_type="booking_updated",
            payload=payload,
            hotel=booking.hotel,
            scope={'booking_id': booking.booking_id, 'status': payload['status']}
        )
        
        hotel_slug = booking.hotel.slug
        channel = self._room_booking_channel(hotel_slug)
        return self._safe_pusher_trigger(channel, "booking_updated", event_data)
    
    def realtime_booking_confirmed(self, booking):
        """Emit normalized booking confirmed event when payment is actually confirmed."""
        self.logger.info(f"✅ Realtime booking: {booking.booking_id} confirmed")
        
        payload = {
            'booking_id': booking.booking_id,
            'confirmation_number': getattr(booking, 'confirmation_number', None),
            'primary_guest_name': f"{booking.primary_first_name} {booking.primary_last_name}",
            'primary_email': booking.primary_email,
            'room_type': str(booking.room_type) if booking.room_type else None,
            'assigned_room_number': booking.assigned_room.room_number if booking.assigned_room else None,
            'check_in': booking.check_in.isoformat(),
            'check_out': booking.check_out.isoformat(),
            'nights': (booking.check_out - booking.check_in).days,
            'total_amount': float(getattr(booking, 'total_amount', 0)),
            'status': 'CONFIRMED',
            'confirmed_at': timezone.now().isoformat(),
            'adults': getattr(booking, 'adults', 1),
            'children': getattr(booking, 'children', 0)
        }
        
        event_data = self._create_normalized_event(
            category="room_booking",
            event_type="booking_confirmed",
            payload=payload,
            hotel=booking.hotel,
            scope={'booking_id': booking.booking_id, 'primary_email': booking.primary_email}
        )
        
        # Send FCM confirmation to guest (now it's actually confirmed)
        self._notify_guest_booking_confirmed(booking)
        
        hotel_slug = booking.hotel.slug
        channel = self._room_booking_channel(hotel_slug)
        return self._safe_pusher_trigger(channel, "booking_confirmed", event_data)
    
    def realtime_booking_party_updated(self, booking, party_members=None):
        """
        Emit normalized booking party updated event.
        
        Args:
            booking: RoomBooking instance
            party_members: Optional QuerySet or list of BookingGuest instances (deprecated - will fetch from booking)
        """
        self.logger.info(f"👥 Realtime booking party: {booking.booking_id} updated")
        
        # Use canonical serializer for consistent output
        from hotel.canonical_serializers import BookingPartyGroupedSerializer
        serializer = BookingPartyGroupedSerializer()
        party_data = serializer.to_representation(booking)
        
        payload = {
            'booking_id': booking.booking_id,
            'confirmation_number': getattr(booking, 'confirmation_number', None),
            'status': booking.status,
            'assigned_room_number': booking.assigned_room.room_number if booking.assigned_room else None,
            **party_data,
            'updated_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="room_booking",
            event_type="booking_party_updated", 
            payload=payload,
            hotel=booking.hotel,
            scope={'booking_id': booking.booking_id}
        )
        
        hotel_slug = booking.hotel.slug
        channel = self._room_booking_channel(hotel_slug)
        return self._safe_pusher_trigger(channel, "booking_party_updated", event_data)
    
    def realtime_booking_cancelled(self, booking, reason=None):
        """Emit normalized booking cancelled event AFTER database commit."""
        from django.db import transaction
        
        def emit_cancellation_event():
            self.logger.info(f"❌ Realtime booking: {booking.booking_id} cancelled")
            
            payload = {
                'booking_id': booking.booking_id,
                'confirmation_number': getattr(booking, 'confirmation_number', None),
                'guest_name': f"{booking.primary_first_name} {booking.primary_last_name}",
                'room': booking.room_number if hasattr(booking, 'room_number') else None,
                'assigned_room_number': booking.assigned_room.room_number if booking.assigned_room else None,
                'check_in': booking.check_in.isoformat(),
                'check_out': booking.check_out.isoformat(),
                'status': 'CANCELLED',
                'cancellation_reason': reason or 'No reason provided',
                'cancelled_at': timezone.now().isoformat()
            }
            
            event_data = self._create_normalized_event(
                category="room_booking",
                event_type="booking_cancelled",
                payload=payload,
                hotel=booking.hotel,
                scope={'booking_id': booking.booking_id, 'reason': reason}
            )
            
            # Send FCM cancellation to guest
            self._notify_guest_booking_cancelled(booking, reason)
            
            hotel_slug = booking.hotel.slug
            channel = self._room_booking_channel(hotel_slug)
            return self._safe_pusher_trigger(channel, "booking_cancelled", event_data)
        
        # Only emit after database transaction commits
        transaction.on_commit(emit_cancellation_event)
    
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
    
    def _room_booking_channel(self, hotel_slug):
        """Helper method to generate room booking channel name."""
        return f"{hotel_slug}.room-bookings"

    # -------------------------------------------------------------------------
    # PHASE 2: NEW BOOKING REALTIME METHODS
    # -------------------------------------------------------------------------

    def realtime_booking_checked_in(self, booking, room=None, primary_guest=None, party_guests=None):
        """
        Emit normalized booking checked-in event.
        
        Args:
            booking: RoomBooking instance
            room: Room instance (deprecated - uses booking.assigned_room)
            primary_guest: Guest instance (deprecated - fetched from booking)
            party_guests: List of all Guest instances (deprecated - fetched from booking)
        """
        room_number = (room.room_number if room 
                      else booking.assigned_room.room_number if booking.assigned_room 
                      else None)
        
        self.logger.info(f"🏨 Realtime booking checked-in: {booking.booking_id} → Room {room_number}")
        
        # Use canonical serializer for complete booking data
        from hotel.canonical_serializers import StaffRoomBookingDetailSerializer
        serializer = StaffRoomBookingDetailSerializer()
        booking_data = serializer.to_representation(booking)
        
        payload = {
            'event': 'booking_checked_in',
            'checked_in_at': booking.checked_in_at.isoformat() if booking.checked_in_at else timezone.now().isoformat(),
            **booking_data
        }
        
        event_data = self._create_normalized_event(
            category="room_booking",
            event_type="booking_checked_in",
            payload=payload,
            hotel=booking.hotel,
            scope={'booking_id': booking.booking_id, 'room_number': room_number}
        )
        
        # Send to room booking channel
        hotel_slug = booking.hotel.slug
        channel = self._room_booking_channel(hotel_slug)
        
        return self._safe_pusher_trigger(channel, "booking_checked_in", event_data)

    def realtime_booking_checked_out(self, booking, room_number=None):
        """
        Emit normalized booking checked-out event.
        
        Args:
            booking: RoomBooking instance
            room_number: int - room number (deprecated - uses booking.assigned_room)
        """
        room_num = (room_number if room_number 
                   else booking.assigned_room.room_number if booking.assigned_room 
                   else None)
        
        self.logger.info(f"🏨 Realtime booking checked-out: {booking.booking_id} from Room {room_num}")
        
        # Use canonical serializer for complete booking data
        from hotel.canonical_serializers import StaffRoomBookingDetailSerializer
        serializer = StaffRoomBookingDetailSerializer()
        booking_data = serializer.to_representation(booking)
        
        payload = {
            'event': 'booking_checked_out',
            'checked_out_at': booking.checked_out_at.isoformat() if booking.checked_out_at else timezone.now().isoformat(),
            **booking_data
        }
        
        event_data = self._create_normalized_event(
            category="room_booking",
            event_type="booking_checked_out", 
            payload=payload,
            hotel=booking.hotel,
            scope={'booking_id': booking.booking_id, 'room_number': room_num}
        )
        
        # Send to room booking channel
        hotel_slug = booking.hotel.slug
        channel = self._room_booking_channel(hotel_slug)
        
        return self._safe_pusher_trigger(channel, "booking_checked_out", event_data)

    def realtime_room_occupancy_updated(self, room):
        """
        Emit normalized room occupancy updated event.
        
        Args:
            room: Room instance
        """
        self.logger.info(f"🏨 Realtime room occupancy updated: Room {room.room_number} → {room.is_occupied}")
        
        # Get current booking for this room if any
        current_booking = room.current_bookings.filter(
            status__in=['checked_in', 'confirmed']
        ).first()
        
        # Use canonical serializer if there's a booking
        booking_data = None
        if current_booking:
            from hotel.canonical_serializers import StaffRoomBookingDetailSerializer
            serializer = StaffRoomBookingDetailSerializer()
            booking_data = serializer.to_representation(current_booking)
        
        # Get minimal guest info for compatibility
        guests_data = []
        for guest in room.guests_in_room.all():
            guests_data.append({
                'id': guest.id,
                'first_name': guest.first_name,
                'last_name': guest.last_name,
                'guest_type': guest.guest_type,
                'id_pin': guest.id_pin
            })
        
        payload = {
            'room_number': room.room_number,
            'is_occupied': room.is_occupied,
            'room_type': room.room_type.name if room.room_type else None,
            'max_occupancy': room.room_type.max_occupancy if room.room_type else None,
            'current_occupancy': room.guests_in_room.count(),
            'guests_in_room': guests_data,
            'current_booking': booking_data
        }
        
        event_data = self._create_normalized_event(
            category="guest_management",
            event_type="room_occupancy_updated",
            payload=payload,
            hotel=room.hotel,
            scope={'room_number': room.room_number}
        )
        
        # Send to rooms channel
        hotel_slug = room.hotel.slug
        channel = f"{hotel_slug}.rooms"
        
        return self._safe_pusher_trigger(channel, "room_occupancy_updated", event_data)

    def realtime_room_updated(self, room, changed_fields=None, source="system"):
        """
        Emit normalized room updated event for operational updates.
        
        This method handles full room snapshot updates for:
        - room_status changes
        - maintenance flags
        - out-of-order status 
        - cleaning/inspection timestamps
        
        IMPORTANT: This method should be called AFTER database commit
        to ensure consistency. Use with transaction.on_commit():
        
        from django.db import transaction
        from notifications.notification_manager import notification_manager
        
        transaction.on_commit(
            lambda: notification_manager.realtime_room_updated(
                room,
                changed_fields=["room_status", "is_occupied"],
                source="checkout"
            )
        )
        
        Args:
            room: Room instance
            changed_fields: List of field names that were changed (optional)
            source: Source of the change ("system", "housekeeping", "front_desk", etc.)
        """
        self.logger.info(f"🏨 Realtime room updated: Room {room.room_number} - {changed_fields or 'unknown fields'}")
        
        # Build full room snapshot payload
        payload = {
            'room_number': room.room_number,
            'room_status': room.room_status,
            'is_occupied': room.is_occupied,
            'is_out_of_order': room.is_out_of_order,
            'maintenance_required': room.maintenance_required,
            'maintenance_priority': room.maintenance_priority,
            'maintenance_notes': room.maintenance_notes,
            'last_cleaned_at': room.last_cleaned_at.isoformat() if room.last_cleaned_at else None,
            'last_inspected_at': room.last_inspected_at.isoformat() if room.last_inspected_at else None,
            'changed_fields': changed_fields or []
        }
        
        # Add room type info if available (without extra queries)
        if hasattr(room, 'room_type') and room.room_type:
            payload['room_type'] = room.room_type.name
            payload['max_occupancy'] = room.room_type.max_occupancy
        
        # Add guests count if available (from prefetch or existing query)
        if hasattr(room, '_prefetched_objects_cache') and 'guests_in_room' in room._prefetched_objects_cache:
            payload['guests_in_room'] = room.guests_in_room.count()
        elif hasattr(room, 'guests_in_room'):
            # Only count if it won't trigger a new query
            try:
                payload['guests_in_room'] = len(room.guests_in_room.all())
            except:
                pass
        
        event_data = self._create_normalized_event(
            category="rooms",
            event_type="room_updated", 
            payload=payload,
            hotel=room.hotel,
            scope={'room_number': room.room_number}
        )
        
        # Send to rooms channel
        hotel_slug = room.hotel.slug
        channel = f"{hotel_slug}.rooms"
        
        return self._safe_pusher_trigger(channel, "room_updated", event_data)

    # -------------------------------------------------------------------------
    # PHASE 3.5: BOOKING INTEGRITY HEALING REALTIME METHODS
    # -------------------------------------------------------------------------
    
    def realtime_booking_integrity_healed(self, hotel, healing_report):
        """
        Emit normalized booking integrity healed event.
        Called when the auto-heal service fixes booking data issues.
        
        Args:
            hotel: Hotel instance
            healing_report: Dict with healing results from booking_integrity service
        """
        self.logger.info(f"🛡️ Realtime booking integrity healed: {hotel.slug} - {healing_report['bookings_processed']} bookings")
        
        payload = {
            'hotel_slug': hotel.slug,
            'hotel_name': hotel.name,
            'summary': {
                'bookings_processed': healing_report['bookings_processed'],
                'total_fixes': sum(healing_report[k] for k in ['created', 'updated', 'deleted', 'demoted']),
                'created': healing_report['created'],
                'updated': healing_report['updated'],
                'deleted': healing_report['deleted'],
                'demoted': healing_report['demoted']
            },
            'healed_at': timezone.now().isoformat(),
            'significant_changes': healing_report['created'] + healing_report['demoted'] > 0
        }
        
        event_data = self._create_normalized_event(
            category="room_booking",
            event_type="integrity_healed",
            payload=payload,
            hotel=hotel,
            scope={'healing_type': 'auto_heal', 'changes_count': payload['summary']['total_fixes']}
        )
        
        # Send to hotel room booking channel
        channel = self._room_booking_channel(hotel.slug)
        return self._safe_pusher_trigger(channel, "booking_integrity_healed", event_data)
    
    def realtime_booking_party_healed(self, booking):
        """
        Emit normalized booking party healed event.
        Called when party integrity issues are fixed for a specific booking.
        
        Args:
            booking: RoomBooking instance that was healed
        """
        self.logger.info(f"👥 Realtime booking party healed: {booking.booking_id}")
        
        # Get current party state after healing
        party_members = list(booking.party.all())
        primary_guest = next((p for p in party_members if p.role == 'PRIMARY'), None)
        companions = [p for p in party_members if p.role == 'COMPANION']
        
        payload = {
            'booking_id': booking.booking_id,
            'confirmation_number': getattr(booking, 'confirmation_number', None),
            'party': {
                'primary': {
                    'id': primary_guest.id,
                    'first_name': primary_guest.first_name,
                    'last_name': primary_guest.last_name,
                    'role': primary_guest.role
                } if primary_guest else None,
                'companions': [
                    {
                        'id': companion.id,
                        'first_name': companion.first_name,
                        'last_name': companion.last_name,
                        'role': companion.role
                    } for companion in companions
                ],
                'total_members': len(party_members)
            },
            'healed_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="room_booking",
            event_type="party_healed",
            payload=payload,
            hotel=booking.hotel,
            scope={'booking_id': booking.booking_id, 'party_size': len(party_members)}
        )
        
        # Send to hotel room booking channel
        channel = self._room_booking_channel(booking.hotel.slug)
        return self._safe_pusher_trigger(channel, "booking_party_healed", event_data)
    
    def realtime_booking_guests_healed(self, booking, primary_guest):
        """
        Emit normalized booking in-house guests healed event.
        Called when in-house guest integrity issues are fixed for a checked-in booking.
        
        Args:
            booking: RoomBooking instance that was healed
            primary_guest: Primary Guest instance after healing
        """
        self.logger.info(f"🏠 Realtime booking guests healed: {booking.booking_id} - Room {booking.assigned_room.room_number if booking.assigned_room else 'None'}")
        
        # Get current in-house guests after healing
        inhouse_guests = list(booking.guests.all())
        companions = [g for g in inhouse_guests if g.guest_type == 'COMPANION']
        
        payload = {
            'booking_id': booking.booking_id,
            'confirmation_number': getattr(booking, 'confirmation_number', None),
            'room_number': booking.assigned_room.room_number if booking.assigned_room else None,
            'primary_guest': {
                'id': primary_guest.id,
                'first_name': primary_guest.first_name,
                'last_name': primary_guest.last_name,
                'guest_type': primary_guest.guest_type,
                'id_pin': primary_guest.id_pin
            },
            'companion_guests': [
                {
                    'id': companion.id,
                    'first_name': companion.first_name,
                    'last_name': companion.last_name,
                    'guest_type': companion.guest_type
                } for companion in companions
            ],
            'total_guests': len(inhouse_guests),
            'healed_at': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="room_booking",
            event_type="guests_healed",
            payload=payload,
            hotel=booking.hotel,
            scope={'booking_id': booking.booking_id, 'room_number': payload['room_number']}
        )
        
        # Send to hotel room booking channel
        channel = self._room_booking_channel(booking.hotel.slug)
        return self._safe_pusher_trigger(channel, "booking_guests_healed", event_data)
    
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
                pusher_client.trigger(staff_channel, "new_guest_message", message_data)
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
            pusher_client.trigger(guest_channel, "staff_reply", message_data)
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
            event_type="realtime_staff_chat_message_deleted",
            payload=payload,
            hotel=hotel,
            scope={'conversation_id': conversation_id, 'message_id': message_id}
        )
        
        hotel_slug = hotel.slug
        channel = f"{hotel_slug}.staff-chat.{conversation_id}"
        return self._safe_pusher_trigger(channel, "realtime_staff_chat_message_deleted", event_data)
    
    def realtime_staff_chat_typing_indicator(self, staff, conversation_id, is_typing=True):
        """Emit staff chat typing indicator (ephemeral event)."""
        self.logger.info(f"✍️ Realtime staff chat: typing indicator for staff {staff.id}")
        
        # Get staff avatar URL
        staff_avatar_url = None
        if staff.profile_image and hasattr(staff.profile_image, 'url'):
            staff_avatar_url = staff.profile_image.url
        
        # Typing indicators use normalized structure for consistency
        payload = {
            'conversation_id': conversation_id,
            'staff_id': staff.id,
            'staff_name': f"{staff.first_name} {staff.last_name}",
            'staff_avatar': staff_avatar_url,  # Include staff's profile image URL
            'is_typing': is_typing,
            'timestamp': timezone.now().isoformat()
        }
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="realtime_staff_chat_typing",
            payload=payload,
            hotel=staff.hotel,
            scope={'conversation_id': conversation_id, 'staff_id': staff.id}
        )
        
        hotel_slug = staff.hotel.slug
        channel = f"{hotel_slug}.staff-chat.{conversation_id}"
        return self._safe_pusher_trigger(channel, "realtime_staff_chat_typing", event_data)
    
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
            event_type="realtime_staff_chat_attachment_uploaded",
            payload=payload,
            hotel=message.conversation.hotel if hasattr(message.conversation, 'hotel') else message.sender.hotel,
            scope={'conversation_id': message.conversation.id, 'attachment_id': attachment.id}
        )
        
        hotel_slug = message.sender.hotel.slug
        channel = f"{hotel_slug}.staff-chat.{message.conversation.id}"
        return self._safe_pusher_trigger(channel, "realtime_staff_chat_attachment_uploaded", event_data)
    
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
            event_type="realtime_staff_chat_attachment_deleted",
            payload=payload,
            hotel=conversation.hotel if hasattr(conversation, 'hotel') else staff.hotel,
            scope={'conversation_id': conversation.id, 'attachment_id': attachment_id}
        )
        
        hotel_slug = staff.hotel.slug
        channel = f"{hotel_slug}.staff-chat.{conversation.id}"
        return self._safe_pusher_trigger(channel, "realtime_staff_chat_attachment_deleted", event_data)
    
    def realtime_staff_chat_staff_mentioned(self, staff, message, conversation_id):
        """Emit staff chat staff mentioned notification."""
        self.logger.info(f"📢 Realtime staff chat: mention for staff {staff.id}")
        
        # Get avatar URLs
        mentioned_staff_avatar = None
        if staff.profile_image and hasattr(staff.profile_image, 'url'):
            mentioned_staff_avatar = staff.profile_image.url
        
        sender_avatar = None
        if message.sender.profile_image and hasattr(message.sender.profile_image, 'url'):
            sender_avatar = message.sender.profile_image.url
        
        payload = {
            'conversation_id': conversation_id,
            'message_id': message.id,
            'mentioned_staff_id': staff.id,
            'mentioned_staff_name': f"{staff.first_name} {staff.last_name}",
            'mentioned_staff_avatar': mentioned_staff_avatar,  # Include mentioned staff's avatar
            'sender_id': message.sender.id,
            'sender_name': f"{message.sender.first_name} {message.sender.last_name}",
            'sender_avatar': sender_avatar,  # Include sender's avatar
            'message': message.message,  # Match serializer field name: 'message'
            'timestamp': message.timestamp.isoformat()  # Match serializer field name: 'timestamp'
        }
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="realtime_staff_chat_staff_mentioned",
            payload=payload,
            hotel=staff.hotel,
            scope={'mentioned_staff_id': staff.id, 'conversation_id': conversation_id}
        )
        
        # Send to staff's personal notification channel
        hotel_slug = staff.hotel.slug
        channel = f"{hotel_slug}.staff-{staff.id}-notifications"
        return self._safe_pusher_trigger(channel, "realtime_staff_chat_staff_mentioned", event_data)
    
    def realtime_staff_chat_messages_read(self, conversation, staff, message_ids):
        """Emit staff chat messages read receipt event."""
        self.logger.info(f"👀 Realtime staff chat: messages read by staff {staff.id}")
        
        # Get staff avatar URL
        staff_avatar_url = None
        if staff.profile_image and hasattr(staff.profile_image, 'url'):
            staff_avatar_url = staff.profile_image.url
        
        payload = {
            'conversation_id': conversation.id,
            'message_ids': message_ids,
            'read_by_staff_id': staff.id,
            'read_by_staff_name': f"{staff.first_name} {staff.last_name}",
            'read_by_staff_avatar': staff_avatar_url,  # Include staff's profile image URL
            'read_at': timezone.now().isoformat(),
            # Frontend compatibility fields - match expected field names
            'id': staff.id,  # Frontend expects 'id' for staff ID
            'staff_id': staff.id,  # Backend compatibility
            'name': f"{staff.first_name} {staff.last_name}",  # Frontend expects 'name'
            'staff_name': f"{staff.first_name} {staff.last_name}",  # Backend compatibility  
            'avatar': staff_avatar_url,  # Frontend expects 'avatar'
            'staff_avatar': staff_avatar_url  # Backend compatibility
        }
        
        event_data = self._create_normalized_event(
            category="staff_chat",
            event_type="realtime_staff_chat_messages_read",
            payload=payload,
            hotel=conversation.hotel if hasattr(conversation, 'hotel') else staff.hotel,
            scope={'conversation_id': conversation.id, 'read_by_staff_id': staff.id}
        )
        
        # Send to conversation channel
        hotel_slug = staff.hotel.slug
        channel = f"{hotel_slug}.staff-chat.{conversation.id}"
        return self._safe_pusher_trigger(channel, "realtime_staff_chat_messages_read", event_data)
    
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
            event_type="realtime_staff_chat_message_delivered",
            payload=payload,
            hotel=message.conversation.hotel if hasattr(message.conversation, 'hotel') else staff.hotel,
            scope={'conversation_id': message.conversation.id, 'message_id': message.id, 'delivered_to_staff_id': staff.id}
        )
        
        # Send to conversation channel
        hotel_slug = staff.hotel.slug
        channel = f"{hotel_slug}.staff-chat.{message.conversation.id}"
        return self._safe_pusher_trigger(channel, "realtime_staff_chat_message_delivered", event_data)

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