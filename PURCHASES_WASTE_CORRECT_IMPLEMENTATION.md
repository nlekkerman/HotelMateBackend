# Purchases and Waste: Correct Backend Implementation

## 🚨 CRITICAL ISSUE IDENTIFIED

The frontend documentation (`PURCHASES_WASTE_BACKEND_EXPLANATION.md`) describes a **`StocktakeMovement`** model that **DOES NOT EXIST** in the backend. This is causing confusion about how purchases and waste should be handled.

---

## Current Backend Implementation

### What Actually Exists

1. **`StockMovement`** model (NOT `StocktakeMovement`)
   - Used for hotel-wide inventory tracking
   - Tracks: `PURCHASE`, `WASTE`, `SALE`, `TRANSFER_IN`, `TRANSFER_OUT`, `ADJUSTMENT`, `COCKTAIL_CONSUMPTION`
   - Linked to `StockPeriod` (not individual stocktake lines)
   - Creates permanent audit trail in the database

2. **`StocktakeLine`** fields:
   - `purchases` - Decimal field storing cumulative purchases in servings
   - `waste` - Decimal field storing cumulative waste in servings
   - These are calculated by summing `StockMovement` records during the period

---

## How It Currently Works

### When User Adds Purchases/Waste

**Endpoint:** `POST /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/add-movement/`

**Request Body:**
```json
{
  "movement_type": "PURCHASE",  // or "WASTE"
  "quantity": 5.5,
  "unit_cost": 2.50,  // optional
  "reference": "INV-12345",  // optional
  "notes": "Manual entry from stocktake"  // optional
}
```

**Backend Process:**

1. **Create `StockMovement` Record**
   ```python
   movement = StockMovement.objects.create(
       hotel=line.stocktake.hotel,
       item=line.item,
       period=period,  # Linked to StockPeriod
       movement_type=movement_type,  # 'PURCHASE' or 'WASTE'
       quantity=quantity,
       unit_cost=unit_cost,
       reference=reference,
       notes=notes,
       staff=staff_user
   )
   ```

2. **Recalculate Line Totals**
   ```python
   from .stocktake_service import _calculate_period_movements
   
   movements = _calculate_period_movements(
       line.item,
       line.stocktake.period_start,
       line.stocktake.period_end
   )
   
   # Update cumulative totals
   line.purchases = movements['purchases']
   line.waste = movements['waste']
   line.save()
   ```

3. **Calculate Expected Quantity**
   ```python
   @property
   def expected_qty(self):
       return self.opening_qty + self.purchases - self.waste
   ```

4. **Calculate Variance**
   ```python
   @property
   def variance_qty(self):
       return self.counted_qty - self.expected_qty
   ```

5. **Return Updated Line**
   ```json
   {
     "message": "Movement created successfully",
     "movement": {
       "id": 123,
       "movement_type": "PURCHASE",
       "quantity": "5.5000",
       "timestamp": "2024-11-18T10:30:00Z"
     },
     "line": {
       "id": 456,
       "item_sku": "D0001",
       "opening_qty": "10.0000",
       "purchases": "5.5000",
       "waste": "0.0000",
       "expected_qty": "15.5000",
       "counted_qty": "12.0000",
       "variance_qty": "-3.5000",
       "variance_value": "-35.00"
     }
   }
   ```

---

## Key Differences from Frontend Documentation

| Frontend Doc Says | Backend Reality |
|------------------|----------------|
| Creates `StocktakeMovement` | Creates `StockMovement` |
| Linked to specific line | Linked to `StockPeriod` and `StockItem` |
| Individual movement tracking per line | Hotel-wide movement tracking |
| `purchases` field increments | `purchases` field **recalculated from ALL movements** |
| Cumulative additions | **SUM of all matching movements** |

---

## The Critical Logic Difference

### Frontend Expects (WRONG):
```
New Purchase = 5.5
Old purchases = 3.0
New purchases = 3.0 + 5.5 = 8.5  ✅ Simple addition
```

