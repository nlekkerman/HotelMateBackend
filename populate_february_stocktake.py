"""
Populate February 2025 stocktake with counted stock for ALL categories.
Opening values will be automatically populated from January closing stock.

Counted values by category:
- Draught: 1 keg + 20 pints
- Bottled: 1 case + 10 bottles
- Spirits: 3 bottles + 0.50 fractional
- Wine: 2 bottles + 0.75 fractional
- Minerals Soft Drinks: 2 cases + 8 bottles
- Minerals Syrups: 4.5 bottles (individual/decimal)
- Minerals Juices: 3 cases + 5 bottles
- Minerals Cordials: 1 case + 6 bottles
- Minerals BIB: 2 boxes + 10 liters
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockPeriod, StockSnapshot, StockItem, StockCategory,
    Stocktake, StocktakeLine
)


def get_opening_qty(item, january_period):
    """Get opening quantity from January closing snapshot"""
    if not january_period:
        return Decimal('0')
    
    jan_snapshot = StockSnapshot.objects.filter(
        item=item,
        period=january_period
    ).first()
    
    return jan_snapshot.total_servings if jan_snapshot else Decimal('0')


def main():
    print("=" * 80)
    print("POPULATE FEBRUARY 2025 STOCKTAKE - ALL CATEGORIES")
    print("=" * 80)
    
    # Find periods
    february = StockPeriod.objects.filter(
        start_date__year=2025,
        start_date__month=2
    ).first()
    
    january = StockPeriod.objects.filter(
        start_date__year=2025,
        start_date__month=1
    ).first()
    
    if not february:
        print("❌ February 2025 period not found!")
        return
    
    print(f"\n✅ Found February 2025 period")
    print(f"   Period ID: {february.id}")
    print(f"   Dates: {february.start_date} to {february.end_date}")
    
    if january:
        print(f"✅ Found January 2025 period (for opening values)")
    
    # Get or create stocktake
    stocktake, created = Stocktake.objects.get_or_create(
        hotel_id=2,
        period_start=february.start_date,
        period_end=february.end_date,
        defaults={'status': 'DRAFT'}
    )
    
    if created:
        print(f"\n✅ Created new stocktake (ID: {stocktake.id})")
    else:
        print(f"\n✅ Found existing stocktake (ID: {stocktake.id})")
        # Clear existing lines
        deleted = StocktakeLine.objects.filter(stocktake=stocktake).delete()
        print(f"   Cleared {deleted[0]} existing lines")
    
    total_lines = 0
    
    # DRAUGHT BEERS
    print("\n" + "=" * 80)
    print("DRAUGHT BEERS - 1 KEG + 20 PINTS")
    print("=" * 80)
    
    draught_beers = StockItem.objects.filter(
        hotel_id=2,
        category_id='D',
        active=True
    )
    
    draught_count = 0
    for item in draught_beers:
        StocktakeLine.objects.create(
            stocktake=stocktake,
            item=item,
            opening_qty=get_opening_qty(item, january),
            counted_full_units=Decimal('1'),
            counted_partial_units=Decimal('20'),
            valuation_cost=item.cost_per_serving or Decimal('0')
        )
        draught_count += 1
        print(f"   ✅ {item.name}: 1 keg + 20 pints")
    
    total_lines += draught_count
    
    # BOTTLED BEERS
    print("\n" + "=" * 80)
    print("BOTTLED BEERS - 1 CASE + 10 BOTTLES")
    print("=" * 80)
    
    bottled_beers = StockItem.objects.filter(
        hotel_id=2,
        category_id='B',
        active=True
    )
    
    bottled_count = 0
    for item in bottled_beers:
        StocktakeLine.objects.create(
            stocktake=stocktake,
            item=item,
            opening_qty=get_opening_qty(item, january),
            counted_full_units=Decimal('1'),
            counted_partial_units=Decimal('10'),
            valuation_cost=item.cost_per_serving or Decimal('0')
        )
        bottled_count += 1
        print(f"   ✅ {item.name}: 1 case + 10 bottles")
    
    total_lines += bottled_count
    
    # SPIRITS
    print("\n" + "=" * 80)
    print("SPIRITS - 3 BOTTLES + 0.50 FRACTIONAL")
    print("=" * 80)
    
    spirits = StockItem.objects.filter(
        hotel_id=2,
        category_id='S',
        active=True
    )
    
    spirits_count = 0
    for item in spirits:
        StocktakeLine.objects.create(
            stocktake=stocktake,
            item=item,
            opening_qty=get_opening_qty(item, january),
            counted_full_units=Decimal('3'),
            counted_partial_units=Decimal('0.50'),
            valuation_cost=item.cost_per_serving or Decimal('0')
        )
        spirits_count += 1
        print(f"   ✅ {item.name}: 3 bottles + 0.50")
    
    total_lines += spirits_count
    
    # WINE
    print("\n" + "=" * 80)
    print("WINE - 2 BOTTLES + 0.75 FRACTIONAL")
    print("=" * 80)
    
    wines = StockItem.objects.filter(
        hotel_id=2,
        category_id='W',
        active=True
    )
    
    wine_count = 0
    for item in wines:
        StocktakeLine.objects.create(
            stocktake=stocktake,
            item=item,
            opening_qty=get_opening_qty(item, january),
            counted_full_units=Decimal('2'),
            counted_partial_units=Decimal('0.75'),
            valuation_cost=item.cost_per_serving or Decimal('0')
        )
        wine_count += 1
        print(f"   ✅ {item.name}: 2 bottles + 0.75")
    
    total_lines += wine_count
    
    # MINERALS - SOFT_DRINKS
    print("\n" + "=" * 80)
    print("MINERALS: SOFT DRINKS - 2 CASES + 8 BOTTLES")
    print("=" * 80)
    
    soft_drinks = StockItem.objects.filter(
        hotel_id=2,
        category_id='M',
        subcategory='SOFT_DRINKS',
        active=True
    )
    
    soft_count = 0
    for item in soft_drinks:
        StocktakeLine.objects.create(
            stocktake=stocktake,
            item=item,
            opening_qty=get_opening_qty(item, january),
            counted_full_units=Decimal('2'),
            counted_partial_units=Decimal('8'),
            valuation_cost=item.cost_per_serving or Decimal('0')
        )
        soft_count += 1
        print(f"   ✅ {item.name}: 2 cases + 8 bottles")
    
    total_lines += soft_count
    
    # MINERALS - SYRUPS
    print("\n" + "=" * 80)
    print("MINERALS: SYRUPS - 4.5 BOTTLES (INDIVIDUAL)")
    print("=" * 80)
    
    syrups = StockItem.objects.filter(
        hotel_id=2,
        category_id='M',
        subcategory='SYRUPS',
        active=True
    )
    
    syrup_count = 0
    for item in syrups:
        StocktakeLine.objects.create(
            stocktake=stocktake,
            item=item,
            opening_qty=get_opening_qty(item, january),
            counted_full_units=Decimal('4'),
            counted_partial_units=Decimal('0.5'),
            valuation_cost=item.cost_per_serving or Decimal('0')
        )
        syrup_count += 1
        print(f"   ✅ {item.name}: 4.5 bottles")
    
    total_lines += syrup_count
    
    # MINERALS - JUICES
    print("\n" + "=" * 80)
    print("MINERALS: JUICES - 3 CASES + 5 BOTTLES")
    print("=" * 80)
    
    juices = StockItem.objects.filter(
        hotel_id=2,
        category_id='M',
        subcategory='JUICES',
        active=True
    )
    
    juice_count = 0
    for item in juices:
        StocktakeLine.objects.create(
            stocktake=stocktake,
            item=item,
            opening_qty=get_opening_qty(item, january),
            counted_full_units=Decimal('3'),
            counted_partial_units=Decimal('5'),
            valuation_cost=item.cost_per_serving or Decimal('0')
        )
        juice_count += 1
        print(f"   ✅ {item.name}: 3 cases + 5 bottles")
    
    total_lines += juice_count
    
    # MINERALS - CORDIALS
    print("\n" + "=" * 80)
    print("MINERALS: CORDIALS - 1 CASE + 6 BOTTLES")
    print("=" * 80)
    
    cordials = StockItem.objects.filter(
        hotel_id=2,
        category_id='M',
        subcategory='CORDIALS',
        active=True
    )
    
    cordial_count = 0
    for item in cordials:
        StocktakeLine.objects.create(
            stocktake=stocktake,
            item=item,
            opening_qty=get_opening_qty(item, january),
            counted_full_units=Decimal('1'),
            counted_partial_units=Decimal('6'),
            valuation_cost=item.cost_per_serving or Decimal('0')
        )
        cordial_count += 1
        print(f"   ✅ {item.name}: 1 case + 6 bottles")
    
    total_lines += cordial_count
    
    # MINERALS - BIB
    print("\n" + "=" * 80)
    print("MINERALS: BIB - 2 BOXES + 10 LITERS")
    print("=" * 80)
    
    bibs = StockItem.objects.filter(
        hotel_id=2,
        category_id='M',
        subcategory='BIB',
        active=True
    )
    
    bib_count = 0
    for item in bibs:
        StocktakeLine.objects.create(
            stocktake=stocktake,
            item=item,
            opening_qty=get_opening_qty(item, january),
            counted_full_units=Decimal('2'),
            counted_partial_units=Decimal('10'),
            valuation_cost=item.cost_per_serving or Decimal('0')
        )
        bib_count += 1
        print(f"   ✅ {item.name}: 2 boxes + 10 liters")
    
    total_lines += bib_count
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Stocktake ID: {stocktake.id}")
    print(f"✅ Period: {february.start_date} to {february.end_date}")
    print(f"\n📊 Items by category:")
    print(f"   - Draught Beers: {draught_count} items")
    print(f"   - Bottled Beers: {bottled_count} items")
    print(f"   - Spirits: {spirits_count} items")
    print(f"   - Wine: {wine_count} items")
    print(f"   - Minerals Soft Drinks: {soft_count} items")
    print(f"   - Minerals Syrups: {syrup_count} items")
    print(f"   - Minerals Juices: {juice_count} items")
    print(f"   - Minerals Cordials: {cordial_count} items")
    print(f"   - Minerals BIB: {bib_count} items")
    print(f"\n✅ Total lines: {total_lines}")
    print(f"✅ Status: {stocktake.status}")
    
    print("\n✅ COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    main()
