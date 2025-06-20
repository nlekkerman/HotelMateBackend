import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from staff.models import Staff


FIREBASE_PROJECT_ID = "hotel-mate-d878f"
FIREBASE_KEY_PATH   = "HotelMateBackend/secrets/hotel-mate-d878f-07c59aad1fb8.json"

def get_access_token():
    print("[FCM] get_access_token()")
    creds = service_account.Credentials.from_service_account_file(
        FIREBASE_KEY_PATH,
        scopes=["https://www.googleapis.com/auth/firebase.messaging"],
    )
    creds.refresh(Request())
    token = creds.token
    print(f"[FCM] Retrieved access token (first 20 chars): {token[:20]}…")
    return token

def _post_fcm(payload: dict):
    url = f"https://fcm.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/messages:send"
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json; UTF-8",
    }
    print(f"[FCM] POST to {url} with payload:\n{json.dumps(payload, indent=2)}")
    try:
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        print(f"[FCM] Response {resp.status_code}: {resp.text}")
        return resp.json()
    except Exception as e:
        print(f"[FCM] ERROR sending FCM: {e!r}")
        if 'resp' in locals():
            print(f"[FCM] Response body: {resp.text}")
        raise

def send_fcm_v1_notification(token: str, title: str, body: str, data: dict = None):
    print(f"[FCM] send_fcm_v1_notification → token={token}, title={title!r}, body={body!r}, data={data}")
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
    print(f"[FCM] send_fcm_data_message → token={token}, data={data}")
    msg = {
        "token": token,
        "data": data,
        "android": {"priority": "high"},
        "apns": {"payload": {"aps": {"content-available": 1}}},
    }
    return _post_fcm({"message": msg})

def notify_porters_of_room_service_order(order):
    print(f"[NOTIFY] notify_porters_of_room_service_order for Order {order.id}")
    porters = (
        Staff.objects
        .filter(
            hotel=order.hotel,
            role="porter",
            is_active=True,
            is_on_duty=True,
        )
        .exclude(fcm_token__in=[None, ""])
    )
    count = porters.count()
    print(f"[NOTIFY] Found {count} porter(s) to notify")
    for p in porters:
        print(f"[NOTIFY] Sending visible notification to porter {p.id} (token={p.fcm_token})")
        send_fcm_v1_notification(
            p.fcm_token,
            title="New Room Service Order",
            body=f"Room {order.room_number}: Total €{order.total_price:.2f}",
            data={"order_id": str(order.id), "type": "room_service"},
        )

def notify_porters_order_count(hotel):
    """
    Send a silent data-only push to all active, on-duty porters
    with the current number of pending orders.
    """
    pending = hotel.order_set.filter(status="pending").count()
    tokens = (
        Staff.objects
        .filter(
            hotel=hotel,
            role="porter",
            is_active=True,
            is_on_duty=True,
        )
        .exclude(fcm_token__in=[None, ""])
        .values_list("fcm_token", flat=True)
    )
    data = {"type": "order_count", "count": str(pending)}
    for t in tokens:
        send_fcm_data_message(t, data)
