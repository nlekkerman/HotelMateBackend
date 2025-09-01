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
    quantity = models.IntegerField(default=0)  # number of bottles/items
    alert_quantity = models.IntegerField(default=0, help_text="Minimum quantity before alert is triggered")
    type = models.ForeignKey(StockItemType, on_delete=models.SET_NULL, null=True, blank=True)
    # NEW: how much volume each bottle contains
    volume_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Volume per bottle/item (e.g., 330 for 330 ml)"
    )
    
    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,  # e.g., [('ml', 'Milliliters'), ('l', 'Liters')]
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
        if self.volume_per_unit and self.quantity and self.unit:
            return f"{self.quantity * float(self.volume_per_unit)} {self.unit}"
        return "N/A"

    def is_below_alert_level(self):
        return self.quantity < self.alert_quantity
    
    def activate_stock_item(self, stock, quantity=None):
        from .models import StockInventory

        if not self.active_stock_item:
            self.active_stock_item = True
            self.save(update_fields=["active_stock_item"])

        # Create or update inventory line, but do NOT update item quantity
        inventory, created = StockInventory.objects.get_or_create(
            stock=stock,
            item=self,
            defaults={"quantity": quantity}
        )
        if not created:
            inventory.quantity = quantity
            inventory.save(update_fields=["quantity"])
            
    def deactivate_stock_item(self):
        from .models import StockInventory

        # Delete all inventory lines (in case item is in multiple stocks)
        StockInventory.objects.filter(item=self).delete()
        self.active_stock_item = False
        self.save(update_fields=["active_stock_item"])  # No quantity update here


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
    OUT = 'out'
    DIRECTION_CHOICES = [
        (IN,  'Stock In'),
        (OUT, 'Stock Out'),
    ]

    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='movements',
        help_text="Which storage location this movement applies to"
    )
    item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='movements',
        help_text="Which defined stock item was moved"
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements',
        help_text="Who performed this movement"
    )
    direction = models.CharField(
        max_length=3,
        choices=DIRECTION_CHOICES
    )
    quantity = models.IntegerField(
        help_text="Amount moved in or out (whole number only)"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"

    def __str__(self):
        return (
            f"{self.get_direction_display()} of {self.quantity} "
            f"{self.item.name} in {self.stock} by {self.staff or '—'}"
        )


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
