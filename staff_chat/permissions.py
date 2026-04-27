"""
Custom permissions for Staff Chat
"""
from rest_framework import permissions


class IsStaffMember(permissions.BasePermission):
    """
    Permission check: User must have a staff profile
    """
    message = "You must be a staff member to access this resource."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'staff_profile')
        )


class IsConversationParticipant(permissions.BasePermission):
    """
    Permission check: User must be a participant in the conversation
    """
    message = "You must be a participant in this conversation."

    def has_object_permission(self, request, view, obj):
        # obj is a StaffConversation
        try:
            staff = request.user.staff_profile
            return obj.participants.filter(id=staff.id).exists()
        except AttributeError:
            return False


class IsSameHotel(permissions.BasePermission):
    """
    Permission check: User must belong to the same hotel
    """
    message = "You can only access resources from your hotel."

    def has_permission(self, request, view):
        hotel_slug = view.kwargs.get('hotel_slug')
        if not hotel_slug:
            return False
        
        try:
            staff = request.user.staff_profile
            return staff.hotel.slug == hotel_slug
        except AttributeError:
            return False

    def has_object_permission(self, request, view, obj):
        # obj could be Conversation or Message
        try:
            staff = request.user.staff_profile
            
            # Handle different object types
            if hasattr(obj, 'hotel'):
                # Object is a Conversation
                return obj.hotel.id == staff.hotel.id
            elif hasattr(obj, 'conversation'):
                # Object is a Message or Attachment
                return obj.conversation.hotel.id == staff.hotel.id
            
            return False
        except AttributeError:
            return False
