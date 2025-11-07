# Stock Tracker API Endpoints

## Overview
All endpoints require authentication and use the hotel identifier in the URL path.
Base URL pattern: `/api/stock/<hotel_identifier>/`

---

## Stock Categories

### List/Create Categories
- **GET** `/api/stock/<hotel_identifier>/categories/`
  - Returns all 5 stock categories (D, B, S, W, M)
  - Includes item count for each category

- **GET** `/api/stock/<hotel_identifier>/categories/<code>/`
  - Get details of specific category (e.g., "D" for Draught)

- **GET** `/api/stock/<hotel_identifier>/categories/<code>/items/`
  - Get all stock items in this category

---

## Locations

### List/Create Locations
- **GET** `/api/stock/<hotel_identifier>/locations/`
  - List all stock locations (Bar, Cellar, Storage, etc.)
  
- **POST** `/api/stock/<hotel_identifier>/locations/`
  - Create new location
  ```json
  {
    "name": "Main Bar",
    "location_type": "BAR",
    "description": "Main bar area",
    "is_active": true
  }
  ```

- **GET/PUT/PATCH/DELETE** `/api/stock/<hotel_identifier>/locations/<id>/`
  - Manage specific location

---

## Stock Periods

### List/Create Periods
- **GET** `/api/stock/<hotel_identifier>/periods/`
  - List all stock periods (sorted by date, newest first)
  
- **POST** `/api/stock/<hotel_identifier>/periods/`
  - Create new period
  ```json
  {
    "period_type": "MONTHLY",
    "start_date": "2024-11-01",
    "end_date": "2024-11-30",
    "year": 2024,
    "month": 11
  }
  ```

- **GET** `/api/stock/<hotel_identifier>/periods/<id>/`
  - Get specific period details

- **GET** `/api/stock/<hotel_identifier>/periods/<id>/snapshots/`
  - Get all stock snapshots for this period
  - Query params: `?category=D` to filter by category

- **GET** `/api/stock/<hotel_identifier>/periods/compare/?period1=<id>&period2=<id>`
  - Compare two periods side-by-side
  - Returns detailed comparison with value/unit changes and percentages

---

## Stock Snapshots

### List Snapshots (Read-only)
- **GET** `/api/stock/<hotel_identifier>/snapshots/`
  - List all stock snapshots
  - Query params: `?item=<id>`, `?period=<id>`

- **GET** `/api/stock/<hotel_identifier>/snapshots/<id>/`
  - Get specific snapshot details

---

## Stock Items

### List/Create Items
- **GET** `/api/stock/<hotel_identifier>/items/`
  - List all stock items
  - Query params: `?category=<code>`, `?search=<term>`
  
- **POST** `/api/stock/<hotel_identifier>/items/`
  - Create new stock item
  ```json
  {
    "sku": "D0001",
    "name": "Guinness 50L",
    "category": "D",
    "size": "50Lt",
    "size_value": 50,
    "size_unit": "L",
    "uom": 88.03,
    "unit_cost": 125.50,
    "current_full_units": 5,
    "current_partial_units": 22.5,
    "menu_price": 5.50
  }
  ```

- **GET/PUT/PATCH/DELETE** `/api/stock/<hotel_identifier>/items/<id>/`
  - Manage specific stock item

### Analytics Endpoints

- **GET** `/api/stock/<hotel_identifier>/items/profitability/`
  - Get profitability analysis for all items
  - Query params: `?category=<code>`
  - Returns: GP%, markup%, pour cost%, profit per serving, etc.
  - Sorted by GP% descending

- **GET** `/api/stock/<hotel_identifier>/items/low-stock/`
  - Get items with ≤2 full units remaining

- **GET** `/api/stock/<hotel_identifier>/items/<id>/history/`
  - Get stock history for this item across all periods

---

## Stock Movements

### List/Create Movements
- **GET** `/api/stock/<hotel_identifier>/movements/`
  - List all stock movements (newest first)
  - Query params: `?item=<id>`, `?movement_type=<type>`
  
- **POST** `/api/stock/<hotel_identifier>/movements/`
  - Record stock movement
  ```json
  {
    "item": 123,
    "movement_type": "PURCHASE",
    "full_units": 10,
    "partial_units": 0,
    "unit_cost": 125.50,
    "reference": "INV-2024-1234",
    "notes": "Weekly delivery"
  }
  ```
  
  Movement types:
  - `PURCHASE` - Stock purchased
  - `SALE` - Stock sold
  - `WASTE` - Stock wasted/damaged
  - `TRANSFER_IN` - Transferred from another location
  - `TRANSFER_OUT` - Transferred to another location
  - `ADJUSTMENT` - Manual adjustment

- **GET/PUT/PATCH/DELETE** `/api/stock/<hotel_identifier>/movements/<id>/`
  - Manage specific movement

---

## Stocktakes

### List/Create Stocktakes
- **GET** `/api/stock/<hotel_identifier>/stocktakes/`
  - List all stocktakes
  - Query params: `?status=<status>`
  
- **POST** `/api/stock/<hotel_identifier>/stocktakes/`
  - Create new stocktake
  ```json
  {
    "period_start": "2024-11-01",
    "period_end": "2024-11-30",
    "notes": "End of month stocktake"
  }
  ```

