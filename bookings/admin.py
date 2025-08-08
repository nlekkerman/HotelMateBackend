from django.contrib import admin
from .models import Booking, BookingCategory, BookingSubcategory, Seats, Restaurant

class SeatsInline(admin.StackedInline):
    model = Seats
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ('total', 'adults', 'children', 'infants')

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

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'capacity', 'is_active')
    list_filter = ('hotel', 'is_active')
    search_fields = ('name',)
    inlines = [BookingInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('bookings__category', 'bookings__category__subcategory')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('category', 'hotel', 'date', 'time', 'created_at')  # Removed 'room', 'restaurant'
    list_filter = ('category', 'category__subcategory', 'hotel', 'date')
    search_fields = ()  # Disabled search
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
