# Voice Command Beer Handling - Frontend Implementation Guide

## Overview

This guide documents the **CORRECTED** voice command handling for beer purchases and waste after fixing the validation and conversion logic to match manual updates.

**Status:** ✅ **FIXED & TESTED** (November 20, 2025)

---

## Critical Change Summary

### What Was Fixed

The voice command confirmation endpoint now applies **identical validation and conversion logic** as the manual `add_movement` endpoint for beer purchases and waste.

| Action | What Changed | Impact |
|--------|-------------|--------|
| **PURCHASE** | ✅ Added whole number validation<br>✅ Added UOM conversion (kegs→pints, cases→bottles) | Backend now converts correctly |
| **WASTE** | ✅ Added partial unit validation<br>✅ Rejects full kegs/cases | Backend now validates properly |

---

## How Voice Commands Work

### 1. Parse Voice Command (Preview)

**Endpoint:** `POST /api/stock_tracker/{hotel}/stocktake-lines/voice-command/`

**Purpose:** Transcribe audio and parse command (NO database changes)

```typescript
const formData = new FormData();
formData.append('audio', audioBlob, 'voice-command.webm');
formData.append('stocktake_id', stocktakeId.toString());

const response = await fetch(url, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});
```

**Response:**
```json
{
  "success": true,
  "command": {
    "action": "purchase",
    "item_identifier": "guinness",
    "value": 2.0,
    "transcription": "purchase 2 kegs of guinness"
  },
  "stocktake_id": 123
}
```

---

### 2. Confirm Voice Command (Update Database)

**Endpoint:** `POST /api/stock_tracker/{hotel}/stocktake-lines/voice-command/confirm/`

**Purpose:** Apply validated command with proper conversion

```typescript
const response = await fetch(url, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    stocktake_id: stocktakeId,
    command: parsedCommand
  })
});
```

**Response (Success):**
```json
{
  "success": true,
  "line": { /* Updated StocktakeLine */ },
  "message": "Added purchase of 2 kegs (176 pints) of Guinness",
  "item_name": "Guinness",
  "item_sku": "D-GUIN-KEG"
}
```

**Response (Validation Error):**
```json
{
  "success": false,
  "error": "Purchases must be in full kegs only. Partial kegs should be recorded as waste."
}
```

---

## Frontend Handling by Action

### COUNT Commands

**No Changes** - COUNT commands work exactly as before.

```typescript
// User says: "count guinness 3 kegs 20 pints"
// Parsed: { action: 'count', full_units: 3, partial_units: 20 }
// Backend: Sets counted_full_units=3, counted_partial_units=20
// Result: counted_qty = (3 * 88) + 20 = 284 pints
```

**Frontend Display:**
```typescript
if (command.action === 'count') {
  if (command.full_units && command.partial_units) {
    message = `Count ${command.full_units} ${fullUnitLabel} and ${command.partial_units} ${partialUnitLabel} of ${itemName}?`;
  } else {
    message = `Count ${command.value} units of ${itemName}?`;
  }
}
```

---

### PURCHASE Commands

**Major Changes** - Backend now validates and converts automatically.

#### Draft Beer (Category D)

```typescript
// User says: "purchase 2 kegs of guinness"
// Parsed: { action: 'purchase', value: 2.0 }
// Backend validates: 2.0 % 1 == 0 ✅ (whole number)
// Backend converts: 2 * 88 = 176 pints
// Creates: StockMovement(quantity=176)
```

**Frontend Display:**
```typescript
if (command.action === 'purchase' && category === 'D') {
  const kegs = command.value;
  const pints = kegs * item.uom; // Calculate for display
  message = `Purchase ${kegs} kegs (${pints} pints) of ${itemName}?`;
}
```

**Validation Feedback:**
```typescript
// If backend returns error for "2.5 kegs"
{
  "success": false,
  "error": "Purchases must be in full kegs only. Partial kegs should be recorded as waste."
}

// Show error to user:
showError("Invalid purchase: " + response.error);
```

#### Bottled Beer (Category B)

```typescript
// User says: "purchase 5 cases of budweiser"
// Parsed: { action: 'purchase', value: 5.0 }
// Backend validates: 5.0 % 1 == 0 ✅
// Backend converts: 5 * 12 = 60 bottles
// Creates: StockMovement(quantity=60)
```

**Frontend Display:**
```typescript
if (command.action === 'purchase' && category === 'B') {
  const cases = command.value;
  const bottles = cases * item.uom;
  message = `Purchase ${cases} cases (${bottles} bottles) of ${itemName}?`;
}
```

