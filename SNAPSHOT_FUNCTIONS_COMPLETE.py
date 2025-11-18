"""
SNAPSHOT CREATION - COMPLETE FUNCTION REFERENCE
================================================

This shows how snapshots are created when approving stocktakes and closing periods.
"""

print("="*80)
print("FUNCTION 1: approve_stocktake() - SERVICE LAYER")
print("Location: stock_tracker/stocktake_service.py")
print("="*80)
print("""
def approve_stocktake(stocktake, approved_by):
    '''
    Approve stocktake and create ADJUSTMENT movements for variances.
    Also updates StockSnapshot closing values so next period has
    correct opening stock.
    
    Args:
        stocktake: Stocktake instance
        approved_by: Staff approving the stocktake
        
    Returns:
        int: Number of adjustment movements created
    '''
    if stocktake.status != Stocktake.DRAFT:
        raise ValueError("Can only approve draft stocktakes")
    
    adjustments_created = 0
    snapshots_updated = 0
    
    # STEP 1: Get the corresponding StockPeriod
    try:
        period = StockPeriod.objects.get(
            hotel=stocktake.hotel,
            start_date=stocktake.period_start,
            end_date=stocktake.period_end
        )
    except StockPeriod.DoesNotExist:
        period = None
    
    # STEP 2: Loop through ALL stocktake lines (all categories)
    for line in stocktake.lines.all():
        variance = line.variance_qty
        
        # Create adjustment movement if variance exists
        if variance != Decimal('0'):
            StockMovement.objects.create(
                hotel=stocktake.hotel,
                item=line.item,
                movement_type=StockMovement.ADJUSTMENT,
                quantity=variance,
                unit_cost=line.valuation_cost,
                reference=f"Stocktake-{stocktake.id}",
                notes=(
                    f"Stocktake adjustment: counted {line.counted_qty}, "
                    f"expected {line.expected_qty}"
                ),
                staff=approved_by,
            )
            adjustments_created += 1
        
        # STEP 3: Update/Create snapshot with counted stock
        # ⚠️ CRITICAL: This only happens if period exists!
        if period:
            try:
                # Try to get existing snapshot
                snapshot = StockSnapshot.objects.get(
                    period=period,
                    item=line.item
                )
                
                # Update closing stock with counted values
                snapshot.closing_full_units = line.counted_full_units
                snapshot.closing_partial_units = line.counted_partial_units
                snapshot.closing_stock_value = line.counted_value
                snapshot.save()
                snapshots_updated += 1
                
            except StockSnapshot.DoesNotExist:
                # Create new snapshot if it doesn't exist
                StockSnapshot.objects.create(
                    hotel=stocktake.hotel,
                    item=line.item,
                    period=period,
                    closing_full_units=line.counted_full_units,
                    closing_partial_units=line.counted_partial_units,
                    unit_cost=line.valuation_cost,
                    cost_per_serving=line.item.cost_per_serving,
                    closing_stock_value=line.counted_value,
                    menu_price=line.item.menu_price or Decimal('0.00')
                )
                snapshots_updated += 1
    
    # STEP 4: Mark stocktake as approved
    stocktake.status = Stocktake.APPROVED
    stocktake.approved_at = timezone.now()
    stocktake.approved_by = approved_by
    stocktake.save()
    
    return adjustments_created
""")

print("\n" + "="*80)
print("FUNCTION 2: approve_and_close() - VIEW ENDPOINT")
print("Location: stock_tracker/views.py")
print("Endpoint: POST /periods/{id}/approve-and-close/")
print("="*80)
print("""
@action(detail=True, methods=['post'])
def approve_and_close(self, request, pk=None, hotel_identifier=None):
    '''
    Combined action: Approve stocktake AND close period in one operation.
    
    Order of operations:
    1. First: Approve the stocktake (DRAFT → APPROVED) + CREATE SNAPSHOTS
    2. Then: Close the period (OPEN → CLOSED)
    '''
    period = self.get_object()
    
    # Check if period is already closed
    if period.is_closed:
        return Response({
            'error': 'Period is already closed'
        }, status=400)
    
    # Get staff member
    staff = request.user.staff_profile
    
    # Find the stocktake for this period
    stocktake = Stocktake.objects.get(
        hotel=period.hotel,
        period_start=period.start_date,
        period_end=period.end_date
    )
    
    # STEP 1: Approve the stocktake
    # ✅ NOW FIXED: Calls approve_stocktake() service function
    adjustments_created = 0
    if stocktake.status != Stocktake.APPROVED:
        from .stocktake_service import approve_stocktake
        adjustments_created = approve_stocktake(stocktake, staff)
    
    # STEP 2: Close the period
    period.is_closed = True
    period.closed_at = timezone.now()
    period.closed_by = staff
    period.save()
    
    return Response({
        'success': True,
        'message': 'Stocktake approved and period closed successfully',
        'adjustments_created': adjustments_created
    })
""")

print("\n" + "="*80)
print("KEY POINTS")
print("="*80)
print("""
1. SNAPSHOTS ARE CREATED IN approve_stocktake() SERVICE FUNCTION
   - For EVERY stocktake line (all 250+ items)
   - For ALL categories (D, B, S, W, M)
   - Saves closing_full_units, closing_partial_units, closing_stock_value

2. TWO WAYS TO APPROVE:
   a) POST /stocktakes/{id}/approve/ 
      → Calls approve_stocktake() ✅
      → Creates snapshots ✅
      
   b) POST /periods/{id}/approve-and-close/
      → NOW FIXED: Calls approve_stocktake() ✅
      → Creates snapshots ✅
      → Then closes period ✅

3. SNAPSHOTS REQUIRE:
   - Period MUST exist with matching dates
   - Stocktake MUST have lines with counted stock
   - If period doesn't exist: NO SNAPSHOTS CREATED! ⚠️

4. CLOSING PERIOD:
   - Separate action from approving stocktake
   - Just marks period as closed (is_closed = True)
   - Does NOT create snapshots
   - Snapshots should already exist from approval

5. FRONTEND NEEDS TO:
   ✅ Submit counted stock (counted_full_units + counted_partial_units)
   ✅ Call approve endpoint (either one works now)
   ❌ DO NOT manually create snapshots
   ❌ DO NOT manually calculate opening stock
""")

print("\n" + "="*80)
print("WHY FEBRUARY HAD NO SNAPSHOTS")
print("="*80)
print("""
Problem: approve_and_close() endpoint was NOT calling approve_stocktake()
         It only changed stocktake.status without creating snapshots!

Timeline:
- Feb stocktake created with 250 lines
- approve_and_close() called on 2025-11-18
- Stocktake status changed to APPROVED ✅
- Period closed ✅
- BUT: approve_stocktake() service NOT called ❌
- Result: NO snapshots created ❌

Solution: FIXED! approve_and_close() now calls approve_stocktake() service
""")
