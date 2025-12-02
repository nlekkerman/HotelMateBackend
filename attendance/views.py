# attendance/views.py

from datetime import timedelta, date, datetime, time
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import viewsets, status, exceptions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

# Security imports
from common.mixins import HotelScopedViewSetMixin, AttendanceHotelScopedMixin
from staff_chat.permissions import IsStaffMember, IsSameHotel
from .pdf_report import build_roster_pdf, build_weekly_roster_pdf, build_daily_plan_grouped_pdf
from django_filters.rest_framework import DjangoFilterBackend
from collections import defaultdict
from .models import ClockLog, StaffFace, RosterPeriod, StaffRoster, ShiftLocation, DailyPlan, DailyPlanEntry, RosterAuditLog, FaceAuditLog
from .serializers import (
    ClockLogSerializer,
    RosterPeriodSerializer,
    StaffRosterSerializer,
    ShiftLocationSerializer,
    DailyPlanEntrySerializer,
    DailyPlanSerializer,
    CopyDayAllSerializer,
    CopyWeekSerializer,
    CopyWeekStaffSerializer,
)

from hotel.models import Hotel
from staff.pusher_utils import (
    trigger_clock_status_update,
    trigger_attendance_log,
    trigger_roster_update
)
from chat.utils import pusher_client

# attendance/filters.py
import django_filters
from .filters import StaffRosterFilter

# ---------------------- helpers ----------------------
def log_roster_operation(hotel, operation_type, performed_by=None, **kwargs):
    """
    Helper function to create audit log entries for roster operations.
    
    Args:
        hotel: Hotel instance
        operation_type: One of RosterAuditLog.OPERATION_TYPES
        performed_by: Staff instance (optional)
        **kwargs: Additional fields (affected_shifts_count, source_period, target_period, etc.)
    """
    try:
        audit_log = RosterAuditLog.objects.create(
            hotel=hotel,
            operation_type=operation_type,
            performed_by=performed_by,
            **kwargs
        )
        return audit_log
    except Exception as e:
        # Don't let audit logging break the main operation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create roster audit log: {e}")
        return None


def euclidean(a, b):
    """Compute Euclidean distance between two equal‑length lists of floats."""
    import math
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ---------------------- Overnight Shift & Overlap Utilities ----------------------

def shift_to_datetime_range(shift_date, shift_start, shift_end):
    """
    Convert (shift_date, shift_start, shift_end) into (start_dt, end_dt),
    supporting overnight shifts where end < start (crossing midnight).
    """
    start_dt = datetime.combine(shift_date, shift_start)
    end_dt = datetime.combine(shift_date, shift_end)

    # Overnight: if end time is "earlier" than start, assume next day
    if shift_end < shift_start:
        end_dt += timedelta(days=1)

    return start_dt, end_dt


def calculate_shift_hours(shift_date, shift_start, shift_end):
    """
    Calculate the duration of a shift in hours, supporting overnight shifts.
    """
    start_dt, end_dt = shift_to_datetime_range(shift_date, shift_start, shift_end)
    duration = end_dt - start_dt
    return round(duration.total_seconds() / 3600, 2)


def is_overnight_shift(shift_start, shift_end):
    """
    Determine if a shift is overnight (crosses midnight).
    """
    return shift_end < shift_start


def validate_shift_duration(shift_date, shift_start, shift_end, max_hours=12.0):
    """
    Validate that a shift duration doesn't exceed maximum allowed hours.
    """
    duration = calculate_shift_hours(shift_date, shift_start, shift_end)
    
    if duration > max_hours:
        raise ValueError(
            f"Shift duration ({duration:.1f} hours) exceeds maximum allowed length ({max_hours} hours)."
        )


def validate_overnight_shift_end_time(shift_start, shift_end, max_end_hour=6):
    """
    Validate that overnight shifts end within reasonable morning hours.
    """
    if is_overnight_shift(shift_start, shift_end):
        if shift_end.hour > max_end_hour:
            raise ValueError(
                f"Overnight shifts cannot end after {max_end_hour:02d}:00. "
                f"End time {shift_end.strftime('%H:%M')} is too late."
            )


def has_overlaps_for_staff(shifts):
    """
    Check for overlapping shifts within the same staff member on the same date.
    Different staff can work the same hours without conflict.
    """
    from collections import defaultdict
    
    # Group shifts by (staff_id, shift_date)
    groups = defaultdict(list)
    
    for shift in shifts:
        # Handle both date objects and string dates
        shift_date = shift["shift_date"]
        if isinstance(shift_date, str):
            shift_date = datetime.strptime(shift_date, "%Y-%m-%d").date()
        elif isinstance(shift_date, datetime):
            shift_date = shift_date.date()
        
        # Handle staff_id vs staff field names
        staff_id = shift.get("staff_id") or shift.get("staff")
        
        key = (staff_id, shift_date)
        groups[key].append(shift)
    
    # Check for overlaps within each group
    for key, group in groups.items():
        if len(group) <= 1:
            continue  # No overlaps possible with single shift
            
        # Convert to datetime ranges
        ranges = []
        for shift in group:
            shift_date = shift["shift_date"]
            if isinstance(shift_date, str):
                shift_date = datetime.strptime(shift_date, "%Y-%m-%d").date()
            elif isinstance(shift_date, datetime):
                shift_date = shift_date.date()
                
            start_dt, end_dt = shift_to_datetime_range(
                shift_date, shift["shift_start"], shift["shift_end"]
            )
            ranges.append((start_dt, end_dt, shift))
        
        # Sort by start time
        ranges.sort(key=lambda r: r[0])
        
        # Check consecutive intervals for overlap
        for i in range(len(ranges) - 1):
            current_end = ranges[i][1]
            next_start = ranges[i + 1][0]
            
            # Overlaps if current shift ends after next shift starts
            # Allow exact adjacency (current_end == next_start)
            if current_end > next_start:
                return True
    
    return False


def get_existing_shifts_for_overlap_check(staff_ids, date_range, hotel_id=None):
    """
    Fetch existing shifts from database for overlap checking.
    """
    # Build query
    query_filters = {
        "staff_id__in": staff_ids,
        "shift_date__range": date_range,
    }
    
    if hotel_id:
        query_filters["hotel_id"] = hotel_id
    
    existing_shifts = StaffRoster.objects.filter(**query_filters).values(
        "staff_id", "shift_date", "shift_start", "shift_end"
    )
    
    return list(existing_shifts)


# Legacy function for backward compatibility
def detect_overlapping_shifts(shifts):
    """
    Legacy function - now uses the improved has_overlaps_for_staff logic.
    """
    return has_overlaps_for_staff(shifts)


def find_matching_shift_for_datetime(hotel, staff, current_dt):
    """
    Find the StaffRoster entry for this hotel & staff whose datetime range
    (using shift_to_datetime_range) contains `current_dt`.

    Consider both today and yesterday for overnight shifts.
    Return a single StaffRoster instance or None.
    """
    from django.utils.timezone import make_aware, is_aware
    
    today = current_dt.date()
    yesterday = today - timedelta(days=1)

    candidates = StaffRoster.objects.filter(
        hotel=hotel,
        staff=staff,
        shift_date__in=[yesterday, today],
        shift_start__isnull=False,
        shift_end__isnull=False,
    )

    matches = []
    for shift in candidates:
        start_dt, end_dt = shift_to_datetime_range(
            shift.shift_date,
            shift.shift_start,
            shift.shift_end,
        )
        
        # Ensure timezone consistency
        if is_aware(current_dt) and not is_aware(start_dt):
            start_dt = make_aware(start_dt)
            end_dt = make_aware(end_dt)
        elif not is_aware(current_dt) and is_aware(start_dt):
            current_dt = make_aware(current_dt)
            
        if start_dt <= current_dt <= end_dt:
            matches.append((start_dt, end_dt, shift))

    if not matches:
        return None

    # In theory there should be at most one due to overlap rules.
    # But just in case, pick the earliest/shortest to be deterministic.
    matches.sort(key=lambda tup: (tup[0], tup[1] - tup[0]))
    return matches[0][2]

# ---------------------- Clock / Face ----------------------
class ClockLogViewSet(AttendanceHotelScopedMixin, viewsets.ModelViewSet):
    queryset = ClockLog.objects.select_related('staff__department','staff', 'hotel').all()
    serializer_class = ClockLogSerializer
    # Permissions are inherited from AttendanceHotelScopedMixin: [IsAuthenticated, IsStaffMember, IsSameHotel]

    @action(detail=False, methods=['post'], url_path='register-face')
    def register_face(self, request, hotel_slug=None):
        descriptor = request.data.get("descriptor")
        if not isinstance(descriptor, list) or len(descriptor) != 128:
            return Response({"error": "A 128‑length descriptor array is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        hotel_slug = self.kwargs.get('hotel_slug')
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        staff = getattr(request.user, "staff_profile", None)
        if not staff:
            return Response({"error": "User has no linked staff profile."},
                            status=status.HTTP_400_BAD_REQUEST)
                            
        # Validate staff belongs to the hotel
        if staff.hotel.slug != hotel_slug:
            return Response({"error": "You don't have access to this hotel."},
                            status=status.HTTP_403_FORBIDDEN)

        StaffFace.objects.filter(staff=staff).delete()
        StaffFace.objects.create(hotel=hotel, staff=staff, encoding=descriptor)
        staff.has_registered_face = True
        staff.save(update_fields=["has_registered_face"])

        return Response({"message": "Face descriptor registered."})

    @action(detail=False, methods=['post'], url_path='face-clock-in')
    def face_clock_in(self, request, hotel_slug=None):
        probe = request.data.get("descriptor")
        if not isinstance(probe, list) or len(probe) != 128:
            return Response({"error": "A 128‑length descriptor array is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        hotel_slug = self.kwargs.get('hotel_slug')
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Validate user has staff profile and belongs to this hotel
        staff = getattr(request.user, "staff_profile", None)
        if not staff or staff.hotel.slug != hotel_slug:
            return Response({"error": "You don't have access to this hotel."},
                            status=status.HTTP_403_FORBIDDEN)
        staff_faces = StaffFace.objects.select_related('staff') \
                                       .filter(hotel=hotel, staff__is_active=True)

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
                existing_log.time_out = now()
                existing_log.save()
                action_message = "Clock‑out"
                action_type = "clock_out"
                log = existing_log
                # Update staff status (both new and legacy fields)
                staff.duty_status = 'off_duty'
                staff.is_on_duty = False
            else:
                # CLOCK-IN path - find matching shift
                current_dt = now()
                matching_shift = find_matching_shift_for_datetime(hotel, staff, current_dt)
                
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
                    action_message = "Clock‑in"
                    action_type = "clock_in"
                    staff.is_on_duty = True
                else:
                    # Unrostered clock-in - return detection result for frontend confirmation
                    return Response({
                        "action": "unrostered_detected",
                        "message": f"No scheduled shift found for {staff.first_name}. Please confirm if you want to clock in anyway.",
                        "staff": {
                            "id": staff.id,
                            "name": f"{staff.first_name} {staff.last_name}",
                            "department": staff.department.name if staff.department else "No Department"
                        },
                        "requires_confirmation": True,
                        "confirmation_endpoint": f"/api/hotels/{hotel_slug}/clock-logs/unrostered-confirm/"
                    }, status=status.HTTP_200_OK)

            staff.save(update_fields=["duty_status", "is_on_duty"])

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

            return Response({
                "message": f"{action_message} successful for {staff.first_name}",
                "log": ClockLogSerializer(log).data
            })

        return Response({"error": "Face not recognized."}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=["get"], url_path="status")
    def current_status(self, request):
        staff = getattr(request.user, "staff_profile", None)
        hotel_slug = request.query_params.get("hotel_slug")
        if not staff or not hotel_slug:
            return Response({"error": "Missing staff or hotel."}, status=400)
            
        # Validate staff belongs to the hotel
        if staff.hotel.slug != hotel_slug:
            return Response({"error": "You don't have access to this hotel."}, status=403)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        latest_log = ClockLog.objects.filter(hotel=hotel, staff=staff) \
                                     .order_by("-time_in").first()

        if not latest_log:
            return Response({"status": "not_clocked_in"})
        if latest_log.time_out:
            return Response({"status": "clocked_out", "last_log": latest_log.time_out})
        return Response({"status": "clocked_in", "since": latest_log.time_in})

    @action(detail=False, methods=['post'], url_path='detect')
    def detect_face_only(self, request, hotel_slug=None):
        probe = request.data.get("descriptor")
        if not isinstance(probe, list) or len(probe) != 128:
            return Response({"error": "A 128‑length descriptor array is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        hotel_slug = self.kwargs.get('hotel_slug')
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Validate user has staff profile and belongs to this hotel
        staff = getattr(request.user, "staff_profile", None)
        if not staff or staff.hotel.slug != hotel_slug:
            return Response({"error": "You don't have access to this hotel."},
                            status=status.HTTP_403_FORBIDDEN)
        staff_faces = StaffFace.objects.select_related('staff') \
                                       .filter(hotel=hotel, staff__is_active=True)

        best_id, best_dist = None, float('inf')
        for face_entry in staff_faces:
            dist = euclidean(probe, face_entry.encoding)
            if dist < best_dist:
                best_dist, best_id = dist, face_entry.staff.id

        if best_dist <= 0.6:
            staff = get_object_or_404(staff_faces.model.staff.field.related_model, id=best_id)
            is_clocked_in = ClockLog.objects.filter(
                hotel=hotel, staff=staff,
                time_in__date=now().date(), time_out__isnull=True
            ).exists()
            return Response({
                "staff_id": staff.id,
                "staff_name": f"{staff.first_name} {staff.last_name}",
                "clocked_in": is_clocked_in
            })

        return Response({"error": "Face not recognized."}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=True, methods=['post'], url_path='auto-attach-shift')
    def auto_attach_shift(self, request, hotel_slug=None, pk=None):
        """
        Try to automatically attach this ClockLog to a StaffRoster shift
        based on its time_in and the existing roster.
        """
        log = self.get_object()
        current_dt = log.time_in

        matching_shift = find_matching_shift_for_datetime(
            hotel=log.hotel,
            staff=log.staff,
            current_dt=current_dt,
        )

        log.roster_shift = matching_shift
        log.save(update_fields=['roster_shift'])

        return Response(
            {
                "detail": "Shift attached." if matching_shift else "No matching shift found.",
                "roster_shift_id": matching_shift.id if matching_shift else None,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='relink-day')
    def relink_day(self, request, hotel_slug=None):
        """
        For a given date (and optionally staff), attempt to auto-attach
        all ClockLogs to matching shifts.
        """
        from django.utils.dateparse import parse_date
        
        date_str = request.data.get('date')
        staff_id = request.data.get('staff_id')

        if not date_str:
            return Response({"detail": "date is required (YYYY-MM-DD)."}, status=400)

        target_date = parse_date(date_str)
        if not target_date:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=400)
            
        hotel = self.get_hotel()  # from HotelScopedViewSetMixin

        logs = ClockLog.objects.filter(
            hotel=hotel,
            time_in__date=target_date,
        )
        if staff_id:
            logs = logs.filter(staff_id=staff_id)

        updated = 0
        for log in logs:
            match = find_matching_shift_for_datetime(hotel, log.staff, log.time_in)
            if match != log.roster_shift:
                log.roster_shift = match
                log.save(update_fields=['roster_shift'])
                updated += 1

        return Response({"updated_logs": updated}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='currently-clocked-in')
    def currently_clocked_in(self, request):
        hotel_slug = request.query_params.get('hotel_slug')
        if not hotel_slug:
            return Response({"detail": "hotel_slug query parameter required"}, status=400)
            
        # Validate staff belongs to the hotel
        staff = getattr(request.user, "staff_profile", None)
        if not staff or staff.hotel.slug != hotel_slug:
            return Response({"detail": "You don't have access to this hotel"}, status=403)

        logs = self.get_queryset().filter(time_out__isnull=True).order_by('-time_in')

        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='department-logs')
    def department_logs(self, request):
        hotel_slug = request.query_params.get('hotel_slug')
        department_slug = request.query_params.get('department_slug')

        if not hotel_slug:
            return Response({"detail": "hotel_slug query parameter required"}, status=400)
            
        # Validate staff belongs to the hotel
        staff = getattr(request.user, "staff_profile", None)
        if not staff or staff.hotel.slug != hotel_slug:
            return Response({"detail": "You don't have access to this hotel"}, status=403)

        logs = self.get_queryset()

        if department_slug:
            logs = logs.filter(staff__department__slug=department_slug)

        logs = logs.order_by('-time_in')

        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 4: UNROSTERED CLOCK-IN APPROVAL ENDPOINTS
    # ═══════════════════════════════════════════════════════════
    
    @action(detail=False, methods=['post'], url_path='unrostered-confirm')
    def unrostered_confirm(self, request, hotel_slug=None):
        """
        Confirm unrostered clock-in when staff wants to proceed without a scheduled shift.
        Creates a ClockLog with is_unrostered=True and is_approved=False (pending manager approval).
        """
        from .utils import send_unrostered_request_notification
        
        staff_id = request.data.get('staff_id')
        if not staff_id:
            return Response({"error": "staff_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Validate user has staff profile and belongs to this hotel
        request_staff = getattr(request.user, "staff_profile", None)
        if not request_staff or request_staff.hotel.slug != hotel_slug:
            return Response({"error": "You don't have access to this hotel."},
                            status=status.HTTP_403_FORBIDDEN)
        
        # Get the staff member to clock in (could be same as request_staff or different)
        from staff.models import Staff
        staff = get_object_or_404(Staff, id=staff_id, hotel=hotel)
        
        # Check if already clocked in today
        today = now().date()
        existing_log = ClockLog.objects.filter(
            hotel=hotel, staff=staff,
            time_in__date=today, time_out__isnull=True
        ).first()
        
        if existing_log:
            return Response({"error": "Staff member is already clocked in."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Create unrostered clock log
        log = ClockLog.objects.create(
            hotel=hotel,
            staff=staff,
            verified_by_face=True,
            roster_shift=None,
            is_unrostered=True,
            is_approved=False,   # manager must approve
            is_rejected=False,
        )
        
        # Update staff status
        # Update staff status (both new and legacy fields)
        staff.duty_status = 'on_duty'
        staff.is_on_duty = True
        staff.save(update_fields=["duty_status", "is_on_duty"])
        
        # Send notification to managers
        send_unrostered_request_notification(hotel, log)
        
        # Trigger Pusher events
        trigger_clock_status_update(hotel_slug, staff, "clock_in")
        trigger_attendance_log(
            hotel_slug,
            {
                'id': log.id,
                'staff_id': staff.id,
                'staff_name': f"{staff.first_name} {staff.last_name}",
                'department': staff.department.name if staff.department else None,
                'time': log.time_in,
                'verified_by_face': True,
                'is_unrostered': True,
                'is_approved': False,
            },
            "clock_in"
        )
        
        serializer = ClockLogSerializer(log)
        return Response(
            {
                "action": "unrostered_clock_in_created",
                "message": f"Unrostered clock-in recorded for {staff.first_name}. Manager approval required.",
                "log": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve_log(self, request, hotel_slug=None, pk=None):
        """
        Approve an unrostered clock log (manager action).
        """
        from .utils import is_period_or_log_locked
        
        log = self.get_object()
        
        # Check if log is locked due to period finalization
        if is_period_or_log_locked(clock_log=log):
            return Response({"error": "Cannot approve log: related period is finalized."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        log.is_approved = True
        log.is_rejected = False
        log.save(update_fields=['is_approved', 'is_rejected'])
        
        # Trigger Pusher event
        pusher_client.trigger(
            f"attendance-{hotel_slug}-staff-{log.staff.id}",
            'clocklog-approved',
            {
                'clock_log_id': log.id,
                'message': 'Your unrostered clock-in has been approved.',
                'approved_by': request.user.staff_profile.first_name if hasattr(request.user, 'staff_profile') else 'Manager'
            }
        )
        
        serializer = ClockLogSerializer(log)
        return Response({
            "detail": "Clock log approved.",
            "log": serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='reject')
    def reject_log(self, request, hotel_slug=None, pk=None):
        """
        Reject an unrostered clock log (manager action).
        """
        from .utils import is_period_or_log_locked
        
        log = self.get_object()
        
        # Check if log is locked due to period finalization
        if is_period_or_log_locked(clock_log=log):
            return Response({"error": "Cannot reject log: related period is finalized."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        log.is_approved = False
        log.is_rejected = True
        log.save(update_fields=['is_approved', 'is_rejected'])
        
        # Clock out staff if currently on duty with this log
        if log.time_out is None:
            log.time_out = now()
            log.save(update_fields=['time_out'])
            # Update staff status (both new and legacy fields)
            log.staff.duty_status = 'off_duty'
            log.staff.is_on_duty = False
            log.staff.save(update_fields=['duty_status', 'is_on_duty'])
        
        # Trigger Pusher event
        pusher_client.trigger(
            f"attendance-{hotel_slug}-staff-{log.staff.id}",
            'clocklog-rejected',
            {
                'clock_log_id': log.id,
                'message': 'Your unrostered clock-in has been rejected and you have been clocked out.',
                'rejected_by': request.user.staff_profile.first_name if hasattr(request.user, 'staff_profile') else 'Manager'
            }
        )
        
        serializer = ClockLogSerializer(log)
        return Response({
            "detail": "Clock log rejected.",
            "log": serializer.data
        }, status=status.HTTP_200_OK)
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 4: BREAK & OVERTIME ALERT ENDPOINTS
    # ═══════════════════════════════════════════════════════════
    
    @action(detail=True, methods=['post'], url_path='stay-clocked-in')
    def stay_clocked_in(self, request, hotel_slug=None, pk=None):
        """
        Staff acknowledges hard limit warning and chooses to stay clocked in.
        """
        log = self.get_object()
        
        if log.time_out is not None:
            return Response({"detail": "Log is already closed."}, status=status.HTTP_400_BAD_REQUEST)
        
        log.long_session_ack_mode = 'stay'
        log.save(update_fields=['long_session_ack_mode'])
        
        # Notify managers of the decision
        pusher_client.trigger(
            f"attendance-{hotel_slug}-managers",
            'staff-long-session-acknowledged',
            {
                'clock_log_id': log.id,
                'staff_id': log.staff.id,
                'staff_name': f"{log.staff.first_name} {log.staff.last_name}",
                'action': 'staying_clocked_in',
                'message': f"{log.staff.first_name} {log.staff.last_name} chose to stay clocked in after hard limit warning.",
                'timestamp': now().isoformat(),
            }
        )
        
        return Response({
            "detail": "Staying clocked in confirmed.",
            "action": "stay_acknowledged"
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='force-clock-out')
    def force_clock_out(self, request, hotel_slug=None, pk=None):
        """
        Staff acknowledges hard limit warning and chooses to clock out immediately.
        """
        log = self.get_object()
        
        if log.time_out is not None:
            return Response({"detail": "Log is already closed."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Clock out the staff member
        log.time_out = now()
        log.long_session_ack_mode = 'clocked_out'
        log.save(update_fields=['time_out', 'long_session_ack_mode'])
        
        # Update staff status (both new and legacy fields)
        log.staff.duty_status = 'off_duty'
        log.staff.is_on_duty = False
        log.staff.save(update_fields=['duty_status', 'is_on_duty'])
        
        # Trigger Pusher events
        trigger_clock_status_update(hotel_slug, log.staff, "clock_out")
        trigger_attendance_log(
            hotel_slug,
            {
                'id': log.id,
                'staff_id': log.staff.id,
                'staff_name': f"{log.staff.first_name} {log.staff.last_name}",
                'department': log.staff.department.name if log.staff.department else None,
                'time': log.time_out,
                'verified_by_face': True,
            },
            "clock_out"
        )
        
        serializer = ClockLogSerializer(log)
        return Response({
            "detail": "Clocked out successfully after hard limit warning.",
            "action": "clock_out_completed",
            "log": serializer.data
        }, status=status.HTTP_200_OK)

# ---------------------- Roster Period ----------------------
class RosterPeriodViewSet(AttendanceHotelScopedMixin, viewsets.ModelViewSet):
    queryset = RosterPeriod.objects.select_related('hotel', 'created_by').all()
    serializer_class = RosterPeriodSerializer
    # Permissions are inherited from AttendanceHotelScopedMixin: [IsAuthenticated, IsStaffMember, IsSameHotel]

    def perform_create(self, serializer):
        """Create roster period with proper hotel and staff assignment"""
        staff_hotel = self.get_staff_hotel()
        staff_profile = self.request.user.staff_profile
        serializer.save(hotel=staff_hotel, created_by=staff_profile)

    @action(detail=True, methods=['post'], url_path='add-shift')
    def add_shift(self, request, pk=None):
        period = self.get_object()
        serializer = StaffRosterSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(period=period, hotel=period.hotel)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='create-department-roster')
    def create_department_roster(self, request, pk=None):
        period = self.get_object()
        hotel = period.hotel
        department = request.data.get("department")
        shifts = request.data.get("shifts", [])
        created, errors = [], []

        for entry in shifts:
            entry.update({
                "department": department,
                "hotel": hotel.id,
                "period": period.id,
            })
            serializer = StaffRosterSerializer(data=entry, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                created.append(serializer.data)
            else:
                errors.append({"data": entry, "errors": serializer.errors})

        return Response({"created": created, "errors": errors},
                        status=201 if not errors else 207)

    @action(detail=False, methods=['post'], url_path='create-for-week')
    def create_for_week(self, request, *args, **kwargs):
        """
        POST /attendance/<hotel_slug>/periods/create-for-week/
        {
          "date": "2025-07-21"
        }
        """
        input_date = request.data.get("date")
        if not input_date:
            return Response({"error": "Field 'date' is required."}, status=400)

        parsed_date = parse_date(input_date)
        if not parsed_date:
            return Response({"error": "Invalid date format."}, status=400)

        # Monday start (0 = Monday)
        start_date = parsed_date - timedelta(days=parsed_date.weekday())
        end_date = start_date + timedelta(days=6)

        hotel = self.get_hotel()

        period, created = RosterPeriod.objects.get_or_create(
            hotel=hotel,
            start_date=start_date,
            defaults={
                "end_date": end_date,
                "title": f"Week of {start_date.strftime('%b %d')}",
                "created_by": getattr(self.request.user, "staff_profile", None),
            }
        )

        serializer = self.get_serializer(period)
        return Response(serializer.data, status=201 if created else 200)
    # add this to your class (or edit your existing one)
    
    @action(detail=True, methods=["get"], url_path="export-pdf")
    def export_pdf(self, request, pk=None, **kwargs):
        """
        GET /attendance/<hotel_slug>/periods/<pk>/export-pdf/?department=...
        """
        period = self.get_object()
        hotel = self.get_hotel()
        department = request.query_params.get("department")
        location_id = request.query_params.get("location")

        qs = StaffRoster.objects.select_related("staff", "location") \
                                .filter(period=period, hotel=hotel)
        if department:
            qs = qs.filter(department__slug=department)

        if location_id:
            qs = qs.filter(location_id=location_id)

        title = f"Weekly Roster – {period.title or period.start_date}"
        meta = [
            f"Hotel: {hotel.name}",
            f"Period: {period.start_date} – {period.end_date}",
            f"Department: {department or 'All'}",
        ]

        # NEW: Use the weekly board-style PDF
        pdf_bytes = build_weekly_roster_pdf(
            title,
            meta,
            qs,
            period.start_date,
            period.end_date
        )

        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = (
            f'attachment; filename="roster_{hotel.slug}_{period.start_date}.pdf"'
        )
        return resp

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        for period in queryset:
            hotel_name = period.hotel.name
            title = period.title
            start_date = period.start_date.strftime("%B %d, %Y")
            end_date = period.end_date.strftime("%B %d, %Y")
            published = period.published
            created_by = f"{period.created_by.first_name} {period.created_by.last_name}" if period.created_by else "N/A"

            # Get departments related to this period through roster requirements
            departments = set(req.department.name for req in period.requirements.all())

            print(
                f"RosterPeriod: {title} | Hotel: {hotel_name} | "
                f"Start: {start_date} | End: {end_date} | Published: {published} | "
                f"Created by: {created_by} | Departments: {', '.join(departments) if departments else 'None'}"
            )

        return Response(serializer.data)
    
    # ═══════════════════════════════════════════════════════════
    # PHASE 4: PERIOD FINALIZATION ENDPOINTS
    # ═══════════════════════════════════════════════════════════
    
    @action(detail=True, methods=['post'], url_path='finalize')
    def finalize_period(self, request, hotel_slug=None, pk=None):
        """
        Finalize a roster period, locking all related ClockLogs and StaffRoster shifts.
        Validates that no unresolved unrostered logs exist within the period.
        """
        from django.utils.timezone import now
        from .utils import validate_period_finalization
        
        period = self.get_object()
        
        # Check if already finalized
        if period.is_finalized:
            return Response({
                "error": f"Period '{period.title}' is already finalized.",
                "finalized_at": period.finalized_at,
                "finalized_by": period.finalized_by.first_name if period.finalized_by else None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate period can be finalized
        force = request.data.get('force', False)
        is_admin = getattr(request.user, 'is_staff', False)
        
        if not force:
            is_valid, error_message = validate_period_finalization(period)
            if not is_valid:
                return Response({
                    "error": error_message,
                    "can_force": is_admin,
                    "suggestion": "Resolve unrostered logs or use force=true (admin only)"
                }, status=status.HTTP_400_BAD_REQUEST)
        elif force and not is_admin:
            return Response({
                "error": "Only administrators can force finalization with unresolved logs."
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Finalize the period
        period.is_finalized = True
        period.finalized_by = getattr(request.user, 'staff_profile', None)
        period.finalized_at = now()
        period.save(update_fields=['is_finalized', 'finalized_by', 'finalized_at'])
        
        # Log the finalization
        log_roster_operation(
            hotel=period.hotel,
            operation_type='finalize_period',
            performed_by=period.finalized_by,
            target_period=period,
            operation_details={
                'period_title': period.title,
                'start_date': str(period.start_date),
                'end_date': str(period.end_date),
                'forced': force,
            }
        )
        
        # Notify managers
        pusher_client.trigger(
            f"attendance-{hotel_slug}-managers",
            'period-finalized',
            {
                'period_id': period.id,
                'period_title': period.title,
                'finalized_by': period.finalized_by.first_name if period.finalized_by else 'System',
                'message': f"Roster period '{period.title}' has been finalized.",
                'timestamp': period.finalized_at.isoformat(),
            }
        )
        
        serializer = RosterPeriodSerializer(period)
        return Response({
            "detail": f"Period '{period.title}' finalized successfully.",
            "period": serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='unfinalize')
    def unfinalize_period(self, request, hotel_slug=None, pk=None):
        """
        Unfinalize a roster period (admin only).
        """
        period = self.get_object()
        
        # Admin check
        if not getattr(request.user, 'is_staff', False):
            return Response({
                "error": "Only administrators can unfinalize periods."
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not period.is_finalized:
            return Response({
                "error": f"Period '{period.title}' is not finalized."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Unfinalize the period
        period.is_finalized = False
        period.finalized_by = None
        period.finalized_at = None
        period.save(update_fields=['is_finalized', 'finalized_by', 'finalized_at'])
        
        # Log the unfinalization
        log_roster_operation(
            hotel=period.hotel,
            operation_type='unfinalize_period',
            performed_by=getattr(request.user, 'staff_profile', None),
            target_period=period,
            operation_details={
                'period_title': period.title,
                'start_date': str(period.start_date),
                'end_date': str(period.end_date),
            }
        )
        
        # Notify managers
        pusher_client.trigger(
            f"attendance-{hotel_slug}-managers",
            'period-unfinalized',
            {
                'period_id': period.id,
                'period_title': period.title,
                'unfinalized_by': request.user.staff_profile.first_name if hasattr(request.user, 'staff_profile') else 'Admin',
                'message': f"Roster period '{period.title}' has been unfinalized and is now editable.",
                'timestamp': now().isoformat(),
            }
        )
        
        serializer = RosterPeriodSerializer(period)
        return Response({
            "detail": f"Period '{period.title}' unfinalized successfully.",
            "period": serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='finalization-status')
    def finalization_status(self, request, hotel_slug=None, pk=None):
        """
        Check finalization status and validation for a roster period.
        """
        from .utils import validate_period_finalization
        
        period = self.get_object()
        
        if period.is_finalized:
            return Response({
                "is_finalized": True,
                "finalized_at": period.finalized_at,
                "finalized_by": period.finalized_by.first_name if period.finalized_by else None,
                "can_unfinalize": getattr(request.user, 'is_staff', False),
            })
        
        # Check if can be finalized
        is_valid, error_message = validate_period_finalization(period)
        
        return Response({
            "is_finalized": False,
            "can_finalize": is_valid,
            "validation_error": error_message if not is_valid else None,
            "can_force": getattr(request.user, 'is_staff', False),
        })

# ---------------------- Staff Roster ----------------------
class StaffRosterViewSet(AttendanceHotelScopedMixin, viewsets.ModelViewSet):
    queryset = StaffRoster.objects.select_related('staff', 'hotel', 'period', 'approved_by', 'location').all()
    serializer_class = StaffRosterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = StaffRosterFilter
    pagination_class = None
    # Permissions are inherited from AttendanceHotelScopedMixin: [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Get hotel-scoped roster queryset with additional filters"""
        # Start with hotel-scoped queryset from mixin
        qs = super().get_queryset()

        # Apply additional filters while maintaining hotel security
        staff_id = self.request.query_params.get("staff") or self.request.query_params.get("staff_id")
        period_id = self.request.query_params.get("period")
        location_id = self.request.query_params.get("location")
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        department_slug = self.request.query_params.get("department")

        if department_slug:
            qs = qs.filter(staff__department__slug=department_slug)
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        if period_id:
            qs = qs.filter(period_id=period_id)
        if location_id:
            qs = qs.filter(location_id=location_id)
        if start and end:
            qs = qs.filter(shift_date__range=[start, end])

        return qs

    @action(detail=False, methods=['post'], url_path='bulk-save')
    def bulk_save(self, request, *args, **kwargs):
        all_shifts = request.data.get('shifts', []) or []
        created_data = [s for s in all_shifts if not s.get("id")]
        updated_data = [s for s in all_shifts if s.get("id")]

        default_hotel = request.data.get("hotel")
        default_period = request.data.get("period")
        if default_hotel:
            for s in created_data:
                s.setdefault("hotel", default_hotel)
        if default_period:
            for s in created_data:
                s.setdefault("period", default_period)

        errors = []
        created_result, updated_result = [], []

        # In-batch duplicate check
        seen = set()
        for idx, shift in enumerate(created_data):
            key = (shift.get("staff"), shift.get("shift_date"), shift.get("shift_start"))
            if key in seen:
                errors.append({"index": idx, "error": "Duplicate shift in batch."})
            else:
                seen.add(key)

        if errors:
            return Response({"created": [], "updated": [], "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # DB-level duplicate check for updates
        for idx, payload in enumerate(updated_data):
            instance = StaffRoster.objects.filter(pk=payload["id"]).first()
            if not instance:
                errors.append({"id": payload.get("id"), "detail": "Shift not found"})
                continue

            staff = payload.get("staff", instance.staff_id)
            shift_date = payload.get("shift_date", instance.shift_date.strftime("%Y-%m-%d"))
            shift_start = payload.get("shift_start", instance.shift_start.strftime("%H:%M"))

            conflict = StaffRoster.objects.filter(
                staff=staff,
                shift_date=shift_date,
                shift_start=shift_start
            ).exclude(id=instance.id).exists()

            if conflict:
                errors.append({"id": payload.get("id"), "detail": "Duplicate shift with these fields exists."})

        if errors:
            return Response({"created": [], "updated": [], "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Comprehensive overlap detection using new utilities
            # Prepare all shifts for overlap checking
            all_shifts_to_check = []
            
            # Add new shifts
            for shift in created_data:
                all_shifts_to_check.append({
                    "staff_id": shift.get("staff"),
                    "shift_date": shift.get("shift_date"),
                    "shift_start": shift.get("shift_start"),
                    "shift_end": shift.get("shift_end"),
                })
            
            # Add updated shifts
            for shift in updated_data:
                all_shifts_to_check.append({
                    "staff_id": shift.get("staff"),
                    "shift_date": shift.get("shift_date"),
                    "shift_start": shift.get("shift_start"),
                    "shift_end": shift.get("shift_end"),
                })
            
            # Get existing shifts for the affected staff/dates (excluding ones being updated)
            staff_ids = set()
            date_range = [None, None]
            
            for shift in all_shifts_to_check:
                staff_ids.add(shift["staff_id"])
                shift_date = shift["shift_date"]
                if isinstance(shift_date, str):
                    shift_date = datetime.strptime(shift_date, "%Y-%m-%d").date()
                
                if date_range[0] is None or shift_date < date_range[0]:
                    date_range[0] = shift_date
                if date_range[1] is None or shift_date > date_range[1]:
                    date_range[1] = shift_date
            
            if staff_ids and date_range[0] and date_range[1]:
                # Get existing shifts but exclude ones being updated
                update_ids = [shift["id"] for shift in updated_data if shift.get("id")]
                existing_query = StaffRoster.objects.filter(
                    staff_id__in=list(staff_ids),
                    shift_date__range=date_range
                )
                if update_ids:
                    existing_query = existing_query.exclude(id__in=update_ids)
                
                existing_shifts = existing_query.values(
                    "staff_id", "shift_date", "shift_start", "shift_end"
                )
                
                # Combine existing and new/updated shifts
                all_shifts_combined = list(existing_shifts) + all_shifts_to_check
                
                # Check for overlaps
                if has_overlaps_for_staff(all_shifts_combined):
                    errors.append({
                        "detail": "Bulk save would create overlapping shifts for one or more staff members."
                    })
            
            # Mark split shifts
            staff_date_map = defaultdict(list)
            for shift in created_data:
                staff_id = shift.get("staff")
                shift_date = shift.get("shift_date")
                if staff_id and shift_date:
                    staff_date_map[(staff_id, shift_date)].append(shift)

            for (staff_id, shift_date), new_shifts in staff_date_map.items():
                existing_count = StaffRoster.objects.filter(
                    staff_id=staff_id, shift_date=shift_date
                ).exclude(
                    id__in=[shift["id"] for shift in updated_data if shift.get("id")]
                ).count()
                
                if len(new_shifts) > 1 or existing_count > 0:
                    for shift in new_shifts:
                        shift["is_split_shift"] = True

            if errors:
                return Response({"created": [], "updated": [], "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

            create_ser = StaffRosterSerializer(data=created_data, many=True, context={'request': request})
            if create_ser.is_valid():
                create_ser.save()
                created_result = create_ser.data
            else:
                print("Create serializer errors:", create_ser.errors)
                errors.extend(create_ser.errors)

            if updated_data and not errors:
                for payload in updated_data:
                    instance = StaffRoster.objects.filter(pk=payload["id"]).first()
                    if not instance:
                        errors.append({"id": payload.get("id"), "detail": "Shift not found"})
                        continue
                    ser = StaffRosterSerializer(instance, data=payload, partial=True, context={'request': request})
                    if ser.is_valid():
                        ser.save()
                        updated_result.append(ser.data)
                    else:
                        print("Update serializer errors:", ser.errors)
                        errors.append(ser.errors)

            if errors:
                transaction.set_rollback(True)
                return Response({"created": [], "updated": [], "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"created": created_result, "updated": updated_result, "errors": []}, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=["get"], url_path="daily-pdf")
    def daily_pdf(self, request, hotel_slug=None, **kwargs):
        day = request.query_params.get("date")
        department = request.query_params.get("department")
        location_id = request.query_params.get("location")

        if not day:
            return Response({"error": "date parameter is required."}, status=400)

        # Use hotel-secured queryset from mixin
        staff_hotel = self.get_staff_hotel()
        qs = self.get_queryset().filter(shift_date=date.fromisoformat(day))

        if department:
            qs = qs.filter(department__slug=department)

        if location_id:
            qs = qs.filter(location_id=location_id)

        title = f"Daily Roster – {day}"
        meta = [
            f"Hotel: {staff_hotel.name}",
            f"Date: {day}",
            f"Department: {department or 'All'}",
        ]

        pdf_bytes = build_roster_pdf(title, meta, qs, landscape_mode=False)
        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="roster_{staff_hotel.slug}_{day}.pdf"'
        return resp

    @action(detail=False, methods=["get"], url_path="staff-pdf")
    def staff_pdf(self, request, hotel_slug=None, **kwargs):
        staff_id = request.query_params.get("staff_id") or request.query_params.get("staff")
        period_id = request.query_params.get("period")
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        department = request.query_params.get("department")
        location_id = request.query_params.get("location")

        if not staff_id:
            return Response({"error": "staff_id parameter is required."}, status=400)

        # Use hotel-secured queryset from mixin
        staff_hotel = self.get_staff_hotel()
        qs = self.get_queryset().filter(staff_id=staff_id)

        period_obj = None
        if period_id:
            qs = qs.filter(period_id=period_id)
            period_obj = RosterPeriod.objects.filter(pk=period_id).first()
        elif start and end:
            qs = qs.filter(shift_date__range=[start, end])
        else:
            return Response({"error": "Provide either 'period' or 'start' & 'end'."}, status=400)

        if department:
            qs = qs.filter(department__slug=department)
        if location_id:
            qs = qs.filter(location_id=location_id)

        staff = qs.first().staff if qs.exists() else None
        staff_name = (
            f"{getattr(staff, 'first_name', '')} {getattr(staff, 'last_name', '')}".strip()
            if staff else f"#{staff_id}"
        )

        if period_obj:
            date_str = f"{period_obj.start_date} – {period_obj.end_date}"
        else:
            date_str = f"{start} – {end}"

        title = f"Roster – {staff_name}"
        meta = [
            f"Hotel: {staff_hotel.name}",
            f"Staff: {staff_name}",
            f"Range: {date_str}",
            f"Department: {department or 'All'}",
        ]

        pdf_bytes = build_roster_pdf(title, meta, qs, landscape_mode=False)
        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="roster_{staff_hotel.slug}_staff_{staff_id}.pdf"'
        return resp
    
class ShiftLocationViewSet(HotelScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = ShiftLocation.objects.all()
    serializer_class = ShiftLocationSerializer
    # Permissions are inherited from HotelScopedViewSetMixin: [IsAuthenticated, IsStaffMember, IsSameHotel]

class DailyPlanViewSet(HotelScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = DailyPlan.objects.all()
    serializer_class = DailyPlanSerializer
    # Permissions are inherited from HotelScopedViewSetMixin: [IsAuthenticated, IsStaffMember, IsSameHotel]

    def get_queryset(self):
        """Get hotel-scoped daily plans with optional department filtering"""
        queryset = super().get_queryset()
        department_slug = self.kwargs.get('department_slug')
        if department_slug:
            queryset = queryset.filter(
                entries__roster__department__slug=department_slug
            ).distinct()
        return queryset

    @action(detail=False, methods=['get'], url_path='prepare-daily-plan')
    def prepare_daily_plan(self, request, *args, **kwargs):
        staff_hotel = self.get_staff_hotel()
        department_slug = kwargs.get('department_slug')
        date_str = request.query_params.get('date')

        if not date_str:
            return Response({'detail': 'date query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'detail': 'Invalid date format, expected YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        plan, created = DailyPlan.objects.get_or_create(hotel=staff_hotel, date=date_obj)

        # Clear existing entries to regenerate fresh
        plan.entries.all().delete()

        # Filter roster shifts for that date
        filters = {
            "hotel": staff_hotel,
            "shift_date": date_obj,
            "shift_start__isnull": False,
            "shift_end__isnull": False,
        }
        if department_slug:
            filters["department__slug"] = department_slug

        roster_shifts = StaffRoster.objects.filter(**filters).select_related(
            'staff', 'location', 'staff__role', 'department'
        )

        # Use update_or_create for each shift to avoid duplicates
        for shift in roster_shifts:
            DailyPlanEntry.objects.update_or_create(
                plan=plan,
                staff=shift.staff,
                location=shift.location,
                shift_start=shift.shift_start,
                shift_end=shift.shift_end,
                defaults={
                    'notes': '',
                    'roster': shift,
                }
            )

        # Return filtered entries with valid shift info
        filtered_entries = plan.entries.filter(
            roster__isnull=False,
            roster__shift_start__isnull=False,
            roster__shift_end__isnull=False,
        ).select_related('staff', 'location', 'roster', 'staff__role', 'staff__department')

        serializer = self.get_serializer(plan)
        data = serializer.data
        data['entries'] = DailyPlanEntrySerializer(filtered_entries, many=True).data

        return Response(data)


class DailyPlanEntryViewSet(viewsets.ModelViewSet):
    queryset = DailyPlanEntry.objects.all()
    serializer_class = DailyPlanEntrySerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]

    def get_daily_plan(self):
        """Get daily plan with hotel security validation"""
        daily_plan_id = self.kwargs.get("daily_plan_pk")
        daily_plan = get_object_or_404(DailyPlan, pk=daily_plan_id)
        
        # Validate the plan belongs to the user's hotel
        staff_hotel = self.request.user.staff_profile.hotel
        if daily_plan.hotel.id != staff_hotel.id:
            raise exceptions.PermissionDenied("You cannot access daily plans from other hotels")
        
        return daily_plan

    def get_queryset(self):
        """Get entries for the specific daily plan with hotel validation"""
        daily_plan = self.get_daily_plan()
        return DailyPlanEntry.objects.filter(plan=daily_plan)

    def perform_create(self, serializer):
        """Create entry with validated daily plan"""
        daily_plan = self.get_daily_plan()
        serializer.save(plan=daily_plan)   


class CopyRosterViewSet(viewsets.ViewSet):
    """
    ViewSet to handle bulk roster copying using CopyWeekSerializer.
    """
    permission_classes = [IsAuthenticated]
    
    # Rate limiting configuration
    MAX_SHIFTS_PER_COPY = 500  # Maximum shifts allowed in single copy operation
    MAX_COPIES_PER_HOUR = 10   # Maximum copy operations per user per hour

    def get_permissions(self):
        """Import permissions dynamically to avoid circular imports"""
        from staff_chat.permissions import IsStaffMember, IsSameHotel
        return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]
    
    def _check_rate_limit(self, request, hotel_slug):
        """Check if user has exceeded copy operation rate limit"""
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            staff = request.user.staff_profile
            one_hour_ago = timezone.now() - timedelta(hours=1)
            
            recent_operations = RosterAuditLog.objects.filter(
                hotel__slug=hotel_slug,
                performed_by=staff,
                timestamp__gte=one_hour_ago,
                operation_type__in=['copy_bulk', 'copy_day', 'copy_staff'],
                success=True
            ).count()
            
            if recent_operations >= self.MAX_COPIES_PER_HOUR:
                return Response(
                    {"detail": f"Rate limit exceeded. Maximum {self.MAX_COPIES_PER_HOUR} copy operations per hour."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            return None
        except AttributeError:
            # No staff profile - let permission classes handle this
            return None
    
    def _check_operation_size(self, shifts_count, operation_name):
        """Check if operation size exceeds safe limits"""
        if shifts_count > self.MAX_SHIFTS_PER_COPY:
            return Response(
                {
                    "detail": (
                        f"Operation too large. {operation_name} would copy {shifts_count} shifts. "
                        f"Maximum allowed: {self.MAX_SHIFTS_PER_COPY}. Please use smaller date ranges."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return None

    @action(detail=False, methods=['post'])
    def copy_roster_bulk(self, request, hotel_slug=None):
        # Check rate limiting
        rate_limit_response = self._check_rate_limit(request, hotel_slug)
        if rate_limit_response:
            return rate_limit_response
            
        serializer = CopyWeekSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        source_period_id = serializer.validated_data['source_period_id']
        target_period_id = serializer.validated_data['target_period_id']

        source_period = get_object_or_404(RosterPeriod, id=source_period_id, hotel__slug=hotel_slug)
        target_period = get_object_or_404(RosterPeriod, id=target_period_id, hotel__slug=hotel_slug)

        # Validate periods belong to same hotel
        if source_period.hotel != target_period.hotel:
            return Response(
                {"detail": "Source and target periods must belong to the same hotel."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if target period is published/locked
        if target_period.published:
            return Response(
                {"detail": "Cannot copy shifts to a published period."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source_shifts = StaffRoster.objects.filter(
            hotel__slug=hotel_slug,
            shift_date__gte=source_period.start_date,
            shift_date__lte=source_period.end_date,
        )

        if not source_shifts.exists():
            return Response(
                {"detail": "No shifts found in the source period."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check operation size before processing
        shifts_count = source_shifts.count()
        size_check_response = self._check_operation_size(shifts_count, "Bulk period copy")
        if size_check_response:
            return size_check_response

        day_diff = (target_period.start_date - source_period.start_date).days

        new_shifts = []
        for shift in source_shifts:
            new_date = shift.shift_date + timedelta(days=day_diff)
            # Ensure new date falls within target period
            if target_period.start_date <= new_date <= target_period.end_date:
                new_shifts.append(
                    StaffRoster(
                        hotel=shift.hotel,
                        staff=shift.staff,
                        shift_date=new_date,
                        shift_start=shift.shift_start,
                        shift_end=shift.shift_end,
                        expected_hours=shift.expected_hours,
                        department=shift.department,
                        location=shift.location,
                        period=target_period,
                    )
                )

        if not new_shifts:
            return Response(
                {"detail": "No valid shifts to copy within target period range."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Check for overlaps before creating
            # Get existing shifts in target period
            existing_shifts = list(
                StaffRoster.objects.filter(
                    hotel__slug=hotel_slug,
                    shift_date__gte=target_period.start_date,
                    shift_date__lte=target_period.end_date,
                ).values("staff_id", "shift_date", "shift_start", "shift_end")
            )
            
            # Prepare candidate shifts for overlap checking
            candidate_shifts = [
                {
                    "staff_id": shift.staff_id,
                    "shift_date": shift.shift_date,
                    "shift_start": shift.shift_start,
                    "shift_end": shift.shift_end,
                } for shift in new_shifts
            ]
            
            # Combine existing and candidate shifts
            all_combined = existing_shifts + candidate_shifts
            
            if has_overlaps_for_staff(all_combined):
                # Audit failed operation
                try:
                    staff = request.user.staff_profile
                    log_roster_operation(
                        hotel=source_period.hotel,
                        operation_type='copy_bulk',
                        performed_by=staff,
                        affected_shifts_count=0,
                        source_period=source_period,
                        target_period=target_period,
                        success=False,
                        error_message="Bulk copy would create overlapping shifts",
                        operation_details={
                            'requested_shifts': len(new_shifts)
                        }
                    )
                except AttributeError:
                    pass
                return Response(
                    {"detail": "Bulk roster copy would create overlapping shifts. Operation cancelled."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Use ignore_conflicts to prevent duplicate key errors
            created_shifts = StaffRoster.objects.bulk_create(new_shifts, ignore_conflicts=True)
            
            # Count actual created shifts (bulk_create with ignore_conflicts doesn't return count)
            actual_count = StaffRoster.objects.filter(
                hotel__slug=hotel_slug,
                shift_date__gte=target_period.start_date,
                shift_date__lte=target_period.end_date,
                period=target_period
            ).count()
            
            # Audit logging
            try:
                staff = request.user.staff_profile
                log_roster_operation(
                    hotel=source_period.hotel,
                    operation_type='copy_bulk',
                    performed_by=staff,
                    affected_shifts_count=len(new_shifts),
                    source_period=source_period,
                    target_period=target_period,
                    success=True,
                    operation_details={
                        'requested_shifts': len(new_shifts),
                        'actual_created': actual_count
                    }
                )
            except AttributeError:
                # Handle case where user has no staff_profile
                pass

        return Response(
            {'copied_shifts_count': len(new_shifts), 'actual_created_count': actual_count},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'])
    def copy_roster_day_all(self, request, hotel_slug=None):
        """
        Copy shifts for all staff from source_date to target_date.
        """
        # Check rate limiting
        rate_limit_response = self._check_rate_limit(request, hotel_slug)
        if rate_limit_response:
            return rate_limit_response
            
        serializer = CopyDayAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        source_date = serializer.validated_data['source_date']
        target_date = serializer.validated_data['target_date']

        source_period = RosterPeriod.objects.filter(
            hotel__slug=hotel_slug,
            start_date__lte=source_date,
            end_date__gte=source_date,
        ).first()
        target_period = RosterPeriod.objects.filter(
            hotel__slug=hotel_slug,
            start_date__lte=target_date,
            end_date__gte=target_date,
        ).first()

        if not source_period or not target_period:
            return Response(
                {"detail": "Source or target date is not within any roster period."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate periods belong to same hotel
        if source_period.hotel != target_period.hotel:
            return Response(
                {"detail": "Source and target periods must belong to the same hotel."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if target period is published/locked
        if target_period.published:
            return Response(
                {"detail": "Cannot copy shifts to a published period."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source_shifts = StaffRoster.objects.filter(
            hotel__slug=hotel_slug,
            shift_date=source_date,
        )

        if not source_shifts.exists():
            return Response(
                {"detail": "No shifts found for the source date."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check operation size before processing
        shifts_count = source_shifts.count()
        size_check_response = self._check_operation_size(shifts_count, "Day copy")
        if size_check_response:
            return size_check_response

        new_shifts = []
        for shift in source_shifts:
            new_shifts.append(
                StaffRoster(
                    hotel=shift.hotel,
                    staff=shift.staff,
                    shift_date=target_date,
                    shift_start=shift.shift_start,
                    shift_end=shift.shift_end,
                    expected_hours=shift.expected_hours,
                    department=shift.department,
                    location=shift.location,
                    period=target_period,
                )
            )

        with transaction.atomic():
            # Check for overlapping shifts using improved detection
            existing_shifts = list(
                StaffRoster.objects.filter(
                    hotel__slug=hotel_slug,
                    shift_date=target_date
                ).values("staff_id", "shift_date", "shift_start", "shift_end")
            )
            
            # Prepare new shifts for overlap checking
            new_shifts_data = [
                {
                    "staff_id": shift.staff_id,
                    "shift_date": shift.shift_date,
                    "shift_start": shift.shift_start,
                    "shift_end": shift.shift_end
                } for shift in new_shifts
            ]
            
            # Combine existing and new shifts
            all_combined = existing_shifts + new_shifts_data
            
            if has_overlaps_for_staff(all_combined):
                # Audit failed operation
                try:
                    staff = request.user.staff_profile
                    log_roster_operation(
                        hotel=source_period.hotel,
                        operation_type='copy_day',
                        performed_by=staff,
                        affected_shifts_count=0,
                        source_period=source_period,
                        target_period=target_period,
                        success=False,
                        error_message="Copying would create overlapping shifts",
                        operation_details={
                            'source_date': source_date.isoformat(),
                            'target_date': target_date.isoformat()
                        }
                    )
                except AttributeError:
                    pass
                return Response(
                    {"detail": "Copying would create overlapping shifts for one or more staff on the target date."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Use ignore_conflicts to prevent duplicate key errors
            StaffRoster.objects.bulk_create(new_shifts, ignore_conflicts=True)
            
            # Audit successful operation
            try:
                staff = request.user.staff_profile
                log_roster_operation(
                    hotel=source_period.hotel,
                    operation_type='copy_day',
                    performed_by=staff,
                    affected_shifts_count=len(new_shifts),
                    source_period=source_period,
                    target_period=target_period,
                    success=True,
                    operation_details={
                        'source_date': source_date.isoformat(),
                        'target_date': target_date.isoformat()
                    }
                )
            except AttributeError:
                pass

        return Response(
            {'copied_shifts_count': len(new_shifts)},
            status=status.HTTP_201_CREATED,
        )
    
    @action(detail=False, methods=['post'])
    def copy_week_staff(self, request, hotel_slug=None):
        """
        Copy all shifts for a single staff member from one period (week) to another.
        """
        # Check rate limiting
        rate_limit_response = self._check_rate_limit(request, hotel_slug)
        if rate_limit_response:
            return rate_limit_response
            
        serializer = CopyWeekStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        staff_id = serializer.validated_data['staff_id']
        source_period_id = serializer.validated_data['source_period_id']
        target_period_id = serializer.validated_data['target_period_id']

        # Get source and target periods
        source_period = get_object_or_404(
            RosterPeriod, id=source_period_id, hotel__slug=hotel_slug
        )
        target_period = get_object_or_404(
            RosterPeriod, id=target_period_id, hotel__slug=hotel_slug
        )

        # Validate periods belong to same hotel
        if source_period.hotel != target_period.hotel:
            return Response(
                {"detail": "Source and target periods must belong to the same hotel."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if target period is published/locked
        if target_period.published:
            return Response(
                {"detail": "Cannot copy shifts to a published period."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get shifts only for this staff in the source period
        source_shifts = StaffRoster.objects.filter(
            hotel__slug=hotel_slug,
            staff_id=staff_id,
            shift_date__gte=source_period.start_date,
            shift_date__lte=source_period.end_date,
        )

        if not source_shifts.exists():
            return Response(
                {"detail": "No shifts found for this staff in the source period."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check operation size before processing
        shifts_count = source_shifts.count()
        size_check_response = self._check_operation_size(shifts_count, "Staff week copy")
        if size_check_response:
            return size_check_response

        # Calculate date difference between periods
        day_diff = (target_period.start_date - source_period.start_date).days

        # Build new shifts list
        new_shifts = []
        for shift in source_shifts:
            new_date = shift.shift_date + timedelta(days=day_diff)
            # Ensure new date falls within target period
            if target_period.start_date <= new_date <= target_period.end_date:
                new_shifts.append(
                    StaffRoster(
                        hotel=shift.hotel,
                        staff=shift.staff,
                        shift_date=new_date,
                        shift_start=shift.shift_start,
                        shift_end=shift.shift_end,
                        expected_hours=shift.expected_hours,
                        department=shift.department,
                        location=shift.location,
                        period=target_period,
                    )
                )

        if not new_shifts:
            return Response(
                {"detail": "No valid shifts to copy within target period range."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Check for overlapping shifts for this staff member
            existing_shifts = list(
                StaffRoster.objects.filter(
                    staff_id=staff_id,
                    shift_date__gte=target_period.start_date,
                    shift_date__lte=target_period.end_date
                ).values("staff_id", "shift_date", "shift_start", "shift_end")
            )
            
            # Prepare new shifts for overlap checking
            new_shifts_data = [
                {
                    "staff_id": shift.staff_id,
                    "shift_date": shift.shift_date,
                    "shift_start": shift.shift_start,
                    "shift_end": shift.shift_end
                } for shift in new_shifts
            ]
            
            # Combine existing and new shifts for overlap detection
            all_combined = existing_shifts + new_shifts_data
            
            if has_overlaps_for_staff(all_combined):
                # Audit failed operation
                try:
                    staff = request.user.staff_profile
                    log_roster_operation(
                        hotel=source_period.hotel,
                        operation_type='copy_staff',
                        performed_by=staff,
                        affected_shifts_count=0,
                        source_period=source_period,
                        target_period=target_period,
                        affected_staff_id=staff_id,
                        success=False,
                        error_message="Copying would create overlapping shifts for this staff member",
                        operation_details={
                            'target_staff_id': staff_id
                        }
                    )
                except AttributeError:
                    pass
                return Response(
                    {"detail": "Copying would create overlapping shifts for this staff member. Operation cancelled."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Use ignore_conflicts to prevent duplicate key errors
            StaffRoster.objects.bulk_create(new_shifts, ignore_conflicts=True)
            
            # Audit successful operation
            try:
                staff = request.user.staff_profile
                log_roster_operation(
                    hotel=source_period.hotel,
                    operation_type='copy_staff',
                    performed_by=staff,
                    affected_shifts_count=len(new_shifts),
                    source_period=source_period,
                    target_period=target_period,
                    affected_staff_id=staff_id,
                    success=True,
                    operation_details={
                        'target_staff_id': staff_id
                    }
                )
            except AttributeError:
                pass

        return Response(
            {"copied_shifts_count": len(new_shifts)},
            status=status.HTTP_201_CREATED,
        )