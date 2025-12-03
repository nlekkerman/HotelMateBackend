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
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

from staff_chat.permissions import IsStaffMember, IsSameHotel
from chat.utils import pusher_client
from .models import (
    Hotel,
    HotelAccessConfig,
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
)
from rooms.models import RoomType, Room
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
                    
                    # Broadcast update via Pusher
                    try:
                        hotel_slug = self.request.user.staff_profile.hotel.slug
                        pusher_client.trigger(
                            f'hotel-{hotel_slug}',
                            'room-type-image-updated',
                            {
                                'room_type_id': room_type.id,
                                'photo_url': photo_url,
                                'timestamp': str(room_type.updated_at) if hasattr(room_type, 'updated_at') else None
                            }
                        )
                    except Exception:
                        pass  # Don't fail if Pusher fails
                    
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
        
        from .models import Hotel
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
            from rest_framework.exceptions import ValidationError
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
            from rest_framework.exceptions import ValidationError
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
                from rest_framework.exceptions import ValidationError
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
        from staff_chat.permissions import IsStaffMember, IsSameHotel
        return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]

    def get(self, request, hotel_slug):
        """Get complete hotel information and theme"""
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Get or create theme
        from common.models import ThemePreference
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
        from common.models import ThemePreference
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
        from staff_chat.permissions import IsStaffMember, IsSameHotel
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
            from datetime import datetime
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                bookings = bookings.filter(check_in__gte=start)
            except ValueError:
                return Response({'error': 'Invalid start_date format'}, status=status.HTTP_400_BAD_REQUEST)

        end_date = request.query_params.get('end_date')
        if end_date:
            from datetime import datetime
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                bookings = bookings.filter(check_out__lte=end)
            except ValueError:
                return Response({'error': 'Invalid end_date format'}, status=status.HTTP_400_BAD_REQUEST)

        from .serializers import RoomBookingListSerializer
        serializer = RoomBookingListSerializer(bookings, many=True)
        return Response(serializer.data)


class StaffBookingConfirmView(APIView):
    """Staff endpoint to confirm a booking."""
    permission_classes = []
    
    def get_permissions(self):
        from staff_chat.permissions import IsStaffMember, IsSameHotel
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

        if booking.status == 'CANCELLED':
            return Response({'error': 'Cannot confirm a cancelled booking'}, status=status.HTTP_400_BAD_REQUEST)

        if booking.status == 'CONFIRMED':
            return Response({'message': 'Booking is already confirmed'}, status=status.HTTP_200_OK)

        booking.status = 'CONFIRMED'
        booking.save()

        # Send email notification to guest
        try:
            from notifications.email_service import send_booking_confirmation_email
            send_booking_confirmation_email(booking)
        except ImportError:
            logger.warning("Email service not available for booking confirmation")
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")

        # Send FCM notification to guest if they have a token
        try:
            from notifications.fcm_service import send_booking_confirmation_notification
            # Try to find guest FCM token from room if they're checked in
            guest_fcm_token = None
            try:
                from rooms.models import Room
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
            
        except ImportError:
            logger.warning("FCM service not available for booking confirmation")

        from .serializers import RoomBookingDetailSerializer
        serializer = RoomBookingDetailSerializer(booking)
        return Response({'message': 'Booking confirmed successfully', 'booking': serializer.data})


class StaffBookingCancelView(APIView):
    """Staff endpoint to cancel a booking."""
    permission_classes = []
    
    def get_permissions(self):
        from staff_chat.permissions import IsStaffMember, IsSameHotel
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

        if booking.status == 'CANCELLED':
            return Response({'message': 'Booking is already cancelled'}, status=status.HTTP_200_OK)

        if booking.status == 'COMPLETED':
            return Response({'error': 'Cannot cancel a completed booking'}, status=status.HTTP_400_BAD_REQUEST)

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
        from django.utils import timezone
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
            from notifications.email_service import send_booking_cancellation_email
            send_booking_cancellation_email(booking, cancellation_reason, staff_name)
        except ImportError:
            logger.warning("Email service not available for booking cancellation")
        except Exception as e:
            logger.error(f"Failed to send cancellation email: {e}")

        # Send FCM notification to guest if they have a token
        try:
            from notifications.fcm_service import send_booking_cancellation_notification
            # Try to find guest FCM token from room if they're checked in
            guest_fcm_token = None
            try:
                from rooms.models import Room
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
            
        except ImportError:
            logger.warning("FCM service not available for booking cancellation")

        from .serializers import RoomBookingDetailSerializer
        serializer = RoomBookingDetailSerializer(booking)
        return Response({
            'message': 'Booking cancelled successfully', 
            'booking': serializer.data,
            'cancellation_reason': cancellation_reason
        })


class StaffBookingDetailView(APIView):
    """Staff endpoint to get detailed booking information."""
    permission_classes = []
    
    def get_permissions(self):
        from staff_chat.permissions import IsStaffMember, IsSameHotel
        return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]

    def get(self, request, hotel_slug, booking_id):
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response({'error': 'Staff profile not found'}, status=status.HTTP_403_FORBIDDEN)

        if staff.hotel.slug != hotel_slug:
            return Response({'error': 'You can only view bookings for your hotel'}, status=status.HTTP_403_FORBIDDEN)

        try:
            booking = RoomBooking.objects.select_related('hotel', 'room_type').get(
                booking_id=booking_id, 
                hotel=staff.hotel
            )
        except RoomBooking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        from .serializers import RoomBookingDetailSerializer
        serializer = RoomBookingDetailSerializer(booking)
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
        from .models import RoomsSection
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
        
        from .serializers import PublicSectionDetailSerializer
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
        from datetime import date
        
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
