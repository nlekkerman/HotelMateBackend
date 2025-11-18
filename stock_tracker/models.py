# models.py
from django.db import models
from decimal import Decimal
from datetime import date
from calendar import monthrange


# ============================================================================
# MINERALS SERVING SIZE CONSTANTS
# ============================================================================
# Serving sizes for Minerals & Syrups subcategories
SYRUP_SERVING_SIZE = Decimal('35')  # 35ml per serving (standard shot)
JUICE_SERVING_SIZE = Decimal('200')  # 200ml per serving
BIB_SERVING_SIZE = Decimal('0.2')  # 200ml = 0.2 liters per serving

# Import juice helpers for 3-level tracking (cases + bottles + ml)
from stock_tracker.juice_helpers import (
    bottles_to_cases_bottles_ml,
    cases_bottles_ml_to_servings,
    servings_to_cases_bottles_ml
)


# ============================================================================
# COCKTAIL RECIPE MODELS (Keep existing - not changing)
# ============================================================================

class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name="ingredients"
    )
    
    # OPTIONAL link to stock inventory item
    # This is for DISPLAY purposes only - does NOT affect stocktake
    linked_stock_item = models.ForeignKey(
        'StockItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_ingredients',
        help_text=(
            "Optional: Link this ingredient to a stock item for "
            "tracking cocktail consumption in inventory"
        )
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
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Selling price per cocktail"
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
    # Revenue tracking
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price per cocktail at time of consumption"
    )
    total_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total revenue (quantity_made × unit_price)"
    )
    total_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total ingredient cost for all cocktails made"
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

    def calculate_revenue(self):
        """Calculate total revenue based on quantity and cocktail price"""
        if self.cocktail.price:
            return Decimal(self.quantity_made) * self.cocktail.price
        return Decimal('0.00')

    def calculate_cost(self):
        """
        Calculate total ingredient cost for all cocktails made
        Returns the total cost based on ingredient usage
        """
        total = Decimal('0.00')
        for ri in self.cocktail.ingredients.all():
            # Get ingredient cost from stock items (if linked)
            # This is simplified - you may need to link ingredients to stock
            # For now, return 0 as placeholder
            pass
        return total

    @property
    def profit(self):
        """Calculate profit (revenue - cost)"""
        if self.total_revenue and self.total_cost:
            return self.total_revenue - self.total_cost
        return None

    def save(self, *args, **kwargs):
        """
        Auto-calculate revenue and cost on save.
        Also creates CocktailIngredientConsumption records.
        """
        # Set unit price from cocktail if not already set
        if not self.unit_price and self.cocktail.price:
            self.unit_price = self.cocktail.price
        
        # Calculate total revenue
        if self.unit_price:
            self.total_revenue = Decimal(self.quantity_made) * self.unit_price
        
        # Calculate total cost (simplified for now)
        self.total_cost = self.calculate_cost()
        
        # Check if this is a new record
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Create ingredient consumption records for NEW cocktail consumptions
        # These are tracked SEPARATELY and do NOT affect stocktake
        if is_new:
            self._create_ingredient_consumption_records()
    
    def _create_ingredient_consumption_records(self):
        """
        Create CocktailIngredientConsumption records for each ingredient.
        
        IMPORTANT: These records are for DISPLAY and optional manual merging.
        They do NOT automatically affect stocktake calculations.
        """
        for recipe_ingredient in self.cocktail.ingredients.all():
            # Calculate total quantity used for this batch
            total_quantity = (
                Decimal(str(recipe_ingredient.quantity_per_cocktail)) *
                Decimal(str(self.quantity_made))
            )
            
            # Get linked stock item if available
            stock_item = recipe_ingredient.ingredient.linked_stock_item
            
            # Create consumption record
            CocktailIngredientConsumption.objects.create(
                cocktail_consumption=self,
                ingredient=recipe_ingredient.ingredient,
                stock_item=stock_item,  # May be None
                quantity_used=total_quantity,
                unit=recipe_ingredient.ingredient.unit,
                # Cost tracking can be added later
                unit_cost=None,
                total_cost=None
            )


class CocktailIngredientConsumption(models.Model):
    """
    Tracks individual ingredient consumption from cocktail making.
    
    CRITICAL: This is COMPLETELY SEPARATE from stocktake logic.
    Does NOT automatically affect stocktake calculations.
    
    Purpose:
    - Track which ingredients were used when cocktails were made
    - Link ingredients to stock items (optional, for display)
    - Enable manual merging into stocktake (via explicit user action)
    
    The is_merged_to_stocktake flag prevents double-counting when user
    manually merges cocktail consumption into stocktake purchases.
    """
    cocktail_consumption = models.ForeignKey(
        CocktailConsumption,
        on_delete=models.CASCADE,
        related_name='ingredient_consumptions',
        help_text="The cocktail batch this ingredient was used in"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='consumptions',
        help_text="The ingredient that was consumed"
    )
    stock_item = models.ForeignKey(
        'StockItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cocktail_consumptions',
        help_text=(
            "Optional link to inventory stock item "
            "(if ingredient is in stocktake)"
        )
    )
    
    # Quantity consumed
    quantity_used = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Total quantity of this ingredient used in the batch"
    )
    unit = models.CharField(
        max_length=20,
        help_text="Unit of measurement (ml, cl, oz, etc.)"
    )
    
    # Cost tracking (optional)
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Cost per unit at time of consumption"
    )
    total_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total cost (quantity_used × unit_cost)"
    )
    
    # Merge tracking
    is_merged_to_stocktake = models.BooleanField(
        default=False,
        help_text="Has this consumption been manually merged into a stocktake?"
    )
    merged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this was merged into stocktake"
    )
    merged_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='merged_cocktail_consumptions',
        help_text="Staff member who merged this into stocktake"
    )
    merged_to_stocktake = models.ForeignKey(
        'Stocktake',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='merged_cocktail_consumptions',
        help_text="Which stocktake this was merged into"
    )
    
    # Metadata
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When this ingredient consumption was recorded"
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['stock_item', 'is_merged_to_stocktake']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['is_merged_to_stocktake']),
        ]
    
    def __str__(self):
        merged_status = " [MERGED]" if self.is_merged_to_stocktake else ""
        return (
            f"{self.quantity_used} {self.unit} of {self.ingredient.name} "
            f"for {self.cocktail_consumption.cocktail.name}{merged_status}"
        )
    
    def save(self, *args, **kwargs):
        """Auto-calculate total cost if unit cost is available"""
        if self.unit_cost and not self.total_cost:
            self.total_cost = self.quantity_used * self.unit_cost
        super().save(*args, **kwargs)
    
    @property
    def can_be_merged(self):
        """Check if this consumption can be merged into stocktake"""
        return (
            not self.is_merged_to_stocktake and
            self.stock_item is not None
        )
    
    def merge_to_stocktake(self, stocktake, staff):
        """
        Mark this consumption as merged to a specific stocktake.
        
        DOES NOT modify stocktake data - that's done separately in the view.
        This only updates the tracking flags.
        """
        from django.utils import timezone
        
        if self.is_merged_to_stocktake:
            raise ValueError("This consumption has already been merged")
        
        if not self.stock_item:
            raise ValueError("Cannot merge - no stock item linked")
        
        self.is_merged_to_stocktake = True
        self.merged_at = timezone.now()
        self.merged_by = staff
        self.merged_to_stocktake = stocktake
        self.save()


