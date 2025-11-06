# models.py
from django.db import models
from decimal import Decimal


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name="ingredients"
    )

    class Meta:
        unique_together = ("name", "hotel")

    def __str__(self):
        return f"{self.name} ({self.unit})"


class CocktailRecipe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name="cocktails"
    )

    class Meta:
        unique_together = ("name", "hotel")

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
        return (
            f"{self.quantity_per_cocktail} {self.ingredient.unit} of "
            f"{self.ingredient.name} for {self.cocktail.name}"
        )


class CocktailConsumption(models.Model):
    cocktail = models.ForeignKey(
        CocktailRecipe,
        on_delete=models.CASCADE,
        related_name='consumptions'
    )
    quantity_made = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name="consumptions"
    )

    def __str__(self):
        date_str = self.timestamp.strftime('%Y-%m-%d')
        return f"{self.quantity_made} x {self.cocktail.name} on {date_str}"

    def total_ingredient_usage(self):
        """
        Returns a dict of {ingredient_name: (total_quantity, unit)}
        """
        usage = {}
        for ri in self.cocktail.ingredients.all():
            total_qty = ri.quantity_per_cocktail * self.quantity_made
            usage[ri.ingredient.name] = (total_qty, ri.ingredient.unit)
        return usage


class StockCategory(models.Model):
    """Categories for stock items (Spirits, Wine, Beers, etc.)"""
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='stock_categories'
    )
    name = models.CharField(max_length=100)
    sort_order = models.IntegerField(default=0)

    class Meta:
        unique_together = ('hotel', 'name')
        verbose_name_plural = 'Stock Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.hotel.name} - {self.name}"


class Location(models.Model):
    """
    Physical storage locations/bins.
    Examples: Bar Storage, Cellar A-12, Keg Room
    """
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='locations'
    )
    name = models.CharField(
        max_length=100,
        help_text="Location name (e.g., 'Spirits Shelf', 'Cellar Rack A-12')"
    )
    active = models.BooleanField(
        default=True,
        help_text="Location is active for use"
    )

    class Meta:
        unique_together = ('hotel', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.hotel.name} - {self.name}"


