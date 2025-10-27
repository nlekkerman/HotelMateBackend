from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# Firebase/FCM functionality has been removed
# This view is kept as a placeholder for future notification systems
class SaveFcmTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({
            "error": "FCM token functionality has been removed"
        }, status=400)



