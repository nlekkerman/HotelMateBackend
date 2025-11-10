# Sales API Quick Reference

## Base URL
```
/api/stock-tracker/{hotel_identifier}/
```

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sales/` | List all sales (with filters) |
| POST | `/sales/` | Create a new sale |
| GET | `/sales/{id}/` | Get single sale details |
| PUT/PATCH | `/sales/{id}/` | Update a sale |
| DELETE | `/sales/{id}/` | Delete a sale |
| GET | `/sales/summary/` | Get sales summary by category |
| POST | `/sales/bulk_create/` | Create multiple sales at once |
| GET | `/stocktake-lines/{id}/sales/` | Get sales for specific line item |

---

## 1. List Sales
**GET** `/api/stock-tracker/{hotel}/sales/`

### Query Parameters
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `stocktake` | int | Filter by stocktake ID | `?stocktake=5` |
| `item` | int | Filter by item ID | `?item=123` |
| `category` | string | Filter by category code | `?category=D` |
| `start_date` | date | Filter by date range | `?start_date=2024-11-01` |
| `end_date` | date | Filter by date range | `?end_date=2024-11-30` |

### Response
```json
[
  {
    "id": 1,
    "stocktake": 5,
    "stocktake_period": "2024-11-01 to 2024-11-30",
    "item": 123,
    "item_sku": "D001",
    "item_name": "Guinness Draught 50L Keg",
    "category_code": "D",
    "category_name": "Draught Beer",
    "quantity": "350.0000",
    "unit_cost": "0.2214",
    "unit_price": "7.00",
    "total_cost": "77.49",
    "total_revenue": "2450.00",
    "gross_profit": "2372.51",
    "gross_profit_percentage": "96.84",
    "pour_cost_percentage": "3.16",
    "sale_date": "2024-11-10",
    "notes": "",
    "created_by": 1,
    "created_by_name": "John Manager",
    "created_at": "2024-11-10T14:30:00Z",
    "updated_at": "2024-11-10T14:30:00Z"
  }
]
```

---

## 2. Create Sale
**POST** `/api/stock-tracker/{hotel}/sales/`

### Request Body
```json
{
  "stocktake": 5,
  "item": 123,
  "quantity": "350.0000",
  "unit_cost": "0.2214",
  "unit_price": "7.00",
  "sale_date": "2024-11-10",
  "notes": "Weekend sales"
}
```

### Required Fields
- `stocktake` - Stocktake ID (integer)
- `item` - Item ID (integer)
- `quantity` - Quantity sold in servings (decimal, e.g., "350.0000")
- `unit_cost` - Cost per serving (decimal, e.g., "0.2214")
- `sale_date` - Date of sale (YYYY-MM-DD)

### Optional Fields
- `unit_price` - Selling price per serving (decimal)
- `notes` - Additional notes (string)

### Auto-Calculated Fields
- `total_cost` = quantity × unit_cost
- `total_revenue` = quantity × unit_price
- `gross_profit` = total_revenue - total_cost
- `gross_profit_percentage` = (gross_profit / total_revenue) × 100
- `pour_cost_percentage` = (total_cost / total_revenue) × 100
- `created_by` - Set from authenticated user

### Response
Same as GET (single sale object)

---

## 3. Update Sale
**PUT/PATCH** `/api/stock-tracker/{hotel}/sales/{id}/`

### Request Body
Same as POST (all fields for PUT, partial for PATCH)

### Response
Updated sale object

---

## 4. Delete Sale
**DELETE** `/api/stock-tracker/{hotel}/sales/{id}/`

### Response
`204 No Content`

---

## 5. Sales Summary
**GET** `/api/stock-tracker/{hotel}/sales/summary/?stocktake={id}`

### Query Parameters
- `stocktake` - **Required** - Stocktake ID

### Response
```json
{
  "stocktake_id": 5,
  "by_category": [
    {
      "item__category__code": "D",
      "item__category__name": "Draught Beer",
      "total_quantity": "1250.0000",
      "total_cost": "276.75",
      "total_revenue": "8750.00",
      "sale_count": 15
    }
  ],
  "overall": {
    "total_quantity": "1700.0000",
    "total_cost": "951.75",
    "total_revenue": "10550.00",
    "sale_count": 23,
    "gross_profit": "9598.25",
    "gross_profit_percentage": "90.98"
  }
}
```

---

## 6. Bulk Create Sales
**POST** `/api/stock-tracker/{hotel}/sales/bulk_create/`

### Request Body
```json
{
  "sales": [
    {
      "stocktake": 5,
      "item": 123,
      "quantity": "350.0000",
      "unit_cost": "0.2214",
      "unit_price": "7.00",
      "sale_date": "2024-11-10"
    },
    {
      "stocktake": 5,
      "item": 124,
      "quantity": "200.0000",
      "unit_cost": "1.50",
      "unit_price": "4.00",
      "sale_date": "2024-11-10"
    }
  ]
}
```

### Response (Success)
```json
{
  "message": "All sales created successfully",
  "created_count": 2,
  "sales": [/* array of created sales */]
}
```

### Response (Partial Success - 207 Multi-Status)
```json
{
  "message": "Some sales failed to create",
  "created_count": 1,
  "errors": [
    {
      "index": 1,
      "errors": {
        "quantity": ["This field is required"]
      }
    }
  ]
}
```

---

## 7. Get Line Item Sales
**GET** `/api/stock-tracker/{hotel}/stocktake-lines/{line_id}/sales/`

### Response
```json
{
  "sales": [
    {
      "id": 1,
      "stocktake": 5,
      "item": 123,
      "quantity": "350.0000",
      "unit_price": "7.00",
      "total_revenue": "2450.00",
      "gross_profit_percentage": "96.84",
      "sale_date": "2024-11-10"
    }
  ],
  "summary": {
    "total_quantity": "350.0000",
    "total_cost": "77.49",
    "total_revenue": "2450.00",
    "gross_profit": "2372.51",
    "gross_profit_percentage": 96.84,
    "sale_count": 1
  },
  "item": {
    "id": 123,
    "sku": "D001",
    "name": "Guinness Draught 50L Keg",
    "menu_price": "7.00",
    "cost_per_serving": "0.2214"
  }
}
```

---

## Frontend Usage Examples

### Fetch Sales for Stocktake Line
```javascript
const fetchLineSales = async (lineId) => {
  const response = await fetch(
    `/api/stock-tracker/${hotelIdentifier}/stocktake-lines/${lineId}/sales/`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return await response.json();
};
```

### Create Sale
```javascript
const createSale = async (saleData) => {
  const response = await fetch(
    `/api/stock-tracker/${hotelIdentifier}/sales/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        stocktake: 5,
        item: 123,
        quantity: "350.0000",
        unit_cost: "0.2214",
        unit_price: "7.00",
        sale_date: "2024-11-10",
        notes: ""
      })
    }
  );
  return await response.json();
};
```

### Delete Sale
```javascript
const deleteSale = async (saleId) => {
  await fetch(
    `/api/stock-tracker/${hotelIdentifier}/sales/${saleId}/`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
};
```

### Get Sales Summary
```javascript
const getSummary = async (stocktakeId) => {
  const response = await fetch(
    `/api/stock-tracker/${hotelIdentifier}/sales/summary/?stocktake=${stocktakeId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return await response.json();
};
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "quantity: This field is required"
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 403 Forbidden
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Data Validation

### Quantity Format
- Must be a positive decimal number
- Max 15 digits, 4 decimal places
- Example: "350.0000", "12.5", "1000"

### Unit Cost/Price Format
- Must be a positive decimal number
- Max 10 digits, 4 decimal places for cost
- Max 10 digits, 2 decimal places for price
- Example: "0.2214", "7.00", "15.50"

### Date Format
- Must be YYYY-MM-DD
- Example: "2024-11-10"

### Notes
- Optional text field
- No maximum length

---

## Backend Priority System

When calculating revenue/COGS for stocktake, the backend uses this priority:

### Revenue (total_revenue):
1. ✅ Line-level manual (`StocktakeLine.manual_sales_value`)
2. ✅ Period-level manual (`StockPeriod.manual_sales_amount`)
3. ✅ Sum of itemized sales (`Sale.total_revenue`)

### COGS (total_cogs):
1. ✅ Period-level manual (`StockPeriod.manual_purchases_amount`)
2. ✅ Line-level manual (`StocktakeLine.manual_purchases_value + manual_waste_value`)
3. ✅ Sum of itemized sales (`Sale.total_cost`)

**This means:** If any manual values exist, they override itemized sales.

---

## Tips for Frontend Integration

### 1. Pre-fill Values
Always pre-fill these fields when creating a sale:
- `unit_price` from `item.menu_price`
- `unit_cost` from `item.cost_per_serving`
- `sale_date` to today's date

### 2. Real-time Updates
After creating/updating/deleting a sale:
1. Refresh the line's sales list
2. Refresh the stocktake summary
3. Update profitability metrics (GP%, Pour Cost%)

### 3. Validation
Client-side validation:
- Quantity > 0
- Date within stocktake period
- Unit price and cost are positive numbers

### 4. Display Format
- Quantity: Show with item's serving unit (pints, bottles, shots)
- Currency: Always show with 2 decimal places (€7.00)
- Percentages: Show with 1-2 decimal places (96.8%)

---

## Testing Checklist

- [ ] Create sale with all required fields
- [ ] Create sale with optional fields (notes, unit_price)
- [ ] Update existing sale
- [ ] Delete sale
- [ ] Fetch sales for stocktake
- [ ] Fetch sales for specific item
- [ ] Get sales summary
- [ ] Bulk create multiple sales
- [ ] Handle validation errors
- [ ] Handle 404 errors
- [ ] Test with locked stocktake (should prevent creation)
