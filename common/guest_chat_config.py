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


# Contract events returned to frontend at bootstrap
GUEST_CHAT_EVENTS = {
    "message_created": "chat.message.created",
    "message_read": "chat.message.read",
}

# Internal broadcast events (not part of frontend bootstrap contract)
GUEST_CHAT_INTERNAL_EVENTS = {
    "message_deleted": "chat.message.deleted",
    "message_edited": "chat.message.edited",
    "unread_updated": "chat.unread.updated",
}
