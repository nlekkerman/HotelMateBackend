from django.contrib import admin
from django import forms
from .models import (
    Booking, BookingCategory, BookingSubcategory, Seats,
    Restaurant, RestaurantBlueprint, BlueprintArea,
    BlueprintObjectType, BlueprintObject
)
from django.utils.html import format_html

# -------------------------
# Custom Forms with Validation
# -------------------------
class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        # Create temporary instance for validation
        instance = Booking(**cleaned_data)
        instance.full_clean()
        return cleaned_data

class BookingCategoryAdminForm(forms.ModelForm):
    class Meta:
        model = BookingCategory
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        # Create temporary instance for validation
        instance = BookingCategory(**cleaned_data)
        instance.full_clean()
        return cleaned_data

# -------------------------
# Inlines
# -------------------------
class SeatsInline(admin.StackedInline):
    model = Seats
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = ('total',)


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
    form = BookingCategoryAdminForm
    list_display = ('name', 'subcategory', 'hotel')
    list_filter = ('subcategory', 'hotel')
    search_fields = ('name', 'subcategory__name')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm
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
        'seen',
    )
    list_filter = (
        'category',
        'category__subcategory',
        'hotel',
        'restaurant',
        'date',
        'seen',
    )
    search_fields = (
        'category__name',
        'category__subcategory__name',
        'hotel__name',
        'guest__name',
        'voucher_code',
    )
    ordering = ('-created_at',)
    inlines = [SeatsInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'category',
            'category__subcategory',
            'hotel',
            'restaurant',
            'guest'
        )


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'hotel',
        'capacity',
        'max_bookings_per_hour',
        'max_group_size',
        'taking_bookings',
        'is_active',
        'opening_time',
        'closing_time',
        'image_thumbnail',
    )
    list_filter = ('hotel', 'is_active')
    search_fields = ('name', 'slug')
    fieldsets = (
        (None, {
            "fields": (
                "name",
                "hotel",
                "slug",
                "description",
                "is_active",
                "image",
            ),
        }),
        ("Capacity & Booking Rules", {
            "fields": (
                "capacity",
                "max_bookings_per_hour",
                "max_group_size",
            ),
        }),
        ("Operating Hours", {
            "fields": (
                "opening_time",
                "closing_time",
            ),
        }),
    )
    
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" style="object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "-"
    image_thumbnail.short_description = 'Image'


@admin.register(RestaurantBlueprint)
class RestaurantBlueprintAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'width', 'height', 'grid_size')
    list_filter = ('restaurant',)


@admin.register(BlueprintArea)
class BlueprintAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'blueprint', 'x', 'y', 'width', 'height')
    list_filter = ('blueprint',)
    search_fields = ('name',)


@admin.register(BlueprintObjectType)
class BlueprintObjectTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'default_width', 'default_height', 'icon')
    search_fields = ('name',)


@admin.register(BlueprintObject)
class BlueprintObjectAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'type',
        'blueprint',
        'x',
        'y',
        'width',
        'height',
        'rotation',
        'z_index'
    )
    list_filter = ('type', 'blueprint')
    search_fields = ('name', 'type__name', 'blueprint__restaurant__name')
