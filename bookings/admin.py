from django.contrib import admin
from .models import (
    Booking, BookingCategory, BookingSubcategory, Seats,
    Restaurant, RestaurantBlueprint, BlueprintArea,
    DiningTable, TableSeatSpot, BookingTable,
    BlueprintObjectType, BlueprintObject
)

# -------------------------
# Inlines
# -------------------------
class SeatsInline(admin.StackedInline):
    model = Seats
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ('total',)


class BookingTableInline(admin.TabularInline):
    model = BookingTable
    extra = 0
    autocomplete_fields = ('table',)


# -------------------------
# Admins
# -------------------------
@admin.register(BookingSubcategory)
class BookingSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'slug')
    list_filter = ('hotel',)
    search_fields = ('name', 'slug')


@admin.register(BookingCategory)
class BookingCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'subcategory', 'hotel')
    list_filter = ('subcategory', 'hotel')
    search_fields = ('name', 'subcategory__name')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'category',
        'hotel',
        'guest',
        'date',
        'start_time',
        'end_time',
        'restaurant',
        'voucher_code',
        'created_at',
    )
    list_filter = (
        'category',
        'category__subcategory',
        'hotel',
        'restaurant',
        'date',
    )
    search_fields = (
        'category__name',
        'category__subcategory__name',
        'hotel__name',
        'guest__name',
        'voucher_code',
    )
    ordering = ('-created_at',)
    inlines = [SeatsInline, BookingTableInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'category', 'category__subcategory', 'hotel', 'restaurant', 'guest'
        ).prefetch_related('booking_tables__table')


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'hotel',
        'capacity',
        'is_active',
        'opening_time',
        'closing_time',
    )
    list_filter = ('hotel', 'is_active')
    search_fields = ('name', 'slug')


@admin.register(RestaurantBlueprint)
class RestaurantBlueprintAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'width', 'height', 'grid_size')
    list_filter = ('restaurant',)


@admin.register(BlueprintArea)
class BlueprintAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'blueprint', 'x', 'y', 'width', 'height')
    list_filter = ('blueprint',)
    search_fields = ('name',)


@admin.register(DiningTable)
class DiningTableAdmin(admin.ModelAdmin):
    list_display = ('code', 'restaurant', 'capacity', 'shape', 'area', 'join_group', 'is_active')
    list_filter = ('restaurant', 'shape', 'area', 'is_active')
    search_fields = ('code', 'restaurant__name', 'join_group')


@admin.register(TableSeatSpot)
class TableSeatSpotAdmin(admin.ModelAdmin):
    list_display = ('table', 'index', 'offset_x', 'offset_y', 'angle_degrees')
    ordering = ('table', 'index')


@admin.register(BookingTable)
class BookingTableAdmin(admin.ModelAdmin):
    list_display = ('booking', 'table')
    list_filter = (
        'table',
        'booking__hotel',
        'booking__date',
        'booking__start_time',
        'booking__end_time',
    )
    search_fields = ('booking__category__name', 'table__code')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'booking', 'table', 'booking__category', 'booking__category__subcategory'
        )


@admin.register(BlueprintObjectType)
class BlueprintObjectTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_width', 'default_height', 'icon')
    search_fields = ('name',)


@admin.register(BlueprintObject)
class BlueprintObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'blueprint', 'x', 'y', 'width', 'height', 'rotation', 'z_index')
    list_filter = ('type', 'blueprint')
    search_fields = ('name', 'type__name', 'blueprint__restaurant__name')
