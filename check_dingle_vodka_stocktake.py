"""
Script to check Dingle Vodka stocktake data and show calculations.
Run: python check_dingle_vodka_stocktake.py
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockItem, 
    Stocktake, 
    StocktakeLine, 
    StockMovement
)
from hotel.models import Hotel

def format_ml(ml_value):
    """Convert ml to bottles for readability"""
    if not ml_value:
        return "0 ml (0 bottles)"
    bottles = float(ml_value) / 700  # Assuming 700ml bottles
    return f"{ml_value} ml ({bottles:.2f} bottles)"

def check_dingle_vodka():
    print("=" * 80)
    print("DINGLE VODKA STOCKTAKE CHECKER")
    print("=" * 80)
    
    # Try to find Dingle Vodka in database
    print("\n[1] SEARCHING FOR DINGLE VODKA IN DATABASE...")
    dingle_items = StockItem.objects.filter(
        name__icontains='dingle'
    ).select_related('hotel', 'category')
    
    if not dingle_items.exists():
        print("❌ No Dingle Vodka found in database")
        print("\n💡 To add Dingle Vodka, create a StockItem:")
        print("""
        StockItem.objects.create(
            hotel=your_hotel,
            sku="VOD-DINGLE-001",
            name="Dingle Vodka",
            size="70cl",
            size_value=700,
            size_unit="ml",
            uom=12,  # 12 bottles per case
            base_unit="ml",
            unit_cost=150.00,  # Cost per case
            category=spirits_category
        )
        """)
        return
    
    dingle = dingle_items.first()
    print(f"✅ Found: {dingle.name} (SKU: {dingle.sku})")
    print(f"   Hotel: {dingle.hotel.name}")
    print(f"   Category: {dingle.category.name if dingle.category else 'None'}")
    print(f"   Size: {dingle.size}")
    print(f"   UOM: {dingle.uom} bottles per case")
    print(f"   Unit Cost: £{dingle.unit_cost} per case")
    print(f"   Cost per bottle: £{dingle.unit_cost / dingle.uom:.2f}")
    print(f"   Current Stock: {format_ml(dingle.current_qty)}")
    
    # Check for stock movements
    print(f"\n[2] CHECKING STOCK MOVEMENTS FOR {dingle.name}...")
    movements = StockMovement.objects.filter(
        item=dingle
    ).order_by('timestamp')
    
    if not movements.exists():
        print("❌ No stock movements recorded")
        print("\n💡 To add movements, create StockMovement records:")
        print("""
        # Purchase (delivery)
        StockMovement.objects.create(
            hotel=hotel,
            item=dingle_vodka,
            movement_type='PURCHASE',
            quantity=8400,  # 1 case = 12 × 700ml
            reference='INV-001',
            timestamp='2025-10-01'
        )
        
        # Sale (consumption)
        StockMovement.objects.create(
            hotel=hotel,
            item=dingle_vodka,
            movement_type='SALE',
            quantity=2800,  # 4 bottles × 700ml
            timestamp='2025-10-15'
        )
        """)
    else:
        print(f"✅ Found {movements.count()} movements:")
        
        totals = {
            'PURCHASE': Decimal('0'),
            'SALE': Decimal('0'),
            'WASTE': Decimal('0'),
            'TRANSFER_IN': Decimal('0'),
            'TRANSFER_OUT': Decimal('0'),
            'ADJUSTMENT': Decimal('0')
        }
        
        for mv in movements:
            print(f"   {mv.timestamp.strftime('%Y-%m-%d %H:%M')} | "
                  f"{mv.movement_type:15s} | {format_ml(mv.quantity):30s} | "
                  f"{mv.reference or 'N/A'}")
            totals[mv.movement_type] += mv.quantity
        
        print("\n   MOVEMENT TOTALS:")
        print(f"   + Purchases:     {format_ml(totals['PURCHASE'])}")
        print(f"   + Transfers In:  {format_ml(totals['TRANSFER_IN'])}")
        print(f"   - Sales:         {format_ml(totals['SALE'])}")
        print(f"   - Waste:         {format_ml(totals['WASTE'])}")
        print(f"   - Transfers Out: {format_ml(totals['TRANSFER_OUT'])}")
        print(f"   +/- Adjustments: {format_ml(totals['ADJUSTMENT'])}")
    
    # Check for stocktakes
    print(f"\n[3] CHECKING STOCKTAKES FOR {dingle.hotel.name}...")
    stocktakes = Stocktake.objects.filter(
        hotel=dingle.hotel
    ).order_by('-period_end')
    
    if not stocktakes.exists():
        print("❌ No stocktakes found")
        print("\n💡 To create a stocktake:")
        print("""
        stocktake = Stocktake.objects.create(
            hotel=hotel,
            period_start='2025-10-01',
            period_end='2025-10-31',
            status='DRAFT'
        )
        
        # Then populate it:
        # POST /api/<hotel>/stocktakes/<id>/populate/
        """)
        return
    
    print(f"✅ Found {stocktakes.count()} stocktake(s):")
    for st in stocktakes:
        print(f"   ID: {st.id} | {st.period_start} to {st.period_end} | "
              f"Status: {st.status}")
    
    # Check stocktake lines for Dingle
    print(f"\n[4] CHECKING STOCKTAKE LINES FOR {dingle.name}...")
    lines = StocktakeLine.objects.filter(
        item=dingle
    ).select_related('stocktake').order_by('-stocktake__period_end')
    
    if not lines.exists():
        print("❌ No stocktake lines found for Dingle Vodka")
        print("\n💡 Lines are auto-created when you populate a stocktake")
        if stocktakes.exists():
            latest = stocktakes.first()
            print(f"\n   Try populating stocktake #{latest.id}:")
            print(f"   POST /api/{dingle.hotel.slug or dingle.hotel.subdomain}"
                  f"/stocktakes/{latest.id}/populate/")
        return
    
    print(f"✅ Found {lines.count()} stocktake line(s):")
    
    for line in lines:
        print("\n" + "─" * 80)
        print(f"STOCKTAKE: {line.stocktake.period_start} to "
              f"{line.stocktake.period_end} (Status: {line.stocktake.status})")
        print("─" * 80)
        
        print(f"\n📦 OPENING BALANCE:")
        print(f"   {format_ml(line.opening_qty)}")
        
        print(f"\n📊 PERIOD MOVEMENTS ({line.stocktake.period_start} to "
              f"{line.stocktake.period_end}):")
        print(f"   + Purchases:     {format_ml(line.purchases)}")
        print(f"   + Transfers In:  {format_ml(line.transfers_in)}")
        print(f"   - Sales:         {format_ml(line.sales)}")
        print(f"   - Waste:         {format_ml(line.waste)}")
        print(f"   - Transfers Out: {format_ml(line.transfers_out)}")
        print(f"   + Prior Adjustments: {format_ml(line.adjustments)}")
        
        print(f"\n🧮 CALCULATION:")
        print(f"   Expected = Opening + Purchases + Transfers_In - Sales "
              f"- Waste - Transfers_Out + Adjustments")
        print(f"   Expected = {line.opening_qty} + {line.purchases} + "
              f"{line.transfers_in} - {line.sales} - {line.waste} - "
              f"{line.transfers_out} + {line.adjustments}")
        print(f"   Expected = {line.expected_qty} ml")
        print(f"   Expected = {format_ml(line.expected_qty)}")
        
        print(f"\n👤 STAFF COUNT:")
        print(f"   Full Units (cases): {line.counted_full_units}")
        print(f"   Partial Units (bottles): {line.counted_partial_units}")
        full_ml = line.counted_full_units * dingle.uom * 700
        partial_ml = line.counted_partial_units * 700
        print(f"   = ({line.counted_full_units} cases × {dingle.uom} bottles × 700ml) "
              f"+ ({line.counted_partial_units} bottles × 700ml)")
        print(f"   = {full_ml} ml + {partial_ml} ml")
        print(f"   Counted Total = {format_ml(line.counted_qty)}")
        
        print(f"\n📉 VARIANCE:")
        print(f"   Variance = Counted - Expected")
        print(f"   Variance = {line.counted_qty} - {line.expected_qty}")
        print(f"   Variance = {line.variance_qty} ml")
        
        if line.variance_qty > 0:
            print(f"   ✅ SURPLUS: Found {format_ml(line.variance_qty)} more than expected")
        elif line.variance_qty < 0:
            print(f"   ⚠️ SHORTAGE: Missing {format_ml(abs(line.variance_qty))}")
        else:
            print(f"   ✅ PERFECT MATCH: No variance")
        
        print(f"\n💰 MONETARY VALUE:")
        print(f"   Valuation Cost: £{line.valuation_cost:.4f} per ml")
        print(f"   Expected Value: £{line.expected_value:.2f}")
        print(f"   Counted Value:  £{line.counted_value:.2f}")
        print(f"   Variance Value: £{line.variance_value:.2f}")
        
        if line.stocktake.is_locked:
            print(f"\n🔒 Stocktake is APPROVED and locked (cannot edit)")
        else:
            print(f"\n🔓 Stocktake is DRAFT (can still update counts)")
            print(f"\n💡 To update count:")
            print(f"   PATCH /api/{dingle.hotel.slug or dingle.hotel.subdomain}"
                  f"/stocktake-lines/{line.id}/")
            print(f"   {{")
            print(f"     \"counted_full_units\": 2.0,  // 2 cases")
            print(f"     \"counted_partial_units\": 5.0  // 5 loose bottles")
            print(f"   }}")

if __name__ == "__main__":
    try:
        check_dingle_vodka()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
