"""
FCM (Firebase Cloud Messaging) utilities for Staff Chat
Push notifications for staff chat messages
"""
import logging
from typing import List, Dict, Any
from notifications.fcm_service import (
    send_fcm_notification,
    send_fcm_multicast
)

logger = logging.getLogger(__name__)


def send_new_message_notification(
    recipient_staff,
    sender_staff,
    conversation,
    message_text
):
    """
    Send FCM notification for new staff chat message
    
    Args:
        recipient_staff: Staff instance receiving notification
        sender_staff: Staff instance who sent the message
        conversation: StaffConversation instance
        message_text: Preview text of the message
    
    Returns:
        bool: True if sent successfully
    """
    if not recipient_staff.fcm_token:
        logger.debug(
            f"No FCM token for staff {recipient_staff.id}"
        )
        return False
    
    # Format sender name
    sender_name = (
        f"{sender_staff.first_name} {sender_staff.last_name}".strip()
    )
    
    # Format title based on conversation type
    if conversation.is_group:
        title = f"💬 {sender_name} in {conversation.title or 'Group Chat'}"
    else:
        title = f"💬 {sender_name}"
    
    # Message preview (max 100 chars)
    body = message_text[:100] if message_text else "Sent a file"
    
    # Notification data
    data = {
        "type": "staff_chat_message",
        "conversation_id": str(conversation.id),
        "sender_id": str(sender_staff.id),
        "sender_name": sender_name,
        "is_group": str(conversation.is_group),
        "hotel_slug": conversation.hotel.slug,
        "click_action": f"/staff-chat/{conversation.hotel.slug}/conversation/{conversation.id}",
        "url": f"https://hotelsmates.com/staff-chat/{conversation.hotel.slug}/conversation/{conversation.id}"
    }
    
    try:
        result = send_fcm_notification(
            recipient_staff.fcm_token,
            title,
            body,
            data=data
        )
        
        if result:
            logger.info(
                f"✅ FCM sent to staff {recipient_staff.id} "
                f"for message from {sender_staff.id}"
            )
        else:
            logger.warning(
                f"❌ FCM failed for staff {recipient_staff.id}"
            )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to send FCM to staff {recipient_staff.id}: {e}"
        )
        return False


def send_mention_notification(
    mentioned_staff,
    sender_staff,
    conversation,
    message_text
):
    """
    Send FCM notification when staff is mentioned (@staff)
    
    Args:
        mentioned_staff: Staff instance who was mentioned
        sender_staff: Staff instance who sent the message
        conversation: StaffConversation instance
        message_text: Message containing the mention
    
    Returns:
        bool: True if sent successfully
    """
    if not mentioned_staff.fcm_token:
        return False
    
    sender_name = (
        f"{sender_staff.first_name} {sender_staff.last_name}".strip()
    )
    
    # Highlight mention in title
    if conversation.is_group:
        title = f"@️⃣ {sender_name} mentioned you in {conversation.title or 'Group Chat'}"
    else:
        title = f"@️⃣ {sender_name} mentioned you"
    
    body = message_text[:100] if message_text else "Check the message"
    
    data = {
        "type": "staff_chat_mention",
        "conversation_id": str(conversation.id),
        "sender_id": str(sender_staff.id),
        "sender_name": sender_name,
        "mentioned_staff_id": str(mentioned_staff.id),
        "is_group": str(conversation.is_group),
        "hotel_slug": conversation.hotel.slug,
        "priority": "high",  # Mentions are high priority
        "click_action": f"/staff-chat/{conversation.hotel.slug}/conversation/{conversation.id}",
        "url": f"https://hotelsmates.com/staff-chat/{conversation.hotel.slug}/conversation/{conversation.id}"
    }
    
    try:
        result = send_fcm_notification(
            mentioned_staff.fcm_token,
            title,
            body,
            data=data
        )
        
        if result:
            logger.info(
                f"✅ Mention FCM sent to staff {mentioned_staff.id}"
            )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to send mention FCM to staff {mentioned_staff.id}: {e}"
        )
        return False


