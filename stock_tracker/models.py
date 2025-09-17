# models.py
from django.db import models
from hotel.models import Hotel
from django.utils.text import slugify

from django.conf import settings


class StockCategory(models.Model):
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name='stock_categories'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(
        max_length=100,
        null=True,
        blank=True,
        help_text="URL-friendly identifier (auto-generated from name)."
    )

    class Meta:
        # you can either keep name-uniqueness:
        unique_together = ('hotel', 'name')
        # —or enforce slug-uniqueness instead:
        # unique_together = ('hotel', 'slug')
        verbose_name_plural = 'stock categories'

    def __str__(self):
        return f"{self.hotel.name} – {self.name}"

    def save(self, *args, **kwargs):
        # auto-generate slug on save if not provided
        if not self.slug and self.name:
            base = slugify(self.name)[:90]
            slug = base
            count = 1
            while StockCategory.objects.filter(hotel=self.hotel, slug=slug).exists():
                slug = f"{base}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)


class StockItemType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Stock Item Type"
        verbose_name_plural = "Stock Item Types"

    def __str__(self):
        return self.name


class StockItem(models.Model):
    UNIT_CHOICES = [
        ('ml', 'Milliliters'),
        ('l', 'Liters'),
    ]
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='stock_items')
    name = models.CharField(max_length=255, default='stock_item', blank=True, unique=True)
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True)
    active_stock_item = models.BooleanField(default=False, help_text="Indicates if the item is active in stock inventory")
    quantity = models.IntegerField(default=0)  # number of bottles/items (STORAGE)
    stock_in_bar = models.IntegerField(default=0, help_text="Already taken out of storage but unsold")  # ✅ NEW
    alert_quantity = models.IntegerField(default=0, help_text="Minimum quantity before alert is triggered")
    type = models.ForeignKey("StockItemType", on_delete=models.SET_NULL, null=True, blank=True)
    volume_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Volume per bottle/item (e.g., 330 for 330 ml)"
    )
    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        null=True,
        blank=True,
        help_text="Unit for volume per bottle/item"
    )

    class Meta:
        unique_together = ('hotel', 'name')

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def total_volume(self):
        if self.volume_per_unit and self.unit:
            return f"{(self.quantity + self.stock_in_bar) * float(self.volume_per_unit)} {self.unit}"
        return "N/A"

    @property
    def total_available(self):
        """Everything we still own: storage + bar."""
        return self.quantity + self.stock_in_bar

    def is_below_alert_level(self):
        return self.total_available < self.alert_quantity


class Stock(models.Model):
    hotel= models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='stocks')
    category = models.ForeignKey(
        StockCategory, on_delete=models.SET_NULL,
        null=True, related_name='stocks'
    )
    # use through=StockInventory
    items = models.ManyToManyField(
        StockItem,
        through='StockInventory',
        related_name='stocks',
        blank=True,
    )

    class Meta:
        unique_together = ('hotel', 'category')
        verbose_name_plural = 'stocks'

    def __str__(self):
        return f"{self.hotel.name} • {self.category.name if self.category else '—'}"


class StockInventory(models.Model):
    """
    The through-model joining Stock ↔ StockItem,
    adding a per-stock quantity for each item.
    """
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='inventory_lines')
    item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='inventory_lines')
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ('stock', 'item')

    def __str__(self):
        return f"{self.stock} – {self.item.name}: {self.quantity}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Keep StockItem quantity in sync
        self.item.quantity = self.quantity
        self.item.save(update_fields=['quantity'])

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        # Optionally reset item quantity on deletion
        self.item.quantity = 0
        self.item.save(update_fields=['quantity'])


