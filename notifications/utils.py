import os
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from staff.models import Staff

import logging
logger = logging.getLogger(__name__)

# Cached credentials
_creds = None

# Path to local service-account JSON (fallback)
LOCAL_KEY_RELATIVE_PATH = "HotelMateBackend/secrets/hotel-mate-d878f-07c59aad1fb8.json"


def _get_creds():
    """
    Load and cache service-account credentials for FCM v1 API.
    """
    global _creds
    if _creds is not None:
        return _creds

    # Load JSON from environment or file
    key_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")

    if key_json:
        info = json.loads(key_json)
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
    else:
        here = os.path.dirname(__file__)
        key_path = os.path.join(here, LOCAL_KEY_RELATIVE_PATH)
        with open(key_path, "r", encoding="utf-8") as f:
            info = json.load(f)

    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/firebase.messaging"],
    )
    creds.refresh(Request())
    _creds = creds
    return _creds


def _post_fcm(payload: dict):
    """
    Send a payload to the FCM v1 send endpoint.
    """
    creds = _get_creds()
    project_id = creds.project_id
    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("FCM send error: %s", e)
        raise


def send_fcm_v1_notification(token: str, title: str, body: str, data: dict = None):
    """
    Send a visible FCM notification to a specific device token.
    """
    message = {
        "message": {
            "token": token,
            "notification": {"title": title, "body": body},
            "android": {"priority": "high"},
            "apns": {"payload": {"aps": {"sound": "default"}}},
        }
    }
    if data:
        message["message"]["data"] = data
    return _post_fcm(message)


def send_fcm_data_message(token: str, data: dict):
    """
    Send a silent (data-only) FCM message to a specific device token.
    """
    message = {
        "message": {
            "token": token,
            "data": data,
            "android": {"priority": "high"},
            "apns": {"payload": {"aps": {"content-available": 1}}},
        }
    }
    return _post_fcm(message)


def notify_porters_of_room_service_order(order):
    """
    Notify all active, on-duty porters of a new room service order 
    via a data-only FCM message so that the service worker shows it.
    """
    porters = (
        Staff.objects
        .filter(
            hotel=order.hotel,
            role__slug="porter",
            is_active=True,
            is_on_duty=True,
            fcm_tokens__token__isnull=False
        )
        .exclude(fcm_tokens__token="")
        .distinct()
    )

    for porter in porters:
        for token in porter.fcm_tokens.values_list("token", flat=True):
            try:
                # send only data—no top-level "notification" field
                send_fcm_data_message(
                    token,
                    {
                        "title": f"New Room Service Order",
                        "body": f"Room {order.room_number}: Total €{order.total_price:.2f}",
                        "type": "room_service",
                        "order_id": str(order.id),
                    }
                )
            except Exception:
                logger.exception("Failed to send room service data‐only message to %s", token)

def notify_porters_order_count(hotel):
    """
    Send a silent data-only update of pending order count to all active, on-duty porters.
    """
    pending = hotel.order_set.filter(status="pending").count()
    data = {"type": "order_count", "count": str(pending)}

    porters = (
        Staff.objects
        .filter(
            hotel=hotel,
            role="porter",
            is_active=True,
            is_on_duty=True,
            fcm_tokens__token__isnull=False
        )
        .exclude(fcm_tokens__token="")
        .distinct()
    )
    for porter in porters:
        tokens = porter.fcm_tokens.values_list("token", flat=True)
        for token in tokens:
            try:
                send_fcm_data_message(token, data)
            except Exception:
                logger.exception("Failed to send order-count update to %s", token)


def notify_porters_of_breakfast_order(order):
    """
    Notify all active, on-duty porters of a new breakfast order with a visible notification.
    """
    porters = (
        Staff.objects
        .filter(
            hotel=order.hotel,
            role="porter",
            is_active=True,
            is_on_duty=True,
            fcm_tokens__token__isnull=False
        )
        .exclude(fcm_tokens__token="")
        .distinct()
    )
    for porter in porters:
        tokens = porter.fcm_tokens.values_list("token", flat=True)
        for token in tokens:
            try:
                send_fcm_v1_notification(
                    token,
                    title="New Breakfast Order",
                    body=f"Room {order.room_number}",
                    data={"order_id": str(order.id), "type": "breakfast"},
                )
            except Exception:
                logger.exception("Failed to send breakfast notification to %s", token)


def notify_porters_breakfast_count(hotel):
    """
    Send a silent data-only update of pending breakfast count to all active, on-duty porters.
    """
    from room_services.models import BreakfastOrder
    pending = BreakfastOrder.objects.filter(hotel=hotel, status="pending").count()
    data = {"type": "breakfast_count", "count": str(pending)}

    porters = (
        Staff.objects
        .filter(
            hotel=hotel,
            role="porter",
            is_active=True,
            is_on_duty=True,
            fcm_tokens__token__isnull=False
        )
        .exclude(fcm_tokens__token="")
        .distinct()
    )
    for porter in porters:
        tokens = porter.fcm_tokens.values_list("token", flat=True)
        for token in tokens:
            try:
                send_fcm_data_message(token, data)
            except Exception:
                logger.exception("Failed to send breakfast-count update to %s", token)
