"""
Canonical permissions system for HotelMate staff navigation.

This module provides the single source of truth for staff navigation permissions,
ensuring consistent payload structure across all authentication endpoints.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from functools import wraps
from rest_framework.permissions import BasePermission

from staff.models import Staff, NavigationItem
from staff.serializers import NavigationItemSerializer

User = get_user_model()


def resolve_staff_navigation(user: User) -> dict:
    """
    Single source of truth for staff navigation permissions.
    Returns consistent payload for all auth endpoints.
    
    Returns:
        dict: Canonical permissions payload with keys:
            - is_staff: bool
            - is_superuser: bool  
            - hotel_slug: str | None
            - access_level: str | None
            - allowed_navs: list[str] (slugs only)
            - navigation_items: list[dict] (full menu structure)
    """
    # Default empty payload - contract guarantees these keys always exist
    base_payload = {
        'is_staff': False,
        'is_superuser': bool(user.is_superuser if user.is_authenticated else False),
        'hotel_slug': None,
        'access_level': None,
        'allowed_navs': [],
        'navigation_items': []
    }
    
    if not user.is_authenticated:
        return base_payload
        
    # Check if user has staff profile
    try:
        staff = user.staff_profile
    except (AttributeError, Staff.DoesNotExist):
        return base_payload
    
    # Update payload with staff info
    base_payload.update({
        'is_staff': True,
        'hotel_slug': staff.hotel.slug,
        'access_level': staff.access_level
    })
    
    # Get hotel navigation items (active only, hotel-scoped)
    hotel_nav_items = NavigationItem.objects.filter(
        hotel=staff.hotel,
        is_active=True
    ).select_related('hotel').order_by('display_order', 'name')
    
    # Determine allowed navigation items based on superuser status
    if user.is_superuser:
        # Superusers get ALL active nav items for their hotel
        allowed_nav_items = hotel_nav_items
    else:
        # Regular staff get only assigned M2M items (filtered to active + same hotel)
        allowed_nav_items = staff.allowed_navigation_items.filter(
            hotel=staff.hotel,
            is_active=True
        ).select_related('hotel').order_by('display_order', 'name')
    
    # Build final payload
    base_payload.update({
        'allowed_navs': list(allowed_nav_items.values_list('slug', flat=True)),
        'navigation_items': NavigationItemSerializer(allowed_nav_items, many=True).data
    })
    
    return base_payload


class HasNavPermission(BasePermission):
    """
    Permission class for checking navigation-based permissions.
    Usage: permission_classes = [IsAuthenticated, HasNavPermission("stock_tracker")]
    """
    
    def __init__(self, required_slug: str):
        self.required_slug = required_slug
        super().__init__()
    
    def has_permission(self, request, view):
        """Check if user has permission for the required navigation slug."""
        user = request.user
        
        # Superuser bypass
        if user.is_superuser:
            return True
            
        # Get canonical permissions
        permissions = resolve_staff_navigation(user)
        
        # Check if user has required navigation permission
        return self.required_slug in permissions.get('allowed_navs', [])


def requires_nav_permission(slug: str):
    """
    Decorator for view methods that require specific navigation permissions.
    Usage: @requires_nav_permission("stock_tracker")
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Superuser bypass
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            # Get canonical permissions
            permissions = resolve_staff_navigation(user)
            
            # Check if user has required navigation permission
            if slug not in permissions.get('allowed_navs', []):
                raise PermissionDenied(f"Navigation permission required: {slug}")
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# Factory function for creating HasNavPermission instances
def create_nav_permission(slug: str):
    """
    Factory function to create HasNavPermission instances.
    Usage: permission_classes = [IsAuthenticated, create_nav_permission("stock_tracker")]
    """
    class NavPermission(HasNavPermission):
        def __init__(self):
            super().__init__(slug)
    return NavPermission