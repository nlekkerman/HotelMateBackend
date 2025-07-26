# attendance/analytics.py
from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import TruncDate, ExtractWeek, ExtractYear, Coalesce
from .models import StaffRoster

class RosterAnalytics:
    """
    Pure data aggregations for roster-based analytics.
    Everything returns plain QuerySets/iterables ready for the view to shape.
    """

    # -------------------------
    # PERIOD (generic) SUMMARY
    # -------------------------
    @staticmethod
    def staff_totals(hotel, start, end, department=None):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department=department)

        return qs.values(
            'staff_id', 'staff__first_name', 'staff__last_name', 'department'
        ).annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            avg_shift_length=Avg('expected_hours')
        ).order_by('department', 'staff__last_name')

    @staticmethod
    def department_totals(hotel, start, end):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])

        return qs.values('department').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            avg_shift_length=Avg('expected_hours'),
            unique_staff=Count('staff', distinct=True)
        ).order_by('department')

    @staticmethod
    def kpis(hotel, start, end):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        return qs.aggregate(
            total_rostered_hours=Coalesce(Sum('expected_hours'), 0.0),
            total_shifts=Coalesce(Count('id'), 0),
            avg_shift_length=Coalesce(Avg('expected_hours'), 0.0),
            unique_staff=Coalesce(Count('staff', distinct=True), 0)
        )

    # --------------
    # DAILY LEVEL
    # --------------
    @staticmethod
    def daily_totals(hotel, start, end, department=None):
        """
        Total rostered hours & shifts per day (for charts).
        """
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department=department)

        return qs.values('shift_date').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id')
        ).order_by('shift_date')

    @staticmethod
    def daily_by_department(hotel, start, end):
        """
        Rostered hours per day per department.
        """
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        return qs.values('shift_date', 'department').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            unique_staff=Count('staff', distinct=True)
        ).order_by('shift_date', 'department')

    @staticmethod
    def daily_by_staff(hotel, start, end, department=None):
        """
        Rostered hours per day per staff.
        """
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department=department)

        return qs.values(
            'shift_date', 'staff_id', 'staff__first_name', 'staff__last_name', 'department'
        ).annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id')
        ).order_by('shift_date', 'department', 'staff__last_name')

    # --------------
    # WEEKLY LEVEL
    # --------------
    @staticmethod
    def weekly_totals(hotel, start, end, department=None):
        """
        Total rostered hours per ISO week (year+week).
        """
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department=department)

        return qs.annotate(
            year=ExtractYear('shift_date'),
            week=ExtractWeek('shift_date')
        ).values('year', 'week').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            unique_staff=Count('staff', distinct=True)
        ).order_by('year', 'week')

    @staticmethod
    def weekly_by_department(hotel, start, end):
        """
        Rostered hours per ISO week per department.
        """
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        return qs.annotate(
            year=ExtractYear('shift_date'),
            week=ExtractWeek('shift_date')
        ).values('year', 'week', 'department').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            unique_staff=Count('staff', distinct=True)
        ).order_by('year', 'week', 'department')

    @staticmethod
    def weekly_by_staff(hotel, start, end, department=None):
        """
        Rostered hours per ISO week per staff.
        """
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department=department)

        return qs.annotate(
            year=ExtractYear('shift_date'),
            week=ExtractWeek('shift_date')
        ).values(
            'year', 'week', 'staff_id', 'staff__first_name', 'staff__last_name', 'department'
        ).annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id')
        ).order_by('year', 'week', 'department', 'staff__last_name')
