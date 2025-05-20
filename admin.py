from django.contrib import admin
from django.http import HttpResponseRedirect
from .models import RoomServiceItem, Room, Order, OrderItem,BreakfastItem, BreakfastOrder, BreakfastOrderItem 
from django.utils.html import mark_safe, format_html


class RoomServiceItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'description', 'image_preview')  # Added 'category' and 'image_preview'
    search_fields = ('name', 'description')  # Allow search on name and description
    list_filter = ('category', 'price')  # Filter by category and price
    ordering = ('category', 'name')  # Group items by category, then name
    list_per_page = 20  # Pagination

    # Image preview for admin
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" />')
        return 'No image'

    image_preview.short_description = 'Image'

class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'room_number', 'is_occupied', 'get_guests_count',
        'room_service_qr_link', 'kids_qr_link', 'breakfast_qr_link',
        'generate_qr_buttons'
    )

    search_fields = ('room_number',)
    list_filter = ('is_occupied',)

    def get_guests_count(self, obj):
        return obj.guests.count()
    get_guests_count.short_description = 'Number of Guests'

    def room_service_qr_link(self, obj):
        if obj.room_service_qr_code:
            return format_html('<a href="{}" target="_blank">Room Service</a>', obj.room_service_qr_code)
        return 'Not Generated'
    room_service_qr_link.short_description = 'Room Service QR'

    def kids_qr_link(self, obj):
        if obj.kids_entertainment_qr_code:
            return format_html('<a href="{}" target="_blank">Kids</a>', obj.kids_entertainment_qr_code)
        return 'Not Generated'
    kids_qr_link.short_description = 'Kids QR'

    def breakfast_qr_link(self, obj):
        if obj.in_room_breakfast_qr_code:
            return format_html('<a href="{}" target="_blank">Breakfast</a>', obj.in_room_breakfast_qr_code)
        return 'Not Generated'
    breakfast_qr_link.short_description = 'Breakfast QR'

    def generate_qr_buttons(self, obj):
        buttons = []
        if not obj.room_service_qr_code:
            buttons.append('Room Service')
        if not obj.kids_entertainment_qr_code:
            buttons.append('Kids')
        if not obj.in_room_breakfast_qr_code:
            buttons.append('Breakfast')
        return ", ".join(buttons) if buttons else "All Generated"
    generate_qr_buttons.short_description = "Missing QR Codes"

    def generate_all_qrs(self, request, queryset):
        for room in queryset:
            room.generate_qr_code("room_service")
            room.generate_qr_code("kids_entertainment")
            room.generate_qr_code("in_room_breakfast")
        self.message_user(request, "All QR codes generated successfully.")

    actions = ['generate_all_qrs']


# --- OrderItem inline ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # One empty form by default
    autocomplete_fields = ['item']
    readonly_fields = ['item_price']

    def item_price(self, obj):
        return obj.item.price if obj.item else "-"
    item_price.short_description = "Unit Price"

# --- Order admin ---
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'room_number', 'status', 'created_at', 'total_price')
    list_filter = ('status', 'created_at')
    search_fields = ('room_number',)
    inlines = [OrderItemInline]

    def total_price(self, obj):
        return f"€{sum(item.item.price * item.quantity for item in obj.orderitem_set.all()):.2f}"
    total_price.short_description = 'Total Price'
    
class BreakfastItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description', 'image_preview')
    search_fields = ('name', 'description')
    list_filter = ('category',)
    ordering = ('category', 'name')

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" />')
        return 'No image'
    image_preview.short_description = 'Image'


class BreakfastOrderItemInline(admin.TabularInline):
    model = BreakfastOrderItem
    extra = 1
    autocomplete_fields = ['item']




class BreakfastOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'room_number', 'status', 'created_at', 'total_price')
    list_filter = ('status', 'created_at')
    search_fields = ('room_number',)
    inlines = [BreakfastOrderItemInline]

    def total_price(self, obj):
        return f"€{sum(item.item.price * item.quantity for item in obj.breakfastorderitem_set.all()):.2f}"
    total_price.short_description = 'Total Price'


# Register these models and their admin classes
admin.site.register(BreakfastItem, BreakfastItemAdmin)
admin.site.register(BreakfastOrder, BreakfastOrderAdmin)
    
# Register Room model with the custom admin interface
admin.site.register(Room, RoomAdmin)
# Register the model and the custom admin class
admin.site.register(RoomServiceItem, RoomServiceItemAdmin)
# ✅ Register the new Order admin
admin.site.register(Order, OrderAdmin)

