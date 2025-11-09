# Frontend Stocktake Calculations Guide

## Overview

This guide explains how the frontend should perform stocktake calculations to match the backend exactly.

---

## Data Structure

### StocktakeLine Fields

Each line in a stocktake contains:

```javascript
{
  id: 123,
  item: { sku: "SKU001", name: "Guinness Keg", uom: 88 },
  
  // Opening stock (frozen at stocktake creation)
  opening_qty: "88.0000",  // in base units (servings)
  
  // Period movements (auto-calculated from StockMovement records)
  purchases: "176.0000",   // total purchases in period
  waste: "5.0000",         // total waste in period
  
  // Counted stock (user input)
  counted_full_units: "2",      // e.g., 2 kegs
  counted_partial_units: "45.50", // e.g., 45.5 pints
  
  // Valuation
  valuation_cost: "2.5000"  // cost per serving (€)
}
```

---

## Core Calculations

### 1. Counted Quantity (Base Units)

Convert counted full/partial units to base units (servings):

```javascript
function calculateCountedQty(line) {
  const fullUnits = parseFloat(line.counted_full_units) || 0;
  const partialUnits = parseFloat(line.counted_partial_units) || 0;
  const uom = parseFloat(line.item.uom) || 1;
  
  // counted_qty = (full_units × uom) + partial_units
  return (fullUnits * uom) + partialUnits;
}

// Example: 2 kegs + 45.5 pints
// = (2 × 88) + 45.5 = 221.5 pints
```

### 2. Expected Quantity

**CRITICAL**: This is the formula the backend uses. Frontend MUST match exactly.

```javascript
function calculateExpectedQty(line) {
  const opening = parseFloat(line.opening_qty) || 0;
  const purchases = parseFloat(line.purchases) || 0;
  const waste = parseFloat(line.waste) || 0;
  
  // Expected = Opening + Purchases - Waste
  // NOTE: Sales are NOT included - calculated separately outside stocktake
  return opening + purchases - waste;
}

// Example:
// Opening: 88 pints
// Purchases: 176 pints (2 kegs delivered)
// Waste: 5 pints (spillage)
// Expected = 88 + 176 - 5 = 259 pints
```

**Important Notes**:
- ✅ All values are in **base units** (servings: pints, shots, bottles)
- ✅ Backend returns strings, so use `parseFloat()` 
- ✅ For hotel-wide system: no transfers, no adjustments needed
- ✅ **Sales are NOT in this formula** - sales calculated separately from stocktake variance

### 3. Variance

Variance shows the difference between physical count and expected:

```javascript
function calculateVariance(line) {
  const counted = calculateCountedQty(line);
  const expected = calculateExpectedQty(line);
  
  // Positive = Surplus, Negative = Shortage
  return counted - expected;
}

// Example:
// Counted: 221.5 pints
// Expected: 259 pints
// Variance: 221.5 - 259 = -37.5 pints (shortage)
```

### 4. Value Calculations

```javascript
function calculateValues(line) {
  const counted = calculateCountedQty(line);
  const expected = calculateExpectedQty(line);
  const cost = parseFloat(line.valuation_cost) || 0;
  
  return {
    expectedValue: expected * cost,
    countedValue: counted * cost,
    varianceValue: (counted - expected) * cost
  };
}

// Example (cost per pint = €2.50):
// Expected Value: 259 × 2.50 = €647.50
// Counted Value: 221.5 × 2.50 = €553.75
// Variance Value: -37.5 × 2.50 = -€93.75
```

---

## Display Units Conversion & Decimal Rules by Category

**CRITICAL**: Different categories have different decimal precision rules for user input!

### Category-Specific Decimal Rules:

