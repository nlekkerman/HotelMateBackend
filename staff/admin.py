from django.contrib import admin
from .models import Staff

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'hotel',          # show hotel in list
        'first_name', 
        'last_name', 
        'department', 
        'role', 
        'access_level',   # added access level
        'position', 
        'email', 
        'phone_number', 
        'is_active',
        'is_on_duty', 
    )
    list_filter = (
        'hotel',          # filter by hotel
        'department', 
        'role', 
        'access_level',   # added access level filter
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
        'hotel',          # order by hotel too
        'department', 
        'last_name'
    )
    list_editable = (
        'is_active', 
        'role',
        'access_level',   # added access level editable
        'is_on_duty',
    )

    fieldsets = (
        (None, {
            'fields': (
                ('user', 'hotel', 'first_name', 'last_name'),  # add hotel here
                ('email', 'phone_number'),
                ('department', 'role', 'access_level', 'position'),  # added access level here
                'is_active', 'is_on_duty'
            )
        }),
    )

    actions = ['mark_as_inactive', 'mark_as_on_duty', 'mark_as_off_duty']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        hotel = getattr(request, 'hotel', None)
        if hotel:
            return qs.filter(hotel=hotel)
        return qs.none()

    @admin.action(description="Mark selected staff as inactive")
    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)
    
    @admin.action(description="Mark selected staff as ON duty")
    def mark_as_on_duty(self, request, queryset):
        queryset.update(is_on_duty=True)

    @admin.action(description="Mark selected staff as OFF duty")
    def mark_as_off_duty(self, request, queryset):
        queryset.update(is_on_duty=False)