class StockMovement(models.Model):
    IN = 'in'
    MOVE_TO_BAR = 'move_to_bar'
    SALE = 'sale'
    WASTE = 'waste'

    DIRECTION_CHOICES = [
        (IN, 'Stock In (Purchase/Delivery)'),
        (MOVE_TO_BAR, 'Moved to Bar'),
        (SALE, 'Sale'),
        (WASTE, 'Waste/Breakage'),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='stock_movements')
    item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='movements')
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:  # update live counters
            if self.direction == self.IN:
                self.item.quantity += self.quantity

            elif self.direction == self.MOVE_TO_BAR:
                if self.item.quantity < self.quantity:
                    raise ValueError("Not enough stock in storage to move to bar")
                self.item.quantity -= self.quantity
                self.item.stock_in_bar += self.quantity

            elif self.direction == self.SALE:
                if self.item.stock_in_bar < self.quantity:
                    raise ValueError("Not enough stock in bar to sell")
                self.item.stock_in_bar -= self.quantity

            elif self.direction == self.WASTE:
                if self.item.stock_in_bar < self.quantity:
                    raise ValueError("Not enough stock in bar to waste")
                self.item.stock_in_bar -= self.quantity

            self.item.save(update_fields=["quantity", "stock_in_bar"])


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    hotel = models.ForeignKey("hotel.Hotel", on_delete=models.CASCADE, related_name="ingredients")

    class Meta:
        unique_together = ("name", "hotel")



class CocktailRecipe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    hotel = models.ForeignKey(
        "hotel.Hotel",
        on_delete=models.CASCADE,
        related_name="cocktails"
    )

    class Meta:
        unique_together = ("name", "hotel")  # same name allowed in different hotels

    def __str__(self):
        return f"{self.name} ({self.hotel.name})"

class RecipeIngredient(models.Model):
    """
    Links a cocktail recipe to its ingredients and quantity per cocktail.
    """
    cocktail = models.ForeignKey(
        CocktailRecipe, 
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient, 
        on_delete=models.CASCADE
    )
    quantity_per_cocktail = models.FloatField(
        help_text="Quantity required per single cocktail"
    )

    class Meta:
        unique_together = ('cocktail', 'ingredient')

    def __str__(self):
        return f"{self.quantity_per_cocktail} {self.ingredient.unit} of {self.ingredient.name} for {self.cocktail.name}"


class CocktailConsumption(models.Model):
    cocktail = models.ForeignKey(
        CocktailRecipe, 
        on_delete=models.CASCADE,
        related_name='consumptions'
    )
    quantity_made = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    hotel = models.ForeignKey(
        "hotel.Hotel",
        on_delete=models.CASCADE,
        related_name="consumptions"
    )

    def __str__(self):
        return f"{self.quantity_made} x {self.cocktail.name} on {self.timestamp.strftime('%Y-%m-%d')}"

    def total_ingredient_usage(self):
        """
        Returns a dict of {ingredient_name: (total_quantity, unit)}
        """
        usage = {}
        for ri in self.cocktail.ingredients.all():
            total_qty = ri.quantity_per_cocktail * self.quantity_made
            usage[ri.ingredient.name] = (total_qty, ri.ingredient.unit)
        return usage


class StockPeriod(models.Model):
    PERIOD_CHOICES = [
        ('week', 'Weekly'),
        ('month', 'Monthly'),
        ('half_year', 'Half-Yearly'),
        ('year', 'Yearly'),
    ]

    hotel = models.ForeignKey("hotel.Hotel", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("hotel", "start_date", "end_date")

    def __str__(self):
        return f"{self.hotel.name} – {self.start_date} → {self.end_date} ({self.get_period_type_display()})"
   

class StockPeriodItem(models.Model):
    period = models.ForeignKey(
        StockPeriod,
        on_delete=models.CASCADE,
        related_name="items"
    )
    item = models.ForeignKey("StockItem", on_delete=models.CASCADE)

    # Stock at the beginning
    opening_storage = models.IntegerField(default=0)
    opening_bar = models.IntegerField(default=0)

    # Stock movements
    added = models.IntegerField(default=0)
    moved_to_bar = models.IntegerField(default=0)
    sales = models.IntegerField(default=0)
    waste = models.IntegerField(default=0)

    # Stock at the end
    closing_storage = models.IntegerField(default=0)
    closing_bar = models.IntegerField(default=0)
    total_closing_stock = models.IntegerField(default=0)

    class Meta:
        unique_together = ("period", "item")

    def __str__(self):
        return f"{self.item.name} in {self.period}"