| Category | Code | Full Units | Partial Units | Max Decimals |
|----------|------|------------|---------------|--------------|
| **Draught** | D | Kegs (whole) | Pints | **2 decimals** |
| **Bottled Beer** | B | Cases (whole) | Bottles | **0 decimals (whole numbers)** |
| **Spirits** | S | Bottles (whole) | Fractional | **2 decimals** |
| **Wine** | W | Bottles (whole) | Fractional | **2 decimals** |
| **Minerals** | M | Cases/Units (whole) | Bottles/Servings | **0 decimals if Doz, 2 otherwise** |

### Frontend Validation Rules:

```javascript
function validatePartialUnits(value, category, itemSize) {
  // Category B (Bottled Beer) - whole numbers only
  if (category === 'B') {
    return Math.round(value);  // No decimals allowed
  }
  
  // Category M (Minerals) - check if dozen packaging
  if (category === 'M' && itemSize?.includes('Doz')) {
    return Math.round(value);  // No decimals for dozen items
  }
  
  // Category D (Draught), S (Spirits), W (Wine) - max 2 decimals
  return parseFloat(value.toFixed(2));
}
```

### Input Field Configuration:

```javascript
// Configure input fields based on category
function getInputConfig(item) {
  const category = item.category?.code;
  
  if (category === 'B' || (category === 'M' && item.size?.includes('Doz'))) {
    return {
      step: 1,           // Whole number steps
      decimals: 0,       // No decimal places
      pattern: '[0-9]*', // Only integers
      example: '12'
    };
  }
  
  // D, S, W, M (non-dozen)
  return {
    step: 0.01,          // 0.01 increments
    decimals: 2,         // Max 2 decimal places
    pattern: '[0-9]+(\\.[0-9]{0,2})?',
    example: '45.50'
  };
}
```

### Display Units Conversion:

```javascript
function convertToDisplayUnits(servings, item) {
  const uom = parseFloat(item.uom) || 1;
  
  // Full units (kegs/cases/bottles)
  const fullUnits = Math.floor(servings / uom);
  
  // Partial units (pints/bottles/servings)
  const partialUnits = servings % uom;
  
  // Round based on category
  const category = item.category?.code;
  
  if (category === 'B' || (category === 'M' && item.size?.includes('Doz'))) {
    // Bottles: whole numbers only (NO decimals)
    return {
      full: fullUnits,
      partial: Math.round(partialUnits),
      decimals: 0
    };
  } else if (category === 'D') {
    // Draught: 2 decimals for pints
    return {
      full: fullUnits,
      partial: parseFloat(partialUnits.toFixed(2)),
      decimals: 2
    };
  } else {
    // Spirits/Wine: 2 decimals
    return {
      full: fullUnits,
      partial: parseFloat(partialUnits.toFixed(2)),
      decimals: 2
    };
  }
}

// Example 1 (Draught): 221.5 pints with uom=88
// Full: Math.floor(221.5 / 88) = 2 kegs
// Partial: 221.5 % 88 = 45.50 pints (2 decimals)

// Example 2 (Bottled Beer): 145 bottles with uom=12
// Full: Math.floor(145 / 12) = 12 cases
// Partial: 145 % 12 = 1 bottle (NO decimals - whole number)
```

### User Input Formatting:

```javascript
function formatUserInput(value, category, itemSize) {
  const num = parseFloat(value) || 0;
  
  // Bottled beer and dozen minerals - whole numbers
  if (category === 'B' || (category === 'M' && itemSize?.includes('Doz'))) {
    return Math.round(num).toString();
  }
  
  // All others - max 2 decimals
  return num.toFixed(2);
}

// Usage in input handler:
inputElement.addEventListener('blur', (e) => {
  const formatted = formatUserInput(
    e.target.value,
    item.category.code,
    item.size
  );
  e.target.value = formatted;
});
```

### Complete Example by Category:

