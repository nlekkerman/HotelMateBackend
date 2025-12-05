"""
Staff Chat Pusher Utils - Refactored to use NotificationManager
for staff_chat domain realtime events.

This module now delegates to the unified NotificationManager for staff chat events
while maintaining backward compatibility.
"""
import logging
from typing import List, Dict, Any
from notifications.notification_manager import notification_manager
from chat.utils import pusher_client

logger = logging.getLogger(__name__)


def get_conversation_channel(hotel_slug, conversation_id):
    """Get standardized conversation channel name."""
    return f"hotel-{hotel_slug}.staff-chat.{conversation_id}"


def get_staff_personal_channel(hotel_slug, staff_id):
    """Get standardized staff personal channel name."""
    return f"hotel-{hotel_slug}.staff-{staff_id}-notifications"


def trigger_conversation_event(hotel_slug, conversation_id, event, data):
    """
    Legacy function - deprecated. Use NotificationManager directly.
    This is maintained for backward compatibility only.
    """
    logger.warning(f"Legacy trigger_conversation_event called for event: {event}. Consider using NotificationManager directly.")
    # Legacy events should be migrated to NotificationManager
    return False


def trigger_staff_notification(hotel_slug, staff_id, event, data):
    """
    Legacy function - deprecated. Use NotificationManager directly.
    This is maintained for backward compatibility only.
    """
    logger.warning(f"Legacy trigger_staff_notification called for event: {event}. Consider using NotificationManager directly.")
    # Legacy events should be migrated to NotificationManager
    return False


def broadcast_new_message(hotel_slug, conversation_id, message):
    """
    Broadcast new staff chat message using NotificationManager.
    Expects message to be the actual StaffChatMessage object.
    """
    try:
        if message:
            return notification_manager.realtime_staff_chat_message_created(message)
        else:
            logger.error("No message object provided to broadcast_new_message")
            return False
    except Exception as e:
        logger.error(f"Failed to broadcast new staff chat message: {e}")
        return False


def broadcast_message_edited(hotel_slug, conversation_id, message):
    """
    Broadcast edited staff chat message using NotificationManager.
    Expects message to be the actual StaffChatMessage object.
    """
    try:
        if message:
            return notification_manager.realtime_staff_chat_message_edited(message)
        else:
            logger.error("No message object provided to broadcast_message_edited")
            return False
    except Exception as e:
        logger.error(f"Failed to broadcast edited staff chat message: {e}")
        return False


def broadcast_message_deleted(hotel_slug, conversation_id, deletion_data):
    """
    Broadcast message deletion using NotificationManager.
    """
    try:
        message_id = deletion_data.get('message_id')
        hotel = deletion_data.get('hotel')  # Should be passed in deletion_data
        
        if message_id and hotel:
            return notification_manager.realtime_staff_chat_message_deleted(message_id, conversation_id, hotel)
        else:
            logger.error("Missing message_id or hotel in deletion_data for staff chat message deletion")
            return False
    except Exception as e:
        logger.error(f"Failed to broadcast staff chat message deletion: {e}")
        return False


def broadcast_message_reaction(hotel_slug, conversation_id, reaction_data):
    """Broadcast message reaction to all conversation participants"""
    return trigger_conversation_event(
        hotel_slug,
        conversation_id,
        "message-reaction",
        reaction_data
    )


def broadcast_typing_indicator(hotel_slug, conversation_id, typing_data):
    """
    Broadcast typing indicator using NotificationManager.
    """
    try:
        staff = typing_data.get('staff')  # Should be passed in typing_data
        is_typing = typing_data.get('is_typing', True)
        
        if staff:
            return notification_manager.realtime_staff_chat_typing_indicator(staff, conversation_id, is_typing)
        else:
            logger.error("Missing staff in typing_data for staff chat typing indicator")
            return False
    except Exception as e:
        logger.error(f"Failed to broadcast staff chat typing indicator: {e}")
        return False


