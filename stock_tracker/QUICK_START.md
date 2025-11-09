# Quick Start: Manual Movement Entry

## What You Can Do Now

✅ **Create movements directly from stocktake line items**  
✅ **View all movements for any line item**  
✅ **Movements update calculations immediately**  
✅ **Both manual and automatic movements work together**

## Example Workflow

### Scenario: Adding a manual purchase to a line item

**Starting state:**
```
Line Item: Guinness Keg (D001)
- Opening: 88 pints
- Purchases: 48 pints (from existing movements)
- Sales: 120 pints
- Expected: 16 pints
- Counted: 42 pints
- Variance: +26 pints (something's wrong!)
```

**You realize you forgot to log a delivery!**

### Step 1: Add the missing purchase

```bash
POST /api/stock_tracker/hotel-slug/stocktake-lines/45/add-movement/

{
  "movement_type": "PURCHASE",
  "quantity": 24,
  "reference": "INV-98765",
  "notes": "Forgot to log this delivery from Nov 7"
}
```

### Step 2: Instant recalculation

```json
Response:
{
  "message": "Movement created successfully",
  "movement": {
    "id": 789,
    "movement_type": "PURCHASE",
    "quantity": "24.0000",
    "timestamp": "2025-11-09T15:45:00Z"
  },
  "line": {
    "id": 45,
    "item_sku": "D001",
    "opening_qty": "88.0000",
    "purchases": "72.0000",  // ← Changed from 48 to 72!
    "sales": "120.0000",
    "expected_qty": "40.0000",  // ← Now matches counted!
    "counted_qty": "42.0000",
    "variance_qty": "2.0000"    // ← Variance is now reasonable
  }
}
```

**Result:**
```
Line Item: Guinness Keg (D001)
- Opening: 88 pints
- Purchases: 72 pints (48 + 24 new)
- Sales: 120 pints
- Expected: 40 pints ✓
- Counted: 42 pints ✓
- Variance: +2 pints ✓ (much better!)
```

## Common Use Cases

### 1. Missing Deliveries
```javascript
// Forgot to log a delivery? Add it:
{
  "movement_type": "PURCHASE",
  "quantity": 24,
  "reference": "INV-12345"
}
```

### 2. Unreported Waste
```javascript
// Keg went bad? Record the waste:
{
  "movement_type": "WASTE",
  "quantity": 88,
  "notes": "Keg went bad, had to dump"
}
```

### 3. Inter-Bar Transfers
```javascript
// Transferred stock to upstairs bar?
{
  "movement_type": "TRANSFER_OUT",
  "quantity": 12,
  "reference": "XFR-BAR2"
}

// Received stock from main bar?
{
  "movement_type": "TRANSFER_IN",
  "quantity": 12,
  "reference": "XFR-BAR1"
}
```

### 4. Manual Sales Entry
```javascript
// Private event not in POS?
{
  "movement_type": "SALE",
  "quantity": 45,
  "reference": "EVENT-WEDDING",
  "notes": "Wedding party - 45 pints"
}
```

### 5. Stocktake Adjustments
```javascript
// Reconciling differences?
{
  "movement_type": "ADJUSTMENT",
  "quantity": -3.5,
  "notes": "Correction after recount"
}
```

## View All Movements

See everything that happened to this item:

```bash
GET /api/stock_tracker/hotel-slug/stocktake-lines/45/movements/
```

Response shows:
- **Summary** of all movement types
- **Individual movements** with full details
- **Timestamps** and staff who created them
- **References** and notes

## Frontend Integration

### Minimal Example (React)

```jsx
function QuickMovementButtons({ lineId, onUpdate }) {
  const addMovement = async (type, qty) => {
    const response = await fetch(
      `/api/stock_tracker/hotel/stocktake-lines/${lineId}/add-movement/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movement_type: type,
          quantity: qty
        })
      }
    );
    
    const data = await response.json();
    onUpdate(data.line); // Update your state
  };

  return (
    <div>
      <button onClick={() => {
        const qty = prompt('Purchase quantity:');
        if (qty) addMovement('PURCHASE', parseFloat(qty));
      }}>
        + Purchase
      </button>
      
      <button onClick={() => {
        const qty = prompt('Waste quantity:');
        if (qty) addMovement('WASTE', parseFloat(qty));
      }}>
        - Waste
      </button>
    </div>
  );
}
```

## Key Benefits

1. **No separate form needed** - Create movements right where you need them
2. **Instant feedback** - See updated totals immediately
3. **Full audit trail** - All movements are tracked and timestamped
4. **Unified system** - Manual and automatic movements work the same way
5. **Real data** - Creates actual StockMovement records in the database

## Important Rules

❌ **Cannot add movements to approved stocktakes**  
✓ Only unlocked stocktakes can be modified

✓ **Movements are permanent once stocktake is approved**  
Cannot delete or edit after approval

✓ **All movements are logged**  
Staff member and timestamp are recorded

✓ **Calculations auto-update**  
No need to manually refresh or recalculate

## Next Steps

1. Add movement input fields to your stocktake UI
2. Display the movements list for transparency
3. Show real-time calculation updates
4. Add validation for quantity inputs
5. Style the interface for easy data entry

Need help? Check the full guide: `MANUAL_MOVEMENTS_GUIDE.md`
