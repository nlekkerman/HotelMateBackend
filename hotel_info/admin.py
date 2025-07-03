# src/apps/hotel_info/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import HotelInfoCategory, HotelInfo, CategoryQRCode, GoodToKnowEntry
from django.contrib import messages 

@admin.register(HotelInfoCategory)
class HotelInfoCategoryAdmin(admin.ModelAdmin):
    list_display        = ("slug", "name")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(HotelInfo)
class HotelInfoAdmin(admin.ModelAdmin):
    list_display    = (
        "title",
        "hotel",
        "category",
        "event_date",
        "event_time",
        "active",
        "created_at",
        "image_thumbnail",
    )
    list_filter     = ("category", "hotel", "active", "event_date")
    readonly_fields = ("created_at", "image_preview")

    fieldsets = (
        (None, {
            'fields': (
                "hotel",
                "category",
                "title",
                "description",
                "image",           # <-- allow upload/edit here
                "event_date",
                "event_time",
                "active",
                "extra_info",
            )
        }),
        ("Preview & Metadata", {
            'fields': (
                "image_preview",  # display current image
                "created_at",
            ),
            'classes': ("collapse",),
        }),
    )

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:50px; max-width:50px; object-fit:contain;" />',
                obj.image.url
            )
        return "-"
    image_thumbnail.short_description = "Image"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:200px; max-width:200px; object-fit:contain;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Image Preview"


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
    readonly_fields = ("qr_url", "generated_at")
    actions      = ["generate_qr_for_selected"]

    def qr_thumbnail(self, obj):
        if obj.qr_url:
            return format_html(
                '<img src="{}" style="max-height:100px; max-width:100px;" />',
                obj.qr_url
            )
        return "-"
    qr_thumbnail.short_description = "QR Code"

    def generate_qr_for_selected(self, request, queryset):
        successes = 0
        for record in queryset:
            try:
                result = record.generate_qr()
                if result:
                    successes += 1
                else:
                    self.message_user(
                        request,
                        f"generate_qr() returned False for {record}",
                        level=messages.WARNING
                    )
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed for {record.hotel.slug}/{record.category.slug}: {e}",
                    level=messages.ERROR
                )
        self.message_user(
            request,
            f"Successfully generated QR for {successes} of {queryset.count()} records.",
            level=messages.INFO
        )

@admin.register(GoodToKnowEntry)
class GoodToKnowEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "hotel", "slug", "active", "created_at", "image_thumbnail", "qr_preview")
    list_filter = ("hotel", "active")
    readonly_fields = ("created_at", "qr_url", "generated_at", "image_preview")
    actions = ["generate_qr_for_selected"]

    fieldsets = (
        (None, {
            'fields': (
                "hotel", "slug", "title", "content", "image",
                "extra_info", "active"
            )
        }),
        ("QR & Metadata", {
            'fields': ("qr_url", "generated_at", "image_preview", "created_at"),
            'classes': ("collapse",),
        }),
    )

    def image_thumbnail(self, obj):
        url = getattr(obj.image, 'url', obj.image)  # If obj.image is URL string, fallback to it
        if url:
            return format_html('<img src="{}" style="max-height:50px;" />', url)
        return "-"
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:200px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Image Preview"

    def qr_preview(self, obj):
        if obj.qr_url:
            return format_html(
                '<img src="{}" style="max-height:80px;" />',
                obj.qr_url
            )
        return "-"
    qr_preview.short_description = "QR Code"

    def generate_qr_for_selected(self, request, queryset):
        count = 0
        for obj in queryset:
            try:
                if obj.generate_qr():
                    count += 1
            except Exception as e:
                self.message_user(request, f"⚠️ Failed to generate QR for {obj}: {e}", level=messages.ERROR)
        self.message_user(request, f"🎉 Generated QR for {count} of {queryset.count()} entries.", level=messages.SUCCESS)


