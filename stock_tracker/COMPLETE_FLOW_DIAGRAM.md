# Complete Data Flow: Frontend to Backend and Back

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React/Vue)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  User sees stocktake line:                                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Guinness Keg (D001)                                          │  │
│  │ Opening: 88 | Purchases: 48 | Sales: 120 | Expected: 16    │  │
│  │ Counted: 42 | Variance: +26 ⚠️ (Something's wrong!)        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  User adds movement:                                                 │
│  ┌──────────────────────────────┐                                   │
│  │ Type: [Purchase ▼]           │                                   │
│  │ Qty:  [24        ]           │                                   │
│  │ Ref:  [INV-12345 ]           │                                   │
│  │ [Add Movement]               │                                   │
│  └──────────────────────────────┘                                   │
│                                                                       │
│  JavaScript sends:                                                   │
│  POST /api/stock_tracker/hotel/stocktake-lines/45/add-movement/    │
│  {                                                                   │
│    "movement_type": "PURCHASE",                                     │
│    "quantity": 24,                                                  │
│    "reference": "INV-12345"                                         │
│  }                                                                   │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ HTTP POST
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND (Django REST API)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. StocktakeLineViewSet.add_movement() receives request            │
│     ├─ Validates movement_type                                      │
│     ├─ Validates quantity                                           │
│     └─ Checks stocktake is not locked                               │
│                                                                       │
│  2. Create StockMovement record                                      │
│     ┌───────────────────────────────────────────┐                   │
│     │ StockMovement                              │                   │
│     │ ─────────────                              │                   │
│     │ id: 789                                    │                   │
│     │ hotel_id: 1                                │                   │
│     │ item_id: 23 (Guinness Keg)                │                   │
│     │ period_id: 4                               │                   │
│     │ movement_type: "PURCHASE"                  │                   │
│     │ quantity: 24.0000                          │                   │
│     │ reference: "INV-12345"                     │                   │
│     │ staff_id: 5 (auto-detected)               │                   │
│     │ timestamp: 2025-11-09 15:45:00 (auto)     │                   │
│     └───────────────────────────────────────────┘                   │
│     Saved to database ✓                                             │
│                                                                       │
│  3. Recalculate line totals                                         │
│     ├─ Query all movements for this item in period                  │
│     ├─ Sum by type: purchases, sales, waste, etc.                   │
│     └─ Update StocktakeLine fields                                  │
│                                                                       │
│     Before:  purchases = 48                                         │
│     After:   purchases = 72 (48 + 24)                              │
│                                                                       │
│  4. Calculate expected_qty                                          │
│     Formula: opening + purchases - sales - waste                    │
│              + transfers_in - transfers_out + adjustments           │
│                                                                       │
│     = 88 + 72 - 120 - 0 + 0 - 0 + 0                               │
│     = 40 ✓                                                          │
│                                                                       │
│  5. Calculate variance                                              │
│     variance = counted - expected                                   │
│              = 42 - 40                                              │
│              = +2 ✓ (Much better!)                                 │
│                                                                       │
│  6. Return response                                                 │
│     {                                                                │
│       "message": "Movement created successfully",                   │
│       "movement": {                                                 │
│         "id": 789,                                                  │
│         "movement_type": "PURCHASE",                                │
│         "quantity": "24.0000",                                      │
│         "timestamp": "2025-11-09T15:45:00Z"                        │
│       },                                                             │
│       "line": {                                                     │
│         "id": 45,                                                   │
│         "purchases": "72.0000",     ← Updated!                     │
│         "expected_qty": "40.0000",  ← Recalculated!               │
│         "variance_qty": "2.0000",   ← Fixed!                       │
│         ... (all other fields)                                      │
│       }                                                              │
│     }                                                                │
│                                                                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ HTTP 201 Response
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React/Vue)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  7. Receive response and update UI                                  │
│     ├─ response.json() gets the data                                │
│     ├─ setLineData(response.line)                                   │
│     └─ UI re-renders with new values                                │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Guinness Keg (D001)                                          │  │
│  │ Opening: 88 | Purchases: 72 | Sales: 120 | Expected: 40    │  │
│  │                        ↑ Updated!           ↑ Updated!       │  │
│  │ Counted: 42 | Variance: +2 ✓ (Fixed!)                       │  │
│  │                         ↑ Updated!                            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Success message shown: "Purchase added successfully!"              │
│  Form cleared, ready for next input                                 │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## What Happens in Database

### Before Adding Movement

**StockMovement Table:**
```sql
id | item_id | type     | quantity | timestamp           | reference
---|---------|----------|----------|---------------------|----------
155| 23      | PURCHASE | 48.0000  | 2025-11-01 10:00:00 | INV-111
156| 23      | SALE     | 120.0000 | 2025-11-05 18:30:00 | POS-Daily
```

