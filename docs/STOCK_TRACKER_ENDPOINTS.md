# Stock Tracker API Endpoints

Base URL: `/api/stock-tracker/`

---

## Stock Categories

### List Categories
```
GET /api/stock-tracker/categories/
```
**Query Parameters:**
- `hotel` - Filter by hotel ID

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
```
POST /api/stock-tracker/categories/
```
**Body:**
```json
{
  "hotel": 1,
  "name": "Wine",
  "sort_order": 10
}
```

### Get Category
```
GET /api/stock-tracker/categories/{id}/
```

### Update Category
```
PUT /api/stock-tracker/categories/{id}/
PATCH /api/stock-tracker/categories/{id}/
```

### Delete Category
```
DELETE /api/stock-tracker/categories/{id}/
```

---

## Stock Items

### List Items
```
GET /api/stock-tracker/items/
```
**Query Parameters:**
- `hotel` - Filter by hotel ID
- `category` - Filter by category ID
- `code` - Filter by item code
- `search` - Search by code or description

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
```
POST /api/stock-tracker/items/
```
**Body:**
```json
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

### Get Item
```
GET /api/stock-tracker/items/{id}/
```

### Update Item
```
PUT /api/stock-tracker/items/{id}/
PATCH /api/stock-tracker/items/{id}/
```

### Delete Item
```
DELETE /api/stock-tracker/items/{id}/
```

---

## Stock Movements

### List Movements
```
GET /api/stock-tracker/movements/
```
**Query Parameters:**
- `hotel` - Filter by hotel ID
- `item` - Filter by item ID
- `movement_type` - Filter by type: `PURCHASE`, `SALE`, `WASTE`, `TRANSFER_IN`, `TRANSFER_OUT`, `ADJUSTMENT`
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
```
POST /api/stock-tracker/movements/
```
**Body:**
```json
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

### Get Movement
```
GET /api/stock-tracker/movements/{id}/
```

### Update Movement
```
PUT /api/stock-tracker/movements/{id}/
PATCH /api/stock-tracker/movements/{id}/
```

### Delete Movement
```
DELETE /api/stock-tracker/movements/{id}/
```

---

## Stocktakes

### List Stocktakes
```
GET /api/stock-tracker/stocktakes/
```
**Query Parameters:**
- `hotel` - Filter by hotel ID
- `status` - Filter by status: `DRAFT`, `APPROVED`
- `period_start` - Filter by start date
- `period_end` - Filter by end date

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
```
POST /api/stock-tracker/stocktakes/
```
**Body:**
```json
{
  "hotel": 1,
  "period_start": "2024-11-01",
  "period_end": "2024-11-30",
  "notes": "November stocktake"
}
```

### Get Stocktake (with lines)
```
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

### Update Stocktake
```
PUT /api/stock-tracker/stocktakes/{id}/
PATCH /api/stock-tracker/stocktakes/{id}/
```
**Note:** Can only update DRAFT stocktakes

### Delete Stocktake
```
DELETE /api/stock-tracker/stocktakes/{id}/
```
**Note:** Can only delete DRAFT stocktakes

### Populate Stocktake
```
POST /api/stock-tracker/stocktakes/{id}/populate/
```
**What it does:**
- Creates StocktakeLine for each StockItem
- Calculates opening balance from movements before period_start
- Sums period movements (purchases, sales, waste, transfers, adjustments)
- Freezes valuation_cost at current unit_cost
- Initializes counted units to 0

**Response:**
```json
{
  "message": "Stocktake populated with 45 items"
}
```

### Approve Stocktake
```
POST /api/stock-tracker/stocktakes/{id}/approve/
```
**Body:**
```json
{
  "approved_by": 5
}
```

**What it does:**
- Sets status to APPROVED
- Sets approved_at timestamp
- Records approved_by staff member
- Creates ADJUSTMENT movements for non-zero variances
- Updates item.current_qty to match counted_qty
- Locks the stocktake (no further edits)

**Response:**
```json
{
  "message": "Stocktake approved. 12 adjustment movements created."
}
```

### Get Category Totals
```
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

---

## Stocktake Lines

### List Lines
```
GET /api/stock-tracker/stocktake-lines/
```
**Query Parameters:**
- `stocktake` - Filter by stocktake ID
- `item` - Filter by item ID

**Response:**
```json
[
  {
    "id": 1,
    "stocktake": 1,
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
```

### Get Line
```
GET /api/stock-tracker/stocktake-lines/{id}/
```

### Update Line (Edit Counts)
```
PATCH /api/stock-tracker/stocktake-lines/{id}/
```
**Body:**
```json
{
  "counted_full_units": "13.00",
  "counted_partial_units": "8.00"
}
```
**Note:** Can only edit lines on DRAFT stocktakes

### Delete Line
```
DELETE /api/stock-tracker/stocktake-lines/{id}/
```
**Note:** Can only delete lines on DRAFT stocktakes

---

## Cocktail Calculator (Existing)

### List Ingredients
```
GET /api/stock-tracker/ingredients/
```

### Create Ingredient
```
POST /api/stock-tracker/ingredients/
```

### List Cocktails
```
GET /api/stock-tracker/cocktails/
```

### Create Cocktail
```
POST /api/stock-tracker/cocktails/
```

### List Consumptions
```
GET /api/stock-tracker/consumptions/
```

### Create Consumption
```
POST /api/stock-tracker/consumptions/
```

### Ingredient Usage Analytics
```
GET /api/stock-tracker/analytics/ingredient-usage/
```
**Query Parameters:**
- `start_date` - Filter from date (YYYY-MM-DD)
- `end_date` - Filter to date (YYYY-MM-DD)
- `hotel` - Filter by hotel ID

---

## Workflow Example

### Complete Stocktake Flow

1. **Create Stocktake**
```bash
POST /api/stock-tracker/stocktakes/
{
  "hotel": 1,
  "period_start": "2024-11-01",
  "period_end": "2024-11-30"
}
# Returns: {"id": 1, ...}
```

2. **Populate Lines**
```bash
POST /api/stock-tracker/stocktakes/1/populate/
# Generates lines with opening balances and period movements
```

3. **Update Counts**
```bash
PATCH /api/stock-tracker/stocktake-lines/1/
{
  "counted_full_units": "13.00",
  "counted_partial_units": "8.00"
}
# Repeat for each line
```

4. **Review Variances**
```bash
GET /api/stock-tracker/stocktakes/1/
# Check variance_qty and variance_value for each line
```

5. **Get Category Summary**
```bash
GET /api/stock-tracker/stocktakes/1/category-totals/
# Review totals by category before approval
```

6. **Approve Stocktake**
```bash
POST /api/stock-tracker/stocktakes/1/approve/
{
  "approved_by": 5
}
# Creates ADJUSTMENT movements and locks stocktake
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Cannot populate approved stocktake"
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 409 Conflict
```json
{
  "non_field_errors": [
    "Stocktake with this Hotel, Period start and Period end already exists."
  ]
}
```

---

## Notes

- All endpoints require authentication
- Dates in format: `YYYY-MM-DD`
- Timestamps in format: `YYYY-MM-DDTHH:MM:SSZ`
- Decimal values as strings with up to 4 decimal places
- `current_qty` auto-updated by movements (don't set manually)
- Stocktakes can only be edited when `status: "DRAFT"`
- ADJUSTMENT movements are auto-created on approve (don't create manually)
