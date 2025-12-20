"""
Housekeeping Admin

Django admin configuration for housekeeping models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import HousekeepingTask, RoomStatusEvent


@admin.register(HousekeepingTask)
class HousekeepingTaskAdmin(admin.ModelAdmin):
    """Admin interface for housekeeping tasks"""
    
    list_display = (
        'task_summary',
        'hotel_name',
        'room_link',
        'task_type',
        'status_badge',
        'priority_badge',
        'assigned_to_link',
        'created_at',
        'is_overdue_indicator'
    )
    
    list_filter = (
        'hotel',
        'task_type',
        'status',
        'priority',
        'created_at',
    )
    
    search_fields = (
        'room__room_number',
        'hotel__name',
        'assigned_to__first_name',
        'assigned_to__last_name',
        'created_by__first_name',
        'created_by__last_name',
        'note',
    )
    
    date_hierarchy = 'created_at'
    
    ordering = ('-priority', '-created_at')
    
    readonly_fields = (
        'created_at',
        'started_at',
        'completed_at',
        'is_overdue',
    )
    
    fieldsets = (
        ('Task Information', {
            'fields': (
                ('hotel', 'room', 'booking'),
                ('task_type', 'status', 'priority'),
                'note'
            )
        }),
        ('Assignment', {
            'fields': (
                ('assigned_to', 'created_by'),
            )
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'started_at', 'completed_at'),
                'is_overdue'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def task_summary(self, obj):
        """Display task summary with icon"""
        icons = {
            'TURNOVER': '🔄',
            'STAYOVER': '🏠',
            'INSPECTION': '🔍',
            'DEEP_CLEAN': '🧹',
            'AMENITY': '🛎️',
        }
        icon = icons.get(obj.task_type, '📋')
        return f"{icon} {obj.get_task_type_display()}"
    task_summary.short_description = 'Task'
    
    def hotel_name(self, obj):
        """Display hotel name"""
        return obj.hotel.name
    hotel_name.short_description = 'Hotel'
    hotel_name.admin_order_field = 'hotel__name'
    
    def room_link(self, obj):
        """Display room with link to room admin"""
        if obj.room:
            url = reverse('admin:rooms_room_change', args=[obj.room.pk])
            return format_html(
                '<a href="{}" target="_blank">Room {}</a>',
                url,
                obj.room.room_number
            )
        return '-'
    room_link.short_description = 'Room'
    room_link.admin_order_field = 'room__room_number'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'OPEN': '#17a2b8',       # info blue
            'IN_PROGRESS': '#ffc107', # warning yellow
            'DONE': '#28a745',       # success green
            'CANCELLED': '#6c757d',  # secondary gray
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def priority_badge(self, obj):
        """Display priority with color coding"""
        colors = {
            'HIGH': '#dc3545',  # danger red
            'MED': '#ffc107',   # warning yellow
            'LOW': '#28a745',   # success green
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'
    
    def assigned_to_link(self, obj):
        """Display assigned staff with link"""
        if obj.assigned_to:
            url = reverse('admin:staff_staff_change', args=[obj.assigned_to.pk])
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                url,
                obj.assigned_to.get_full_name()
            )
        return '<span style="color: #6c757d;">Unassigned</span>'
    assigned_to_link.short_description = 'Assigned To'
    assigned_to_link.admin_order_field = 'assigned_to__last_name'
    assigned_to_link.allow_tags = True
    
    def is_overdue_indicator(self, obj):
        """Display overdue indicator"""
        if obj.is_overdue:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠️ OVERDUE</span>'
            )
        return '✅'
    is_overdue_indicator.short_description = 'SLA Status'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'hotel', 'room', 'room__room_type', 'assigned_to', 'created_by', 'booking'
        )


@admin.register(RoomStatusEvent)
class RoomStatusEventAdmin(admin.ModelAdmin):
    """Admin interface for room status audit events"""
    
    list_display = (
        'event_summary',
        'hotel_name',
        'room_link',
        'status_transition',
        'source_badge',
        'changed_by_link',
        'created_at',
    )
    
    list_filter = (
        'hotel',
        'source',
        'to_status',
        'from_status',
        'created_at',
    )
    
    search_fields = (
        'room__room_number',
        'hotel__name',
        'changed_by__first_name',
        'changed_by__last_name',
        'note',
        'from_status',
        'to_status',
    )
    
    date_hierarchy = 'created_at'
    
    ordering = ('-created_at',)
    
    readonly_fields = (
        'hotel',
        'room',
        'from_status',
        'to_status',
        'changed_by',
        'source',
        'note',
        'created_at',
    )
    
    fieldsets = (
        ('Event Information', {
            'fields': (
                ('hotel', 'room'),
                ('from_status', 'to_status'),
                ('changed_by', 'source'),
                'created_at'
            )
        }),
        ('Notes', {
            'fields': ('note',),
        }),
    )
    
    def has_add_permission(self, request):
        """Disable adding events through admin (immutable audit trail)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing events (immutable audit trail)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting events (immutable audit trail)"""
        return False
    
    def event_summary(self, obj):
        """Display event summary with timestamp"""
        return f"Status Change - {obj.created_at.strftime('%m/%d %H:%M')}"
    event_summary.short_description = 'Event'
    
    def hotel_name(self, obj):
        """Display hotel name"""
        return obj.hotel.name
    hotel_name.short_description = 'Hotel'
    hotel_name.admin_order_field = 'hotel__name'
    
    def room_link(self, obj):
        """Display room with link to room admin"""
        if obj.room:
            url = reverse('admin:rooms_room_change', args=[obj.room.pk])
            return format_html(
                '<a href="{}" target="_blank">Room {}</a>',
                url,
                obj.room.room_number
            )
        return '-'
    room_link.short_description = 'Room'
    room_link.admin_order_field = 'room__room_number'
    
    def status_transition(self, obj):
        """Display status transition with arrow"""
        return format_html(
            '<span style="font-family: monospace;">{} → {}</span>',
            obj.from_status,
            obj.to_status
        )
    status_transition.short_description = 'Transition'
    
    def source_badge(self, obj):
        """Display source with color coding"""
        colors = {
            'HOUSEKEEPING': '#17a2b8',     # info blue
            'FRONT_DESK': '#28a745',       # success green
            'SYSTEM': '#6c757d',           # secondary gray
            'MANAGER_OVERRIDE': '#dc3545', # danger red
        }
        color = colors.get(obj.source, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_source_display()
        )
    source_badge.short_description = 'Source'
    source_badge.admin_order_field = 'source'
    
    def changed_by_link(self, obj):
        """Display staff who made the change"""
        if obj.changed_by:
            url = reverse('admin:staff_staff_change', args=[obj.changed_by.pk])
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                url,
                obj.changed_by.get_full_name()
            )
        return '<span style="color: #6c757d;">System</span>'
    changed_by_link.short_description = 'Changed By'
    changed_by_link.admin_order_field = 'changed_by__last_name'
    changed_by_link.allow_tags = True
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'hotel', 'room', 'changed_by'
        )


# Admin site customization
admin.site.site_header = "HotelMate Housekeeping Admin"
admin.site.site_title = "Housekeeping Admin"
admin.site.index_title = "Housekeeping Management"
