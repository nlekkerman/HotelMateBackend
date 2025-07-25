from django.contrib import admin
from django.utils.html import format_html
from dal import autocomplete
from django import forms

from .models import (
    StaffFace, ClockLog, RosterPeriod, StaffRoster,
    StaffAvailability, ShiftTemplate, RosterRequirement
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
    list_display = ('staff', 'hotel', 'time_in', 'time_out', 'verified_by_face', 'auto_clock_out')
    list_filter = ('hotel', 'verified_by_face', 'auto_clock_out')
    search_fields = ('staff__first_name', 'staff__last_name', 'hotel__name')
    readonly_fields = ('time_in',)
    fields = ('hotel', 'staff', 'time_in', 'time_out', 'verified_by_face', 'location_note', 'auto_clock_out')


# ──────────────── Staff Roster Admin with Autocomplete ──────────────── #

class StaffRosterForm(forms.ModelForm):
    class Meta:
        model = StaffRoster
        fields = '__all__'
        widgets = {
            'staff': autocomplete.ModelSelect2(url='staff-autocomplete'),
            'period': autocomplete.ModelSelect2(url='rosterperiod-autocomplete'),
        }

@admin.register(StaffRoster)
class StaffRosterAdmin(admin.ModelAdmin):
    form = StaffRosterForm
    list_display = (
        'staff', 'hotel', 'department', 'shift_date', 'shift_start', 'shift_end',
        'shift_type', 'is_split_shift', 'expected_hours'
    )
    list_filter = ('hotel', 'department', 'shift_type', 'is_night_shift', 'is_split_shift')
    search_fields = ('staff__first_name', 'staff__last_name', 'notes')
    ordering = ('-shift_date', 'shift_start')
    date_hierarchy = 'shift_date'
    fieldsets = (
        (None, {
            'fields': (
                'hotel', 'staff', 'department', 'period',
                'shift_date', ('shift_start', 'shift_end'),
                ('break_start', 'break_end'),
                'shift_type', 'is_split_shift', 'is_night_shift',
                'expected_hours', 'notes'
            )
        }),
        ('Approval', {'fields': ('approved_by',)}),
    )


# ──────────────── Other Admin Models ──────────────── #

@admin.register(RosterPeriod)
class RosterPeriodAdmin(admin.ModelAdmin):
    list_display = ('title', 'hotel', 'start_date', 'end_date', 'published')
    list_filter = ('hotel', 'published')
    search_fields = ('title', 'hotel__name')


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