### Backend Actually Does (CORRECT):
```
Query ALL StockMovement records for this item during period:
- Movement 1: PURCHASE, 3.0
- Movement 2: PURCHASE, 5.5
- Movement 3: WASTE, 2.0

purchases = SUM(PURCHASE movements) = 3.0 + 5.5 = 8.5  ✅
waste = SUM(WASTE movements) = 2.0  ✅
```

**Result:** Same totals, but different approach!

---

## Why This Design is Better

### ✅ Advantages

1. **Single Source of Truth**
   - `StockMovement` table is the authoritative record
   - Line fields are **calculated views** of movements

2. **Audit Trail**
   - Every purchase/waste entry creates a permanent record
   - Can track who added what, when
   - Can delete individual movements and recalculate

3. **Hotel-Wide Reporting**
   - Movements are tracked at hotel/period level
   - Can report on purchases/waste across all stocktakes
   - Not siloed to individual stocktake lines

4. **Consistency**
   - If movements are added outside stocktake flow, they're still included
   - Multiple stocktakes for same period see same data

5. **Flexibility**
   - Can edit/delete individual movements
   - Line totals automatically update
   - No risk of cumulative arithmetic errors

---

## Frontend Requirements

### What the Frontend MUST Do

1. **Accept Response Structure**
   ```javascript
   const response = await api.post(url, payload);
   
   // Response includes BOTH movement and updated line
   const { movement, line } = response.data;
   
   // Update UI with line data (already recalculated)
   updateLineInState(line.id, line);
   ```

2. **Display Correct Values**
   - `line.purchases` - Total cumulative purchases (already calculated)
   - `line.waste` - Total cumulative waste (already calculated)
   - `line.expected_qty` - Calculated from formula
   - `line.variance_qty` - Counted minus expected

3. **NO Optimistic Updates**
   - Do NOT add quantity to existing `purchases` locally
   - Do NOT calculate `expected_qty` in frontend
   - Always use backend response values

4. **Movement History**
   - Can fetch movement history: `GET /stocktake-lines/{id}/movements/`
   - Displays list of individual purchase/waste entries
   - Shows who added what, when

---

## Complete Flow Example

### Initial State
```json
{
  "id": 123,
  "item_sku": "B0045",
  "opening_qty": "24.0000",
  "purchases": "0.0000",
  "waste": "0.0000",
  "expected_qty": "24.0000"
}
```

### User Adds Purchase (12 bottles)
**POST** `/stocktake-lines/123/add-movement/`
```json
{
  "movement_type": "PURCHASE",
  "quantity": 12.0,
  "notes": "Delivery received"
}
```

**Backend:**
1. Creates StockMovement record (id=501)
2. Queries all movements for item during period
3. Recalculates: `purchases = SUM(PURCHASE) = 12.0`
4. Returns updated line

**Response:**
```json
{
  "message": "Movement created successfully",
  "movement": {
    "id": 501,
    "movement_type": "PURCHASE",
    "quantity": "12.0000",
    "timestamp": "2024-11-18T10:00:00Z"
  },
  "line": {
    "id": 123,
    "purchases": "12.0000",
    "expected_qty": "36.0000"
  }
}
```

### User Adds Waste (2 bottles)
**POST** `/stocktake-lines/123/add-movement/`
```json
{
  "movement_type": "WASTE",
  "quantity": 2.0,
  "notes": "Broken bottles"
}
```

**Backend:**
1. Creates StockMovement record (id=502)
2. Recalculates: 
   - `purchases = 12.0` (unchanged)
   - `waste = 2.0` (new)
3. Returns updated line

**Response:**
```json
{
  "line": {
    "purchases": "12.0000",
    "waste": "2.0000",
    "expected_qty": "34.0000"
  }
}
```

### User Deletes Purchase Movement
**DELETE** `/stocktake-lines/123/delete-movement/501/`

