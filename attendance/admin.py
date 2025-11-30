from django.contrib import admin
from django.utils.html import format_html
from dal import autocomplete
from django import forms

from .models import (
    StaffFace, ClockLog, RosterPeriod, StaffRoster,
    StaffAvailability, ShiftTemplate, RosterRequirement,
    ShiftLocation, DailyPlan, DailyPlanEntry, RosterAuditLog,
    FaceAuditLog,
)

# ──────────────── Face Recognition Admin ──────────────── #

@admin.register(StaffFace)
class StaffFaceAdmin(admin.ModelAdmin):
    list_display = ('staff', 'hotel', 'created_at', 'image_preview')
    list_filter = ('hotel',)
    search_fields = ('staff__first_name', 'staff__last_name', 'hotel__name')
    readonly_fields = ('created_at', 'encoding', 'image_preview')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:100px; max-width:100px;"/>', obj.image.url)
        return "(no image)"
    image_preview.short_description = 'Preview'


# ──────────────── Clock Logs Admin ──────────────── #

@admin.register(ClockLog)
class ClockLogAdmin(admin.ModelAdmin):
    list_display = (
        'staff', 'hotel', 'time_in', 'time_out', 'hours_worked',
        'verified_by_face', 'is_unrostered', 'is_approved', 'auto_clock_out'
    )
    list_filter = (
        'hotel', 'verified_by_face', 'auto_clock_out', 'is_unrostered',
        'is_approved', 'is_rejected'
    )
    search_fields = ('staff__first_name', 'staff__last_name', 'hotel__name')
    readonly_fields = ('time_in', 'hours_worked')
    list_editable = ('is_approved',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hotel', 'staff', 'roster_shift')
        }),
        ('Time Tracking', {
            'fields': ('time_in', 'time_out', 'hours_worked', 'verified_by_face')
        }),
        ('Approval & Status', {
            'fields': (
                'is_unrostered', 'is_approved', 'is_rejected',
                'auto_clock_out', 'location_note'
            )
        }),
        ('Warning Flags', {
            'fields': (
                'break_warning_sent', 'overtime_warning_sent',
                'hard_limit_warning_sent', 'long_session_ack_mode'
            ),
            'classes': ('collapse',)
        }),
    )


# ──────────────── Shift Location Admin ──────────────── #

@admin.register(ShiftLocation)
class ShiftLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'color_swatch')
    list_filter = ('hotel',)
    search_fields = ('name', 'hotel__name')

    def color_swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:16px;height:16px;'
            'border:1px solid #ccc;background:{};margin-right:6px;"></span>{}',
            obj.color, obj.color
        )
    color_swatch.short_description = "Color"


# ──────────────── Staff Roster Admin with Autocomplete ──────────────── #

class StaffRosterForm(forms.ModelForm):
    class Meta:
        model = StaffRoster
        fields = '__all__' 
@admin.register(StaffRoster)
class StaffRosterAdmin(admin.ModelAdmin):
    form = StaffRosterForm
    list_display = (
        'staff', 'hotel', 'department', 'location', 'period',
        'shift_date', 'shift_start', 'shift_end',
        'shift_type', 'is_split_shift', 'expected_hours', 'approved_by'
    )
    list_filter = (
        'hotel', 'department', 'location', 'period',
        'shift_type', 'is_night_shift', 'is_split_shift'
    )
    search_fields = ('staff__first_name', 'staff__last_name', 'notes')
    ordering = ('-shift_date', 'shift_start')
    date_hierarchy = 'shift_date'
    list_select_related = ('staff', 'department', 'location', 'period', 'approved_by')
    
    fieldsets = (
        ('Assignment', {
            'fields': (
                'hotel', 'staff', 'department', 'location', 'period'
            )
        }),
        ('Shift Details', {
            'fields': (
                'shift_date', ('shift_start', 'shift_end'),
                ('break_start', 'break_end'),
                'shift_type', 'is_split_shift', 'is_night_shift',
                'expected_hours'
            )
        }),
        ('Approval & Notes', {
            'fields': ('approved_by', 'notes')
        }),
    )


# ──────────────── Other Admin Models ──────────────── #

@admin.register(RosterPeriod)
class RosterPeriodAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'hotel', 'start_date', 'end_date', 
        'published', 'is_finalized', 'created_by'
    )
    list_filter = ('hotel', 'published', 'is_finalized')
    search_fields = ('title', 'hotel__name')
    readonly_fields = ('finalized_by', 'finalized_at')
    
    fieldsets = (
        ('Period Information', {
            'fields': ('hotel', 'title', 'start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('published', 'created_by')
        }),
        ('Finalization', {
            'fields': ('is_finalized', 'finalized_by', 'finalized_at'),
            'classes': ('collapse',),
            'description': 'Once finalized, related shifts and clock logs are locked'
        }),
    )


@admin.register(StaffAvailability)
class StaffAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('staff', 'date', 'available', 'reason')
    list_filter = ('available', 'date')
    search_fields = ('staff__first_name', 'staff__last_name')


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'start_time', 'end_time', 'is_night')
    list_filter = ('hotel', 'is_night')
    search_fields = ('name',)


@admin.register(RosterRequirement)
class RosterRequirementAdmin(admin.ModelAdmin):
    list_display = ('department', 'role', 'date', 'required_count')
    list_filter = ('department', 'role', 'date')
    search_fields = ('role', 'department')


# ──────────────── Daily Plan Admin ──────────────── #

class DailyPlanEntryInline(admin.TabularInline):
    model = DailyPlanEntry
    extra = 1  # number of empty forms
    autocomplete_fields = ['staff', 'location', 'roster']
    fields = ['staff', 'department', 'location', 'notes', 'roster', 'shift_start', 'shift_end']  # include department here
    readonly_fields = ['department', 'shift_start', 'shift_end']  # make it read-only
    ordering = ['location__name', 'staff__last_name', 'staff__first_name']


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'date', 'created_at', 'updated_at')
    list_filter = ('hotel', 'date')
    search_fields = ('hotel__name',)
    date_hierarchy = 'date'
    inlines = [DailyPlanEntryInline]


# ──────────────── Roster Audit Log Admin ──────────────── #

@admin.register(RosterAuditLog)
class RosterAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'performed_by', 'operation_type', 'hotel', 'affected_shifts_count',
        'success', 'timestamp'
    )
    list_filter = (
        'hotel', 'operation_type', 'success', 'timestamp'
    )
    search_fields = (
        'performed_by__first_name', 'performed_by__last_name',
        'hotel__name', 'error_message'
    )
    readonly_fields = (
        'performed_by', 'operation_type', 'hotel', 'affected_shifts_count',
        'source_period', 'target_period', 'roster_shift', 'affected_staff',
        'operation_details', 'success', 'error_message', 'timestamp'
    )
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Operation Details', {
            'fields': (
                'performed_by', 'operation_type', 'hotel',
                'affected_shifts_count', 'success'
            )
        }),
        ('Period Operations', {
            'fields': ('source_period', 'target_period'),
            'classes': ('collapse',)
        }),
        ('Shift Operations', {
            'fields': ('roster_shift', 'affected_staff'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('operation_details', 'error_message', 'timestamp'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Audit logs should not be manually created
    
    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs should not be deleted