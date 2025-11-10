"""
Test to verify that cocktail sales are completely isolated from stocktake calculations.
This test confirms that changing cocktail data does NOT affect stocktake totals.

Run with: python test_cocktail_stocktake_isolation.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from datetime import date
from django.contrib.auth import get_user_model
from hotel.models import Hotel
from staff.models import Staff
from stock_tracker.models import (
    StockCategory, StockItem, StockPeriod, Stocktake, Sale,
    CocktailRecipe, CocktailConsumption, Ingredient, RecipeIngredient
)

User = get_user_model()


def test_stocktake_isolation():
    """Verify stocktake calculations are isolated from cocktails"""
    
    print("\n" + "="*80)
    print("🔒 TESTING COCKTAIL-STOCKTAKE ISOLATION")
    print("="*80 + "\n")
    
    # Setup
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found!")
        return
    
    user = User.objects.filter(is_superuser=True).first()
    staff = Staff.objects.filter(user=user).first()
    
    # Create test period
    period_start = date(2025, 11, 1)
    period_end = date(2025, 11, 10)
    
    period, _ = StockPeriod.objects.get_or_create(
        hotel=hotel,
        period_type=StockPeriod.MONTHLY,
        start_date=period_start,
        end_date=period_end,
        defaults={
            'year': 2025,
            'month': 11,
            'period_name': 'November 2025'
        }
    )
    
    stocktake, _ = Stocktake.objects.get_or_create(
        hotel=hotel,
        period_start=period_start,
        period_end=period_end,
        defaults={'status': Stocktake.DRAFT}
    )
    
    print(f"📊 Stocktake: {stocktake}")
    print(f"📅 Period: {period}\n")
    
    # Test 1: Initial stocktake totals (should be based on Sale records only)
    print("="*80)
    print("TEST 1: Initial Stocktake Totals")
    print("="*80)
    
    initial_revenue = stocktake.total_revenue
    initial_cogs = stocktake.total_cogs
    
    print(f"Initial Revenue: €{initial_revenue}")
    print(f"Initial COGS: €{initial_cogs}")
    print(f"Sale count: {stocktake.sales.count()}")
    print("✅ Baseline established\n")
    
    # Test 2: Add cocktail consumption
    print("="*80)
    print("TEST 2: Add Cocktail Consumption")
    print("="*80)
    
    cocktail = CocktailRecipe.objects.filter(hotel=hotel).first()
    if not cocktail:
        print("⚠️ No cocktails found, creating one...")
        ingredient, _ = Ingredient.objects.get_or_create(
            hotel=hotel,
            name="Test Vodka",
            defaults={'unit': 'ml'}
        )
        cocktail, _ = CocktailRecipe.objects.get_or_create(
            hotel=hotel,
            name="Test Martini",
            defaults={'price': Decimal('14.00')}
        )
        RecipeIngredient.objects.get_or_create(
            cocktail=cocktail,
            ingredient=ingredient,
            defaults={'quantity_per_cocktail': 50.0}
        )
    
    # Create cocktail consumption
    consumption = CocktailConsumption.objects.create(
        cocktail=cocktail,
        quantity_made=10,
        hotel=hotel,
        timestamp=period_start
    )
    
    print(f"Created: {consumption}")
    print(f"Cocktail Revenue: €{consumption.total_revenue}")
    print(f"Cocktail Cost: €{consumption.total_cost}\n")
    
    # Test 3: Verify stocktake totals DID NOT CHANGE
    print("="*80)
    print("TEST 3: Verify Stocktake Totals After Cocktail Addition")
    print("="*80)
    
    # Refresh stocktake to get latest data
    stocktake.refresh_from_db()
    
    after_revenue = stocktake.total_revenue
    after_cogs = stocktake.total_cogs
    
    print(f"Revenue BEFORE cocktail: €{initial_revenue}")
    print(f"Revenue AFTER cocktail:  €{after_revenue}")
    print(f"COGS BEFORE cocktail: €{initial_cogs}")
    print(f"COGS AFTER cocktail:  €{after_cogs}\n")
    
    if after_revenue == initial_revenue and after_cogs == initial_cogs:
        print("✅ PASS: Stocktake totals unchanged by cocktail addition")
    else:
        print("❌ FAIL: Stocktake totals changed! Cocktails affecting stocktake!")
        return False
    
    # Test 4: Verify StockPeriod can see both separately
    print("\n" + "="*80)
    print("TEST 4: Verify StockPeriod Analysis Properties")
    print("="*80)
    
    stock_only_revenue = sum(
        st.total_revenue for st in period.stocktakes.all()
    )
    cocktail_revenue = period.cocktail_revenue
    combined_revenue = period.total_sales_with_cocktails
    
    print(f"Stock-only revenue: €{stock_only_revenue}")
    print(f"Cocktail revenue: €{cocktail_revenue}")
    print(f"Combined revenue: €{combined_revenue}")
    print(f"Expected combined: €{stock_only_revenue + cocktail_revenue}\n")
    
    if combined_revenue == stock_only_revenue + cocktail_revenue:
        print("✅ PASS: StockPeriod correctly combines separate sources")
    else:
        print("❌ FAIL: Combined calculation incorrect")
        return False
    
    # Test 5: Verify Sale model doesn't link to cocktails
    print("\n" + "="*80)
    print("TEST 5: Verify Sale Model Structure")
    print("="*80)
    
    # Check if Sale has cocktail-related fields
    sale_fields = [f.name for f in Sale._meta.get_fields()]
    has_cocktail_link = any('cocktail' in field.lower() for field in sale_fields)
    
    print(f"Sale model fields: {', '.join(sale_fields)}")
    print(f"Has cocktail link: {has_cocktail_link}\n")
    
    if not has_cocktail_link:
        print("✅ PASS: Sale model has no cocktail links")
    else:
        print("❌ FAIL: Sale model has cocktail-related fields!")
        return False
    
    # Test 6: Verify CocktailConsumption doesn't link to stocktake
    print("\n" + "="*80)
    print("TEST 6: Verify CocktailConsumption Model Structure")
    print("="*80)
    
    consumption_fields = [f.name for f in CocktailConsumption._meta.get_fields()]
    has_stocktake_link = 'stocktake' in consumption_fields
    
    print(f"CocktailConsumption fields: {', '.join(consumption_fields)}")
    print(f"Has stocktake link: {has_stocktake_link}\n")
    
    if not has_stocktake_link:
        print("✅ PASS: CocktailConsumption has no stocktake link")
    else:
        print("❌ FAIL: CocktailConsumption has stocktake link!")
        return False
    
    # Test 7: Verify changing cocktail doesn't affect stocktake
    print("\n" + "="*80)
    print("TEST 7: Verify Changing Cocktail Data Doesn't Affect Stocktake")
    print("="*80)
    
    # Update cocktail consumption
    consumption.quantity_made = 50
    consumption.save()
    
    print(f"Updated cocktail quantity: {consumption.quantity_made}")
    print(f"New cocktail revenue: €{consumption.total_revenue}\n")
    
    # Check stocktake again
    stocktake.refresh_from_db()
    final_revenue = stocktake.total_revenue
    final_cogs = stocktake.total_cogs
    
    print(f"Stocktake revenue after cocktail update: €{final_revenue}")
    print(f"Stocktake COGS after cocktail update: €{final_cogs}\n")
    
    if final_revenue == initial_revenue and final_cogs == initial_cogs:
        print("✅ PASS: Stocktake still unchanged after cocktail modification")
    else:
        print("❌ FAIL: Cocktail changes affecting stocktake!")
        return False
    
    # Final Summary
    print("\n" + "="*80)
    print("🎉 ISOLATION TEST SUMMARY")
    print("="*80)
    print("✅ Stocktake.total_revenue excludes cocktails")
    print("✅ Stocktake.total_cogs excludes cocktails")
    print("✅ Sale model has no cocktail links")
    print("✅ CocktailConsumption has no stocktake link")
    print("✅ StockPeriod combines data at analysis layer only")
    print("✅ Changing cocktails doesn't affect stocktake")
    print("\n🔒 CONCLUSION: Cocktails are completely isolated from stocktake calculations!")
    print("="*80 + "\n")
    
    # Cleanup
    consumption.delete()
    
    return True


if __name__ == '__main__':
    success = test_stocktake_isolation()
    exit(0 if success else 1)