**Backend:**
1. Deletes StockMovement(id=501)
2. Recalculates:
   - `purchases = SUM(PURCHASE) = 0.0` (no more purchases)
   - `waste = 2.0` (unchanged)

**Response:**
```json
{
  "line": {
    "purchases": "0.0000",
    "waste": "2.0000",
    "expected_qty": "22.0000"
  }
}
```

---

## Verification Queries

### Check Movements for a Line
```sql
SELECT 
    movement_type,
    quantity,
    reference,
    notes,
    timestamp
FROM stock_tracker_stockmovement
WHERE item_id = (
    SELECT item_id 
    FROM stock_tracker_stocktakeline 
    WHERE id = 123
)
AND timestamp >= '2024-11-01'
AND timestamp <= '2024-11-30'
ORDER BY timestamp DESC;
```

### Verify Calculations
```sql
-- Total purchases
SELECT SUM(quantity) 
FROM stock_tracker_stockmovement
WHERE item_id = 456
AND movement_type = 'PURCHASE'
AND timestamp BETWEEN '2024-11-01' AND '2024-11-30';

-- Should match line.purchases
SELECT purchases 
FROM stock_tracker_stocktakeline
WHERE id = 123;
```

---

## Summary

### ✅ What Backend Does (CORRECT)

1. Creates **permanent `StockMovement` records** for audit trail
2. **Recalculates** `purchases` and `waste` from ALL movements each time
3. Automatically updates `expected_qty` and `variance_qty`
4. Returns fully calculated line data to frontend
5. Broadcasts changes via Pusher to all clients

### ❌ What Frontend Doc Describes (INCORRECT)

1. References non-existent `StocktakeMovement` model
2. Suggests cumulative additions (which happen, but via SUM not +=)
3. Implies line-specific movement tracking (actually period-wide)

### ✅ What Frontend Should Do (FIX REQUIRED)

1. Send `movement_type` and `quantity` to backend
2. Accept response with updated line data
3. Replace entire line state with response data
4. Never calculate `purchases`, `waste`, or `expected_qty` locally
5. Trust backend calculations completely

---

## Action Items

### For Frontend Team

1. **Update Documentation**
   - Replace references to `StocktakeMovement` with `StockMovement`
   - Clarify that backend does ALL calculations
   - Emphasize "trust the response" principle

2. **Review Code**
   - Remove any optimistic updates to `purchases`/`waste`
   - Remove local `expected_qty` calculations
   - Ensure using response data directly

3. **Test Scenarios**
   - Add purchase → verify totals
   - Add waste → verify totals
   - Delete movement → verify recalculation
   - Add multiple purchases → verify SUM

### For Backend Team

1. **✅ Already Correct** - No changes needed
2. Consider adding response field documentation
3. Consider adding validation examples to API docs

---

## API Reference

### Add Movement
**POST** `/api/stock_tracker/{hotel}/stocktake-lines/{line_id}/add-movement/`

**Request:**
```json
{
  "movement_type": "PURCHASE|WASTE",
  "quantity": 10.5,
  "unit_cost": 2.50,  // optional
  "reference": "INV-12345",  // optional
  "notes": "Manual entry"  // optional
}
```

**Response:**
```json
{
  "message": "Movement created successfully",
  "movement": {
    "id": 123,
    "movement_type": "PURCHASE",
    "quantity": "10.5000",
    "timestamp": "2024-11-18T10:30:00Z"
  },
  "line": {
    "id": 456,
    "item_sku": "D0001",
    "opening_qty": "10.0000",
    "purchases": "15.5000",  // Recalculated total
    "waste": "2.0000",
    "expected_qty": "23.5000",  // Calculated
    "counted_qty": "20.0000",
    "variance_qty": "-3.5000",  // Calculated
    "variance_value": "-35.00"
  }
}
```

### Get Movements
**GET** `/api/stock_tracker/{hotel}/stocktake-lines/{line_id}/movements/`

