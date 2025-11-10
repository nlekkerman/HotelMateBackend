"""
Test script for combined sales (stock + cocktails) calculations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, CocktailConsumption
from hotel.models import Hotel
from datetime import datetime


def test_combined_sales():
    """Test that period sales include both stock and cocktails"""
    
    print("=" * 60)
    print("TESTING COMBINED SALES (STOCK + COCKTAILS)")
    print("=" * 60)
    
    # Get hotel
    hotel = Hotel.objects.get(id=2)
    print(f"\nUsing Hotel: {hotel.name}")
    
    # Get latest period
    period = StockPeriod.objects.filter(hotel=hotel).first()
    
    if not period:
        print("\n❌ No stock periods found for this hotel")
        return
    
    print(f"\nTesting Period: {period.period_name}")
    print(f"Date Range: {period.start_date} to {period.end_date}")
    
    # Get cocktail consumptions for this period
    cocktail_sales = period.get_cocktail_sales()
    
    print(f"\n{'='*60}")
    print("COCKTAIL SALES IN PERIOD")
    print(f"{'='*60}")
    
    print(f"\nTotal Cocktail Consumptions: {cocktail_sales.count()}")
    print(f"Total Cocktails Made: {period.cocktail_quantity}")
    print(f"Cocktail Revenue: €{period.cocktail_revenue}")
    print(f"Cocktail Cost: €{period.cocktail_cost}")
    print(f"Cocktail Profit: €{period.cocktail_revenue - period.cocktail_cost}")
    
    # Show breakdown by cocktail
    if cocktail_sales.exists():
        print(f"\nBreakdown by Cocktail:")
        from django.db.models import Sum
        breakdown = cocktail_sales.values(
            'cocktail__name'
        ).annotate(
            quantity=Sum('quantity_made'),
            revenue=Sum('total_revenue')
        ).order_by('-revenue')
        
        for item in breakdown:
            print(f"  - {item['cocktail__name']}: "
                  f"{item['quantity']} made, €{item['revenue']} revenue")
    
    # Get stock sales
    print(f"\n{'='*60}")
    print("STOCK SALES IN PERIOD")
    print(f"{'='*60}")
    
    stock_revenue = 0
    stock_cost = 0
    
    stocktakes = period.stocktakes.all()
    print(f"\nStocktakes in period: {stocktakes.count()}")
    
    for stocktake in stocktakes:
        if stocktake.total_revenue:
            stock_revenue += stocktake.total_revenue
        if stocktake.total_cogs:
            stock_cost += stocktake.total_cogs
    
    print(f"Stock Revenue: €{stock_revenue}")
    print(f"Stock Cost: €{stock_cost}")
    print(f"Stock Profit: €{stock_revenue - stock_cost}")
    
    # Combined totals
    print(f"\n{'='*60}")
    print("COMBINED TOTALS (STOCK + COCKTAILS)")
    print(f"{'='*60}")
    
    combined_revenue = period.total_sales_with_cocktails
    combined_cost = period.total_cost_with_cocktails
    combined_profit = period.profit_with_cocktails
    
    print(f"\nTotal Revenue: €{combined_revenue}")
    print(f"  - Stock Revenue: €{stock_revenue}")
    print(f"  - Cocktail Revenue: €{period.cocktail_revenue}")
    
    print(f"\nTotal Cost: €{combined_cost}")
    print(f"  - Stock Cost: €{stock_cost}")
    print(f"  - Cocktail Cost: €{period.cocktail_cost}")
    
    print(f"\nTotal Profit: €{combined_profit}")
    
    # Calculate percentages
    if combined_revenue > 0:
        cocktail_percent = (period.cocktail_revenue / combined_revenue) * 100
        print(f"\nCocktail Revenue %: {cocktail_percent:.1f}%")
        print(f"Stock Revenue %: {100 - cocktail_percent:.1f}%")
    
    print(f"\n{'='*60}")
    print("✅ Combined Sales Test Complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    test_combined_sales()
