from django.contrib import admin
from .models import Staff, StaffFCMToken

class StaffFCMTokenInline(admin.TabularInline):
    model = StaffFCMToken
    extra = 0
    readonly_fields = ('token', 'created_at', 'last_used_at')
    can_delete = True

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'hotel',
        'first_name',
        'last_name',
        'department',
        'role',
        'access_level',
        'email',
        'phone_number',
        'is_active',
        'is_on_duty',
    )
    list_filter = (
        'hotel',
        'department',
        'role',
        'access_level',
        'is_active',
        'is_on_duty',
    )
    search_fields = (
        'first_name',
        'last_name',
        'email',
        'phone_number',
        'user__username',
    )
    ordering = (
        'hotel',
        'department',
        'last_name',
    )
    list_editable = (
        'is_active',
        'role',
        'access_level',
        'is_on_duty',
    )

    fieldsets = (
        (None, {
            'fields': (
                ('user', 'hotel', 'first_name', 'last_name'),
                ('email', 'phone_number'),
                ('department', 'role', 'access_level'),
                'is_active', 'is_on_duty'
            )
        }),
    )

    inlines = [StaffFCMTokenInline]

    actions = ['mark_as_inactive', 'mark_as_on_duty', 'mark_as_off_duty']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        hotel = getattr(request, 'hotel', None)
        return qs.filter(hotel=hotel) if hotel else qs.none()

    @admin.action(description="Mark selected staff as inactive")
    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Mark selected staff as ON duty")
    def mark_as_on_duty(self, request, queryset):
        queryset.update(is_on_duty=True)

    @admin.action(description="Mark selected staff as OFF duty")
    def mark_as_off_duty(self, request, queryset):
        queryset.update(is_on_duty=False)
