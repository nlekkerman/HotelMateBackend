"""
Pusher utilities for Stock Tracker
Real-time event broadcasting for stocktake changes
"""
import logging
from chat.utils import pusher_client

logger = logging.getLogger(__name__)


def get_stocktake_channel(hotel_identifier, stocktake_id):
    """Get Pusher channel name for a specific stocktake"""
    return f"{hotel_identifier}-stocktake-{stocktake_id}"


def get_hotel_stocktakes_channel(hotel_identifier):
    """Get Pusher channel name for all stocktakes in a hotel"""
    return f"{hotel_identifier}-stocktakes"


def trigger_stocktake_event(hotel_identifier, stocktake_id, event, data):
    """
    Trigger event on stocktake channel
    All users viewing this stocktake will receive this
    """
    channel = get_stocktake_channel(hotel_identifier, stocktake_id)
    try:
        pusher_client.trigger(channel, event, data)
        logger.info(
            f"Pusher: stocktake channel={channel}, event={event}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to trigger Pusher on {channel}: {e}"
        )
        return False


def trigger_hotel_stocktakes_event(hotel_identifier, event, data):
    """
    Trigger event on hotel stocktakes channel
    All users viewing stocktakes list will receive this
    """
    channel = get_hotel_stocktakes_channel(hotel_identifier)
    try:
        pusher_client.trigger(channel, event, data)
        logger.info(
            f"Pusher: hotel stocktakes channel={channel}, event={event}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to trigger Pusher on {channel}: {e}"
        )
        return False


# ============================================================================
# STOCKTAKE EVENTS (List View)
# ============================================================================

def broadcast_stocktake_created(hotel_identifier, stocktake_data):
    """Broadcast new stocktake creation to hotel stocktakes list"""
    return trigger_hotel_stocktakes_event(
        hotel_identifier,
        "stocktake-created",
        stocktake_data
    )


def broadcast_stocktake_deleted(hotel_identifier, stocktake_id):
    """Broadcast stocktake deletion to hotel stocktakes list"""
    return trigger_hotel_stocktakes_event(
        hotel_identifier,
        "stocktake-deleted",
        {"stocktake_id": stocktake_id}
    )


def broadcast_stocktake_status_changed(
    hotel_identifier, stocktake_id, stocktake_data
):
    """
    Broadcast stocktake status change (DRAFT -> APPROVED)
    Sent to both list view and detail view
    """
    # Notify list view
    trigger_hotel_stocktakes_event(
        hotel_identifier,
        "stocktake-status-changed",
        stocktake_data
    )
    
    # Notify detail view
    return trigger_stocktake_event(
        hotel_identifier,
        stocktake_id,
        "stocktake-status-changed",
        stocktake_data
    )


# ============================================================================
# STOCKTAKE LINE EVENTS (Detail View - Individual Lines)
# ============================================================================

def broadcast_line_counted_updated(
    hotel_identifier, stocktake_id, line_data
):
    """
    Broadcast when user updates counted quantities for a line
    All users viewing this stocktake will see the update
    """
    return trigger_stocktake_event(
        hotel_identifier,
        stocktake_id,
        "line-counted-updated",
        line_data
    )


def broadcast_line_movement_added(
    hotel_identifier, stocktake_id, movement_data
):
    """
    Broadcast when a movement (purchase/waste) is added to a line
    Updates expected quantities and variance for all viewers
    """
    return trigger_stocktake_event(
        hotel_identifier,
        stocktake_id,
        "line-movement-added",
        movement_data
    )


def broadcast_line_movement_deleted(
    hotel_identifier, stocktake_id, deletion_data
):
    """
    Broadcast when a movement is deleted from a line
    Updates expected quantities and variance for all viewers
    """
    return trigger_stocktake_event(
        hotel_identifier,
        stocktake_id,
        "line-movement-deleted",
        deletion_data
    )


def broadcast_stocktake_populated(
    hotel_identifier, stocktake_id, populate_data
):
    """
    Broadcast when stocktake is populated with items
    All viewers will see the full list of lines appear
    """
    return trigger_stocktake_event(
        hotel_identifier,
        stocktake_id,
        "stocktake-populated",
        populate_data
    )


# ============================================================================
# BULK UPDATE EVENTS
# ============================================================================

def broadcast_bulk_lines_updated(hotel_identifier, stocktake_id, bulk_data):
    """
    Broadcast when multiple lines are updated at once
    Useful for batch imports or bulk edits
    """
    return trigger_stocktake_event(
        hotel_identifier,
        stocktake_id,
        "bulk-lines-updated",
        bulk_data
    )


# ============================================================================
# USER PRESENCE EVENTS (Optional - for "who's viewing" feature)
# ============================================================================

def broadcast_user_joined(hotel_identifier, stocktake_id, user_data):
    """
    Broadcast when a user starts viewing a stocktake
    Can show "John is viewing this stocktake"
    """
    return trigger_stocktake_event(
        hotel_identifier,
        stocktake_id,
        "user-joined",
        user_data
    )


def broadcast_user_left(hotel_identifier, stocktake_id, user_data):
    """
    Broadcast when a user stops viewing a stocktake
    """
    return trigger_stocktake_event(
        hotel_identifier,
        stocktake_id,
        "user-left",
        user_data
    )


def broadcast_user_editing_line(hotel_identifier, stocktake_id, editing_data):
    """
    Broadcast when a user starts editing a specific line
    Can show "Sarah is editing Guinness Keg" to prevent conflicts
    """
    return trigger_stocktake_event(
        hotel_identifier,
        stocktake_id,
        "user-editing-line",
        editing_data
    )
