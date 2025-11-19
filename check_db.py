from stock_tracker.models import StocktakeLine

# Get the syrup line
line = StocktakeLine.objects.filter(
    stocktake__id=45,
    item__sku='M0006'
).first()

if line:
    print(f"\nDATABASE VALUES for {line.item.name} (SKU: {line.item.sku})")
    print("=" * 80)
    print(f"counted_full_units (DB):    {line.counted_full_units}")
    print(f"counted_partial_units (DB): {line.counted_partial_units}")
    print("")
    print(f"counted_qty (calculated):   {line.counted_qty}")
    print(f"expected_qty (calculated):  {line.expected_qty}")
    print(f"variance_qty (calculated):  {line.variance_qty}")
    print("")
    print(f"Item UOM: {line.item.uom}")
    print(f"Item Subcategory: {line.item.subcategory}")
    
    # Check if this is being calculated correctly
    manual_calc = line.counted_full_units + line.counted_partial_units
    print("")
    print(f"Manual calculation (full + partial): {manual_calc}")
else:
    print("Line not found!")
