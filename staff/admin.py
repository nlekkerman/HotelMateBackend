from django.contrib import admin
from django.utils.html import format_html
from .models import Staff, StaffFCMToken, Department, Role


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'department', 'description')
    list_filter = ('department',)
    search_fields = ('name', 'slug', 'description', 'department__name')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('department__name', 'name')



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
        'has_registered_face',
        'is_active',
        'is_on_duty',
    )
    list_filter = (
        'hotel',
        'department',
        'role',
        'access_level',
        'has_registered_face',
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
        'department__name',
        'last_name',
    )
    list_editable = (
        'has_registered_face',
        'is_active',
        'role',
        'access_level',
        'is_on_duty',
    )

    fieldsets = (
        (None, {
            'fields': (
                ('user', 'hotel'),
                ('first_name', 'last_name'),
                ('email', 'phone_number'),
                ('department', 'role', 'access_level'),
                ('is_active', 'is_on_duty', 'has_registered_face'),
                'profile_image',
                'profile_image_preview',
            )
        }),
    )
    readonly_fields = ('profile_image_preview',)

    inlines = [StaffFCMTokenInline]

    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html(
                '<img src="{}" style="height:60px; width:60px; object-fit:cover; border-radius:50%;" />',
                obj.profile_image.url
            )
        return "-"
    profile_image_preview.short_description = "Profile Image"

    def get_department(self, obj):
        return obj.department.name if obj.department else "-"
    get_department.admin_order_field = 'department__name'
    get_department.short_description = 'Department'

    def get_role(self, obj):
        return obj.role.name if obj.role else "-"
    get_role.admin_order_field = 'role__name'
    get_role.short_description = 'Role'

    actions = ['mark_as_inactive', 'mark_as_on_duty', 'mark_as_off_duty']

    @admin.action(description="Mark selected staff as inactive")
    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Mark selected staff as ON duty")
    def mark_as_on_duty(self, request, queryset):
        queryset.update(is_on_duty=True)

    @admin.action(description="Mark selected staff as OFF duty")
    def mark_as_off_duty(self, request, queryset):
        queryset.update(is_on_duty=False)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Assuming request has hotel attribute, otherwise modify accordingly
        hotel = getattr(request, 'hotel', None)
        return qs.filter(hotel=hotel) if hotel else qs.none()