# ============================================================================
# REFACTORED STOCK TRACKER MODELS
# ============================================================================

class StockCategory(models.Model):
    """
    Categories auto-created from SKU prefix
    D = Draught Beer
    B = Bottled Beer
    S = Spirits
    W = Wine
    M = Minerals & Syrups
    """
    code = models.CharField(
        max_length=1,
        unique=True,
        primary_key=True,
        default='X'
    )
    name = models.CharField(max_length=50, default='Unknown')

    class Meta:
        verbose_name_plural = 'Stock Categories'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class StockItem(models.Model):
    """
    Universal stock item model that handles all product types.
    Category logic driven by SKU prefix (D, B, S, W, M).
    """
    # === IDENTIFICATION ===
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='stock_items'
    )
    sku = models.CharField(
        max_length=50,
        help_text="Product code (prefix determines category: D/B/S/W/M)"
    )
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        StockCategory,
        on_delete=models.PROTECT,
        related_name='stock_items',
        help_text="Auto-set from SKU prefix"
    )
    
    # === MINERALS SUBCATEGORY ===
    # Only used for category 'M' - defines storage and serving logic
    subcategory = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('SOFT_DRINKS', 'Soft Drinks (Bottled)'),
            ('SYRUPS', 'Syrups & Flavourings'),
            ('JUICES', 'Juices & Lemonades'),
            ('CORDIALS', 'Cordials'),
            ('BIB', 'Bag-in-Box (18L)'),
            ('BULK_JUICES', 'Bulk Juices (Individual Bottles)'),
        ],
        help_text="Sub-category for Minerals (M) items only"
    )

    # === SIZE & PACKAGING ===
    size = models.CharField(
        max_length=50,
        help_text="Display format: '50Lt', '70cl', 'Doz'"
    )
    size_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Numeric size: 50, 70, 330"
    )
    size_unit = models.CharField(
        max_length=10,
        help_text="Unit: L, cl, ml, Doz"
    )

    # === UNIT OF MEASURE (UOM) ===
    # The meaning changes by category:
    # D (Draught): pints per keg
    # B (Bottled): bottles per case (usually 12)
    # S (Spirits): shots per bottle
    # W (Wine): glasses per bottle
    # M (Minerals): varies
    uom = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Servings per unit (pints/keg, bottles/case, shots/bottle)"
    )

    # === COSTING ===
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Cost per FULL unit (keg, case, bottle)"
    )

    # === CURRENT STOCK ===
    # We track both full units AND partial units
    current_full_units = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Full units: kegs, cases, bottles"
    )
    current_partial_units = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        help_text="Partial units: pints, loose bottles, % of bottle"
    )
    
    # === INVENTORY MANAGEMENT ===
    par_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum servings to keep in stock (reorder point)"
    )

    # === SELLING PRICES ===
    menu_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Selling price per serving (pint/bottle/shot/glass)"
    )
    menu_price_large = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Large serving price (e.g., double shot, large wine)"
    )
    bottle_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Selling price for whole bottle"
    )
    promo_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Promotional/happy hour price"
    )

    # === FLAGS ===
    available_on_menu = models.BooleanField(
        default=True,
        help_text="Currently available for sale"
    )
    available_by_bottle = models.BooleanField(
        default=False,
        help_text="Can be sold as whole bottle"
    )
    active = models.BooleanField(default=True)

    # === METADATA ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('hotel', 'sku')
        ordering = ['category__code', 'sku']

    def __str__(self):
        return f"{self.sku} - {self.name}"

    def save(self, *args, **kwargs):
        """Auto-set category from SKU prefix"""
        if self.sku and not hasattr(self, '_category_set'):
            prefix = self.sku[0].upper()
            try:
                self.category = StockCategory.objects.get(code=prefix)
            except StockCategory.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    # === CALCULATED PROPERTIES ===

    @property
    def cost_per_serving(self):
        """
        Cost per individual serving (pint, bottle, shot, glass)
        Formula: unit_cost ÷ uom
        BIB Exception: unit_cost ÷ servings_per_box
        """
        # BIB special case: calculate from serving size (36ml)
        if (self.category_id == 'M' and
                self.subcategory == 'BIB' and
                self.size_value and
                self.size_value > 0):
            # 18L box = 18000ml, divide by serving size (36ml)
            box_ml = Decimal('18000')
            servings_per_box = box_ml / self.size_value
            return self.unit_cost / servings_per_box
        
        if self.uom and self.uom > 0:
            return self.unit_cost / self.uom
        return Decimal('0.0000')

    @property
    def total_stock_in_servings(self):
        """
        Convert all stock to servings for consistent calculations.
        
        Minerals (M) - handled by subcategory:
          SOFT_DRINKS: cases + bottles → bottles (1 bottle = 1 serving)
          SYRUPS: bottles + ml → servings (35ml per serving)
          JUICES: bottles + ml → servings (200ml per serving)
          CORDIALS: cases + bottles → bottles (no serving conversion)
          BIB: boxes + liters → servings (200ml per serving)
        
        Draught (D): kegs + pints → pints
        Bottled (B): cases + bottles → bottles
        Spirits (S): bottles + fractional → shots
        Wine (W): bottles + fractional → glasses
        """
        category = self.category_id
        
        # Handle Minerals subcategories
        if category == 'M' and self.subcategory:
            if self.subcategory == 'SOFT_DRINKS':
                # Cases + Bottles → bottles
                # Full = cases, Partial = bottles (0-11)
                # UOM = 12 bottles/case
                # Serving = 1 bottle
                return (self.current_full_units * self.uom) + self.current_partial_units
            
            elif self.subcategory == 'SYRUPS':
                # Individual bottles (decimal input)
                # User enters total bottles as decimal (e.g., 10.5 bottles)
                # Stored as: current_full_units + current_partial_units = total bottles
                # Example: 10.5 bottles × 700ml = 7350ml ÷ 35ml = 210 servings
                
                total_bottles = self.current_full_units + self.current_partial_units
                total_ml = total_bottles * self.uom
                return total_ml / SYRUP_SERVING_SIZE  # ml → servings (35ml)
            
            elif self.subcategory == 'JUICES':
                # Cases + Bottles (with decimals) → servings (200ml)
                # current_full_units = cases (whole number)
                # current_partial_units = bottles (can be 3.5, 11.75, etc.)
                #   - Integer part = full bottles
                #   - Decimal part = ml (e.g., 0.5 × 1000ml = 500ml)
                
                cases = self.current_full_units
                bottles_with_fraction = self.current_partial_units
                
                # Split bottles into whole bottles + ml
                full_bottles = int(bottles_with_fraction)
                ml = (bottles_with_fraction - full_bottles) * self.uom
                
                # Calculate servings using 3-level helper
                return cases_bottles_ml_to_servings(
                    cases, full_bottles, ml,
                    bottle_size_ml=float(self.uom),
                    bottles_per_case=12,
                    serving_size_ml=200
                )
            
            elif self.subcategory == 'CORDIALS':
                # Cases + Bottles → bottles (no serving conversion)
                # Full = cases, Partial = bottles
                # UOM = 12 bottles/case
                return (self.current_full_units * self.uom) + self.current_partial_units
            
            elif self.subcategory == 'BIB':
                # BIB: Storage only (no serving conversion)
                # Full = boxes, Partial = decimal fraction (e.g., 0.5)
                # UOM = 1 (individual box)
                # Return total boxes (e.g., 1.5 boxes)
                return self.current_full_units + self.current_partial_units
            
            elif self.subcategory == 'BULK_JUICES':
                # Individual bottles with decimals (NOT on menu)
                # current_full_units = whole bottles
                # current_partial_units = fractional bottles (e.g., 0.5)
                # UOM = 1 (individual bottles)
                # Return total bottles (e.g., 43 + 0.5 = 43.5 bottles)
                return self.current_full_units + self.current_partial_units
        
        # Draught: kegs + pints (partial = pints)
        if category == 'D':
            full_servings = self.current_full_units * self.uom
            return full_servings + self.current_partial_units
        
        # Bottled Beer: cases + bottles (partial = bottles)
        if category == 'B':
            full_servings = self.current_full_units * self.uom
            return full_servings + self.current_partial_units
        
        # Spirits, Wine: bottles + fractional (partial = fractional)
        if category in ['S', 'W']:
            full_servings = self.current_full_units * self.uom
            partial_servings = self.current_partial_units * self.uom
            return full_servings + partial_servings
        
        # Fallback for any uncategorized items
        full_servings = self.current_full_units * self.uom
        return full_servings + self.current_partial_units

    @property
    def total_stock_value(self):
        """
        Total value of current stock at cost price
        Formula: total_servings × cost_per_serving
        BIB Exception: total_boxes × unit_cost
        """
        # BIB uses unit_cost not cost_per_serving
        if (self.category_id == 'M' and
                self.subcategory == 'BIB'):
            total_boxes = (
                self.current_full_units + self.current_partial_units
            )
            return total_boxes * self.unit_cost
        return self.total_stock_in_servings * self.cost_per_serving

    @property
    def full_units_value(self):
        """Value of full units only (kegs, cases, bottles)"""
        return self.current_full_units * self.unit_cost

    @property
    def partial_units_value(self):
        """
        Value of partial units - size-specific handling
        
        Items sold by DOZEN ("Doz"): partial = individual bottles
        BIB: partial = fractional boxes at unit_cost
        Others: partial = fractional units of the base unit
        """
        # BIB: partial boxes valued at unit_cost
        if (self.category_id == 'M' and
                self.subcategory == 'BIB'):
            return self.current_partial_units * self.unit_cost
        
        # Check if item is sold by dozen
        if self.size and 'Doz' in self.size:
            # Partial bottles valued at cost per bottle (cost per serving)
            return self.current_partial_units * self.cost_per_serving
        else:
            # Partial fractional units valued at unit cost
            return self.current_partial_units * self.unit_cost

    # === PROFITABILITY METRICS ===

    @property
    def gross_profit_per_serving(self):
        """Profit per serving: menu_price - cost_per_serving"""
        if self.menu_price:
            return self.menu_price - self.cost_per_serving
        return None

    @property
    def gross_profit_percentage(self):
        """
        GP%: ((selling_price - cost) / selling_price) × 100
        Industry standard GP% for bars: 70-85%
        """
        if self.menu_price and self.menu_price > 0:
            gp = ((self.menu_price - self.cost_per_serving) / self.menu_price) * 100
            return round(gp, 2)
        return None

    @property
    def markup_percentage(self):
        """
        Markup%: ((selling_price - cost) / cost) × 100
        Shows how many times you mark up the cost
        """
        if self.cost_per_serving and self.cost_per_serving > 0 and self.menu_price:
            markup = ((self.menu_price - self.cost_per_serving) / self.cost_per_serving) * 100
            return round(markup, 2)
        return None

    @property
    def pour_cost_percentage(self):
        """
        Pour Cost%: (cost_per_serving / menu_price) × 100
        Target pour cost for spirits: 15-20%
        Target pour cost for beer: 20-25%
        Target pour cost for wine: 25-35%
        """
        if self.menu_price and self.menu_price > 0:
            pour_cost = (self.cost_per_serving / self.menu_price) * 100
            return round(pour_cost, 2)
        return None

    # === DISPLAY HELPERS (for frontend) ===

    @property
    def display_full_units(self):
        """
        Display-friendly full units for frontend
        For "Doz" items: converts bottles to cases
        Others: returns as-is
        """
        if self.size and 'Doz' in self.size and self.uom > 0:
            # Convert total bottles to cases
            total_bottles = self.current_partial_units
            cases = int(total_bottles / self.uom)
            return cases
        return self.current_full_units

    @property
    def display_partial_units(self):
        """
        Display-friendly partial units for frontend
        For "Doz" items: shows remaining bottles after cases
        Others: returns as-is
        """
        if self.size and 'Doz' in self.size and self.uom > 0:
            # Show remaining bottles after full cases
            total_bottles = self.current_partial_units
            remaining = total_bottles % self.uom
            return remaining
        return self.current_partial_units

    def suggest_menu_price(self, target_gp_percentage=75):
        """
        Suggest menu price based on target GP%
        Formula: menu_price = cost / (1 - (target_gp / 100))
        """
        if self.cost_per_serving and self.cost_per_serving > 0:
            suggested_price = self.cost_per_serving / (1 - (Decimal(str(target_gp_percentage)) / 100))
            # Round to nearest €0.50
            return round(suggested_price * 2) / 2
        return None

    # === DISPLAY HELPERS ===

    def get_stock_display(self):
        """
        Human-readable stock display
        Shows full + partial units in their original form
        """
        category_code = self.category_id

        if category_code == 'D':
            return (
                f"{self.current_full_units} kegs + "
                f"{self.current_partial_units} kegs"
            )
        elif category_code == 'B':
            return (
                f"{self.current_full_units} cases + "
                f"{self.current_partial_units} cases"
            )
        elif category_code in ['S', 'W']:
            return (
                f"{self.current_full_units} bottles + "
                f"{self.current_partial_units} bottles"
            )
        else:
            return (
                f"{self.current_full_units} + "
                f"{self.current_partial_units}"
            )


