"""
Common mixins for Django REST framework views
"""
from django.shortcuts import get_object_or_404
from rest_framework import exceptions
from rest_framework.permissions import IsAuthenticated

from hotel.models import Hotel
from staff_chat.permissions import IsStaffMember, IsSameHotel


class HotelScopedViewSetMixin:
    """
    Mixin that provides hotel-scoped functionality for attendance/roster viewsets.
    
    This mixin ensures:
    1. Proper permission classes are applied (IsAuthenticated, IsStaffMember, IsSameHotel)
    2. QuerySets are always filtered to the user's hotel
    3. Hotel is properly assigned during create/update operations
    4. Consistent error handling for hotel-related operations
    
    Usage:
        class MyViewSet(HotelScopedViewSetMixin, viewsets.ModelViewSet):
            # The mixin will automatically add proper permissions and scoping
            pass
    
    Required:
        - URL must include 'hotel_slug' parameter
        - Model must have a 'hotel' foreign key field
        - User must have a 'staff_profile' attribute
    """
    
    # Default permission classes for hotel-scoped views
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_hotel(self):
        """
        Get the hotel instance from the URL hotel_slug parameter.
        
        Returns:
            Hotel: The hotel instance
            
        Raises:
            Http404: If hotel_slug is missing or hotel doesn't exist
        """
        hotel_slug = self.kwargs.get("hotel_slug")
        if not hotel_slug:
            raise exceptions.ValidationError("hotel_slug parameter is required in the URL")
        return get_object_or_404(Hotel, slug=hotel_slug)
    
    def get_staff_hotel(self):
        """
        Get the authenticated user's staff hotel.
        
        Returns:
            Hotel: The staff member's hotel
            
        Raises:
            PermissionDenied: If user has no staff profile
        """
        if not hasattr(self.request.user, 'staff_profile'):
            raise exceptions.PermissionDenied("User must have a staff profile")
        return self.request.user.staff_profile.hotel
    
    def validate_hotel_access(self):
        """
        Validate that the URL hotel matches the user's staff hotel.
        
        This provides an additional security check beyond the IsSameHotel permission.
        
        Raises:
            PermissionDenied: If hotels don't match
        """
        url_hotel = self.get_hotel()
        staff_hotel = self.get_staff_hotel()
        
        if url_hotel.id != staff_hotel.id:
            raise exceptions.PermissionDenied(
                "You don't have access to this hotel"
            )
    
    def get_queryset(self):
        """
        Return queryset filtered to the user's hotel.
        
        This method should be overridden in subclasses to apply additional filters,
        but must call super().get_queryset() to maintain hotel scoping.
        
        Returns:
            QuerySet: Hotel-scoped queryset
        """
        if not hasattr(self, 'queryset') or self.queryset is None:
            raise NotImplementedError(
                "HotelScopedViewSetMixin requires either a 'queryset' attribute "
                "or an overridden get_queryset() method"
            )
        
        # Validate access first
        self.validate_hotel_access()
        
        # Filter to user's hotel
        staff_hotel = self.get_staff_hotel()
        return self.queryset.filter(hotel=staff_hotel)
    
    def perform_create(self, serializer):
        """
        Assign hotel during creation based on the user's staff profile.
        
        Args:
            serializer: The model serializer instance
        """
        staff_hotel = self.get_staff_hotel()
        
        # Ensure hotel field is set correctly and cannot be overridden
        serializer.save(hotel=staff_hotel)
    
    def perform_update(self, serializer):
        """
        Ensure hotel cannot be changed during updates.
        
        Args:
            serializer: The model serializer instance
        """
        # Get the current instance
        instance = self.get_object()
        
        # Validate the instance belongs to the user's hotel
        staff_hotel = self.get_staff_hotel()
        if instance.hotel.id != staff_hotel.id:
            raise exceptions.PermissionDenied(
                "You cannot modify resources from other hotels"
            )
        
        # Ensure hotel remains unchanged
        serializer.save(hotel=instance.hotel)


class AttendanceHotelScopedMixin(HotelScopedViewSetMixin):
    """
    Specialized mixin for attendance-related viewsets.
    
    Extends HotelScopedViewSetMixin with attendance-specific functionality:
    - Automatic staff assignment for operations requiring approval
    - Additional validation for roster-specific operations
    """
    
    def perform_create(self, serializer):
        """
        Create with hotel and staff assignment for attendance records.
        
        Args:
            serializer: The model serializer instance
        """
        staff_hotel = self.get_staff_hotel()
        staff_profile = self.request.user.staff_profile
        
        # Check if the serializer expects an 'approved_by' field
        if 'approved_by' in serializer.Meta.fields:
            serializer.save(hotel=staff_hotel, approved_by=staff_profile)
        else:
            serializer.save(hotel=staff_hotel)
    
    def get_queryset(self):
        """
        Get attendance queryset with common optimizations.
        
        Returns:
            QuerySet: Optimized hotel-scoped queryset
        """
        queryset = super().get_queryset()
        
        # Add common select_related optimizations for attendance queries
        if hasattr(queryset.model, 'staff'):
            queryset = queryset.select_related('staff', 'hotel')
        
        # Add period-related optimization if available
        if hasattr(queryset.model, 'period'):
            queryset = queryset.select_related('period')
            
        return queryset