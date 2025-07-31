from django.contrib import admin
from django.utils.html import format_html
from dal import autocomplete
from django import forms

from .models import (
    StaffFace, ClockLog, RosterPeriod, StaffRoster,
    StaffAvailability, ShiftTemplate, RosterRequirement,
    ShiftLocation,DailyPlan, DailyPlanEntry,
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
        widgets = {
            'staff': autocomplete.ModelSelect2(url='staff-autocomplete'),
            'period': autocomplete.ModelSelect2(url='rosterperiod-autocomplete'),
            # If you decide to add an autocomplete endpoint for locations:
            # 'location': autocomplete.ModelSelect2(url='shiftlocation-autocomplete'),
        }

@admin.register(StaffRoster)
class StaffRosterAdmin(admin.ModelAdmin):
    form = StaffRosterForm
    list_display = (
        'staff', 'hotel', 'department', 'location',  # 👈 location shown
        'shift_date', 'shift_start', 'shift_end',
        'shift_type', 'is_split_shift', 'expected_hours'
    )
    list_filter = (
        'hotel', 'department', 'location',            # 👈 filter by location
        'shift_type', 'is_night_shift', 'is_split_shift'
    )
    search_fields = ('staff__first_name', 'staff__last_name', 'notes')
    ordering = ('-shift_date', 'shift_start')
    date_hierarchy = 'shift_date'
    fieldsets = (
        (None, {
            'fields': (
                'hotel', 'staff', 'department', 'location', 'period',  # 👈 location here
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

    list_display = ('hotel', 'date', 'created_at', 'updated_at')
    list_filter = ('hotel', 'date')
    search_fields = ('hotel__name',)
    date_hierarchy = 'date'
    inlines = [DailyPlanEntryInline]