---

### WASTE Commands

**Major Changes** - Backend now validates partial units only.

#### Draft Beer (Category D)

```typescript
// User says: "waste 25 pints of guinness"
// Parsed: { action: 'waste', value: 25.0 }
// Backend validates: 25.0 < 88 ✅ (partial keg)
// Backend stores: StockMovement(quantity=25) - NO conversion
// Result: ✅ Accepted

// User says: "waste 100 pints of guinness"
// Parsed: { action: 'waste', value: 100.0 }
// Backend validates: 100.0 >= 88 ❌ (full keg or more)
// Result: ❌ Rejected
```

**Frontend Display:**
```typescript
if (command.action === 'waste' && category === 'D') {
  const pints = command.value;
  const maxPints = item.uom - 0.01; // 87.99 for 88-pint keg
  
  if (pints >= item.uom) {
    // Warn user BEFORE confirming
    showWarning(`Waste must be less than ${item.uom} pints (partial keg only). Use adjustments for full kegs.`);
    disableConfirm();
  } else {
    message = `Waste ${pints} pints of ${itemName}?`;
  }
}
```

**Error Handling:**
```typescript
// Backend rejection for 100 pints
{
  "success": false,
  "error": "Waste must be partial keg only (less than 88 pints). Full kegs/cases should be recorded as negative adjustments."
}
```

#### Bottled Beer (Category B)

```typescript
// User says: "waste 7 bottles of budweiser"
// Parsed: { action: 'waste', value: 7.0 }
// Backend validates: 7.0 < 12 ✅ (partial case)
// Result: ✅ Accepted

// User says: "waste 15 bottles of budweiser"
// Parsed: { action: 'waste', value: 15.0 }
// Backend validates: 15.0 >= 12 ❌ (over full case)
// Result: ❌ Rejected
```

**Frontend Display:**
```typescript
if (command.action === 'waste' && category === 'B') {
  const bottles = command.value;
  
  if (bottles >= item.uom) {
    showWarning(`Waste must be less than ${item.uom} bottles (partial case only).`);
    disableConfirm();
  } else {
    message = `Waste ${bottles} bottles of ${itemName}?`;
  }
}
```

---

## Complete Frontend Example

```typescript
// Voice command confirmation modal component
function VoiceCommandConfirmModal({ 
  command, 
  stocktakeId, 
  onConfirm, 
  onCancel 
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Get matched item details
  const item = matchedItem; // From fuzzy search
  const category = item.category;
  const uom = item.uom;
  
  // Build confirmation message
  const getMessage = () => {
    const { action, value, full_units, partial_units, item_identifier } = command;
    
    switch (action) {
      case 'count':
        if (full_units !== undefined && partial_units !== undefined) {
          const fullLabel = category === 'D' ? 'kegs' : 'cases';
          const partialLabel = category === 'D' ? 'pints' : 'bottles';
          return `Count ${full_units} ${fullLabel} and ${partial_units} ${partialLabel} of ${item.name}?`;
        }
        return `Count ${value} units of ${item.name}?`;
      
      case 'purchase':
        if (category === 'D') {
          const pints = value * uom;
          return `Purchase ${value} kegs (${pints} pints) of ${item.name}?`;
        } else if (category === 'B') {
          const bottles = value * uom;
          return `Purchase ${value} cases (${bottles} bottles) of ${item.name}?`;
        }
        return `Purchase ${value} units of ${item.name}?`;
      
      case 'waste':
        if (category === 'D') {
          // Check if value exceeds keg size
          if (value >= uom) {
            setError(`Waste must be less than ${uom} pints (partial keg only)`);
            return null;
          }
          return `Waste ${value} pints of ${item.name}?`;
        } else if (category === 'B') {
          if (value >= uom) {
            setError(`Waste must be less than ${uom} bottles (partial case only)`);
            return null;
          }
          return `Waste ${value} bottles of ${item.name}?`;
        }
        return `Waste ${value} units of ${item.name}?`;
      
      default:
        return `Unknown action: ${action}`;
    }
  };
  
  const handleConfirm = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/stock_tracker/${hotelId}/stocktake-lines/voice-command/confirm/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            stocktake_id: stocktakeId,
            command: command
          })
        }
      );
      
      const data = await response.json();
      
      if (data.success) {
        // Show success message
        showSuccess(data.message);
        onConfirm(data.line);
      } else {
        // Show validation error from backend
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to apply voice command');
    } finally {
      setLoading(false);
    }
  };
  
  const message = getMessage();
  const canConfirm = message && !error;
  
  return (
    <Modal>
      <h3>Confirm Voice Command</h3>
      
      {/* Show transcription */}
      <div className="transcription">
        Heard: "{command.transcription}"
      </div>
      
      {/* Show parsed command */}
      {message && (
        <div className="confirmation-message">
          {message}
        </div>
      )}
      
      {/* Show validation warning */}
      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}
      
      {/* Action buttons */}
      <div className="actions">
        <button onClick={onCancel} disabled={loading}>
          Cancel
        </button>
        <button 
          onClick={handleConfirm} 
          disabled={!canConfirm || loading}
        >
          {loading ? 'Applying...' : 'Confirm'}
        </button>
      </div>
    </Modal>
  );
}
```