def send_new_conversation_notification(
    participant_staff,
    creator_staff,
    conversation
):
    """
    Send FCM notification when staff is added to a new conversation
    
    Args:
        participant_staff: Staff instance being added
        creator_staff: Staff instance who created the conversation
        conversation: StaffConversation instance
    
    Returns:
        bool: True if sent successfully
    """
    if not participant_staff.fcm_token:
        return False
    
    creator_name = (
        f"{creator_staff.first_name} {creator_staff.last_name}".strip()
    )
    
    if conversation.is_group:
        title = f"👥 New Group Chat: {conversation.title or 'Unnamed Group'}"
        body = f"{creator_name} added you to a group conversation"
    else:
        title = f"💬 New Chat with {creator_name}"
        body = "You can now start chatting"
    
    data = {
        "type": "staff_chat_new_conversation",
        "conversation_id": str(conversation.id),
        "creator_id": str(creator_staff.id),
        "creator_name": creator_name,
        "is_group": str(conversation.is_group),
        "hotel_slug": conversation.hotel.slug,
        "click_action": f"/staff-chat/{conversation.hotel.slug}/conversation/{conversation.id}",
        "url": f"https://hotelsmates.com/staff-chat/{conversation.hotel.slug}/conversation/{conversation.id}"
    }
    
    try:
        result = send_fcm_notification(
            participant_staff.fcm_token,
            title,
            body,
            data=data
        )
        
        if result:
            logger.info(
                f"✅ New conversation FCM sent to staff {participant_staff.id}"
            )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to send new conversation FCM: {e}"
        )
        return False


def send_file_attachment_notification(
    recipient_staff,
    sender_staff,
    conversation,
    file_count,
    file_types
):
    """
    Send FCM notification for file attachments
    
    Args:
        recipient_staff: Staff instance receiving notification
        sender_staff: Staff instance who sent files
        conversation: StaffConversation instance
        file_count: Number of files attached
        file_types: List of file types (e.g., ['image', 'pdf'])
    
    Returns:
        bool: True if sent successfully
    """
    if not recipient_staff.fcm_token:
        return False
    
    sender_name = (
        f"{sender_staff.first_name} {sender_staff.last_name}".strip()
    )
    
    # Determine icon based on file types
    if 'image' in file_types:
        icon = "📷"
        file_desc = f"{file_count} image(s)"
    elif 'pdf' in file_types:
        icon = "📄"
        file_desc = f"{file_count} document(s)"
    else:
        icon = "📎"
        file_desc = f"{file_count} file(s)"
    
    if conversation.is_group:
        title = (
            f"{icon} {sender_name} in "
            f"{conversation.title or 'Group Chat'}"
        )
    else:
        title = f"{icon} {sender_name}"
    
    body = f"Sent {file_desc}"
    
    data = {
        "type": "staff_chat_file",
        "conversation_id": str(conversation.id),
        "sender_id": str(sender_staff.id),
        "sender_name": sender_name,
        "file_count": str(file_count),
        "has_attachments": "true",
        "is_group": str(conversation.is_group),
        "hotel_slug": conversation.hotel.slug,
        "click_action": f"/staff-chat/{conversation.hotel.slug}/conversation/{conversation.id}",
        "url": f"https://hotelsmates.com/staff-chat/{conversation.hotel.slug}/conversation/{conversation.id}"
    }
    
    try:
        result = send_fcm_notification(
            recipient_staff.fcm_token,
            title,
            body,
            data=data
        )
        
        if result:
            logger.info(
                f"✅ File attachment FCM sent to staff {recipient_staff.id}"
            )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to send file attachment FCM: {e}"
        )
        return False


def notify_conversation_participants(
    conversation,
    sender_staff,
    message_text,
    exclude_sender=True,
    mentions=None
):
    """
    Send FCM notifications to all participants in a conversation
    
    Args:
        conversation: StaffConversation instance
        sender_staff: Staff instance who sent the message
        message_text: Message preview text
        exclude_sender: If True, don't notify the sender
        mentions: List of staff IDs who were mentioned (get priority)
    
    Returns:
        tuple: (success_count, total_count)
    """
    participants = conversation.participants.all()
    
    if exclude_sender:
        participants = participants.exclude(id=sender_staff.id)
    
    success_count = 0
    total_count = participants.count()
    
    for participant in participants:
        # Check if this participant was mentioned
        is_mentioned = mentions and participant.id in mentions
        
        if is_mentioned:
            # Send mention notification (higher priority)
            result = send_mention_notification(
                participant,
                sender_staff,
                conversation,
                message_text
            )
        else:
            # Send regular message notification
            result = send_new_message_notification(
                participant,
                sender_staff,
                conversation,
                message_text
            )
        
        if result:
            success_count += 1
    
    logger.info(
        f"FCM notifications: {success_count}/{total_count} sent "
        f"for conversation {conversation.id}"
    )
    
    return (success_count, total_count)
