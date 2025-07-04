import os
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from staff.models import Staff

FIREBASE_PROJECT_ID = "hotel-mate-d878f"
LOCAL_KEY_RELATIVE_PATH = "HotelMateBackend/secrets/hotel-mate-d878f-07c59aad1fb8.json"
import logging
logger = logging.getLogger(__name__)

def get_access_token():
    key_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")

    if key_json:
        info = json.loads(key_json)

        # Fix the private key
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
    return creds.token

def _post_fcm(payload: dict):
    url = (
        f"https://fcm.googleapis.com/v1/projects/"
        f"{FIREBASE_PROJECT_ID}/messages:send"
    )
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json; UTF-8",
    }
    try:
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # Optional: log or re-raise with more context
        raise

def send_fcm_v1_notification(token: str, title: str, body: str, data: dict = None):
    msg = {
        "token": token,
        "notification": {"title": title, "body": body},
        "android": {"priority": "high"},
        "apns": {"payload": {"aps": {"sound": "default"}}},
    }
    if data:
        msg["data"] = data
    return _post_fcm({"message": msg})

def send_fcm_data_message(token: str, data: dict):
    msg = {
        "token": token,
        "data": data,
        "android": {"priority": "high"},
        "apns": {"payload": {"aps": {"content-available": 1}}},
    }
    return _post_fcm({"message": msg})


def notify_porters_of_room_service_order(order):
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
            send_fcm_v1_notification(
                token,
                title="New Room Service Order",
                body=f"Room {order.room_number}: Total €{order.total_price:.2f}",
                data={"order_id": str(order.id), "type": "room_service"},
            )

def notify_porters_order_count(hotel):
    pending = hotel.order_set.filter(status="pending").count()
    data = {"type": "order_count", "count": str(pending)}

    porters = (
        Staff.objects
        .filter(
            hotel=hotel,
            role="porter",
            is_active=True,
            is_on_duty=True,
            fcm_tokens__isnull=False
        )
        .distinct()
    )

    for porter in porters:
        tokens = porter.fcm_tokens.values_list("token", flat=True)
        for t in tokens:
            send_fcm_data_message(t, data)


def notify_porters_of_breakfast_order(order):
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
            send_fcm_v1_notification(
                token,
                title="New Breakfast Order",
                body=f"Room {order.room_number}",
                data={"order_id": str(order.id), "type": "breakfast"},
            )

def notify_porters_breakfast_count(hotel):
    from room_services.models import BreakfastOrder  # or adjust import path
    pending = BreakfastOrder.objects.filter(hotel=hotel, status="pending").count()
    data = {"type": "breakfast_count", "count": str(pending)}

    porters = (
        Staff.objects
        .filter(
            hotel=hotel,
            role="porter",
            is_active=True,
            is_on_duty=True,
            fcm_tokens__isnull=False
        )
        .distinct()
    )

    for porter in porters:
        tokens = porter.fcm_tokens.values_list("token", flat=True)
        for t in tokens:
            send_fcm_data_message(t, data)
