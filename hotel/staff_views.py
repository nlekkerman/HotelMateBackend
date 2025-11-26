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
from django.shortcuts import get_object_or_404

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
