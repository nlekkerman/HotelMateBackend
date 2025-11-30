# Face Management Views - Phase 1 Implementation
# This contains the face lifecycle control endpoints

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from attendance.models import FaceAuditLog, StaffFace
from hotel.models import Hotel


def create_face_audit_log(hotel, staff, action, performed_by=None, reason=None, 
                         consent_given=True, request=None):
    """Helper function to create face audit log entries"""
    client_ip = None
    user_agent = ""
    
    if request:
        client_ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length
    
    return FaceAuditLog.objects.create(
        hotel=hotel,
        staff=staff,
        action=action,
        performed_by=performed_by,
        reason=reason,
        consent_given=consent_given,
        client_ip=client_ip,
        user_agent=user_agent
    )


class FaceManagementMixin:
    """Mixin to add face lifecycle management endpoints to ClockLogViewSet"""
    
    @action(detail=False, methods=['delete'], url_path='revoke-face/(?P<staff_id>[^/.]+)')
    def revoke_face(self, request, hotel_slug=None, staff_id=None):
        """Revoke face data for a specific staff member (manager action)"""
        from staff.models import Staff
        
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        target_staff = get_object_or_404(Staff, id=staff_id, hotel=hotel)
        
        # Get requesting staff
        requesting_staff = getattr(request.user, "staff_profile", None)
        if not requesting_staff or requesting_staff.hotel != hotel:
            return Response(
                {"error": "You don't have access to this hotel."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check permissions - must be manager/admin level
        if requesting_staff.access_level == 'regular_staff' and requesting_staff != target_staff:
            return Response(
                {"error": "You don't have permission to revoke face data for other staff members."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if staff has face data
        face_data = StaffFace.objects.filter(staff=target_staff).first()
        if not face_data:
            return Response(
                {"error": "Staff member has no registered face data."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Remove face data
        face_data.delete()
        target_staff.has_registered_face = False
        target_staff.save(update_fields=["has_registered_face"])
        
        # Create audit log
        create_face_audit_log(
            hotel=hotel,
            staff=target_staff,
            action='REVOKED',
            performed_by=requesting_staff,
            reason=request.data.get('reason', ''),
            request=request
        )
        
        return Response({
            "message": f"Face data revoked for {target_staff.first_name} {target_staff.last_name}.",
            "staff_id": target_staff.id,
            "has_registered_face": False
        })

    @action(detail=False, methods=['get'], url_path='face-audit-logs')
    def face_audit_logs(self, request, hotel_slug=None):
        """Get face audit logs for the hotel"""
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Check permissions
        requesting_staff = getattr(request.user, "staff_profile", None)
        if not requesting_staff or requesting_staff.hotel != hotel:
            return Response(
                {"error": "You don't have access to this hotel."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only managers/admins can view audit logs
        if requesting_staff.access_level == 'regular_staff':
            return Response(
                {"error": "You don't have permission to view face audit logs."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get audit logs
        logs = FaceAuditLog.objects.filter(hotel=hotel).select_related(
            'staff', 'performed_by'
        )
        
        # Optional filtering
        staff_id = request.query_params.get('staff_id')
        if staff_id:
            logs = logs.filter(staff_id=staff_id)
            
        action = request.query_params.get('action')
        if action:
            logs = logs.filter(action=action)
        
        # Import serializer from temporary file
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        try:
            from face_audit_serializer import FaceAuditLogSerializer
            serializer = FaceAuditLogSerializer(logs[:50], many=True)  # Limit to 50 results
            return Response(serializer.data)
        except ImportError:
            # Fallback to basic dict response
            logs_data = []
            for log in logs[:50]:
                logs_data.append({
                    'id': log.id,
                    'hotel': log.hotel.slug,
                    'staff': log.staff.id,
                    'staff_name': f"{log.staff.first_name} {log.staff.last_name}",
                    'action': log.action,
                    'performed_by': log.performed_by.id if log.performed_by else None,
                    'performed_by_name': f"{log.performed_by.first_name} {log.performed_by.last_name}" if log.performed_by else "System",
                    'reason': log.reason,
                    'consent_given': log.consent_given,
                    'created_at': log.created_at
                })
            return Response(logs_data)


def update_register_face_with_audit(view_instance, request, hotel_slug=None):
    """Updated register_face method with audit logging"""
    descriptor = request.data.get("descriptor")
    if not isinstance(descriptor, list) or len(descriptor) != 128:
        return Response({"error": "A 128‑length descriptor array is required."},
                        status=status.HTTP_400_BAD_REQUEST)

    hotel_slug = view_instance.kwargs.get('hotel_slug')
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    staff = getattr(request.user, "staff_profile", None)
    if not staff:
        return Response({"error": "User has no linked staff profile."},
                        status=status.HTTP_400_BAD_REQUEST)
                        
    # Validate staff belongs to the hotel
    if staff.hotel.slug != hotel_slug:
        return Response({"error": "You don't have access to this hotel."},
                        status=status.HTTP_403_FORBIDDEN)

    # Check if staff already had face data (for audit logging)
    had_existing_face = StaffFace.objects.filter(staff=staff).exists()
    
    # Remove any existing face data
    StaffFace.objects.filter(staff=staff).delete()
    
    # Create new face data
    StaffFace.objects.create(hotel=hotel, staff=staff, encoding=descriptor)
    staff.has_registered_face = True
    staff.save(update_fields=["has_registered_face"])
    
    # Create audit log
    action = 'RE_REGISTERED' if had_existing_face else 'REGISTERED'
    create_face_audit_log(
        hotel=hotel,
        staff=staff,
        action=action,
        performed_by=staff,  # Self-registration
        consent_given=request.data.get('consent_given', True),
        request=request
    )

    return Response({"message": "Face descriptor registered."})