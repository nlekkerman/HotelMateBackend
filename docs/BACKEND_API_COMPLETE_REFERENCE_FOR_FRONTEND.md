# 🎯 BACKEND API COMPLETE REFERENCE FOR FRONTEND TEAM

**Date:** November 12, 2025  
**Purpose:** Complete documentation of what the backend calculates and sends to frontend  
**Rule:** Frontend should ONLY display values - NO CALCULATIONS!

---

## 📋 TABLE OF CONTENTS
1. [Key Concept: Backend Does ALL Math](#key-concept)
2. [StocktakeLine Model Properties](#model-properties)
3. [StocktakeLine Serializer Fields](#serializer-fields)
4. [API Endpoints](#api-endpoints)
5. [Pusher Real-Time Events](#pusher-events)
6. [Complete API Response Example](#response-example)
7. [Frontend Display Guidelines](#frontend-guidelines)

---

## 🔑 KEY CONCEPT: BACKEND DOES ALL MATH {#key-concept}

### ✅ WHAT BACKEND CALCULATES (Read-Only for Frontend):

```javascript
// Opening, Expected, Counted, Variance - ALL calculated by backend
opening_qty           // Opening stock in servings
expected_qty          // Opening + Purchases - Waste
counted_qty           // (counted_full_units × UOM) + counted_partial_units
variance_qty          // counted_qty - expected_qty

// Values - ALL calculated by backend
expected_value        // expected_qty × valuation_cost
counted_value         // counted_qty × valuation_cost
variance_value        // counted_value - expected_value

// Display units - ALL calculated by backend
opening_display_full_units       // "0" kegs/cases/bottles
opening_display_partial_units    // "12" pints/bottles/shots
expected_display_full_units      // Converted from expected_qty
expected_display_partial_units   // With category-specific rounding
counted_display_full_units       // Converted from counted_qty
counted_display_partial_units    // With category-specific rounding
variance_display_full_units      // Converted from variance_qty
variance_display_partial_units   // With category-specific rounding
```

### ❌ WHAT FRONTEND SENDS (User Input Only):

```javascript
// Only 2 fields - what the user physically counted
{
  "counted_full_units": 2,      // User entered: 2 kegs/cases/bottles
  "counted_partial_units": 15.5  // User entered: 15.5 pints/bottles/shots
}
```

### 🔄 THE FLOW:

```
1. User enters counted values → Frontend sends to backend
2. Backend calculates EVERYTHING → Saves to database
3. Backend broadcasts via Pusher → All clients get updated data
4. Frontend receives Pusher event → Updates display with backend values
```

---

## 🧮 STOCKTAKELINE MODEL PROPERTIES {#model-properties}

### Database Fields (Stored in DB):

```python
# User identifies the item
stocktake              # FK to Stocktake
item                   # FK to StockItem

# Opening balances (frozen when stocktake created)
opening_qty            # Decimal(15,4) - Opening stock in servings

# Period movements (from StockMovement records)
purchases              # Decimal(15,4) - Total purchases in servings
waste                  # Decimal(15,4) - Total waste in servings
transfers_in           # Decimal(15,4) - Stock transferred in
transfers_out          # Decimal(15,4) - Stock transferred out
adjustments            # Decimal(15,4) - Manual adjustments

# Manual override fields (optional - for Excel imports)
manual_purchases_value # Decimal(15,2) - Override purchase total (€)
manual_waste_value     # Decimal(15,2) - Override waste total (€)
manual_sales_value     # Decimal(15,2) - Override sales total (€)

# User counted values (INPUT FIELDS - what staff physically count)
counted_full_units     # Decimal(10,2) - Cases/Kegs/Bottles
counted_partial_units  # Decimal(10,2) - Bottles/Pints/Shots

# Valuation (frozen cost at stocktake creation)
valuation_cost         # Decimal(10,4) - Cost per serving for this period
```

### Calculated Properties (NOT in DB - calculated on-the-fly):

```python
@property
def counted_qty(self):
    """
    Convert user input to total servings.
    
    Logic differs by category:
    - Draught (D) + Dozen (Doz): partial already in servings
      Formula: (full × UOM) + partial
      Example: (2 kegs × 88 pints) + 15.5 pints = 191.5 servings
    
    - Spirits/Wine/Other: partial is fractional
      Formula: (full × UOM) + (partial × UOM)
      Example: (1 bottle × 20 shots) + (0.5 bottle × 20) = 30 shots
    """
    if category in ['D', 'Dozen items']:
        return (counted_full_units × uom) + counted_partial_units
    else:
        return (counted_full_units × uom) + (counted_partial_units × uom)

@property
def expected_qty(self):
    """
    ⚠️ CRITICAL FORMULA - This is what SHOULD be in stock.
    
    Formula: expected = opening + purchases - waste
    
    NOTE: Sales are NOT included here!
    Sales are tracked separately for profit calculations.
    """
    return opening_qty + purchases - waste

@property
def variance_qty(self):
    """
    Difference between what we counted and what we expected.
    
    Positive = Surplus (found more than expected)
    Negative = Shortage (missing stock)
    """
    return counted_qty - expected_qty

@property
def expected_value(self):
    """Expected stock value at frozen cost"""
    return expected_qty × valuation_cost

@property
def counted_value(self):
    """Actual counted stock value at frozen cost"""
    return counted_qty × valuation_cost

@property
def variance_value(self):
    """Variance in euros"""
    return counted_value - expected_value
```

---

## 📦 STOCKTAKELINE SERIALIZER FIELDS {#serializer-fields}

### What Frontend Receives in API Response:

```python
{
  # ============= IDENTIFICATION =============
  "id": 123,
  "stocktake": 16,
  "item": 45,
  "item_sku": "B0012",
  "item_name": "Cronins 0.0%",
  "category_code": "B",
  "category_name": "Bottled Beer",
  "item_size": "Doz",
  "item_uom": "12.00",
  
  # ============= RAW QUANTITIES (Servings) =============
  "opening_qty": "0.0000",
  "purchases": "12.4300",
  "waste": "1.0000",
  "transfers_in": "0.0000",
  "transfers_out": "0.0000",
  "adjustments": "0.0000",
  
  # ============= MANUAL OVERRIDES (Optional) =============
  "manual_purchases_value": null,
  "manual_waste_value": null,
  "manual_sales_value": null,
  
  # ============= USER INPUT FIELDS =============
  "counted_full_units": "0.00",    # ✏️ ONLY field user edits
  "counted_partial_units": "0.00", # ✏️ ONLY field user edits
  
  # ============= CALCULATED QUANTITIES (Backend) =============
  "counted_qty": "0.0000",         # ✅ Backend calculates
  "expected_qty": "11.4300",       # ✅ Backend calculates
  "variance_qty": "-11.4300",      # ✅ Backend calculates
  
  # ============= DISPLAY UNITS (Backend Converts) =============
  "opening_display_full_units": "0",      # ✅ Backend converts
  "opening_display_partial_units": "0",   # ✅ Backend converts
  "expected_display_full_units": "0",     # ✅ Backend converts
  "expected_display_partial_units": "11", # ✅ Backend converts (rounded)
  "counted_display_full_units": "0",      # ✅ Backend converts
  "counted_display_partial_units": "0",   # ✅ Backend converts
  "variance_display_full_units": "0",     # ✅ Backend converts
  "variance_display_partial_units": "-11",# ✅ Backend converts
  
  # ============= VALUES (Backend Calculates) =============
  "valuation_cost": "1.2300",           # Frozen cost per serving
  "expected_value": "13.53",            # ✅ Backend calculates
  "counted_value": "0.00",              # ✅ Backend calculates
  "variance_value": "-13.53",           # ✅ Backend calculates
}
```

---

## 🔧 BACKEND HELPER METHOD: `_calculate_display_units()` {#helper-method}

### How Backend Converts Servings to Display Units:

```python
def _calculate_display_units(servings, item):
    """
    Convert base servings to full + partial units.
    Applies category-specific rounding rules.
    
    Args:
        servings: Decimal - Total quantity in servings
        item: StockItem - Contains category, size, uom
    
    Returns:
        (full_units_string, partial_units_string)
    """
    from decimal import Decimal, ROUND_HALF_UP
    
    servings_decimal = Decimal(str(servings))
    uom = Decimal(str(item.uom))
    
    # Calculate full and partial
    full = int(servings_decimal / uom)
    partial = servings_decimal % uom
    
    # Apply category-specific rounding
    category = item.category.code
    size = item.size or ''
    
    if category == 'B' or (category == 'M' and 'Doz' in size):
        # Bottled Beer + Dozen Minerals: whole numbers only
        # Example: 11.43 bottles → "11" (not "11.43")
        partial_display = str(int(round(float(partial))))
        
    elif category == 'D':
        # Draught: pints with 2 decimals
        # Example: 15.678 pints → "15.68"
        partial_rounded = partial.quantize(
            Decimal('0.01'), 
            rounding=ROUND_HALF_UP
        )
        partial_display = str(partial_rounded)
        
    else:
        # Spirits, Wine, Other: 2 decimals
        # Example: 0.567 bottles → "0.57"
        partial_rounded = partial.quantize(
            Decimal('0.01'), 
            rounding=ROUND_HALF_UP
        )
        partial_display = str(partial_rounded)
    
    return str(full), partial_display
```

### Examples of Display Conversion:

```javascript
// Example 1: Bottled Beer (B0012 - UOM=12)
servings = 11.43
→ full = 0 cases
→ partial = 11.43 bottles → "11" (rounded to whole number)
Display: "0 cases, 11 bottles"

// Example 2: Draught Beer (D0005 - UOM=88)
servings = 191.567
→ full = 2 kegs
→ partial = 15.567 pints → "15.57" (2 decimals)
Display: "2 kegs, 15.57 pints"

// Example 3: Spirits (S0001 - UOM=20)
servings = 30.678
→ full = 1 bottle
→ partial = 10.678 shots → "10.68" (2 decimals)
Display: "1 bottle, 10.68 shots"

// Example 4: Wine (W0001 - UOM=1)
servings = 2.567
→ full = 2 bottles
→ partial = 0.567 bottles → "0.57" (2 decimals)
Display: "2 bottles, 0.57 bottles"
```

---

## 🌐 API ENDPOINTS {#api-endpoints}

### 1. GET Stocktake with All Lines

```http
GET /api/stock_tracker/{hotel_slug}/stocktakes/{stocktake_id}/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": 16,
  "hotel": 1,
  "period_start": "2025-11-01",
  "period_end": "2025-11-30",
  "status": "IN_PROGRESS",
  "is_locked": false,
  "lines": [
    {
      "id": 123,
      "item_sku": "B0012",
      "item_name": "Cronins 0.0%",
      "opening_qty": "0.0000",
      "purchases": "12.4300",
      "waste": "1.0000",
      "expected_qty": "11.4300",
      "counted_full_units": "0.00",
      "counted_partial_units": "0.00",
      "counted_qty": "0.0000",
      "variance_qty": "-11.4300",
      "expected_value": "13.53",
      "counted_value": "0.00",
      "variance_value": "-13.53",
      "opening_display_full_units": "0",
      "opening_display_partial_units": "0",
      "expected_display_full_units": "0",
      "expected_display_partial_units": "11"
    }
    // ... 253 more lines
  ],
  "total_lines": 254
}
```

---

### 2. PATCH Update Counted Values (User Input)

```http
PATCH /api/stock_tracker/{hotel_slug}/stocktake-lines/{line_id}/
Authorization: Bearer {token}
Content-Type: application/json

{
  "counted_full_units": 2,
  "counted_partial_units": 15.5
}
```

**What Backend Does:**
1. Validates input (must be >= 0, correct decimal places)
2. Saves `counted_full_units` and `counted_partial_units`
3. Calculates `counted_qty` using formula
4. Calculates `variance_qty = counted_qty - expected_qty`
5. Calculates all values (`counted_value`, `variance_value`)
6. Converts to display units using `_calculate_display_units()`
7. Broadcasts update via Pusher to all connected clients
8. Returns complete updated line with ALL calculated fields

**Response:** (Same structure as GET, with updated values)
```json
{
  "id": 123,
  "counted_full_units": "2.00",
  "counted_partial_units": "15.50",
  "counted_qty": "191.5000",      // Backend calculated
  "variance_qty": "180.0700",      // Backend calculated
  "counted_value": "235.55",       // Backend calculated
  "variance_value": "221.48",      // Backend calculated
  "counted_display_full_units": "2",
  "counted_display_partial_units": "15.50",
  "variance_display_full_units": "2",
  "variance_display_partial_units": "4.07"
}
```

---

### 3. POST Add Movement (Purchase/Waste)

```http
POST /api/stock_tracker/{hotel_slug}/stocktake-lines/{line_id}/add_movement/
Authorization: Bearer {token}
Content-Type: application/json

{
  "movement_type": "PURCHASE",  // or "WASTE"
  "quantity": 12.43,             // in servings
  "notes": "Added via stocktake"
}
```

**What Backend Does:**
1. Creates `StockMovement` record
2. Recalculates `purchases` or `waste` from all movements
3. Recalculates `expected_qty = opening + purchases - waste`
4. Recalculates variance and all values
5. Broadcasts update via Pusher
6. Returns updated line

**Response:** Complete updated line with new expected_qty

---

### 4. GET Category Totals

```http
GET /api/stock_tracker/{hotel_slug}/stocktakes/{stocktake_id}/category_totals/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "B": {
    "item_count": 21,
    "opening_qty": "173.66",
    "purchases": "0.00",
    "sales_qty": "0.00",
    "waste": "0.00",
    "expected_qty": "173.66",
    "counted_qty": "0.00",
    "variance_qty": "-173.66",
    "expected_value": "244.03",
    "counted_value": "0.00",
    "variance_value": "-244.03"
  },
  "D": {
    "item_count": 14,
    // ... same structure
  },
  "M": { /* ... */ },
  "S": { /* ... */ },
  "W": { /* ... */ }
}
```

**Optional filter:**
```http
GET /api/stock_tracker/{hotel_slug}/stocktakes/{stocktake_id}/category_totals/?category=B
```

---

### 5. GET Movement History

```http
GET /api/stock_tracker/{hotel_slug}/stocktake-lines/{line_id}/movements/
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "id": 567,
    "movement_type": "PURCHASE",
    "quantity": "12.4300",
    "unit_cost": "1.23",
    "total_cost": "15.29",
    "timestamp": "2025-11-05T14:30:00Z",
    "reference": "INV-12345",
    "notes": "Added via stocktake"
  },
  {
    "id": 568,
    "movement_type": "WASTE",
    "quantity": "1.0000"
  }
]
```

---

## 🔴 PUSHER REAL-TIME EVENTS {#pusher-events}

### Event: `line-counted-updated`

**Channel:** `private-hotel-{hotel_id}-stocktake-{stocktake_id}`

**When Triggered:**
- User updates counted values (PATCH request)
- Movement added (POST add_movement)
- Any change to StocktakeLine

**Payload:**
```json
{
  "line_id": 123,
  "item_sku": "B0012",
  "line": {
    // Complete StocktakeLineSerializer data
    "id": 123,
    "item_sku": "B0012",
    "counted_full_units": "2.00",
    "counted_partial_units": "15.50",
    "counted_qty": "191.5000",
    "expected_qty": "11.4300",
    "variance_qty": "180.0700",
    "expected_value": "13.53",
    "counted_value": "235.55",
    "variance_value": "221.48",
    // ... all fields with latest calculated values
  }
}
```

**Frontend Handler:**
```javascript
// Subscribe to stocktake channel
const channel = pusher.subscribe(`private-hotel-${hotelId}-stocktake-${stocktakeId}`);

// Listen for line updates
channel.bind('line-counted-updated', (data) => {
  // Update the line in state with ALL backend-calculated values
  updateLineInState(data.line_id, data.line);
  
  // Refresh category totals if needed
  refreshCategoryTotals();
  
  // NO CALCULATIONS - just display what backend sent!
});
```

---

## 📊 COMPLETE API RESPONSE EXAMPLE {#response-example}

### Example: Bottled Beer Item After User Counts

**Initial State (before counting):**
```json
{
  "id": 123,
  "stocktake": 16,
  "item": 45,
  "item_sku": "B0012",
  "item_name": "Cronins 0.0%",
  "category_code": "B",
  "category_name": "Bottled Beer",
  "item_size": "Doz",
  "item_uom": "12.00",
  
  "opening_qty": "0.0000",
  "purchases": "12.4300",
  "waste": "1.0000",
  
  "counted_full_units": "0.00",
  "counted_partial_units": "0.00",
  
  "expected_qty": "11.4300",
  "counted_qty": "0.0000",
  "variance_qty": "-11.4300",
  
  "opening_display_full_units": "0",
  "opening_display_partial_units": "0",
  "expected_display_full_units": "0",
  "expected_display_partial_units": "11",
  "counted_display_full_units": "0",
  "counted_display_partial_units": "0",
  "variance_display_full_units": "0",
  "variance_display_partial_units": "-11",
  
  "valuation_cost": "1.2300",
  "expected_value": "13.53",
  "counted_value": "0.00",
  "variance_value": "-13.53"
}
```

**User Action:** Counts 1 case and 2 bottles
```javascript
// Frontend sends:
{
  "counted_full_units": 1,
  "counted_partial_units": 2
}
```

**After Update (backend response):**
```json
{
  "id": 123,
  // ... same identification fields ...
  
  "opening_qty": "0.0000",
  "purchases": "12.4300",
  "waste": "1.0000",
  
  "counted_full_units": "1.00",      // ✏️ User input
  "counted_partial_units": "2.00",   // ✏️ User input
  
  "expected_qty": "11.4300",         // Still same (opening + purchases - waste)
  "counted_qty": "14.0000",          // ✅ Backend: (1 × 12) + 2 = 14
  "variance_qty": "2.5700",          // ✅ Backend: 14 - 11.43 = 2.57
  
  "expected_display_full_units": "0",
  "expected_display_partial_units": "11",
  "counted_display_full_units": "1",
  "counted_display_partial_units": "2",
  "variance_display_full_units": "0",
  "variance_display_partial_units": "3",  // ✅ Backend: 2.57 → "3" (rounded)
  
  "valuation_cost": "1.2300",
  "expected_value": "13.53",
  "counted_value": "17.22",          // ✅ Backend: 14 × 1.23
  "variance_value": "3.69"           // ✅ Backend: 17.22 - 13.53
}
```

---

## 🎨 FRONTEND DISPLAY GUIDELINES {#frontend-guidelines}

### ❌ WHAT FRONTEND SHOULD NOT DO:

```javascript
// ❌ DON'T calculate expected
const expected = line.opening_qty + line.purchases - line.waste;

// ❌ DON'T calculate counted
const counted = (line.counted_full_units * line.uom) + line.counted_partial_units;

// ❌ DON'T calculate variance
const variance = counted - expected;

// ❌ DON'T convert to display units
const fullUnits = Math.floor(servings / uom);
const partialUnits = servings % uom;

// ❌ DON'T use optimistic updates
function optimisticUpdateCount(lineId, newValues) {
  // Calculating locally creates inconsistency!
}
```

### ✅ WHAT FRONTEND SHOULD DO:

```javascript
// ✅ Display backend values directly
<div>
  <span>Expected: {line.expected_display_full_units} cases, {line.expected_display_partial_units} bottles</span>
  <span>Value: €{line.expected_value}</span>
</div>

// ✅ Send user input and wait for backend
async function handleCountUpdate(lineId, fullUnits, partialUnits) {
  // 1. Send to backend
  const response = await api.patch(`/stocktake-lines/${lineId}/`, {
    counted_full_units: fullUnits,
    counted_partial_units: partialUnits
  });
  
  // 2. Update state with backend response (has ALL calculated fields)
  updateLine(response.data);
  
  // 3. Pusher will also broadcast to other users
  // No need to calculate anything!
}

// ✅ Listen to Pusher for real-time updates
pusherChannel.bind('line-counted-updated', (data) => {
  // Backend already calculated everything
  updateLine(data.line);
  
  // Just display the values!
});

// ✅ Display variance with colors based on backend values
function getVarianceColor(line) {
  if (line.variance_value > 0) return 'green';  // Surplus
  if (line.variance_value < 0) return 'red';    // Shortage
  return 'grey';                                 // Balanced
}

// ✅ Show warnings based on backend values
function showWarning(line) {
  return Math.abs(line.variance_value) > 10;  // Backend value
}
```

### Input Validation (Frontend Only Validates User Entry):

```javascript
// ✅ Frontend validates user input before sending
function validatePartialUnits(value, line) {
  const uom = parseFloat(line.item_uom);
  const category = line.category_code;
  const size = line.item_size || '';
  
  // Bottled Beer + Dozen Minerals: whole numbers only
  if (category === 'B' || (category === 'M' && size.includes('Doz'))) {
    if (!Number.isInteger(value)) {
      return 'Must be a whole number';
    }
    if (value < 0 || value >= uom) {
      return `Must be between 0 and ${uom - 1}`;
    }
  }
  
  // Draught, Spirits, Wine: max 2 decimals
  else {
    if (!/^\d+(\.\d{0,2})?$/.test(value.toString())) {
      return 'Max 2 decimal places';
    }
    if (value < 0 || value >= uom) {
      return `Must be between 0.00 and ${(uom - 0.01).toFixed(2)}`;
    }
  }
  
  return null; // Valid
}
```

---

## 🎯 SUMMARY: BACKEND vs FRONTEND RESPONSIBILITIES

| Task | Backend | Frontend |
|------|---------|----------|
| Calculate expected_qty | ✅ Yes | ❌ No |
| Calculate counted_qty | ✅ Yes | ❌ No |
| Calculate variance | ✅ Yes | ❌ No |
| Convert to display units | ✅ Yes | ❌ No |
| Apply rounding rules | ✅ Yes | ❌ No |
| Calculate values (€) | ✅ Yes | ❌ No |
| Validate user input format | ❌ No | ✅ Yes |
| Display values | ❌ No | ✅ Yes |
| Send user counts to API | ❌ No | ✅ Yes |
| Listen to Pusher events | ❌ No | ✅ Yes |
| Update UI on changes | ❌ No | ✅ Yes |

---

## 📞 CONTACT & SUPPORT

**Backend Developer:** [Your Name]  
**API Base URL:** `https://api.hotelmate.com/api/stock_tracker/`  
**Pusher Channel Pattern:** `private-hotel-{hotel_id}-stocktake-{stocktake_id}`  
**Documentation Version:** 1.0  
**Last Updated:** November 12, 2025

---

## ⚠️ CRITICAL REMINDERS

1. **Never calculate on frontend** - Backend has the single source of truth
2. **Never use optimistic updates** - Wait for Pusher to confirm changes
3. **All numeric fields are strings in API** - Use `parseFloat()` for display only
4. **Backend handles all rounding** - Display fields come pre-rounded
5. **Pusher ensures real-time sync** - All users see changes instantly
6. **Validation happens twice** - Frontend validates input format, Backend validates business rules

---

**END OF DOCUMENTATION**
