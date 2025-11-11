"""
Test Sales and Cocktail Isolation
===================================

CRITICAL TESTS: Verify that cocktails and sales are NEVER mixed in calculations.

These tests ensure:
1. Cocktail sales DO NOT affect stocktake calculations
2. Cocktail consumption DOES NOT affect COGS
3. Cocktail revenue IS NOT included in StocktakeLine calculations
4. Combined values are ONLY used for reporting (analysis_* properties)
5. Stock item sales and cocktails remain separate in database
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from hotel.models import Hotel
from staff.models import Staff, Department
from stock_tracker.models import (
    StockCategory,
    StockItem,
    StockPeriod,
    Stocktake,
    StocktakeLine,
    Sale
)
from entertainment.models import (
    Cocktail,
    Ingredient,
    CocktailRecipe,
    CocktailConsumption
)
from datetime import date

User = get_user_model()


class SalesCocktailIsolationTest(TestCase):
    """
    Test that cocktails and stock item sales are completely isolated.
    """
    
    def setUp(self):
        """Create test data"""
        # Create hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            subdomain="test-hotel"
        )
        
        # Create user and staff
        self.user = User.objects.create_user(
            username="teststaff",
            email="test@test.com",
            password="testpass123"
        )
        
        self.department = Department.objects.create(
            name="Bar",
            hotel=self.hotel
        )
        
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            first_name="Test",
            last_name="Staff",
            department=self.department,
            position="Bartender"
        )
        
        # Create category
        self.category_spirits = StockCategory.objects.get_or_create(
            code='S',
            defaults={'name': 'Spirits'}
        )[0]
        
        # Create stock items
        self.vodka = StockItem.objects.create(
            hotel=self.hotel,
            sku="VOD001",
            name="Vodka",
            category=self.category_spirits,
            size="700ml",
            size_value=700,
            size_unit="ml",
            uom=Decimal('28'),  # 25 servings per bottle
            unit_cost=Decimal('15.00'),
            menu_price=Decimal('6.00'),
            current_full_units=10,
            current_partial_units=Decimal('250')
        )
        
        self.gin = StockItem.objects.create(
            hotel=self.hotel,
            sku="GIN001",
            name="Gin",
            category=self.category_spirits,
            size="700ml",
            size_value=700,
            size_unit="ml",
            uom=Decimal('28'),
            unit_cost=Decimal('18.00'),
            menu_price=Decimal('7.00'),
            current_full_units=8,
            current_partial_units=Decimal('224')
        )
        
        # Create period
        self.period = StockPeriod.objects.create(
            hotel=self.hotel,
            period_type='monthly',
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30),
            year=2025,
            month=11
        )
        
        # Create stocktake
        self.stocktake = Stocktake.objects.create(
            hotel=self.hotel,
            period_start=self.period.start_date,
            period_end=self.period.end_date,
            status='DRAFT'
        )
        
        # Create stocktake lines
        self.vodka_line = StocktakeLine.objects.create(
            stocktake=self.stocktake,
            item=self.vodka,
            opening_qty=Decimal('250'),  # 250 servings
            purchases=Decimal('280'),  # 10 bottles = 280 servings
            waste=Decimal('0'),
            transfers_in=Decimal('0'),
            transfers_out=Decimal('0'),
            adjustments=Decimal('0'),
            counted_full_units=8,
            counted_partial_units=Decimal('224'),  # 8*28 + 224 = 448 servings
            valuation_cost=self.vodka.cost_per_serving
        )
        
        self.gin_line = StocktakeLine.objects.create(
            stocktake=self.stocktake,
            item=self.gin,
            opening_qty=Decimal('224'),
            purchases=Decimal('224'),  # 8 bottles
            waste=Decimal('0'),
            transfers_in=Decimal('0'),
            transfers_out=Decimal('0'),
            adjustments=Decimal('0'),
            counted_full_units=6,
            counted_partial_units=Decimal('168'),  # 6*28 + 168 = 336 servings
            valuation_cost=self.gin.cost_per_serving
        )
        
        # Create ingredient for cocktail
        self.vodka_ingredient = Ingredient.objects.create(
            name="Vodka (Ingredient)",
            unit_of_measurement="ml",
            cost_per_unit=Decimal('0.50')
        )
        
        # Create cocktail
        self.martini = Cocktail.objects.create(
            name="Vodka Martini",
            menu_price=Decimal('12.00')
        )
        
        # Create cocktail recipe
        CocktailRecipe.objects.create(
            cocktail=self.martini,
            ingredient=self.vodka_ingredient,
            quantity=Decimal('50')  # 50ml
        )
    
    def test_cocktail_consumption_does_not_affect_stocktake_line(self):
        """
        CRITICAL: Verify cocktail consumption does NOT change StocktakeLine.
        """
        # Record initial stocktake line values
        initial_sales_qty = self.vodka_line.sales_qty
        initial_expected_qty = self.vodka_line.expected_qty
        initial_variance_qty = self.vodka_line.variance_qty
        initial_expected_value = self.vodka_line.expected_value
        
        # Create cocktail consumption
        CocktailConsumption.objects.create(
            stocktake=self.stocktake,
            cocktail=self.martini,
            quantity=Decimal('50'),  # 50 martinis sold
            unit_cost=Decimal('25.00'),
            unit_price=Decimal('12.00'),
            total_cost=Decimal('1250.00'),
            total_revenue=Decimal('600.00'),
            created_by=self.staff
        )
        
        # Refresh stocktake line
        self.vodka_line.refresh_from_db()
        
        # Verify stocktake line is UNCHANGED
        self.assertEqual(
            self.vodka_line.sales_qty,
            initial_sales_qty,
            "Cocktail consumption MUST NOT affect StocktakeLine.sales_qty"
        )
        self.assertEqual(
            self.vodka_line.expected_qty,
            initial_expected_qty,
            "Cocktail consumption MUST NOT affect StocktakeLine.expected_qty"
        )
        self.assertEqual(
            self.vodka_line.variance_qty,
            initial_variance_qty,
            "Cocktail consumption MUST NOT affect StocktakeLine.variance_qty"
        )
        self.assertEqual(
            self.vodka_line.expected_value,
            initial_expected_value,
            "Cocktail consumption MUST NOT affect StocktakeLine.expected_value"
        )
    
    def test_sale_affects_stocktake_line(self):
        """
        Verify that Sale records DO affect StocktakeLine (as expected).
        """
        # Record initial values
        initial_sales_qty = self.vodka_line.sales_qty
        
        # Create sale (50 vodka servings sold)
        Sale.objects.create(
            stocktake=self.stocktake,
            item=self.vodka,
            quantity=Decimal('50'),
            unit_cost=self.vodka.cost_per_serving,
            unit_price=self.vodka.menu_price,
            total_cost=Decimal('50') * self.vodka.cost_per_serving,
            total_revenue=Decimal('50') * self.vodka.menu_price,
            sale_date=date(2025, 11, 15),
            created_by=self.staff
        )
        
        # Refresh stocktake line
        self.vodka_line.refresh_from_db()
        
        # Verify sale IS counted
        new_sales_qty = self.vodka_line.sales_qty
        self.assertEqual(
            new_sales_qty,
            initial_sales_qty + Decimal('50'),
            "Sale SHOULD affect StocktakeLine.sales_qty"
        )
    
    def test_cocktail_and_sale_remain_separate(self):
        """
        Verify cocktails and sales are tracked in separate tables.
        """
        # Create sale
        sale = Sale.objects.create(
            stocktake=self.stocktake,
            item=self.vodka,
            quantity=Decimal('30'),
            unit_cost=self.vodka.cost_per_serving,
            unit_price=self.vodka.menu_price,
            total_cost=Decimal('30') * self.vodka.cost_per_serving,
            total_revenue=Decimal('30') * self.vodka.menu_price,
            sale_date=date(2025, 11, 15),
            created_by=self.staff
        )
        
        # Create cocktail consumption
        cocktail_consumption = CocktailConsumption.objects.create(
            stocktake=self.stocktake,
            cocktail=self.martini,
            quantity=Decimal('20'),
            unit_cost=Decimal('25.00'),
            unit_price=Decimal('12.00'),
            total_cost=Decimal('500.00'),
            total_revenue=Decimal('240.00'),
            created_by=self.staff
        )
        
        # Verify they exist in separate tables
        sales_count = Sale.objects.filter(stocktake=self.stocktake).count()
        cocktail_count = CocktailConsumption.objects.filter(
            stocktake=self.stocktake
        ).count()
        
        self.assertEqual(sales_count, 1, "Should have 1 Sale record")
        self.assertEqual(
            cocktail_count, 1, "Should have 1 CocktailConsumption record"
        )
        
        # Verify sale is linked to stock item
        self.assertEqual(sale.item, self.vodka)
        self.assertIsNone(
            getattr(sale, 'cocktail', None),
            "Sale should NOT have cocktail field"
        )
        
        # Verify cocktail consumption is linked to cocktail
        self.assertEqual(cocktail_consumption.cocktail, self.martini)
        self.assertIsNone(
            getattr(cocktail_consumption, 'item', None),
            "CocktailConsumption should NOT have item field"
        )
    
    def test_analysis_properties_combine_data(self):
        """
        Verify StockPeriod.analysis_* properties combine data for reporting.
        These should ONLY be used for display, not calculations.
        """
        # Create sales
        Sale.objects.create(
            stocktake=self.stocktake,
            item=self.vodka,
            quantity=Decimal('100'),
            unit_cost=self.vodka.cost_per_serving,
            unit_price=self.vodka.menu_price,
            total_cost=Decimal('100') * self.vodka.cost_per_serving,
            total_revenue=Decimal('100') * self.vodka.menu_price,
            sale_date=date(2025, 11, 15),
            created_by=self.staff
        )
        
        # Create cocktail consumptions
        CocktailConsumption.objects.create(
            stocktake=self.stocktake,
            cocktail=self.martini,
            quantity=Decimal('50'),
            unit_cost=Decimal('25.00'),
            unit_price=Decimal('12.00'),
            total_cost=Decimal('1250.00'),
            total_revenue=Decimal('600.00'),
            created_by=self.staff
        )
        
        # Get analysis totals
        combined_sales = self.period.analysis_total_sales_combined
        combined_cost = self.period.analysis_total_cost_combined
        combined_profit = self.period.analysis_profit_combined
        
        # Verify they include both stock + cocktails
        stock_revenue = Decimal('100') * self.vodka.menu_price  # 600
        cocktail_revenue = Decimal('600.00')
        expected_combined_revenue = stock_revenue + cocktail_revenue
        
        self.assertEqual(
            combined_sales,
            expected_combined_revenue,
            "analysis_total_sales_combined should include stock + cocktails"
        )
        
        # Verify these are for ANALYSIS ONLY
        # Check docstring mentions "ANALYSIS"
        property_doc = self.period.__class__.analysis_total_sales_combined.fget.__doc__
        self.assertIn(
            "ANALYSIS",
            property_doc.upper(),
            "analysis_* properties must have ANALYSIS in docstring"
        )
    
    def test_stocktake_cogs_excludes_cocktails(self):
        """
        CRITICAL: Verify Stocktake.total_cogs ONLY includes stock items.
        """
        # Create sales (stock items)
        Sale.objects.create(
            stocktake=self.stocktake,
            item=self.vodka,
            quantity=Decimal('100'),
            unit_cost=self.vodka.cost_per_serving,
            unit_price=self.vodka.menu_price,
            total_cost=Decimal('100') * self.vodka.cost_per_serving,
            total_revenue=Decimal('100') * self.vodka.menu_price,
            sale_date=date(2025, 11, 15),
            created_by=self.staff
        )
        
        # Create cocktail consumption
        CocktailConsumption.objects.create(
            stocktake=self.stocktake,
            cocktail=self.martini,
            quantity=Decimal('50'),
            unit_cost=Decimal('25.00'),
            unit_price=Decimal('12.00'),
            total_cost=Decimal('1250.00'),  # High cost
            total_revenue=Decimal('600.00'),
            created_by=self.staff
        )
        
        # Get stocktake COGS
        stocktake_cogs = self.stocktake.total_cogs
        
        # Calculate expected COGS (stock items only)
        expected_cogs = (
            (self.vodka_line.opening_qty + self.vodka_line.purchases -
             self.vodka_line.counted_qty) * self.vodka_line.valuation_cost +
            (self.gin_line.opening_qty + self.gin_line.purchases -
             self.gin_line.counted_qty) * self.gin_line.valuation_cost
        )
        
        # Verify COGS matches (no cocktail cost included)
        self.assertEqual(
            stocktake_cogs,
            expected_cogs,
            "Stocktake.total_cogs MUST ONLY include stock items, NOT cocktails"
        )
        
        # Verify cocktail cost is NOT included
        self.assertNotEqual(
            stocktake_cogs,
            expected_cogs + Decimal('1250.00'),
            "Cocktail cost must NOT be added to stocktake COGS"
        )
    
    def test_stocktake_revenue_excludes_cocktails(self):
        """
        CRITICAL: Verify Stocktake.total_revenue ONLY includes stock items.
        """
        # Create sales
        Sale.objects.create(
            stocktake=self.stocktake,
            item=self.vodka,
            quantity=Decimal('50'),
            unit_cost=self.vodka.cost_per_serving,
            unit_price=self.vodka.menu_price,
            total_cost=Decimal('50') * self.vodka.cost_per_serving,
            total_revenue=Decimal('50') * self.vodka.menu_price,
            sale_date=date(2025, 11, 15),
            created_by=self.staff
        )
        
        # Create cocktail consumption
        CocktailConsumption.objects.create(
            stocktake=self.stocktake,
            cocktail=self.martini,
            quantity=Decimal('100'),
            unit_cost=Decimal('25.00'),
            unit_price=Decimal('12.00'),
            total_cost=Decimal('2500.00'),
            total_revenue=Decimal('1200.00'),  # Large revenue
            created_by=self.staff
        )
        
        # Get stocktake revenue
        stocktake_revenue = self.stocktake.total_revenue
        
        # Calculate expected revenue (stock items only)
        stock_sales = Sale.objects.filter(stocktake=self.stocktake)
        expected_revenue = sum(
            sale.total_revenue for sale in stock_sales
        )
        
        # Verify revenue matches (no cocktail revenue included)
        self.assertEqual(
            stocktake_revenue,
            expected_revenue,
            "Stocktake.total_revenue MUST ONLY include stock items"
        )
        
        # Verify cocktail revenue is NOT included
        self.assertNotEqual(
            stocktake_revenue,
            expected_revenue + Decimal('1200.00'),
            "Cocktail revenue must NOT be added to stocktake revenue"
        )


class AnalysisUtilitiesIsolationTest(TestCase):
    """
    Test that analysis utilities never modify data.
    """
    
    def test_combine_sales_data_is_pure_function(self):
        """
        Verify combine_sales_data() doesn't modify inputs.
        """
        from stock_tracker.utils.sales_analysis import combine_sales_data
        
        general_sales = {
            'revenue': Decimal('1000.00'),
            'cost': Decimal('400.00'),
            'count': 100
        }
        
        cocktail_sales = {
            'revenue': Decimal('500.00'),
            'cost': Decimal('200.00'),
            'count': 50
        }
        
        # Make copies
        general_copy = general_sales.copy()
        cocktail_copy = cocktail_sales.copy()
        
        # Call function
        result = combine_sales_data(general_sales, cocktail_sales)
        
        # Verify inputs unchanged
        self.assertEqual(general_sales, general_copy)
        self.assertEqual(cocktail_sales, cocktail_copy)
        
        # Verify result is correct
        self.assertEqual(
            result['total_revenue'],
            Decimal('1500.00')
        )
        self.assertEqual(
            result['total_cost'],
            Decimal('600.00')
        )
