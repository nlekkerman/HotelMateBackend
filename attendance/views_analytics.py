# attendance/views_analytics.py
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from hotel.models import Hotel
from .analytics import RosterAnalytics as RA
from .serializers_analytics import (
    PeriodQuerySerializer,
    # period
    StaffRosterAnalyticsRowSerializer,
    DepartmentRosterAnalyticsRowSerializer,
    RosterKpiSerializer,
    # daily
    DailyTotalsRowSerializer,
    DailyDepartmentRowSerializer,
    DailyStaffRowSerializer,
    # weekly
    WeeklyTotalsRowSerializer,
    WeeklyDepartmentRowSerializer,
    WeeklyStaffRowSerializer,
)


class RosterAnalyticsViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def _hotel(self, hotel_slug, request=None):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        # --- Optional access guard ---
        # if request and hasattr(request.user, "staff_profile"):
        #     if request.user.staff_profile.hotel_id != hotel.id and not request.user.is_superuser:
        #         raise PermissionDenied("You are not allowed to access this hotel's analytics.")
        return hotel

    # ---------- Period ----------
    @action(detail=False, methods=['get'], url_path='staff-summary')
    def staff_summary(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = PeriodQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        d = params.validated_data

        rows = RA.staff_totals(self._hotel(hotel_slug, request), d['start'], d['end'], d.get('department'))

        payload = [{
            'staff_id': r['staff_id'],
            'first_name': r['staff__first_name'],
            'last_name': r['staff__last_name'],
            'department': r['department'],
            'total_rostered_hours': float(r['total_rostered_hours'] or 0),
            'shifts_count': r['shifts_count'],
            'avg_shift_length': float(r['avg_shift_length'] or 0),
        } for r in rows]
        return Response(StaffRosterAnalyticsRowSerializer(payload, many=True).data)

    @action(detail=False, methods=['get'], url_path='department-summary')
    def department_summary(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = PeriodQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        d = params.validated_data

        rows = RA.department_totals(self._hotel(hotel_slug, request), d['start'], d['end'])
        payload = [{
            'department': r['department'],
            'total_rostered_hours': float(r['total_rostered_hours'] or 0),
            'shifts_count': r['shifts_count'],
            'avg_shift_length': float(r['avg_shift_length'] or 0),
            'unique_staff': r['unique_staff'],
        } for r in rows]
        return Response(DepartmentRosterAnalyticsRowSerializer(payload, many=True).data)

    @action(detail=False, methods=['get'], url_path='kpis')
    def kpis(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = PeriodQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        d = params.validated_data

        k = RA.kpis(self._hotel(hotel_slug, request), d['start'], d['end'])
        data = {
            'total_rostered_hours': float(k.get('total_rostered_hours', 0) or 0),
            'total_shifts': int(k.get('total_shifts', 0) or 0),
            'avg_shift_length': float(k.get('avg_shift_length', 0) or 0),
            'unique_staff': int(k.get('unique_staff', 0) or 0),
        }
        return Response(RosterKpiSerializer(data).data)

    # ---------- Daily ----------
    @action(detail=False, methods=['get'], url_path='daily-totals')
    def daily_totals(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = PeriodQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        d = params.validated_data

        rows = RA.daily_totals(self._hotel(hotel_slug, request), d['start'], d['end'], d.get('department'))
        payload = [{
            'date': r['shift_date'],
            'total_rostered_hours': float(r['total_rostered_hours'] or 0),
            'shifts_count': r['shifts_count'],
        } for r in rows]
        return Response(DailyTotalsRowSerializer(payload, many=True).data)

    @action(detail=False, methods=['get'], url_path='daily-by-department')
    def daily_by_department(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = PeriodQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        d = params.validated_data

        rows = RA.daily_by_department(self._hotel(hotel_slug, request), d['start'], d['end'])
        payload = [{
            'date': r['shift_date'],
            'department': r['department'],
            'total_rostered_hours': float(r['total_rostered_hours'] or 0),
            'shifts_count': r['shifts_count'],
            'unique_staff': r['unique_staff'],
        } for r in rows]
        return Response(DailyDepartmentRowSerializer(payload, many=True).data)

    @action(detail=False, methods=['get'], url_path='daily-by-staff')
    def daily_by_staff(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = PeriodQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        d = params.validated_data

        rows = RA.daily_by_staff(self._hotel(hotel_slug, request), d['start'], d['end'], d.get('department'))
        payload = [{
            'date': r['shift_date'],
            'staff_id': r['staff_id'],
            'first_name': r['staff__first_name'],
            'last_name': r['staff__last_name'],
            'department': r['department'],
            'total_rostered_hours': float(r['total_rostered_hours'] or 0),
            'shifts_count': r['shifts_count'],
        } for r in rows]
        return Response(DailyStaffRowSerializer(payload, many=True).data)

    # ---------- Weekly ----------
    @action(detail=False, methods=['get'], url_path='weekly-totals')
    def weekly_totals(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = PeriodQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        d = params.validated_data

        rows = RA.weekly_totals(self._hotel(hotel_slug, request), d['start'], d['end'], d.get('department'))
        payload = [{
            'year': r['year'],
            'week': r['week'],
            'total_rostered_hours': float(r['total_rostered_hours'] or 0),
            'shifts_count': r['shifts_count'],
            'unique_staff': r['unique_staff'],
        } for r in rows]
        return Response(WeeklyTotalsRowSerializer(payload, many=True).data)

    @action(detail=False, methods=['get'], url_path='weekly-by-department')
    def weekly_by_department(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = PeriodQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        d = params.validated_data

        rows = RA.weekly_by_department(self._hotel(hotel_slug, request), d['start'], d['end'])
        payload = [{
            'year': r['year'],
            'week': r['week'],
            'department': r['department'],
            'total_rostered_hours': float(r['total_rostered_hours'] or 0),
            'shifts_count': r['shifts_count'],
            'unique_staff': r['unique_staff'],
        } for r in rows]
        return Response(WeeklyDepartmentRowSerializer(payload, many=True).data)

    @action(detail=False, methods=['get'], url_path='weekly-by-staff')
    def weekly_by_staff(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = PeriodQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        d = params.validated_data

        rows = RA.weekly_by_staff(self._hotel(hotel_slug, request), d['start'], d['end'], d.get('department'))
        payload = [{
            'year': r['year'],
            'week': r['week'],
            'staff_id': r['staff_id'],
            'first_name': r['staff__first_name'],
            'last_name': r['staff__last_name'],
            'department': r['department'],
            'total_rostered_hours': float(r['total_rostered_hours'] or 0),
            'shifts_count': r['shifts_count'],
        } for r in rows]
        return Response(WeeklyStaffRowSerializer(payload, many=True).data)