class StockItem(models.Model):
    """
    Enhanced inventory item with comprehensive product details.
    Supports mixed unit tracking (full + partial units).
    """
    # Core identification
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='stock_items'
    )
    category = models.ForeignKey(
        StockCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items'
    )
    sku = models.CharField(
        max_length=50,
        help_text="SKU/Product code"
    )
    name = models.CharField(
        max_length=200,
        help_text="Product name"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed product description"
    )
    
    # Classification
    product_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Wine, Beer, Spirit, Soft Drink, Food, etc."
    )
    subtype = models.CharField(
        max_length=50,
        blank=True,
        help_text="Fortified, Red, IPA, Sparkling, etc."
    )
    tag = models.CharField(
        max_length=100,
        blank=True,
        help_text="Additional tags for filtering"
    )
    
    # Size / Units
    size = models.CharField(
        max_length=50,
        help_text="e.g., 70cl, 30Lt, Doz"
    )
    size_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Numeric size (e.g., 70)"
    )
    size_unit = models.CharField(
        max_length=10,
        blank=True,
        help_text="cl, ml, L, g, kg"
    )
    uom = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Units per case (e.g., 12 bottles/case)"
    )
    base_unit = models.CharField(
        max_length=20,
        default='ml',
        help_text="Base unit for calculations (ml, g, pieces)"
    )
    
    # Cost / Pricing
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Cost per full unit (case/keg/bottle)"
    )
    cost_per_base = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Auto-calculated: cost per ml/g/piece"
    )
    case_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total case cost"
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Selling price per unit"
    )
    
    # Inventory levels
    current_qty = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Current stock in base units"
    )
    par_level = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Minimum stock level"
    )
    
    # Storage location
    bin = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items',
        help_text="Default storage location/bin"
    )
    
    # Vendor / Origin
    vendor = models.CharField(
        max_length=120,
        blank=True,
        help_text="Supplier name"
    )
    country = models.CharField(
        max_length=120,
        blank=True,
        help_text="Country of origin"
    )
    region = models.CharField(
        max_length=120,
        blank=True,
        help_text="Production region"
    )
    subregion = models.CharField(
        max_length=120,
        blank=True,
        help_text="Sub-region/appellation"
    )
    producer = models.CharField(
        max_length=120,
        blank=True,
        help_text="Producer/manufacturer"
    )
    vineyard = models.CharField(
        max_length=120,
        blank=True,
        help_text="Vineyard/estate"
    )
    
    # Product attributes
    abv_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Alcohol by volume percentage"
    )
    vintage = models.CharField(
        max_length=10,
        blank=True,
        help_text="Year/vintage"
    )
    
    # Barcodes
    unit_upc = models.CharField(
        max_length=64,
        blank=True,
        help_text="Unit barcode/UPC"
    )
    case_upc = models.CharField(
        max_length=64,
        blank=True,
        help_text="Case barcode/UPC"
    )
    
    # Serving/Pour size (for price calculator)
    serving_size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Standard serving/pour size (e.g., 25, 150)"
    )
    serving_unit = models.CharField(
        max_length=10,
        blank=True,
        default='ml',
        help_text="Serving unit (ml, oz, cl)"
    )
    menu_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Menu price per serving"
    )
    
    # Flags
    active = models.BooleanField(
        default=True,
        help_text="Item is active for ordering"
    )
    hide_on_menu = models.BooleanField(
        default=False,
        help_text="Hide from customer menu"
    )

    class Meta:
        unique_together = ('hotel', 'sku')
        ordering = ['category__sort_order', 'sku']

    def __str__(self):
        return f"{self.sku} - {self.name}"

    def save(self, *args, **kwargs):
        """Auto-calculate cost_per_base on save"""
        if self.unit_cost and self.uom:
            self.cost_per_base = self.unit_cost / self.uom
        super().save(*args, **kwargs)

    @property
    def gp_percentage(self):
        """Calculate GP% if selling price exists"""
        if self.selling_price and self.cost_per_base:
            gp = ((self.selling_price - self.cost_per_base) /
                  self.selling_price) * 100
            return round(gp, 2)
        return None
    
    @property
    def is_below_par(self):
        """Check if current quantity is below par level"""
        return self.current_qty < self.par_level if self.par_level else False
    
    # Price calculator properties
    @property
    def pour_cost(self):
        """
        Calculate cost per serving/pour.
        Formula: serving_size × cost_per_base
        """
        if self.serving_size and self.cost_per_base:
            return self.serving_size * self.cost_per_base
        return None
    
    @property
    def pour_cost_percentage(self):
        """
        Calculate pour cost as percentage of menu price.
        Formula: (pour_cost / menu_price) × 100
        """
        if self.pour_cost and self.menu_price and self.menu_price > 0:
            return round((self.pour_cost / self.menu_price) * 100, 2)
        return None
    
    @property
    def profit_per_serving(self):
        """
        Calculate profit per serving.
        Formula: menu_price - pour_cost
        """
        if self.menu_price and self.pour_cost:
            return self.menu_price - self.pour_cost
        return None
    
    @property
    def profit_margin_percentage(self):
        """
        Calculate profit margin percentage.
        Formula: (profit / menu_price) × 100
        """
        if self.profit_per_serving and self.menu_price and \
           self.menu_price > 0:
            return round(
                (self.profit_per_serving / self.menu_price) * 100, 2
            )
        return None