class StockPeriod(models.Model):
    """
    Defines different period types for stock comparison.
    Can be predefined (weekly, monthly) or custom date ranges.
    """
    WEEKLY = 'WEEKLY'
    MONTHLY = 'MONTHLY'
    QUARTERLY = 'QUARTERLY'
    YEARLY = 'YEARLY'
    CUSTOM = 'CUSTOM'

    PERIOD_TYPES = [
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
        (QUARTERLY, 'Quarterly'),
        (YEARLY, 'Yearly'),
        (CUSTOM, 'Custom Date Range'),
    ]

    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='stock_periods'
    )

    period_type = models.CharField(
        max_length=20,
        choices=PERIOD_TYPES
    )

    # Date range
    start_date = models.DateField()
    end_date = models.DateField()

    # Period identifiers (for predefined periods)
    year = models.IntegerField(help_text="2024, 2025, etc.")
    quarter = models.IntegerField(
        null=True,
        blank=True,
        help_text="1-4 for quarterly periods"
    )

    manual_sales_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Manually entered sales amount for the period"
    )
    manual_purchases_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Manually entered purchase costs for the period (COGS)"
    )
    month = models.IntegerField(
        null=True,
        blank=True,
        help_text="1-12 for monthly periods"
    )
    week = models.IntegerField(
        null=True,
        blank=True,
        help_text="1-52 for weekly periods"
    )

    # Display name
    period_name = models.CharField(
        max_length=100,
        help_text="e.g., 'October 2024', 'Q4 2024', 'Week 42 2024'"
    )

    # Status
    is_closed = models.BooleanField(
        default=False,
        help_text="Period is finalized and locked"
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_periods'
    )
    
    # Reopen tracking
    reopened_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this period was reopened"
    )
    reopened_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reopened_periods',
        help_text="Staff member who last reopened this period"
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Manual entry for total sales amount (when itemized sales are missing)
    manual_sales_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Manual total sales amount for the period (if itemized sales are missing)"
    )

    class Meta:
        ordering = ['-end_date', '-start_date']
        unique_together = ('hotel', 'period_type', 'start_date', 'end_date')

    def __str__(self):
        return f"{self.hotel.name} - {self.period_name}"
    
    def save(self, *args, **kwargs):
        """Auto-generate period_name if not provided"""
        if not self.period_name:
            month_names = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November',
                'December'
            ]
            
            if self.period_type == self.MONTHLY and self.month and self.year:
                self.period_name = f"{month_names[self.month-1]} {self.year}"
            elif self.period_type == self.QUARTERLY and self.quarter and self.year:
                self.period_name = f"Q{self.quarter} {self.year}"
            elif self.period_type == self.WEEKLY and self.week and self.year:
                self.period_name = f"Week {self.week} {self.year}"
            elif self.period_type == self.YEARLY and self.year:
                self.period_name = f"Year {self.year}"
            else:
                # For CUSTOM or if no specific identifiers
                self.period_name = f"{self.start_date} to {self.end_date}"
        
        # Auto-populate year, month, quarter from start_date if not provided
        if not self.year and self.start_date:
            self.year = self.start_date.year
        
        if self.period_type == self.MONTHLY and not self.month and self.start_date:
            self.month = self.start_date.month
        
        super().save(*args, **kwargs)

    @classmethod
    def create_monthly_period(cls, hotel, year, month):
        """Helper to create a monthly period"""
        start_date = date(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]

        return cls.objects.get_or_create(
            hotel=hotel,
            period_type=cls.MONTHLY,
            start_date=start_date,
            end_date=end_date,
            defaults={
                'year': year,
                'month': month,
                'period_name': f"{month_names[month-1]} {year}"
            }
        )

    @classmethod
    def create_quarterly_period(cls, hotel, year, quarter):
        """Helper to create a quarterly period"""
        quarter_months = {
            1: (1, 3),   # Q1: Jan-Mar
            2: (4, 6),   # Q2: Apr-Jun
            3: (7, 9),   # Q3: Jul-Sep
            4: (10, 12)  # Q4: Oct-Dec
        }

        start_month, end_month = quarter_months[quarter]
        start_date = date(year, start_month, 1)

        last_day = monthrange(year, end_month)[1]
        end_date = date(year, end_month, last_day)

        return cls.objects.get_or_create(
            hotel=hotel,
            period_type=cls.QUARTERLY,
            start_date=start_date,
            end_date=end_date,
            defaults={
                'year': year,
                'quarter': quarter,
                'period_name': f"Q{quarter} {year}"
            }
        )

    def get_previous_period(self):
        """Get the previous period of the same type"""
        if self.period_type == self.MONTHLY and self.month:
            prev_month = self.month - 1
            prev_year = self.year
            if prev_month == 0:
                prev_month = 12
                prev_year -= 1

            return StockPeriod.objects.filter(
                hotel=self.hotel,
                period_type=self.MONTHLY,
                year=prev_year,
                month=prev_month
            ).first()

        elif self.period_type == self.QUARTERLY and self.quarter:
            prev_quarter = self.quarter - 1
            prev_year = self.year
            if prev_quarter == 0:
                prev_quarter = 4
                prev_year -= 1

            return StockPeriod.objects.filter(
                hotel=self.hotel,
                period_type=self.QUARTERLY,
                year=prev_year,
                quarter=prev_quarter
            ).first()

        elif self.period_type == self.YEARLY:
            return StockPeriod.objects.filter(
                hotel=self.hotel,
                period_type=self.YEARLY,
                year=self.year - 1
            ).first()

        # For CUSTOM periods, find the most recent period ending before this one
        return StockPeriod.objects.filter(
            hotel=self.hotel,
            end_date__lt=self.start_date
        ).order_by('-end_date').first()

    def get_cocktail_sales(self):
        """
        Get cocktail consumptions for this period
        Returns queryset of CocktailConsumption
        """
        return CocktailConsumption.objects.filter(
            hotel=self.hotel,
            timestamp__gte=self.start_date,
            timestamp__lte=self.end_date
        )

    @property
    def cocktail_revenue(self):
        """Total revenue from cocktail sales in this period"""
        from django.db.models import Sum
        result = self.get_cocktail_sales().aggregate(
            total=Sum('total_revenue')
        )
        return result['total'] or Decimal('0.00')

    @property
    def cocktail_cost(self):
        """Total cost of cocktails made in this period"""
        from django.db.models import Sum
        result = self.get_cocktail_sales().aggregate(
            total=Sum('total_cost')
        )
        return result['total'] or Decimal('0.00')

    @property
    def cocktail_quantity(self):
        """Total number of cocktails made in this period"""
        from django.db.models import Sum
        result = self.get_cocktail_sales().aggregate(
            total=Sum('quantity_made')
        )
        return result['total'] or 0

    @property
    def analysis_total_sales_combined(self):
        """
        FOR ANALYSIS/REPORTING ONLY - NOT USED IN STOCKTAKE CALCULATIONS.
        
        Combines stock item sales revenue + cocktail sales revenue for
        business intelligence and reporting purposes.
        
        This does NOT affect:
        - Inventory calculations
        - Stocktake COGS
        - Variance calculations
        - Stock valuations
        
        Cocktails are tracked separately and only combined here for
        display/reporting purposes.
        """
        # Get stock sales from matching stocktakes
        stock_sales = Decimal('0.00')
        matching_stocktakes = Stocktake.objects.filter(
            hotel=self.hotel,
            period_start=self.start_date,
            period_end=self.end_date
        )
        for stocktake in matching_stocktakes:
            if stocktake.total_revenue:
                stock_sales += stocktake.total_revenue
        
        # Add cocktail revenue (separate tracking)
        return stock_sales + self.cocktail_revenue

    @property
    def analysis_total_cost_combined(self):
        """
        FOR ANALYSIS/REPORTING ONLY - NOT USED IN STOCKTAKE CALCULATIONS.
        
        Combines stock item COGS + cocktail costs for reporting.
        This does NOT affect stocktake calculations or inventory.
        """
        # Get stock COGS from matching stocktakes
        stock_cost = Decimal('0.00')
        matching_stocktakes = Stocktake.objects.filter(
            hotel=self.hotel,
            period_start=self.start_date,
            period_end=self.end_date
        )
        for stocktake in matching_stocktakes:
            if stocktake.total_cogs:
                stock_cost += stocktake.total_cogs
        
        # Add cocktail cost (separate tracking)
        return stock_cost + self.cocktail_cost

    @property
    def analysis_profit_combined(self):
        """
        FOR ANALYSIS/REPORTING ONLY - NOT USED IN STOCKTAKE CALCULATIONS.
        
        Combined profit from stock items + cocktails for reporting.
        This is purely for business intelligence displays.
        """
        return (self.analysis_total_sales_combined -
                self.analysis_total_cost_combined)


