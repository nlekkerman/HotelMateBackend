# Stock Tracker API - Frontend Integration Guide

## Overview

The stock tracker system manages inventory through categories, items, movements, and periodic stocktakes. It implements the full formula from `Stocktake_Formulas.md`:

```
expected_qty = opening + purchases - sales - waste + transfers_in - transfers_out + adjustments
variance_qty = counted_qty - expected_qty
```

## Base URL

All endpoints are prefixed with `/api/stock-tracker/`

---

## 1. Stock Categories

### List Categories
```http
GET /api/stock-tracker/categories/
```

**Response:**
```json
[
  {
    "id": 1,
    "hotel": 1,
    "name": "Wine",
    "sort_order": 10
  }
]
```

### Create Category
```http
POST /api/stock-tracker/categories/
Content-Type: application/json

{
  "hotel": 1,
  "name": "Wine",
  "sort_order": 10
}
```

---

## 2. Stock Items

### List Items
```http
GET /api/stock-tracker/items/
```

**Query Parameters:**
- `hotel` - Filter by hotel ID
- `category` - Filter by category ID

**Response:**
```json
[
  {
    "id": 1,
    "hotel": 1,
    "category": 1,
    "code": "WIN001",
    "description": "Pinot Grigio",
    "size": "70cl",
    "uom": "12.00",
    "unit_cost": "45.5000",
    "selling_price": "8.50",
    "current_qty": "120.0000",
    "base_unit": "ml",
    "gp_percentage": "81.33"
  }
]
```

### Create Item
```http
POST /api/stock-tracker/items/
Content-Type: application/json

{
  "hotel": 1,
  "category": 1,
  "code": "WIN001",
  "description": "Pinot Grigio",
  "size": "70cl",
  "uom": "12.00",
  "unit_cost": "45.5000",
  "selling_price": "8.50",
  "base_unit": "ml"
}
```

**Notes:**
- `uom`: Units of measure (e.g., 12 bottles per case)
- `unit_cost`: Cost per full unit (case/keg/bottle)
- `current_qty`: Automatically updated by movements
- `gp_percentage`: Auto-calculated if `selling_price` provided

---

## 3. Stock Movements

### List Movements
```http
GET /api/stock-tracker/movements/
```

**Query Parameters:**
- `hotel` - Filter by hotel ID
- `item` - Filter by item ID
- `movement_type` - Filter by type (PURCHASE, SALE, WASTE, TRANSFER_IN, TRANSFER_OUT, ADJUSTMENT)
- `timestamp__gte` - Filter movements after date (YYYY-MM-DD)
- `timestamp__lte` - Filter movements before date (YYYY-MM-DD)

**Response:**
```json
[
  {
    "id": 1,
    "hotel": 1,
    "item": 1,
    "movement_type": "PURCHASE",
    "quantity": "144.0000",
    "unit_cost": "45.5000",
    "reference": "INV-2024-001",
    "notes": "Weekly delivery",
    "timestamp": "2024-11-01T10:30:00Z",
    "staff": 5
  }
]
```

### Create Movement
```http
POST /api/stock-tracker/movements/
Content-Type: application/json

{
  "hotel": 1,
  "item": 1,
  "movement_type": "PURCHASE",
  "quantity": "144.0000",
  "unit_cost": "45.5000",
  "reference": "INV-2024-001",
  "notes": "Weekly delivery",
  "staff": 5
}
```

**Movement Types:**
- `PURCHASE` - Stock received (increases qty)
- `SALE` - Stock sold/consumed (decreases qty)
- `WASTE` - Breakage/spoilage (decreases qty)
- `TRANSFER_IN` - Received from another location (increases qty)
- `TRANSFER_OUT` - Sent to another location (decreases qty)
- `ADJUSTMENT` - Stocktake adjustment (auto-created on approve)

**Important:** 
- Item's `current_qty` is automatically updated when movement is saved
- `quantity` should always be positive; direction is determined by `movement_type`

---

## 4. Stocktakes

### List Stocktakes
```http
GET /api/stock-tracker/stocktakes/
```