def notify_staff_mentioned(hotel_slug, staff_id, mention_data):
    """
    Notify staff of @mentions in chat using NotificationManager.
    """
    try:
        staff = mention_data.get('staff')  # Should be passed in mention_data
        message = mention_data.get('message')  # Should be passed in mention_data
        conversation_id = mention_data.get('conversation_id')
        
        if staff and message and conversation_id:
            return notification_manager.realtime_staff_chat_mention(staff, message, conversation_id)
        else:
            logger.error("Missing staff, message, or conversation_id in mention_data for staff chat mention")
            return False
    except Exception as e:
        logger.error(f"Failed to notify staff mention: {e}")
        return False


# Legacy compatibility functions
def trigger_conversation_event(hotel_slug, conversation_id, event, data):
    """Legacy function - redirects to appropriate new methods."""
    if event == "new-message":
        # Legacy callers may still pass serialized data, extract message if available
        message = data.get('message') if isinstance(data, dict) else data
        return broadcast_new_message(hotel_slug, conversation_id, message)
    elif event == "message-edited":
        message = data.get('message') if isinstance(data, dict) else data
        return broadcast_message_edited(hotel_slug, conversation_id, message)
    elif event == "message-deleted":
        return broadcast_message_deleted(hotel_slug, conversation_id, data)
    elif event == "typing":
        return broadcast_typing_indicator(hotel_slug, conversation_id, data)
    else:
        logger.warning(f"Unknown staff chat event: {event}")
        return False


def trigger_staff_notification(hotel_slug, staff_id, event, data):
    """Legacy function for staff personal notifications."""
    if event == "mentioned":
        return notify_staff_mentioned(hotel_slug, staff_id, data)
    else:
        logger.warning(f"Legacy trigger_staff_notification called for event: {event}. Use NotificationManager directly.")
        return False


def broadcast_read_receipt(hotel_slug, conversation_id, staff, message_ids):
    """Broadcast read receipt using NotificationManager"""
    try:
        from .models import StaffConversation
        conversation = StaffConversation.objects.get(id=conversation_id)
        return notification_manager.realtime_staff_chat_message_read(conversation, staff, message_ids)
    except Exception as e:
        logger.error(f"Failed to broadcast read receipt: {e}")
        return False


def notify_staff_of_mention(hotel_slug, staff_id, mention_data):
    """Notify staff member they were mentioned in a message"""
    return trigger_staff_notification(
        hotel_slug,
        staff_id,
        "message-mention",
        mention_data
    )


def notify_staff_of_new_conversation(hotel_slug, staff_id, conversation_data):
    """Notify staff member they were added to a new conversation"""
    return trigger_staff_notification(
        hotel_slug,
        staff_id,
        "new-conversation",
        conversation_data
    )


def broadcast_to_multiple_staff(hotel_slug, staff_ids, event, data):
    """
    Broadcast event to multiple staff members' personal channels
    Used for notifying multiple staff of group events
    """
    success_count = 0
    for staff_id in staff_ids:
        if trigger_staff_notification(hotel_slug, staff_id, event, data):
            success_count += 1
    
    logger.info(
        f"Broadcast to {success_count}/{len(staff_ids)} staff members"
    )
    return success_count


def broadcast_conversation_updated(
    hotel_slug, conversation_id, update_data
):
    """Broadcast conversation metadata updates (title, participants, etc.)"""
    return trigger_conversation_event(
        hotel_slug,
        conversation_id,
        "conversation-updated",
        update_data
    )


def broadcast_attachment_uploaded(hotel_slug, conversation_id, attachment, message):
    """Broadcast new file attachment using NotificationManager"""
    try:
        return notification_manager.realtime_staff_chat_attachment_uploaded(attachment, message)
    except Exception as e:
        logger.error(f"Failed to broadcast attachment upload: {e}")
        return False


def broadcast_attachment_deleted(hotel_slug, conversation_id, attachment_id, staff):
    """Broadcast attachment deletion using NotificationManager"""
    try:
        from .models import StaffConversation
        conversation = StaffConversation.objects.get(id=conversation_id)
        return notification_manager.realtime_staff_chat_attachment_deleted(attachment_id, conversation, staff)
    except Exception as e:
        logger.error(f"Failed to broadcast attachment deletion: {e}")
        return False
