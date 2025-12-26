from django.urls import path
from .views import SaveFcmTokenView, PusherAuthView

urlpatterns = [
    path("save-fcm-token/", SaveFcmTokenView.as_view(), name="save-fcm-token"),
    path("pusher/auth/", PusherAuthView.as_view(), name="pusher-auth"),
]
