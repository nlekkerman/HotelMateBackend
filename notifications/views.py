from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from staff.models import Staff
from notifications.utils import send_fcm_v1_notification



class SaveFcmTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('fcm_token')
        if not token:
            return Response({"error": "No FCM token provided."}, status=400)
        staff = Staff.objects.filter(user=request.user).first()
        if not staff:
            return Response({"error": "Staff profile not found."}, status=404)
        staff.fcm_token = token
        staff.save()
        return Response({"status": "success"})



