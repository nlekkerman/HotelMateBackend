from django.contrib import admin
from .models import MaintenanceRequest, MaintenanceComment, MaintenancePhoto
from django.utils.safestring import mark_safe

class MaintenancePhotoInline(admin.TabularInline):
    model = MaintenancePhoto
    extra = 0
    fields = ('image', 'uploaded_at')  # minimal fields
    readonly_fields = ('uploaded_at',)
    can_delete = False  # prevent delete overhead
    show_change_link = False  # no link to edit photo separately

class MaintenanceCommentInline(admin.TabularInline):
    model = MaintenanceComment
    extra = 0
    fields = ('message', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False
    show_change_link = False

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'hotel', 'room', 'location_note', 'status', 'created_at')
    list_filter = ('status', 'hotel', 'created_at')
    search_fields = ('title', 'description', 'location_note')

    readonly_fields = (
        'hotel',
        'room',
        'reported_by',
        'accepted_by',
        'status',
        'created_at',
        'updated_at',
    )

    raw_id_fields = ('reported_by', 'accepted_by', 'room')  # Optional: for lookup-only
    inlines = [MaintenancePhotoInline, MaintenanceCommentInline]

@admin.register(MaintenanceComment)
class MaintenanceCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'staff', 'request', 'created_at')
    search_fields = ('message',)
    readonly_fields = ('created_at',)

@admin.register(MaintenancePhoto)
class MaintenancePhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'uploaded_by', 'uploaded_at', 'image_id_display')
    readonly_fields = ('uploaded_at',)

    def image_id_display(self, obj):
        return obj.image.public_id if hasattr(obj.image, 'public_id') else "-"
    image_id_display.short_description = "Cloudinary ID"
