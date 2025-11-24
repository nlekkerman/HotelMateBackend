"""
Room booking views for external booking system.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status


class BookingDetailView(APIView):
    """
    Get booking details by booking ID.
    Phase 1: Returns mock data based on booking ID format.
    
    GET /api/bookings/<booking_id>/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, booking_id):
        # Phase 1: Return placeholder booking data
        # In Phase 2, this would query the database
        
        # Extract info from booking_id format: BK-YYYY-XXXXXX
        try:
            parts = booking_id.split('-')
            if len(parts) != 3 or parts[0] != 'BK':
                return Response(
                    {"detail": "Invalid booking ID format"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            year = parts[1]
            code = parts[2]
            
        except (IndexError, ValueError):
            return Response(
                {"detail": "Invalid booking ID format"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return mock booking data
        booking_data = {
            "booking_id": booking_id,
            "confirmation_number": f"HOT-{year}-{code[:4]}",
            "status": "PENDING_PAYMENT",
            "created_at": f"{year}-11-24T15:30:00Z",
            "hotel": {
                "name": "Hotel Killarney",
                "slug": "hotel-killarney",
                "phone": "+353 64 663 1555",
                "email": "info@hotelkillarney.ie"
            },
            "room": {
                "type": "Deluxe King Room",
                "code": "DLX-KING",
                "photo": None
            },
            "dates": {
                "check_in": "2025-12-20",
                "check_out": "2025-12-22",
                "nights": 2
            },
            "guests": {
                "adults": 2,
                "children": 0,
                "total": 2
            },
            "guest": {
                "name": "Guest Name",
                "email": "guest@example.com",
                "phone": "+353 87 123 4567"
            },
            "special_requests": "",
            "pricing": {
                "subtotal": "300.00",
                "taxes": "27.00",
                "discount": "0.00",
                "total": "327.00",
                "currency": "EUR"
            },
            "promo_code": None,
            "payment_required": True,
            "payment_url": f"/api/bookings/{booking_id}/payment/session/"
        }
        
        return Response(booking_data, status=status.HTTP_200_OK)
