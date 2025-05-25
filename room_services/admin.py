from django.contrib import admin
from django.utils.html import mark_safe
from .models import (
    RoomServiceItem, Order, OrderItem,
    BreakfastItem, BreakfastOrder, BreakfastOrderItem
)


# --- RoomServiceItem admin ---
class RoomServiceItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'description', 'image_preview')
    search_fields = ('name', 'description')
    list_filter = ('category', 'price')
    ordering = ('category', 'name')
    list_per_page = 20

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" />')
        return 'No image'
    image_preview.short_description = 'Image'


# --- OrderItem inline ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
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


# --- BreakfastItem admin ---
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


# --- BreakfastOrderItem inline ---
class BreakfastOrderItemInline(admin.TabularInline):
    model = BreakfastOrderItem
    extra = 1
    autocomplete_fields = ['item']


# --- BreakfastOrder admin ---
class BreakfastOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'room_number', 'status', 'created_at', 'total_price')
    list_filter = ('status', 'created_at')
    search_fields = ('room_number',)
    inlines = [BreakfastOrderItemInline]

    def total_price(self, obj):
        return f"€{sum(item.item.price * item.quantity for item in obj.breakfastorderitem_set.all()):.2f}"
    total_price.short_description = 'Total Price'


# --- Register models ---
admin.site.register(RoomServiceItem, RoomServiceItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(BreakfastItem, BreakfastItemAdmin)
admin.site.register(BreakfastOrder, BreakfastOrderAdmin)
