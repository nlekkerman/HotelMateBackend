# stock_tracker/stock_alerts.py

import os
import json
import requests
import logging
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from staff.models import Staff

FIREBASE_PROJECT_ID = "hotel-mate-d878f"
LOCAL_KEY_RELATIVE_PATH = "HotelMateBackend/secrets/hotel-mate-d878f-07c59aad1fb8.json"

logger = logging.getLogger(__name__)

def get_access_token():
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
    return creds.token

def _send_fcm_message(token: str, title: str, body: str, data: dict = None):
    url = f"https://fcm.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/messages:send"
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json; UTF-8",
    }

    message = {
        "token": token,
        "notification": {"title": title, "body": body},
        "android": {"priority": "high"},
        "apns": {"payload": {"aps": {"sound": "default"}}},
    }

    if data:
        message["data"] = data

    payload = {"message": message}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"[FCM] Notification failed: {e}")
        return None

def notify_super_admins_about_stock_movement(summary: str, hotel):
    print("[Stock Alert] Preparing to notify super staff admins about stock movement...")

    super_admins = (
        Staff.objects
        .filter(
            hotel=hotel,
            access_level='super_staff_admin',
            is_active=True,
        )
        .exclude(fcm_token__in=[None, "", " "])
    )

    print(f"[Stock Alert] Found {super_admins.count()} eligible super admins.")

    for admin in super_admins:
        token = admin.fcm_token
        print(f"[DEBUG] Admin: {admin.email}, Token: {repr(token)}")
        token_preview = token[:10] + "..." if token else "No Token"
        print(f"[Stock Alert] Sending FCM to: {admin.email} ({token_preview})")

        result = _send_fcm_message(
            token=token,
            title="📦 Stock Movement Logged",
            body=summary,
            data={"type": "stock_movement"}
        )
        if result:
            print(f"[Stock Alert] Notification sent successfully to {admin.email}")
        else:
            print(f"[Stock Alert] Failed to notify {admin.email}")
