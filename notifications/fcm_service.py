"""
Firebase Cloud Messaging (FCM) Service
Sends native push notifications to mobile devices when app is closed
"""
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
_firebase_initialized = False


def initialize_firebase():
    """Initialize Firebase Admin SDK with credentials from environment"""
    global _firebase_initialized
    
    if _firebase_initialized:
        return True
    
    try:
        # Get credentials from environment variable
        firebase_creds_json = settings.FIREBASE_SERVICE_ACCOUNT_JSON
        
        if not firebase_creds_json:
            logger.warning("Firebase credentials not found in settings")
            return False
        
        # Parse JSON credentials
        cred_dict = json.loads(firebase_creds_json)
        
        # Fix private key newlines (convert \n to actual newlines)
        if 'private_key' in cred_dict:
            cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
        
        cred = credentials.Certificate(cred_dict)
        
        # Initialize Firebase app
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin SDK initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return False


def send_fcm_notification(token, title, body, data=None):
    """
    Send FCM push notification to a single device
    
    Args:
        token: FCM device token
        title: Notification title
        body: Notification body text
        data: Optional dict of custom data
    
    Returns:
        bool: True if sent successfully
    """
    if not initialize_firebase():
        logger.error("Firebase not initialized, cannot send notification")
        return False
    
    if not token:
        logger.warning("No FCM token provided")
        return False
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='notification_icon',
                    color='#FF6B35',
                    sound='default',
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1,
                    ),
                ),
            ),
        )
        
        response = messaging.send(message)
        logger.info(f"FCM notification sent successfully: {response}")
        return True
        
    except messaging.UnregisteredError:
        logger.warning(f"FCM token is invalid or unregistered: {token}")
        return False
    except Exception as e:
        logger.error(f"Failed to send FCM notification: {e}")
        return False


def send_fcm_multicast(tokens, title, body, data=None):
    """
    Send FCM push notification to multiple devices
    
    Args:
        tokens: List of FCM device tokens
        title: Notification title
        body: Notification body text
        data: Optional dict of custom data
    
    Returns:
        tuple: (success_count, failure_count)
    """
    if not initialize_firebase():
        logger.error("Firebase not initialized, cannot send notifications")
        return (0, len(tokens))
    
    if not tokens:
        return (0, 0)
    
    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=tokens,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='notification_icon',
                    color='#FF6B35',
                    sound='default',
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1,
                    ),
                ),
            ),
        )
        
        response = messaging.send_multicast(message)
        logger.info(
            f"FCM multicast: {response.success_count} successful, "
            f"{response.failure_count} failed"
        )
        return (response.success_count, response.failure_count)
        
    except Exception as e:
        logger.error(f"Failed to send FCM multicast: {e}")
        return (0, len(tokens))


def send_porter_order_notification(staff, order):
    """
    Send push notification to porter about new room service order
    
    Args:
        staff: Staff instance (porter)
        order: Order instance
    
    Returns:
        bool: True if notification sent successfully
    """
    if not staff.fcm_token:
        logger.warning(
            f"❌ No FCM token for porter {staff.first_name} "
            f"{staff.last_name} (ID: {staff.id})"
        )
        return False
    
    title = "🔔 New Room Service Order"
    body = f"Room {order.room_number} - €{order.total_price:.2f}"
    data = {
        "type": "room_service_order",
        "order_id": str(order.id),
        "room_number": str(order.room_number),
        "total_price": str(order.total_price),
        "status": order.status,
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
        "route": "/orders/room-service"
    }
    
    logger.info(
        f"📤 Sending FCM to porter {staff.first_name} {staff.last_name} "
        f"for order #{order.id}"
    )
    
    result = send_fcm_notification(staff.fcm_token, title, body, data)
    
    if result:
        logger.info(
            f"✅ FCM sent successfully to porter {staff.id}"
        )
    else:
        logger.error(
            f"❌ FCM failed for porter {staff.id}"
        )
    
    return result


