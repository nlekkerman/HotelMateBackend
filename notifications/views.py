from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import AnonymousUser
import json
import hmac
import hashlib
import logging
from django.conf import settings
from staff.models import Staff
from hotel.models import GuestBookingToken

logger = logging.getLogger(__name__)


class PusherAuthView(APIView):
    """
    Dual-mode Pusher authentication endpoint.
    
    Mode 1 - Staff auth: JWT/session-based authentication for staff channels
    Mode 2 - Guest token auth: Guest token authentication for booking-specific channels
    
    Channel Access Rules:
    - Staff: {hotelSlug}.room-bookings, {hotelSlug}.rooms, etc.
    - Guests: ONLY private-guest-booking.{booking_id}
    
    CRITICAL: Guest tokens must hard-reject any {hotelSlug}.* channels
    """
    permission_classes = [AllowAny]  # Custom auth logic inside
    
    def post(self, request, hotel_slug=None):
        socket_id = request.data.get('socket_id')
        channel_name = request.data.get('channel_name')
        # Check token in multiple places: querystring, body, headers
        guest_token = (
            request.GET.get('token') or 
            request.data.get('token') or 
            request.data.get('guest_token') or 
            request.headers.get('Authorization', '').replace('Bearer ', '')
        )
        
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
        Mode 2: Guest token authentication for booking channels
        """
        # CRITICAL: Hard reject any hotel channels for guest tokens
        if '.' in channel_name and not channel_name.startswith('private-guest-booking.'):
            logger.warning(f"Guest auth rejected: attempted access to staff channel {channel_name}")
            return Response({"error": "Guest tokens cannot access staff channels"}, status=403)
        
        # Validate guest booking channel format
        if not channel_name.startswith('private-guest-booking.'):
            logger.warning(f"Guest auth rejected: invalid channel format {channel_name}")
            return Response({"error": "Invalid channel format for guest token"}, status=403)
        
        # Extract booking ID from channel name
        try:
            booking_id = channel_name.replace('private-guest-booking.', '')
        except:
            logger.error(f"Guest auth failed: invalid booking channel format {channel_name}")
            return Response({"error": "Invalid booking channel format"}, status=400)
        
        # Validate guest token
        token_obj = GuestBookingToken.validate_token(guest_token, booking_id)
        if not token_obj:
            logger.warning(f"Guest auth failed: invalid token for booking {booking_id}")
            logger.warning(f"Frontend sent token: {guest_token[:20]}... (length: {len(guest_token)})")
            # Debug: Check if any tokens exist for this booking
            from hotel.models import RoomBooking
            try:
                booking = RoomBooking.objects.get(booking_id=booking_id)
                existing_tokens = GuestBookingToken.objects.filter(booking=booking, revoked_at__isnull=True)
                logger.warning(f"Existing valid tokens for {booking_id}: {existing_tokens.count()}")
            except:
                logger.warning(f"Booking {booking_id} not found during debug")
            return Response({"error": "UNAUTHORIZED", "detail": "Invalid or expired guest token"}, status=403)
        
        # Generate Pusher auth signature for guest
        auth = self._generate_pusher_auth(socket_id, channel_name, {
            "user_id": f"guest-{token_obj.booking.booking_id}",
            "user_info": {
                "type": "guest",
                "booking_id": token_obj.booking.booking_id,
                "hotel": token_obj.hotel.slug
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



