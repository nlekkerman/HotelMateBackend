"""
Modern, comprehensive filtering system for staff room booking management.

Single source of truth for all booking filters. Replaces legacy scattered filtering logic.
"""
import django_filters
from django import forms
from django.db import models
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from hotel.models import RoomBooking
from rooms.models import RoomType, Room
from hotel.utils.hotel_time import (
    hotel_today, hotel_date_range_utc, hotel_day_range_utc,
    hotel_checkout_deadline_utc, is_overdue_checkout
)


class StaffRoomBookingFilter(django_filters.FilterSet):
    """
    Comprehensive FilterSet for staff room booking management.
    
    Provides all filtering capabilities in a single, testable, maintainable class.
    No legacy parameters, no backward compatibility.
    """
    
    # A) OPERATIONAL BUCKETS
    bucket = django_filters.ChoiceFilter(
        choices=[
            ('arrivals', 'Arrivals'),
            ('in_house', 'In House'),
            ('departures', 'Departures'),
            ('pending', 'Pending'),
            ('checked_out', 'Checked Out'),
            ('cancelled', 'Cancelled'),
            ('expired', 'Expired'),
            ('no_show', 'No Show'),
            ('overdue_checkout', 'Overdue Checkout'),
        ],
        method='filter_bucket',
        help_text="Operational status buckets for hotel management"
    )
    
    # B) DATE FILTERING
    date_mode = django_filters.ChoiceFilter(
        choices=[
            ('stay', 'Stay Dates (check_in/check_out)'),
            ('created', 'Created Date'),
            ('updated', 'Updated Date'),
            ('checked_in', 'Checked In Date'),
            ('checked_out', 'Checked Out Date'),
        ],
        method='filter_date_range',
        help_text="Date filtering axis"
    )
    
    date_from = django_filters.DateFilter(
        method='filter_date_range',
        help_text="Start date (YYYY-MM-DD)"
    )
    
    date_to = django_filters.DateFilter(
        method='filter_date_range', 
        help_text="End date (YYYY-MM-DD)"
    )
    
    # C) TEXT SEARCH
    q = django_filters.CharFilter(
        method='filter_search',
        help_text="Search across booking ID, guest names, contact info, room details"
    )
    
    # D) ROOM & ASSIGNMENT
    assigned = django_filters.BooleanFilter(
        field_name='assigned_room',
        lookup_expr='isnull',
        exclude=True,
        help_text="Filter by room assignment status"
    )
    
    room_id = django_filters.NumberFilter(
        field_name='assigned_room__id',
        help_text="Filter by specific room ID"
    )
    
    room_number = django_filters.CharFilter(
        method='filter_room_number',
        help_text="Filter by room number"
    )
    
    room_type = django_filters.CharFilter(
        method='filter_room_type',
        help_text="Filter by room type (code or ID)"
    )
    
    # E) PARTY SIZE
    adults = django_filters.NumberFilter(
        field_name='adults',
        help_text="Filter by number of adults"
    )
    
    children = django_filters.NumberFilter(
        field_name='children', 
        help_text="Filter by number of children"
    )
    
    party_size_min = django_filters.NumberFilter(
        method='filter_party_size_min',
        help_text="Minimum total party size (adults + children)"
    )
    
    party_size_max = django_filters.NumberFilter(
        method='filter_party_size_max',
        help_text="Maximum total party size (adults + children)"
    )
    
    # F) PRECHECKIN STATUS
    precheckin = django_filters.ChoiceFilter(
        choices=[
            ('complete', 'Complete'),
            ('pending', 'Pending'),
            ('none', 'Not Required/None'),
        ],
        method='filter_precheckin',
        help_text="Pre-checkin completion status"
    )
    
    # G) FINANCIAL (only if fields exist)
    amount_min = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte',
        help_text="Minimum booking amount"
    )
    
    amount_max = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte', 
        help_text="Maximum booking amount"
    )
    
    currency = django_filters.CharFilter(
        field_name='currency',
        help_text="Filter by currency code"
    )
    
    payment_status = django_filters.CharFilter(
        field_name='payment_status',
        help_text="Filter by payment status"
    )
    
    # H) STAFF WORKFLOW
    seen = django_filters.BooleanFilter(
        field_name='staff_seen_at',
        lookup_expr='isnull',
        exclude=True,
        help_text="Filter by staff seen status"
    )
    
    seen_by_staff_id = django_filters.NumberFilter(
        field_name='staff_seen_by__id',
        help_text="Filter by specific staff member who marked as seen"
    )
    
    # I) STATUS (explicit)
    status = django_filters.CharFilter(
        method='filter_status_list',
        help_text="Comma-separated list of statuses (e.g., CONFIRMED,IN_HOUSE)"
    )
    
    class Meta:
        model = RoomBooking
        fields = []  # All filtering handled by custom methods
    
    def __init__(self, *args, **kwargs):
        """Initialize with hotel context for timezone-aware filtering."""
        self.hotel = kwargs.pop('hotel', None)
        super().__init__(*args, **kwargs)
        
        if not self.hotel:
            raise ValueError("StaffRoomBookingFilter requires 'hotel' parameter")
    
    def filter_bucket(self, queryset, name, value):
        """Filter by operational buckets using reality-based logic."""
        if not value:
            return queryset
            
        today = hotel_today(self.hotel)
        
        # Get date range for bucket filtering
        date_from = self.form.cleaned_data.get('date_from', today)
        date_to = self.form.cleaned_data.get('date_to', today)
        
        if value == 'arrivals':
            # Check-in within date range, not yet checked in, confirmed-ish status
            return queryset.filter(
                check_in__gte=date_from,
                check_in__lte=date_to,
                checked_in_at__isnull=True,
                status__in=['CONFIRMED', 'PENDING_APPROVAL']
            )
            
        elif value == 'in_house':
            # Checked in but not checked out
            return queryset.filter(
                checked_in_at__isnull=False,
                checked_out_at__isnull=True
            )
            
        elif value == 'departures':
            # Check-out within date range, not yet checked out
            return queryset.filter(
                check_out__gte=date_from,
                check_out__lte=date_to,
                checked_out_at__isnull=True,
                checked_in_at__isnull=False  # Must be checked in
            )
            
        elif value == 'overdue_checkout':
            # Past checkout deadline, checked in, not checked out
            overdue_bookings = []
            for booking in queryset.filter(
                checked_in_at__isnull=False,
                checked_out_at__isnull=True
            ):
                if is_overdue_checkout(self.hotel, booking.check_out, booking.checked_out_at):
                    overdue_bookings.append(booking.id)
            
            return queryset.filter(id__in=overdue_bookings)
            
        elif value == 'pending':
            # Awaiting payment or approval, not checked in
            return queryset.filter(
                status__in=['PENDING_PAYMENT', 'PENDING_APPROVAL'],
                checked_in_at__isnull=True
            )
            
        elif value == 'checked_out':
            # Actually checked out or completed
            return queryset.filter(
                Q(checked_out_at__isnull=False) | Q(status='COMPLETED')
            )
            
        elif value == 'cancelled':
            return queryset.filter(status='CANCELLED')
            
        elif value == 'expired':
            return queryset.filter(status='EXPIRED')
            
        elif value == 'no_show':
            return queryset.filter(status='NO_SHOW')
        
        return queryset
    
    def filter_date_range(self, queryset, name, value):
        """Filter by date range based on date_mode axis."""
        date_mode = self.form.cleaned_data.get('date_mode', 'stay')
        date_from = self.form.cleaned_data.get('date_from')
        date_to = self.form.cleaned_data.get('date_to')
        
        if not (date_from or date_to):
            return queryset
        
        if date_mode == 'stay':
            # Use DateFields directly (check_in, check_out)
            if date_from:
                queryset = queryset.filter(check_in__gte=date_from)
            if date_to:
                queryset = queryset.filter(check_out__lte=date_to)
                
        else:
            # Convert hotel dates to UTC datetime windows for datetime fields
            if date_from and date_to:
                start_utc, end_utc = hotel_date_range_utc(self.hotel, date_from, date_to)
            elif date_from:
                start_utc, end_utc = hotel_day_range_utc(self.hotel, date_from)
            elif date_to:
                start_utc, end_utc = hotel_day_range_utc(self.hotel, date_to)
            else:
                return queryset
            
            if date_mode == 'created':
                queryset = queryset.filter(
                    created_at__gte=start_utc,
                    created_at__lte=end_utc
                )
            elif date_mode == 'updated':
                queryset = queryset.filter(
                    updated_at__gte=start_utc,
                    updated_at__lte=end_utc
                )
            elif date_mode == 'checked_in':
                queryset = queryset.filter(
                    checked_in_at__gte=start_utc,
                    checked_in_at__lte=end_utc
                )
            elif date_mode == 'checked_out':
                queryset = queryset.filter(
                    checked_out_at__gte=start_utc,
                    checked_out_at__lte=end_utc
                )
        
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Comprehensive text search across all relevant fields."""
        if not value or not value.strip():
            return queryset
        
        search_terms = Q()
        
        # Booking identifiers
        search_terms |= Q(booking_id__icontains=value)
        search_terms |= Q(confirmation_number__icontains=value)
        
        # Primary guest
        search_terms |= Q(primary_first_name__icontains=value)
        search_terms |= Q(primary_last_name__icontains=value)
        search_terms |= Q(primary_email__icontains=value)
        search_terms |= Q(primary_phone__icontains=value)
        
        # Booker (if different from primary guest)
        search_terms |= Q(booker_first_name__icontains=value)
        search_terms |= Q(booker_last_name__icontains=value)
        search_terms |= Q(booker_email__icontains=value)
        search_terms |= Q(booker_phone__icontains=value)
        
        # Room information
        search_terms |= Q(assigned_room__room_number__icontains=value)
        search_terms |= Q(room_type__name__icontains=value)
        search_terms |= Q(room_type__code__icontains=value)
        
        return queryset.filter(search_terms)
    
    def filter_room_number(self, queryset, name, value):
        """Filter by room number (hotel-scoped)."""
        if not value:
            return queryset
        
        return queryset.filter(
            assigned_room__room_number=value,
            assigned_room__hotel=self.hotel
        )
    
    def filter_room_type(self, queryset, name, value):
        """Filter by room type code or ID (hotel-scoped)."""
        if not value:
            return queryset
        
        try:
            # Try as room type ID first
            if value.isdigit():
                room_type = RoomType.objects.get(id=int(value), hotel=self.hotel)
            else:
                # Try as room type code
                room_type = RoomType.objects.get(code=value, hotel=self.hotel)
            
            return queryset.filter(room_type=room_type)
            
        except RoomType.DoesNotExist:
            # Invalid room type for this hotel, return empty
            return queryset.none()
    
    def filter_party_size_min(self, queryset, name, value):
        """Filter by minimum total party size."""
        if value is None:
            return queryset
        
        return queryset.annotate(
            total_guests=models.F('adults') + models.F('children')
        ).filter(total_guests__gte=value)
    
    def filter_party_size_max(self, queryset, name, value):
        """Filter by maximum total party size.""" 
        if value is None:
            return queryset
        
        return queryset.annotate(
            total_guests=models.F('adults') + models.F('children')
        ).filter(total_guests__lte=value)
    
    def filter_precheckin(self, queryset, name, value):
        """Filter by precheckin status."""
        if not value:
            return queryset
        
        if value == 'complete':
            return queryset.filter(precheckin_submitted_at__isnull=False)
        elif value == 'pending':
            # Required but not completed
            return queryset.filter(
                precheckin_submitted_at__isnull=True
                # Add additional logic here if there's a "precheckin required" field
            )
        elif value == 'none':
            # Not required or no precheckin system
            return queryset.filter(precheckin_submitted_at__isnull=True)
        
        return queryset
    
    def filter_status_list(self, queryset, name, value):
        """Filter by comma-separated list of statuses."""
        if not value:
            return queryset
        
        status_list = [status.strip().upper() for status in value.split(',')]
        return queryset.filter(status__in=status_list)
    
    def get_bucket_counts(self, base_queryset):
        """
        Get counts for all operational buckets.
        
        Reuses the same bucket filtering logic for consistency.
        """
        counts = {}
        
        bucket_choices = [choice[0] for choice in self.filters['bucket'].extra['choices']]
        
        for bucket in bucket_choices:
            # Create a temporary filter instance to get bucket-filtered queryset
            temp_data = self.form.data.copy()
            temp_data['bucket'] = bucket
            
            temp_form = self.form.__class__(temp_data)
            if temp_form.is_valid():
                temp_filter = self.__class__(
                    temp_form.cleaned_data, 
                    queryset=base_queryset,
                    hotel=self.hotel
                )
                counts[bucket] = temp_filter.qs.count()
            else:
                counts[bucket] = 0
        
        return counts


def validate_ordering(ordering: str, allowed_orderings: List[str]) -> str:
    """
    Validate and return safe ordering parameter.
    
    Args:
        ordering: Requested ordering parameter
        allowed_orderings: List of allowed ordering options
        
    Returns:
        str: Validated ordering parameter
        
    Raises:
        ValueError: If ordering is not in allowed list
    """
    if ordering not in allowed_orderings:
        raise ValueError(f"Invalid ordering: {ordering}. Allowed: {', '.join(allowed_orderings)}")
    
    return ordering


def get_allowed_orderings() -> List[str]:
    """Get list of allowed ordering parameters."""
    return [
        'check_in', '-check_in',
        'check_out', '-check_out', 
        'created_at', '-created_at',
        'updated_at', '-updated_at',
        'booking_id', '-booking_id',
        'status', '-status',
        'total_amount', '-total_amount'
    ]