**Query Parameters:**
- `hotel` - Filter by hotel ID
- `status` - Filter by status (DRAFT, APPROVED)

**Response:**
```json
[
  {
    "id": 1,
    "hotel": 1,
    "period_start": "2024-11-01",
    "period_end": "2024-11-30",
    "status": "DRAFT",
    "created_at": "2024-11-06T10:00:00Z",
    "approved_at": null,
    "approved_by": null,
    "notes": "November stocktake"
  }
]
```

### Create Stocktake
```http
POST /api/stock-tracker/stocktakes/
Content-Type: application/json

{
  "hotel": 1,
  "period_start": "2024-11-01",
  "period_end": "2024-11-30",
  "notes": "November stocktake"
}
```

**Response:** Returns created stocktake with `status: "DRAFT"`

### Get Stocktake Details (with lines)
```http
GET /api/stock-tracker/stocktakes/{id}/
```

**Response:**
```json
{
  "id": 1,
  "hotel": 1,
  "period_start": "2024-11-01",
  "period_end": "2024-11-30",
  "status": "DRAFT",
  "created_at": "2024-11-06T10:00:00Z",
  "approved_at": null,
  "approved_by": null,
  "notes": "November stocktake",
  "lines": [
    {
      "id": 1,
      "item": 1,
      "item_code": "WIN001",
      "item_description": "Pinot Grigio",
      "opening_qty": "120.0000",
      "purchases": "144.0000",
      "sales": "96.0000",
      "waste": "12.0000",
      "transfers_in": "0.0000",
      "transfers_out": "0.0000",
      "adjustments": "0.0000",
      "counted_full_units": "13.00",
      "counted_partial_units": "8.00",
      "valuation_cost": "3.7917",
      "counted_qty": "164.0000",
      "expected_qty": "156.0000",
      "variance_qty": "8.0000",
      "expected_value": "591.54",
      "counted_value": "621.84",
      "variance_value": "30.30"
    }
  ]
}
```

---

## 5. Stocktake Workflow

### Step 1: Create Stocktake
Create a DRAFT stocktake with period dates:

```http
POST /api/stock-tracker/stocktakes/
Content-Type: application/json

{
  "hotel": 1,
  "period_start": "2024-11-01",
  "period_end": "2024-11-30"
}
```

### Step 2: Populate Stocktake Lines
Generate stocktake lines with opening balances and period movements:

```http
POST /api/stock-tracker/stocktakes/{id}/populate/
```

**What it does:**
- Creates a `StocktakeLine` for each `StockItem` in the hotel
- Calculates `opening_qty` from movements before `period_start`
- Sums period movements: purchases, sales, waste, transfers, adjustments
- Freezes `valuation_cost` at current `item.unit_cost`
- Initializes `counted_full_units` and `counted_partial_units` to 0

**Response:**
```json
{
  "message": "Stocktake populated with 45 items"
}
```

### Step 3: Update Counted Quantities
Frontend should allow users to input physical counts:

```http
PATCH /api/stock-tracker/stocktake-lines/{line_id}/
Content-Type: application/json

{
  "counted_full_units": "13.00",
  "counted_partial_units": "8.00"
}
```

**Notes:**
- `counted_full_units`: Full cases/kegs counted (e.g., 13 full cases)
- `counted_partial_units`: Partial units (e.g., 8 bottles from an open case)
- `counted_qty` is auto-calculated: `(counted_full_units * item.uom) + counted_partial_units`
- Cannot edit lines once stocktake is APPROVED

### Step 4: Review Variances
Use the detail endpoint to show variances to user:

```http
GET /api/stock-tracker/stocktakes/{id}/
```

Display:
- `expected_qty` (calculated from formula)
- `counted_qty` (from user input)
- `variance_qty` (counted - expected)
- `variance_value` (variance * valuation_cost)

### Step 5: Get Category Totals (Optional)
Get subtotals grouped by category:

```http
GET /api/stock-tracker/stocktakes/{id}/category-totals/
```