**StocktakeLine Table:**
```sql
id | stocktake_id | item_id | opening_qty | purchases | sales   | expected_qty | counted_qty | variance_qty
---|--------------|---------|-------------|-----------|---------|--------------|-------------|-------------
45 | 7            | 23      | 88.0000     | 48.0000   | 120.0000| 16.0000      | 42.0000     | 26.0000
```

### After Adding Movement

**StockMovement Table:** (New row added!)
```sql
id | item_id | type     | quantity | timestamp           | reference
---|---------|----------|----------|---------------------|----------
155| 23      | PURCHASE | 48.0000  | 2025-11-01 10:00:00 | INV-111
156| 23      | SALE     | 120.0000 | 2025-11-05 18:30:00 | POS-Daily
789| 23      | PURCHASE | 24.0000  | 2025-11-09 15:45:00 | INV-12345  ← NEW!
```

**StocktakeLine Table:** (Totals updated!)
```sql
id | stocktake_id | item_id | opening_qty | purchases | sales   | expected_qty | counted_qty | variance_qty
---|--------------|---------|-------------|-----------|---------|--------------|-------------|-------------
45 | 7            | 23      | 88.0000     | 72.0000   | 120.0000| 40.0000      | 42.0000     | 2.0000
                                           ↑ Changed!            ↑ Changed!                   ↑ Changed!
```

## Timeline: What Happens in Milliseconds

```
T+0ms    : Frontend sends POST request
T+50ms   : Django receives request
T+55ms   : Validation passes
T+60ms   : StockMovement record created in database
T+65ms   : Query all movements for recalculation
T+70ms   : Sum movements by type
T+75ms   : Update StocktakeLine record
T+80ms   : Serialize response data
T+85ms   : Send HTTP 201 response
T+135ms  : Frontend receives response
T+140ms  : React/Vue updates state
T+145ms  : UI re-renders with new values
T+150ms  : User sees updated data!
```

**Total time: ~150ms** 🚀

## Code Flow

### Frontend Code
```javascript
// 1. User clicks "Add Purchase"
const handleAddPurchase = async () => {
  // 2. Send request
  const response = await fetch(
    '/api/stock_tracker/hotel/stocktake-lines/45/add-movement/',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        movement_type: 'PURCHASE',
        quantity: 24,
        reference: 'INV-12345'
      })
    }
  );
  
  // 3. Get response
  const data = await response.json();
  
  // 4. Update UI state
  setLineData(data.line);  // ← UI updates automatically!
  
  // 5. Show success
  alert('Purchase added!');
};
```

### Backend Code Flow
```python
# views.py - add_movement action
@action(detail=True, methods=['post'])
def add_movement(self, request, pk=None):
    line = self.get_object()
    
    # 1. Create movement
    movement = StockMovement.objects.create(
        hotel=line.stocktake.hotel,
        item=line.item,
        period=line.stocktake.period,
        movement_type=request.data.get('movement_type'),
        quantity=request.data.get('quantity'),
        reference=request.data.get('reference'),
        staff=request.user.staff,
        timestamp=timezone.now()  # Auto
    )
    
    # 2. Recalculate line totals
    movements = _calculate_period_movements(
        line.item,
        line.stocktake.period_start,
        line.stocktake.period_end
    )
    
    # 3. Update line
    line.purchases = movements['purchases']
    line.sales = movements['sales']
    # ... etc
    line.save()
    
    # 4. Return updated data
    serializer = self.get_serializer(line)
    return Response({
        'movement': {...},
        'line': serializer.data  # ← Frontend gets this!
    })
```

## Summary: Complete Flow

1. **Frontend**: User enters movement data in form
2. **Frontend**: JavaScript sends POST request with JSON payload
3. **Backend**: Django receives and validates request
4. **Database**: StockMovement record created
5. **Backend**: Recalculates all totals from movements
6. **Database**: StocktakeLine record updated
7. **Backend**: Returns updated line data as JSON
8. **Frontend**: Receives response
9. **Frontend**: Updates React/Vue state
10. **UI**: Re-renders with new values
11. **User**: Sees changes immediately!

## Key Benefits

✅ **Real StockMovement records** - Not temporary data  
✅ **Instant recalculation** - No manual refresh needed  
✅ **Audit trail** - Who, what, when tracked  
✅ **Data integrity** - Formula verified  
✅ **Fast response** - ~150ms round trip  
✅ **Clean UI** - One form, instant feedback  

## Test It Yourself

```bash
# Run the quick test
cd stock_tracker
python quick_test_movement.py

# Or run the full simulation
python test_frontend_simulation.py
```

Both scripts show you exactly what happens at each step!
