"""
Enhanced face management views with comprehensive lifecycle control,
safety features, and Cloudinary integration.
"""
import base64
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from hotel.models import Hotel
from staff.models import Staff
from .models import StaffFace, ClockLog, FaceAuditLog
from .serializers import (
    FaceRegistrationSerializer, FaceClockInSerializer, StaffFaceEnhancedSerializer,
    FaceRevocationSerializer, FaceAuditLogSerializer, ClockLogSerializer
)
from .utils import (
    find_best_face_match, generate_face_registration_response,
    create_face_audit_log, check_face_attendance_permissions
)
from common.mixins import AttendanceHotelScopedMixin


class FaceManagementViewSet(AttendanceHotelScopedMixin, viewsets.GenericViewSet):
    """
    Comprehensive face management endpoints with lifecycle control.
    
    Provides endpoints for:
    - Face registration with Cloudinary storage
    - Face revocation with audit trail
    - Face listing with privacy controls
    - Audit log access for compliance
    """
    permission_classes = [IsAuthenticated]
    
    def get_hotel(self):
        """Get hotel from URL parameter."""
        hotel_slug = self.kwargs.get('hotel_slug')
        return get_object_or_404(Hotel, slug=hotel_slug)
    
    def check_staff_permissions(self, request, hotel):
        """Validate staff permissions for face operations."""
        staff = getattr(request.user, 'staff_profile', None)
        if not staff:
            return False, "User does not have staff profile"
        
        # Use utility function for comprehensive permission check
        return check_face_attendance_permissions(staff, hotel)
    
    @action(detail=False, methods=['post'], url_path='register-face')
    def register_face(self, request, hotel_slug=None):
        """
        Register staff face with image and encoding data.
        
        POST /api/staff/hotel/{hotel_slug}/attendance/face-management/register-face/
        
        Body:
        {
            "image": "data:image/jpeg;base64,/9j/4AAQ...",
            "encoding": [0.123, -0.456, ...], // 128 floats
            "staff_id": 123, // optional, defaults to requesting user
            "consent_given": true
        }
        """
        hotel = self.get_hotel()
        
        # Check permissions
        has_permission, error_message = self.check_staff_permissions(request, hotel)
        if not has_permission:
            return Response(
                {'error': error_message}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize and validate request data
        serializer = FaceRegistrationSerializer(
            data=request.data,
            context={'request': request, 'hotel': hotel}
        )
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create face registration
            staff_face = serializer.save()
            
            # Generate response using utility function
            response_data = generate_face_registration_response(staff_face)
            
            return Response({
                'message': 'Face registered successfully',
                'face_data': response_data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Face registration failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='revoke-face')
    def revoke_face(self, request, hotel_slug=None):
        """
        Revoke staff face data with audit trail.
        
        POST /api/staff/hotel/{hotel_slug}/attendance/face-management/revoke-face/
        
        Body:
        {
            "staff_id": 123, // optional, defaults to requesting user
            "reason": "Privacy request" // optional
        }
        """
        hotel = self.get_hotel()
        
        # Check permissions
        has_permission, error_message = self.check_staff_permissions(request, hotel)
        if not has_permission:
            return Response(
                {'error': error_message}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize and validate request data
        serializer = FaceRevocationSerializer(
            data=request.data,
            context={'request': request, 'hotel': hotel}
        )
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Perform revocation
            revoked_face = serializer.save()
            
            return Response({
                'message': 'Face data revoked successfully',
                'staff_id': revoked_face.staff.id,
                'staff_name': revoked_face.staff.user.get_full_name(),
                'revoked_at': now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Face revocation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='list-faces')
    def list_faces(self, request, hotel_slug=None):
        """
        List registered faces for the hotel (privacy-aware).
        
        GET /api/staff/hotel/{hotel_slug}/attendance/face-management/list-faces/
        
        Query params:
        - active_only: true/false (default true)
        - staff_id: filter by specific staff
        """
        hotel = self.get_hotel()
        
        # Check permissions
        has_permission, error_message = self.check_staff_permissions(request, hotel)
        if not has_permission:
            return Response(
                {'error': error_message}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Build queryset
        queryset = StaffFace.objects.filter(hotel=hotel).select_related('staff', 'registered_by')
        
        # Apply filters
        active_only = request.GET.get('active_only', 'true').lower() == 'true'
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        staff_id = request.GET.get('staff_id')
        if staff_id:
            try:
                queryset = queryset.filter(staff_id=int(staff_id))
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid staff_id parameter'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Serialize with privacy protections (excludes encoding data)
        serializer = StaffFaceEnhancedSerializer(queryset, many=True)
        
        return Response({
            'count': queryset.count(),
            'faces': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='face-clock-in')
    def face_clock_in(self, request, hotel_slug=None):
        """
        Enhanced face clock-in with safety monitoring and improved matching.
        
        POST /api/staff/hotel/{hotel_slug}/attendance/face-management/face-clock-in/
        
        Body:
        {
            "image": "data:image/jpeg;base64,/9j/4AAQ...",
            "encoding": [0.123, -0.456, ...], // 128 floats
            "location_note": "Front Desk", // optional
            "force_action": "clock_in" // optional: clock_in/clock_out
        }
        """
        hotel = self.get_hotel()
        
        # Check permissions
        has_permission, error_message = self.check_staff_permissions(request, hotel)
        if not has_permission:
            return Response(
                {'error': error_message}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Serialize and validate request data
        serializer = FaceClockInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        probe_encoding = validated_data['encoding']
        
        try:
            # Find matching face using enhanced matching algorithm
            staff_faces_qs = StaffFace.objects.filter(
                hotel=hotel,
                is_active=True
            ).select_related('staff')
            
            matched_staff, confidence_score = find_best_face_match(
                probe_encoding, 
                staff_faces_qs, 
                threshold=0.6  # Could be made configurable via hotel settings
            )
            
            if not matched_staff:
                return Response({
                    'error': 'Face not recognized',
                    'confidence_score': confidence_score,
                    'message': 'No matching face found or confidence too low'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check for existing open clock log
            today = now().date()
            existing_log = ClockLog.objects.filter(
                hotel=hotel,
                staff=matched_staff,
                time_in__date=today,
                time_out__isnull=True
            ).first()
            
            if existing_log:
                # Clock out
                existing_log.time_out = now()
                existing_log.save()
                
                # Serialize with enhanced features
                serializer = ClockLogSerializer(existing_log)
                
                return Response({
                    'action': 'clock_out',
                    'message': f'Clocked out successfully',
                    'confidence_score': confidence_score,
                    'clock_log': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                # Clock in - create new log
                new_log = ClockLog.objects.create(
                    hotel=hotel,
                    staff=matched_staff,
                    verified_by_face=True,
                    location_note=validated_data.get('location_note', ''),
                    time_in=now()
                )
                
                # TODO: Add roster shift matching logic here
                # TODO: Add unrostered detection logic here
                
                # Serialize with enhanced features
                serializer = ClockLogSerializer(new_log)
                
                return Response({
                    'action': 'clock_in',
                    'message': f'Clocked in successfully',
                    'confidence_score': confidence_score,
                    'clock_log': serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': f'Face clock-in failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='audit-logs')
    def audit_logs(self, request, hotel_slug=None):
        """
        Get face audit logs for compliance tracking.
        
        GET /api/staff/hotel/{hotel_slug}/attendance/face-management/audit-logs/
        
        Query params:
        - staff_id: filter by staff
        - action: filter by action type (REGISTERED/REVOKED/RE_REGISTERED)
        - start_date: filter from date (YYYY-MM-DD)
        - end_date: filter to date (YYYY-MM-DD)
        """
        hotel = self.get_hotel()
        
        # Check permissions (might require manager role for audit access)
        has_permission, error_message = self.check_staff_permissions(request, hotel)
        if not has_permission:
            return Response(
                {'error': error_message}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Build queryset
        queryset = FaceAuditLog.objects.filter(hotel=hotel).select_related(
            'staff', 'performed_by'
        ).order_by('-created_at')
        
        # Apply filters
        staff_id = request.GET.get('staff_id')
        if staff_id:
            try:
                queryset = queryset.filter(staff_id=int(staff_id))
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid staff_id parameter'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        action = request.GET.get('action')
        if action and action in ['REGISTERED', 'REVOKED', 'RE_REGISTERED']:
            queryset = queryset.filter(action=action)
        
        start_date = request.GET.get('start_date')
        if start_date:
            try:
                from datetime import datetime
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=start_dt)
            except ValueError:
                return Response(
                    {'error': 'Invalid start_date format (use YYYY-MM-DD)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        end_date = request.GET.get('end_date')
        if end_date:
            try:
                from datetime import datetime
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=end_dt)
            except ValueError:
                return Response(
                    {'error': 'Invalid end_date format (use YYYY-MM-DD)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Paginate results
        page_size = int(request.GET.get('page_size', 50))
        page_size = min(page_size, 200)  # Max 200 records per page
        
        page = int(request.GET.get('page', 1))
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        total_count = queryset.count()
        page_queryset = queryset[start_index:end_index]
        
        # Serialize
        serializer = FaceAuditLogSerializer(page_queryset, many=True)
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'has_next': end_index < total_count,
            'has_previous': page > 1,
            'results': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='face-status')
    def face_status(self, request, hotel_slug=None):
        """
        Get current face registration status for requesting user.
        
        GET /api/staff/hotel/{hotel_slug}/attendance/face-management/face-status/
        """
        hotel = self.get_hotel()
        
        # Check permissions
        has_permission, error_message = self.check_staff_permissions(request, hotel)
        if not has_permission:
            return Response(
                {'error': error_message}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        staff = request.user.staff_profile
        
        try:
            face_data = StaffFace.objects.get(staff=staff, is_active=True)
            serializer = StaffFaceEnhancedSerializer(face_data)
            
            return Response({
                'has_registered_face': True,
                'face_data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except StaffFace.DoesNotExist:
            return Response({
                'has_registered_face': False,
                'face_data': None
            }, status=status.HTTP_200_OK)