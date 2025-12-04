"""
Staff Chat Pusher Utils - Refactored to use NotificationManager
for staff_chat domain realtime events.

This module now delegates to the unified NotificationManager for staff chat events
while maintaining backward compatibility.
"""
import logging
from typing import List, Dict, Any
from notifications.notification_manager import notification_manager

logger = logging.getLogger(__name__)


def get_conversation_channel(hotel_slug, conversation_id):
    """Get standardized conversation channel name."""
    return f"hotel-{hotel_slug}.staff-chat.{conversation_id}"


def get_staff_personal_channel(hotel_slug, staff_id):
    """Get standardized staff personal channel name."""
    return f"hotel-{hotel_slug}.staff-{staff_id}-notifications"


def trigger_conversation_event(hotel_slug, conversation_id, event, data):
    """
    Trigger event on conversation channel
    All participants in conversation will receive this
    """
    channel = get_conversation_channel(hotel_slug, conversation_id)
    try:
        pusher_client.trigger(channel, event, data)
        logger.info(
            f"Pusher: conversation channel={channel}, event={event}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to trigger Pusher on {channel}: {e}"
        )
        return False


def trigger_staff_notification(hotel_slug, staff_id, event, data):
    """
    Trigger event on staff personal channel
    Used for notifications, mentions, etc.
    """
    channel = get_staff_personal_channel(hotel_slug, staff_id)
    try:
        pusher_client.trigger(channel, event, data)
        logger.info(
            f"Pusher: staff channel={channel}, event={event}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to trigger Pusher on {channel}: {e}"
        )
        return False


def broadcast_new_message(hotel_slug, conversation_id, message_data):
    """
    Broadcast new staff chat message using NotificationManager.
    Expects message_data to have a 'message' object.
    """
    try:
        message = message_data.get('message')
        if message:
            return notification_manager.realtime_staff_chat_message_created(message)
        else:
            logger.error("No message object provided to broadcast_new_message")
            return False
    except Exception as e:
        logger.error(f"Failed to broadcast new staff chat message: {e}")
        return False


def broadcast_message_edited(hotel_slug, conversation_id, message_data):
    """
    Broadcast edited staff chat message using NotificationManager.
    """
    try:
        message = message_data.get('message')
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
    Broadcast message deletion - using direct Pusher for now.
    TODO: Add realtime_staff_chat_message_deleted method to NotificationManager.
    """
    from chat.utils import pusher_client
    
    channel = get_conversation_channel(hotel_slug, conversation_id)
    try:
        pusher_client.trigger(channel, "message-deleted", deletion_data)
        logger.info(f"Staff chat message deleted: {channel}")
        return True
    except Exception as e:
        logger.error(f"Failed to broadcast message deletion: {e}")
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
    Broadcast typing indicator - using direct Pusher for now.
    Typing indicators are ephemeral and don't need full normalization.
    """
    from chat.utils import pusher_client
    
    channel = get_conversation_channel(hotel_slug, conversation_id)
    try:
        pusher_client.trigger(channel, "typing", typing_data)
        return True
    except Exception as e:
        logger.error(f"Failed to broadcast typing indicator: {e}")
        return False


def notify_staff_mentioned(hotel_slug, staff_id, mention_data):
    """
    Notify staff of @mentions in chat using NotificationManager.
    TODO: Add realtime_staff_chat_mention method to NotificationManager.
    """
    from chat.utils import pusher_client
    
    channel = get_staff_personal_channel(hotel_slug, staff_id)
    try:
        pusher_client.trigger(channel, "mentioned", mention_data)
        logger.info(f"Staff mention notification: {channel}")
        return True
    except Exception as e:
        logger.error(f"Failed to notify staff mention: {e}")
        return False


# Legacy compatibility functions
def trigger_conversation_event(hotel_slug, conversation_id, event, data):
    """Legacy function - redirects to appropriate new methods."""
    if event == "new-message":
        return broadcast_new_message(hotel_slug, conversation_id, data)
    elif event == "message-edited":
        return broadcast_message_edited(hotel_slug, conversation_id, data)
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
        # Generic staff notification using direct Pusher
        from chat.utils import pusher_client
        channel = get_staff_personal_channel(hotel_slug, staff_id)
        try:
            pusher_client.trigger(channel, event, data)
            return True
        except Exception as e:
            logger.error(f"Failed staff notification: {e}")
            return False
    """Broadcast typing indicator to all conversation participants"""
    return trigger_conversation_event(
        hotel_slug,
        conversation_id,
        "user-typing",
        typing_data
    )


def broadcast_read_receipt(hotel_slug, conversation_id, read_data):
    """Broadcast read receipt to all conversation participants"""
    return trigger_conversation_event(
        hotel_slug,
        conversation_id,
        "messages-read",
        read_data
    )


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


def broadcast_attachment_uploaded(hotel_slug, conversation_id, attachment_data):
    """Broadcast new file attachment to conversation"""
    return trigger_conversation_event(
        hotel_slug,
        conversation_id,
        "attachment-uploaded",
        attachment_data
    )


def broadcast_attachment_deleted(hotel_slug, conversation_id, deletion_data):
    """Broadcast attachment deletion to conversation"""
    return trigger_conversation_event(
        hotel_slug,
        conversation_id,
        "attachment-deleted",
        deletion_data
    )
