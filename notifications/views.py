from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# FCM token functionality has been moved to /api/staff/save-fcm-token/
# This redirect view helps with migration
class SaveFcmTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({
            "error": (
                "FCM token endpoint has moved to "
                "/api/staff/save-fcm-token/"
            ),
            "new_endpoint": "/api/staff/save-fcm-token/",
            "message": "Please update your frontend to use the new endpoint"
        }, status=410)  # 410 Gone - resource permanently moved



