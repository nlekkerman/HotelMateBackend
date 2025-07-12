# ar_navigation/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ARAnchor
from .serializers import ARAnchorSerializer

class ARAnchorViewSet(viewsets.ModelViewSet):
    queryset = ARAnchor.objects.select_related("hotel", "restaurant")
    serializer_class = ARAnchorSerializer
    lookup_field = "id"

    @action(detail=True, methods=["post"])
    def regenerate_qr(self, request, pk=None):
        anchor = self.get_object()
        anchor.generate_qr_code()
        return Response(
            {"qr_code_url": anchor.qr_code_url},
            status=status.HTTP_200_OK
        )
