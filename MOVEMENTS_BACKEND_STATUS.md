# Backend Status: Purchases/Movements System

## ✅ BACKEND IS WORKING CORRECTLY

The purchases/movements creation system is **fully functional** and **tested**.

---

## 🎯 API Endpoint

```
POST /api/hotels/{hotel_slug}/stock-tracker/stocktake-lines/{line_id}/add-movement/
```

### Supported Movement Types (Hotel-Wide System)
- `PURCHASE` - Deliveries, purchases
- `SALE` - Sales, consumption
- `WASTE` - Breakage, spillage, spoilage

---

## ✅ What the Backend Does Correctly

### 1. Movement Creation
- ✅ Creates `StockMovement` records in database
- ✅ Validates required fields (`movement_type`, `quantity`)
- ✅ Validates movement type is one of: PURCHASE, SALE, WASTE
- ✅ Prevents adding movements to locked/approved stocktakes
- ✅ Records timestamp automatically
- ✅ Tracks staff member who created the movement

### 2. Automatic Recalculation
After creating a movement, the backend **automatically**:
- ✅ Recalculates `purchases` total from all PURCHASE movements
- ✅ Recalculates `sales` total from all SALE movements
- ✅ Recalculates `waste` total from all WASTE movements
- ✅ Recalculates `expected_qty` using the correct formula
- ✅ Recalculates `variance_qty` based on new expected

### 3. Correct Formula Implementation

The backend uses this formula (verified by tests):

```python
expected_qty = (
    opening_qty +
    purchases +
    transfers_in -
    sales -           # ← INCLUDES SALES
    waste -
    transfers_out +
    adjustments
)
```

For hotel-wide system (no transfers), this simplifies to:

```python
expected_qty = opening_qty + purchases - sales - waste
```

**This is the correct formula according to the documentation.**

### 4. Response Format

Returns complete updated line data:

```json
{
  "message": "Movement created successfully",
  "movement": {
    "id": 156,
    "movement_type": "PURCHASE",
    "quantity": "24.0000",
    "timestamp": "2025-11-09T14:30:00Z"
  },
  "line": {
    "id": 45,
    "item_name": "Guinness Keg",
    "opening_qty": "88.0000",
    "purchases": "72.0000",
    "sales": "120.0000",
    "waste": "0.0000",
    "expected_qty": "40.0000",
    "counted_qty": "42.0000",
    "variance_qty": "2.0000",
    // ... more fields
  }
}
```

---

## 🧪 Backend Tests

All tests pass successfully:

### Test Coverage
- ✅ `test_add_purchase_movement` - Verifies PURCHASE movements work
- ✅ `test_add_sale_movement` - Verifies SALE movements work
- ✅ `test_get_movements_for_line` - Verifies movement retrieval
- ✅ `test_formula_verification` - Confirms formula is correct

### Run Tests
```bash
python manage.py test stock_tracker.test_movement_api
```

---

## 📋 Backend Implementation Details

### File: `stock_tracker/views.py`
- Line 675-764: `add_movement` action method
- Line 770-805: `movements` action method (get all movements)

### File: `stock_tracker/models.py`
- Line 1267-1280: `expected_qty` property with correct formula
- Line 1282-1286: `variance_qty` property

### File: `stock_tracker/stocktake_service.py`
- Line 119-157: `_calculate_period_movements` function

### File: `stock_tracker/urls.py`
- Line 335-338: URL pattern for add-movement endpoint

---

## 🔍 How It Works

### Flow When Frontend POSTs Movement:

1. **Receive Request**
   - Validates `movement_type` and `quantity` are present
   - Validates movement type is PURCHASE, SALE, or WASTE
   - Checks stocktake is not locked

2. **Create Movement Record**
   ```python
   movement = StockMovement.objects.create(
       hotel=line.stocktake.hotel,
       item=line.item,
       period=line.stocktake.period,
       movement_type='PURCHASE',
       quantity=24,
       reference='INV-123',
       notes='Delivery',
       staff=request.user.staff,
       timestamp=timezone.now()
   )
   ```