class StockMovement(models.Model):
    """
    Tracks all stock movements: purchases, sales, waste,
    transfers, and adjustments.
    """
    PURCHASE = 'PURCHASE'
    SALE = 'SALE'
    WASTE = 'WASTE'
    TRANSFER_IN = 'TRANSFER_IN'
    TRANSFER_OUT = 'TRANSFER_OUT'
    ADJUSTMENT = 'ADJUSTMENT'

    MOVEMENT_TYPES = [
        (PURCHASE, 'Purchase/Delivery'),
        (SALE, 'Sale/Consumption'),
        (WASTE, 'Waste/Breakage'),
        (TRANSFER_IN, 'Transfer In'),
        (TRANSFER_OUT, 'Transfer Out'),
        (ADJUSTMENT, 'Stocktake Adjustment'),
    ]

    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='movements'
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Quantity in base units"
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Cost per base unit at time of movement"
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Invoice number, stocktake ID, etc."
    )
    notes = models.TextField(blank=True)
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return (
            f"{self.movement_type}: {self.quantity} "
            f"{self.item.base_unit} of {self.item.sku}"
        )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Update current_qty based on movement type
            if self.movement_type in [self.PURCHASE, self.TRANSFER_IN]:
                self.item.current_qty += self.quantity
            elif self.movement_type in [
                self.SALE,
                self.WASTE,
                self.TRANSFER_OUT
            ]:
                self.item.current_qty -= self.quantity
            elif self.movement_type == self.ADJUSTMENT:
                # Adjustment directly sets the variance
                self.item.current_qty += self.quantity

            self.item.save(update_fields=['current_qty'])


class Stocktake(models.Model):
    """
    Represents a stocktaking period for a hotel.
    """
    DRAFT = 'DRAFT'
    APPROVED = 'APPROVED'

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (APPROVED, 'Approved'),
    ]

    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='stocktakes'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_stocktakes'
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('hotel', 'period_start', 'period_end')
        ordering = ['-period_end']

    def __str__(self):
        return (
            f"{self.hotel.name} Stocktake: "
            f"{self.period_start} to {self.period_end}"
        )

    @property
    def is_locked(self):
        """Once approved, stocktake cannot be edited"""
        return self.status == self.APPROVED


class StocktakeLine(models.Model):
    """
    Individual line item in a stocktake with counted quantities
    and calculated expected/variance.
    """
    stocktake = models.ForeignKey(
        Stocktake,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='stocktake_lines'
    )

    # Opening balances (frozen at populate time)
    opening_qty = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Opening quantity in base units"
    )

    # Period movements (calculated from StockMovement)
    purchases = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000')
    )
    sales = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000')
    )
    waste = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000')
    )
    transfers_in = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000')
    )
    transfers_out = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000')
    )
    adjustments = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Prior adjustments in period"
    )

    # Counted quantities (user input)
    counted_full_units = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Full cases/kegs/bottles counted"
    )
    counted_partial_units = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Partial units (e.g., 7 bottles from a case)"
    )

    # Valuation (frozen at populate/approve)
    valuation_cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Cost per base unit for valuation"
    )

    class Meta:
        unique_together = ('stocktake', 'item')
        ordering = ['item__category__sort_order', 'item__sku']

    def __str__(self):
        return f"{self.stocktake} - {self.item.sku}"

    @property
    def counted_qty(self):
        """
        Convert mixed units to base units:
        counted_qty = (full_units * UOM + partial_units) * conversion
        """
        full_in_base = self.counted_full_units * self.item.uom
        return full_in_base + self.counted_partial_units

    @property
    def expected_qty(self):
        """
        Formula: expected = open + P + Tin - S - W - Tout + A
        All values in base units.
        """
        return (
            self.opening_qty +
            self.purchases +
            self.transfers_in -
            self.sales -
            self.waste -
            self.transfers_out +
            self.adjustments
        )

    @property
    def variance_qty(self):
        """
        Variance = counted - expected
        Positive = surplus, Negative = shortage
        """
        return self.counted_qty - self.expected_qty

    @property
    def expected_value(self):
        """Expected value at frozen cost"""
        return self.expected_qty * self.valuation_cost

    @property
    def counted_value(self):
        """Counted value at frozen cost"""
        return self.counted_qty * self.valuation_cost

    @property
    def variance_value(self):
        """Variance in monetary terms"""
        return self.counted_value - self.expected_value
