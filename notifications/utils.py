# HotelMateBackend/notifications/utils.py

import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from staff.models import Staff


FIREBASE_PROJECT_ID = "hotel-mate-d878f"
FIREBASE_KEY_PATH = "HotelMateBackend/secrets/hotel-mate-d878f-07c59aad1fb8.json"

def get_access_token():
    credentials = service_account.Credentials.from_service_account_file(
        FIREBASE_KEY_PATH,
        scopes=["https://www.googleapis.com/auth/firebase.messaging"],
    )
    credentials.refresh(Request())
    return credentials.token

def send_fcm_v1_notification(token, title, body, data=None):
    access_token = get_access_token()
    url = f"https://fcm.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/messages:send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "message": {
            "token": token,
            "notification": {"title": title, "body": body},
            "data": data or {},
            "android": {"priority": "high"},
            "apns": {"payload": {"aps": {"sound": "default"}}},
        }
    }
    print(f"\n--- Sending Notification ---")
    print(f"To FCM Token: {token}")
    print(f"Title: {title}")
    print(f"Body: {body}")
    print(f"Extra Data: {data}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"FCM Response Status: {response.status_code}")
        print(f"FCM Response Data: {response.text}")
        return response.json()
    except Exception as e:
        print(f"Error sending notification: {e}")
        return {"error": str(e)}


def notify_porters_of_room_service_order(order):
    # Find Porters, on duty, active, in correct hotel, with token
    porters = Staff.objects.filter(
        hotel=order.hotel,
        role='porter',
        is_active=True,
        is_on_duty=True,
    ).exclude(fcm_token__isnull=True).exclude(fcm_token__exact="")

    for porter in porters:
        send_fcm_v1_notification(
            porter.fcm_token,
            title="New Room Service Order",
            body=f"Room {order.room_number}: Total ${order.total_price:.2f}",
            data={"order_id": str(order.id), "type": "room_service"}

        )

