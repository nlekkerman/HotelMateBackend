from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
import json
import hmac
import hashlib
import logging
from django.conf import settings
from staff.models import Staff
from common.guest_access import (
    resolve_guest_access,
    resolve_guest_access_without_slug,
    GuestAccessError,
    InvalidTokenError,
)

logger = logging.getLogger(__name__)


class PusherAuthView(APIView):
    """
    Dual-mode Pusher authentication endpoint.
    
    Mode 1 - Staff auth: JWT/session-based authentication for staff channels
    Mode 2 - Guest token auth: Guest token authentication for booking-specific channels
    
    Channel Access Rules:
    - Staff: {hotelSlug}.room-bookings, {hotelSlug}.rooms, etc.
    - Guests: ONLY private-hotel-{slug}-guest-chat-booking-{booking_id}
    
    CRITICAL: Guest tokens must hard-reject any non-guest channels
    """
    authentication_classes = []  # Staff auth checked manually; guest tokens use our own resolver
    permission_classes = [AllowAny]  # Custom auth logic inside
    
    def post(self, request, hotel_slug=None):
        socket_id = request.data.get('socket_id')
        channel_name = request.data.get('channel_name')
        # Guest token: prefer ?token= query param, fall back to body/GuestToken header
        guest_token = (
            request.GET.get('token') or 
            request.data.get('token') or 
            request.data.get('guest_token')
        )
        # Also check GuestToken header (NOT Bearer — that's staff)
        if not guest_token:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('GuestToken '):
                guest_token = auth_header[11:]
        
        logger.info(f"Pusher auth request: channel={channel_name}, has_token={bool(guest_token)}, hotel_slug={hotel_slug}")
        
        if not socket_id or not channel_name:
            logger.error("Pusher auth missing required fields")
            return Response({"error": "Missing socket_id or channel_name"}, status=400)
        
        # Determine auth mode
        if guest_token:
            return self._handle_guest_auth(socket_id, channel_name, guest_token)
        else:
            return self._handle_staff_auth(request, socket_id, channel_name)
    
    def _handle_staff_auth(self, request, socket_id, channel_name):
        """
        Mode 1: Staff authentication for hotel channels
        """
        # Require staff authentication
        if isinstance(request.user, AnonymousUser) or not request.user.is_authenticated:
            logger.warning(f"Staff auth failed: unauthenticated user for channel {channel_name}")
            return Response({"error": "Staff authentication required"}, status=401)
        
        # Get staff profile
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            logger.warning(f"Staff auth failed: no staff profile for user {request.user.id}")
            return Response({"error": "Staff profile not found"}, status=401)
        
        # Validate channel access for staff
        hotel_slug = staff.hotel.slug
        allowed_patterns = [
            f"{hotel_slug}.room-bookings",
            f"{hotel_slug}.rooms", 
            f"{hotel_slug}-staff-",  # Staff-specific channels
            f"attendance-{hotel_slug}-",  # Attendance channels
            f"private-hotel-{hotel_slug}-guest-chat-booking-",  # Guest booking channels (for chat support)
        ]
        
        if not any(channel_name.startswith(pattern) for pattern in allowed_patterns):
            logger.warning(f"Staff auth failed: channel access denied for {channel_name} (hotel: {hotel_slug})")
            return Response({"error": "Channel access denied for staff"}, status=403)
        
        # Generate Pusher auth signature
        auth = self._generate_pusher_auth(socket_id, channel_name, {
            "user_id": staff.id,
            "user_info": {
                "name": f"{staff.first_name} {staff.last_name}",
                "hotel": hotel_slug,
                "role": staff.role.slug if staff.role else None
            }
        })
        
        logger.info(f"Staff auth successful: user={staff.id}, channel={channel_name}")
        return Response(auth)
    
    def _handle_guest_auth(self, socket_id, channel_name, guest_token):
        """
        Legacy guest token path — DISABLED.
        Guest Pusher auth is now handled exclusively by the canonical endpoint:
        /api/guest/hotel/{slug}/chat/pusher/auth (with X-Guest-Chat-Session header)
        """
        logger.warning(
            f"Guest token submitted to legacy PusherAuthView — rejecting. "
            f"channel={channel_name}"
        )
        return Response(
            {
                "error": "Guest Pusher auth has moved",
                "code": "ENDPOINT_MOVED",
                "detail": "Use /api/guest/hotel/{slug}/chat/pusher/auth with X-Guest-Chat-Session header",
            },
            status=403,
        )
    
    def _generate_pusher_auth(self, socket_id, channel_name, channel_data=None):
        """
        Generate Pusher authentication signature
        """
        if channel_data:
            channel_data_str = json.dumps(channel_data)
            string_to_sign = f"{socket_id}:{channel_name}:{channel_data_str}"
        else:
            string_to_sign = f"{socket_id}:{channel_name}"
        
        signature = hmac.new(
            settings.PUSHER_SECRET.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        auth_string = f"{settings.PUSHER_KEY}:{signature}"
        
        result = {"auth": auth_string}
        if channel_data:
            result["channel_data"] = channel_data_str
        
        return result


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



