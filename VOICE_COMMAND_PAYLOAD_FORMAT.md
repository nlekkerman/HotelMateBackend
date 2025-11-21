# 🎤 Voice Command API - Payload Format Reference

**Last Updated:** November 21, 2025  
**Status:** ✅ Production Ready

---

## Overview

This document defines the exact payload format for voice command parsing and confirmation endpoints.

---

## 1. Parse Voice Command (Preview)

**Endpoint:** `POST /api/stock_tracker/{hotel}/stocktake-lines/voice-command/`

### Request

```http
POST /api/stock_tracker/dublin/stocktake-lines/voice-command/
Content-Type: multipart/form-data
Authorization: Bearer {token}

audio=<WebM audio blob>
stocktake_id=123
```

### Response - Success with Full+Partial Units

```json
{
  "success": true,
  "command": {
    "action": "count",
    "item_identifier": "budweiser",
    "value": 5,
    "full_units": 3,
    "partial_units": 5,
    "transcription": "counted, Budweiser bottle, 3 cases, 5 bottles"
  },
  "stocktake_id": 123
}
```

**Field Descriptions:**
- `action` (string): One of: `"count"`, `"purchase"`, `"waste"`
- `item_identifier` (string): Product name or SKU extracted from speech
- `value` (number): 
  - For COUNT with full+partial: Set to `partial_units` value (for backwards compatibility)
  - For single value commands: The quantity
- `full_units` (number|null): Main containers (cases, kegs, bottles, dozen)
- `partial_units` (number|null): Loose units (bottles, pints, fractional)
- `transcription` (string): Original text from speech-to-text

### Response - Success with Single Value

```json
{
  "success": true,
  "command": {
    "action": "purchase",
    "item_identifier": "heineken",
    "value": 7,
    "transcription": "purchase heineken 7"
  },
  "stocktake_id": 123
}
```

**Note:** When `full_units` and `partial_units` are not present, they are **omitted** from the response (not null).

### Response - Error

```json
{
  "success": false,
  "error": "No action keyword found in 'xyz'",
  "transcription": "xyz"
}
```

---

## 2. Confirm Voice Command (Apply)

**Endpoint:** `POST /api/stock_tracker/{hotel}/stocktake-lines/voice-command/confirm/`

### Request - COUNT with Full+Partial

```json
{
  "stocktake_id": 123,
  "command": {
    "action": "count",
    "item_identifier": "budweiser",
    "value": 5,
    "full_units": 3,
    "partial_units": 5,
    "transcription": "counted, Budweiser bottle, 3 cases, 5 bottles"
  }
}
```

### Request - COUNT with Single Value

```json
{
  "stocktake_id": 123,
  "command": {
    "action": "count",
    "item_identifier": "heineken",
    "value": 42,
    "transcription": "count heineken 42"
  }
}
```

### Request - PURCHASE

```json
{
  "stocktake_id": 123,
  "command": {
    "action": "purchase",
    "item_identifier": "guinness",
    "value": 2,
    "transcription": "purchase 2 kegs of guinness"
  }
}
```

### Response - Success (COUNT)

```json
{
  "success": true,
  "line": {
    "id": 456,
    "item_sku": "B0070",
    "item_name": "Budweiser Bottle",
    "category_code": "B",
    "item_uom": 12,
    "counted_full_units": 3,
    "counted_partial_units": 5,
    "counted_qty": 41,
    "expected_qty": 50,
    "variance_qty": -9,
    "opening_qty": 40,
    "purchases": 10,
    "waste": 0,
    "counted_value": 45.10,
    "expected_value": 55.00,
    "variance_value": -9.90,
    "input_fields": {
      "full": {"name": "counted_full_units", "label": "Cases"},
      "partial": {"name": "counted_partial_units", "label": "Bottles", "max": 11}
    }
  },
  "message": "Counted 3 and 5 of Budweiser Bottle",
  "item_name": "Budweiser Bottle",
  "item_sku": "B0070"
}
```

### Response - Success (PURCHASE)

```json
{
  "success": true,
  "line": {
    "id": 789,
    "item_sku": "D-GUIN-KEG",
    "item_name": "Guinness",
    "purchases": 176,
    ...
  },
  "message": "Added purchase of 2 kegs (176 pints) of Guinness",
  "item_name": "Guinness",
  "item_sku": "D-GUIN-KEG"
}
```