```javascript
// DRAUGHT BEER (D) - 2 decimals allowed
{
  counted_full_units: 2,      // 2 kegs
  counted_partial_units: 45.50 // 45.50 pints ✅
}

// BOTTLED BEER (B) - NO decimals (whole bottles only)
{
  counted_full_units: 10,     // 10 cases
  counted_partial_units: 8    // 8 bottles ✅ (not 8.5!)
}

// SPIRITS (S) - 2 decimals allowed
{
  counted_full_units: 4,      // 4 bottles
  counted_partial_units: 0.75 // 0.75 of a bottle ✅
}

// WINE (W) - 2 decimals allowed
{
  counted_full_units: 6,      // 6 bottles
  counted_partial_units: 0.33 // 0.33 of a bottle ✅
}

// MINERALS Dozen (M + Doz) - NO decimals
{
  counted_full_units: 5,      // 5 cases
  counted_partial_units: 3    // 3 bottles ✅ (not 3.5!)
}
```

---

## Handling Movements (Purchases/Waste)

When a user adds a purchase or waste movement:

### Step 1: Create Movement

**IMPORTANT**: Use the correct URL structure!

```javascript
async function addMovement(lineId, movementType, quantity, hotelIdentifier) {
  // ✅ CORRECT URL structure (note: add-movement with HYPHEN)
  const url = `/api/stock_tracker/${hotelIdentifier}/stocktake-lines/${lineId}/add-movement/`;
  
  // ❌ WRONG - don't use these:
  // /api/hotels/${hotelIdentifier}/stocktakes/...
  // /api/stock_tracker/${hotelIdentifier}/stocktake-lines/${lineId}/add_movement/ (underscore)
  
  const response = await fetch(url, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}` // Include auth token
    },
    body: JSON.stringify({
      movement_type: movementType, // 'PURCHASE' or 'WASTE'
      quantity: quantity,           // in base units (servings)
      notes: "Added via stocktake"
    })
  });
  
  if (!response.ok) {
    throw new Error(`Failed to add movement: ${response.status}`);
  }
  
  return await response.json();
}

// Example usage:
addMovement(1709, 'PURCHASE', 88, 'hotel-killarney')
  .then(data => console.log('Movement added:', data))
  .catch(error => console.error('Error:', error));
}
```

### Step 2: Optimistic Update (Optional)

If you want immediate UI feedback before backend response:

```javascript
function optimisticUpdate(line, movementType, quantity) {
  const updated = { ...line };
  
  // Update the appropriate movement total
  if (movementType === 'PURCHASE') {
    updated.purchases = (parseFloat(line.purchases) + quantity).toFixed(4);
  } else if (movementType === 'WASTE') {
    updated.waste = (parseFloat(line.waste) + quantity).toFixed(4);
  }
  
  // Recalculate expected using same formula as backend
  const opening = parseFloat(updated.opening_qty);
  const purchases = parseFloat(updated.purchases);
  const waste = parseFloat(updated.waste);
  
  updated.expected_qty = (opening + purchases - waste).toFixed(4);
  
  // Recalculate variance
  const counted = calculateCountedQty(updated);
  updated.variance_qty = (counted - parseFloat(updated.expected_qty)).toFixed(4);
  
  return updated;
}
```

### Step 3: Sync with Backend Response

```javascript
async function addMovementWithSync(line, movementType, quantity) {
  // 1. Optimistic update for immediate feedback
  const optimistic = optimisticUpdate(line, movementType, quantity);
  updateUI(optimistic);
  
  // 2. Send to backend
  const response = await addMovement(line.id, movementType, quantity);
  
  // 3. Replace with backend's authoritative data
  updateUI(response.line);
  
  // 4. Optional: Log if they differ
  if (optimistic.expected_qty !== response.line.expected_qty) {
    console.warn('Optimistic calculation mismatch!', {
      optimistic: optimistic.expected_qty,
      backend: response.line.expected_qty
    });
  }
}
```

---

## Common Pitfalls

### ❌ String Concatenation Instead of Addition

```javascript
// WRONG - strings concatenate
const total = line.purchases + 24;  // "50" + 24 = "5024"

