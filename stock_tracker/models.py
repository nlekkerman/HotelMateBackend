# models.py
from django.db import models
from decimal import Decimal
from datetime import date, timedelta
from calendar import monthrange


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
        """
        if self.uom and self.uom > 0:
            return self.unit_cost / self.uom
        return Decimal('0.0000')

    @property
    def total_stock_in_servings(self):
        """
        Convert all stock to servings for consistent calculations:

        SIZE-SPECIFIC HANDLING:
        
        Draught Beer (D) + Bag-in-Box (size contains "LT") + Dozen ("Doz"):
        - Full units = kegs/BIBs/cases
        - Partial units = individual servings (pints/serves/bottles)
        - Formula: (full_units × servings_per_unit) + partial_servings
        - Example Draught: (6 kegs × 88) + 39.75 pints = 567.75 pints
        - Example BIB: (1 BIB × 500) + 1 serve = 501 serves
        - Example Bottled: (0 cases × 12) + 145 bottles = 145 bottles
        
        All other items (Spirits, Wine, Individual items):
        - Full units = base units (bottles, units)
        - Partial units = fractional base units (0.70 = 0.70 of a bottle)
        - Formula: (full_units × servings) + (partial_units × servings)
        - Example Spirits: (2 bottles × 20) + (0.70 bottles × 20) = 54 shots
        """
        category = self.category_id
        
        # Draught, BIB (LT in size), and Dozen: partial = servings
        if (category == 'D') or (self.size and ('Doz' in self.size or 'LT' in self.size.upper())):
            full_servings = self.current_full_units * self.uom
            # Partial units are already in serving units
            return full_servings + self.current_partial_units
        else:
            # Spirits, Wine, Individual items: partial = fractional
            full_servings = self.current_full_units * self.uom
            partial_servings = self.current_partial_units * self.uom
            return full_servings + partial_servings

    @property
    def total_stock_value(self):
        """
        Total value of current stock at cost price
        Formula: total_servings × cost_per_serving
        """
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
        Others: partial = fractional units of the base unit
        """
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

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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

    @property
    def total_servings(self):
        """
        Calculate total servings from full + partial units
        Matches StockItem.total_stock_in_servings logic
        """
        category = self.item.category_id
        
        # Draught, BIB (LT), Dozen: partial = servings
        if (category == 'D') or (self.item.size and ('Doz' in self.item.size or 'LT' in self.item.size.upper())):
            full_servings = self.closing_full_units * self.item.uom
            return full_servings + self.closing_partial_units
        else:
            # Spirits, Wine, Individual: partial = fractional
            full_servings = self.closing_full_units * self.item.uom
            partial_servings = self.closing_partial_units * self.item.uom
            return full_servings + partial_servings
    
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
        - Others: 0
        """
        from decimal import Decimal
        
        if not opening_servings:
            return 0
        
        category = self.item.category_id
        servings = Decimal(str(opening_servings))
        uom = Decimal(str(self.item.uom))
        
        # Draught: convert pints to kegs
        if category == 'D' and uom > 0:
            kegs = int(servings / uom)
            return kegs
        
        # Dozen: convert bottles to cases
        if self.item.size and 'Doz' in self.item.size and uom > 0:
            dozens = int(servings / uom)
            return dozens
        
        return 0
    
    def calculate_opening_display_partial(self, opening_servings):
        """
        Calculate display partial units for opening stock
        - Draught (D): remaining pints
        - Dozen: remaining bottles
        - Others: opening_servings as-is
        """
        from decimal import Decimal
        
        if not opening_servings:
            return 0
        
        category = self.item.category_id
        servings = Decimal(str(opening_servings))
        uom = Decimal(str(self.item.uom))
        
        # Draught: remaining pints
        if category == 'D' and uom > 0:
            remaining = servings % uom
            return remaining
        
        # Dozen: remaining bottles
        if self.item.size and 'Doz' in self.item.size and uom > 0:
            remaining = servings % uom
            return remaining
        
        return opening_servings


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
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Update current stock based on movement type
            if self.movement_type in [self.PURCHASE, self.TRANSFER_IN]:
                # Add to partial units (servings)
                self.item.current_partial_units += self.quantity
            elif self.movement_type in [self.SALE, self.WASTE, self.TRANSFER_OUT]:
                # Subtract from partial units (servings)
                self.item.current_partial_units -= self.quantity
            elif self.movement_type == self.ADJUSTMENT:
                # Adjustment directly modifies
                self.item.current_partial_units += self.quantity

            self.item.save(update_fields=['current_partial_units'])


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
        ordering = ['item__category__code', 'item__sku']

    def __str__(self):
        return f"{self.stocktake} - {self.item.sku}"

    @property
    def counted_qty(self):
        """
        Convert mixed units to servings (base units):
        Matches StockItem.total_stock_in_servings logic
        
        Draught (D) + BIB (LT) + Dozen (Doz):
        - Full units = kegs/BIBs/cases
        - Partial units = pints/serves/bottles (ALREADY servings)
        - Formula: (full × servings_per_unit) + partial
        
        All other items (Spirits, Wine, Individual):
        - Full units = bottles/units
        - Partial units = fractional units
        - Formula: (full × servings) + (partial × servings)
        """
        category = self.item.category_id
        
        # Draught + BIB + Dozen: partial = servings
        if (category == 'D') or (self.item.size and ('Doz' in self.item.size or 'LT' in self.item.size.upper())):
            full_servings = self.counted_full_units * self.item.uom
            return full_servings + self.counted_partial_units
        else:
            # Spirits, Wine, Individual: partial = fractional
            full_servings = self.counted_full_units * self.item.uom
            partial_servings = self.counted_partial_units * self.item.uom
            return full_servings + partial_servings

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
