# Frontend Guide: Understanding Counted Values

## How Cases and Bottles Are Stored

### The Two Fields

Every stocktake line has two counted fields:

```json
{
  "counted_full_units": 3,      // Main containers (cases, kegs, boxes)
  "counted_partial_units": 6,   // Loose units (bottles, pints, individual items)
  "counted_qty": 42             // Total calculated by backend (READ ONLY)
}
```

---

## By Category: What Each Field Represents

### Bottled Beer (Category B)
```
counted_full_units    = CASES
counted_partial_units = BOTTLES (loose, not in cases)
```

**Example:** "3 cases and 6 bottles"
```json
{
  "counted_full_units": 3,      // 3 cases
  "counted_partial_units": 6,   // 6 loose bottles
  "counted_qty": 42             // Backend calculates: (3 × 12) + 6 = 42 bottles
}
```

**Display in UI:**
```
Budweiser Bottle
Counted: 3 cases + 6 bottles
Total: 42 bottles
```

---

### Draught Beer (Category D)
```
counted_full_units    = KEGS
counted_partial_units = PINTS (from opened kegs)
```

**Example:** "2 kegs and 15 pints"
```json
{
  "counted_full_units": 2,      // 2 full kegs
  "counted_partial_units": 15,  // 15 pints from opened keg
  "counted_qty": 159            // Backend calculates: (2 × 72) + 15 = 159 pints
}
```

**Display in UI:**
```
Guinness Draught
Counted: 2 kegs + 15 pints
Total: 159 pints
```

---

### Spirits (Category S)
```
counted_full_units    = BOTTLES (total bottles as decimal)
counted_partial_units = 0 (always, because UOM=1)
```

**Example:** "5.5 bottles" (5 full + 1 half-empty)
```json
{
  "counted_full_units": 5.5,    // 5.5 bottles total
  "counted_partial_units": 0,   // Not used (UOM=1)
  "counted_qty": 5.5            // Same as full_units
}
```

**Display in UI:**
```
Jameson Whiskey
Counted: 5.5 bottles
```

---

### Wine (Category W)
```
counted_full_units    = BOTTLES (total bottles as decimal)
counted_partial_units = 0 (always, because UOM=1)
```

**Example:** "12.75 bottles"
```json
{
  "counted_full_units": 12.75,  // 12.75 bottles total
  "counted_partial_units": 0,   // Not used (UOM=1)
  "counted_qty": 12.75          // Same as full_units
}
```

**Display in UI:**
```
House Red Wine
Counted: 12.75 bottles
```

---

### Soft Drinks (Minerals - Soft Drinks)
```
counted_full_units    = CASES
counted_partial_units = BOTTLES (loose, not in cases)
```

**Example:** "4 cases and 8 bottles"
```json
{
  "counted_full_units": 4,      // 4 cases
  "counted_partial_units": 8,   // 8 loose bottles
  "counted_qty": 56             // Backend calculates: (4 × 12) + 8 = 56 bottles
}
```

---

### Syrups (Minerals - Syrups)
```
counted_full_units    = BOTTLES (total bottles as decimal)
counted_partial_units = 0 (always, because UOM=1)
```

**Example:** "2.5 bottles"
```json
{
  "counted_full_units": 2.5,    // 2.5 bottles total
  "counted_partial_units": 0,   // Not used (UOM=1)
  "counted_qty": 2.5            // Same as full_units
}
```

---

## How Voice Commands Map to These Fields

### Voice: "Count Budweiser 3 cases 6 bottles"

**Backend parses:**
```json
{
  "action": "count",
  "item_identifier": "budweiser",
  "full_units": 3,
  "partial_units": 6
}
```

**Frontend confirms → Backend applies:**
```python
line.counted_full_units = 3      # 3 cases
line.counted_partial_units = 6   # 6 bottles
line.save()
# Model calculates counted_qty = (3 × 12) + 6 = 42
```

**Response to frontend:**
```json
{
  "success": true,
  "line": {
    "counted_full_units": 3,
    "counted_partial_units": 6,
    "counted_qty": 42,
    "variance_qty": -8
  }
}
```

---

## Frontend Input Fields

### For Bottled Beer, Soft Drinks, Draught

Show **TWO input fields:**

