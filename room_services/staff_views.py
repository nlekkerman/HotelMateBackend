"""
Staff CRUD Views for Room Service Menu Management
Provides staff-only CRUD operations for:
- Room Service Items (menu)
- Breakfast Items (menu)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)

from staff_chat.permissions import IsStaffMember, IsSameHotel
from notifications.notification_manager import notification_manager
from .models import RoomServiceItem, BreakfastItem
from .serializers import RoomServiceItemStaffSerializer, BreakfastItemStaffSerializer


class StaffRoomServiceItemViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for room service menu items.
    Scoped to staff's hotel only.
    """
    serializer_class = RoomServiceItemStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Only return room service items for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return RoomServiceItem.objects.filter(
                hotel=staff.hotel
            ).order_by('category', 'name')
        except AttributeError:
            return RoomServiceItem.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set hotel from staff profile"""
        staff = self.request.user.staff_profile
        item = serializer.save(hotel=staff.hotel)
        
        # Send real-time notification
        try:
            notification_manager.realtime_menu_item_updated(
                hotel=staff.hotel,
                menu_type='room_service',
                item_data={
                    'id': item.id,
                    'name': item.name,
                    'category': item.category,
                    'price': str(item.price),
                    'is_on_stock': item.is_on_stock
                },
                action='created'
            )
        except Exception as e:
            logger.error(f"Failed to send menu item notification: {e}")
    
    def perform_update(self, serializer):
        """Send update notification"""
        item = serializer.save()
        staff = self.request.user.staff_profile
        
        try:
            notification_manager.realtime_menu_item_updated(
                hotel=staff.hotel,
                menu_type='room_service',
                item_data={
                    'id': item.id,
                    'name': item.name,
                    'category': item.category,
                    'price': str(item.price),
                    'is_on_stock': item.is_on_stock
                },
                action='updated'
            )
        except Exception as e:
            logger.error(f"Failed to send menu item update notification: {e}")
    
    def perform_destroy(self, instance):
        """Send delete notification"""
        staff = self.request.user.staff_profile
        item_data = {
            'id': instance.id,
            'name': instance.name,
            'category': instance.category
        }
        
        instance.delete()
        
        try:
            notification_manager.realtime_menu_item_updated(
                hotel=staff.hotel,
                menu_type='room_service',
                item_data=item_data,
                action='deleted'
            )
        except Exception as e:
            logger.error(f"Failed to send menu item delete notification: {e}")
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None, hotel_slug=None):
        """
        Upload or update room service item image.
        Accepts either file upload or image URL.
        
        POST /api/staff/hotel/{slug}/room-service-items/{id}/upload-image/
        
        Body (multipart/form-data or JSON):
        - image: file upload (multipart)
        OR
        - image_url: image URL string (JSON)
        """
        try:
            item = self.get_object()
            
            if 'image' in request.FILES:
                # Handle file upload
                item.image = request.FILES['image']
                item.save()
                
                serializer = self.get_serializer(item)
                return Response({
                    'message': 'Image uploaded successfully',
                    'item': serializer.data
                })
                
            elif 'image_url' in request.data:
                # Handle URL upload
                item.image = request.data['image_url']
                item.save()
                
                serializer = self.get_serializer(item)
                return Response({
                    'message': 'Image URL set successfully',
                    'item': serializer.data
                })
            else:
                return Response(
                    {'error': 'No image file or image_url provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return Response(
                {'error': f'Image upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StaffBreakfastItemViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for breakfast menu items.
    Scoped to staff's hotel only.
    """
    serializer_class = BreakfastItemStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Only return breakfast items for staff's hotel"""
        try:
            staff = self.request.user.staff_profile
            return BreakfastItem.objects.filter(
                hotel=staff.hotel
            ).order_by('category', 'name')
        except AttributeError:
            return BreakfastItem.objects.none()
    
    def perform_create(self, serializer):
        """Automatically set hotel from staff profile"""
        staff = self.request.user.staff_profile
        item = serializer.save(hotel=staff.hotel)
        
        # Send real-time notification
        try:
            notification_manager.realtime_menu_item_updated(
                hotel=staff.hotel,
                menu_type='breakfast',
                item_data={
                    'id': item.id,
                    'name': item.name,
                    'category': item.category,
                    'quantity': item.quantity,
                    'is_on_stock': item.is_on_stock
                },
                action='created'
            )
        except Exception as e:
            logger.error(f"Failed to send breakfast item notification: {e}")
    
    def perform_update(self, serializer):
        """Send update notification"""
        item = serializer.save()
        staff = self.request.user.staff_profile
        
        try:
            notification_manager.realtime_menu_item_updated(
                hotel=staff.hotel,
                menu_type='breakfast',
                item_data={
                    'id': item.id,
                    'name': item.name,
                    'category': item.category,
                    'quantity': item.quantity,
                    'is_on_stock': item.is_on_stock
                },
                action='updated'
            )
        except Exception as e:
            logger.error(f"Failed to send breakfast item update notification: {e}")
    
    def perform_destroy(self, instance):
        """Send delete notification"""
        staff = self.request.user.staff_profile
        item_data = {
            'id': instance.id,
            'name': instance.name,
            'category': instance.category
        }
        
        instance.delete()
        
        try:
            notification_manager.realtime_menu_item_updated(
                hotel=staff.hotel,
                menu_type='breakfast',
                item_data=item_data,
                action='deleted'
            )
        except Exception as e:
            logger.error(f"Failed to send breakfast item delete notification: {e}")
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None, hotel_slug=None):
        """
        Upload or update breakfast item image.
        Accepts either file upload or image URL.
        
        POST /api/staff/hotel/{slug}/breakfast-items/{id}/upload-image/
        
        Body (multipart/form-data or JSON):
        - image: file upload (multipart)
        OR
        - image_url: image URL string (JSON)
        """
        try:
            item = self.get_object()
            
            if 'image' in request.FILES:
                # Handle file upload
                item.image = request.FILES['image']
                item.save()
                
                serializer = self.get_serializer(item)
                return Response({
                    'message': 'Image uploaded successfully',
                    'item': serializer.data
                })
                
            elif 'image_url' in request.data:
                # Handle URL upload
                item.image = request.data['image_url']
                item.save()
                
                serializer = self.get_serializer(item)
                return Response({
                    'message': 'Image URL set successfully',
                    'item': serializer.data
                })
            else:
                return Response(
                    {'error': 'No image file or image_url provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return Response(
                {'error': f'Image upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )