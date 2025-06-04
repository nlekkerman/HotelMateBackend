from django.contrib import admin
from django import forms
from .models import Booking, BookingCategory, BookingSubcategory, Seats, Restaurant

class BookingInline(admin.TabularInline):  # or StackedInline for more detail
    model = Booking
    extra = 0
    fields = ('category', 'date', 'time', 'note')
    readonly_fields = ('created_at',)
    show_change_link = True

# -----------------------
# Custom Admin Form for Booking
# -----------------------
class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If editing an existing booking, filter restaurants by its hotel
        if self.instance and self.instance.pk and self.instance.hotel_id:
            self.fields['restaurant'].queryset = Restaurant.objects.filter(hotel=self.instance.hotel)
        else:
            # On creation (no instance.pk yet), show all active restaurants by default
            self.fields['restaurant'].queryset = Restaurant.objects.filter(is_active=True)


# -----------------------
# Booking Subcategory Admin
# -----------------------
@admin.register(BookingSubcategory)
class BookingSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel')
    list_filter = ('hotel',)
    search_fields = ('name',)


# -----------------------
# Booking Category Admin
# -----------------------
@admin.register(BookingCategory)
class BookingCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'subcategory', 'hotel')
    list_filter = ('subcategory', 'hotel')
    search_fields = ('name',)


# -----------------------
# Inline for Seats
# -----------------------
class SeatsInline(admin.StackedInline):
    model = Seats
    extra = 0
    max_num = 1


# -----------------------
# Booking Admin
# -----------------------
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('category', 'hotel', 'restaurant', 'date', 'time', 'created_at')
    list_filter = ('category', 'category__subcategory', 'hotel', 'date')
    search_fields = ('note',)
    ordering = ('-created_at',)
    inlines = [SeatsInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "restaurant":
            if request.resolver_match and "object_id" not in request.resolver_match.kwargs:
                # Creating a new Booking: show only active restaurants
                kwargs["queryset"] = Restaurant.objects.filter(is_active=True)
            else:
                # Editing: show only restaurants of the hotel on the instance (will be refined in __init__)
                kwargs["queryset"] = Restaurant.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
# -----------------------
# Restaurant Admin
# -----------------------
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'hotel',
        'capacity', 'opening_time', 'closing_time', 'is_active'
    )
    list_filter = ('hotel', 'is_active',)
    search_fields = ('name', 'hotel__name')
    inlines = [BookingInline] 