### Response - Validation Error

```json
{
  "success": false,
  "error": "Purchases must be in full kegs only. Partial kegs should be recorded as waste."
}
```

---

## 3. Field Presence Rules

### COUNT Command

| Scenario | `value` | `full_units` | `partial_units` |
|----------|---------|--------------|-----------------|
| **"count budweiser 3 cases 5 bottles"** | `5` (partial) | `3` | `5` |
| **"count heineken 42"** | `42` | ❌ omitted | ❌ omitted |
| **"count guinness 3 dozen"** | `36` | `3` (dozen) | `0` |

### PURCHASE Command

| Scenario | `value` | `full_units` | `partial_units` |
|----------|---------|--------------|-----------------|
| **"purchase 5 cases budweiser"** | `5` | ❌ omitted | ❌ omitted |
| **"purchase 2 kegs guinness"** | `2` | ❌ omitted | ❌ omitted |

**Note:** PURCHASE commands with full+partial units are **rejected** by the parser:
```json
{
  "success": false,
  "error": "Purchase command cannot have partial units. Use 'purchase 3' for full units only. Partial units should be recorded as waste."
}
```

### WASTE Command

| Scenario | `value` | `full_units` | `partial_units` |
|----------|---------|--------------|-----------------|
| **"waste 25 pints guinness"** | `25` | ❌ omitted | ❌ omitted |
| **"waste 7 bottles budweiser"** | `7` | ❌ omitted | ❌ omitted |
| **"waste 0.5 bottle vodka"** | `0.5` | ❌ omitted | ❌ omitted |

---

## 4. Frontend Integration Guide

### Detecting Full+Partial vs Single Value

```typescript
function isFullPartialCommand(command) {
  return (
    command.full_units !== undefined && 
    command.full_units !== null &&
    command.partial_units !== undefined &&
    command.partial_units !== null
  );
}
```

### Calculating Total Servings

```typescript
function calculateTotalServings(command, item) {
  if (isFullPartialCommand(command)) {
    // COUNT with cases+bottles or kegs+pints
    const uom = item.item_uom; // e.g., 12 for beer cases, 88 for kegs
    return (command.full_units * uom) + command.partial_units;
  } else {
    // Single value command
    return command.value;
  }
}
```

### Example Usage

```typescript
const VoiceCommandPreview = ({ command, stocktake }) => {
  const [matchedItem, setMatchedItem] = useState(null);
  const [total, setTotal] = useState(null);

  useEffect(() => {
    // Find matching item
    const item = findItemInStocktake(command.item_identifier, stocktake);
    setMatchedItem(item);

    // Calculate total if full+partial
    if (item && isFullPartialCommand(command)) {
      setTotal(calculateTotalServings(command, item));
    } else {
      setTotal(command.value);
    }
  }, [command, stocktake]);

  return (
    <div>
      <h3>Confirm Voice Command</h3>
      
      <p><strong>Action:</strong> {command.action}</p>
      <p><strong>Product:</strong> {matchedItem?.item_name || command.item_identifier}</p>
      
      {isFullPartialCommand(command) ? (
        <>
          <p><strong>Cases:</strong> {command.full_units}</p>
          <p><strong>Bottles:</strong> {command.partial_units}</p>
          {total !== null && <p><strong>Total:</strong> {total}</p>}
        </>
      ) : (
        <p><strong>Quantity:</strong> {command.value}</p>
      )}
      
      <p><em>You said: "{command.transcription}"</em></p>
      
      <button onClick={() => confirmCommand(command)}>Confirm</button>
    </div>
  );
};
```

---

## 5. Common Scenarios

### Scenario 1: Bottled Beer with Cases + Bottles

**Input:** "counted budweiser 3 cases 5 bottles"

**Parse Response:**
```json
{
  "action": "count",
  "item_identifier": "budweiser",
  "value": 5,
  "full_units": 3,
  "partial_units": 5
}
```

**Frontend Calculation:**
```javascript
uom = 12 (bottles per case)
total = (3 × 12) + 5 = 41 bottles
```

