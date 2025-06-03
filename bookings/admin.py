from django.contrib import admin
from .models import Booking, BookingCategory, BookingSubcategory, Seats


@admin.register(BookingSubcategory)
class BookingSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel')
    list_filter = ('hotel',)
    search_fields = ('name',)


@admin.register(BookingCategory)
class BookingCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'subcategory', 'hotel')
    list_filter = ('subcategory', 'hotel')
    search_fields = ('name',)


class SeatsInline(admin.StackedInline):
    model = Seats
    extra = 0
    max_num = 1


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('category', 'hotel', 'date', 'time', 'created_at')
    list_filter = ('category', 'category__subcategory', 'hotel', 'date')
    search_fields = ('note',)
    ordering = ('-created_at',)
    inlines = [SeatsInline]
