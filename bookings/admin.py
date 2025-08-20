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
    readonly_fields = ('total',)  # Total can be computed from adults+children+infants

class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    can_delete = False
    max_num = 0
    fields = ('category', 'date', 'time', 'note')
    readonly_fields = fields
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category', 'category__subcategory', 'hotel', 'restaurant')

class BlueprintObjectInline(admin.TabularInline):
    model = BlueprintObject
    extra = 0
    fields = ('type', 'name', 'x', 'y', 'width', 'height', 'rotation', 'z_index')
    show_change_link = True

# -------------------------
# Admins
# -------------------------
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'capacity', 'is_active')
    list_filter = ('hotel', 'is_active')
    search_fields = ('name',)
    inlines = [BookingInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('bookings__category', 'bookings__category__subcategory')

@admin.register(BlueprintObjectType)
class BlueprintObjectTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_width', 'default_height', 'icon')
    search_fields = ('name',)

@admin.register(BlueprintObject)
class BlueprintObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'blueprint', 'x', 'y', 'width', 'height', 'rotation', 'z_index')
    list_filter = ('type', 'blueprint')
    search_fields = ('name', 'type__name', 'blueprint__restaurant__name')

@admin.register(RestaurantBlueprint)
class RestaurantBlueprintAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'width', 'height', 'grid_size')
    list_filter = ('restaurant',)
    inlines = [BlueprintObjectInline]

@admin.register(BlueprintArea)
class BlueprintAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'blueprint')
    list_filter = ('blueprint',)
    search_fields = ('name',)

@admin.register(DiningTable)
class DiningTableAdmin(admin.ModelAdmin):
    list_display = ('code', 'restaurant', 'capacity', 'shape', 'is_active')
    list_filter = ('restaurant', 'shape', 'is_active')
    search_fields = ('code',)

@admin.register(TableSeatSpot)
class TableSeatSpotAdmin(admin.ModelAdmin):
    list_display = ('table', 'index', 'offset_x', 'offset_y', 'angle_degrees')
    ordering = ('table', 'index')

@admin.register(BookingTable)
class BookingTableAdmin(admin.ModelAdmin):
    list_display = ('booking', 'table')
    list_filter = ('table', 'booking__hotel', 'booking__date')
    search_fields = ('booking__category__name', 'table__code')  # fixed table__number

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('booking', 'table', 'booking__category', 'booking__category__subcategory')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('category', 'hotel', 'date', 'time', 'created_at')
    list_filter = ('category', 'category__subcategory', 'hotel', 'date')
    search_fields = ('category__name', 'category__subcategory__name', 'hotel__name')
    ordering = ('-created_at',)
    inlines = [SeatsInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category', 'category__subcategory', 'hotel')

@admin.register(BookingCategory)
class BookingCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'subcategory', 'hotel')
    list_filter = ('subcategory', 'hotel')
    search_fields = ('name',)

@admin.register(BookingSubcategory)
class BookingSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel')
    list_filter = ('hotel',)
    search_fields = ('name',)
