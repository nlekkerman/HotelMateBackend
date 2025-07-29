# attendance/filters.py
import django_filters
from .models import StaffRoster

class StaffRosterFilter(django_filters.FilterSet):
    department = django_filters.CharFilter(field_name='department__slug', lookup_expr='exact')
    hotel_slug = django_filters.CharFilter(field_name='hotel__slug', lookup_expr='exact')
    
    class Meta:
        model = StaffRoster
        fields = ['department', 'hotel_slug', 'period', 'location']