// CORRECT - parse to numbers first
const total = parseFloat(line.purchases) + 24;  // 50 + 24 = 74
```

### ❌ Wrong Formula

```javascript
// WRONG - missing waste
expected = opening + purchases;

// WRONG - including sales (sales calculated separately!)
expected = opening + purchases - sales - waste;

// ✅ CORRECT - current formula (NO SALES)
expected = opening + purchases - waste;
```

### ❌ Not Rounding Display Values

```javascript
// WRONG - too many decimals
display.partial = 45.333333333;

// CORRECT - round based on category
display.partial = parseFloat((45.333333333).toFixed(2));  // 45.33
```

---

## Complete Example

Here's a complete calculation for a Guinness Keg line:

```javascript
const line = {
  item: {
    sku: "BEER_DRAUGHT_GUIN",
    name: "Guinness Keg (11gal)",
    uom: 88,
    category: { code: 'D' }
  },
  opening_qty: "88.0000",
  purchases: "176.0000",
  waste: "5.0000",
  counted_full_units: "2",
  counted_partial_units: "45.50",
  valuation_cost: "2.5000"
};

// 1. Calculate counted quantity
const counted = (2 * 88) + 45.5;  // 221.5 pints

// 2. Calculate expected quantity
const expected = 88 + 176 - 5;  // 259 pints

// 3. Calculate variance
const variance = 221.5 - 259;  // -37.5 pints (shortage)

// 4. Calculate values
const expectedValue = 259 * 2.5;   // €647.50
const countedValue = 221.5 * 2.5;  // €553.75
const varianceValue = -37.5 * 2.5; // -€93.75

// 5. Display units
const display = {
  counted: { full: 2, partial: 45.50 },
  expected: { full: 2, partial: 83.00 },  // 259 = (2 × 88) + 83
  variance: { full: 0, partial: -37.50 }
};

console.log('Counted:', `${display.counted.full} kegs + ${display.counted.partial} pints`);
console.log('Expected:', `${display.expected.full} kegs + ${display.expected.partial} pints`);
console.log('Variance:', `${display.variance.full} kegs + ${display.variance.partial} pints`);
console.log('Variance Value:', `€${varianceValue.toFixed(2)}`);
```

---

## Testing Your Calculations

Compare your frontend calculations with backend:

```javascript
async function testCalculations(stocktakeId, lineId) {
  // Get line from API
  const response = await fetch(
    `/api/stock_tracker/${hotelId}/stocktake-lines/${lineId}/`
  );
  const backendLine = await response.json();
  
  // Calculate in frontend
  const frontendExpected = calculateExpectedQty(backendLine);
  const backendExpected = parseFloat(backendLine.expected_qty);
  
  // Compare
  const match = Math.abs(frontendExpected - backendExpected) < 0.0001;
  
  console.log({
    frontendExpected,
    backendExpected,
    match: match ? '✅' : '❌',
    difference: frontendExpected - backendExpected
  });
}
```

---

## Complete Variance Calculation Flow

Here's the complete picture of what you need for variance:

```javascript
// STEP 1: Get COUNTED quantity (what's physically there)
const countedQty = (parseFloat(line.counted_full_units) * line.item.uom) 
                   + parseFloat(line.counted_partial_units);

// STEP 2: Calculate EXPECTED quantity (what should be there)
const expectedQty = parseFloat(line.opening_qty) 
                    + parseFloat(line.purchases) 
                    - parseFloat(line.waste);

// STEP 3: Calculate VARIANCE (the difference)
const varianceQty = countedQty - expectedQty;

