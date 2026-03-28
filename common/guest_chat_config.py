"""
Guest Chat Configuration — Single Source of Truth

Canonical channel naming and event constants for the guest realtime
chat system. Every piece of code that references channel names or
event names MUST use these definitions.
"""


def guest_chat_channel(hotel_slug: str, booking_id: str) -> str:
    """Canonical Pusher channel for a guest chat conversation.

    MUST be the ONLY source for guest chat channel names.
    Used in: bootstrap response, pusher auth, all broadcasts.
    """
    return f"private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}"


# Canonical guest chat event names — ALL exposed to frontend at bootstrap
GUEST_CHAT_EVENTS = {
    "message_created": "chat.message.created",
    "message_read": "chat.message.read",
    "message_deleted": "chat.message.deleted",
    "message_edited": "chat.message.edited",
    "unread_updated": "chat.unread.updated",
}

# Backward-compat alias — code that still imports GUEST_CHAT_INTERNAL_EVENTS
# will continue to work. New code should use GUEST_CHAT_EVENTS directly.
GUEST_CHAT_INTERNAL_EVENTS = {
    "message_deleted": GUEST_CHAT_EVENTS["message_deleted"],
    "message_edited": GUEST_CHAT_EVENTS["message_edited"],
    "unread_updated": GUEST_CHAT_EVENTS["unread_updated"],
}
