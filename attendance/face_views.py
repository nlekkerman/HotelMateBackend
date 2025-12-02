"""
Enhanced face management views with comprehensive lifecycle control,
safety features, and Cloudinary integration.
"""
import base64
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
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
    create_face_audit_log, check_face_attendance_permissions,
    send_unrostered_request_notification
)
from staff.pusher_utils import trigger_clock_status_update
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
            "confirmation_mode": false // optional: true for two-step confirmation
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
                # For clock-out: Return two-step confirmation options
                session_duration = (now() - existing_log.time_in).total_seconds() / 3600
                
                # Get staff image
                staff_image = None
                try:
                    staff_face = StaffFace.objects.get(staff=matched_staff, is_active=True)
                    staff_image = staff_face.get_image_url()
                except StaffFace.DoesNotExist:
                    pass
                
                # Calculate break time
                current_break_time = 0
                if existing_log.is_on_break and existing_log.break_start:
                    current_break_time = (now() - existing_log.break_start).total_seconds() / 60  # minutes
                
                # Use kiosk mode from the saved clock log
                kiosk_action = 'show_options_then_refresh' if existing_log.is_kiosk_mode else 'show_options_stay_logged_in'
                
                return Response({
                    'action': 'clock_out_options',
                    'message': f'{matched_staff.first_name} {matched_staff.last_name} - Choose action',
                    'staff': {
                        'id': matched_staff.id,
                        'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                        'department': matched_staff.department.name if matched_staff.department else 'No Department',
                        'image': staff_image
                    },
                    'session_info': {
                        'duration_hours': round(session_duration, 2),
                        'clock_in_time': existing_log.time_in.isoformat(),
                        'is_on_break': existing_log.is_on_break,
                        'current_break_minutes': round(current_break_time, 0) if existing_log.is_on_break else 0,
                        'total_break_minutes': existing_log.total_break_minutes
                    },
                    'kiosk_action': kiosk_action,
                    'available_actions': [
                        {
                            'action': 'clock_out',
                            'label': 'Clock Out',
                            'description': f'End shift ({round(session_duration, 1)}h worked)',
                            'endpoint': f'/api/staff/hotel/{hotel.slug}/attendance/face-management/confirm-clock-out/',
                            'primary': True
                        },
                        {
                            'action': 'start_break',
                            'label': 'Start Break',
                            'description': 'Take a break',
                            'endpoint': f'/api/staff/hotel/{hotel.slug}/attendance/face-management/toggle-break/',
                            'primary': False
                        }
                    ] if not existing_log.is_on_break else [
                        {
                            'action': 'resume_shift',
                            'label': 'Resume Shift',
                            'description': f'End break and resume working ({round(current_break_time, 0)}min break)',
                            'endpoint': f'/api/staff/hotel/{hotel.slug}/attendance/face-management/toggle-break/',
                            'primary': True
                        }
                    ],
                    'confidence_score': confidence_score
                }, status=status.HTTP_200_OK)
            else:
                # Clock in - create new log with roster checking
                from .views import find_matching_shift_for_datetime
                
                current_dt = now()
                matching_shift = find_matching_shift_for_datetime(hotel, matched_staff, current_dt)
                
                if matching_shift:
                    # Normal rostered clock-in (ONE STEP - AUTOMATIC)
                    new_log = ClockLog.objects.create(
                        hotel=hotel,
                        staff=matched_staff,
                        verified_by_face=True,
                        location_note=validated_data.get('location_note', ''),
                        time_in=current_dt,
                        roster_shift=matching_shift,
                        is_unrostered=False,
                        is_approved=True,
                        is_on_break=False,
                        is_kiosk_mode=validated_data.get('is_kiosk_mode', False)
                    )
                    
                    # Update staff status (both new and legacy fields)
                    matched_staff.duty_status = 'on_duty'
                    matched_staff.is_on_duty = True
                    matched_staff.save(update_fields=['duty_status', 'is_on_duty'])
                    
                    # Trigger Pusher event for real-time status update
                    trigger_clock_status_update(hotel.slug, matched_staff, 'clock_in')
                    
                    # Get staff image for success message
                    staff_image = None
                    try:
                        staff_face = StaffFace.objects.get(staff=matched_staff, is_active=True)
                        staff_image = staff_face.get_image_url()
                    except StaffFace.DoesNotExist:
                        pass
                    
                    # Serialize with enhanced features
                    serializer = ClockLogSerializer(new_log)
                    
                    # Determine frontend action based on kiosk mode
                    kiosk_action = 'refresh_for_next_person' if new_log.is_kiosk_mode else 'stay_logged_in'
                    
                    return Response({
                        'action': 'clock_in_success',
                        'message': f'{matched_staff.first_name} {matched_staff.last_name} clocked in successfully!',
                        'staff': {
                            'id': matched_staff.id,
                            'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                            'department': matched_staff.department.name if matched_staff.department else 'No Department',
                            'image': staff_image
                        },
                        'is_rostered': True,
                        'shift_info': {
                            'id': matching_shift.id,
                            'date': matching_shift.shift_date.isoformat(),
                            'start_time': matching_shift.shift_start.strftime('%H:%M'),
                            'end_time': matching_shift.shift_end.strftime('%H:%M'),
                            'department': matching_shift.department.name if matching_shift.department else None
                        } if matching_shift else None,
                        'confidence_score': confidence_score,
                        'kiosk_action': kiosk_action,
                        'clock_log': serializer.data
                    }, status=status.HTTP_201_CREATED)
                else:
                    # Unrostered staff - return confirmation prompt
                    return Response({
                        'action': 'unrostered_detected',
                        'message': f'No scheduled shift found for {matched_staff.first_name} {matched_staff.last_name}. Confirm to clock in anyway.',
                        'staff': {
                            'id': matched_staff.id,
                            'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                            'department': matched_staff.department.name if matched_staff.department else 'No Department'
                        },
                        'requires_confirmation': True,
                        'confidence_score': confidence_score,
                        'confirmation_endpoint': f'/staff/hotel/{hotel.slug}/attendance/face-management/force-clock-in/'
                    }, status=status.HTTP_200_OK)
                
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
    
    @action(detail=False, methods=['post'], url_path='detect-staff')
    def detect_staff_with_status(self, request, hotel_slug=None):
        """
        Detect staff from face encoding and return current clock status with action options.
        
        POST /api/staff/hotel/{hotel_slug}/attendance/face-management/detect-staff/
        
        Body:
        {
            "encoding": [128-dimensional array]
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
        
        # Validate encoding
        encoding = request.data.get('encoding')
        if not isinstance(encoding, list) or len(encoding) != 128:
            return Response({
                'error': 'A 128-length descriptor array is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find matching face
            staff_faces_qs = StaffFace.objects.filter(
                hotel=hotel,
                is_active=True
            ).select_related('staff')
            
            matched_staff, confidence_score = find_best_face_match(
                encoding, 
                staff_faces_qs, 
                threshold=0.6
            )
            
            if not matched_staff:
                return Response({
                    'error': 'Face not recognized',
                    'confidence_score': confidence_score,
                    'message': 'No matching face found or confidence too low'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check current clock status
            today = now().date()
            existing_log = ClockLog.objects.filter(
                hotel=hotel,
                staff=matched_staff,
                time_in__date=today,
                time_out__isnull=True
            ).first()
            
            # Calculate session duration if clocked in
            session_duration_hours = None
            if existing_log:
                duration = now() - existing_log.time_in
                session_duration_hours = round(duration.total_seconds() / 3600, 2)
            
            # Determine available actions
            available_actions = []
            if existing_log:
                available_actions.append({
                    'action': 'clock_out',
                    'label': 'Clock Out',
                    'description': f'End shift (worked {session_duration_hours}h)',
                    'endpoint': f'/api/staff/hotel/{hotel.slug}/attendance/face-management/face-clock-in/',
                    'urgent': session_duration_hours and session_duration_hours >= 10
                })
            else:
                available_actions.append({
                    'action': 'clock_in',
                    'label': 'Clock In',
                    'description': 'Start new shift',
                    'endpoint': f'/api/staff/hotel/{hotel.slug}/attendance/face-management/face-clock-in/'
                })
            
            return Response({
                'recognized': True,
                'staff': {
                    'id': matched_staff.id,
                    'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                    'department': matched_staff.department.name if matched_staff.department else 'No Department'
                },
                'current_status': {
                    'is_clocked_in': bool(existing_log),
                    'session_duration_hours': session_duration_hours,
                    'clock_in_time': existing_log.time_in.isoformat() if existing_log else None
                },
                'confidence_score': confidence_score,
                'available_actions': available_actions,
                'auto_action_available': True  # Can use one-step mode
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Face detection failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

    @action(detail=False, methods=['post'], url_path='force-clock-in')
    def force_clock_in_unrostered(self, request, hotel_slug=None):
        """
        Force clock-in for unrostered staff after confirmation.
        
        POST /api/staff/hotel/{hotel_slug}/attendance/face-management/force-clock-in/
        
        Body:
        {
            "encoding": [128-dimensional array],
            "reason": "Emergency coverage needed",
            "location_note": "Front Desk" (optional)
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
        encoding = request.data.get('encoding')
        reason = request.data.get('reason', 'Unrostered clock-in confirmed by staff')
        
        if not isinstance(encoding, list) or len(encoding) != 128:
            return Response({
                'error': 'A 128-length descriptor array is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find matching face
            staff_faces_qs = StaffFace.objects.filter(
                hotel=hotel,
                is_active=True
            ).select_related('staff')
            
            matched_staff, confidence_score = find_best_face_match(
                encoding, 
                staff_faces_qs, 
                threshold=0.6
            )
            
            if not matched_staff:
                return Response({
                    'error': 'Face not recognized',
                    'confidence_score': confidence_score,
                    'message': 'No matching face found or confidence too low'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if already clocked in
            today = now().date()
            existing_log = ClockLog.objects.filter(
                hotel=hotel,
                staff=matched_staff,
                time_in__date=today,
                time_out__isnull=True
            ).first()
            
            if existing_log:
                return Response({
                    'error': 'Staff already clocked in',
                    'message': f'{matched_staff.first_name} is already clocked in since {existing_log.time_in}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create unrostered clock log
            current_dt = now()
            new_log = ClockLog.objects.create(
                hotel=hotel,
                staff=matched_staff,
                verified_by_face=True,
                location_note=request.data.get('location_note', ''),
                time_in=current_dt,
                roster_shift=None,
                is_unrostered=True,
                is_approved=False,  # Requires manager approval
                is_rejected=False
            )
            
            # Update staff status
            # Update staff status back to on_duty (end break)
            matched_staff.duty_status = 'on_duty'
            matched_staff.save(update_fields=['duty_status'])
            
            # Create audit log
            create_face_audit_log(
                hotel=hotel,
                staff=matched_staff,
                action='FORCED_CLOCK_IN',
                performed_by=matched_staff,
                reason=reason,
                request=request
            )
            
            # Notify managers about unrostered clock-in
            from .utils import send_unrostered_request_notification
            send_unrostered_request_notification(hotel, new_log)
            
            # Serialize response
            serializer = ClockLogSerializer(new_log)
            
            return Response({
                'action': 'unrostered_clock_in',
                'message': f'{matched_staff.first_name} {matched_staff.last_name} clocked in (unrostered - requires approval)',
                'staff': {
                    'id': matched_staff.id,
                    'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                    'department': matched_staff.department.name if matched_staff.department else 'No Department'
                },
                'is_rostered': False,
                'requires_approval': True,
                'confidence_score': confidence_score,
                'clock_log': serializer.data
            }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'error': f'Force clock-in failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='confirm-clock-out')
    def confirm_clock_out(self, request, hotel_slug=None):
        """
        Confirm clock-out action after two-step verification.
        
        POST /api/staff/hotel/{hotel_slug}/attendance/face-management/confirm-clock-out/
        
        Body:
        {
            "encoding": [128-dimensional array]
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
        
        # Validate encoding
        encoding = request.data.get('encoding')
        if not isinstance(encoding, list) or len(encoding) != 128:
            return Response({
                'error': 'A 128-length descriptor array is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find matching face
            staff_faces_qs = StaffFace.objects.filter(
                hotel=hotel,
                is_active=True
            ).select_related('staff')
            
            matched_staff, confidence_score = find_best_face_match(
                encoding, 
                staff_faces_qs, 
                threshold=0.6
            )
            
            if not matched_staff:
                return Response({
                    'error': 'Face not recognized',
                    'confidence_score': confidence_score
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Find existing open log
            today = now().date()
            existing_log = ClockLog.objects.filter(
                hotel=hotel,
                staff=matched_staff,
                time_in__date=today,
                time_out__isnull=True
            ).first()
            
            if not existing_log:
                return Response({
                    'error': 'No active clock-in found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # End break if currently on break
            if existing_log.is_on_break:
                existing_log.is_on_break = False
                if existing_log.break_start:
                    break_duration = (now() - existing_log.break_start).total_seconds() / 60
                    existing_log.total_break_minutes += int(break_duration)
                existing_log.break_end = now()
            
            # Clock out
            existing_log.time_out = now()
            existing_log.save()
            
            # Update staff status
            matched_staff.duty_status = 'off_duty'
            matched_staff.save(update_fields=['duty_status'])
            
            # Trigger Pusher event for real-time status update
            trigger_clock_status_update(hotel.slug, matched_staff, 'clock_out')
            
            # Calculate session duration
            session_duration = (existing_log.time_out - existing_log.time_in).total_seconds() / 3600
            
            # Get staff image
            staff_image = None
            try:
                staff_face = StaffFace.objects.get(staff=matched_staff, is_active=True)
                staff_image = staff_face.get_image_url()
            except StaffFace.DoesNotExist:
                pass
            
            # Serialize response
            serializer = ClockLogSerializer(existing_log)
            
            # Use kiosk mode from saved log to determine frontend action
            kiosk_action = 'refresh_for_next_person' if existing_log.is_kiosk_mode else 'stay_logged_in'
            
            return Response({
                'action': 'clock_out_success',
                'message': f'{matched_staff.first_name} {matched_staff.last_name} clocked out successfully!',
                'staff': {
                    'id': matched_staff.id,
                    'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                    'department': matched_staff.department.name if matched_staff.department else 'No Department',
                    'image': staff_image
                },
                'session_summary': {
                    'duration_hours': round(session_duration, 2),
                    'total_break_minutes': existing_log.total_break_minutes,
                    'clock_in_time': existing_log.time_in.isoformat(),
                    'clock_out_time': existing_log.time_out.isoformat()
                },
                'confidence_score': confidence_score,
                'kiosk_action': kiosk_action,
                'clock_log': serializer.data
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': f'Clock-out failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='toggle-break')
    def toggle_break(self, request, hotel_slug=None):
        """
        Start or end break for currently clocked-in staff.
        
        POST /api/staff/hotel/{hotel_slug}/attendance/face-management/toggle-break/
        
        Body:
        {
            "encoding": [128-dimensional array]
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
        
        # Validate encoding
        encoding = request.data.get('encoding')
        if not isinstance(encoding, list) or len(encoding) != 128:
            return Response({
                'error': 'A 128-length descriptor array is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find matching face
            staff_faces_qs = StaffFace.objects.filter(
                hotel=hotel,
                is_active=True
            ).select_related('staff')
            
            matched_staff, confidence_score = find_best_face_match(
                encoding, 
                staff_faces_qs, 
                threshold=0.6
            )
            
            if not matched_staff:
                return Response({
                    'error': 'Face not recognized',
                    'confidence_score': confidence_score
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Find existing open log
            today = now().date()
            existing_log = ClockLog.objects.filter(
                hotel=hotel,
                staff=matched_staff,
                time_in__date=today,
                time_out__isnull=True
            ).first()
            
            if not existing_log:
                return Response({
                    'error': 'No active clock-in found'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get staff image
            staff_image = None
            try:
                staff_face = StaffFace.objects.get(staff=matched_staff, is_active=True)
                staff_image = staff_face.get_image_url()
            except StaffFace.DoesNotExist:
                pass
            
            if existing_log.is_on_break:
                # End break
                if existing_log.break_start:
                    break_duration = (now() - existing_log.break_start).total_seconds() / 60
                    existing_log.total_break_minutes += int(break_duration)
                
                existing_log.is_on_break = False
                existing_log.break_end = now()
                existing_log.save()
                
                # Update staff duty status back to on_duty
                matched_staff.duty_status = 'on_duty'
                matched_staff.save(update_fields=['duty_status'])
                
                # Trigger Pusher event for break end (staff back on duty)
                trigger_clock_status_update(hotel.slug, matched_staff, 'end_break')
                
                # Use kiosk mode from saved log
                kiosk_action = 'refresh_for_next_person' if existing_log.is_kiosk_mode else 'stay_logged_in'
                
                return Response({
                    'action': 'break_ended',
                    'message': f'{matched_staff.first_name} {matched_staff.last_name} break ended',
                    'staff': {
                        'id': matched_staff.id,
                        'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                        'department': matched_staff.department.name if matched_staff.department else 'No Department',
                        'image': staff_image
                    },
                    'break_info': {
                        'break_duration_minutes': int(break_duration) if existing_log.break_start else 0,
                        'total_break_minutes': existing_log.total_break_minutes,
                        'is_on_break': False
                    },
                    'confidence_score': confidence_score,
                    'kiosk_action': kiosk_action
                }, status=status.HTTP_200_OK)
            else:
                # Start break
                existing_log.is_on_break = True
                existing_log.break_start = now()
                existing_log.save()
                
                # Update staff duty status (keep is_on_duty=True since still working)
                matched_staff.duty_status = 'on_break'
                # Don't change is_on_duty - staff is still working, just on break
                matched_staff.save(update_fields=['duty_status'])
                
                # Trigger Pusher event for break start
                trigger_clock_status_update(hotel.slug, matched_staff, 'start_break')
                
                # Use kiosk mode from saved log
                kiosk_action = 'refresh_for_next_person' if existing_log.is_kiosk_mode else 'stay_logged_in'
                
                return Response({
                    'action': 'break_started',
                    'message': f'{matched_staff.first_name} {matched_staff.last_name} break started',
                    'staff': {
                        'id': matched_staff.id,
                        'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                        'department': matched_staff.department.name if matched_staff.department else 'No Department',
                        'image': staff_image
                    },
                    'break_info': {
                        'break_start_time': existing_log.break_start.isoformat(),
                        'total_break_minutes': existing_log.total_break_minutes,
                        'is_on_break': True
                    },
                    'confidence_score': confidence_score,
                    'kiosk_action': kiosk_action
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {'error': f'Break toggle failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def force_clock_in_unrostered(request, hotel_slug):
    """
    Independent endpoint for force clock-in of unrostered staff.
    
    POST /api/staff/hotel/{hotel_slug}/attendance/face-management/force-clock-in/
    
    Body:
    {
        "encoding": [128-dimensional array],
        "reason": "Emergency coverage needed",
        "location_note": "Front Desk" (optional)
    }
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    # Check permissions
    staff = getattr(request.user, 'staff_profile', None)
    if not staff:
        return Response(
            {'error': "User does not have staff profile"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    has_permission, error_message = check_face_attendance_permissions(staff, hotel)
    if not has_permission:
        return Response(
            {'error': error_message}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Serialize and validate request data
    encoding = request.data.get('encoding')
    reason = request.data.get('reason', 'Unrostered clock-in confirmed by staff')
    
    if not isinstance(encoding, list) or len(encoding) != 128:
        return Response({
            'error': 'A 128-length descriptor array is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find matching face
        staff_faces_qs = StaffFace.objects.filter(
            hotel=hotel,
            is_active=True
        ).select_related('staff')
        
        matched_staff, confidence_score = find_best_face_match(
            encoding, 
            staff_faces_qs, 
            threshold=0.6
        )
        
        if not matched_staff:
            return Response({
                'error': 'Face not recognized',
                'confidence_score': confidence_score,
                'message': 'No matching face found or confidence too low'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already clocked in
        today = now().date()
        existing_log = ClockLog.objects.filter(
            hotel=hotel,
            staff=matched_staff,
            time_in__date=today,
            time_out__isnull=True
        ).first()
        
        if existing_log:
            return Response({
                'error': 'Staff already clocked in',
                'message': f'{matched_staff.first_name} is already clocked in since {existing_log.time_in}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create unrostered clock log
        current_dt = now()
        new_log = ClockLog.objects.create(
            hotel=hotel,
            staff=matched_staff,
            verified_by_face=True,
            location_note=request.data.get('location_note', ''),
            time_in=current_dt,
            roster_shift=None,
            is_unrostered=True,
            is_approved=False,  # Requires manager approval
            is_rejected=False
        )
        
        # Update staff status (both new and legacy fields)
        matched_staff.duty_status = 'on_duty'
        matched_staff.is_on_duty = True
        matched_staff.save(update_fields=['duty_status', 'is_on_duty'])
        
        # Create audit log
        create_face_audit_log(
            hotel=hotel,
            staff=matched_staff,
            action='FORCED_CLOCK_IN',
            performed_by=matched_staff,
            reason=reason,
            request=request
        )
        
        # Notify managers about unrostered clock-in
        from .utils import send_unrostered_request_notification
        send_unrostered_request_notification(hotel, new_log)
        
        # Get staff image for response
        staff_image = None
        try:
            staff_face = StaffFace.objects.get(staff=matched_staff, is_active=True)
            staff_image = staff_face.get_image_url()
        except StaffFace.DoesNotExist:
            pass
        
        # Serialize response
        serializer = ClockLogSerializer(new_log)
        
        return Response({
            'action': 'unrostered_clock_in',
            'message': f'{matched_staff.first_name} {matched_staff.last_name} clocked in (unrostered - requires approval)',
            'staff': {
                'id': matched_staff.id,
                'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                'department': matched_staff.department.name if matched_staff.department else 'No Department',
                'image': staff_image
            },
            'is_rostered': False,
            'requires_approval': True,
            'confidence_score': confidence_score,
            'clock_log': serializer.data
        }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response(
            {'error': f'Force clock-in failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_clock_out_view(request, hotel_slug):
    """
    Independent endpoint for clock-out confirmation.
    
    POST /api/staff/hotel/{hotel_slug}/attendance/face-management/confirm-clock-out/
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    # Check permissions
    staff = getattr(request.user, 'staff_profile', None)
    if not staff:
        return Response(
            {'error': "User does not have staff profile"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    has_permission, error_message = check_face_attendance_permissions(staff, hotel)
    if not has_permission:
        return Response(
            {'error': error_message}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validate encoding
    encoding = request.data.get('encoding')
    if not isinstance(encoding, list) or len(encoding) != 128:
        return Response({
            'error': 'A 128-length descriptor array is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find matching face
        staff_faces_qs = StaffFace.objects.filter(
            hotel=hotel,
            is_active=True
        ).select_related('staff')
        
        matched_staff, confidence_score = find_best_face_match(
            encoding, 
            staff_faces_qs, 
            threshold=0.6
        )
        
        if not matched_staff:
            return Response({
                'error': 'Face not recognized',
                'confidence_score': confidence_score
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Find existing open log
        today = now().date()
        existing_log = ClockLog.objects.filter(
            hotel=hotel,
            staff=matched_staff,
            time_in__date=today,
            time_out__isnull=True
        ).first()
        
        if not existing_log:
            return Response({
                'error': 'No active clock-in found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # End break if currently on break
        if existing_log.is_on_break:
            existing_log.is_on_break = False
            if existing_log.break_start:
                break_duration = (now() - existing_log.break_start).total_seconds() / 60
                existing_log.total_break_minutes += int(break_duration)
            existing_log.break_end = now()
        
        # Clock out
        existing_log.time_out = now()
        existing_log.save()
        
        # Update staff status (both new and legacy fields)
        matched_staff.duty_status = 'off_duty'
        matched_staff.is_on_duty = False
        matched_staff.save(update_fields=['duty_status', 'is_on_duty'])
        
        # Calculate session duration
        session_duration = (existing_log.time_out - existing_log.time_in).total_seconds() / 3600
        
        # Get staff image
        staff_image = None
        try:
            staff_face = StaffFace.objects.get(staff=matched_staff, is_active=True)
            staff_image = staff_face.get_image_url()
        except StaffFace.DoesNotExist:
            pass
        
        # Serialize response
        serializer = ClockLogSerializer(existing_log)
        
        return Response({
            'action': 'clock_out_success',
            'message': f'{matched_staff.first_name} {matched_staff.last_name} clocked out successfully!',
            'staff': {
                'id': matched_staff.id,
                'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                'department': matched_staff.department.name if matched_staff.department else 'No Department',
                'image': staff_image
            },
            'session_summary': {
                'duration_hours': round(session_duration, 2),
                'total_break_minutes': existing_log.total_break_minutes,
                'clock_in_time': existing_log.time_in.isoformat(),
                'clock_out_time': existing_log.time_out.isoformat()
            },
            'confidence_score': confidence_score,
            'clock_log': serializer.data
        }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response(
            {'error': f'Clock-out failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_break_view(request, hotel_slug):
    """
    Independent endpoint for break toggle.
    
    POST /api/staff/hotel/{hotel_slug}/attendance/face-management/toggle-break/
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    # Check permissions
    staff = getattr(request.user, 'staff_profile', None)
    if not staff:
        return Response(
            {'error': "User does not have staff profile"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    has_permission, error_message = check_face_attendance_permissions(staff, hotel)
    if not has_permission:
        return Response(
            {'error': error_message}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validate encoding
    encoding = request.data.get('encoding')
    if not isinstance(encoding, list) or len(encoding) != 128:
        return Response({
            'error': 'A 128-length descriptor array is required.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find matching face
        staff_faces_qs = StaffFace.objects.filter(
            hotel=hotel,
            is_active=True
        ).select_related('staff')
        
        matched_staff, confidence_score = find_best_face_match(
            encoding, 
            staff_faces_qs, 
            threshold=0.6
        )
        
        if not matched_staff:
            return Response({
                'error': 'Face not recognized',
                'confidence_score': confidence_score
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Find existing open log
        today = now().date()
        existing_log = ClockLog.objects.filter(
            hotel=hotel,
            staff=matched_staff,
            time_in__date=today,
            time_out__isnull=True
        ).first()
        
        if not existing_log:
            return Response({
                'error': 'No active clock-in found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get staff image
        staff_image = None
        try:
            staff_face = StaffFace.objects.get(staff=matched_staff, is_active=True)
            staff_image = staff_face.get_image_url()
        except StaffFace.DoesNotExist:
            pass
        
        if existing_log.is_on_break:
            # End break
            existing_log.is_on_break = False
            if existing_log.break_start:
                break_duration = (now() - existing_log.break_start).total_seconds() / 60
                existing_log.total_break_minutes += int(break_duration)
            existing_log.break_end = now()
            existing_log.save()
            
            # Update staff duty status back to on_duty
            matched_staff.duty_status = 'on_duty'
            matched_staff.save(update_fields=['duty_status'])
            
            return Response({
                'action': 'break_ended',
                'message': f'{matched_staff.first_name} {matched_staff.last_name} ended break',
                'staff': {
                    'id': matched_staff.id,
                    'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                    'department': matched_staff.department.name if matched_staff.department else 'No Department',
                    'image': staff_image
                },
                'break_info': {
                    'is_on_break': False,
                    'break_duration_minutes': int(break_duration) if existing_log.break_start else 0,
                    'total_break_minutes': existing_log.total_break_minutes
                },
                'confidence_score': confidence_score
            }, status=status.HTTP_200_OK)
        else:
            # Start break
            existing_log.is_on_break = True
            existing_log.break_start = now()
            existing_log.save()
            
            # Update staff duty status (keep is_on_duty=True since still working)
            matched_staff.duty_status = 'on_break'
            # Don't change is_on_duty - staff is still working, just on break
            matched_staff.save(update_fields=['duty_status'])
            
            # Trigger Pusher event for break start
            trigger_clock_status_update(hotel.slug, matched_staff, 'start_break')
            
            return Response({
                'action': 'break_started',
                'message': f'{matched_staff.first_name} {matched_staff.last_name} started break',
                'staff': {
                    'id': matched_staff.id,
                    'name': f'{matched_staff.first_name} {matched_staff.last_name}',
                    'department': matched_staff.department.name if matched_staff.department else 'No Department',
                    'image': staff_image
                },
                'break_info': {
                    'is_on_break': True,
                    'break_start_time': existing_log.break_start.isoformat(),
                    'total_break_minutes': existing_log.total_break_minutes
                },
                'confidence_score': confidence_score
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response(
            {'error': f'Break toggle failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )