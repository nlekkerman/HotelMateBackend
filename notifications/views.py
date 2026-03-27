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
        Mode 2: Guest token authentication for booking channels.
        
        Canonical channel format: private-hotel-{slug}-guest-chat-booking-{booking_id}
        Also supports legacy format: private-guest-booking.{booking_id} (for transition)
        
        Uses resolve_guest_access (with slug) when slug is extractable from channel,
        falls back to resolve_guest_access_without_slug for legacy channels.
        """
        import re
        
        # Canonical channel: private-hotel-{slug}-guest-chat-booking-{booking_id}
        canonical_match = re.match(
            r'^private-hotel-([a-z0-9-]+)-guest-chat-booking-(.+)$',
            channel_name
        )
        # Legacy channel: private-guest-booking.{booking_id}
        legacy_match = re.match(
            r'^private-guest-booking\.(.+)$',
            channel_name
        ) if not canonical_match else None
        
        if not canonical_match and not legacy_match:
            logger.warning(f"Guest auth rejected: invalid channel format {channel_name}")
            return Response({"error": "Invalid channel format for guest token"}, status=403)
        
        clean_token = guest_token.strip()
        
        try:
            if canonical_match:
                hotel_slug = canonical_match.group(1)
                booking_id = canonical_match.group(2)
                ctx = resolve_guest_access(
                    token_str=clean_token,
                    hotel_slug=hotel_slug,
                )
            else:
                booking_id = legacy_match.group(1)
                ctx = resolve_guest_access_without_slug(clean_token)
        except GuestAccessError:
            logger.warning(f"Guest auth failed: invalid token for channel {channel_name}")
            return Response({"error": "UNAUTHORIZED", "detail": "Invalid or expired guest token"}, status=403)
        
        # Verify the resolved booking matches the channel's booking ID
        if ctx.booking.booking_id != booking_id:
            logger.warning(
                f"Guest auth failed: token booking {ctx.booking.booking_id} "
                f"does not match channel booking {booking_id}"
            )
            return Response({"error": "UNAUTHORIZED", "detail": "Token does not match channel"}, status=403)
        
        # Generate Pusher auth signature for guest
        auth = self._generate_pusher_auth(socket_id, channel_name, {
            "user_id": f"guest-{ctx.booking.booking_id}",
            "user_info": {
                "type": "guest",
                "booking_id": ctx.booking.booking_id,
                "hotel": ctx.booking.hotel.slug
            }
        })
        
        logger.info(f"Guest auth successful: booking={booking_id}, channel={channel_name}")
        return Response(auth)
    
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



