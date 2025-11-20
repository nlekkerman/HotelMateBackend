# Voice Command Confirmation - Real-Time Updates

## Overview

When a voice command is **CONFIRMED**, it applies exactly like a manual edit and broadcasts real-time updates via Pusher.

---

## How It Works

### 1. Voice Flow
```
User speaks → Backend transcribes & parses → Preview modal → User confirms → APPLY TO STOCKTAKE
```

### 2. Confirmation = Manual Edit

When confirmed, voice commands follow the **exact same path** as manual edits:

#### Count Action
- Sets `counted_full_units` and `counted_partial_units` directly on the line
- Model's `counted_qty` property calculates total in base units
- Example: "3 cases, 5 bottles" → `full=3`, `partial=5`

#### Purchase Action  
- Creates a `StockMovement` record with type `PURCHASE`
- Adds to line's `purchases` field
- Uses backend's calculated quantity in base units

#### Waste Action
- Creates a `StockMovement` record with type `WASTE`  
- Adds to line's `waste` field
- Uses backend's calculated quantity in base units

---

## Real-Time Broadcasting

### Pusher Integration

After applying the command, the system broadcasts via Pusher:

```python
from stock_tracker.pusher_utils import broadcast_line_counted_updated

broadcast_line_counted_updated(
    hotel_identifier,
    stocktake.id,
    {
        "line_id": line.id,
        "item_sku": stock_item.sku,
        "line": serializer.data  # Full line with calculated values
    }
)
```

### What Gets Broadcasted

- **Line ID**: Which stocktake line changed
- **Item SKU**: Which product was updated  
- **Full Line Data**: All fields including calculated values:
  - `counted_qty`
  - `expected_qty`
  - `variance_qty`
  - `counted_value`
  - `variance_value`

---

## Multi-User Experience

### Scenario
- Staff Member A: Doing voice counts on their phone
- Staff Member B: Monitoring stocktake on desktop
- Staff Member C: Also counting different items

### Result
When Staff Member A confirms: "Count Budweiser 3 cases 5 bottles"

**Everyone sees instantly:**
- Budweiser line updates to show 3 cases, 5 bottles counted
- Variance recalculates automatically
- No page refresh needed
- Real-time collaboration

---

## Key Principles

✅ **Trust the backend** - Quantities are already calculated and validated  
✅ **No recalculation** - Just apply the numbers from the backend  
✅ **Same as manual** - Uses identical code path as typing in UI  
✅ **Real-time sync** - Pusher broadcasts to all connected users  
✅ **No preview mode** - Confirmed = Applied immediately  

---

## Code Location

**Backend**: `voice_recognition/views.py` → `VoiceCommandConfirmView`

**Pusher Broadcast**: Lines 346-357

**Manual Edit Comparison**: `stock_tracker/views.py` → `StocktakeLineViewSet.update()`
