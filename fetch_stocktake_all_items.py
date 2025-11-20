"""
Fetch all items from a stocktake and log them with complete details
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockCategory
from decimal import Decimal

def fetch_stocktake_items(stocktake_id=None):
    """Fetch and log all items from a stocktake"""
    
    # Get the stocktake
    if stocktake_id:
        try:
            stocktake = Stocktake.objects.get(id=stocktake_id)
        except Stocktake.DoesNotExist:
            print(f"❌ Stocktake with ID {stocktake_id} not found!")
            return
    else:
        # Get the most recent stocktake
        stocktake = Stocktake.objects.order_by('-period_start').first()
        if not stocktake:
            print("❌ No stocktakes found in the system!")
            return
    
    print("=" * 120)
    print("STOCKTAKE DETAILS")
    print("=" * 120)
    print(f"ID: {stocktake.id}")
    print(f"Hotel: {stocktake.hotel.name}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"Status: {stocktake.status}")
    print(f"Total Lines: {stocktake.lines.count()}")
    if stocktake.approved_at:
        print(f"Approved: {stocktake.approved_at}")
        if stocktake.approved_by:
            print(f"Approved By: {stocktake.approved_by.username}")
    print()
    
    # Get all lines with related item data
    lines = StocktakeLine.objects.filter(
        stocktake=stocktake
    ).select_related('item', 'item__category').order_by(
        'item__category__code', 'item__subcategory', 'item__name'
    )
    
    if not lines.exists():
        print("⚠️ No stocktake lines found!")
        return
    
    # Process by category
    categories = StockCategory.objects.all().order_by('code')
    
    for category in categories:
        cat_lines = lines.filter(item__category=category)
        
        if not cat_lines.exists():
            continue
        
        print("=" * 120)
        print(f"CATEGORY: {category.code} - {category.name}")
        print("=" * 120)
        print(f"Items: {cat_lines.count()}")
        print()
        
        # Header
        print(f"{'SKU':<15} {'Name':<40} {'Subcategory':<20} {'UOM':<10} {'Opening':<12} {'Counted':<12} {'Variance':<12} {'Value €':<12}")
        print("-" * 120)
        
        # Track totals
        total_opening = Decimal('0')
        total_counted = Decimal('0')
        total_variance = Decimal('0')
        total_value = Decimal('0')
        
        # Process lines in this category
        current_subcategory = None
        for line in cat_lines:
            # Print subcategory header when it changes
            if current_subcategory != line.item.subcategory:
                if current_subcategory is not None:
                    print()
                current_subcategory = line.item.subcategory
                subcat_display = current_subcategory or "NO SUBCATEGORY"
                print(f"\n>>> {subcat_display}")
                print("-" * 120)
            
            # Calculate counted quantity
            counted_qty = line.counted_qty if line.counted_qty else Decimal('0')
            
            # Calculate variance
            variance_qty = line.variance_qty if line.variance_qty else Decimal('0')
            
            # Calculate value
            value = line.counted_value if line.counted_value else Decimal('0')
            
            # Accumulate totals
            total_opening += line.opening_qty
            total_counted += counted_qty
            total_variance += variance_qty
            total_value += value
            
            # Display line
            print(f"{line.item.sku:<15} "
                  f"{line.item.name[:38]:<40} "
                  f"{(line.item.subcategory or 'N/A')[:18]:<20} "
                  f"{str(line.item.uom):<10} "
                  f"{float(line.opening_qty):>10.2f}  "
                  f"{float(counted_qty):>10.2f}  "
                  f"{float(variance_qty):>10.2f}  "
                  f"{float(value):>10.2f}")
        
        # Category totals
        print("=" * 120)
        print(f"{'CATEGORY TOTALS:':<75} "
              f"{float(total_opening):>10.2f}  "
              f"{float(total_counted):>10.2f}  "
              f"{float(total_variance):>10.2f}  "
              f"{float(total_value):>10.2f}")
        print("=" * 120)
        print()
    
    # Overall summary
    print("\n" + "=" * 120)
    print("OVERALL SUMMARY")
    print("=" * 120)
    
    # Calculate grand totals
    all_lines = lines
    grand_total_opening = sum(line.opening_qty for line in all_lines)
    grand_total_counted = sum(line.counted_qty or Decimal('0') for line in all_lines)
    grand_total_variance = sum(line.variance_qty or Decimal('0') for line in all_lines)
    grand_total_value = sum(line.counted_value or Decimal('0') for line in all_lines)
    
    print(f"Total Items: {all_lines.count()}")
    print(f"Total Opening Value: €{float(grand_total_opening):,.2f}")
    print(f"Total Counted Value: €{float(grand_total_value):,.2f}")
    print(f"Total Variance: €{float(grand_total_variance):,.2f}")
    
    # Category breakdown
    print("\nBreakdown by Category:")
    print("-" * 120)
    for category in categories:
        cat_lines = lines.filter(item__category=category)
        if cat_lines.exists():
            cat_value = sum(line.counted_value or Decimal('0') for line in cat_lines)
            cat_variance = sum(line.variance_value or Decimal('0') for line in cat_lines)
            print(f"{category.code} - {category.name:30s}: {cat_lines.count():3d} items | "
                  f"Value: €{float(cat_value):>10,.2f} | Variance: €{float(cat_variance):>10,.2f}")
    
    print("=" * 120)


if __name__ == '__main__':
    import sys
    
    # Check if stocktake ID provided as argument
    if len(sys.argv) > 1:
        try:
            stocktake_id = int(sys.argv[1])
            fetch_stocktake_items(stocktake_id)
        except ValueError:
            print("❌ Invalid stocktake ID. Please provide a number.")
    else:
        # Fetch most recent stocktake
        print("No stocktake ID provided. Fetching most recent stocktake...")
        print()
        fetch_stocktake_items()
