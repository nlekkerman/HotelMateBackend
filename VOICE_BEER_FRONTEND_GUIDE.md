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

## Voice Command User Input Validation (Frontend Pre-Check)

### Critical Rule: Frontend Must Guide Users to Valid Inputs

Just like the manual entry UI prevents invalid inputs, the voice command flow should:

1. **PREVIEW parsed values** before confirmation
2. **VALIDATE locally** using same rules as manual entry
3. **SHOW warnings** for invalid values
4. **DISABLE confirm button** if validation fails
5. **EXPLAIN why** the value is invalid

---

## Voice Input Validation Logic (Match Manual Entry)

### Purchase Validation (Frontend)

```typescript
/**
 * Validate purchase quantity BEFORE sending to backend
 * Matches manual entry validation rules exactly
 */
function validatePurchaseQuantity(
  value: number, 
  category: string, 
  uom: number
): { valid: boolean; error?: string; convertedQty?: number } {
  
  // Rule 1: Must be whole number (no decimals)
  if (value % 1 !== 0) {
    if (category === 'D') {
      return {
        valid: false,
        error: "Purchases must be in full kegs only. Partial kegs should be recorded as waste."
      };
    } else if (category === 'B') {
      return {
        valid: false,
        error: "Purchases must be in full cases only. Partial cases should be recorded as waste."
      };
    } else if (category === 'S' || category === 'W') {
      return {
        valid: false,
        error: "Purchases must be in full bottles only. Partial bottles should be recorded as waste."
      };
    }
  }
  
  // Rule 2: Calculate converted quantity for display
  let convertedQty = value;
  if (uom !== 1) {
    // Draft/Bottled Beer: convert containers to servings
    convertedQty = value * uom;
  }
  
  return { 
    valid: true, 
    convertedQty 
  };
}
```

### Waste Validation (Frontend)

