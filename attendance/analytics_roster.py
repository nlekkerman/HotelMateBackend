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

        results = qs.values(
            'shift_date',
            'department__id',
            'department__name',
            'department__slug'
        ).annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            unique_staff=Count('staff', distinct=True),
        ).order_by('shift_date', 'department__name')
        
        # Transform to expected format
        return [
            {
                'date': row['shift_date'],
                'dept_id': row['department__id'],
                'department_name': row['department__name'],
                'department_slug': row['department__slug'],
                'total_rostered_hours': row['total_rostered_hours'],
                'shifts_count': row['shifts_count'],
                'unique_staff': row['unique_staff'],
            }
            for row in results
        ]

    # Daily by staff
    @staticmethod
    def daily_by_staff(hotel, start, end, department=None):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department__slug=department)

        results = qs.values(
            'shift_date',
            'staff_id',
            'staff__first_name',
            'staff__last_name',
            'department__id',
            'department__name',
            'department__slug'
        ).annotate(
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
        ).order_by('shift_date', 'department__name', 'staff__last_name')
        
        # Transform to expected format
        return [
            {
                'date': row['shift_date'],
                'staff_id': row['staff_id'],
                'first_name': row['staff__first_name'],
                'last_name': row['staff__last_name'],
                'dept_id': row['department__id'],
                'department_name': row['department__name'],
                'department_slug': row['department__slug'],
                'total_rostered_hours': row['total_rostered_hours'],
                'shifts_count': row['shifts_count'],
            }
            for row in results
        ]

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

        results = qs.values(
            'department__id',
            'department__name', 
            'department__slug'
        ).annotate(
            year=ExtractYear('shift_date'),
            week=ExtractWeek('shift_date'),
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
            unique_staff=Count('staff', distinct=True),
        ).order_by('year', 'week', 'department__name')
        
        # Transform to expected format
        return [
            {
                'year': row['year'],
                'week': row['week'],
                'dept_id': row['department__id'],
                'department_name': row['department__name'],
                'department_slug': row['department__slug'],
                'total_rostered_hours': row['total_rostered_hours'],
                'shifts_count': row['shifts_count'],
                'unique_staff': row['unique_staff'],
            }
            for row in results
        ]

    # Weekly by staff
    @staticmethod
    def weekly_by_staff(hotel, start, end, department=None):
        qs = StaffRoster.objects.filter(hotel=hotel, shift_date__range=[start, end])
        if department:
            qs = qs.filter(department__slug=department)

        results = qs.values(
            'staff_id',
            'staff__first_name',
            'staff__last_name',
            'department__id',
            'department__name',
            'department__slug'
        ).annotate(
            year=ExtractYear('shift_date'),
            week=ExtractWeek('shift_date'),
            total_rostered_hours=Sum('expected_hours'),
            shifts_count=Count('id'),
        ).order_by('year', 'week', 'department__name', 'staff__last_name')
        
        # Transform to expected format
        return [
            {
                'year': row['year'],
                'week': row['week'],
                'staff_id': row['staff_id'],
                'first_name': row['staff__first_name'],
                'last_name': row['staff__last_name'],
                'dept_id': row['department__id'],
                'department_name': row['department__name'],
                'department_slug': row['department__slug'],
                'total_rostered_hours': row['total_rostered_hours'],
                'shifts_count': row['shifts_count'],
            }
            for row in results
        ]

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