**Backend Saves:**
```python
counted_full_units = 3
counted_partial_units = 5
counted_qty = 41  # Calculated by model property
```

### Scenario 2: Draft Beer with Kegs + Pints

**Input:** "count guinness 2 kegs 15 pints"

**Parse Response:**
```json
{
  "action": "count",
  "item_identifier": "guinness",
  "value": 15,
  "full_units": 2,
  "partial_units": 15
}
```

**Frontend Calculation:**
```javascript
uom = 88 (pints per keg)
total = (2 × 88) + 15 = 191 pints
```

**Backend Saves:**
```python
counted_full_units = 2
counted_partial_units = 15
counted_qty = 191
```

### Scenario 3: Simple Count

**Input:** "count heineken 42"

**Parse Response:**
```json
{
  "action": "count",
  "item_identifier": "heineken",
  "value": 42
}
```

**Frontend Display:**
```
Quantity: 42
```

**Backend Saves:**
```python
counted_full_units = 42
counted_partial_units = 0
counted_qty = 42
```

### Scenario 4: Purchase (Full Units Only)

**Input:** "purchase 5 cases budweiser"

**Parse Response:**
```json
{
  "action": "purchase",
  "item_identifier": "budweiser",
  "value": 5
}
```

**Backend Validation & Conversion:**
```python
# Validates: 5 % 1 == 0 ✓ (whole number)
# Converts: 5 × 12 = 60 bottles
# Creates: StockMovement(quantity=60)
```

**Response:**
```json
{
  "message": "Added purchase of 5 cases (60 bottles) of Budweiser"
}
```

---

## 6. Error Responses

### Item Not Found

```json
{
  "success": false,
  "error": "Stock item not found: budwiser"
}
```

### Invalid Purchase (Partial Units)

```json
{
  "success": false,
  "error": "Purchases must be in full cases only. Partial cases should be recorded as waste."
}
```

### Invalid Waste (Full Units)

```json
{
  "success": false,
  "error": "Waste must be partial case only (less than 12 bottles). Full cases should be recorded as negative adjustments."
}
```

### Stocktake Locked

```json
{
  "success": false,
  "error": "Stocktake is locked (approved)"
}
```

---

## 7. Backend Implementation Notes

### Parser Logic (`command_parser.py`)

1. Detects action keywords (`count`, `purchase`, `waste`)
2. Extracts numeric values (handles "3 cases 5 bottles" pattern)
3. Validates PURCHASE cannot have partial units
4. Returns structured command with `full_units` and `partial_units` when detected
5. Sets `value` to `partial_units` for backwards compatibility

### Confirm Logic (`views.py`)

1. Fuzzy matches `item_identifier` to find `StockItem`
2. Gets or creates `StocktakeLine`
3. For COUNT: Sets `counted_full_units` and `counted_partial_units` directly
4. For PURCHASE/WASTE: Validates and creates `StockMovement` records
5. Returns full serialized line data with all calculated fields

### Model Properties

The `StocktakeLine` model has a `counted_qty` property that automatically calculates:
```python
@property
def counted_qty(self):
    if self.item.uom == Decimal('1'):
        # UOM=1: bottles/boxes (no conversion)
        return self.counted_full_units + self.counted_partial_units
    else:
        # UOM>1: cases/kegs (convert to servings)
        return (self.counted_full_units * self.item.uom) + self.counted_partial_units
```

---

## Summary

| Field | Purpose | When Present |
|-------|---------|--------------|
| `value` | Single quantity OR backwards compat display | Always |
| `full_units` | Main containers (cases/kegs/dozen) | COUNT with breakdown |
| `partial_units` | Loose units (bottles/pints) | COUNT with breakdown |
| `transcription` | Original speech text | Always |

**Key Rule:** If `full_units` and `partial_units` are present, use them for display and calculation. Otherwise, use `value`.

---

## Related Files

- **Parser:** `voice_recognition/command_parser.py`
- **Views:** `voice_recognition/views.py`
- **Bug Fix Doc:** `VOICE_COUNT_DISPLAY_FIX.md`
- **Frontend Guide:** `VOICE_RECOGNITION_FRONTEND_GUIDE.md`
- **Beer Guide:** `VOICE_BEER_FRONTEND_GUIDE.md`

---

**Last Updated:** November 21, 2025