```typescript
/**
 * Validate waste quantity BEFORE sending to backend
 * Matches manual entry validation rules exactly
 */
function validateWasteQuantity(
  value: number, 
  category: string, 
  subcategory: string | null,
  uom: number
): { valid: boolean; error?: string } {
  
  if (uom === 1) {
    // UOM=1: Spirits, Wine, Syrups, BIB, Bulk Juices
    // Must be less than 1 (partial bottle/box only)
    if (value >= 1) {
      let unitName = 'unit';
      
      if (category === 'M' && subcategory === 'SYRUPS') {
        unitName = 'bottle';
      } else if (category === 'M') {
        unitName = 'box';
      } else if (category === 'S' || category === 'W') {
        unitName = 'bottle';
      }
      
      return {
        valid: false,
        error: `Waste must be partial ${unitName}s only (less than 1 ${unitName}). Full ${unitName}s should be recorded as negative adjustments.`
      };
    }
  } else {
    // UOM>1: Draught, Bottled Beer, Soft Drinks, Cordials
    // Must be less than full unit
    if (value >= uom) {
      let unitName = '';
      
      if (category === 'D') {
        unitName = `partial keg only (less than ${Math.floor(uom)} pints)`;
      } else if (category === 'B') {
        unitName = `partial case only (less than ${Math.floor(uom)} bottles)`;
      } else if (category === 'M' && subcategory === 'SOFT_DRINKS') {
        unitName = `partial case only (less than ${Math.floor(uom)} bottles)`;
      } else if (category === 'M' && subcategory === 'CORDIALS') {
        unitName = `partial case only (less than ${Math.floor(uom)} bottles)`;
      } else {
        unitName = `partial unit (less than ${Math.floor(uom)})`;
      }
      
      return {
        valid: false,
        error: `Waste must be ${unitName}. Full kegs/cases should be recorded as negative adjustments.`
      };
    }
  }
  
  return { valid: true };
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
  const [validationWarning, setValidationWarning] = useState(null);
  
  // Get matched item details
  const item = matchedItem; // From fuzzy search
  const category = item.category;
  const subcategory = item.subcategory;
  const uom = item.uom;
  
  // Validate and build confirmation message
  const validateAndBuildMessage = () => {
    const { action, value, full_units, partial_units, item_identifier } = command;
    
    // Reset validation state
    setValidationWarning(null);
    
    switch (action) {
      case 'count':
        // COUNT: No validation needed, always valid
        if (full_units !== undefined && partial_units !== undefined) {
          const fullLabel = category === 'D' ? 'kegs' : 'cases';
          const partialLabel = category === 'D' ? 'pints' : 'bottles';
          return {
            valid: true,
            message: `Count ${full_units} ${fullLabel} and ${partial_units} ${partialLabel} of ${item.name}?`,
            details: null
          };
        }
        return {
          valid: true,
          message: `Count ${value} units of ${item.name}?`,
          details: null
        };
      
      case 'purchase': {
        // PURCHASE: Validate using same logic as manual entry
        const validation = validatePurchaseQuantity(value, category, uom);
        
        if (!validation.valid) {
          setValidationWarning(validation.error);
          return {
            valid: false,
            message: null,
            details: null
          };
        }
        
        // Build display message with converted quantity
        if (category === 'D') {
          const kegs = Math.floor(value);
          const pints = validation.convertedQty;
          return {
            valid: true,
            message: `Purchase ${kegs} ${kegs === 1 ? 'keg' : 'kegs'} of ${item.name}?`,
            details: `Backend will record: ${pints} pints`
          };
        } else if (category === 'B') {
          const cases = Math.floor(value);
          const bottles = validation.convertedQty;
          return {
            valid: true,
            message: `Purchase ${cases} ${cases === 1 ? 'case' : 'cases'} of ${item.name}?`,
            details: `Backend will record: ${bottles} bottles`
          };
        } else if (category === 'S' || category === 'W') {
          const bottles = Math.floor(value);
          return {
            valid: true,
            message: `Purchase ${bottles} ${bottles === 1 ? 'bottle' : 'bottles'} of ${item.name}?`,
            details: null
          };
        }
        
        return {
          valid: true,
          message: `Purchase ${value} units of ${item.name}?`,
          details: null
        };
      }
      
      case 'waste': {
        // WASTE: Validate using same logic as manual entry
        const validation = validateWasteQuantity(value, category, subcategory, uom);
        
        if (!validation.valid) {
          setValidationWarning(validation.error);
          return {
            valid: false,
            message: null,
            details: null
          };
        }
        
        // Build display message
        if (category === 'D') {
          return {
            valid: true,
            message: `Waste ${value} pints of ${item.name}?`,
            details: `Partial keg waste (max: ${Math.floor(uom - 0.01)} pints)`
          };
        } else if (category === 'B') {
          return {
            valid: true,
            message: `Waste ${value} bottles of ${item.name}?`,
            details: `Partial case waste (max: ${Math.floor(uom - 1)} bottles)`
          };
        } else if (category === 'S' || category === 'W') {
          return {
            valid: true,
            message: `Waste ${value} of a bottle of ${item.name}?`,
            details: `Partial bottle waste (max: 0.99)`
          };
        }
        
        return {
          valid: true,
          message: `Waste ${value} units of ${item.name}?`,
          details: null
        };
      }
      
      default:
        return {
          valid: false,
          message: null,
          details: null
        };
    }
  };
  
  const handleConfirm = async () => {
    // Double-check validation before sending
    const result = validateAndBuildMessage();
    
    if (!result.valid) {
      // This shouldn't happen if button is disabled, but safety check
      return;
    }
    
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
        // Show success message from backend
        showSuccess(data.message);
        onConfirm(data.line);
      } else {
        // Backend validation error (should rarely happen with frontend validation)
        setError(data.error);
        console.warn('Backend rejected command that passed frontend validation:', data.error);
      }
    } catch (err) {
      setError('Failed to apply voice command');
      console.error('Voice command error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Validate and get message
  const result = validateAndBuildMessage();
  const canConfirm = result.valid && !error && !loading;
  
  return (
    <Modal>
      <h3>Confirm Voice Command</h3>
      
      {/* Show transcription */}
      <div className="transcription">
        <strong>Heard:</strong> "{command.transcription}"
      </div>
      
      {/* Show matched item */}
      <div className="matched-item">
        <strong>Matched Item:</strong> {item.name} ({item.sku})
        <div className="item-category">
          Category: {category} | UOM: {uom}
        </div>
      </div>
      
      {/* Show parsed command */}
      {result.valid && result.message && (
        <div className="confirmation-message">
          <div className="main-message">
            {result.message}
          </div>
          {result.details && (
            <div className="details-message">
              ℹ️ {result.details}
            </div>
          )}
        </div>
      )}
      
      {/* Show frontend validation warning */}
      {validationWarning && (
        <div className="validation-warning">
          <strong>⚠️ Invalid Input</strong>
          <p>{validationWarning}</p>
          <p className="help-text">
            {command.action === 'purchase' && 'Tip: Purchases must be in full containers. Use waste for partial containers.'}
            {command.action === 'waste' && 'Tip: Waste is for partial containers only. Use adjustments for full containers.'}
          </p>
        </div>
      )}
      
      {/* Show backend error (rare) */}
      {error && (
        <div className="error-message">
          <strong>❌ Error</strong>
          <p>{error}</p>
        </div>
      )}
      
      {/* Action buttons */}
      <div className="actions">
        <button 
          onClick={onCancel} 
          disabled={loading}
          className="btn-cancel"
        >
          Cancel
        </button>
        <button 
          onClick={handleConfirm} 
          disabled={!canConfirm}
          className={`btn-confirm ${canConfirm ? 'enabled' : 'disabled'}`}
        >
          {loading ? (
            <>
              <Spinner /> Applying...
            </>
          ) : (
            'Confirm & Apply'
          )}
        </button>
      </div>
      
      {/* Show why button is disabled */}
      {!canConfirm && !loading && (
        <div className="disabled-reason">
          {validationWarning ? (
            '⚠️ Cannot confirm: Invalid input value'
          ) : error ? (
            '⚠️ Cannot confirm: Error occurred'
          ) : (
            '⚠️ Cannot confirm'
          )}
        </div>
      )}
    </Modal>
  );
}
```

