from django.contrib import admin
from .models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'first_name', 
        'last_name', 
        'department', 
        'role', 
        'position', 
        'email', 
        'phone_number', 
        'is_active',
        'is_on_duty', 
    )
    list_filter = (
        'department', 
        'role', 
        'is_active',
        'is_on_duty',
    )
    search_fields = (
        'first_name', 
        'last_name', 
        'email', 
        'phone_number', 
        'position',
        'user__username'
    )
    ordering = (
        'department', 
        'last_name'
    )
    list_editable = (
        'is_active', 
        'role',
        'is_on_duty',
    )
    readonly_fields = (
        # add 'email', 'phone_number' if you want them read-only
    )

    fieldsets = (
        (None, {
            'fields': (
                ('user', 'first_name', 'last_name'),
                ('email', 'phone_number'),
                ('department', 'role', 'position'),
                'is_active', 'is_on_duty'
            )
        }),
    )

    actions = ['mark_as_inactive','mark_as_on_duty', 'mark_as_off_duty']

    @admin.action(description="Mark selected staff as inactive")
    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)
    
    @admin.action(description="Mark selected staff as ON duty")
    def mark_as_on_duty(self, request, queryset):
        queryset.update(is_on_duty=True)

    @admin.action(description="Mark selected staff as OFF duty")
    def mark_as_off_duty(self, request, queryset):
        queryset.update(is_on_duty=False)