---

## Validation Rules Summary

### Purchase Validation

| Category | Input | Validation | Conversion | Example |
|----------|-------|------------|------------|---------|
| **Draft (D)** | Kegs | Must be whole number | `kegs × 88 → pints` | 2 kegs → 176 pints |
| **Bottled (B)** | Cases | Must be whole number | `cases × 12 → bottles` | 5 cases → 60 bottles |
| **Spirits (S)** | Bottles | Must be whole number | None (1:1) | 3 bottles → 3 bottles |

**Rejection Examples:**
- ❌ "purchase 2.5 kegs" - not whole number
- ❌ "purchase 3.7 cases" - not whole number

### Waste Validation

| Category | Input | Validation | Conversion | Example |
|----------|-------|------------|------------|---------|
| **Draft (D)** | Pints | Must be < 88 | None | 25 pints → 25 pints |
| **Bottled (B)** | Bottles | Must be < 12 | None | 7 bottles → 7 bottles |
| **Spirits (S)** | Bottles | Must be < 1 | None | 0.5 bottles → 0.5 bottles |

**Rejection Examples:**
- ❌ "waste 88 pints" - full keg (use adjustments)
- ❌ "waste 12 bottles" - full case (use adjustments)
- ❌ "waste 100 pints" - over full keg

---

## Testing Checklist

### Draft Beer Tests

- [ ] Purchase 2 kegs → Creates movement with 176 pints
- [ ] Purchase 2.5 kegs → Shows validation error
- [ ] Waste 25 pints → Accepted
- [ ] Waste 88 pints → Shows validation error
- [ ] Count 3 kegs 20 pints → Sets full=3, partial=20

### Bottled Beer Tests

- [ ] Purchase 5 cases → Creates movement with 60 bottles
- [ ] Purchase 3.5 cases → Shows validation error
- [ ] Waste 7 bottles → Accepted
- [ ] Waste 12 bottles → Shows validation error
- [ ] Count 7 cases 5 bottles → Sets full=7, partial=5

---

## Error Messages Reference

```typescript
const ERROR_MESSAGES = {
  // Purchase errors
  PURCHASE_DRAFT_NOT_WHOLE: "Purchases must be in full kegs only. Partial kegs should be recorded as waste.",
  PURCHASE_BOTTLED_NOT_WHOLE: "Purchases must be in full cases only. Partial cases should be recorded as waste.",
  
  // Waste errors
  WASTE_DRAFT_TOO_LARGE: (uom) => `Waste must be partial keg only (less than ${uom} pints). Full kegs should be recorded as negative adjustments.`,
  WASTE_BOTTLED_TOO_LARGE: (uom) => `Waste must be partial case only (less than ${uom} bottles). Full cases should be recorded as negative adjustments.`,
  
  // General errors
  ITEM_NOT_FOUND: (identifier) => `Stock item not found: ${identifier}`,
  STOCKTAKE_LOCKED: "Cannot edit approved stocktake",
};
```

---

## Migration Notes

### If You Have Existing Voice Command UI

1. **Add validation warnings** before user confirms
2. **Update confirmation messages** to show converted quantities
3. **Handle validation errors** from backend
4. **Test all scenarios** with real data

### Backend Changes (Already Applied)

- ✅ Purchase validation: whole numbers only
- ✅ Purchase conversion: kegs→pints, cases→bottles
- ✅ Waste validation: partial units only
- ✅ Descriptive error messages
- ✅ Comprehensive test suite

---

## Support

For questions or issues:
- Check test file: `test_voice_beer_validation.py`
- Review backend implementation: `voice_recognition/views.py` (lines 287-500)
- Compare with manual updates: `stock_tracker/views.py` `add_movement` action

**Last Updated:** November 20, 2025  
**Status:** Production Ready ✅
