@admin.register(AttendanceSettings)
class AttendanceSettingsAdmin(admin.ModelAdmin):
    """Admin interface for managing hotel attendance settings"""
    list_display = (
        'hotel',
        'face_attendance_enabled',
        'break_warning_hours',
        'overtime_warning_hours',
        'enforce_limits',
    )
    list_filter = ('face_attendance_enabled', 'enforce_limits')
    search_fields = ('hotel__name', 'hotel__slug')
    
    fieldsets = (
        ('Hotel', {
            'fields': ('hotel',)
        }),
        ('Time Limits & Warnings', {
            'fields': (
                'break_warning_hours',
                'overtime_warning_hours', 
                'hard_limit_hours',
                'enforce_limits',
            ),
            'description': 'Configure shift duration warnings and limits'
        }),
        ('Face Recognition Settings', {
            'fields': (
                'face_attendance_enabled',
                'face_attendance_min_confidence',
                'require_face_consent',
                'allow_face_self_registration',
                'face_data_retention_days',
                'face_attendance_departments',
            ),
            'description': 'Configure face recognition for attendance tracking'
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Add help text for face_attendance_departments field"""
        form = super().get_form(request, obj, **kwargs)
        if 'face_attendance_departments' in form.base_fields:
            form.base_fields['face_attendance_departments'].help_text = (
                'JSON list of department IDs that can use face attendance. '
                'Leave empty to allow all departments. Example: [1, 2, 3]'
            )
        return form