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
    StocktakeLine,
    Sale
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
        'size', 'uom', 'unit_cost', 'display_stock',
        'menu_price', 'display_gp_percentage', 'available_on_menu'
    )
    list_filter = (
        'hotel', 'category', 'available_on_menu',
        'available_by_bottle', 'active'
    )
    search_fields = ('sku', 'name')
    ordering = ('hotel', 'category', 'sku')
    readonly_fields = (
        'cost_per_serving', 'total_stock_in_servings', 'total_stock_value',
        'gross_profit_per_serving', 'gross_profit_percentage',
        'markup_percentage', 'pour_cost_percentage',
        'display_full_units', 'display_partial_units',
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
                'display_full_units', 'display_partial_units',
                'total_stock_in_servings', 'total_stock_value'
            )
        }),
        ('Selling Prices', {
            'fields': (
                'menu_price', 'menu_price_large', 'bottle_price',
                'promo_price'
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

    def display_stock(self, obj):
        """Display stock with cases + bottles for Doz items"""
        if obj.size and 'Doz' in obj.size:
            cases = obj.display_full_units
            bottles = obj.display_partial_units
            
            if cases > 0 and bottles > 0:
                return f"{int(cases)} cases + {int(bottles)} bottles"
            elif cases > 0:
                return f"{int(cases)} cases"
            else:
                return f"{int(bottles)} bottles"
        else:
            # For other items, show normal format
            full = obj.current_full_units
            partial = obj.current_partial_units
            
            if full > 0 and partial > 0:
                return f"{full} + {partial:.2f}"
            elif full > 0:
                return f"{full}"
            else:
                return f"{partial:.2f}"
    display_stock.short_description = 'Stock'
    
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
        'start_date', 'end_date', 'is_closed', 'reopened_by'
    )
    list_filter = ('hotel', 'period_type', 'is_closed', 'year')
    search_fields = ('period_name',)
    ordering = ('-end_date', '-start_date')
    readonly_fields = (
        'created_at', 'closed_at', 'closed_by',
        'reopened_at', 'reopened_by'
    )
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
            'fields': (
                'is_closed', 'closed_at', 'closed_by',
                'reopened_at', 'reopened_by', 'notes'
            )
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
        'opening_qty', 'purchases', 'waste',
        'transfers_in', 'transfers_out', 'adjustments',
        'valuation_cost', 'display_item_info'
    )
    fields = (
        'display_item_info', 'counted_full_units', 'counted_partial_units',
        'opening_qty', 'purchases', 'waste'
    )
    
    def display_item_info(self, obj):
        """Display item SKU and name"""
        if obj.item:
            return f"{obj.item.sku} - {obj.item.name}"
        return "-"
    display_item_info.short_description = 'Item'


@admin.register(Stocktake)
class StocktakeAdmin(admin.ModelAdmin):
    list_display = (
        'hotel', 'period_start', 'period_end',
        'status', 'approved_at', 'approved_by', 'total_lines'
    )
    list_filter = ('hotel', 'status', 'period_end')
    search_fields = ('hotel__name',)
    ordering = ('-period_end',)
    readonly_fields = ('created_at', 'approved_at', 'approved_by')
    actions = ['approve_stocktakes', 'unapprove_stocktakes']
    # Removed inlines to allow quick status changes without loading 254 items
    
    def total_lines(self, obj):
        """Show count of stocktake lines"""
        return obj.lines.count()
    total_lines.short_description = 'Total Items'
    
    @admin.action(description='✅ Approve selected stocktakes')
    def approve_stocktakes(self, request, queryset):
        """Approve selected stocktakes"""
        from django.utils import timezone
        updated = 0
        for stocktake in queryset:
            if stocktake.status != 'APPROVED':
                stocktake.status = 'APPROVED'
                stocktake.approved_at = timezone.now()
                try:
                    stocktake.approved_by = request.user.staff_profile
                except AttributeError:
                    stocktake.approved_by = None
                stocktake.save()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} stocktake(s) approved successfully.'
        )
    
    @admin.action(description='📝 Change selected stocktakes to DRAFT')
    def unapprove_stocktakes(self, request, queryset):
        """Change selected stocktakes back to DRAFT"""
        updated = queryset.filter(status='APPROVED').update(
            status='DRAFT',
            approved_at=None,
            approved_by=None
        )
        
        self.message_user(
            request,
            f'{updated} stocktake(s) changed to DRAFT.'
        )

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.save()
        else:
            if obj.status != 'APPROVED':
                super().save_model(request, obj, form, change)


@admin.register(StocktakeLine)
class StocktakeLineAdmin(admin.ModelAdmin):
    list_display = (
        'stocktake', 'item', 'display_counted_stock', 'variance_qty'
    )
    list_filter = ('stocktake__hotel', 'stocktake')
    search_fields = ('item__sku', 'item__name')
    readonly_fields = (
        'opening_qty', 'purchases', 'waste',
        'transfers_in', 'transfers_out', 'adjustments',
        'valuation_cost', 'counted_qty', 'expected_qty',
        'variance_qty', 'expected_value', 'counted_value',
        'variance_value'
    )

    def display_counted_stock(self, obj):
        """Display counted stock with cases + bottles for Doz items"""
        if obj.item.size and 'Doz' in obj.item.size:
            full = obj.counted_full_units or 0
            partial = obj.counted_partial_units or 0
            
            if full > 0 and partial > 0:
                return f"{int(full)} cases + {int(partial)} bottles"
            elif full > 0:
                return f"{int(full)} cases"
            elif partial > 0:
                return f"{int(partial)} bottles"
            else:
                return "Not counted"
        else:
            # For other items, show normal format
            full = obj.counted_full_units or 0
            partial = obj.counted_partial_units or 0
            
            if full > 0 or partial > 0:
                if full > 0 and partial > 0:
                    return f"{full} + {partial:.2f}"
                elif full > 0:
                    return f"{full}"
                else:
                    return f"{partial:.2f}"
            else:
                return "Not counted"
    display_counted_stock.short_description = 'Counted'


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        'sale_date', 'item', 'quantity', 'total_cost',
        'total_revenue', 'gross_profit', 'stocktake', 'created_by'
    )
    list_filter = ('stocktake__hotel', 'sale_date', 'item__category')
    search_fields = (
        'item__sku', 'item__name', 'stocktake__period_start',
        'notes'
    )
    ordering = ('-sale_date', '-created_at')
    readonly_fields = (
        'total_cost', 'total_revenue', 'gross_profit',
        'gross_profit_percentage', 'created_at', 'updated_at'
    )
    fieldsets = (
        ('Sale Details', {
            'fields': (
                'stocktake', 'item', 'sale_date',
                'quantity', 'unit_cost', 'unit_price'
            )
        }),
        ('Calculated Totals', {
            'fields': (
                'total_cost', 'total_revenue',
                'gross_profit', 'gross_profit_percentage'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queries with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'stocktake', 'item', 'item__category', 'created_by'
        )