**Response:**
```json
[
  {
    "category_id": 1,
    "category_name": "Wine",
    "expected_value": "12450.75",
    "counted_value": "12680.50",
    "variance_value": "229.75"
  },
  {
    "category_id": 2,
    "category_name": "Spirits",
    "expected_value": "8920.00",
    "counted_value": "8850.25",
    "variance_value": "-69.75"
  }
]
```

### Step 6: Approve Stocktake
Finalize the stocktake and create adjustment movements:

```http
POST /api/stock-tracker/stocktakes/{id}/approve/
Content-Type: application/json

{
  "approved_by": 5
}
```

**What it does:**
- Sets `status` to "APPROVED"
- Sets `approved_at` to current timestamp
- Records `approved_by` staff member
- For each line with non-zero `variance_qty`:
  - Creates a `StockMovement` with type "ADJUSTMENT"
  - Updates `item.current_qty` to match `counted_qty`
  - Uses frozen `valuation_cost` for movement
- Locks the stocktake (no further edits allowed)

**Response:**
```json
{
  "message": "Stocktake approved. 12 adjustment movements created."
}
```

---

## 6. Frontend UI Recommendations

### Stocktake List Screen
- Show period dates, status badge (DRAFT/APPROVED), created date
- Filter by date range and status
- Actions: View, Edit (if DRAFT), Approve (if DRAFT)

### Stocktake Detail/Edit Screen
Layout suggestion:
```
Header:
- Period: Nov 1 - Nov 30, 2024
- Status: DRAFT
- Buttons: [Populate] [Approve] [Cancel]

Table (grouped by category):
Category: Wine
┌──────────┬─────────────┬──────────┬──────────┬─────────┬──────────┬──────────┬──────────┐
│ Code     │ Description │ Expected │ Full     │ Partial │ Counted  │ Variance │ Value    │
├──────────┼─────────────┼──────────┼──────────┼─────────┼──────────┼──────────┼──────────┤
│ WIN001   │ Pinot Grig. │ 156.00   │ [13]     │ [8]     │ 164.00   │ +8.00    │ +€30.30  │
│ WIN002   │ Merlot      │ 84.00    │ [6]      │ [10]    │ 82.00    │ -2.00    │ -€9.50   │
└──────────┴─────────────┴──────────┴──────────┴─────────┴──────────┴──────────┴──────────┘
Category Total:                                                                   +€20.80

Category: Spirits
...
```

### Input Fields
- Allow editing `counted_full_units` and `counted_partial_units` only
- Show all other fields as read-only (calculated)
- Highlight variances > threshold (e.g., >5% or >€50) in red/yellow

### Category Totals Summary
Show before approval:
```
┌─────────────────┬──────────────┬──────────────┬───────────────┐
│ Category        │ Expected     │ Counted      │ Variance      │
├─────────────────┼──────────────┼──────────────┼───────────────┤
│ Wine            │ €12,450.75   │ €12,680.50   │ +€229.75      │
│ Spirits         │ €8,920.00    │ €8,850.25    │ -€69.75       │
│ Beer            │ €3,200.00    │ €3,215.00    │ +€15.00       │
├─────────────────┼──────────────┼──────────────┼───────────────┤
│ Total           │ €24,570.75   │ €24,745.75   │ +€175.00      │
└─────────────────┴──────────────┴──────────────┴───────────────┘
```

---

## 7. Calculation Details

### Counted Quantity
```
counted_qty = (counted_full_units × item.uom) + counted_partial_units
```

**Example:**
- Item: Wine bottle (70cl), UOM = 12 (12 bottles per case)
- Counted: 13 full cases + 8 loose bottles
- Result: (13 × 12) + 8 = 156 + 8 = 164 bottles

### Expected Quantity (Formula)
```
expected_qty = opening + purchases - sales - waste + transfers_in - transfers_out + adjustments
```

All quantities in base units (bottles, ml, kg, etc.)

### Variance
```
variance_qty = counted_qty - expected_qty
variance_value = variance_qty × valuation_cost
```

Positive variance = more stock than expected (overage)
Negative variance = less stock than expected (shortage)

