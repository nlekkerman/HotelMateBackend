from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ARAnchor
from .serializers import ARAnchorSerializer

class ARAnchorViewSet(viewsets.ModelViewSet):
    serializer_class = ARAnchorSerializer

    def get_queryset(self):
        qs = ARAnchor.objects.select_related("hotel", "restaurant").all()
        hotel_slug      = self.request.query_params.get("hotel")
        restaurant_slug = self.request.query_params.get("restaurant")
        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
        if restaurant_slug:
            qs = qs.filter(restaurant__slug=restaurant_slug)
        return qs

    @action(detail=True, methods=["post"])
    def regenerate_qr(self, request, pk=None):
        anchor = self.get_object()
        anchor.generate_qr_code()
        return Response({"qr_code_url": anchor.qr_code_url})
