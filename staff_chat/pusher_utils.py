"""
Pusher utilities for Staff Chat
Real-time event broadcasting for staff conversations
"""
import logging
from typing import List, Dict, Any
from chat.utils import pusher_client

logger = logging.getLogger(__name__)


def get_conversation_channel(hotel_slug, conversation_id):
    """Get Pusher channel name for a conversation"""
    return f"{hotel_slug}-staff-conversation-{conversation_id}"


def get_staff_personal_channel(hotel_slug, staff_id):
    """Get Pusher channel name for personal staff notifications"""
    return f"{hotel_slug}-staff-{staff_id}-notifications"


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
    """Broadcast new message to all conversation participants"""
    return trigger_conversation_event(
        hotel_slug,
        conversation_id,
        "new-message",
        message_data
    )


def broadcast_message_edited(hotel_slug, conversation_id, message_data):
    """Broadcast message edit to all conversation participants"""
    return trigger_conversation_event(
        hotel_slug,
        conversation_id,
        "message-edited",
        message_data
    )


def broadcast_message_deleted(hotel_slug, conversation_id, deletion_data):
    """Broadcast message deletion to all conversation participants"""
    return trigger_conversation_event(
        hotel_slug,
        conversation_id,
        "message-deleted",
        deletion_data
    )


def broadcast_message_reaction(hotel_slug, conversation_id, reaction_data):
    """Broadcast message reaction to all conversation participants"""
    return trigger_conversation_event(
        hotel_slug,
        conversation_id,
        "message-reaction",
        reaction_data
    )


def broadcast_typing_indicator(hotel_slug, conversation_id, typing_data):
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
