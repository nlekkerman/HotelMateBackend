from django.contrib import admin
from .models import StockCategory, StockItem, Stock, StockInventory, StockMovement

@admin.register(StockCategory)
class StockCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'hotel', 'name', 'slug')
    list_filter = ('hotel',)
    search_fields = ('name', 'slug')
    ordering = ('hotel', 'name')
    prepopulated_fields = {'slug': ('name',)}  # auto-fill slug from name

@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'hotel', 'name', 'sku', 'quantity', 'alert_quantity', 'alert_status')
    list_filter = ('hotel',)
    search_fields = ('name', 'sku')
    ordering = ('hotel', 'name')

    @admin.display(description='Status')
    def alert_status(self, obj):
        if obj.quantity < obj.alert_quantity:
            return "⚠️ Low Stock"
        return "✅ OK"

class StockInventoryInline(admin.TabularInline):
    model = StockInventory
    extra = 1
    fk_name = 'stock'
    autocomplete_fields = ('item',)
    fields = ('item', 'quantity')

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('id', 'hotel', 'category')
    list_filter = ('hotel', 'category')
    search_fields = ('category__name',)
    ordering = ('hotel', 'category')
    inlines = (StockInventoryInline,)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # After saving the Stock, ensure it has inventory lines for all StockItems of the hotel
        existing_item_ids = obj.inventory_lines.values_list('item_id', flat=True)
        all_items = StockItem.objects.filter(hotel=obj.hotel).exclude(id__in=existing_item_ids)

        for item in all_items:
            StockInventory.objects.create(stock=obj, item=item, quantity=0)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'hotel', 'stock', 'item', 'direction', 'quantity', 'staff')
    list_filter  = ('hotel', 'stock__category', 'direction', 'staff')
    search_fields = ('item__name',)
