# attendance/analytics_roster.py
from django.db.models import Sum, Count, Avg
from .models import StaffRoster


class RosterOnlyAnalytics:
    @staticmethod
    def staff_totals(hotel, start, end, department=None):
        qs = StaffRoster.objects.filter(
            hotel=hotel,
            shift_date__range=[start, end]
        )
        if department:
            qs = qs.filter(department=department)

        return qs.values(
            'staff_id',
            'staff__first_name',
            'staff__last_name',
            'department'
        ).annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            avg_shift_length=Avg('expected_hours')
        ).order_by('department', 'staff__last_name')

    @staticmethod
    def department_totals(hotel, start, end):
        qs = StaffRoster.objects.filter(
            hotel=hotel,
            shift_date__range=[start, end]
        )

        return qs.values('department').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            avg_shift_length=Avg('expected_hours'),
            unique_staff=Count('staff', distinct=True)
        ).order_by('department')

    @staticmethod
    def kpis(hotel, start, end):
        qs = StaffRoster.objects.filter(
            hotel=hotel,
            shift_date__range=[start, end]
        )
        return qs.aggregate(
            total_rostered_hours=Sum('expected_hours'),
            total_shifts=Count('id'),
            avg_shift_length=Avg('expected_hours'),
            unique_staff=Count('staff', distinct=True)
        )