3. **Recalculate Line Totals**
   ```python
   movements = _calculate_period_movements(
       line.item,
       line.stocktake.period_start,
       line.stocktake.period_end
   )
   
   line.purchases = movements['purchases']
   line.sales = movements['sales']
   line.waste = movements['waste']
   line.save()
   ```

4. **Return Updated Data**
   - Serializes the line with all recalculated fields
   - Returns movement details + updated line state

---

## ⚠️ Frontend Requirements

For the optimistic update to match the backend, the frontend **MUST**:

1. **Use the SAME formula**:
   ```javascript
   expected_qty = opening_qty + purchases - sales - waste
   ```

2. **Convert strings to numbers**:
   ```javascript
   parseFloat(line.purchases) + quantity
   ```

3. **Handle all movement types correctly**:
   ```javascript
   switch(movementType) {
     case 'PURCHASE':
       line.purchases += qty;
       break;
     case 'SALE':
       line.sales += qty;
       break;
     case 'WASTE':
       line.waste += qty;
       break;
   }
   ```

---

## 🐛 Common Frontend Issues

### Issue: "Backend returns different expected_qty than my calculation"

**Cause**: Frontend formula doesn't match backend formula

**Solution**: Ensure frontend uses: `opening + purchases - sales - waste`

### Issue: "Numbers are concatenating instead of adding"

**Cause**: Backend returns strings, frontend doesn't convert to numbers

**Solution**: Use `parseFloat()` on all numeric fields

```javascript
// ❌ WRONG
const total = line.purchases + 24;  // "50" + 24 = "5024"

// ✅ CORRECT
const total = parseFloat(line.purchases) + 24;  // 50 + 24 = 74
```

### Issue: "Optimistic update looks right, then changes"

**Cause**: Frontend calculation differs from backend

**Solution**: Log both calculations and compare:
```javascript
console.log('Frontend expected:', optimisticExpected);
console.log('Backend expected:', data.line.expected_qty);
```

---

## 📚 Related Documentation

- `FRONTEND_MOVEMENTS_GUIDE.md` - Complete frontend implementation guide
- `FRONTEND_IMPLEMENTATION.md` - Original optimistic update guide
- `stock_tracker/WASTE_AND_VARIANCE_EXPLAINED.md` - Formula explanation
- `stock_tracker/MANUAL_MOVEMENTS_GUIDE.md` - API documentation
- `stock_tracker/API_REFERENCE.md` - Detailed API specs

---

## 🆘 Troubleshooting

### Test the Backend Directly

Use curl or Postman to test:

```bash
curl -X POST \
  http://localhost:8000/api/hotels/your-hotel/stock-tracker/stocktake-lines/45/add-movement/ \
  -H "Content-Type: application/json" \
  -d '{
    "movement_type": "PURCHASE",
    "quantity": 24,
    "reference": "TEST-001",
    "notes": "Test purchase"
  }'
```

### Check Backend Logs

Run Django in verbose mode:
```bash
python manage.py runserver --verbosity 2
```

### Run Backend Tests

```bash
# All movement tests
python manage.py test stock_tracker.test_movement_api

# Specific test
python manage.py test stock_tracker.test_movement_api.MovementAPITest.test_add_purchase_movement
```

---

## ✅ Summary

**Backend Status**: ✅ **FULLY FUNCTIONAL**

**The issue is in the frontend implementation:**
1. Formula mismatch (not including sales)
2. String concatenation instead of numeric addition
3. Incorrect optimistic update calculation

**Solution**: Follow the guide in `FRONTEND_MOVEMENTS_GUIDE.md`

---

## 📞 Support

If frontend still has issues after following the guide:
1. Check browser console for errors
2. Check network tab for request/response
3. Compare frontend calculation with backend response
4. Verify all numeric conversions with `parseFloat()`