def send_porter_breakfast_notification(staff, order):
    """
    Send push notification to porter about new breakfast order
    
    Args:
        staff: Staff instance (porter)
        order: BreakfastOrder instance
    
    Returns:
        bool: True if notification sent successfully
    """
    if not staff.fcm_token:
        logger.debug(
            f"No FCM token for porter {staff.first_name} {staff.last_name}"
        )
        return False
    
    delivery_time = order.delivery_time if order.delivery_time else "ASAP"
    title = "🍳 New Breakfast Order"
    body = f"Room {order.room_number} - Delivery: {delivery_time}"
    data = {
        "type": "breakfast_order",
        "order_id": str(order.id),
        "room_number": str(order.room_number),
        "delivery_time": str(delivery_time),
        "status": order.status,
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
        "route": "/orders/breakfast"
    }
    
    return send_fcm_notification(staff.fcm_token, title, body, data)


def send_porter_count_update(staff, pending_count, order_type):
    """
    Send push notification to porter about order count update
    
    Args:
        staff: Staff instance (porter)
        pending_count: Number of pending orders
        order_type: Type of orders (room_service or breakfast)
    
    Returns:
        bool: True if notification sent successfully
    """
    if not staff.fcm_token:
        return False
    
    if order_type == "room_service_orders":
        title = "📋 Room Service Updates"
        body = f"{pending_count} pending order(s)"
    else:
        title = "📋 Breakfast Updates"
        body = f"{pending_count} pending order(s)"
    
    data = {
        "type": "order_count_update",
        "pending_count": str(pending_count),
        "order_type": order_type,
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
    }
    
    return send_fcm_notification(staff.fcm_token, title, body, data)


def send_kitchen_staff_order_notification(staff, order):
    """
    Send push notification to kitchen staff about new room service order
    
    Args:
        staff: Staff instance (kitchen staff member)
        order: Order instance
    
    Returns:
        bool: True if notification sent successfully
    """
    if not staff.fcm_token:
        logger.debug(
            f"No FCM token for kitchen staff "
            f"{staff.first_name} {staff.last_name}"
        )
        return False
    
    title = "🔔 New Room Service Order"
    body = f"Room {order.room_number} - €{order.total_price:.2f}"
    data = {
        "type": "room_service_order",
        "order_id": str(order.id),
        "room_number": str(order.room_number),
        "total_price": str(order.total_price),
        "status": order.status,
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
        "route": "/orders/room-service"
    }
    
    return send_fcm_notification(staff.fcm_token, title, body, data)


def send_booking_confirmation_notification(guest_fcm_token, booking):
    """
    Send push notification to guest about booking confirmation
    
    Args:
        guest_fcm_token: Guest's FCM token (from room if available)
        booking: RoomBooking instance
    
    Returns:
        bool: True if notification sent successfully
    """
    if not guest_fcm_token:
        logger.debug(f"No FCM token for guest booking {booking.booking_id}")
        return False
    
    title = "✅ Booking Confirmed!"
    body = f"Your reservation at {booking.hotel.name} has been confirmed"
    data = {
        "type": "booking_confirmation",
        "booking_id": booking.booking_id,
        "confirmation_number": booking.confirmation_number,
        "hotel_name": booking.hotel.name,
        "room_type": booking.room_type.name if booking.room_type else "",
        "check_in": str(booking.check_in),
        "check_out": str(booking.check_out),
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
        "route": "/bookings/details"
    }
    
    logger.info(f"📤 Sending booking confirmation FCM for {booking.booking_id}")
    return send_fcm_notification(guest_fcm_token, title, body, data)


def send_booking_cancellation_notification(guest_fcm_token, booking, reason=None):
    """
    Send push notification to guest about booking cancellation
    
    Args:
        guest_fcm_token: Guest's FCM token (from room if available)
        booking: RoomBooking instance
        reason: Cancellation reason
    
    Returns:
        bool: True if notification sent successfully
    """
    if not guest_fcm_token:
        logger.debug(f"No FCM token for guest booking {booking.booking_id}")
        return False
    
    title = "❌ Booking Cancelled"
    body = f"Your reservation at {booking.hotel.name} has been cancelled"
    if reason and reason != "Cancelled by staff":
        body += f" - {reason}"
    
    data = {
        "type": "booking_cancellation", 
        "booking_id": booking.booking_id,
        "confirmation_number": booking.confirmation_number,
        "hotel_name": booking.hotel.name,
        "cancellation_reason": reason or "No reason provided",
        "click_action": "FLUTTER_NOTIFICATION_CLICK",
        "route": "/bookings/cancelled"
    }
    
    logger.info(f"📤 Sending booking cancellation FCM for {booking.booking_id}")
    return send_fcm_notification(guest_fcm_token, title, body, data)
