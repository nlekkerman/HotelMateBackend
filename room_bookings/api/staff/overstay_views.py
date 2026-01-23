"""
Overstay management API views for staff.

Hotel-scoped endpoints for acknowledging and extending overstays.
"""
import logging
from datetime import datetime, date
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from hotel.models import Hotel, RoomBooking, OverstayIncident

logger = logging.getLogger(__name__)


class OverstayAcknowledgeView(APIView):
    """
    POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/overstay/acknowledge/
    
    Staff acknowledges awareness of overstay.
    """
    permission_classes = [IsAuthenticated]  # TODO: Add HasOverstayPermissions
    
    def post(self, request, hotel_slug, booking_id):
        try:
            # Get hotel
            hotel = Hotel.objects.get(slug=hotel_slug)
            
            # Get booking by booking_id (reference string, not pk)
            booking = RoomBooking.objects.get(
                hotel=hotel,
                booking_id=booking_id
            )
            
            # Validate booking status (must be checked in)
            if booking.status != 'CHECKED_IN':
                return Response(
                    {'detail': 'Booking not in valid state (not checked-in)'},
                    status=status.HTTP_409_CONFLICT
                )
            
            # Get request data
            note = request.data.get('note', '')
            dismiss = request.data.get('dismiss', False)
            
            # Acknowledge overstay
            result = acknowledge_overstay(
                hotel=hotel,
                booking=booking,
                staff_user=request.user,
                note=note,
                dismiss=dismiss
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Hotel.DoesNotExist:
            return Response(
                {'detail': 'Hotel not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except RoomBooking.DoesNotExist:
            return Response(
                {'detail': 'Booking not found in hotel'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error acknowledging overstay: {e}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OverstayExtendView(APIView):
    """
    POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/overstay/extend/
    
    Staff approves additional nights for overstaying guest.
    """
    permission_classes = [IsAuthenticated]  # TODO: Add HasOverstayPermissions
    
    def post(self, request, hotel_slug, booking_id):
        try:
            # Get hotel
            hotel = Hotel.objects.get(slug=hotel_slug)
            
            # Get booking by booking_id (reference string, not pk)  
            booking = RoomBooking.objects.get(
                hotel=hotel,
                booking_id=booking_id
            )
            
            # Validate booking status (must be checked in)
            if booking.status != 'CHECKED_IN':
                return Response(
                    {'detail': 'Booking not in valid state (not checked-in)'},
                    status=status.HTTP_409_CONFLICT
                )
            
            # Get request data
            new_checkout_date = request.data.get('new_checkout_date')
            add_nights = request.data.get('add_nights')
            
            # Validate exactly one input provided
            if (new_checkout_date and add_nights) or (not new_checkout_date and not add_nights):
                return Response(
                    {'detail': 'Exactly one of new_checkout_date or add_nights must be provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse new_checkout_date if provided
            if new_checkout_date:
                try:
                    new_checkout_date = datetime.strptime(new_checkout_date, '%Y-%m-%d').date()
                except ValueError:
                    return Response(
                        {'detail': 'Invalid date format. Use YYYY-MM-DD'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate new checkout date is in the future
                if new_checkout_date <= booking.check_out:
                    return Response(
                        {'detail': 'New checkout date must be after current checkout date'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Validate add_nights if provided
            if add_nights is not None:
                try:
                    add_nights = int(add_nights)
                    if add_nights < 1:
                        raise ValueError()
                except (ValueError, TypeError):
                    return Response(
                        {'detail': 'add_nights must be a positive integer'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Get idempotency key from headers
            idempotency_key = request.headers.get("Idempotency-Key") or None
            if idempotency_key:
                idempotency_key = idempotency_key.strip() or None
            
            # Extend overstay
            result = extend_overstay(
                hotel=hotel,
                booking=booking,
                staff_user=request.user,
                new_checkout_date=new_checkout_date,
                add_nights=add_nights,
                idempotency_key=idempotency_key
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Hotel.DoesNotExist:
            return Response(
                {'detail': 'Hotel not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except RoomBooking.DoesNotExist:
            return Response(
                {'detail': 'Booking not found in hotel'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ConflictError as e:
            return Response(
                {
                    'detail': e.message,
                    'conflicts': e.conflicts,
                    'suggested_rooms': e.suggestions
                },
                status=status.HTTP_409_CONFLICT
            )
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error extending overstay: {e}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OverstayStatusView(APIView):
    """
    GET /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/overstay/status/
    
    Retrieve current overstay status for booking.
    """
    permission_classes = [IsAuthenticated]  # TODO: Add HasOverstayPermissions
    
    def get(self, request, hotel_slug, booking_id):
        try:
            # Get hotel
            hotel = Hotel.objects.get(slug=hotel_slug)
            
            # Get booking by booking_id (reference string, not pk)
            booking = RoomBooking.objects.get(
                hotel=hotel,
                booking_id=booking_id
            )
            
            # Check if booking has an overstay incident
            incident = OverstayIncident.objects.filter(booking=booking).first()
            
            # Calculate if currently overstay
            now_utc = timezone.now()
            checkout_noon_utc = get_hotel_noon_utc(hotel, booking.check_out)
            is_overstay = (
                booking.status == 'CHECKED_IN' and
                booking.assigned_room is not None and
                now_utc >= checkout_noon_utc
            )
            
            result = {
                'booking_id': booking.booking_id,
                'is_overstay': is_overstay
            }
            
            if incident:
                # Calculate hours overdue
                hours_overdue = max(0, (now_utc - checkout_noon_utc).total_seconds() / 3600)
                
                result['overstay'] = {
                    'status': incident.status,
                    'detected_at': incident.detected_at.isoformat(),
                    'expected_checkout_date': incident.expected_checkout_date.isoformat(),
                    'hours_overdue': round(hours_overdue, 1)
                }
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Hotel.DoesNotExist:
            return Response(
                {'detail': 'Hotel not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except RoomBooking.DoesNotExist:
            return Response(
                {'detail': 'Booking not found in hotel'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting overstay status: {e}")
            return Response(
                {'detail': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )