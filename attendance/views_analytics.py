# attendance/views_analytics.py
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status
from .serializers_analytics import (
    PeriodQuerySerializer,
    RosterKpiSerializer,
    DepartmentRosterAnalyticsRowSerializer,
    StaffRosterAnalyticsRowSerializer,
    DailyTotalsRowSerializer,
    DailyDepartmentRowSerializer,
    DailyStaffRowSerializer,
    WeeklyTotalsRowSerializer,
    WeeklyDepartmentRowSerializer,
    WeeklyStaffRowSerializer,
)
from hotel.models import Hotel
from .analytics_roster import RosterAnalytics


class RosterAnalyticsViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def _hotel(self, hotel_slug):
        return get_object_or_404(Hotel, slug=hotel_slug)

    def _validate_period(self, request):
        serializer = PeriodQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    @action(detail=False, methods=['get'], url_path='kpis')
    def kpis(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = self._validate_period(request)

        hotel = self._hotel(hotel_slug)
        kpi_data = RosterAnalytics.kpis(hotel, params['start'], params['end'], params.get('department'))
        
        response_data = {
            'total_rostered_hours': float(kpi_data.get('total_rostered_hours') or 0),
            'total_shifts': int(kpi_data.get('total_shifts') or 0),
            'avg_shift_length': float(kpi_data.get('avg_shift_length') or 0),
            'unique_staff': int(kpi_data.get('unique_staff') or 0),
        }
        return Response(RosterKpiSerializer(response_data).data)

    @action(detail=False, methods=['get'], url_path='department-summary')
    def department_summary(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = self._validate_period(request)

        hotel = self._hotel(hotel_slug)
        data = RosterAnalytics.department_totals(hotel, params['start'], params['end'])
        return Response(DepartmentRosterAnalyticsRowSerializer(data, many=True).data)

    @action(detail=False, methods=['get'], url_path='staff-summary')
    def staff_summary(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = self._validate_period(request)

        hotel = self._hotel(hotel_slug)
        data = RosterAnalytics.staff_totals(hotel, params['start'], params['end'], params.get('department'))
        return Response(StaffRosterAnalyticsRowSerializer(data, many=True).data)

    @action(detail=False, methods=['get'], url_path='daily-totals')
    def daily_totals(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = self._validate_period(request)

        hotel = self._hotel(hotel_slug)
        data = RosterAnalytics.daily_totals(hotel, params['start'], params['end'], params.get('department'))
        return Response(DailyTotalsRowSerializer(data, many=True).data)

    @action(detail=False, methods=['get'], url_path='daily-by-department')
    def daily_by_department(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = self._validate_period(request)

        hotel = self._hotel(hotel_slug)
        data = RosterAnalytics.daily_by_department(hotel, params['start'], params['end'])
        return Response(DailyDepartmentRowSerializer(data, many=True).data)

    @action(detail=False, methods=['get'], url_path='daily-by-staff')
    def daily_by_staff(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = self._validate_period(request)

        hotel = self._hotel(hotel_slug)
        data = RosterAnalytics.daily_by_staff(hotel, params['start'], params['end'], params.get('department'))
        return Response(DailyStaffRowSerializer(data, many=True).data)

    @action(detail=False, methods=['get'], url_path='weekly-totals')
    def weekly_totals(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = self._validate_period(request)

        hotel = self._hotel(hotel_slug)
        data = RosterAnalytics.weekly_totals(hotel, params['start'], params['end'], params.get('department'))
        return Response(WeeklyTotalsRowSerializer(data, many=True).data)

    @action(detail=False, methods=['get'], url_path='weekly-by-department')
    def weekly_by_department(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = self._validate_period(request)

        hotel = self._hotel(hotel_slug)
        data = RosterAnalytics.weekly_by_department(hotel, params['start'], params['end'])
        return Response(WeeklyDepartmentRowSerializer(data, many=True).data)

    @action(detail=False, methods=['get'], url_path='weekly-by-staff')
    def weekly_by_staff(self, request, *args, **kwargs):
        hotel_slug = kwargs.get('hotel_slug')
        params = self._validate_period(request)

        hotel = self._hotel(hotel_slug)
        data = RosterAnalytics.weekly_by_staff(hotel, params['start'], params['end'], params.get('department'))
        return Response(WeeklyStaffRowSerializer(data, many=True).data)
