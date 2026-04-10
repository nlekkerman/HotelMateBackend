"""
Hotel provisioning API view.

POST /api/hotels/provision/

Django superuser only. Creates a hotel, primary admin, staff profile,
and optional registration packages in one atomic operation.
"""
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .provisioning import provision_hotel
from .provisioning_serializers import (
    ProvisionHotelRequestSerializer,
    ProvisionHotelResponseSerializer,
)
from staff.permissions import IsDjangoSuperUser

logger = logging.getLogger(__name__)


class ProvisionHotelView(APIView):
    """
    POST /api/hotels/provision/

    Canonical hotel provisioning endpoint.
    Requires Django superuser.
    """
    permission_classes = [IsDjangoSuperUser]

    def post(self, request):
        serializer = ProvisionHotelRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = provision_hotel(serializer.validated_data)

        response_data = {
            "hotel_id": result["hotel"].id,
            "hotel_slug": result["hotel"].slug,
            "hotel_name": result["hotel"].name,
            "admin_user_id": result["admin_user"].id,
            "admin_username": result["admin_user"].username,
            "admin_email": result["admin_user"].email,
            "staff_id": result["staff"].id,
            "access_level": result["staff"].access_level,
            "department": str(result["staff"].department) if result["staff"].department else None,
            "role": str(result["staff"].role) if result["staff"].role else None,
            "registration_packages": result["registration_packages"],
            "warnings": result["warnings"],
        }

        out = ProvisionHotelResponseSerializer(response_data)
        return Response(out.data, status=status.HTTP_201_CREATED)
