from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Staff, Department, Role, RegistrationCode,
    UserProfile, NavigationItem
)


@admin.register(NavigationItem)
class NavigationItemAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'path',
        'display_order',
        'is_active',
        'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'path', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')
    list_editable = ('display_order', 'is_active')
    
    fieldsets = (
        (None, {
            'fields': (
                'name',
                'slug',
                'path',
                'description',
                'display_order',
                'is_active',
            )
        }),
    )


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
        'has_fcm_token',
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
                'allowed_navigation_items',
            )
        }),
        ('Push Notifications', {
            'fields': ('fcm_token', 'fcm_token_preview'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('profile_image_preview', 'fcm_token_preview')
    filter_horizontal = ('allowed_navigation_items',)

    def has_fcm_token(self, obj):
        """Display if staff has FCM token saved"""
        if obj.fcm_token:
            return format_html('<span style="color:green;">✓</span>')
        return format_html('<span style="color:red;">✗</span>')
    has_fcm_token.short_description = 'FCM Token'
    has_fcm_token.admin_order_field = 'fcm_token'

    def fcm_token_preview(self, obj):
        """Show preview of FCM token in admin"""
        if obj.fcm_token:
            preview = obj.fcm_token[:50] + '...' if len(obj.fcm_token) > 50 else obj.fcm_token
            return format_html(
                '<div style="font-family:monospace; font-size:11px; background:#f0f0f0; padding:8px; border-radius:4px;">'
                '<strong>Token saved:</strong><br>{}<br><br>'
                '<strong>Length:</strong> {} characters<br>'
                '<strong>Status:</strong> <span style="color:green;">✓ Ready for push notifications</span>'
                '</div>',
                preview,
                len(obj.fcm_token)
            )
        return format_html(
            '<div style="background:#fff3cd; padding:8px; border-radius:4px; border-left:4px solid #ffc107;">'
            '<strong>No FCM token saved</strong><br>'
            'Staff will not receive push notifications when browser is closed.<br><br>'
            'To save token: Staff must login to React web app and grant notification permissions.'
            '</div>'
        )
    fcm_token_preview.short_description = 'FCM Token Status'

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

@admin.register(RegistrationCode)
class RegistrationCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'hotel_slug',
        'has_qr_code',
        'used_by',
        'created_at',
        'used_at'
    )
    list_filter = ('hotel_slug', 'used_at')
    search_fields = ('code', 'hotel_slug', 'used_by__username', 'qr_token')
    readonly_fields = (
        'used_by',
        'used_at',
        'created_at',
        'qr_token',
        'qr_code_preview',
        'registration_url'
    )
    ordering = ('-created_at', 'hotel_slug', 'code')
    
    fieldsets = (
        ('Registration Code Information', {
            'fields': (
                'code',
                'hotel_slug',
                'created_at',
            )
        }),
        ('QR Code Information', {
            'fields': (
                'qr_token',
                'qr_code_url',
                'qr_code_preview',
                'registration_url',
            ),
            'description': (
                'QR code links registration code with a secure token. '
                'Both code and QR must be provided to new employees.'
            )
        }),
        ('Usage Information', {
            'fields': (
                'used_by',
                'used_at',
            )
        }),
    )
    
    def has_qr_code(self, obj):
        """Display if registration code has QR code generated"""
        if obj.qr_code_url and obj.qr_token:
            return format_html(
                '<span style="color:green;">✓ QR Ready</span>'
            )
        elif obj.qr_token:
            return format_html(
                '<span style="color:orange;">⚠ Token only</span>'
            )
        return format_html(
            '<span style="color:red;">✗ No QR</span>'
        )
    has_qr_code.short_description = 'QR Status'
    
    def qr_code_preview(self, obj):
        """Display QR code image in admin"""
        if obj.qr_code_url:
            return format_html(
                '<div style="padding:10px; background:#f8f9fa; '
                'border-radius:8px;">'
                '<img src="{}" style="max-width:200px; '
                'max-height:200px; display:block; margin-bottom:10px;" />'
                '<div style="font-size:12px; color:#666;">'
                '<strong>QR Code URL:</strong><br>'
                '<a href="{}" target="_blank" '
                'style="word-break:break-all;">{}</a>'
                '</div>'
                '</div>',
                obj.qr_code_url,
                obj.qr_code_url,
                obj.qr_code_url
            )
        return format_html(
            '<div style="background:#fff3cd; padding:12px; '
            'border-radius:4px; border-left:4px solid #ffc107;">'
            '<strong>⚠ No QR Code Generated</strong><br>'
            'Use the API endpoint to generate QR code:<br>'
            '<code>POST /api/staff/registration-package/</code>'
            '</div>'
        )
    qr_code_preview.short_description = 'QR Code Preview'
    
    def registration_url(self, obj):
        """Display the registration URL that QR code points to"""
        if obj.qr_token:
            url = (
                f"https://hotelsmates.com/register?"
                f"token={obj.qr_token}&hotel={obj.hotel_slug}"
            )
            return format_html(
                '<div style="background:#e7f3ff; padding:12px; '
                'border-radius:4px; border-left:4px solid #2196F3;">'
                '<strong>Registration URL:</strong><br>'
                '<a href="{}" target="_blank" '
                'style="word-break:break-all; font-family:monospace; '
                'font-size:11px;">{}</a><br><br>'
                '<strong style="color:#d32f2f;">⚠ Security Note:</strong><br>'
                '<span style="font-size:11px;">Employee must also enter '
                'registration code: <strong>{}</strong></span>'
                '</div>',
                url,
                url,
                obj.code
            )
        return format_html(
            '<div style="background:#ffebee; padding:12px; '
            'border-radius:4px;">'
            'No QR token generated yet'
            '</div>'
        )
    registration_url.short_description = 'Registration URL'
    
    actions = ['generate_qr_codes']
    
    @admin.action(description="Generate QR codes for selected registration codes")
    def generate_qr_codes(self, request, queryset):
        """Generate QR codes for codes that don't have them"""
        count = 0
        for reg_code in queryset:
            if not reg_code.qr_token:
                reg_code.generate_qr_token()
            if not reg_code.qr_code_url:
                reg_code.generate_qr_code()
                count += 1
        
        self.message_user(
            request,
            f'Successfully generated QR codes for {count} registration code(s).'
        )

    
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'username', 
        'email',
        'registration_code_display',
        'staff_exists'
    )
    search_fields = (
        'user__username', 
        'user__email', 
        'registration_code__code'
    )
    list_filter = (
        'registration_code__hotel_slug',
    )
    readonly_fields = ('registration_code',)

    def username(self, obj):
        return obj.user.username
    username.admin_order_field = 'user__username'

    def email(self, obj):
        return obj.user.email
    email.admin_order_field = 'user__email'

    def registration_code_display(self, obj):
        if obj.registration_code:
            return obj.registration_code.code
        return "-"
    registration_code_display.short_description = "Registration Code"

    def staff_exists(self, obj):
        if hasattr(obj.user, 'staff_profile'):
            return format_html('<span style="color:green;">Yes</span>')
        return format_html('<span style="color:red;">No</span>')
    staff_exists.short_description = "Staff Created"