// Interpretation:
// varianceQty > 0  → Surplus (we have more than expected)
// varianceQty < 0  → Shortage (we have less than expected)
// varianceQty = 0  → Perfect match ✅
```

### What You Need for Complete Variance:

1. **Counted Stock** (user input):
   - `counted_full_units`
   - `counted_partial_units`
   - `item.uom` (to convert to base units)

2. **Movement Data** (from backend):
   - `opening_qty` (opening balance)
   - `purchases` (deliveries/purchases)
   - `waste` (breakage/spillage)

3. **Calculations**:
   - Counted → Expected → Variance

---

## Summary Checklist

✅ Use `parseFloat()` on all numeric fields from API  
✅ **Expected formula: `opening + purchases - waste`** (NO SALES!)
✅ Sales calculated separately outside stocktake  
✅ Counted = `(full_units × uom) + partial_units`  
✅ Variance = `counted - expected`  
✅ Values = `quantity × cost`  
✅ Round display units based on category  
✅ Optimistic updates use same formula as backend  
✅ Always sync with backend response after mutation  
✅ **You need opening, purchases, and waste to calculate variance**  

---

---

## Backend API Reference

### StocktakeLine Model Structure

The backend model stores stocktake line data:

```python
class StocktakeLine(models.Model):
    # Foreign Keys
    stocktake = ForeignKey(Stocktake)
    item = ForeignKey(StockItem)
    
    # Opening balances (frozen at populate time)
    opening_qty = DecimalField(max_digits=15, decimal_places=4)
    
    # Period movements (auto-calculated from StockMovement records)
    purchases = DecimalField(max_digits=15, decimal_places=4, default=0)
    waste = DecimalField(max_digits=15, decimal_places=4, default=0)
    transfers_in = DecimalField(max_digits=15, decimal_places=4, default=0)
    transfers_out = DecimalField(max_digits=15, decimal_places=4, default=0)
    adjustments = DecimalField(max_digits=15, decimal_places=4, default=0)
    
    # Manual override (optional)
    manual_purchases_value = DecimalField(null=True, blank=True)
    
    # Counted quantities (USER INPUT - this is what frontend sends)
    counted_full_units = DecimalField(max_digits=10, decimal_places=2, default=0)
    counted_partial_units = DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Valuation
    valuation_cost = DecimalField(max_digits=10, decimal_places=4)
    
    # Computed properties (calculated on-the-fly)
    @property
    def counted_qty(self):
        return (self.counted_full_units * self.item.uom) + self.counted_partial_units
    
    @property
    def expected_qty(self):
        return self.opening_qty + self.purchases - self.waste
    
    @property
    def variance_qty(self):
        return self.counted_qty - self.expected_qty
```

### StocktakeLine Serializer (API Response)

When you GET a stocktake line, the API returns:

```json
{
  "id": 123,
  "stocktake": 4,
  "item": 45,
  "item_sku": "BEER_DRAUGHT_GUIN",
  "item_name": "Guinness Keg (11gal)",
  "category_code": "D",
  "category_name": "Draught Beer",
  "item_size": "11gal",
  "item_uom": "88.00",
  
  // Raw quantities (in base units - servings)
  "opening_qty": "88.0000",
  "purchases": "176.0000",
  "sales_qty": "0.0000",
  "waste": "5.0000",
  "transfers_in": "0.0000",
  "transfers_out": "0.0000",
  "adjustments": "0.0000",
  
  // Manual override (optional)
  "manual_purchases_value": null,
  
  // Counted quantities (USER INPUT - what you PATCH to update)
  "counted_full_units": "2.00",
  "counted_partial_units": "45.50",
  
  // Calculated quantities (READ ONLY - computed by backend)
  "counted_qty": "221.5000",
  "expected_qty": "259.0000",
  "variance_qty": "-37.5000",
  
  // Display quantities (for UI - kegs+pints format)
  "opening_display_full_units": "1",
  "opening_display_partial_units": "0.00",
  "expected_display_full_units": "2",
  "expected_display_partial_units": "83.00",
  "counted_display_full_units": "2",
  "counted_display_partial_units": "45.50",
  "variance_display_full_units": "0",
  "variance_display_partial_units": "-37.50",
  
  // Values (in currency)
  "valuation_cost": "2.5000",
  "expected_value": "647.50",
  "counted_value": "553.75",
  "variance_value": "-93.75"
}
```

### Correct API Endpoints

**CRITICAL**: All stock tracker endpoints use `/api/stock_tracker/` prefix, NOT `/api/hotels/`!

```javascript
// ✅ CORRECT URL patterns:
GET    /api/stock_tracker/{hotel_identifier}/stocktakes/
GET    /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/
POST   /api/stock_tracker/{hotel_identifier}/stocktakes/
PATCH  /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/

