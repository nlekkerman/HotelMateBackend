"""
Staff CRUD Views for Hotel Content Management
Provides staff-only CRUD operations for:
- Room Types (marketing)
- Rooms (inventory)
- Access Configuration
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from datetime import datetime, timedelta, date
from guests.models import Guest
import hashlib
import secrets
import logging
import stripe
import json

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

from staff_chat.permissions import IsStaffMember, IsSameHotel
from chat.utils import pusher_client
from notifications.notification_manager import notification_manager
from notifications.email_service import send_booking_confirmation_email, send_booking_cancellation_email
from notifications.fcm_service import send_booking_confirmation_notification, send_booking_cancellation_notification
from room_bookings.services.room_assignment import RoomAssignmentService
from room_bookings.exceptions import RoomAssignmentError
from rest_framework.pagination import PageNumberPagination
from .models import (
    Hotel,
    HotelAccessConfig,
    HotelPrecheckinConfig,
    Preset,
    HotelPublicPage,
    PublicSection,
    PublicElement,
    PublicElementItem,
    HeroSection,
    GalleryContainer,
    GalleryImage,
    ListContainer,
    Card,
    NewsItem,
    ContentBlock,
    RoomsSection,
    RoomBooking,
    BookingPrecheckinToken,
    BookingGuest,
)
from rooms.models import RoomType, Room
from guests.models import Guest
from .canonical_serializers import (
    StaffRoomBookingListSerializer,
    StaffRoomBookingDetailSerializer,
    BookingPartyGroupedSerializer,
)
from .serializers import (
    RoomTypeStaffSerializer,
    HotelAccessConfigStaffSerializer,
    PresetSerializer,
    HotelPublicPageSerializer,
    PublicSectionStaffSerializer,
    PublicElementStaffSerializer,
    PublicElementItemStaffSerializer,
    HeroSectionSerializer,
    GalleryContainerSerializer,
    GalleryImageSerializer,
    BulkGalleryImageUploadSerializer,
    ListContainerSerializer,
    CardSerializer,
    NewsItemSerializer,
    ContentBlockSerializer,
    RoomsSectionStaffSerializer,
    PublicSectionDetailSerializer,
)
from rooms.serializers import RoomStaffSerializer
from .permissions import IsSuperStaffAdminForHotel

# Additional imports moved from inline locations
from rest_framework.exceptions import PermissionDenied
from staff.models import Staff
from bookings.models import Restaurant
from common.models import ThemePreference
from hotel.services.booking_integrity import heal_booking_party
from hotel.precheckin.field_registry import PRECHECKIN_FIELD_REGISTRY
from django.core.exceptions import ValidationError
from pusher import pusher_client


# ============================================================================
# CENTRALIZED STAFF RESOLUTION HELPER
# ============================================================================

def get_staff_or_403(user, hotel):
    """
    Centralized staff resolution with proper validation.
    
    Args:
        user: Django User instance
        hotel: Hotel instance
        
    Returns:
        Staff instance if valid
        
    Raises:
        PermissionDenied: If user is not valid staff for the hotel
    """
    staff = Staff.objects.filter(
        user=user,
        hotel=hotel,
        is_active=True
    ).first()
    
    if not staff:
        raise PermissionDenied("Staff access required")
    
    return staff


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
    def upload_image(self, request, pk=None, hotel_slug=None):
        """
        Upload or update room type image.
        Accepts either file upload or image URL.
        
        POST /api/staff/hotel/{slug}/room-types/{id}/upload-image/
        
        Body (multipart/form-data or JSON):
        - photo: file upload (multipart)
        OR
        - photo_url: image URL string (JSON)
        """
        try:
            room_type = self.get_object()
            
            # Check for file upload
            if 'photo' in request.FILES:
                photo_file = request.FILES['photo']
                try:
                    room_type.photo = photo_file
                    room_type.save()
                    
                    photo_url = None
                    if room_type.photo:
                        try:
                            photo_url = room_type.photo.url
                        except Exception:
                            photo_url = str(room_type.photo)
                    
                    # Broadcast update via unified channel
                    try:
                        hotel_slug = self.request.user.staff_profile.hotel.slug
                        # Use consistent hotel channel format
                        channel = f'hotel-{hotel_slug}'
                        pusher_client.trigger(
                            channel,
                            'room-type-image-updated',
                            {
                                'room_type_id': room_type.id,
                                'photo_url': photo_url,
                                'timestamp': str(room_type.updated_at) if hasattr(room_type, 'updated_at') else None
                            }
                        )
                        logger.info(f"Room type image update sent to {channel}")
                    except Exception as e:
                        logger.error(f"Failed to broadcast room type update: {e}")
                    
                    return Response({
                        'message': 'Image uploaded successfully',
                        'photo_url': photo_url
                    }, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({
                        'error': f'Upload failed: {str(e)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Check for URL in request data
            elif 'photo_url' in request.data:
                photo_url = request.data['photo_url']
                
                if not photo_url:
                    return Response(
                        {'error': 'photo_url cannot be empty'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                try:
                    # CloudinaryField accepts URLs directly
                    room_type.photo = photo_url
                    room_type.save()
                    
                    saved_url = None
                    if room_type.photo:
                        try:
                            saved_url = room_type.photo.url
                        except Exception:
                            saved_url = str(room_type.photo)
                    
                    return Response({
                        'message': 'Image URL saved successfully',
                        'photo_url': saved_url
                    }, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({
                        'error': f'Save failed: {str(e)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            else:
                return Response(
                    {'error': 'Please provide either a photo file or photo_url'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({
                'error': f'Request failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        """Generate new guest PIN for room - DEPRECATED: PINs are now managed at Guest level"""
        return Response({
            'error': 'PIN generation is now handled at the Guest level during check-in',
            'message': 'Room-level PIN generation has been deprecated'
        }, status=400)
    
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


# ============================================================================
# PRESET MANAGEMENT
# ============================================================================

class PresetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only endpoint for presets.
    Returns all available presets for sections, cards, images, news blocks, etc.
    Staff can view presets but not create/edit them (managed via admin or seeding).
    """
    serializer_class = PresetSerializer
    permission_classes = [IsAuthenticated]
    queryset = Preset.objects.all()
    
    @action(detail=False, methods=['get'])
    def grouped(self, request):
        """
        Returns presets grouped by target_type and section_type.
        Example response:
        {
            "section": {
                "hero": [...],
                "gallery": [...],
                "list": [...],
                "news": [...],
                "footer": [...]
            },
            "card": [...],
            "image": [...],
            "news_block": [...],
            "footer": [...],
            "page_theme": [...]
        }
        """
        presets = Preset.objects.all()
        grouped_data = {}
        
        # Group by target_type
        for preset in presets:
            target = preset.target_type
            
            if target == 'section':
                # Further group sections by section_type
                if 'section' not in grouped_data:
                    grouped_data['section'] = {}
                
                section_type = preset.section_type or 'general'
                if section_type not in grouped_data['section']:
                    grouped_data['section'][section_type] = []
                
                grouped_data['section'][section_type].append(
                    PresetSerializer(preset).data
                )
            else:
                # Other target types don't need sub-grouping
                if target not in grouped_data:
                    grouped_data[target] = []
                
                grouped_data[target].append(
                    PresetSerializer(preset).data
                )
        
        return Response(grouped_data)


# ============================================================================
# HOTEL PUBLIC PAGE MANAGEMENT (Super Staff Admin)
# ============================================================================

class HotelPublicPageViewSet(viewsets.ModelViewSet):
    """
    Manage HotelPublicPage with global style variant.
    Super Staff Admin only.
    """
    serializer_class = HotelPublicPageSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        """Only return public page for staff's hotel"""
        hotel_slug = self.kwargs.get('hotel_slug')
        
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        
        if not hotel_slug:
            return HotelPublicPage.objects.none()
        
        return HotelPublicPage.objects.filter(hotel__slug=hotel_slug)
    
    @action(detail=False, methods=['post'], url_path='apply-page-style')
    def apply_page_style(self, request, hotel_slug=None):
        """
        Apply a global style preset to all sections.
        
        POST /api/staff/hotel/<hotel_slug>/public-page/apply-page-style/
        
        Body:
        {
            "style_variant": 1  // 1..5
        }
        
        This will:
        1. Set global_style_variant on HotelPublicPage
        2. Update style_variant on ALL active PublicSection instances
        3. Update style_variant on ALL section-specific models (HeroSection, GalleryContainer, etc.)
        """
        style_variant = request.data.get('style_variant')
        
        # Validate input
        if style_variant is None:
            return Response(
                {'error': 'style_variant is required (1-5)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            style_variant = int(style_variant)
            if style_variant < 1 or style_variant > 5:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {'error': 'style_variant must be an integer between 1 and 5'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create HotelPublicPage
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        public_page, created = HotelPublicPage.objects.get_or_create(hotel=hotel)
        
        # Update global style variant
        public_page.global_style_variant = style_variant
        public_page.save()
        
        # Update all sections for this hotel
        sections = PublicSection.objects.filter(hotel=hotel, is_active=True)
        sections.update(style_variant=style_variant)
        
        # Update all section-specific models
        for section in sections:
            # Update HeroSection if exists
            if hasattr(section, 'hero_data'):
                section.hero_data.style_variant = style_variant
                section.hero_data.save()
            
            # Update all GalleryContainers
            section.galleries.all().update(style_variant=style_variant)
            
            # Update all ListContainers
            section.lists.all().update(style_variant=style_variant)
            
            # Update all NewsItems
            section.news_items.all().update(style_variant=style_variant)
        
        # Return updated page data with all sections
        sections_data = PublicSectionStaffSerializer(
            sections,
            many=True,
            context={'request': request}
        ).data
        
        return Response({
            'message': f'Applied style preset {style_variant} to all sections',
            'public_page': HotelPublicPageSerializer(public_page).data,
            'updated_sections_count': sections.count(),
            'sections': sections_data
        }, status=status.HTTP_200_OK)


# ============================================================================
# PUBLIC PAGE SECTION CRUD (Super Staff Admin)
# ============================================================================

class PublicSectionViewSet(viewsets.ModelViewSet):
    """
    CRUD for PublicSection.
    Super Staff Admin only.
    Scoped to staff's hotel.
    """
    serializer_class = PublicSectionStaffSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        """Only return sections for staff's hotel"""
        # Try to get hotel_slug from kwargs (URL path) or from staff profile
        hotel_slug = self.kwargs.get('hotel_slug')
        
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        
        if not hotel_slug:
            return PublicSection.objects.none()
        
        return PublicSection.objects.filter(
            hotel__slug=hotel_slug
        ).order_by('position')
    
    def perform_create(self, serializer):
        """Automatically set hotel from URL or staff profile"""
        hotel_slug = self.kwargs.get('hotel_slug')
        
        # Fallback to staff profile if hotel_slug not in URL
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Ensure is_active is explicitly set
        is_active = serializer.validated_data.get('is_active', True)
        serializer.save(hotel=hotel, is_active=is_active)


class PublicElementViewSet(viewsets.ModelViewSet):
    """
    CRUD for PublicElement.
    Super Staff Admin only.
    """
    serializer_class = PublicElementStaffSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        """Only return elements for staff's hotel sections"""
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        if not hotel_slug:
            return PublicElement.objects.none()
        return PublicElement.objects.filter(
            section__hotel__slug=hotel_slug
        )


class PublicElementItemViewSet(viewsets.ModelViewSet):
    """
    CRUD for PublicElementItem.
    Super Staff Admin only.
    """
    serializer_class = PublicElementItemStaffSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        """Only return items for staff's hotel sections"""
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        if not hotel_slug:
            return PublicElementItem.objects.none()
        return PublicElementItem.objects.filter(
            element__section__hotel__slug=hotel_slug
        ).order_by('sort_order')


# ============================================================================
# SECTION-SPECIFIC CRUD VIEWSETS
# ============================================================================

class HeroSectionViewSet(viewsets.ModelViewSet):
    """
    CRUD for Hero section data.
    Automatically creates Hero data with placeholders when section is created.
    """
    serializer_class = HeroSectionSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        if not hotel_slug:
            return HeroSection.objects.none()
        return HeroSection.objects.filter(
            section__hotel__slug=hotel_slug
        )
    
    @action(detail=True, methods=['post'], url_path='upload-hero-image')
    def upload_hero_image(self, request, pk=None, hotel_slug=None):
        """Upload hero background image"""
        hero = self.get_object()
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        hero.hero_image = request.FILES['image']
        hero.save()
        
        serializer = self.get_serializer(hero)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='upload-logo')
    def upload_logo(self, request, pk=None, hotel_slug=None):
        """Upload hero logo image"""
        hero = self.get_object()
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        hero.hero_logo = request.FILES['image']
        hero.save()
        
        serializer = self.get_serializer(hero)
        return Response(serializer.data)


class GalleryContainerViewSet(viewsets.ModelViewSet):
    """
    CRUD for Gallery containers.
    Each Gallery section can have multiple gallery containers.
    """
    serializer_class = GalleryContainerSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        if not hotel_slug:
            return GalleryContainer.objects.none()
        return GalleryContainer.objects.filter(
            section__hotel__slug=hotel_slug
        ).order_by('sort_order')


class GalleryImageViewSet(viewsets.ModelViewSet):
    """
    CRUD for Gallery images.
    Supports bulk upload.
    """
    serializer_class = GalleryImageSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        if not hotel_slug:
            return GalleryImage.objects.none()
        return GalleryImage.objects.filter(
            gallery__section__hotel__slug=hotel_slug
        ).order_by('sort_order')
    
    @action(detail=False, methods=['post'], url_path='bulk-upload')
    def bulk_upload(self, request, hotel_slug=None):
        """
        Bulk upload images to a gallery.
        POST body: gallery (ID), images (array of files)
        """
        serializer = BulkGalleryImageUploadSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        images = serializer.save()
        
        # Return created images
        response_serializer = GalleryImageSerializer(images, many=True)
        return Response({
            'message': f'{len(images)} image(s) uploaded successfully',
            'images': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class ListContainerViewSet(viewsets.ModelViewSet):
    """
    CRUD for List containers.
    Each List section can have multiple list containers.
    """
    serializer_class = ListContainerSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        if not hotel_slug:
            return ListContainer.objects.none()
        return ListContainer.objects.filter(
            section__hotel__slug=hotel_slug
        ).order_by('sort_order')
    
    def perform_create(self, serializer):
        """Validate that lists cannot be attached to rooms sections"""
        section = serializer.validated_data.get('section')
        if section and hasattr(section, 'rooms_data'):
            raise ValidationError({"section": "Cannot attach lists to rooms sections"})
        serializer.save()


class CardViewSet(viewsets.ModelViewSet):
    """
    CRUD for Cards within list containers.
    """
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        if not hotel_slug:
            return Card.objects.none()
        return Card.objects.filter(
            list_container__section__hotel__slug=hotel_slug
        ).order_by('sort_order')
    
    def perform_create(self, serializer):
        """Validate that cards cannot be attached to rooms sections"""
        list_container = serializer.validated_data.get('list_container')
        if list_container and hasattr(list_container.section, 'rooms_data'):
            raise ValidationError({"list_container": "Cannot attach cards to rooms sections"})
        serializer.save()
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None, hotel_slug=None):
        """Upload card image"""
        card = self.get_object()
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        card.image = request.FILES['image']
        card.save()
        
        serializer = self.get_serializer(card)
        return Response(serializer.data)


class NewsItemViewSet(viewsets.ModelViewSet):
    """
    CRUD for News items.
    """
    serializer_class = NewsItemSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        if not hotel_slug:
            return NewsItem.objects.none()
        return NewsItem.objects.filter(
            section__hotel__slug=hotel_slug
        ).order_by('sort_order')


class ContentBlockViewSet(viewsets.ModelViewSet):
    """
    CRUD for Content blocks (text/image) within news items.
    """
    serializer_class = ContentBlockSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        if not hotel_slug:
            return ContentBlock.objects.none()
        return ContentBlock.objects.filter(
            news_item__section__hotel__slug=hotel_slug
        ).order_by('sort_order')
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None, hotel_slug=None):
        """Upload image for image blocks"""
        block = self.get_object()
        
        if block.block_type != 'image':
            return Response(
                {'error': 'Can only upload images to image blocks'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        block.image = request.FILES['image']
        block.save()
        
        serializer = self.get_serializer(block)
        return Response(serializer.data)


class RoomsSectionViewSet(viewsets.ModelViewSet):
    """
    CRUD for Rooms section configuration.
    Staff can manage subtitle, description, and style_variant.
    Room types are queried live from PMS - no duplication.
    """
    serializer_class = RoomsSectionStaffSerializer
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug and hasattr(self.request.user, 'staff_profile'):
            hotel_slug = self.request.user.staff_profile.hotel.slug
        if not hotel_slug:
            return RoomsSection.objects.none()
        return RoomsSection.objects.filter(
            section__hotel__slug=hotel_slug
        )
    
    def perform_create(self, serializer):
        """Validate only one rooms section per hotel"""
        section = serializer.validated_data.get('section')
        if section:
            hotel = section.hotel
            existing = RoomsSection.objects.filter(section__hotel=hotel).exists()
            if existing:
                raise ValidationError({"section": "Hotel already has a rooms section"})
        serializer.save()


# ============================================================================
# STAFF HOTEL SETTINGS & MANAGEMENT VIEWS
# ============================================================================

class HotelSettingsView(APIView):
    """
    Simple hotel settings endpoint for basic hotel information.
    For theme/colors, use /common/theme/ endpoint instead.
    """
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]

    def get(self, request, hotel_slug):
        """Get complete hotel information and theme"""
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Get or create theme
        theme, _ = ThemePreference.objects.get_or_create(hotel=hotel)
        
        # Complete hotel info + theme
        data = {
            # Basic info
            'id': hotel.id,
            'name': hotel.name,
            'slug': hotel.slug,
            'subdomain': hotel.subdomain,
            'is_active': hotel.is_active,
            'sort_order': hotel.sort_order,
            
            # Marketing
            'tagline': hotel.tagline,
            'short_description': hotel.short_description,
            'long_description': hotel.long_description,
            
            # Location
            'city': hotel.city,
            'country': hotel.country,
            'address_line_1': hotel.address_line_1,
            'address_line_2': hotel.address_line_2,
            'postal_code': hotel.postal_code,
            'latitude': float(hotel.latitude) if hotel.latitude else None,
            'longitude': float(hotel.longitude) if hotel.longitude else None,
            
            # Contact
            'phone': hotel.phone,
            'email': hotel.email,
            'website_url': hotel.website_url,
            'booking_url': hotel.booking_url,
            
            # Classification
            'hotel_type': hotel.hotel_type,
            'tags': hotel.tags,
            
            # Images
            'logo': hotel.logo.url if hotel.logo else None,
            'hero_image': hotel.hero_image.url if hotel.hero_image else None,
            'landing_page_image': hotel.landing_page_image.url if hotel.landing_page_image else None,
            
            # Theme colors
            'main_color': theme.main_color,
            'secondary_color': theme.secondary_color,
            'background_color': theme.background_color,
            'text_color': theme.text_color,
            'border_color': theme.border_color,
            'button_color': theme.button_color,
            'button_text_color': theme.button_text_color,
            'button_hover_color': theme.button_hover_color,
            'link_color': theme.link_color,
            'link_hover_color': theme.link_hover_color,
        }
        
        return Response(data)
    
    def patch(self, request, hotel_slug):
        """Update any hotel information and theme"""
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # All updatable hotel fields
        hotel_fields = [
            'name', 'subdomain', 'is_active', 'sort_order',
            'tagline', 'short_description', 'long_description',
            'city', 'country', 'address_line_1', 'address_line_2', 'postal_code',
            'latitude', 'longitude',
            'phone', 'email', 'website_url', 'booking_url',
            'hotel_type', 'tags'
        ]
        
        for field in hotel_fields:
            if field in request.data:
                setattr(hotel, field, request.data[field])
        
        # Handle file uploads
        if 'logo' in request.FILES:
            hotel.logo = request.FILES['logo']
        if 'hero_image' in request.FILES:
            hotel.hero_image = request.FILES['hero_image']
        if 'landing_page_image' in request.FILES:
            hotel.landing_page_image = request.FILES['landing_page_image']
        
        hotel.save()
        
        # Update theme fields if provided
        theme, _ = ThemePreference.objects.get_or_create(hotel=hotel)
        
        theme_fields = [
            'main_color', 'secondary_color', 'background_color', 'text_color',
            'border_color', 'button_color', 'button_text_color', 
            'button_hover_color', 'link_color', 'link_hover_color'
        ]
        
        for field in theme_fields:
            if field in request.data:
                setattr(theme, field, request.data[field])
        
        theme.save()
        
        # Return complete updated data
        data = {
            # Basic info
            'id': hotel.id,
            'name': hotel.name,
            'slug': hotel.slug,
            'subdomain': hotel.subdomain,
            'is_active': hotel.is_active,
            'sort_order': hotel.sort_order,
            
            # Marketing
            'tagline': hotel.tagline,
            'short_description': hotel.short_description,
            'long_description': hotel.long_description,
            
            # Location
            'city': hotel.city,
            'country': hotel.country,
            'address_line_1': hotel.address_line_1,
            'address_line_2': hotel.address_line_2,
            'postal_code': hotel.postal_code,
            'latitude': float(hotel.latitude) if hotel.latitude else None,
            'longitude': float(hotel.longitude) if hotel.longitude else None,
            
            # Contact
            'phone': hotel.phone,
            'email': hotel.email,
            'website_url': hotel.website_url,
            'booking_url': hotel.booking_url,
            
            # Classification
            'hotel_type': hotel.hotel_type,
            'tags': hotel.tags,
            
            # Images
            'logo': hotel.logo.url if hotel.logo else None,
            'hero_image': hotel.hero_image.url if hotel.hero_image else None,
            'landing_page_image': hotel.landing_page_image.url if hotel.landing_page_image else None,
            
            # Theme colors
            'main_color': theme.main_color,
            'secondary_color': theme.secondary_color,
            'background_color': theme.background_color,
            'text_color': theme.text_color,
            'border_color': theme.border_color,
            'button_color': theme.button_color,
            'button_text_color': theme.button_text_color,
            'button_hover_color': theme.button_hover_color,
            'link_color': theme.link_color,
            'link_hover_color': theme.link_hover_color,
        }
        
        return Response(data)


class StaffBookingsListView(APIView):
    """Staff endpoint to list room bookings for their hotel."""
    permission_classes = []
    
    def get_permissions(self):
        return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]

    def get(self, request, hotel_slug):
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response({'error': 'Staff profile not found'}, status=status.HTTP_403_FORBIDDEN)

        if staff.hotel.slug != hotel_slug:
            return Response({'error': 'You can only view bookings for your hotel'}, status=status.HTTP_403_FORBIDDEN)

        bookings = RoomBooking.objects.filter(hotel=staff.hotel).select_related('hotel', 'room_type').order_by('-created_at')

        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter.upper())

        start_date = request.query_params.get('start_date')
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                bookings = bookings.filter(check_in__gte=start)
            except ValueError:
                return Response({'error': 'Invalid start_date format'}, status=status.HTTP_400_BAD_REQUEST)

        end_date = request.query_params.get('end_date')
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                bookings = bookings.filter(check_out__lte=end)
            except ValueError:
                return Response({'error': 'Invalid end_date format'}, status=status.HTTP_400_BAD_REQUEST)


        serializer = StaffRoomBookingListSerializer(bookings, many=True)
        return Response(serializer.data)


class StaffBookingConfirmView(APIView):
    """Staff endpoint to confirm a booking."""
    permission_classes = []
    
    def get_permissions(self):
        return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]

    def post(self, request, hotel_slug, booking_id):
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response({'error': 'Staff profile not found'}, status=status.HTTP_403_FORBIDDEN)

        if staff.hotel.slug != hotel_slug:
            return Response({'error': 'You can only confirm bookings for your hotel'}, status=status.HTTP_403_FORBIDDEN)

        try:
            booking = RoomBooking.objects.get(booking_id=booking_id, hotel=staff.hotel)
        except RoomBooking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        # 🚨 CRITICAL: Block Stripe bookings from using old confirm endpoint
        if (booking.payment_provider == "stripe" or 
            booking.payment_intent_id or 
            booking.payment_authorized_at):
            return Response({
                'error': 'Stripe bookings require staff approve/decline endpoints.',
                'required_endpoints': {
                    'approve': f'/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/approve/',
                    'decline': f'/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/decline/'
                }
            }, status=status.HTTP_403_FORBIDDEN)

        if booking.status == 'CANCELLED':
            return Response({'error': 'Cannot confirm a cancelled booking'}, status=status.HTTP_400_BAD_REQUEST)

        if booking.status == 'CONFIRMED':
            return Response({'message': 'Booking is already confirmed'}, status=status.HTTP_200_OK)
        
        # 🚨 CRITICAL: Enforce status transitions - only allow from valid states
        if booking.status == 'PENDING_PAYMENT':
            return Response({
                'error': 'Cannot confirm booking still pending payment. Guest must complete payment first.',
                'current_status': booking.status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if booking.status == 'PENDING_APPROVAL':
            return Response({
                'error': 'Booking requires authorize-capture approval. Use approve/decline endpoints.',
                'current_status': booking.status,
                'required_endpoints': {
                    'approve': f'/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/approve/',
                    'decline': f'/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/decline/'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        booking.status = 'CONFIRMED'
        booking.save()

        # Send email notification to guest
        try:
            send_booking_confirmation_email(booking)
        except ImportError:
            logger.warning("Email service not available for booking confirmation")
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")

        # Send booking confirmation via NotificationManager (handles both FCM and realtime)
        try:
            notification_manager.realtime_booking_created(booking)
            logger.info(f"NotificationManager sent booking confirmation for {booking.booking_id}")
        except Exception as e:
            logger.error(f"NotificationManager failed for booking confirmation {booking.booking_id}: {e}")
            
            # Fallback to direct FCM
            try:
                # Try to find guest FCM token from room if they're checked in
                guest_fcm_token = None
                try:
                    guest_room = Room.objects.filter(
                        hotel=booking.hotel,
                        guests__isnull=False,
                        is_occupied=True
                    ).first()
                    if guest_room and guest_room.guest_fcm_token:
                        guest_fcm_token = guest_room.guest_fcm_token
                except:
                    pass
                
                if guest_fcm_token:
                    send_booking_confirmation_notification(guest_fcm_token, booking)
                    logger.info("Fallback FCM booking confirmation sent")
                
            except ImportError:
                logger.warning("FCM service not available for booking confirmation")
            except Exception as fallback_e:
                logger.error(f"Fallback FCM confirmation also failed: {fallback_e}")

        serializer = StaffRoomBookingDetailSerializer(booking)
        return Response({'message': 'Booking confirmed successfully', 'booking': serializer.data})


class StaffBookingCancelView(APIView):
    """Staff endpoint to cancel a booking."""
    permission_classes = []
    
    def get_permissions(self):
        return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]

    def post(self, request, hotel_slug, booking_id):
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response({'error': 'Staff profile not found'}, status=status.HTTP_403_FORBIDDEN)

        if staff.hotel.slug != hotel_slug:
            return Response({'error': 'You can only cancel bookings for your hotel'}, status=status.HTTP_403_FORBIDDEN)

        try:
            booking = RoomBooking.objects.get(booking_id=booking_id, hotel=staff.hotel)
        except RoomBooking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        # 🚨 CRITICAL: Block Stripe bookings from using old cancel endpoint
        if (booking.payment_provider == "stripe" or 
            booking.payment_intent_id or 
            booking.payment_authorized_at):
            return Response({
                'error': 'Stripe bookings require staff approve/decline endpoints.',
                'current_status': booking.status,
                'required_endpoints': {
                    'approve': f'/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/approve/',
                    'decline': f'/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/decline/'
                }
            }, status=status.HTTP_403_FORBIDDEN)

        if booking.status == 'CANCELLED':
            return Response({'message': 'Booking is already cancelled'}, status=status.HTTP_200_OK)

        if booking.status == 'COMPLETED':
            return Response({'error': 'Cannot cancel a completed booking'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 🚨 CRITICAL: Block cancellation of payments with active Stripe authorization
        if booking.status == 'PENDING_APPROVAL':
            return Response({
                'error': 'Cannot cancel booking with pending payment authorization. Use decline endpoint to cancel authorization.',
                'current_status': booking.status,
                'required_endpoint': f'/api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/decline/'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get cancellation reason from request
        cancellation_reason = request.data.get('reason', 'Cancelled by staff')
        
        # Get proper staff name from Staff profile (primary) or User (fallback)
        try:
            # First try staff profile fields (most likely to have proper names)
            staff_name = f"{staff.first_name} {staff.last_name}".strip()
            
            # If staff profile doesn't have names, try User model
            if not staff_name:
                user = request.user
                staff_name = f"{user.first_name} {user.last_name}".strip()
            
            # Final fallback to username or generic name
            if not staff_name:
                staff_name = getattr(request.user, 'username', 'Staff Member')
                
        except Exception as e:
            staff_name = 'Staff Member'
        
        booking.status = 'CANCELLED'
        
        # Add detailed cancellation information to special_requests
        current_requests = booking.special_requests or ''
        cancellation_info = (
            f"\n\n--- BOOKING CANCELLED ---\n"
            f"Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Cancelled by: {staff_name}\n"
            f"Reason: {cancellation_reason}"
        )
        booking.special_requests = f"{current_requests}{cancellation_info}".strip()
        booking.save()

        # Send email notification to guest
        try:
            send_booking_cancellation_email(booking, cancellation_reason, staff_name)
        except ImportError:
            logger.warning("Email service not available for booking cancellation")
        except Exception as e:
            logger.error(f"Failed to send cancellation email: {e}")

        # Send booking cancellation via NotificationManager (handles both FCM and realtime)
        try:
            notification_manager.realtime_booking_cancelled(booking, cancellation_reason)
            logger.info(f"NotificationManager sent booking cancellation for {booking.booking_id}")
        except Exception as e:
            logger.error(f"NotificationManager failed for booking cancellation {booking.booking_id}: {e}")
            
            # Fallback to direct FCM
            try:
                # Try to find guest FCM token from room if they're checked in
                guest_fcm_token = None
                try:
                    guest_room = Room.objects.filter(
                        hotel=booking.hotel,
                        guests__isnull=False,
                        is_occupied=True
                    ).first()
                    if guest_room and guest_room.guest_fcm_token:
                        guest_fcm_token = guest_room.guest_fcm_token
                except:
                    pass
                
                if guest_fcm_token:
                    send_booking_cancellation_notification(guest_fcm_token, booking, cancellation_reason)
                    logger.info("Fallback FCM booking cancellation sent")
                
            except ImportError:
                logger.warning("FCM service not available for booking cancellation")
            except Exception as fallback_e:
                logger.error(f"Fallback FCM cancellation also failed: {fallback_e}")

        serializer = StaffRoomBookingDetailSerializer(booking)
        return Response({
            'message': 'Booking cancelled successfully', 
            'booking': serializer.data,
            'cancellation_reason': cancellation_reason
        })


class StaffBookingDetailView(APIView):
    """Staff endpoint to get detailed booking information."""
    permission_classes = []
    
    def get_permissions(self):
        return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]

    def get(self, request, hotel_slug, booking_id):
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response({'error': 'Staff profile not found'}, status=status.HTTP_403_FORBIDDEN)

        if staff.hotel.slug != hotel_slug:
            return Response({'error': 'You can only view bookings for your hotel'}, status=status.HTTP_403_FORBIDDEN)

        try:
            booking = RoomBooking.objects.select_related(
                'hotel', 'room_type', 'assigned_room__room_type'
            ).prefetch_related(
                'party', 'guests__room'
            ).get(
                booking_id=booking_id, 
                hotel=staff.hotel
            )
        except RoomBooking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = StaffRoomBookingDetailSerializer(booking)
        return Response(serializer.data)


class PublicPageBuilderView(APIView):
    """Staff builder endpoint for a hotel's public page."""
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]

    def get(self, request, hotel_slug):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        sections = PublicSection.objects.filter(hotel=hotel).order_by("position").select_related("element").prefetch_related("element__items")
        section_data = PublicSectionStaffSerializer(sections, many=True).data
        
        response = {
            "hotel": {
                "id": hotel.id,
                "slug": hotel.slug,
                "name": hotel.name,
                "city": hotel.city,
                "country": hotel.country,
                "tagline": hotel.tagline,
                "booking_url": hotel.booking_url,
            },
            "is_empty": len(section_data) == 0,
            "sections": section_data,
            "presets": {
                "element_types": ["hero", "text_block", "image_block", "gallery", "cards_list", "reviews_list", "rooms_list", "contact_block", "map_block", "footer_block"],
                "section_presets": []
            },
        }
        return Response(response)


class HotelStatusCheckView(APIView):
    """Quick endpoint to check hotel's current state."""
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]

    def get(self, request, hotel_slug):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        section_count = PublicSection.objects.filter(hotel=hotel).count()
        
        return Response({
            "hotel": {"id": hotel.id, "name": hotel.name, "slug": hotel.slug, "city": hotel.city, "country": hotel.country},
            "branding": {"has_hero_image": bool(hotel.hero_image), "hero_image_url": hotel.hero_image.url if hotel.hero_image else None},
            "public_page": {"section_count": section_count, "is_empty": section_count == 0},
        })


class PublicPageBootstrapView(APIView):
    """Bootstrap a hotel with default public page sections."""
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]

    def post(self, request, hotel_slug):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        existing_count = PublicSection.objects.filter(hotel=hotel).count()
        
        if existing_count > 0:
            return Response({"detail": f"Hotel already has {existing_count} section(s)"}, status=status.HTTP_400_BAD_REQUEST)

        # Create default sections (simplified)
        hero = PublicSection.objects.create(hotel=hotel, position=0, name="Hero", is_active=True)
        PublicElement.objects.create(section=hero, element_type="hero", title="Welcome", subtitle="Your perfect stay")
        
        # Create default rooms section
        rooms_section = PublicSection.objects.create(
            hotel=hotel,
            position=2,
            name="Our Rooms & Suites",
            is_active=True
        )
        RoomsSection.objects.create(
            section=rooms_section,
            subtitle="Choose the perfect stay for your visit",
            style_variant=1
        )
        
        return Response({"message": "Bootstrap complete"}, status=status.HTTP_201_CREATED)


class SectionCreateView(APIView):
    """Enhanced section creation endpoint."""
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def post(self, request, hotel_slug):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        section_type = request.data.get('section_type')
        
        if not section_type or section_type not in ['hero', 'gallery', 'list', 'news', 'rooms']:
            return Response({'error': 'Invalid section_type'}, status=status.HTTP_400_BAD_REQUEST)
        
        name = request.data.get('name', f'{section_type.title()} Section')
        position = request.data.get('position', 0)
        container_name = request.data.get('container_name', '')
        article_title = request.data.get('article_title', '')
        
        # Create the section
        section = PublicSection.objects.create(
            hotel=hotel, 
            position=position, 
            name=name, 
            is_active=True
        )
        
        # Create section-specific related objects based on type
        if section_type == 'hero':
            self._create_hero_section(section)
            
        elif section_type == 'gallery':
            self._create_gallery_section(section, container_name)
            
        elif section_type == 'list':
            self._create_list_section(section, container_name)
            
        elif section_type == 'news':
            self._create_news_section(section, article_title)
            
        elif section_type == 'rooms':
            self._create_rooms_section(section)
        
        serializer = PublicSectionDetailSerializer(section)
        return Response({
            'message': f'{section_type.title()} section created', 
            'section': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def _create_hero_section(self, section):
        """Create hero section with default placeholder data."""
        HeroSection.objects.create(
            section=section,
            hero_title="Update your hero title here",
            hero_text="Update your hero description text here.",
            style_variant=1
        )
    
    def _create_gallery_section(self, section, container_name):
        """Create gallery section with an empty gallery container."""
        gallery_name = container_name.strip() if container_name else "Gallery 1"
        GalleryContainer.objects.create(
            section=section,
            name=gallery_name,
            sort_order=0,
            style_variant=1
        )
    
    def _create_list_section(self, section, container_name):
        """Create list section with an empty list container."""
        list_title = container_name.strip() if container_name else ""
        ListContainer.objects.create(
            section=section,
            title=list_title,
            sort_order=0,
            style_variant=1
        )
    
    def _create_news_section(self, section, article_title):
        """Create news section with a placeholder article and content blocks."""
        news_title = article_title.strip() if article_title else "Update Article Title"
        news_item = NewsItem.objects.create(
            section=section,
            title=news_title,
            date=date.today(),
            summary="Update this summary with your article excerpt.",
            sort_order=0,
            style_variant=1
        )
        
        # Create placeholder content blocks for the news article
        ContentBlock.objects.create(
            news_item=news_item,
            block_type='image',
            body='',
            image_position='full_width',
            image_caption='Add your cover image here',
            sort_order=0
        )
        
        ContentBlock.objects.create(
            news_item=news_item,
            block_type='text',
            body='Start writing your article content here. This is the first text block.',
            image_position='full_width',
            sort_order=1
        )
        
        ContentBlock.objects.create(
            news_item=news_item,
            block_type='image',
            body='',
            image_position='right',
            image_caption='Add an inline image (optional)',
            sort_order=2
        )
        
        ContentBlock.objects.create(
            news_item=news_item,
            block_type='text',
            body='Continue your article here. This text will wrap around the image above.',
            image_position='full_width',
            sort_order=3
        )
        
        ContentBlock.objects.create(
            news_item=news_item,
            block_type='image',
            body='',
            image_position='left',
            image_caption='Another inline image (optional)',
            sort_order=4
        )
        
        ContentBlock.objects.create(
            news_item=news_item,
            block_type='text',
            body='Conclude your article with this final text block.',
            image_position='full_width',
            sort_order=5
        )
    
    def _create_rooms_section(self, section):
        """Create rooms section configuration."""
        RoomsSection.objects.create(
            section=section,
            subtitle="Choose the perfect stay for your visit",
            description="",
            style_variant=1
        )


# ============================================================================
# PHASE 2: BOOKING ASSIGNMENT ENDPOINTS
# ============================================================================

class BookingAssignmentView(APIView):
    """
    Staff endpoints for booking room assignment (check-in) and checkout.
    
    POST /api/staff/hotels/{slug}/bookings/{booking_id}/assign-room/
    POST /api/staff/hotels/{slug}/bookings/{booking_id}/checkout/
    """
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]

    def get_hotel_and_booking(self, hotel_slug, booking_id):
        """Helper to get hotel and booking with validation"""
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        booking = get_object_or_404(RoomBooking, hotel=hotel, booking_id=booking_id)
        return hotel, booking

    def _emit_assignment_realtime_events(self, booking, room, primary_guest, party_guest_objects):
        """Emit realtime events for room assignment - called after transaction commit"""
        try:
            notification_manager.realtime_booking_checked_in(booking, room, primary_guest, party_guest_objects)
            notification_manager.realtime_room_occupancy_updated(room)
        except Exception as e:
            logger.error(f"Failed to emit assignment realtime events for booking {booking.booking_id}: {e}")
    
    def _emit_checkout_realtime_events_assignment(self, booking, room, hotel):
        """Emit realtime events for checkout from assignment view - called after transaction commit"""
        try:
            notification_manager.realtime_booking_checked_out(booking, room.room_number)
            notification_manager.realtime_room_occupancy_updated(room)
            
            # Room status notification
            pusher_client.trigger(
                f'hotel-{hotel.slug}',
                'room-status-changed',
                {
                    'room_number': room.room_number,
                    'old_status': 'OCCUPIED',
                    'new_status': 'CHECKOUT_DIRTY',
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to emit checkout realtime events for booking {booking.booking_id}: {e}")

    def post(self, request, hotel_slug, booking_id, action=None):
        """Route to specific action"""
        if action == 'assign-room':
            return self.assign_room(request, hotel_slug, booking_id)
        elif action == 'checkout':
            return self.checkout_booking(request, hotel_slug, booking_id)
        else:
            return Response(
                {"error": "Invalid action. Use 'assign-room' or 'checkout'"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def assign_room(self, request, hotel_slug, booking_id):
        """
        Assign room to booking (check-in process).
        
        POST /api/staff/hotels/{slug}/bookings/{booking_id}/assign-room/
        Body: { "room_number": 203 }
        """
        try:
            hotel, booking = self.get_hotel_and_booking(hotel_slug, booking_id)
            
            # Validate booking status
            if booking.status != 'CONFIRMED':
                return Response(
                    {"error": f"Booking must be CONFIRMED to assign room. Current status: {booking.status}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate primary guest exists
            if not booking.primary_first_name or not booking.primary_last_name:
                return Response(
                    {"error": "Booking must have primary guest name to check-in"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get room number from request
            room_number = request.data.get('room_number')
            if not room_number:
                return Response(
                    {"error": "room_number is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find and validate room
            try:
                room = Room.objects.get(hotel=hotel, room_number=room_number)
            except Room.DoesNotExist:
                return Response(
                    {"error": f"Room {room_number} not found in {hotel.name}"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Validate room state
            if not room.is_active:
                return Response(
                    {"error": f"Room {room_number} is not active"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if room.is_out_of_order:
                return Response(
                    {"error": f"Room {room_number} is out of order"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if room.is_occupied:
                return Response(
                    {"error": f"Room {room_number} is already occupied"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Capacity validation
            if room.room_type and hasattr(room.room_type, 'max_occupancy') and room.room_type.max_occupancy:
                party_total_count = booking.party.count()
                if party_total_count > room.room_type.max_occupancy:
                    return Response(
                        {
                            "error": "capacity_exceeded",
                            "message": f"Party size ({party_total_count}) exceeds room capacity ({room.room_type.max_occupancy})",
                            "party_total_count": party_total_count,
                            "max_occupancy": room.room_type.max_occupancy
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Perform assignment atomically
            with transaction.atomic():
                # Update booking
                booking.assigned_room = room
                if not booking.checked_in_at:
                    booking.checked_in_at = timezone.now()
                booking.save()
                
                # Get all booking party members
                booking_guests = booking.party.all().select_related()
                
                # Convert all party members to in-house Guests
                primary_guest = None
                party_guest_objects = []
                
                for booking_guest in booking_guests:
                    # Create/update Guest record idempotently using booking_guest FK
                    guest, created = Guest.objects.get_or_create(
                        booking_guest=booking_guest,
                        defaults={
                            'hotel': hotel,
                            'first_name': booking_guest.first_name,
                            'last_name': booking_guest.last_name,
                            'room': room,
                            'check_in_date': booking.check_in,
                            'check_out_date': booking.check_out,
                            'days_booked': (booking.check_out - booking.check_in).days,
                            'guest_type': booking_guest.role,
                            'primary_guest': None,  # Will be set after we find primary
                            'booking': booking,
                        }
                    )
                    
                    if not created:
                        # Update existing guest
                        guest.hotel = hotel
                        guest.first_name = booking_guest.first_name
                        guest.last_name = booking_guest.last_name
                        guest.room = room
                        guest.check_in_date = booking.check_in
                        guest.check_out_date = booking.check_out
                        guest.days_booked = (booking.check_out - booking.check_in).days
                        guest.guest_type = booking_guest.role
                        guest.booking = booking
                        guest.save()
                    
                    party_guest_objects.append(guest)
                    
                    # Track primary guest
                    if booking_guest.role == 'PRIMARY':
                        primary_guest = guest
                
                # Update companion references to point to primary guest
                if primary_guest:
                    for guest in party_guest_objects:
                        if guest.guest_type == 'COMPANION':
                            guest.primary_guest = primary_guest
                            guest.save()
                
                # Update room occupancy - Room Turnover Workflow
                room.is_occupied = True
                room.room_status = 'OCCUPIED'  # NEW - maintain status consistency
                room.save()
                
                # Trigger realtime notifications - ONLY AFTER DB COMMIT
                transaction.on_commit(
                    lambda: self._emit_assignment_realtime_events(booking, room, primary_guest, party_guest_objects)
                )
            
            # Return success response with canonical serializer
            
            # Refresh booking with related data for serializer
            booking.refresh_from_db()
            
            return Response({
                "message": f"Successfully assigned room {room_number} to booking {booking_id}",
                **StaffRoomBookingDetailSerializer(booking).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error assigning room to booking {booking_id}: {str(e)}")
            return Response(
                {"error": "Internal server error during room assignment"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def checkout_booking(self, request, hotel_slug, booking_id):
        """
        Checkout booking (detach guests from room).
        
        POST /api/staff/hotels/{slug}/bookings/{booking_id}/checkout/
        """
        try:
            from room_bookings.services.checkout import checkout_booking
            
            hotel, booking = self.get_hotel_and_booking(hotel_slug, booking_id)
            staff_user = request.user.staff_profile
            
            # Use centralized checkout service
            checkout_booking(
                booking=booking,
                performed_by=staff_user,
                source="booking_assignment_view",
            )
            
            # Refresh booking with updated data
            booking.refresh_from_db()
            
            return Response({
                "message": f"Successfully checked out booking {booking_id} from room {booking.assigned_room.room_number}",
                **StaffRoomBookingDetailSerializer(booking).data
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error checking out booking {booking_id}: {str(e)}")
            return Response(
                {"error": "Internal server error during checkout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# PHASE 3: BOOKING PARTY MANAGEMENT ENDPOINTS
# ============================================================================

class BookingPartyManagementView(APIView):
    """
    Staff endpoints for managing booking party lists.
    
    GET /api/staff/hotels/{slug}/bookings/{booking_id}/party/
    PUT /api/staff/hotels/{slug}/bookings/{booking_id}/party/companions/
    """
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]

    def get_hotel_and_booking(self, hotel_slug, booking_id):
        """Helper to get hotel and booking with validation"""
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        booking = get_object_or_404(RoomBooking, hotel=hotel, booking_id=booking_id)
        return hotel, booking

    def get(self, request, hotel_slug, booking_id):
        """
        Get booking party information.
        
        GET /api/staff/hotels/{slug}/bookings/{booking_id}/party/
        
        Returns:
        {
          "primary": {...},
          "companions": [...]
        }
        """
        try:
            hotel, booking = self.get_hotel_and_booking(hotel_slug, booking_id)
            
            # Use canonical serializer for consistent output
            serializer = BookingPartyGroupedSerializer()
            party_data = serializer.to_representation(booking)
            
            # Auto-heal if no PRIMARY exists
            if not party_data['primary'] and booking.primary_first_name:
                heal_booking_party(booking, notify=True)
                # Re-serialize after healing
                party_data = serializer.to_representation(booking)
            
            return Response({
                'booking_id': booking.booking_id,
                **party_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error retrieving party for booking {booking_id}: {str(e)}")
            return Response(
                {"error": "Internal server error retrieving party"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, hotel_slug, booking_id, action=None):
        """Route to specific party action"""
        if action == 'companions':
            return self.update_companions(request, hotel_slug, booking_id)
        else:
            return Response(
                {"error": "Invalid action. Use 'companions'"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update_companions(self, request, hotel_slug, booking_id):
        """
        Replace companions list (PRIMARY remains controlled by booking).
        
        PUT /api/staff/hotels/{slug}/bookings/{booking_id}/party/companions/
        
        Body:
        {
          "companions": [
            {"id": 12, "first_name":"Jane","last_name":"Doe"},
            {"first_name":"Kid","last_name":"Doe"}  // new companion
          ]
        }
        """
        try:
            hotel, booking = self.get_hotel_and_booking(hotel_slug, booking_id)
            
            # Validate booking not checked in yet (optional restriction)
            if booking.checked_in_at:
                return Response(
                    {"error": "Cannot modify party after check-in. Use guest management instead."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            companions_data = request.data.get('companions', [])
            
            with transaction.atomic():
                
                # Get current companions (excluding PRIMARY)
                current_companions = booking.party.filter(role='COMPANION')
                current_companion_ids = set(current_companions.values_list('id', flat=True))
                
                # Process new companions list
                updated_companion_ids = set()
                
                for companion_data in companions_data:
                    first_name = companion_data.get('first_name', '').strip()
                    last_name = companion_data.get('last_name', '').strip()
                    
                    if not first_name or not last_name:
                        return Response(
                            {"error": "All companions must have first_name and last_name"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    companion_id = companion_data.get('id')
                    
                    if companion_id:
                        # Update existing companion
                        try:
                            companion = current_companions.get(id=companion_id)
                            companion.first_name = first_name
                            companion.last_name = last_name
                            companion.email = companion_data.get('email', '')
                            companion.phone = companion_data.get('phone', '')
                            companion.save()
                            updated_companion_ids.add(companion_id)
                        except BookingGuest.DoesNotExist:
                            return Response(
                                {"error": f"Companion with id {companion_id} not found"},
                                status=status.HTTP_404_NOT_FOUND
                            )
                    else:
                        # Create new companion
                        companion = BookingGuest.objects.create(
                            booking=booking,
                            role='COMPANION',
                            first_name=first_name,
                            last_name=last_name,
                            email=companion_data.get('email', ''),
                            phone=companion_data.get('phone', ''),
                            is_staying=True
                        )
                        updated_companion_ids.add(companion.id)
                
                # Delete companions not in the updated list
                companions_to_delete = current_companion_ids - updated_companion_ids
                if companions_to_delete:
                    BookingGuest.objects.filter(
                        id__in=companions_to_delete,
                        booking=booking,
                        role='COMPANION'
                    ).delete()
                
                # Trigger realtime notification
                updated_party = booking.party.all()
                notification_manager.realtime_booking_party_updated(booking, updated_party)
            
            # Return updated party
            return self.get(request, hotel_slug, booking_id)
            
        except Exception as e:
            logger.error(f"Error updating companions for booking {booking_id}: {str(e)}")
            return Response(
                {"error": "Internal server error updating companions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# SAFE ROOM ASSIGNMENT SYSTEM (Phase 3: API Endpoints)
# ============================================================================

class AvailableRoomsView(APIView):
    """GET /api/staff/hotels/{hotel_slug}/bookings/{booking_id}/available-rooms/"""
    
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get(self, request, hotel_slug, booking_id):
        booking = get_object_or_404(RoomBooking, booking_id=booking_id, hotel__slug=hotel_slug)
        
        available_rooms = RoomAssignmentService.find_available_rooms_for_booking(booking)
        
        data = [{
            'id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type.name,
            'room_status': room.room_status,
            'is_bookable': room.is_bookable()
        } for room in available_rooms]
        
        return Response({'available_rooms': data})


class SafeAssignRoomView(APIView):
    """POST /api/staff/hotels/{hotel_slug}/bookings/{booking_id}/safe-assign-room/"""
    
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def post(self, request, hotel_slug, booking_id):
        room_id = request.data.get('room_id')
        notes = request.data.get('notes', '')
        
        if not room_id:
            return Response(
                {'error': {'code': 'MISSING_ROOM_ID', 'message': 'room_id is required'}},
                status=400
            )
        
        # Enforce party completion before room assignment
        try:
            booking = RoomBooking.objects.get(
                booking_id=booking_id,
                hotel__slug=hotel_slug
            )
            if not booking.party_complete:
                return Response(
                    {'code': 'PARTY_INCOMPLETE', 'message': 'Please provide all staying guest names before room assignment.'},
                    status=400
                )
        except RoomBooking.DoesNotExist:
            return Response(
                {'error': {'code': 'BOOKING_NOT_FOUND', 'message': 'Booking not found'}},
                status=404
            )
        
        # Centralized staff resolution
        staff_user = get_staff_or_403(request.user, booking.hotel)
        
        try:
            # ONLY ASSIGN ROOM - NO CHECK-IN SIDE EFFECTS - NO REALTIME EVENTS
            booking = RoomAssignmentService.assign_room_atomic(
                booking_id=booking_id,
                room_id=room_id,
                staff_user=staff_user,
                notes=notes
            )
            
            # Return updated booking with assigned room details (SILENT - NO REALTIME)
            serializer = RoomBookingDetailSerializer(booking)
            return Response({
                'message': f'Successfully assigned room to booking {booking_id}',
                **serializer.data
            })
            
        except RoomBooking.DoesNotExist:
            return Response(
                {'error': {'code': 'BOOKING_NOT_FOUND', 'message': 'Booking not found'}},
                status=404
            )
        except Room.DoesNotExist:
            return Response(
                {'error': {'code': 'ROOM_NOT_FOUND', 'message': 'Room not found'}},
                status=404
            )
        except RoomAssignmentError as e:
            status_code = 409 if e.code in ['ROOM_OVERLAP_CONFLICT', 'BOOKING_ALREADY_CHECKED_IN'] else 400
            return Response(
                {'error': {'code': e.code, 'message': e.message, 'details': e.details}},
                status=status_code
            )


class UnassignRoomView(APIView):
    """POST /api/staff/hotels/{hotel_slug}/bookings/{booking_id}/unassign-room/"""
    
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    @transaction.atomic
    def post(self, request, hotel_slug, booking_id):
        booking = get_object_or_404(
            RoomBooking.objects.select_for_update(),
            booking_id=booking_id, 
            hotel__slug=hotel_slug
        )
        
        # Centralized staff resolution
        staff_user = get_staff_or_403(request.user, booking.hotel)
        
        # Use proper in-house check: checked_in_at exists AND not checked_out_at  
        if booking.checked_in_at and not booking.checked_out_at:
            return Response(
                {'error': {'code': 'BOOKING_ALREADY_CHECKED_IN', 'message': 'Cannot unassign room for in-house guest'}},
                status=409
            )
        
        if not booking.assigned_room:
            return Response(
                {'error': {'code': 'NO_ROOM_ASSIGNED', 'message': 'No room currently assigned'}},
                status=400
            )
        
        # Audit log unassignment
        booking.assigned_room = None
        booking.room_unassigned_at = timezone.now()
        booking.room_unassigned_by = staff_user
        if booking.assignment_notes:
            booking.assignment_notes += f"\n[UNASSIGNED: {timezone.now()} by {staff_user}]"
        else:
            booking.assignment_notes = f"[UNASSIGNED: {timezone.now()} by {staff_user}]"
        booking.save()
        
        return Response({'message': 'Room unassigned successfully'})


class BookingCheckInView(APIView):
    """POST /api/staff/hotels/{hotel_slug}/room-bookings/{booking_id}/check-in/"""
    
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def _emit_checkin_realtime_events(self, booking, room, primary_guest, party_guest_objects):
        """Emit realtime events for check-in - called after transaction commit"""
        try:
            notification_manager.realtime_booking_checked_in(booking, room, primary_guest, party_guest_objects)
            notification_manager.realtime_room_occupancy_updated(room)
        except Exception as e:
            logger.error(f"Failed to emit check-in realtime events for booking {booking.booking_id}: {e}")
    
    def post(self, request, hotel_slug, booking_id):
        try:
            # Get booking with hotel validation
            booking = RoomBooking.objects.get(
                booking_id=booking_id,
                hotel__slug=hotel_slug
            )
        except RoomBooking.DoesNotExist:
            return Response(
                {'error': {'code': 'BOOKING_NOT_FOUND', 'message': 'Booking not found'}},
                status=404
            )
        
        # Centralized staff resolution
        staff_user = get_staff_or_403(request.user, booking.hotel)
        
        # Check if booking is eligible for check-in
        if booking.status != 'CONFIRMED':
            return Response(
                {'error': {'code': 'BOOKING_NOT_CONFIRMED', 'message': f'Booking must be CONFIRMED to check-in. Current status: {booking.status}'}},
                status=400
            )
        
        if not booking.assigned_room:
            return Response(
                {'error': {'code': 'NO_ROOM_ASSIGNED', 'message': 'Room must be assigned before check-in'}},
                status=400
            )
        
        if not booking.party_complete:
            return Response(
                {'error': {'code': 'PARTY_INCOMPLETE', 'message': 'Please provide all staying guest names before check-in'}},
                status=400
            )
        
        # Check for double check-in (idempotency)
        if booking.checked_in_at and not booking.checked_out_at:
            return Response(
                {'error': {'code': 'ALREADY_CHECKED_IN', 'message': 'Booking is already checked in'}},
                status=409
            )
        
        # PERFORM FULL CHECK-IN PROCESS
        with transaction.atomic():
            # Set check-in timestamp
            booking.checked_in_at = timezone.now()
            booking.save()
            
            # Get the assigned room
            room = booking.assigned_room
            hotel = booking.hotel
            
            # Get all booking party members
            booking_guests = booking.party.all().select_related()
            
            # Convert all party members to in-house Guests
            primary_guest = None
            party_guest_objects = []
            
            for booking_guest in booking_guests:
                # Create/update Guest record idempotently using booking_guest FK
                guest, created = Guest.objects.get_or_create(
                    booking_guest=booking_guest,
                    defaults={
                        'hotel': hotel,
                        'first_name': booking_guest.first_name,
                        'last_name': booking_guest.last_name,
                        'room': room,
                        'check_in_date': booking.check_in,
                        'check_out_date': booking.check_out,
                        'days_booked': (booking.check_out - booking.check_in).days,
                        'guest_type': booking_guest.role,
                        'primary_guest': None,  # Will be set after we find primary
                        'booking': booking,
                    }
                )
                
                if not created:
                    # Update existing guest
                    guest.hotel = hotel
                    guest.first_name = booking_guest.first_name
                    guest.last_name = booking_guest.last_name
                    guest.room = room
                    guest.check_in_date = booking.check_in
                    guest.check_out_date = booking.check_out
                    guest.days_booked = (booking.check_out - booking.check_in).days
                    guest.guest_type = booking_guest.role
                    guest.booking = booking
                    guest.save()
                
                party_guest_objects.append(guest)
                
                # Track primary guest
                if booking_guest.role == 'PRIMARY':
                    primary_guest = guest
            
            # Update companion references to point to primary guest
            if primary_guest:
                for guest in party_guest_objects:
                    if guest.guest_type == 'COMPANION':
                        guest.primary_guest = primary_guest
                        guest.save()
            
            # Update room occupancy - Room Turnover Workflow
            room.is_occupied = True
            room.room_status = 'OCCUPIED'
            room.save()
            
            # Trigger realtime notifications - ONLY AFTER DB COMMIT
            transaction.on_commit(
                lambda: self._emit_checkin_realtime_events(booking, room, primary_guest, party_guest_objects)
            )
        
        # Return updated booking with check-in details
        serializer = StaffRoomBookingDetailSerializer(booking)
        return Response({
            'message': f'Successfully checked in booking {booking_id}',
            **serializer.data
        })


class BookingCheckOutView(APIView):
    """POST /api/staff/hotels/{hotel_slug}/room-bookings/{booking_id}/check-out/"""
    
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def _emit_checkout_realtime_events(self, booking, room, hotel):
        """Emit realtime events for check-out - called after transaction commit"""
        try:
            notification_manager.realtime_booking_checked_out(booking, room.room_number)
            notification_manager.realtime_room_occupancy_updated(room)
            
            # Room status notification
            pusher_client.trigger(
                f'hotel-{hotel.slug}',
                'room-status-changed',
                {
                    'room_number': room.room_number,
                    'old_status': 'OCCUPIED',
                    'new_status': 'CHECKOUT_DIRTY',
                    'timestamp': timezone.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to emit check-out realtime events for booking {booking.booking_id}: {e}")
    
    def post(self, request, hotel_slug, booking_id):
        try:
            from room_bookings.services.checkout import checkout_booking
            
            # Get booking with hotel validation
            booking = RoomBooking.objects.get(
                booking_id=booking_id,
                hotel__slug=hotel_slug
            )
        except RoomBooking.DoesNotExist:
            return Response(
                {'error': {'code': 'BOOKING_NOT_FOUND', 'message': 'Booking not found'}},
                status=404
            )
        
        # Centralized staff resolution
        staff_user = get_staff_or_403(request.user, booking.hotel)
        
        # Validate booking is checked in
        if not booking.checked_in_at or booking.checked_out_at:
            return Response(
                {'error': {'code': 'NOT_CHECKED_IN', 'message': 'Booking must be checked in to check out'}},
                status=400
            )
        
        try:
            # Use centralized checkout service
            checkout_booking(
                booking=booking,
                performed_by=staff_user,
                source="staff_checkout_endpoint",
            )
            
            # Return updated booking with check-out details
            booking.refresh_from_db()
            serializer = StaffRoomBookingDetailSerializer(booking)
            
            return Response({
                'message': f'Successfully checked out booking {booking_id} from room {booking.assigned_room.room_number}',
                **serializer.data
            })
            
        except ValueError as e:
            return Response(
                {'error': {'code': 'CHECKOUT_FAILED', 'message': str(e)}},
                status=400
            )
        except Exception as e:
            logger.error(f"Unexpected error during checkout: {e}")
            return Response(
                {'error': {'code': 'INTERNAL_ERROR', 'message': 'An unexpected error occurred'}},
                status=500
            )


class SafeStaffBookingListView(APIView):
    """GET /api/staff/hotels/{hotel_slug}/bookings/safe/"""
    
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel] 
    
    def get(self, request, hotel_slug):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        queryset = RoomBooking.objects.filter(hotel=hotel).select_related(
            'assigned_room', 'room_type', 'room_assigned_by'
        )
        
        # Query parameter filters
        from_date = request.query_params.get('from')
        to_date = request.query_params.get('to')
        status_filter = request.query_params.get('status')
        assigned = request.query_params.get('assigned')  # true/false
        arriving = request.query_params.get('arriving')  # today
        room_type = request.query_params.get('room_type')
        
        if from_date:
            queryset = queryset.filter(check_in__gte=from_date)
        if to_date:
            queryset = queryset.filter(check_out__lte=to_date)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if assigned == 'true':
            queryset = queryset.filter(assigned_room__isnull=False)
        elif assigned == 'false':
            queryset = queryset.filter(assigned_room__isnull=True)
        if arriving == 'today':
            today = timezone.now().date()
            queryset = queryset.filter(check_in=today)
        if room_type:
            # Use room_type code instead of name (names can collide across hotels)
            try:
                room_type_obj = RoomType.objects.get(hotel=hotel, code=room_type)
                queryset = queryset.filter(room_type=room_type_obj)
            except RoomType.DoesNotExist:
                pass  # Invalid room type, ignore filter
                
        # Paginate and serialize
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = RoomBookingListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SendPrecheckinLinkView(APIView):
    """Send pre-check-in link to guest via email"""
    permission_classes = [IsAuthenticated]

    def post(self, request, hotel_slug, booking_id):
        """Generate token and send pre-check-in email to guest"""
        
        # Validate hotel scope and get booking
        try:
            booking = RoomBooking.objects.get(
                booking_id=booking_id,
                hotel__slug=hotel_slug
            )
        except RoomBooking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=404
            )
        
        # Generate secure token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = timezone.now() + timedelta(hours=72)
        
        # Determine target email
        target_email = booking.primary_email or booking.booker_email
        if not target_email:
            return Response(
                {'error': 'No email address found for this booking'},
                status=400
            )
        
        # Revoke any existing active tokens for this booking
        BookingPrecheckinToken.objects.filter(
            booking=booking,
            used_at__isnull=True,
            revoked_at__isnull=True
        ).update(revoked_at=timezone.now())
        
        # Get current hotel precheckin configuration for snapshot
        hotel_config = HotelPrecheckinConfig.get_or_create_default(booking.hotel)
        
        # Create new token with config snapshot
        token = BookingPrecheckinToken.objects.create(
            booking=booking,
            token_hash=token_hash,
            expires_at=expires_at,
            sent_to_email=target_email,
            config_snapshot_enabled=hotel_config.fields_enabled.copy(),
            config_snapshot_required=hotel_config.fields_required.copy()
        )
        
        # Send email with pre-check-in link
        # For now, we'll construct a simple email
        # TODO: Create dedicated pre-check-in email template
        base_domain = getattr(settings, 'FRONTEND_BASE_URL', 'https://hotelsmates.com')
        precheckin_url = f"{base_domain}/guest/hotel/{hotel_slug}/precheckin?token={raw_token}"
        
        try:
            subject = f"Complete your check-in details - {booking.hotel.name}"
            message = f"""
Dear {booking.primary_guest_name or 'Guest'},

Please complete your party details before your stay at {booking.hotel.name}.

Booking: {booking.booking_id}
Dates: {booking.check_in} to {booking.check_out}

Complete your details here: {precheckin_url}

This link expires in 72 hours.

Best regards,
{booking.hotel.name} Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[target_email],
                fail_silently=False,
            )
            
        except Exception as e:
            # If email fails, revoke the token
            token.revoked_at = timezone.now()
            token.save()
            return Response(
                {'error': 'Failed to send email'},
                status=500
            )
        
        return Response({
            'success': True,
            'sent_to': target_email,
            'expires_at': expires_at.isoformat(),
            'booking_id': booking.booking_id
        })


class HotelPrecheckinConfigView(APIView):
    """Manage hotel-level precheckin field configuration"""
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def get(self, request, hotel_slug):
        """Get current precheckin configuration for hotel"""
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        config = HotelPrecheckinConfig.get_or_create_default(hotel)
        
        return Response({
            'enabled': config.fields_enabled,
            'required': config.fields_required,
            'field_registry': PRECHECKIN_FIELD_REGISTRY
        })
    
    def post(self, request, hotel_slug):
        """Update precheckin configuration for hotel"""
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        enabled = request.data.get('enabled', {})
        required = request.data.get('required', {})
        
        if not isinstance(enabled, dict) or not isinstance(required, dict):
            return Response(
                {'error': 'enabled and required must be objects'},
                status=400
            )
        
        # Validate all keys exist in registry
        for field_key in enabled.keys():
            if field_key not in PRECHECKIN_FIELD_REGISTRY:
                return Response(
                    {'error': f'Unknown field key: {field_key}'},
                    status=400
                )
        
        for field_key in required.keys():
            if field_key not in PRECHECKIN_FIELD_REGISTRY:
                return Response(
                    {'error': f'Unknown field key: {field_key}'},
                    status=400
                )
        
        # Validate subset rule: required must be subset of enabled
        for field_key, is_required in required.items():
            if is_required and not enabled.get(field_key, False):
                return Response(
                    {'error': f'Field \'{field_key}\' cannot be required without being enabled'},
                    status=400
                )
        
        # Get or create config and update
        config = HotelPrecheckinConfig.get_or_create_default(hotel)
        config.fields_enabled = enabled
        config.fields_required = required
        
        # Run model validation
        try:
            config.full_clean()
            config.save()
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=400
            )
        
        return Response({
            'success': True,
            'enabled': config.fields_enabled,
            'required': config.fields_required
        })


# ============================================================================
# STRIPE AUTHORIZE-CAPTURE FLOW: STAFF ACCEPT/DECLINE ENDPOINTS
# ============================================================================

class StaffBookingAcceptView(APIView):
    """
    Approve a PENDING_APPROVAL booking by capturing the authorized payment.
    
    POST /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/approve/
    
    Multi-tenant safe: Validates hotel ownership before processing.
    """
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def post(self, request, hotel_slug, booking_id):
        """Approve a booking and capture the authorized payment."""
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response(
                {'error': 'Staff profile not found'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Multi-tenant safety: validate hotel ownership
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        if staff.hotel != hotel:
            return Response(
                {'error': 'You can only accept bookings for your hotel'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            # Get booking with row lock for atomic updates
            try:
                booking = RoomBooking.objects.select_for_update().get(
                    booking_id=booking_id, 
                    hotel=hotel
                )
                print(f"🔍 Found booking {booking_id} with status: {booking.status}, payment_intent: {booking.payment_intent_id}")
            except RoomBooking.DoesNotExist:
                return Response(
                    {'error': 'Booking not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Idempotency check: if already CONFIRMED, return success
            if booking.status == 'CONFIRMED':
                return Response({
                    'status': 'approved',
                    'booking_id': booking_id,
                    'message': 'Booking is already confirmed (idempotent)',
                    'booking': {
                        'booking_id': booking.booking_id,
                        'status': booking.status,
                        'paid_at': booking.paid_at.isoformat() if booking.paid_at else None
                    }
                }, status=status.HTTP_200_OK)
            
            # Validate booking state
            if booking.status != 'PENDING_APPROVAL':
                return Response(
                    {'error': f'Cannot approve booking with status {booking.status}. Expected PENDING_APPROVAL.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate payment provider and intent
            if booking.payment_provider != 'stripe':
                return Response(
                    {'error': f'Invalid payment provider: {booking.payment_provider}. Expected stripe.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not booking.payment_intent_id:
                return Response(
                    {'error': 'No payment intent found for capture. Cannot approve booking.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Capture payment via Stripe
            try:
                print(f"🔄 Capturing payment for booking {booking_id}, PaymentIntent: {booking.payment_intent_id}")
                
                # First, check if PaymentIntent is already captured
                intent = stripe.PaymentIntent.retrieve(booking.payment_intent_id)
                
                if intent.status == 'succeeded':
                    print(f"✅ Payment already captured: {intent.id}")
                    captured_intent = intent
                elif intent.status == 'requires_capture':
                    captured_intent = stripe.PaymentIntent.capture(booking.payment_intent_id)
                    if captured_intent.status != 'succeeded':
                        raise Exception(f"Unexpected capture status: {captured_intent.status}")
                    print(f"✅ Payment captured successfully: {captured_intent.id}")
                else:
                    raise Exception(f"PaymentIntent in unexpected state: {intent.status}")
                
            except stripe.error.InvalidRequestError as e:
                if "already been captured" in str(e):
                    # Handle already captured case by retrieving the intent
                    print(f"⚠️ PaymentIntent already captured, retrieving status...")
                    try:
                        captured_intent = stripe.PaymentIntent.retrieve(booking.payment_intent_id)
                        if captured_intent.status == 'succeeded':
                            print(f"✅ Confirmed payment already captured: {captured_intent.id}")
                        else:
                            raise Exception(f"PaymentIntent captured but status is: {captured_intent.status}")
                    except Exception as retrieve_error:
                        logger.error(f"Failed to retrieve already captured PaymentIntent {booking.payment_intent_id}: {retrieve_error}")
                        return Response(
                            {'error': f'Payment verification failed: {str(retrieve_error)}'}, 
                            status=status.HTTP_502_BAD_GATEWAY
                        )
                else:
                    logger.error(f"Stripe capture failed for booking {booking_id}: {e}")
                    return Response(
                        {'error': f'Payment capture failed: {str(e)}'}, 
                        status=status.HTTP_502_BAD_GATEWAY
                    )
            except stripe.error.StripeError as e:
                logger.error(f"Stripe capture failed for booking {booking_id}: {e}")
                return Response(
                    {'error': f'Payment capture failed: {str(e)}'}, 
                    status=status.HTTP_502_BAD_GATEWAY
                )
            except Exception as e:
                logger.error(f"Unexpected error during capture for booking {booking_id}: {e}")
                return Response(
                    {'error': f'Payment capture failed: {str(e)}'}, 
                    status=status.HTTP_502_BAD_GATEWAY
                )
            
            # Update booking to CONFIRMED state
            booking.status = 'CONFIRMED'
            booking.paid_at = timezone.now()
            
            booking.save(update_fields=[
                'status', 'paid_at'
            ])
            
            print(f"✅ Booking {booking_id} approved and confirmed by staff {staff.id}")
        
        # Send confirmation notifications
        try:
            send_booking_confirmation_email(booking)
            logger.info(f"Confirmation email sent for approved booking {booking_id}")
        except ImportError:
            logger.warning(f"Email service not available for booking confirmation")
        except Exception as e:
            logger.error(f"Failed to send confirmation email for booking {booking_id}: {e}")
        
        try:
            # Try to get FCM token if guest is checked in
            guest_fcm_token = None
            try:
                if booking.assigned_room:
                    guest_fcm_token = booking.assigned_room.guest_fcm_token
            except:
                pass
            
            if guest_fcm_token:
                send_booking_confirmation_notification(guest_fcm_token, booking)
                logger.info(f"Confirmation notification sent for approved booking {booking_id}")
        except ImportError:
            logger.warning(f"FCM service not available for booking confirmation")
        except Exception as e:
            logger.error(f"Failed to send confirmation notification for booking {booking_id}: {e}")
        
        # Trigger realtime update
        try:
            notification_manager.realtime_booking_updated(booking)
        except Exception as e:
            logger.error(f"Failed to send realtime update for booking {booking_id}: {e}")
        
        return Response({
            'status': 'approved',
            'booking_id': booking_id,
            'message': 'Booking approved and payment captured successfully',
            'booking': {
                'booking_id': booking.booking_id,
                'status': booking.status,
                'paid_at': booking.paid_at.isoformat() if booking.paid_at else None
            }
        }, status=status.HTTP_200_OK)


class StaffBookingDeclineView(APIView):
    """
    Decline a PENDING_APPROVAL booking by cancelling the authorization.
    
    POST /api/staff/hotel/<hotel_slug>/room-bookings/<booking_id>/decline/
    Body: {"reason_code": "AVAILABILITY", "reason_note": "Room no longer available"}
    
    Multi-tenant safe: Validates hotel ownership before processing.
    """
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def post(self, request, hotel_slug, booking_id):
        """Decline a booking and cancel the authorized payment."""
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response(
                {'error': 'Staff profile not found'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Multi-tenant safety: validate hotel ownership
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        if staff.hotel != hotel:
            return Response(
                {'error': 'You can only decline bookings for your hotel'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Extract decline reason from request
        reason_code = request.data.get('reason_code', 'OTHER')
        reason_note = request.data.get('reason_note', '')
        
        # Ensure we have a reason code for declined bookings
        if not reason_code:
            reason_code = 'OTHER'
        
        with transaction.atomic():
            # Get booking with row lock for atomic updates
            try:
                booking = RoomBooking.objects.select_for_update().get(
                    booking_id=booking_id, 
                    hotel=hotel
                )
            except RoomBooking.DoesNotExist:
                return Response(
                    {'error': 'Booking not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Idempotency check: if already DECLINED, return success
            if booking.status == 'DECLINED':
                return Response({
                    'status': 'declined',
                    'booking_id': booking_id,
                    'message': 'Booking is already declined (idempotent)',
                    'booking': {
                        'booking_id': booking.booking_id,
                        'status': booking.status,
                        'decision_made_at': booking.decision_made_at.isoformat() if booking.decision_made_at else None,
                        'decline_reason_code': booking.decline_reason_code,
                        'decline_reason_note': booking.decline_reason_note
                    }
                }, status=status.HTTP_200_OK)
            
            # Validate booking state
            if booking.status != 'PENDING_APPROVAL':
                return Response(
                    {'error': f'Cannot decline booking with status {booking.status}. Expected PENDING_APPROVAL.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate payment provider (only process if Stripe)
            if booking.payment_provider and booking.payment_provider != 'stripe':
                return Response(
                    {'error': f'Invalid payment provider: {booking.payment_provider}. Expected stripe.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Cancel authorization via Stripe (if payment_intent exists)
            if booking.payment_intent_id:
                try:
                    print(f"🔄 Cancelling authorization for booking {booking_id}, PaymentIntent: {booking.payment_intent_id}")
                    cancelled_intent = stripe.PaymentIntent.cancel(booking.payment_intent_id)
                    
                    if cancelled_intent.status != 'canceled':
                        logger.warning(f"Unexpected cancellation status: {cancelled_intent.status} for booking {booking_id}")
                    
                    print(f"✅ Authorization cancelled successfully: {cancelled_intent.id}")
                    
                except stripe.error.StripeError as e:
                    logger.error(f"Stripe cancellation failed for booking {booking_id}: {e}")
                    return Response(
                        {'error': f'Payment cancellation failed: {str(e)}'}, 
                        status=status.HTTP_502_BAD_GATEWAY
                    )
                except Exception as e:
                    logger.error(f"Unexpected error during cancellation for booking {booking_id}: {e}")
                    return Response(
                        {'error': f'Payment cancellation failed: {str(e)}'}, 
                        status=status.HTTP_502_BAD_GATEWAY
                    )
            
            # Update booking to DECLINED state
            booking.status = 'DECLINED'
            booking.decision_made_by = staff.user  # Store User, not Staff
            booking.decision_made_at = timezone.now()
            booking.decline_reason_code = reason_code
            booking.decline_reason_note = reason_note
            
            booking.save(update_fields=[
                'status', 'decision_made_by', 'decision_made_at', 
                'decline_reason_code', 'decline_reason_note'
            ])
            
            print(f"✅ Booking {booking_id} declined by staff {staff.id} - Reason: {reason_code}")
        
        # Send decline notifications
        try:
            staff_name = f"{staff.first_name} {staff.last_name}".strip() or staff.user.username
            send_booking_cancellation_email(booking, reason_note or reason_code, staff_name)
            logger.info(f"Decline email sent for booking {booking_id}")
        except ImportError:
            logger.warning(f"Email service not available for booking decline")
        except Exception as e:
            logger.error(f"Failed to send decline email for booking {booking_id}: {e}")
        
        try:
            notification_manager.realtime_booking_updated(booking)
            logger.info(f"Decline notification sent for booking {booking_id}")
        except Exception as e:
            logger.error(f"Failed to send decline notification for booking {booking_id}: {e}")
        
        return Response({
            'status': 'declined',
            'booking_id': booking_id,
            'reason_code': reason_code,
            'reason_note': reason_note,
            'message': 'Booking declined and authorization cancelled',
            'booking': {
                'booking_id': booking.booking_id,
                'status': booking.status,
                'decision_made_at': booking.decision_made_at.isoformat() if booking.decision_made_at else None,
                'decline_reason_code': booking.decline_reason_code,
                'decline_reason_note': booking.decline_reason_note
            }
        }, status=status.HTTP_200_OK)
