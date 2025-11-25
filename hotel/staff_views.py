"""
Staff CRUD Views for Hotel Content Management (B5)
Provides staff-only CRUD operations for:
- Offers
- Leisure Activities
- Room Types (marketing)
- Rooms (inventory)
- Access Configuration
- Gallery Image Management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
import cloudinary.uploader

from staff_chat.permissions import IsStaffMember, IsSameHotel
from chat.utils import pusher_client
from .models import (
    Offer,
    LeisureActivity,
    HotelAccessConfig,
    Gallery,
    GalleryImage
)
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


class StaffGalleryImageUploadView(APIView):
    """
    Staff endpoint to upload gallery images to Cloudinary.
    Returns image URL to add to gallery array.
    
    POST /api/staff/hotel/<hotel_slug>/settings/gallery/upload/
    Body (multipart): { "image": file }
    Response: { "url": "https://cloudinary.com/...", "public_id": "..." }
    """
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def post(self, request, hotel_slug):
        # Verify staff access
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if staff.hotel.slug != hotel_slug:
            return Response(
                {'error': 'You can only upload images for your hotel'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check for image file
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Upload to Cloudinary
        image_file = request.FILES['image']
        try:
            result = cloudinary.uploader.upload(
                image_file,
                folder=f"hotels/{hotel_slug}/gallery",
                resource_type="image"
            )
            
            # Add to Hotel gallery (public page)
            hotel = staff.hotel
            if result['secure_url'] not in hotel.gallery:
                hotel.gallery.append(result['secure_url'])
                hotel.save()
            
            # Broadcast gallery update via Pusher
            try:
                pusher_client.trigger(
                    f'hotel-{hotel_slug}',
                    'gallery-image-uploaded',
                    {
                        'url': result['secure_url'],
                        'public_id': result['public_id'],
                        'gallery': hotel.gallery
                    }
                )
            except Exception:
                pass  # Don't fail if Pusher fails
            
            return Response({
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'gallery': hotel.gallery,
                'message': 'Image uploaded successfully'
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StaffGalleryManagementView(APIView):
    """
    Staff endpoint to manage hotel gallery.
    
    POST /api/staff/hotel/<hotel_slug>/settings/gallery/reorder/
    Body: { "gallery": ["url1", "url2", "url3"] }
    
    DELETE /api/staff/hotel/<hotel_slug>/settings/gallery/remove/
    Body: { "url": "https://cloudinary.com/image.jpg" }
    """
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def post(self, request, hotel_slug):
        """Reorder gallery images"""
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if staff.hotel.slug != hotel_slug:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get hotel
        hotel = staff.hotel
        
        # Validate gallery data
        new_gallery = request.data.get('gallery')
        if not isinstance(new_gallery, list):
            return Response(
                {'error': 'gallery must be a list of URLs'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update gallery on Hotel model (public page)
        hotel.gallery = new_gallery
        hotel.save()
        
        # Broadcast via Pusher
        try:
            pusher_client.trigger(
                f'hotel-{hotel_slug}',
                'gallery-reordered',
                {'gallery': hotel.gallery}
            )
        except Exception:
            pass
        
        return Response({
            'message': 'Gallery updated successfully',
            'gallery': hotel.gallery
        })
    
    def delete(self, request, hotel_slug):
        """Remove single image from gallery"""
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if staff.hotel.slug != hotel_slug:
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get hotel
        hotel = staff.hotel
        
        # Get URL to remove
        url_to_remove = request.data.get('url')
        if not url_to_remove:
            return Response(
                {'error': 'url parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove from gallery
        if url_to_remove in hotel.gallery:
            hotel.gallery.remove(url_to_remove)
            hotel.save()
            
            # Broadcast gallery update via Pusher
            try:
                pusher_client.trigger(
                    f'hotel-{hotel_slug}',
                    'gallery-image-removed',
                    {
                        'removed_url': url_to_remove,
                        'gallery': hotel.gallery
                    }
                )
            except Exception:
                pass
            
            return Response({
                'message': 'Image removed from gallery',
                'gallery': hotel.gallery
            })
        else:
            return Response(
                {'error': 'URL not found in gallery'},
                status=status.HTTP_404_NOT_FOUND
            )


# ==================== Gallery Management ViewSets ====================


class StaffGalleryViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD operations for galleries.
    
    Endpoints:
    - GET    /api/staff/hotel/<slug>/galleries/ - List all galleries
    - POST   /api/staff/hotel/<slug>/galleries/ - Create new gallery
    - GET    /api/staff/hotel/<slug>/galleries/<id>/ - Get gallery
    - PATCH  /api/staff/hotel/<slug>/galleries/<id>/ - Update gallery
    - DELETE /api/staff/hotel/<slug>/galleries/<id>/ - Delete gallery
    """
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Return galleries for staff's hotel"""
        staff = self.request.user.staff_profile
        from .serializers import GallerySerializer
        self.serializer_class = GallerySerializer
        return Gallery.objects.filter(hotel=staff.hotel).prefetch_related(
            'images'
        )
    
    def get_serializer_class(self):
        """Use different serializers for list/create/update"""
        from .serializers import (
            GallerySerializer,
            GalleryCreateUpdateSerializer
        )
        if self.action in ['create', 'update', 'partial_update']:
            return GalleryCreateUpdateSerializer
        return GallerySerializer
    
    def perform_create(self, serializer):
        """Set hotel from staff profile"""
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel)
    
    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None, hotel_slug=None):
        """
        Upload image to gallery.
        POST /api/staff/hotel/<slug>/galleries/<id>/upload_image/
        Body (multipart): { "image": file, "caption": "...", ... }
        """
        gallery = self.get_object()
        
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from .serializers import GalleryImageCreateSerializer
        serializer = GalleryImageCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(gallery=gallery)
            
            # Broadcast update
            try:
                pusher_client.trigger(
                    f'hotel-{gallery.hotel.slug}',
                    'gallery-updated',
                    {
                        'gallery_id': gallery.id,
                        'gallery_name': gallery.name,
                        'action': 'image_added',
                        'image_count': gallery.images.count()
                    }
                )
            except Exception:
                pass
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reorder_images(self, request, pk=None, hotel_slug=None):
        """
        Reorder images in gallery.
        POST /api/staff/hotel/<slug>/galleries/<id>/reorder_images/
        Body: { "image_ids": [3, 1, 5, 2] }
        """
        gallery = self.get_object()
        image_ids = request.data.get('image_ids', [])
        
        if not isinstance(image_ids, list):
            return Response(
                {'error': 'image_ids must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update display_order for each image
        for order, image_id in enumerate(image_ids):
            GalleryImage.objects.filter(
                id=image_id,
                gallery=gallery
            ).update(display_order=order)
        
        # Broadcast update
        try:
            pusher_client.trigger(
                f'hotel-{gallery.hotel.slug}',
                'gallery-updated',
                {
                    'gallery_id': gallery.id,
                    'gallery_name': gallery.name,
                    'action': 'images_reordered'
                }
            )
        except Exception:
            pass
        
        return Response({'message': 'Images reordered successfully'})


class StaffGalleryImageViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD operations for gallery images.
    
    Endpoints:
    - GET    /api/staff/hotel/<slug>/gallery-images/ - List images
    - GET    /api/staff/hotel/<slug>/gallery-images/<id>/ - Get image
    - PATCH  /api/staff/hotel/<slug>/gallery-images/<id>/ - Update caption
    - DELETE /api/staff/hotel/<slug>/gallery-images/<id>/ - Delete image
    """
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Return images for staff's hotel galleries"""
        staff = self.request.user.staff_profile
        return GalleryImage.objects.filter(
            gallery__hotel=staff.hotel
        ).select_related('gallery')
    
    def get_serializer_class(self):
        """Use different serializers for update"""
        from .serializers import (
            GalleryImageSerializer,
            GalleryImageUpdateSerializer
        )
        if self.action in ['update', 'partial_update']:
            return GalleryImageUpdateSerializer
        return GalleryImageSerializer
    
    def perform_destroy(self, instance):
        """Broadcast deletion and remove image"""
        gallery = instance.gallery
        instance.delete()
        
        # Broadcast update
        try:
            pusher_client.trigger(
                f'hotel-{gallery.hotel.slug}',
                'gallery-updated',
                {
                    'gallery_id': gallery.id,
                    'gallery_name': gallery.name,
                    'action': 'image_removed',
                    'image_count': gallery.images.count()
                }
            )
        except Exception:
            pass
