# src/apps/hotel_info/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages

from .models import HotelInfoCategory, HotelInfo, CategoryQRCode


# ─── 1. HotelInfoCategory stays the same ────────────────────────────────────────
@admin.register(HotelInfoCategory)
class HotelInfoCategoryAdmin(admin.ModelAdmin):
    list_display        = ("slug", "name")
    prepopulated_fields = {"slug": ("name",)}


# ─── 2. HotelInfo no longer shows or generates any QR ─────────────────────────
@admin.register(HotelInfo)
class HotelInfoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "hotel",
        "category",
        "event_date",
        "event_time",
        "active",
        "created_at",
        "image_thumbnail",  # <-- Add this for image preview in list view
    )
    list_filter = ("category", "hotel", "active", "event_date")
    readonly_fields = ("created_at", 'image_preview')

    def get_fields(self, request, obj=None):
        base_fields = [
            "hotel",
            "category",
            "title",
            "description",
            "event_date",
            "event_time",
            "active",
            "extra_info",
        ]
        if obj:
            base_fields.append("created_at")
            base_fields.append("image_preview")  # Show image preview in detail view
        else:
            # On add form, no preview
            base_fields.append("image")
        return base_fields

    # Show thumbnail in list display
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:50px; max-width:50px; object-fit:contain;" />',
                obj.image.url if hasattr(obj.image, 'url') else obj.image
            )
        return "-"
    image_thumbnail.short_description = "Image"

    # Show bigger image preview in detail view
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:200px; max-width:200px; object-fit:contain;" />',
                obj.image.url if hasattr(obj.image, 'url') else obj.image
            )
        return "No image"
    image_preview.short_description = "Image Preview"

# ─── 3. New admin for CategoryQRCode ──────────────────────────────────────────
@admin.register(CategoryQRCode)
class CategoryQRCodeAdmin(admin.ModelAdmin):
    list_display = (
        "hotel",
        "category",
        "qr_thumbnail",
        "qr_url",
        "generated_at",
    )
    list_filter  = ("category", "hotel")
    actions      = ["generate_qr_for_selected"]

    readonly_fields = ("qr_url", "generated_at")

    def qr_thumbnail(self, obj):
        if obj.qr_url:
            return format_html(
                '<img src="{}" style="max-height:100px; max-width:100px;" />',
                obj.qr_url
            )
        return "-"
    qr_thumbnail.short_description = "QR Code"

    def generate_qr_for_selected(self, request, queryset):
        total = queryset.count()
        successes = 0

        for record in queryset:
            try:
                url = record.generate_qr()
                if url:
                    successes += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed for {record.hotel.slug}/{record.category.slug}: {e}",
                    level=messages.ERROR,
                )

        self.message_user(
            request,
            f"Successfully generated QR for {successes} of {total} selected records.",
            level=messages.INFO,
        )
    generate_qr_for_selected.short_description = "Generate QR for selected categories"