- **GET/PUT/PATCH/DELETE** `/api/stock/<hotel_identifier>/stocktakes/<id>/`
  - Manage specific stocktake

### Stocktake Actions

- **POST** `/api/stock/<hotel_identifier>/stocktakes/<id>/populate/`
  - Generate stocktake lines with opening balances and movements
  - Cannot populate locked/approved stocktakes

- **POST** `/api/stock/<hotel_identifier>/stocktakes/<id>/approve/`
  - Approve stocktake and create adjustment movements for variances
  - Cannot approve already approved stocktakes

- **GET** `/api/stock/<hotel_identifier>/stocktakes/<id>/category-totals/`
  - Get totals grouped by category

---

## Stocktake Lines

### List/Update Lines
- **GET** `/api/stock/<hotel_identifier>/stocktake-lines/`
  - List all stocktake lines
  - Query params: `?stocktake=<id>`, `?item=<id>`

- **GET** `/api/stock/<hotel_identifier>/stocktake-lines/<id>/`
  - Get specific line details

- **PUT/PATCH** `/api/stock/<hotel_identifier>/stocktake-lines/<id>/`
  - Update counted quantities (cannot edit approved stocktakes)
  ```json
  {
    "counted_full_units": 5,
    "counted_partial_units": 8
  }
  ```

---

## Cocktail Endpoints (Existing)

### Ingredients
- **GET/POST** `/api/stock/<hotel_identifier>/ingredients/`
- **GET/PUT/PATCH/DELETE** `/api/stock/<hotel_identifier>/ingredients/<id>/`

### Cocktails
- **GET/POST** `/api/stock/<hotel_identifier>/cocktails/`
- **GET/PUT/PATCH/DELETE** `/api/stock/<hotel_identifier>/cocktails/<id>/`

### Cocktail Consumption
- **GET/POST** `/api/stock/<hotel_identifier>/consumptions/`
- **GET/PUT/PATCH/DELETE** `/api/stock/<hotel_identifier>/consumptions/<id>/`

### Analytics
- **GET** `/api/stock/<hotel_identifier>/analytics/ingredient-usage/`

---

## Response Formats

### Stock Item Response
```json
{
  "id": 1,
  "hotel": 1,
  "sku": "D0005",
  "name": "50 Guinness",
  "category": "D",
  "category_code": "D",
  "category_name": "Draught Beer",
  "size": "50Lt",
  "size_value": 50,
  "size_unit": "L",
  "uom": 88.03,
  "unit_cost": 179.00,
  "current_full_units": 7,
  "current_partial_units": 0,
  "menu_price": 5.50,
  "total_units": 7.00,
  "total_stock_value": 1253.00,
  "cost_per_serving": 2.03,
  "gross_profit_per_serving": 3.47,
  "gp_percentage": 63.09,
  "markup_percentage": 170.94,
  "pour_cost_percentage": 36.91,
  "created_at": "2024-11-07T16:15:30Z",
  "updated_at": "2024-11-07T16:15:30Z"
}
```

### Stock Snapshot Response
```json
{
  "id": 1,
  "hotel": 1,
  "item": 1,
  "item_sku": "D0005",
  "item_name": "50 Guinness",
  "category_code": "D",
  "period": 1,
  "period_name": "October 2024",
  "closing_full_units": 7,
  "closing_partial_units": 0,
  "total_units": 7.00,
  "unit_cost": 179.00,
  "cost_per_serving": 2.03,
  "closing_stock_value": 1253.00,
  "created_at": "2024-11-07T16:15:30Z"
}
```

### Period Comparison Response
```json
{
  "period1": {
    "id": 1,
    "period_name": "October 2024",
    "start_date": "2024-10-01",
    "end_date": "2024-10-31"
  },
  "period2": {
    "id": 2,
    "period_name": "November 2024",
    "start_date": "2024-11-01",
    "end_date": "2024-11-30"
  },
  "comparison": [
    {
      "item_id": 1,
      "sku": "D0005",
      "name": "50 Guinness",
      "category": "D",
      "period1": {
        "period_name": "October 2024",
        "closing_stock": 1253.00,
        "units": 7.00
      },
      "period2": {
        "period_name": "November 2024",
        "closing_stock": 895.00,
        "units": 5.00
      },
      "change": {
        "value": -358.00,
        "units": -2.00,
        "percentage": -28.57
      }
    }
  ]
}
```

### Profitability Analysis Response
```json
[
  {
    "id": 1,
    "sku": "S0380",
    "name": "Jack Daniels",
    "category": "S",
    "unit_cost": 28.50,
    "menu_price": 5.50,
    "cost_per_serving": 1.43,
    "gross_profit": 4.07,
    "gp_percentage": 74.00,
    "markup_percentage": 284.62,
    "pour_cost_percentage": 26.00,
    "current_stock_value": 142.50
  }
]
```

---

## Notes

1. **Authentication**: All endpoints require authentication
2. **Hotel Context**: Hotel is automatically set from URL parameter
3. **Staff Context**: Staff is automatically set from authenticated user (where applicable)
4. **Filtering**: Most list endpoints support filtering via query parameters
5. **Ordering**: Default ordering specified per endpoint
6. **Pagination**: Currently disabled (pagination_class = None)
7. **Decimal Precision**: All monetary values use Decimal with proper precision
8. **Calculated Fields**: Many fields (GP%, markup%, etc.) are read-only calculated properties
