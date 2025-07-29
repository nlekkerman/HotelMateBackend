from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import ExtractWeek, ExtractYear
from .models import StaffRoster
from django.db.models import Sum, Count, Avg, DecimalField
from django.db.models.functions import Coalesce
class RosterAnalytics:
    # Staff totals - alias nested fields to flat keys expected by serializers
    @staticmethod
    def staff_totals(hotel, start, end, department=None):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department__slug=department)

        return qs.values('staff_id').annotate(
            first_name=F('staff__first_name'),
            last_name=F('staff__last_name'),
            department__id=F('department__id'),
            department_name=F('department__name'),
            department_slug=F('department__slug'),
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            avg_shift_length=Avg('expected_hours'),
        ).order_by('department_name', 'last_name')

    # Department totals - renaming applied via annotate; avoid collision by aliasing department_id as dept_id
    @staticmethod
    def department_totals(hotel, start, end, department=None):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end], department__isnull=False)
        if department:
            qs = qs.filter(department__slug=department)

        return qs.annotate(
            dept_id=F('department__id'),
            department_name=F('department__name'),
            department_slug=F('department__slug'),
        ).values('dept_id', 'department_name', 'department_slug').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            avg_shift_length=Avg('expected_hours'),
            unique_staff=Count('staff', distinct=True),
        ).order_by('department_name')

    # Daily totals - rename shift_date -> date
    @staticmethod
    def daily_totals(hotel, start, end, department=None):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department__slug=department)

        return qs.annotate(date=F('shift_date')).values('date').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
        ).order_by('date')

    # Daily by department
    @staticmethod
    def daily_by_department(hotel, start, end):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end], department__isnull=False)

        return qs.annotate(
            date=F('shift_date'),
            dept_id=F('department__id'),
            department_name=F('department__name'),
            department_slug=F('department__slug'),
        ).values('date', 'dept_id').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            unique_staff=Count('staff', distinct=True),
        ).order_by('date', 'department_name')

    # Daily by staff
    @staticmethod
    def daily_by_staff(hotel, start, end, department=None):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department__slug=department)

        return qs.annotate(
            date=F('shift_date'),
            first_name=F('staff__first_name'),
            last_name=F('staff__last_name'),
            dept_id=F('department__id'),
            department_name=F('department__name'),
            department_slug=F('department__slug'),
        ).values('date', 'staff_id').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
        ).order_by('date', 'department_name', 'last_name')

    # Weekly totals
    @staticmethod
    def weekly_totals(hotel, start, end, department=None):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department__slug=department)

        return qs.annotate(
            year=ExtractYear('shift_date'),
            week=ExtractWeek('shift_date'),
        ).values('year', 'week').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            unique_staff=Count('staff', distinct=True),
        ).order_by('year', 'week')

    # Weekly by department
    @staticmethod
    def weekly_by_department(hotel, start, end):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end], department__isnull=False)

        return qs.annotate(
            year=ExtractYear('shift_date'),
            week=ExtractWeek('shift_date'),
            dept_id=F('department__id'),
            department_name=F('department__name'),
            department_slug=F('department__slug'),
        ).values('year', 'week', 'dept_id').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            unique_staff=Count('staff', distinct=True),
        ).order_by('year', 'week', 'department_name')

    # Weekly by staff
    @staticmethod
    def weekly_by_staff(hotel, start, end, department=None):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department__slug=department)

        return qs.annotate(
            year=ExtractYear('shift_date'),
            week=ExtractWeek('shift_date'),
            first_name=F('staff__first_name'),
            last_name=F('staff__last_name'),
            dept_id=F('department__id'),
            department_name=F('department__name'),
            department_slug=F('department__slug'),
        ).values('year', 'week', 'staff_id').annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
        ).order_by('year', 'week', 'department_name', 'last_name')

    # KPIs method added here to avoid AttributeError
    @staticmethod
    def kpis(hotel, start, end, department=None):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department__slug=department)

        total_hours = qs.aggregate(
            total_hours=Coalesce(Sum('expected_hours'), 0, output_field=DecimalField())
        )['total_hours']
        total_shifts = qs.aggregate(total_shifts=Count('id'))['total_shifts']
        unique_staff = qs.aggregate(unique_staff=Count('staff', distinct=True))['unique_staff']

        avg_shift_length = qs.aggregate(avg_shift_length=Avg('expected_hours'))['avg_shift_length'] or 0

        return {
            'total_rostered_hours': float(total_hours),  # convert Decimal to float if desired
            'total_shifts': total_shifts,
            'unique_staff': unique_staff,
            'avg_shift_length': round(avg_shift_length, 2),
        }