GET    /api/stock_tracker/{hotel_identifier}/stocktake-lines/
GET    /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/
PATCH  /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/

POST   /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/add-movement/
GET    /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/movements/

// ❌ WRONG - these DON'T exist:
// /api/hotels/{hotel}/stocktakes/...
// /api/stock_tracker/{hotel}/stocktakes/{id}/lines/.../movements/
```

### What Frontend Can UPDATE

Only these fields can be updated via PATCH:

```javascript
// Update counted stock
PATCH /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/
{
  "counted_full_units": "2.00",     // ✅ Can update
  "counted_partial_units": "45.50", // ✅ Can update
  "manual_purchases_value": "100.00" // ✅ Can update (optional)
}

// These are READ ONLY (auto-calculated):
// ❌ opening_qty (frozen at populate)
// ❌ purchases (from StockMovement records)
// ❌ waste (from StockMovement records)
// ❌ counted_qty (computed from full/partial)
// ❌ expected_qty (computed from formula)
// ❌ variance_qty (computed from counted - expected)
```

### Adding Movements (Purchases/Waste)

To add purchases or waste, use the add-movement endpoint:

```javascript
// ✅ CORRECT endpoint (note: add-movement with HYPHEN)
POST /api/stock_tracker/{hotel_identifier}/stocktake-lines/{line_id}/add-movement/

// Request Body:
{
  "movement_type": "PURCHASE",  // or "WASTE"
  "quantity": "88.0000",        // in base units (servings)
  "unit_cost": "2.5000",        // optional
  "reference": "INV-12345",     // optional
  "notes": "Delivery from supplier" // optional
}

// Backend Response:
{
  "message": "Movement created successfully",
  "movement": {
    "id": 789,
    "movement_type": "PURCHASE",
    "quantity": "88.0000",
    "timestamp": "2025-11-09T10:30:00Z"
  },
  "line": {
    // Full updated StocktakeLine object
    "purchases": "264.0000",  // Auto-updated!
    "expected_qty": "347.0000", // Auto-recalculated!
    "variance_qty": "-125.5000" // Auto-recalculated!
  }
}
```

**Real Example:**
```javascript
// Add a purchase for line 1709 in hotel-killarney
POST /api/stock_tracker/hotel-killarney/stocktake-lines/1709/add-movement/
{
  "movement_type": "PURCHASE",
  "quantity": "88.0000",
  "notes": "Keg delivery"
}
```

### Key Field Types

```javascript
// Strings (must parse to numbers)
"opening_qty": "88.0000"           → parseFloat() → 88.0000
"purchases": "176.0000"            → parseFloat() → 176.0000
"item_uom": "88.00"                → parseFloat() → 88.00

// User input (can be numbers or strings)
counted_full_units: 2              → "2.00" sent to backend
counted_partial_units: 45.5        → "45.50" sent to backend
```

---

## Need Help?

If calculations don't match:

1. Log both frontend and backend values
2. Check you're using `parseFloat()` everywhere
3. Verify the formula matches exactly
4. Check for category-specific rounding issues
5. Test with simple examples first

For questions, check:
- Backend formulas: `stock_tracker/models.py` (StocktakeLine properties)
- Backend serializer: `stock_tracker/stock_serializers.py` (StocktakeLineSerializer)
- Backend service: `stock_tracker/stocktake_service.py`
- Formula documentation: `stock_tracker/WASTE_AND_VARIANCE_EXPLAINED.md`