```tsx
<div className="flex gap-2">
  <div>
    <label>Cases/Kegs</label>
    <input 
      type="number" 
      value={countedFullUnits}
      onChange={(e) => updateLine({
        counted_full_units: parseFloat(e.target.value) || 0
      })}
    />
  </div>
  
  <div>
    <label>Bottles/Pints</label>
    <input 
      type="number" 
      value={countedPartialUnits}
      onChange={(e) => updateLine({
        counted_partial_units: parseFloat(e.target.value) || 0
      })}
    />
  </div>
</div>

<p className="text-sm text-gray-500">
  Total: {countedQty} {item.category_id === 'D' ? 'pints' : 'bottles'}
</p>
```

### For Spirits, Wine, Syrups

Show **ONE input field:**

```tsx
<div>
  <label>Bottles</label>
  <input 
    type="number" 
    step="0.25"
    value={countedFullUnits}
    onChange={(e) => updateLine({
      counted_full_units: parseFloat(e.target.value) || 0,
      counted_partial_units: 0  // Always 0 for UOM=1 items
    })}
  />
  <span className="text-xs text-gray-400">
    Use decimals: 2.5 = 2½ bottles, 3.75 = 3¾ bottles
  </span>
</div>
```

---

## When Voice Command is Confirmed

### 1. Backend Response Includes Full Line Data

```json
{
  "success": true,
  "line": {
    "id": 456,
    "item": {
      "id": 789,
      "sku": "B0070",
      "name": "Budweiser Bottle",
      "category_id": "B"
    },
    "counted_full_units": 3.00,       // Use this for "cases" input
    "counted_partial_units": 6.00,    // Use this for "bottles" input
    "counted_qty": 42.00,             // Show as calculated total
    "expected_qty": 50.00,
    "variance_qty": -8.00,
    "opening_qty": 40.00,
    "purchases": 10.00,
    "waste": 0.00
  },
  "message": "Counted 3 and 6 of Budweiser Bottle"
}
```

### 2. Update Your UI State

```tsx
const handleVoiceConfirm = async (command) => {
  const result = await voiceCommandService.confirmVoiceCommand(
    hotelId,
    stocktakeId,
    command
  );
  
  if (result.success) {
    // Update the specific line in your state
    updateStocktakeLine(result.line.id, {
      counted_full_units: result.line.counted_full_units,
      counted_partial_units: result.line.counted_partial_units,
      counted_qty: result.line.counted_qty,
      variance_qty: result.line.variance_qty,
      // ... all other fields from result.line
    });
    
    toast.success(result.message);
  }
};
```

### 3. Pusher Real-time Update

```tsx
useEffect(() => {
  const channel = pusher.subscribe(`stocktake-${stocktakeId}`);
  
  channel.bind('line-counted-updated', (data) => {
    // data.line contains the full updated line
    updateStocktakeLine(data.line_id, data.line);
  });
  
  return () => {
    channel.unbind_all();
    channel.unsubscribe();
  };
}, [stocktakeId]);
```

---

## Quick Reference Table

| Category | Full Units Field | Partial Units Field | Display |
|----------|------------------|---------------------|---------|
| Bottled Beer (B) | Cases | Bottles | "3 cases + 6 bottles" |
| Draught (D) | Kegs | Pints | "2 kegs + 15 pints" |
| Spirits (S) | Bottles (decimal) | 0 | "5.5 bottles" |
| Wine (W) | Bottles (decimal) | 0 | "12.75 bottles" |
| Soft Drinks (M) | Cases | Bottles | "4 cases + 8 bottles" |
| Syrups (M) | Bottles (decimal) | 0 | "2.5 bottles" |

---

## Important Rules

✅ **DO:**
- Use `counted_full_units` for main containers (cases/kegs/bottles)
- Use `counted_partial_units` for loose units (bottles/pints)
- Display `counted_qty` as the calculated total (read-only)
- Send BOTH fields when updating a line

❌ **DON'T:**
- Try to calculate `counted_qty` yourself (backend does this)
- Use `value` field from voice command for counts
- Assume all items work the same way
- Forget to handle the category-specific logic

---

## Testing Checklist

- [ ] Bottled beer: Type "3" in cases, "6" in bottles → See total 42
- [ ] Draught: Type "2" in kegs, "15" in pints → See total 159
- [ ] Spirits: Type "5.5" in bottles → See total 5.5
- [ ] Voice: "Count Budweiser 3 cases 6 bottles" → See 3 cases + 6 bottles
- [ ] Manual edit: Change cases to 4 → Total updates to 54
- [ ] Real-time: Another user counts → Your UI updates instantly
