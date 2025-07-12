# ar_navigation/admin.py
from django.contrib import admin
from .models import ARAnchor

@admin.register(ARAnchor)
class ARAnchorAdmin(admin.ModelAdmin):
    list_display = ("hotel", "restaurant", "url", "qr_code_url")
    readonly_fields = ("url", "qr_code_url")
    actions = ("regenerate_qr_codes",)
    fieldsets = (
        (None, {"fields": ("hotel", "restaurant", "url", "qr_code_url")}),
    )

    def save_model(self, request, obj, form, change):
        # when first creating, generate a QR
        if not change:
            obj.generate_qr_code()
        super().save_model(request, obj, form, change)

    def regenerate_qr_codes(self, request, queryset):
        for anchor in queryset:
            anchor.generate_qr_code()
        self.message_user(
            request,
            f"Regenerated QR code for {queryset.count()} anchor(s)."
        )
    regenerate_qr_codes.short_description = "Regenerate QR code(s)"
