from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError

from .models import (
    StockCategory,
    StockItem,
    Stock,
    StockInventory,
    StockMovement,
    StockItemType,
    Ingredient,
    CocktailRecipe,
    RecipeIngredient,
    CocktailConsumption
)

@admin.register(StockItemType)
class StockItemTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    ordering = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class StockItemTypeInline(admin.TabularInline):
    model = StockItemType
    extra = 1
# --- Custom FormSet to prevent duplicate items in inline ---
class StockInventoryInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        seen = set()
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue
            item = form.cleaned_data.get('item')
            if item in seen:
                raise ValidationError(f"Duplicate item '{item}' in stock inventory.")
            seen.add(item)

# --- Admin for StockCategory ---
@admin.register(StockCategory)
class StockCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'hotel', 'name', 'slug')
    list_filter = ('hotel',)
    search_fields = ('name', 'slug')
    ordering = ('hotel', 'name')
    prepopulated_fields = {'slug': ('name',)}  # auto-fill slug from name

@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'hotel', 'name','type', 'sku', 'quantity', 'volume_per_unit_display', 'unit_display', 'alert_quantity', 'alert_status'
    )
    list_filter = ('hotel', 'unit', 'type')
    search_fields = ('name', 'sku')
    ordering = ('hotel', 'name')

    # Use select_related if 'hotel' is ForeignKey and used frequently
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('hotel')

    @admin.display(description='Volume per Item')
    def volume_per_unit_display(self, obj):
        if obj.volume_per_unit and obj.unit:
            return f"{obj.volume_per_unit} {obj.unit}"
        return "-"

    @admin.display(description='Unit')
    def unit_display(self, obj):
        return dict(StockItem.UNIT_CHOICES).get(obj.unit, '-')

    @admin.display(description='Status')
    def alert_status(self, obj):
        return "⚠️ Low Stock" if obj.quantity < obj.alert_quantity else "✅ OK"

# --- Inline for StockInventory ---
class StockInventoryInline(admin.TabularInline):
    model = StockInventory
    extra = 1
    fk_name = 'stock'
    autocomplete_fields = ('item',)
    fields = ('item', 'quantity')
    formset = StockInventoryInlineFormSet
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('item', 'item__hotel')
# --- Admin for Stock ---
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('id', 'hotel', 'category')
    list_filter = ('hotel', 'category')
    search_fields = ('category__name',)
    ordering = ('hotel', 'category')
    inlines = (StockInventoryInline,)

    def save_formset(self, request, form, formset, change):
        """
        Save formset and then auto-create missing inventory lines for this stock.
        Also syncs item.quantity to match inventory.
        """
        instances = formset.save(commit=False)

        for form_instance in instances:
            form_instance.save()
            # Sync item quantity with this stock line
            form_instance.item.quantity = form_instance.quantity
            form_instance.item.save(update_fields=['quantity'])

        formset.save_m2m()

        if formset.model == StockInventory:
            stock = form.instance
            existing_item_ids = stock.inventory_lines.values_list('item_id', flat=True)
            all_items = StockItem.objects.filter(hotel=stock.hotel).exclude(id__in=existing_item_ids)

            for item in all_items:
                inventory, created = StockInventory.objects.get_or_create(
                    stock=stock,
                    item=item,
                    defaults={'quantity': item.quantity}  # sync initial quantity
                )

        return instances

# --- Admin for StockMovement ---
@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'hotel', 'stock', 'item', 'direction', 'quantity', 'staff')
    list_filter = ('hotel', 'stock__category', 'direction', 'staff')
    search_fields = ('item__name',)


# --- Ingredient ---
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unit', 'hotel')
    search_fields = ('name',)
    list_filter = ('hotel',)  # filter by hotel
    ordering = ('name',)

# --- RecipeIngredient Inline ---
class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)
    fields = ('ingredient', 'quantity_per_cocktail')

# --- CocktailRecipe ---
@admin.register(CocktailRecipe)
class CocktailRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'hotel')
    search_fields = ('name',)
    list_filter = ('hotel',)  # filter by hotel
    ordering = ('name',)
    inlines = (RecipeIngredientInline,)

# --- CocktailConsumption ---
@admin.register(CocktailConsumption)
class CocktailConsumptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cocktail', 'quantity_made', 'timestamp', 'hotel')
    list_filter = ('cocktail', 'timestamp', 'cocktail__hotel')  # filter by cocktail's hotel
    search_fields = ('cocktail__name',)
    ordering = ('-timestamp',)
