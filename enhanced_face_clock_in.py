# Enhanced Face Clock-In View with Phase 2 Safety Features
# This replaces the existing face_clock_in method in ClockLogViewSet

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from attendance.models import ClockLog, StaffFace, FaceAuditLog
from hotel.models import Hotel
from attendance.views import find_matching_shift_for_datetime, euclidean, trigger_clock_status_update, trigger_attendance_log

# Import Phase 2 helpers
import sys
import os
sys.path.append(os.path.dirname(__file__))
from phase2_safety_support import (
    calculate_safety_warnings, get_shift_info, enhanced_face_clock_in_response,
    handle_force_log_unrostered, get_unrostered_response_with_force_option
)


def enhanced_face_clock_in_method(self, request, hotel_slug=None):
    """Enhanced face_clock_in method with Phase 2 safety features"""
    probe = request.data.get("descriptor")
    if not isinstance(probe, list) or len(probe) != 128:
        return Response({"error": "A 128‑length descriptor array is required."},
                        status=status.HTTP_400_BAD_REQUEST)

    hotel_slug = self.kwargs.get('hotel_slug')
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    # Validate user has staff profile and belongs to this hotel
    requesting_staff = getattr(request.user, "staff_profile", None)
    if not requesting_staff or requesting_staff.hotel.slug != hotel_slug:
        return Response({"error": "You don't have access to this hotel."},
                        status=status.HTTP_403_FORBIDDEN)
    
    staff_faces = StaffFace.objects.select_related('staff').filter(
        hotel=hotel, staff__is_active=True
    )

    # Face recognition
    best_id, best_dist = None, float('inf')
    for face_entry in staff_faces:
        dist = euclidean(probe, face_entry.encoding)
        if dist < best_dist:
            best_dist, best_id = dist, face_entry.staff.id

    if best_dist <= 0.6:
        staff = get_object_or_404(staff_faces.model.staff.field.related_model, id=best_id)
        today = now().date()
        existing_log = ClockLog.objects.filter(
            hotel=hotel, staff=staff,
            time_in__date=today, time_out__isnull=True
        ).first()

        if existing_log:
            # CLOCK OUT - Calculate session warnings before clocking out
            safety_warnings = calculate_safety_warnings(staff, existing_log, hotel)
            
            existing_log.time_out = now()
            existing_log.save()
            action_type = "clock_out"
            log = existing_log
            staff.is_on_duty = False
            staff.save(update_fields=["is_on_duty"])
            
            # Create enhanced response with safety info
            response_data = enhanced_face_clock_in_response(
                staff, log, action_type, hotel, existing_log
            )
            
        else:
            # CLOCK IN - Check for matching shift
            current_dt = now()
            matching_shift = find_matching_shift_for_datetime(hotel, staff, current_dt)
            
            # Handle force_log parameter for unrostered staff
            force_log = request.data.get('force_log', False)
            force_reason = request.data.get('force_reason', '')
            
            if matching_shift:
                # Normal rostered clock-in
                log = ClockLog.objects.create(
                    hotel=hotel,
                    staff=staff,
                    verified_by_face=True,
                    roster_shift=matching_shift,
                    is_unrostered=False,
                    is_approved=True,
                    is_rejected=False,
                )
                action_type = "clock_in"
                staff.is_on_duty = True
                staff.save(update_fields=["is_on_duty"])
                
                response_data = enhanced_face_clock_in_response(
                    staff, log, action_type, hotel
                )
                
            elif force_log:
                # Force log unrostered staff
                log = handle_force_log_unrostered(staff, hotel, request, force_reason)
                action_type = "clock_in"
                
                response_data = enhanced_face_clock_in_response(
                    staff, log, action_type, hotel
                )
                response_data['force_logged'] = True
                response_data['requires_manager_approval'] = True
                
            else:
                # Unrostered - return options for frontend
                return Response(
                    get_unrostered_response_with_force_option(staff, hotel_slug),
                    status=status.HTTP_200_OK
                )

        # Trigger Pusher events for real-time updates
        trigger_clock_status_update(hotel_slug, staff, action_type)
        trigger_attendance_log(
            hotel_slug,
            {
                'id': log.id,
                'staff_id': staff.id,
                'staff_name': f"{staff.first_name} {staff.last_name}",
                'department': (
                    staff.department.name if staff.department else None
                ),
                'time': (
                    log.time_out if action_type == 'clock_out'
                    else log.time_in
                ),
                'verified_by_face': True,
            },
            action_type
        )

        return Response(response_data)

    return Response({"error": "Face not recognized."}, status=status.HTTP_401_UNAUTHORIZED)


def force_log_endpoint_method(self, request, hotel_slug=None):
    """New endpoint for force logging unrostered staff"""
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    # Get requesting staff
    requesting_staff = getattr(request.user, "staff_profile", None)
    if not requesting_staff or requesting_staff.hotel != hotel:
        return Response(
            {"error": "You don't have access to this hotel."}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    staff_id = request.data.get('staff_id')
    reason = request.data.get('reason', 'Manual force log via kiosk')
    
    if not staff_id:
        return Response(
            {"error": "staff_id is required."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from staff.models import Staff
    target_staff = get_object_or_404(Staff, id=staff_id, hotel=hotel)
    
    # Check if already clocked in today
    today = now().date()
    existing_log = ClockLog.objects.filter(
        hotel=hotel, staff=target_staff,
        time_in__date=today, time_out__isnull=True
    ).first()

    if existing_log:
        return Response(
            {"error": "Staff member is already clocked in."}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create force log
    log = handle_force_log_unrostered(target_staff, hotel, request, reason)
    
    # Create response
    response_data = enhanced_face_clock_in_response(
        target_staff, log, "clock_in", hotel
    )
    response_data['force_logged'] = True
    response_data['requires_manager_approval'] = True
    
    return Response(response_data)