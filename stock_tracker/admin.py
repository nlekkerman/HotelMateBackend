from django.contrib import admin
from .models import (
    Ingredient,
    CocktailRecipe,
    RecipeIngredient,
    CocktailConsumption,
    StockCategory,
    StockItem,
    StockMovement,
    Stocktake,
    StocktakeLine
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unit', 'hotel')
    search_fields = ('name',)
    list_filter = ('hotel',)
    ordering = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)
    fields = ('ingredient', 'quantity_per_cocktail')


@admin.register(CocktailRecipe)
class CocktailRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'hotel')
    search_fields = ('name',)
    list_filter = ('hotel',)
    ordering = ('name',)
    inlines = (RecipeIngredientInline,)


@admin.register(CocktailConsumption)
class CocktailConsumptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cocktail', 'quantity_made', 'timestamp', 'hotel')
    list_filter = ('cocktail', 'timestamp', 'cocktail__hotel')
    search_fields = ('cocktail__name',)
    ordering = ('-timestamp',)


# Stock Management Admin

@admin.register(StockCategory)
class StockCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'hotel', 'name', 'sort_order')
    list_filter = ('hotel',)
    search_fields = ('name',)
    ordering = ('hotel', 'sort_order', 'name')


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'description', 'category', 'hotel',
        'current_qty', 'unit_cost', 'gp_percentage'
    )
    list_filter = ('hotel', 'category')
    search_fields = ('code', 'description')
    ordering = ('hotel', 'category', 'code')
    readonly_fields = ('gp_percentage',)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp', 'hotel', 'item', 'movement_type',
        'quantity', 'staff'
    )
    list_filter = ('hotel', 'movement_type', 'timestamp')
    search_fields = ('item__code', 'item__description', 'reference')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)


class StocktakeLineInline(admin.TabularInline):
    model = StocktakeLine
    extra = 0
    readonly_fields = (
        'opening_qty', 'purchases', 'sales', 'waste',
        'transfers_in', 'transfers_out', 'adjustments',
        'valuation_cost'
    )
    fields = (
        'item', 'counted_full_units', 'counted_partial_units',
        'opening_qty', 'purchases', 'sales'
    )


@admin.register(Stocktake)
class StocktakeAdmin(admin.ModelAdmin):
    list_display = (
        'hotel', 'period_start', 'period_end',
        'status', 'approved_at', 'approved_by'
    )
    list_filter = ('hotel', 'status', 'period_end')
    search_fields = ('hotel__name',)
    ordering = ('-period_end',)
    readonly_fields = ('created_at', 'approved_at', 'approved_by', 'status')
    inlines = [StocktakeLineInline]

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.save()
        else:
            if obj.status != 'APPROVED':
                super().save_model(request, obj, form, change)


@admin.register(StocktakeLine)
class StocktakeLineAdmin(admin.ModelAdmin):
    list_display = (
        'stocktake', 'item', 'counted_full_units',
        'counted_partial_units', 'variance_qty'
    )
    list_filter = ('stocktake__hotel', 'stocktake')
    search_fields = ('item__code', 'item__description')
    readonly_fields = (
        'opening_qty', 'purchases', 'sales', 'waste',
        'transfers_in', 'transfers_out', 'adjustments',
        'valuation_cost', 'counted_qty', 'expected_qty',
        'variance_qty', 'expected_value', 'counted_value',
        'variance_value'
    )
