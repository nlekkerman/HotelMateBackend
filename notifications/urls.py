from django.urls import path
from .views import SaveFcmTokenView

urlpatterns = [
    path("save-fcm-token/", SaveFcmTokenView.as_view(), name="save-fcm-token"),
]
