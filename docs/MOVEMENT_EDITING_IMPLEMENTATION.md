# Movement Editing Feature - Implementation Summary

## What Was Added

### ✅ New Endpoint: Update Movement

**URL Pattern:**
```
PATCH /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/update-movement/{movement_id}/
```

**Purpose:** Edit an existing purchase or waste movement without deleting and re-creating it.

---

## Implementation Details

### 1. Backend View (`stock_tracker/views.py`)

Added `update_movement()` action to `StocktakeLineViewSet`:

**Features:**
- ✅ Validates stocktake not locked/approved
- ✅ Finds movement by ID within the stocktake period
- ✅ Updates any combination of fields:
  - `movement_type` ('PURCHASE' or 'WASTE')
  - `quantity` (must be > 0)
  - `unit_cost` (optional)
  - `reference` (optional)
  - `notes` (optional)
- ✅ Recalculates line purchases/waste from ALL movements
- ✅ Broadcasts update via Pusher to all viewers
- ✅ Returns updated movement + line data + old values for audit

**Response Example:**
```json
{
  "message": "Movement updated successfully",
  "movement": {
    "id": 5678,
    "movement_type": "WASTE",
    "quantity": "100.0000",
    "unit_cost": "2.5000",
    "reference": "INV-123",
    "notes": "Corrected quantity",
    "timestamp": "2025-11-09T10:30:00Z"
  },
  "old_values": {
    "movement_type": "PURCHASE",
    "quantity": "50.0000",
    "unit_cost": null,
    "reference": "INV-123",
    "notes": "Original notes"
  },
  "line": {
    "id": 1709,
    "purchases": "176.0000",
    "waste": "100.0000",
    "expected_qty": "164.0000",
    "variance_qty": "-20.5000",
    ...
  }
}
```

---

### 2. Pusher Broadcast (`stock_tracker/pusher_utils.py`)

Added `broadcast_line_movement_updated()` function:

**Event:** `line-movement-updated`

**Channel:** `{hotel}-stocktake-{stocktake_id}`

**Data Broadcast:**
```json
{
  "line_id": 1709,
  "item_sku": "BEER_DRAUGHT_GUIN",
  "movement": {
    "id": 5678,
    "movement_type": "WASTE",
    "quantity": "100.0000",
    ...
  },
  "old_values": {
    "movement_type": "PURCHASE",
    "quantity": "50.0000",
    ...
  },
  "line": { ... }
}
```

**Viewers receive:**
- Updated movement details
- Previous values for comparison
- Recalculated line data (purchases, waste, expected, variance)

---

### 3. URL Routing (`stock_tracker/urls.py`)

**Added:**
```python
stocktake_line_update_movement = StocktakeLineViewSet.as_view({
    'patch': 'update_movement'
})

path(
    '<str:hotel_identifier>/stocktake-lines/<int:pk>/update-movement/<int:movement_id>/',
    stocktake_line_update_movement,
    name='line-update-movement'
),
```

---

### 4. Frontend Documentation

Updated `docs/FRONTEND_STOCKTAKE_CALCULATIONS.md`:

**Added Section:** "Step 4: Editing Movements (Correcting Mistakes)"

**Two Options Documented:**
1. **Update Movement** - Edit existing movement (NEW)
2. **Delete Movement** - Remove movement completely (existing)

**Example Frontend Code:**
```javascript
// Update movement
async function updateMovement(lineId, movementId, updates, hotelIdentifier) {
  const url = `/api/stock_tracker/${hotelIdentifier}/stocktake-lines/${lineId}/update-movement/${movementId}/`;
  
  const response = await fetch(url, {
    method: 'PATCH',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(updates)
  });
  
  return await response.json();
}

// Usage examples:
// Correct quantity
updateMovement(1709, 5678, {
  quantity: 176.0,
  notes: 'Corrected quantity'
}, 'hotel-killarney');

// Change type
updateMovement(1709, 5678, {
  movement_type: 'WASTE',  // Was PURCHASE
  notes: 'Changed to waste'
}, 'hotel-killarney');

// Update all fields
updateMovement(1709, 5678, {
  movement_type: 'PURCHASE',
  quantity: 88.0,
  unit_cost: 2.50,
  reference: 'INV-67890',
  notes: 'Updated delivery info'
}, 'hotel-killarney');
```

