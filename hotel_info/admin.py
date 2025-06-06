from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import HotelInfo
import json

@admin.register(HotelInfo)
class HotelInfoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "hotel",
        "category",
        "active",
        "created_at",
        "info_qr_image",
        "generate_info_qr_button",
    )
    readonly_fields = ("pretty_extra_info",)  # We’ll dynamically add the QR field in get_fields()

    # ─── Dynamically choose which fields to show on the change page ────────────────
    def get_fields(self, request, obj=None):
        """
        Only display the one non-empty QR field for the given HotelInfo instance.
        By default, show: title, hotel, category, description, active, created_at.
        Then, if the relevant info_qr_<category> is non-empty, show that field as read-only.
        Finally, show pretty_extra_info at the bottom.
        """
        base_fields = ["title", "hotel", "category", "description", "active", "created_at"]

        if obj:
            # Determine which QR field name corresponds to obj.category
            field_map = {
                "info_board":       "info_qr_board",
                "kid_entertainment": "info_qr_kids",
                "dining":           "info_qr_dining",
                "offers":           "info_qr_offers",
            }
            qr_field_name = field_map.get(obj.category)

            # Only append that QR field if it is non-empty (i.e. has a URL)
            if qr_field_name and getattr(obj, qr_field_name):
                base_fields.append(qr_field_name)

            # Always show extra_info (raw JSON) as the last read-only field
            base_fields.append("pretty_extra_info")

        return base_fields

    # ─── Indicate which of the model fields should be read-only ───────────────────
    def get_readonly_fields(self, request, obj=None):
        """
        Make created_at + the single QR field + pretty_extra_info be read-only.
        (Django will complain if we list a field in readonly_fields() but do
        not include it in get_fields().)
        """
        ro_fields = ["created_at", "pretty_extra_info"]
        if obj:
            field_map = {
                "info_board":       "info_qr_board",
                "kid_entertainment": "info_qr_kids",
                "dining":           "info_qr_dining",
                "offers":           "info_qr_offers",
            }
            qr_field_name = field_map.get(obj.category)
            if qr_field_name and getattr(obj, qr_field_name):
                ro_fields.append(qr_field_name)

        return ro_fields

    # ─── Show a thumbnail of the QR-code in the list display ───────────────────────
    def info_qr_image(self, obj):
        """
        Displays the QR-code image for this instance, based on its category.
        Falls back to extra_info["qr_url"] if the dedicated field is empty.
        """
        field_map = {
            "info_board":       obj.info_qr_board,
            "kid_entertainment": obj.info_qr_kids,
            "dining":           obj.info_qr_dining,
            "offers":           obj.info_qr_offers,
        }
        qr_url = field_map.get(obj.category)

        # If the dedicated field is blank, check extra_info["qr_url"]
        if not qr_url and obj.extra_info and isinstance(obj.extra_info, dict):
            qr_url = obj.extra_info.get("qr_url")

        if qr_url:
            return format_html(
                '<img src="{}" style="max-height:100px; max-width:100px;" />',
                qr_url
            )
        return "-"

    info_qr_image.short_description = "QR Code"

    # ─── “Generate QR” button in the list display ─────────────────────────────────
    def generate_info_qr_button(self, obj):
        if obj.pk:
            url = reverse("admin:hotelinfo_generate_qr", args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Generate QR</a>',
                url
            )
        return "-"

    generate_info_qr_button.short_description = "Actions"
    generate_info_qr_button.allow_tags = True

    # ─── Pretty-print extra_info as JSON ─────────────────────────────────────────
    def pretty_extra_info(self, obj):
        """
        Shows the raw JSON stored in extra_info, nicely indented.
        """
        if obj.extra_info:
            formatted = json.dumps(obj.extra_info, indent=2)
            return format_html('<pre style="white-space: pre-wrap;">{}</pre>', formatted)
        return "-"

    pretty_extra_info.short_description = "Extra Info (Raw)"
    pretty_extra_info.allow_tags = True

    # ─── Add a custom URL to generate a single QR from the changelist ──────────────
    def get_urls(self):
        """
        Prepend our custom “generate_qr” URL to the default admin URLs.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "generate_qr/<int:hotelinfo_id>/",
                self.admin_site.admin_view(self.generate_single_qr),
                name="hotelinfo_generate_qr",
            ),
        ]
        return custom_urls + urls

    def generate_single_qr(self, request, hotelinfo_id, *args, **kwargs):
        """
        Invoked when you click “Generate QR” in the changelist.
        Calls generate_info_qr() on that HotelInfo, shows a message, then
        redirects back to the HotelInfo changelist.
        """
        info_obj = get_object_or_404(HotelInfo, pk=hotelinfo_id)
        try:
            qr_url = info_obj.generate_info_qr()
            if qr_url:
                messages.success(
                    request,
                    format_html(
                        'QR code generated successfully: '
                        '<a href="{}" target="_blank">View QR</a>',
                        qr_url
                    )
                )
            else:
                messages.warning(
                    request,
                    "generate_info_qr() returned None. "
                    "Perhaps `hotel` or `category` is not set correctly."
                )
        except Exception as e:
            messages.error(
                request,
                f"Error generating QR for '{info_obj}': {e}"
            )

        # Redirect back to the HotelInfo changelist
        changelist_url = reverse("admin:hotel_info_hotelinfo_changelist")
        return redirect(changelist_url)