---

## 8. Error Handling

### Common Errors

**Editing locked stocktake:**
```json
{
  "error": "Cannot modify stocktake lines after approval"
}
```

**Duplicate period:**
```json
{
  "non_field_errors": [
    "Stocktake with this Hotel, Period start and Period end already exists."
  ]
}
```

**Approving already approved:**
```json
{
  "error": "Stocktake is already approved"
}
```

---

## 9. Data Model Reference

### StockItem Fields
- `code` - Unique item code per hotel
- `description` - Item name
- `size` - Container size (e.g., "70cl", "30Lt")
- `uom` - Units of measure (conversion factor)
- `unit_cost` - Cost per full unit (4 decimals)
- `current_qty` - Current stock level (auto-updated)
- `base_unit` - Base measurement unit (ml, g, pieces)

### StocktakeLine Fields (Read-Only)
- `opening_qty` - Stock at period_start
- `purchases` - Deliveries in period
- `sales` - Consumption in period  
- `waste` - Breakage/spoilage in period
- `transfers_in` - Received transfers in period
- `transfers_out` - Sent transfers in period
- `adjustments` - Prior adjustments in period
- `valuation_cost` - Frozen cost per base unit

### StocktakeLine Fields (Editable)
- `counted_full_units` - Full containers counted
- `counted_partial_units` - Partial units counted

### StocktakeLine Fields (Calculated)
- `counted_qty` - Total counted (full + partial)
- `expected_qty` - Calculated from formula
- `variance_qty` - Counted - expected
- `expected_value` - Expected × cost
- `counted_value` - Counted × cost
- `variance_value` - Variance × cost

---

## 10. Testing Endpoints

Use Django admin or create test data:

```python
# Create category
POST /api/stock-tracker/categories/
{"hotel": 1, "name": "Wine", "sort_order": 10}

# Create item
POST /api/stock-tracker/items/
{
  "hotel": 1,
  "category": 1,
  "code": "WIN001",
  "description": "Pinot Grigio 70cl",
  "size": "70cl",
  "uom": "12.00",
  "unit_cost": "45.5000",
  "base_unit": "bottles"
}

# Add opening stock
POST /api/stock-tracker/movements/
{
  "hotel": 1,
  "item": 1,
  "movement_type": "ADJUSTMENT",
  "quantity": "120.0000",
  "reference": "Opening balance",
  "staff": 1
}

# Add purchase
POST /api/stock-tracker/movements/
{
  "hotel": 1,
  "item": 1,
  "movement_type": "PURCHASE",
  "quantity": "144.0000",
  "reference": "INV-001",
  "staff": 1
}

# Create stocktake
POST /api/stock-tracker/stocktakes/
{"hotel": 1, "period_start": "2024-11-01", "period_end": "2024-11-30"}

# Populate it (use returned stocktake ID)
POST /api/stock-tracker/stocktakes/1/populate/

# Update count
PATCH /api/stock-tracker/stocktake-lines/1/
{"counted_full_units": "13.00", "counted_partial_units": "8.00"}

# Approve
POST /api/stock-tracker/stocktakes/1/approve/
{"approved_by": 1}
```

---

## 11. Reference Documents

- **Formulas**: See `Stocktake_Formulas.md` for detailed formula documentation
- **Excel Example**: See `Aug25_full_sheet.md` for real-world stocktake structure
- **Backend Code**: 
  - Models: `stock_tracker/models.py`
  - Service Layer: `stock_tracker/stocktake_service.py`
  - Serializers: `stock_tracker/stock_serializers.py`
  - Views: `stock_tracker/views.py`

---

## Summary

**Key Points:**
1. Create DRAFT stocktake → Populate → Edit counts → Review → Approve
2. All calculations are automatic (expected, variance, valuations)
3. Users only input `counted_full_units` and `counted_partial_units`
4. Approval creates ADJUSTMENT movements and locks the stocktake
5. Use frozen `valuation_cost` for consistent historical reporting
6. Support mixed units (full cases + partial bottles/pieces)