---

## CSS Styling Example

```css
/* Voice command confirmation modal */
.voice-confirmation-modal {
  max-width: 500px;
  padding: 24px;
}

.transcription {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #666;
}

.matched-item {
  border-left: 3px solid #2196F3;
  padding: 12px;
  margin-bottom: 16px;
  background: #E3F2FD;
}

.item-category {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.confirmation-message {
  padding: 16px;
  background: #E8F5E9;
  border-radius: 4px;
  margin-bottom: 16px;
}

.main-message {
  font-size: 18px;
  font-weight: 600;
  color: #2E7D32;
  margin-bottom: 8px;
}

.details-message {
  font-size: 13px;
  color: #558B2F;
  font-style: italic;
}

.validation-warning {
  background: #FFF3E0;
  border-left: 4px solid #FF9800;
  padding: 16px;
  margin-bottom: 16px;
}

.validation-warning strong {
  color: #E65100;
  display: block;
  margin-bottom: 8px;
}

.validation-warning p {
  margin: 8px 0;
  color: #E65100;
}

.help-text {
  font-size: 13px;
  color: #F57C00;
  font-style: italic;
  margin-top: 12px;
}

.error-message {
  background: #FFEBEE;
  border-left: 4px solid #F44336;
  padding: 16px;
  margin-bottom: 16px;
}

.error-message strong {
  color: #C62828;
  display: block;
  margin-bottom: 8px;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-cancel,
.btn-confirm {
  flex: 1;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: #E0E0E0;
  color: #424242;
}

.btn-cancel:hover:not(:disabled) {
  background: #BDBDBD;
}

.btn-confirm.enabled {
  background: #4CAF50;
  color: white;
}

.btn-confirm.enabled:hover {
  background: #45a049;
}

.btn-confirm.disabled {
  background: #BDBDBD;
  color: #757575;
  cursor: not-allowed;
}

.disabled-reason {
  text-align: center;
  font-size: 13px;
  color: #757575;
  margin-top: 8px;
  font-style: italic;
}
```