---

## Complete Movement CRUD Operations

| Operation | Method | Endpoint | Purpose |
|-----------|--------|----------|---------|
| **Create** | POST | `/stocktake-lines/{id}/add-movement/` | Add purchase/waste |
| **Read** | GET | `/stocktake-lines/{id}/movements/` | List all movements |
| **Update** | PATCH | `/stocktake-lines/{id}/update-movement/{mid}/` | Edit movement ✨ NEW |
| **Delete** | DELETE | `/stocktake-lines/{id}/delete-movement/{mid}/` | Remove movement |

---

## User Workflow

### Before (No Edit):
1. User enters wrong quantity: 50 instead of 100
2. Must delete movement
3. Must re-create movement with correct quantity
4. Risk of losing reference/notes

### After (With Edit):
1. User enters wrong quantity: 50 instead of 100
2. Click "Edit" button
3. Change quantity to 100
4. Save - done! ✅
5. All metadata preserved

---

## Key Benefits

### 🎯 Better User Experience
- No need to delete and re-create
- Preserves movement timestamp
- Preserves reference and notes
- Audit trail with old_values

### 🔄 Real-time Collaboration
- All viewers see edit instantly via Pusher
- Shows old vs new values
- Line recalculates automatically

### 🛡️ Data Integrity
- Validates stocktake not locked
- Validates quantity > 0
- Recalculates from ALL movements (not just delta)
- Maintains referential integrity

### 📝 Audit Trail
- Returns old_values for logging
- Timestamp preserved from original creation
- Can track who changed what (via request.user if added)

---

## Testing

**Test Script:** `test_update_movement.py`

**What it tests:**
1. Create movement (PURCHASE, qty=50)
2. Verify line updated correctly
3. Update movement (WASTE, qty=100)
4. Verify line recalculated correctly
5. Clean up (delete movement)
6. Verify line restored to original state

**Run test:**
```bash
python test_update_movement.py
```

---

## Frontend Implementation Checklist

### UI Changes Needed:

- [ ] Add "Edit" button next to each movement in list
- [ ] Create edit modal/form with fields:
  - [ ] Movement Type dropdown (PURCHASE/WASTE)
  - [ ] Quantity input (validated > 0)
  - [ ] Unit Cost input (optional)
  - [ ] Reference input (optional)
  - [ ] Notes textarea (optional)
- [ ] Show loading state during update
- [ ] Display success message on completion
- [ ] Update line display with new values

### Pusher Integration:

- [ ] Subscribe to `line-movement-updated` event
- [ ] Handler updates movement in list
- [ ] Handler updates line totals
- [ ] Show notification: "Movement updated by [user]"
- [ ] Highlight changed movement briefly

### Error Handling:

- [ ] Handle 400: Stocktake locked
- [ ] Handle 404: Movement not found
- [ ] Handle 400: Invalid quantity (must be > 0)
- [ ] Handle 400: Invalid movement_type
- [ ] Show user-friendly error messages

---

## API Examples

### Example 1: Correct Quantity
```bash
PATCH /api/stock_tracker/hotel-killarney/stocktake-lines/1709/update-movement/5678/
Content-Type: application/json

{
  "quantity": 176.0,
  "notes": "Corrected quantity - was 50, should be 176"
}
```

### Example 2: Change Type
```bash
PATCH /api/stock_tracker/hotel-killarney/stocktake-lines/1709/update-movement/5678/
Content-Type: application/json

{
  "movement_type": "WASTE",
  "notes": "This was actually waste, not a purchase"
}
```

### Example 3: Update Everything
```bash
PATCH /api/stock_tracker/hotel-killarney/stocktake-lines/1709/update-movement/5678/
Content-Type: application/json

{
  "movement_type": "PURCHASE",
  "quantity": 88.0,
  "unit_cost": 2.50,
  "reference": "INV-NEW-123",
  "notes": "Completely updated movement"
}
```

---

## Summary

✅ **Complete CRUD** for movements (Create, Read, Update, Delete)  
✅ **Real-time updates** via Pusher for all viewers  
✅ **Audit trail** with old_values in response  
✅ **Data integrity** with automatic recalculation  
✅ **User-friendly** - no need to delete and re-create  
✅ **Fully documented** for frontend developers  

**Status:** Ready for frontend integration! 🚀
