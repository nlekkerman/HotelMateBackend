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


class IsMessageSender(permissions.BasePermission):
    """
    Permission check: User must be the sender of the message
    Used for edit/delete operations
    """
    message = "You can only modify your own messages."

    def has_object_permission(self, request, view, obj):
        # obj is a StaffChatMessage
        try:
            staff = request.user.staff_profile
            return obj.sender.id == staff.id
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


class CanManageConversation(permissions.BasePermission):
    """
    Permission check: User can manage conversation
    (creator or manager role)
    """
    message = "You don't have permission to manage this conversation."

    def has_object_permission(self, request, view, obj):
        # obj is a StaffConversation
        try:
            staff = request.user.staff_profile
            
            # Creator can always manage
            if obj.created_by and obj.created_by.id == staff.id:
                return True
            
            # Managers and admins can manage any conversation
            if staff.role and staff.role.slug in ['manager', 'admin']:
                return True
            
            return False
        except AttributeError:
            return False


class CanDeleteMessage(permissions.BasePermission):
    """
    Permission check: User can delete message
    (own messages or manager role for hard delete)
    """
    message = "You don't have permission to delete this message."

    def has_object_permission(self, request, view, obj):
        # obj is a StaffChatMessage
        try:
            staff = request.user.staff_profile
            
            # Hard delete check
            hard_delete = request.query_params.get('hard_delete') == 'true'
            
            if hard_delete:
                # Only managers/admins can hard delete
                if staff.role and staff.role.slug in ['manager', 'admin']:
                    return True
                # Or if it's their own message
                return obj.sender.id == staff.id
            else:
                # Soft delete - anyone can delete their own messages
                return obj.sender.id == staff.id
        except AttributeError:
            return False