**Response:**
```json
{
  "movements": [
    {
      "id": 123,
      "movement_type": "PURCHASE",
      "quantity": "10.5000",
      "reference": "INV-12345",
      "notes": "Manual entry",
      "timestamp": "2024-11-18T10:30:00Z"
    }
  ],
  "summary": {
    "total_purchases": "15.5000",
    "total_waste": "2.0000",
    "movement_count": 3
  }
}
```

### Delete Movement
**DELETE** `/api/stock_tracker/{hotel}/stocktake-lines/{line_id}/delete-movement/{movement_id}/`

**Response:**
```json
{
  "message": "Movement deleted successfully",
  "deleted_movement": {
    "id": 123,
    "movement_type": "PURCHASE",
    "quantity": "10.5000"
  },
  "line": {
    // Updated line data with recalculated totals
  }
}
```

### Update Movement
**PATCH** `/api/stock_tracker/{hotel}/stocktake-lines/{line_id}/update-movement/{movement_id}/`

**Request:**
```json
{
  "movement_type": "PURCHASE",
  "quantity": 75.0,
  "unit_cost": 2.50,
  "reference": "Updated ref",
  "notes": "Corrected quantity"
}
```

**Response:**
```json
{
  "message": "Movement updated successfully",
  "movement": {
    // Updated movement data
  },
  "old_values": {
    // Previous values for audit
  },
  "line": {
    // Updated line data with recalculated totals
  }
}
```

---

## ⚠️ CRITICAL BUGS FIXED

### Bug #1: Movement Timestamp Outside Period

**Problem:** When adding purchases/waste via the API, movements were created with `timestamp=NOW()`. If you're entering data for a past period (e.g., February stocktake in November), the movement timestamp would be in November, **outside the stocktake period**. This caused the movement to be excluded from calculations.

**Example:**
- Stocktake period: Feb 1-28, 2025
- User adds purchase on Nov 18, 2025
- Movement timestamp: Nov 18, 2025 ❌ (outside period)
- Result: Movement not included in purchases calculation

**Fix Applied:**
```python
# Create movement with timestamp within the stocktake period
movement_timestamp = timezone.now()
period_end_dt = timezone.make_aware(
    datetime.combine(line.stocktake.period_end, time.max)
)

# If current time is after period, use period end date instead
if movement_timestamp > period_end_dt:
    movement_timestamp = period_end_dt

# Create movement and override auto_now_add timestamp
movement = StockMovement.objects.create(...)
movement.timestamp = movement_timestamp  # Force timestamp to be in period
movement.save(update_fields=['timestamp'])
```

**Impact:**
- ✅ Movements are always within the stocktake period
- ✅ Historical data entry works correctly
- ✅ Purchases/waste fields update properly

---

### Bug #2: Date/DateTime Comparison Issue

**Problem:** The `_calculate_period_movements` function was comparing:
- `timestamp` (DateTimeField) 
- `period_start` / `period_end` (DateField)

This caused Django to receive **naive datetime** objects, which could miss movements created at certain times of day.

**Fix Applied:**
```python
# Before (WRONG)
movements = item.movements.filter(
    timestamp__gte=period_start,  # date compared to datetime
    timestamp__lte=period_end
)

# After (CORRECT)
from django.utils import timezone
from datetime import datetime, time

start_dt = timezone.make_aware(datetime.combine(period_start, time.min))
end_dt = timezone.make_aware(datetime.combine(period_end, time.max))

movements = item.movements.filter(
    timestamp__gte=start_dt,  # timezone-aware datetime
    timestamp__lte=end_dt
)
```

**Impact:**
- ✅ All movements are now properly included in calculations
- ✅ Purchases and waste fields update correctly after adding movements
- ✅ No timezone warnings in logs

---

## Conclusion

The backend implementation is **correct and robust** with the datetime fix applied. The frontend needs to:

1. Update documentation to match actual backend behavior
2. Trust backend calculations completely
3. Use response data directly without local calculations
4. Understand that `StockMovement` (not `StocktakeMovement`) is the source of truth

**Backend fix applied** ✅ - system is now working as designed!