class PeriodReopenPermission(models.Model):
    """
    Tracks which staff members have permission to reopen closed periods.
    Only superusers can assign/revoke this permission.
    """
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='period_reopen_permissions'
    )
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name='period_reopen_permissions'
    )
    granted_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_reopen_permissions',
        help_text="Superuser who granted this permission"
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Permission can be revoked by setting to False"
    )
    can_grant_to_others = models.BooleanField(
        default=False,
        help_text="If True, this staff can grant permissions to other staff (like a manager). Only superusers can set this."
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('hotel', 'staff')
        ordering = ['-granted_at']

    def __str__(self):
        status = "Active" if self.is_active else "Revoked"
        manager_badge = " [Manager]" if self.can_grant_to_others else ""
        return f"{self.staff.user.username} - {self.hotel.name} ({status}){manager_badge}"


class StockSnapshot(models.Model):
    """
    Stock levels at a specific point in time (end of period).
    """
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='stock_snapshots'
    )
    item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='snapshots'
    )
    period = models.ForeignKey(
        StockPeriod,
        on_delete=models.CASCADE,
        related_name='snapshots'
    )

    # Stock levels at period end
    closing_full_units = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Full units at period end"
    )
    closing_partial_units = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Partial units at period end"
    )

    # Costs frozen at period end
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Cost per unit at period end"
    )
    cost_per_serving = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Cost per serving at period end"
    )

    # Calculated values
    closing_stock_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total value at period end"
    )

    # Selling prices (if tracked)
    menu_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Menu price at period end"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('hotel', 'item', 'period')
        ordering = ['-period__end_date', 'item__sku']

    def __str__(self):
        return f"{self.item.sku} - {self.period.period_name}"

    @staticmethod
    def split_bottles_into_cases_and_remainder(total_bottles, item):
        """
        Split total bottles into cases + remaining bottles for Doz items.
        Used when saving closing stock for items with 'Doz' size.
        
        Examples:
          - 279 bottles with UOM=12 → (23 cases, 3 bottles)
          - 169 bottles with UOM=12 → (14 cases, 1 bottle)
          - 10.5 bottles (Spirits) → (10.5, 0) - NOT split for non-Doz
        
        Args:
            total_bottles: Total number of bottles (Decimal)
            item: StockItem instance
            
        Returns:
            tuple: (full_units, partial_units) as Decimals
        """
        from decimal import Decimal
        
        # Only split for Doz items (Bottled Beer, Minerals SOFT_DRINKS/CORDIALS)
        if item.size and 'Doz' in item.size and item.uom > 0:
            # Split into cases + remainder bottles
            uom = Decimal(str(item.uom))
            full_cases = int(total_bottles / uom)
            remaining_bottles = total_bottles % uom
            return (Decimal(str(full_cases)), remaining_bottles)
        else:
            # For Spirits, Wine, Syrups, etc: keep as-is (e.g., 10.50 bottles)
            # Assume total_bottles already represents full + partial correctly
            return (Decimal('0.00'), total_bottles)

    def save(self, *args, **kwargs):
        """
        Override save to automatically split bottles into cases+bottles
        for Minerals with 'Doz' size (SOFT_DRINKS, CORDIALS).
        
        This ensures Minerals with Doz size work the same as Draught Beer:
        - Draught: kegs + pints
        - Bottled Beer: cases + bottles (already works via UI)
        - Minerals Doz: cases + bottles (auto-convert here)
        """
        from decimal import Decimal
        
        # Only auto-convert for Minerals (M) with Doz size
        if (self.item.category_id == 'M' and 
            self.item.size and 'Doz' in self.item.size and 
            self.item.uom > 0):
            
            # Check if full_units = 0 and partial has total bottles
            # This indicates data needs conversion
            if self.closing_full_units == 0 and self.closing_partial_units > 0:
                total_bottles = self.closing_partial_units
                uom = Decimal(str(self.item.uom))
                
                # Split into cases + remaining bottles
                full_cases = int(total_bottles / uom)
                remaining_bottles = total_bottles % uom
                
                self.closing_full_units = Decimal(str(full_cases))
                self.closing_partial_units = remaining_bottles
        
        super().save(*args, **kwargs)

    @property
    def total_servings(self):
        """
        Calculate total servings from full + partial units
        Matches StockItem.total_stock_in_servings logic
        """
        category = self.item.category_id
        
        # Draught: partial = servings (pints)
        if category == 'D':
            full_servings = self.closing_full_units * self.item.uom
            return full_servings + self.closing_partial_units
        
        # Bottled Beer (Doz), Soft Drinks, Cordials: partial = servings
        elif (self.item.size and 'Doz' in self.item.size) or (
            self.item.subcategory in ['SOFT_DRINKS', 'CORDIALS']
        ):
            full_servings = self.closing_full_units * self.item.uom
            return full_servings + self.closing_partial_units
        
        # Spirits, Wine, Syrups, BIB, Bulk Juices:
        # full + partial = total units (e.g., 10.5 bottles)
        elif category in ['S', 'W'] or self.item.subcategory in [
            'SYRUPS', 'BIB', 'BULK_JUICES'
        ]:
            total_units = (
                self.closing_full_units + self.closing_partial_units
            )
            return total_units * self.item.uom
        
        # Juices and other Minerals: partial = servings
        else:
            full_servings = self.closing_full_units * self.item.uom
            return full_servings + self.closing_partial_units
    
    @property
    def display_full_units(self):
        """
        Display-friendly full units for frontend UI
        - Draught (D): kegs
        - Dozen: cases
        - Others: closing_full_units as-is
        """
        category = self.item.category_id
        total_servings = self.total_servings
        
        # Draught: convert pints to kegs
        if category == 'D' and self.item.uom > 0:
            kegs = int(total_servings / self.item.uom)
            return kegs
        
        # Dozen: convert bottles to cases
        if self.item.size and 'Doz' in self.item.size and self.item.uom > 0:
            dozens = int(total_servings / self.item.uom)
            return dozens
        
        return self.closing_full_units
    
    @property
    def display_partial_units(self):
        """
        Display-friendly partial units for frontend UI
        - Draught (D): remaining pints after full kegs
        - Dozen: remaining bottles after full cases
        - Others: closing_partial_units as-is
        """
        category = self.item.category_id
        total_servings = self.total_servings
        
        # Draught: show remaining pints
        if category == 'D' and self.item.uom > 0:
            remaining_pints = total_servings % self.item.uom
            return remaining_pints
        
        # Dozen: show remaining bottles
        if self.item.size and 'Doz' in self.item.size and self.item.uom > 0:
            remaining_bottles = total_servings % self.item.uom
            return remaining_bottles
        
        return self.closing_partial_units
    
    def calculate_opening_display_full(self, opening_servings):
        """
        Calculate display full units for opening stock
        - Draught (D): kegs
        - Dozen: cases
        - BIB (LT): boxes
        - Others (Spirits, Wine, Individual): full bottles/units
        """
        from decimal import Decimal
        
        if not opening_servings:
            return 0
        
        category = self.item.category_id
        servings = Decimal(str(opening_servings))
        uom = Decimal(str(self.item.uom))
        
        if uom == 0:
            return 0
        
        # Draught: convert pints to kegs
        if category == 'D':
            kegs = int(servings / uom)
            return kegs
        
        # Dozen (Bottled Beers): convert bottles to cases
        if self.item.size and 'Doz' in self.item.size:
            dozens = int(servings / uom)
            return dozens
        
        # BIB (Bag in Box): convert liters to boxes
        if self.item.size and 'LT' in self.item.size.upper():
            boxes = int(servings / uom)
            return boxes
        
        # Spirits, Wine, Individual Minerals (Syrups, etc): full bottles/units
        # For these, closing_full_units represents the actual full bottles
        return int(self.closing_full_units)
    
    def calculate_opening_display_partial(self, opening_servings):
        """
        Calculate display partial units for opening stock
        - Draught (D): remaining pints after full kegs
        - Dozen: remaining bottles after full cases
        - BIB (LT): remaining liters after full boxes
        - Others (Spirits, Wine, Individual): fractional part (0.00-0.99)
        """
        from decimal import Decimal
        
        if not opening_servings:
            return 0
        
        category = self.item.category_id
        servings = Decimal(str(opening_servings))
        uom = Decimal(str(self.item.uom))
        
        if uom == 0:
            return servings
        
        # Draught: remaining pints after full kegs
        if category == 'D':
            remaining = servings % uom
            return remaining
        
        # Dozen (Bottled Beers): remaining bottles after full cases
        if self.item.size and 'Doz' in self.item.size:
            remaining = servings % uom
            return remaining
        
        # BIB (Bag in Box): remaining liters after full boxes
        if self.item.size and 'LT' in self.item.size.upper():
            remaining = servings % uom
            return remaining
        
        # Spirits, Wine, Individual Minerals (Syrups, etc): fractional bottles
        # For these, closing_partial_units represents the fractional part
        return self.closing_partial_units


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
    COCKTAIL_CONSUMPTION = 'COCKTAIL_CONSUMPTION'

    MOVEMENT_TYPES = [
        (PURCHASE, 'Purchase/Delivery'),
        (SALE, 'Sale/Consumption'),
        (WASTE, 'Waste/Breakage'),
        (TRANSFER_IN, 'Transfer In'),
        (TRANSFER_OUT, 'Transfer Out'),
        (ADJUSTMENT, 'Stocktake Adjustment'),
        (COCKTAIL_CONSUMPTION, 'Cocktail Ingredient Usage (Merged)'),
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
    period = models.ForeignKey(
        StockPeriod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movements',
        help_text="Period this movement belongs to"
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Quantity in servings (pints, bottles, shots)"
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Cost per serving at time of movement"
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
            f"servings of {self.item.sku}"
        )

    def save(self, *args, **kwargs):
        # Just save the movement - don't update StockItem.current_* fields
        # Those fields are now updated only when periods are closed
        # Real-time inventory tracking is done through period snapshots
        super().save(*args, **kwargs)
        
        # REMOVED: Auto-update of current_partial_units
        # Reason: Using period-based tracking, not real-time inventory
        # If you need real-time inventory, create a separate CurrentInventory model


class Location(models.Model):
    """
    Physical storage locations/bins.
    Examples: Bar Storage, Cellar A-12, Keg Room
    """
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='stock_locations'
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

class Stocktake(models.Model):
    from django.utils.functional import cached_property

    @cached_property
    def total_cogs(self):
        """
        Calculate total cost of goods sold.
        Priority:
        1. StockPeriod.manual_purchases_amount (single total value)
        2. Sum of manual_purchases_value + manual_waste_value from lines
        3. Sum of total_cost from Sale records
        """
        from django.db.models import Sum
        
        # Priority 1: Check period manual_purchases_amount
        period = None
        try:
            period = StockPeriod.objects.get(
                hotel=self.hotel,
                start_date=self.period_start,
                end_date=self.period_end
            )
        except StockPeriod.DoesNotExist:
            pass
        
        if period and period.manual_purchases_amount is not None:
            return period.manual_purchases_amount
        
        # Priority 2: Check if any lines have manual values
        manual_totals = self.lines.aggregate(
            purchases=Sum('manual_purchases_value'),
            waste=Sum('manual_waste_value')
        )
        
        manual_purchases = manual_totals['purchases'] or 0
        manual_waste = manual_totals['waste'] or 0
        manual_total = manual_purchases + manual_waste
        
        if manual_total > 0:
            return manual_total
        
        # Priority 3: Fallback to Sale records
        total = self.sales.aggregate(total=Sum('total_cost'))['total']
        return total or 0

    @property
    def total_revenue(self):
        """
        Calculate total sales revenue.
        Priority:
        1. Sum of manual_sales_value from lines
        2. StockPeriod.manual_sales_amount
        3. Sum of total_revenue from Sale records
        """
        from django.db.models import Sum
        
        # Check if any lines have manual sales values
        manual_sales = self.lines.aggregate(
            total=Sum('manual_sales_value')
        )['total']
        
        if manual_sales and manual_sales > 0:
            return manual_sales
        
        # Check period manual_sales_amount
        period = None
        try:
            period = StockPeriod.objects.get(
                hotel=self.hotel,
                start_date=self.period_start,
                end_date=self.period_end
            )
        except StockPeriod.DoesNotExist:
            pass
        
        if period and period.manual_sales_amount is not None:
            return period.manual_sales_amount
        
        # Fallback to Sale records
        total = self.sales.aggregate(total=Sum('total_revenue'))['total']
        return total or 0

    @property
    def gross_profit_percentage(self):
        revenue = self.total_revenue
        cogs = self.total_cogs
        if revenue and revenue > 0:
            gp = ((revenue - cogs) / revenue) * 100
            return round(gp, 2)
        return None

    @property
    def pour_cost_percentage(self):
        revenue = self.total_revenue
        cogs = self.total_cogs
        if revenue and revenue > 0:
            pour_cost = (cogs / revenue) * 100
            return round(pour_cost, 2)
        return None
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

    def get_category_totals(self, category_code=None):
        """
        Calculate expected_qty totals for entire categories.
        
        Args:
            category_code: Optional category code (D, B, S, W, M).
                          If None, returns totals for all categories.
        
        Returns:
            dict: Category totals with opening, movements, expected, etc.
        
        Example:
            {
                'D': {
                    'category_name': 'Draught Beer',
                    'opening_qty': Decimal('1250.0000'),
                    'purchases': Decimal('500.0000'),
                    'waste': Decimal('25.0000'),
                    'transfers_in': Decimal('0.0000'),
                    'transfers_out': Decimal('0.0000'),
                    'adjustments': Decimal('0.0000'),
                    'expected_qty': Decimal('1725.0000'),
                    'counted_qty': Decimal('1720.0000'),
                    'variance_qty': Decimal('-5.0000'),
                    'opening_value': Decimal('3125.00'),
                    'purchases_value': Decimal('1250.00'),
                    'expected_value': Decimal('4300.00'),
                    'counted_value': Decimal('4287.50'),
                    'variance_value': Decimal('-12.50'),
                    'item_count': 15
                }
            }
        
        Note: This method uses @property calculations from StocktakeLine
        (expected_qty, counted_qty, variance_qty, expected_value,
        counted_value, variance_value) which are computed dynamically
        from the current database values. No caching is involved.
        """
        # Fetch fresh data from database
        lines = self.lines.select_related('item', 'item__category')
        
        if category_code:
            lines = lines.filter(item__category__code=category_code)
        
        # Group by category
        categories = {}
        
        for line in lines:
            cat_code = line.item.category.code
            
            if cat_code not in categories:
                categories[cat_code] = {
                    'category_code': cat_code,
                    'category_name': line.item.category.name,
                    'opening_qty': Decimal('0.0000'),
                    'purchases': Decimal('0.0000'),
                    'waste': Decimal('0.0000'),
                    'transfers_in': Decimal('0.0000'),
                    'transfers_out': Decimal('0.0000'),
                    'adjustments': Decimal('0.0000'),
                    'expected_qty': Decimal('0.0000'),
                    'counted_qty': Decimal('0.0000'),
                    'variance_qty': Decimal('0.0000'),
                    'opening_value': Decimal('0.00'),
                    'purchases_value': Decimal('0.00'),
                    'expected_value': Decimal('0.00'),
                    'counted_value': Decimal('0.00'),
                    'variance_value': Decimal('0.00'),
                    'manual_purchases_value': Decimal('0.00'),
                    'item_count': 0
                }
            
            cat = categories[cat_code]
            
            # Sum all movements
            cat['opening_qty'] += line.opening_qty
            cat['purchases'] += line.purchases
            cat['waste'] += line.waste
            cat['transfers_in'] += line.transfers_in
            cat['transfers_out'] += line.transfers_out
            cat['adjustments'] += line.adjustments
            
            # Sum calculated values
            cat['expected_qty'] += line.expected_qty
            cat['counted_qty'] += line.counted_qty
            cat['variance_qty'] += line.variance_qty
            
            # Sum monetary values
            cat['opening_value'] += line.opening_value
            cat['purchases_value'] += line.purchases_value
            cat['expected_value'] += line.expected_value
            cat['counted_value'] += line.counted_value
            cat['variance_value'] += line.variance_value
            
            # Sum manual overrides
            if line.manual_purchases_value:
                cat['manual_purchases_value'] += line.manual_purchases_value
            
            cat['item_count'] += 1
        
        # Return single category if specified
        if category_code:
            return categories.get(category_code, None)
        
        return categories


class Sale(models.Model):
    """
    Independent Sales model to track all sales/consumption.
    Replaces the old sales field in StocktakeLine.
    Allows flexible sales tracking and calculations.
    
    Sales can be created:
    1. Standalone (stocktake=None) - Independent sales tracking
    2. Linked to stocktake - For period reporting and merging with inventory
    """
    stocktake = models.ForeignKey(
        Stocktake,
        on_delete=models.CASCADE,
        related_name='sales',
        null=True,
        blank=True,
        help_text="Optional: Stocktake period this sale belongs to. If None, sale is standalone."
    )
    item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='sales',
        help_text="Item that was sold"
    )
    
    # Sales quantity (in servings/base units)
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Quantity sold in servings (pints, bottles, shots, glasses)"
    )
    
    # Cost and revenue
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Cost per serving at time of sale"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Selling price per serving (for revenue calculation)"
    )
    
    # Calculated totals (for easier querying)
    total_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total cost of goods sold (quantity × unit_cost)"
    )
    total_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total revenue (quantity × unit_price)"
    )
    
    # Metadata
    sale_date = models.DateField(
        help_text="Date of sale"
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sales'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sale_date', '-created_at']
        indexes = [
            models.Index(fields=['stocktake', 'item']),
            models.Index(fields=['sale_date']),
        ]

    def __str__(self):
        return (
            f"Sale: {self.quantity} × {self.item.sku} "
            f"on {self.sale_date}"
        )

    def save(self, *args, **kwargs):
        """Auto-calculate totals before saving"""
        self.total_cost = self.quantity * self.unit_cost
        if self.unit_price:
            self.total_revenue = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    @property
    def gross_profit(self):
        """Calculate gross profit if revenue is available"""
        if self.total_revenue:
            return self.total_revenue - self.total_cost
        return None

    @property
    def gross_profit_percentage(self):
        """Calculate GP% if revenue is available"""
        if self.total_revenue and self.total_revenue > 0:
            profit = self.total_revenue - self.total_cost
            gp = (profit / self.total_revenue) * 100
            return round(gp, 2)
        return None

    @property
    def pour_cost_percentage(self):
        """
        Calculate Pour Cost % (inverse of GP%)
        Pour Cost % = (COGS / Revenue) × 100
        Shows what percentage of revenue goes to product costs
        Target pour cost for bars: 15-30%
        """
        if self.total_revenue and self.total_revenue > 0:
            pour_cost = (self.total_cost / self.total_revenue) * 100
            return round(pour_cost, 2)
        return None


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

    # Manual override fields for direct entry (optional)
    manual_purchases_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Manual override: Total purchase value in period (€)"
    )
    manual_waste_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Manual override: Total waste value in period (€)"
    )
    manual_sales_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Manual override: Total sales revenue in period (€)"
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
        ordering = ['item__category__code', 'item__sku']

    def __str__(self):
        return f"{self.stocktake} - {self.item.sku}"

    @property
    def sales_qty(self):
        """
        Calculate total sales from related Sale records.
        This replaces the old sales field calculation.
        """
        from django.db.models import Sum
        
        total = self.stocktake.sales.filter(
            item=self.item
        ).aggregate(
            total=Sum('quantity')
        )['total']
        
        return total or Decimal('0.0000')

    @property
    def counted_qty(self):
        """
        Convert counted units to servings.
        Matches StockItem.total_stock_in_servings logic exactly.
        
        Minerals (M) - handled by subcategory:
          SOFT_DRINKS: counted_cases + counted_bottles → bottles
          SYRUPS: counted_bottles + counted_ml → servings (35ml)
          JUICES: counted_bottles + counted_ml → servings (200ml)
          CORDIALS: counted_cases + counted_bottles → bottles
          BIB: counted_boxes + counted_liters → servings (200ml)
        
        Draught (D): counted_kegs + counted_pints → pints
        Bottled (B): counted_cases + counted_bottles → bottles
        Spirits (S): counted_bottles + counted_fractional → shots
        Wine (W): counted_bottles + counted_fractional → glasses
        """
        category = self.item.category_id
        
        # Handle Minerals subcategories
        if category == 'M' and self.item.subcategory:
            if self.item.subcategory == 'SOFT_DRINKS':
                # Cases + Bottles → bottles
                # counted_full_units = cases
                # counted_partial_units = bottles (0-11)
                return (self.counted_full_units * self.item.uom) + self.counted_partial_units
            
            elif self.item.subcategory == 'SYRUPS':
                # Individual bottles (decimal input)
                # User enters total bottles as decimal (e.g., 10.5 bottles)
                # Stored as: counted_full_units + counted_partial_units = total bottles
                # Example: 10.5 bottles × 700ml = 7350ml ÷ 35ml = 210 servings
                
                total_bottles = self.counted_full_units + self.counted_partial_units
                total_ml = total_bottles * self.item.uom
                return total_ml / SYRUP_SERVING_SIZE  # ml → servings (35ml)
            
            elif self.item.subcategory == 'JUICES':
                # Cases + Bottles (with decimals) → servings (200ml)
                # counted_full_units = cases (whole number)
                # counted_partial_units = bottles (can be 3.5, 11.75, etc.)
                #   - Integer part = full bottles
                #   - Decimal part = ml (e.g., 0.5 × 1000ml = 500ml)
                
                cases = self.counted_full_units
                bottles_with_fraction = self.counted_partial_units
                
                # Split bottles into whole bottles + ml
                full_bottles = int(bottles_with_fraction)
                ml = (bottles_with_fraction - full_bottles) * self.item.uom
                
                # Calculate servings using 3-level helper
                return cases_bottles_ml_to_servings(
                    cases, full_bottles, ml,
                    bottle_size_ml=float(self.item.uom),
                    bottles_per_case=12,
                    serving_size_ml=200
                )
            
            elif self.item.subcategory == 'CORDIALS':
                # Cases + Bottles → bottles (no serving conversion)
                # counted_full_units = cases
                # counted_partial_units = bottles
                return (self.counted_full_units * self.item.uom) + self.counted_partial_units
            
            elif self.item.subcategory == 'BIB':
                # BIB: Storage only (no serving conversion)
                # counted_full_units = boxes
                # counted_partial_units = decimal fraction (e.g., 0.5)
                # Return total boxes for stocktake tracking
                return self.counted_full_units + self.counted_partial_units
            
            elif self.item.subcategory == 'BULK_JUICES':
                # Individual bottles with decimals (NOT on menu)
                # counted_full_units = whole bottles
                # counted_partial_units = fractional (e.g., 0.5)
                # Return total bottles (e.g., 43 + 0.5 = 43.5 bottles)
                return self.counted_full_units + self.counted_partial_units
        
        # Draught: kegs + pints (partial = pints)
        if category == 'D':
            full_servings = self.counted_full_units * self.item.uom
            return full_servings + self.counted_partial_units
        
        # Bottled Beer: cases + bottles (partial = bottles)
        if category == 'B':
            full_servings = self.counted_full_units * self.item.uom
            return full_servings + self.counted_partial_units
        
        # Spirits, Wine: bottles + fractional (partial = fractional)
        if category in ['S', 'W']:
            full_servings = self.counted_full_units * self.item.uom
            partial_servings = self.counted_partial_units * self.item.uom
            return full_servings + partial_servings
        
        # Fallback for any uncategorized items
        full_servings = self.counted_full_units * self.item.uom
        return full_servings + self.counted_partial_units

    @property
    def expected_qty(self):
        """
        Formula: expected = opening + purchases - waste
        Sales are NOT included - calculated separately outside stocktake.
        All values in base units.
        """
        return (
            self.opening_qty +
            self.purchases -
            self.waste
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
        # BIB and SYRUPS: Use unit_cost (bottles/boxes), not serving cost
        if (self.item.category_id == 'M' and
                self.item.subcategory in ['BIB', 'SYRUPS']):
            return self.expected_qty * self.item.unit_cost
        return self.expected_qty * self.valuation_cost

    @property
    def counted_value(self):
        """Counted value at frozen cost"""
        # BIB and SYRUPS: value by unit_cost (per bottle/box), not serving cost
        if (self.item.category_id == 'M' and
                self.item.subcategory in ['BIB', 'SYRUPS']):
            total_units = (
                self.counted_full_units + self.counted_partial_units
            )
            return total_units * self.item.unit_cost

        return self.counted_qty * self.valuation_cost

    @property
    def variance_value(self):
        """Variance in monetary terms"""
        return self.counted_value - self.expected_value

    @property
    def opening_value(self):
        """Opening stock value at frozen cost"""
        # BIB and SYRUPS: Use unit_cost (bottles/boxes), not serving cost
        if (self.item.category_id == 'M' and
                self.item.subcategory in ['BIB', 'SYRUPS']):
            return self.opening_qty * self.item.unit_cost
        return self.opening_qty * self.valuation_cost

    @property
    def purchases_value(self):
        """Purchases value at frozen cost"""
        return self.purchases * self.valuation_cost
    
    # ========================================================================
    # COCKTAIL CONSUMPTION TRACKING (DISPLAY ONLY - DOES NOT AFFECT STOCKTAKE)
    # ========================================================================
    
    def get_available_cocktail_consumption(self):
        """
        Get unmerged cocktail consumption for this stock item during the period.
        
        CRITICAL: This is for DISPLAY ONLY.
        Does NOT affect expected_qty, variance_qty, or any stocktake calculations.
        
        Returns:
            QuerySet of CocktailIngredientConsumption that:
            - Linked to this stock item
            - Not yet merged (is_merged_to_stocktake=False)
            - Within stocktake period dates
        """
        from django.utils import timezone
        from datetime import datetime
        
        # Convert dates to datetime for proper comparison
        start_dt = timezone.make_aware(
            datetime.combine(self.stocktake.period_start, datetime.min.time())
        )
        end_dt = timezone.make_aware(
            datetime.combine(self.stocktake.period_end, datetime.max.time())
        )
        
        return CocktailIngredientConsumption.objects.filter(
            stock_item=self.item,
            is_merged_to_stocktake=False,
            timestamp__gte=start_dt,
            timestamp__lte=end_dt
        )
    
    def get_merged_cocktail_consumption(self):
        """
        Get cocktail consumption that has been merged into this stocktake.
        
        Returns:
            QuerySet of CocktailIngredientConsumption that were merged
        """
        return CocktailIngredientConsumption.objects.filter(
            stock_item=self.item,
            is_merged_to_stocktake=True,
            merged_to_stocktake=self.stocktake
        )
    
    @property
    def available_cocktail_consumption_qty(self):
        """
        Total quantity of this item used in cocktails (unmerged).
        
        DISPLAY ONLY - does NOT affect stocktake calculations.
        Shows quantity that COULD be merged but hasn't been yet.
        """
        from django.db.models import Sum
        
        result = self.get_available_cocktail_consumption().aggregate(
            total=Sum('quantity_used')
        )
        return result['total'] or Decimal('0.0000')
    
    @property
    def merged_cocktail_consumption_qty(self):
        """
        Total quantity that has been merged from cocktails.
        
        DISPLAY ONLY - shows what was already merged.
        """
        from django.db.models import Sum
        
        result = self.get_merged_cocktail_consumption().aggregate(
            total=Sum('quantity_used')
        )
        return result['total'] or Decimal('0.0000')
    
    @property
    def available_cocktail_consumption_value(self):
        """
        Value of unmerged cocktail consumption.
        
        DISPLAY ONLY - shows potential value if merged.
        """
        return self.available_cocktail_consumption_qty * self.valuation_cost
    
    @property
    def merged_cocktail_consumption_value(self):
        """
        Value of merged cocktail consumption.
        
        DISPLAY ONLY - shows value that was merged.
        """
        return self.merged_cocktail_consumption_qty * self.valuation_cost
    
    @property
    def can_merge_cocktails(self):
        """
        Check if there's unmerged cocktail consumption available to merge.
        
        Frontend uses this to show/hide the "Merge Cocktails" button.
        """
        return self.available_cocktail_consumption_qty > 0
