"""
Staff CRUD Views for Hotel Content Management (B5)
Provides staff-only CRUD operations for:
- Offers
- Leisure Activities
- Room Types (marketing)
- Rooms (inventory)
- Access Configuration
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from staff_chat.permissions import IsStaffMember, IsSameHotel
from .models import Offer, LeisureActivity, HotelAccessConfig
from rooms.models import RoomType, Room
from .serializers import (
    OfferStaffSerializer,
    LeisureActivityStaffSerializer,
    RoomTypeStaffSerializer,
    HotelAccessConfigStaffSerializer,
)
from rooms.serializers import RoomStaffSerializer


class StaffOfferViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for hotel offers.
    Scoped to staff's hotel only.
    """
    serializer_class = OfferStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Only return offers for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return Offer.objects.filter(
                hotel=staff.hotel
            ).order_by('sort_order', '-created_at')
        except AttributeError:
            return Offer.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set hotel from staff profile"""
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel)


class StaffLeisureActivityViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for leisure activities.
    Scoped to staff's hotel only.
    """
    serializer_class = LeisureActivityStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Only return activities for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return LeisureActivity.objects.filter(
                hotel=staff.hotel
            ).order_by('category', 'sort_order', 'name')
        except AttributeError:
            return LeisureActivity.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set hotel from staff profile"""
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel)


class StaffRoomTypeViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for room types (marketing).
    Scoped to staff's hotel only.
    """
    serializer_class = RoomTypeStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Only return room types for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return RoomType.objects.filter(
                hotel=staff.hotel
            ).order_by('sort_order', 'name')
        except AttributeError:
            return RoomType.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set hotel from staff profile"""
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel)
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        """
        Upload or update room type image.
        Accepts either file upload or image URL.
        
        POST /api/staff/hotel/{slug}/hotel/staff/room-types/{id}/upload-image/
        
        Body (multipart/form-data or JSON):
        - photo: file upload (multipart)
        OR
        - photo_url: image URL string (JSON)
        """
        room_type = self.get_object()
        
        # Check for file upload
        if 'photo' in request.FILES:
            photo_file = request.FILES['photo']
            room_type.photo = photo_file
            room_type.save()
            
            return Response({
                'message': 'Image uploaded successfully',
                'photo_url': room_type.photo.url if room_type.photo else None
            }, status=status.HTTP_200_OK)
        
        # Check for URL in request data
        elif 'photo_url' in request.data:
            photo_url = request.data['photo_url']
            
            if not photo_url:
                return Response(
                    {'error': 'photo_url cannot be empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # CloudinaryField accepts URLs directly
            room_type.photo = photo_url
            room_type.save()
            
            return Response({
                'message': 'Image URL saved successfully',
                'photo_url': room_type.photo.url if room_type.photo else None
            }, status=status.HTTP_200_OK)
        
        else:
            return Response(
                {'error': 'Please provide either a photo file or photo_url'},
                status=status.HTTP_400_BAD_REQUEST
            )


class StaffRoomViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for rooms (physical inventory).
    Scoped to staff's hotel only.
    Includes actions for PIN and QR code generation.
    """
    serializer_class = RoomStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Only return rooms for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return Room.objects.filter(
                hotel=staff.hotel
            ).order_by('room_number')
        except AttributeError:
            return Room.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set hotel from staff profile"""
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel)
    
    @action(detail=True, methods=['post'])
    def generate_pin(self, request, pk=None):
        """Generate new guest PIN for room"""
        room = self.get_object()
        room.generate_guest_pin()
        return Response({
            'message': 'PIN generated successfully',
            'guest_id_pin': room.guest_id_pin
        })
    
    @action(detail=True, methods=['post'])
    def generate_qr(self, request, pk=None):
        """Generate QR codes for room"""
        room = self.get_object()
        qr_type = request.data.get('type', 'room_service')
        
        if qr_type == 'room_service':
            room.generate_qr_code('room_service')
        elif qr_type == 'breakfast':
            room.generate_qr_code('in_room_breakfast')
        elif qr_type == 'chat_pin':
            room.generate_chat_pin_qr_code()
        elif qr_type == 'restaurant':
            # Need restaurant slug
            restaurant_slug = request.data.get('restaurant_slug')
            if not restaurant_slug:
                return Response(
                    {'error': 'restaurant_slug required for restaurant QR'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            from bookings.models import Restaurant
            restaurant = get_object_or_404(
                Restaurant,
                hotel=room.hotel,
                slug=restaurant_slug
            )
            room.generate_booking_qr_for_restaurant(restaurant)
        else:
            return Response(
                {'error': f'Invalid QR type: {qr_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(room)
        return Response(serializer.data)


class StaffAccessConfigViewSet(viewsets.ModelViewSet):
    """
    Staff endpoint to manage hotel access configuration.
    OneToOne relationship - only one config per hotel.
    Only supports GET/PUT/PATCH (no create/delete).
    """
    serializer_class = HotelAccessConfigStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    http_method_names = ['get', 'put', 'patch']
    
    def get_queryset(self):
        """Only return config for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return HotelAccessConfig.objects.filter(hotel=staff.hotel)
        except AttributeError:
            return HotelAccessConfig.objects.none()
    
    def get_object(self):
        """Get or create config for staff's hotel"""
        staff = self.request.user.staff_profile
        config, created = HotelAccessConfig.objects.get_or_create(
            hotel=staff.hotel
        )
        return config
