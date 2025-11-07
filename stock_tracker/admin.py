from django.contrib import admin
from .models import (
    Ingredient,
    CocktailRecipe,
    RecipeIngredient,
    CocktailConsumption,
    StockCategory,
    StockItem,
    StockPeriod,
    StockSnapshot,
    StockMovement,
    Location,
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


# ============================================================================
# STOCK MANAGEMENT ADMIN
# ============================================================================

@admin.register(StockCategory)
class StockCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('name',)
    ordering = ('code',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'hotel', 'name', 'active')
    list_filter = ('hotel', 'active')
    search_fields = ('name',)
    ordering = ('hotel', 'name')


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = (
        'sku', 'name', 'category', 'hotel',
        'size', 'uom', 'unit_cost',
        'current_full_units', 'current_partial_units',
        'menu_price', 'display_gp_percentage', 'available_on_menu'
    )
    list_filter = ('hotel', 'category', 'available_on_menu', 'available_by_bottle', 'active')
    search_fields = ('sku', 'name')
    ordering = ('hotel', 'category', 'sku')
    readonly_fields = (
        'cost_per_serving', 'total_stock_in_servings', 'total_stock_value',
        'gross_profit_per_serving', 'gross_profit_percentage',
        'markup_percentage', 'pour_cost_percentage',
        'created_at', 'updated_at'
    )
    fieldsets = (
        ('Identification', {
            'fields': ('hotel', 'sku', 'name', 'category')
        }),
        ('Size & Packaging', {
            'fields': ('size', 'size_value', 'size_unit', 'uom')
        }),
        ('Costing', {
            'fields': ('unit_cost', 'cost_per_serving')
        }),
        ('Current Stock', {
            'fields': (
                'current_full_units', 'current_partial_units',
                'total_stock_in_servings', 'total_stock_value'
            )
        }),
        ('Selling Prices', {
            'fields': (
                'menu_price', 'menu_price_large', 'bottle_price', 'promo_price'
            )
        }),
        ('Profitability Metrics', {
            'fields': (
                'gross_profit_per_serving', 'gross_profit_percentage',
                'markup_percentage', 'pour_cost_percentage'
            ),
            'classes': ('collapse',)
        }),
        ('Availability', {
            'fields': ('available_on_menu', 'available_by_bottle', 'active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_gp_percentage(self, obj):
        """Display gross profit percentage in list view"""
        gp = obj.gross_profit_percentage
        if gp is not None:
            return f"{gp:.2f}%"
        return "-"
    display_gp_percentage.short_description = 'GP%'
    display_gp_percentage.admin_order_field = 'menu_price'


@admin.register(StockPeriod)
class StockPeriodAdmin(admin.ModelAdmin):
    list_display = (
        'period_name', 'hotel', 'period_type',
        'start_date', 'end_date', 'is_closed'
    )
    list_filter = ('hotel', 'period_type', 'is_closed', 'year')
    search_fields = ('period_name',)
    ordering = ('-end_date', '-start_date')
    readonly_fields = ('created_at', 'closed_at', 'closed_by')
    fieldsets = (
        ('Period Details', {
            'fields': (
                'hotel', 'period_type', 'period_name',
                'start_date', 'end_date'
            )
        }),
        ('Period Identifiers', {
            'fields': ('year', 'quarter', 'month', 'week'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_closed', 'closed_at', 'closed_by', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(StockSnapshot)
class StockSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        'item', 'period', 'closing_full_units',
        'closing_partial_units', 'closing_stock_value'
    )
    list_filter = ('hotel', 'period__period_type', 'period')
    search_fields = ('item__sku', 'item__name', 'period__period_name')
    ordering = ('-period__end_date', 'item__sku')
    readonly_fields = ('created_at',)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp', 'hotel', 'item', 'movement_type',
        'quantity', 'get_staff_name', 'reference'
    )
    list_filter = ('hotel', 'movement_type', 'timestamp')
    search_fields = (
        'item__sku', 'item__name', 'reference',
        'staff__first_name', 'staff__last_name'
    )
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    
    def get_staff_name(self, obj):
        """Display staff full name instead of just ID"""
        if obj.staff:
            full_name = (
                f"{obj.staff.first_name} {obj.staff.last_name}".strip()
            )
            return full_name or obj.staff.username
        return "-"
    get_staff_name.short_description = 'Staff'
    get_staff_name.admin_order_field = 'staff__last_name'


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
    search_fields = ('item__sku', 'item__name')
    readonly_fields = (
        'opening_qty', 'purchases', 'sales', 'waste',
        'transfers_in', 'transfers_out', 'adjustments',
        'valuation_cost', 'counted_qty', 'expected_qty',
        'variance_qty', 'expected_value', 'counted_value',
        'variance_value'
    )