---

## Complete Validation Flow Example

### Step-by-Step: Purchase 2.5 Kegs (Invalid)

```typescript
// 1. User records voice: "purchase 2.5 kegs of guinness"
// 2. Parser returns: { action: 'purchase', value: 2.5, item_identifier: 'guinness' }
// 3. Frontend shows preview modal

// 4. Validation runs:
const validation = validatePurchaseQuantity(2.5, 'D', 88);
// Returns: { valid: false, error: "Purchases must be in full kegs only..." }

// 5. UI shows:
// ⚠️ Invalid Input
// Purchases must be in full kegs only. Partial kegs should be recorded as waste.
// Tip: Purchases must be in full containers. Use waste for partial containers.
// 
// [Cancel] [Confirm & Apply - DISABLED]

// 6. User cannot proceed - must cancel and re-record
```

### Step-by-Step: Purchase 2 Kegs (Valid)

```typescript
// 1. User records voice: "purchase 2 kegs of guinness"
// 2. Parser returns: { action: 'purchase', value: 2.0, item_identifier: 'guinness' }
// 3. Frontend shows preview modal

// 4. Validation runs:
const validation = validatePurchaseQuantity(2, 'D', 88);
// Returns: { valid: true, convertedQty: 176 }

// 5. UI shows:
// Purchase 2 kegs of Guinness?
// ℹ️ Backend will record: 176 pints
//
// [Cancel] [Confirm & Apply - ENABLED]

// 6. User clicks confirm
// 7. Backend receives: { action: 'purchase', value: 2 }
// 8. Backend validates: 2 % 1 == 0 ✓
// 9. Backend converts: 2 * 88 = 176 pints
// 10. Backend creates: StockMovement(quantity=176)
// 11. Success message: "Added purchase of 2 kegs (176 pints) of Guinness"
```

### Step-by-Step: Waste 100 Pints (Invalid)

```typescript
// 1. User records voice: "waste 100 pints of guinness"
// 2. Parser returns: { action: 'waste', value: 100, item_identifier: 'guinness' }
// 3. Frontend shows preview modal

// 4. Validation runs:
const validation = validateWasteQuantity(100, 'D', null, 88);
// Returns: { valid: false, error: "Waste must be partial keg only..." }

// 5. UI shows:
// ⚠️ Invalid Input
// Waste must be partial keg only (less than 88 pints). Full kegs/cases should be recorded as negative adjustments.
// Tip: Waste is for partial containers only. Use adjustments for full containers.
//
// [Cancel] [Confirm & Apply - DISABLED]

// 6. User cannot proceed
```

### Step-by-Step: Waste 25 Pints (Valid)

```typescript
// 1. User records voice: "waste 25 pints of guinness"
// 2. Parser returns: { action: 'waste', value: 25, item_identifier: 'guinness' }
// 3. Frontend shows preview modal

// 4. Validation runs:
const validation = validateWasteQuantity(25, 'D', null, 88);
// Returns: { valid: true }

// 5. UI shows:
// Waste 25 pints of Guinness?
// ℹ️ Partial keg waste (max: 87 pints)
//
// [Cancel] [Confirm & Apply - ENABLED]

// 6. User clicks confirm
// 7. Backend receives: { action: 'waste', value: 25 }
// 8. Backend validates: 25 < 88 ✓
// 9. Backend creates: StockMovement(quantity=25) - no conversion
// 10. Success message: "Added waste of 25 units of Guinness"
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
