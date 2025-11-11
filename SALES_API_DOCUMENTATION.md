# Sales API Documentation

## Overview

The Sales API allows you to track, create, and query sales data for stock items. Sales can be created as **standalone records** or **linked to a stocktake period** for period reporting.

---

## Base URL

```
/api/stock-tracker/<hotel_identifier>/sales/
```

**hotel_identifier**: The hotel's slug or subdomain (e.g., `hotel-killarney`, `myhotel`)

---

## Endpoints

### 1. List All Sales

**GET** `/api/stock-tracker/<hotel_identifier>/sales/`

Retrieves all sales for the specified hotel.

**Response:**
```json
[
  {
    "id": 1,
    "item": {
      "id": 123,
      "sku": "D0005",
      "name": "50 Guinness"
    },
    "quantity": "555.0000",
    "unit_cost": "2.1200",
    "unit_price": "6.30",
    "total_cost": "1175.88",
    "total_revenue": "3496.50",
    "sale_date": "2025-09-11",
    "notes": "",
    "stocktake": null,
    "created_by": null,
    "created_at": "2025-11-11T10:00:00Z"
  }
]
```

---

### 2. Filter Sales by Date Range

**GET** `/api/stock-tracker/<hotel_identifier>/sales/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

Filter sales within a specific date range.

**Query Parameters:**
- `start_date` (optional): Filter sales from this date onwards (format: `YYYY-MM-DD`)
- `end_date` (optional): Filter sales up to this date (format: `YYYY-MM-DD`)

**Examples:**

```bash
# Sales from October 1st onwards
GET /api/stock-tracker/hotel-killarney/sales/?start_date=2025-10-01

# Sales up to October 31st
GET /api/stock-tracker/hotel-killarney/sales/?end_date=2025-10-31

# Sales in October 2025
GET /api/stock-tracker/hotel-killarney/sales/?start_date=2025-10-01&end_date=2025-10-31

# Sales in September 2025
GET /api/stock-tracker/hotel-killarney/sales/?start_date=2025-09-01&end_date=2025-09-30
```

---

### 3. Filter Sales by Stocktake Period

**GET** `/api/stock-tracker/<hotel_identifier>/sales/?stocktake=<stocktake_id>`

Get all sales linked to a specific stocktake period.

**Query Parameters:**
- `stocktake`: Stocktake ID

**Example:**
```bash
GET /api/stock-tracker/hotel-killarney/sales/?stocktake=42
```

---

### 4. Filter Sales by Item

**GET** `/api/stock-tracker/<hotel_identifier>/sales/?item=<item_id>`

Get all sales for a specific stock item.

**Query Parameters:**
- `item`: Stock item ID

**Example:**
```bash
GET /api/stock-tracker/hotel-killarney/sales/?item=123
```

---

### 5. Filter Sales by Category

**GET** `/api/stock-tracker/<hotel_identifier>/sales/?category=<category_code>`

Get all sales for items in a specific category.

**Query Parameters:**
- `category`: Category code (`D`, `B`, `S`, `W`, `M`)

**Category Codes:**
- `D` = Draught
- `B` = Bottled
- `S` = Spirits
- `W` = Wine
- `M` = Minerals/Soft Drinks

**Example:**
```bash
# All draught beer sales
GET /api/stock-tracker/hotel-killarney/sales/?category=D

# All bottled beer sales
GET /api/stock-tracker/hotel-killarney/sales/?category=B
```

---

### 6. Combined Filters

You can combine multiple filters for advanced queries.

**Examples:**

```bash
# Draught beer sales in October 2025
GET /api/stock-tracker/hotel-killarney/sales/?category=D&start_date=2025-10-01&end_date=2025-10-31

# Specific item sales in a date range
GET /api/stock-tracker/hotel-killarney/sales/?item=123&start_date=2025-09-01&end_date=2025-09-30

# Stocktake period sales for specific category
GET /api/stock-tracker/hotel-killarney/sales/?stocktake=42&category=S
```

---

### 7. Get Sales Summary

**GET** `/api/stock-tracker/<hotel_identifier>/sales/summary/?stocktake=<stocktake_id>`

Get aggregated sales summary by category for a stocktake period.

**Query Parameters:**
- `stocktake` (required): Stocktake ID

**Response:**
```json
{
  "by_category": [
    {
      "category_code": "D",
      "category_name": "Draught",
      "total_quantity": "1110.0000",
      "total_cost": "2351.76",
      "total_revenue": "6993.00",
      "sale_count": 2
    },
    {
      "category_code": "B",
      "category_name": "Bottled",
      "total_quantity": "5550.0000",
      "total_cost": "8234.56",
      "total_revenue": "24678.50",
      "sale_count": 15
    }
  ],
  "overall": {
    "total_quantity": "6660.0000",
    "total_cost": "10586.32",
    "total_revenue": "31671.50",
    "sale_count": 17
  }
}
```

---

### 8. Create a New Sale

**POST** `/api/stock-tracker/<hotel_identifier>/sales/`

Create a new sale record.

**Request Body:**
```json
{
  "item": 123,
  "quantity": "50.0000",
  "unit_cost": "2.1200",
  "unit_price": "6.30",
  "sale_date": "2025-11-11",
  "notes": "Evening shift sales",
  "stocktake": null
}
```

**Fields:**
- `item` (required): Stock item ID
- `quantity` (required): Quantity sold (in servings/units)
- `unit_cost` (required): Cost per unit
- `unit_price` (optional): Selling price per unit
- `sale_date` (required): Date of sale (format: `YYYY-MM-DD`)
- `notes` (optional): Additional notes
- `stocktake` (optional): Stocktake ID to link this sale to a period

**Note:** `total_cost` and `total_revenue` are calculated automatically.

---

### 9. Bulk Create Sales

**POST** `/api/stock-tracker/<hotel_identifier>/sales/bulk-create/`

Create multiple sales at once.

**Request Body:**
```json
{
  "sales": [
    {
      "item": 123,
      "quantity": "50.0000",
      "unit_cost": "2.1200",
      "unit_price": "6.30",
      "sale_date": "2025-11-11"
    },
    {
      "item": 124,
      "quantity": "30.0000",
      "unit_cost": "1.50",
      "unit_price": "4.50",
      "sale_date": "2025-11-11"
    }
  ]
}
```

**Response:**
```json
{
  "message": "Created 2 sales successfully",
  "created_count": 2,
  "sales": [...]
}
```

---

### 10. Update a Sale

**PATCH** `/api/stock-tracker/<hotel_identifier>/sales/<sale_id>/`

Update an existing sale record.

**Request Body:**
```json
{
  "quantity": "55.0000",
  "notes": "Updated quantity"
}
```

---

### 11. Delete a Sale

**DELETE** `/api/stock-tracker/<hotel_identifier>/sales/<sale_id>/`

Delete a sale record.

---

## Frontend Integration Examples

### React/JavaScript

```javascript
// Get all sales for a date range
const fetchSalesByDateRange = async (hotelIdentifier, startDate, endDate) => {
  const url = `/api/stock-tracker/${hotelIdentifier}/sales/?start_date=${startDate}&end_date=${endDate}`;
  const response = await fetch(url);
  const sales = await response.json();
  return sales;
};

// Example usage
const sales = await fetchSalesByDateRange('hotel-killarney', '2025-10-01', '2025-10-31');
console.log(sales);

// Create a new sale
const createSale = async (hotelIdentifier, saleData) => {
  const url = `/api/stock-tracker/${hotelIdentifier}/sales/`;
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(saleData)
  });
  return await response.json();
};

// Example usage
const newSale = await createSale('hotel-killarney', {
  item: 123,
  quantity: "50.0000",
  unit_cost: "2.1200",
  unit_price: "6.30",
  sale_date: "2025-11-11",
  notes: "Daily sales entry"
});
```

### Axios

```javascript
import axios from 'axios';

// Get sales with filters
const getSales = async (filters) => {
  const { hotelIdentifier, startDate, endDate, category, item } = filters;
  
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (category) params.append('category', category);
  if (item) params.append('item', item);
  
  const response = await axios.get(
    `/api/stock-tracker/${hotelIdentifier}/sales/?${params.toString()}`
  );
  
  return response.data;
};

// Usage
const sales = await getSales({
  hotelIdentifier: 'hotel-killarney',
  startDate: '2025-10-01',
  endDate: '2025-10-31',
  category: 'D'
});
```

---

## Common Use Cases

### 1. Daily Sales Dashboard

Fetch today's sales:
```javascript
const today = new Date().toISOString().split('T')[0];
const todaySales = await fetch(
  `/api/stock-tracker/hotel-killarney/sales/?start_date=${today}&end_date=${today}`
);
```

### 2. Monthly Sales Report

Fetch all sales for the current month:
```javascript
const now = new Date();
const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
  .toISOString().split('T')[0];
const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  .toISOString().split('T')[0];

const monthlySales = await fetch(
  `/api/stock-tracker/hotel-killarney/sales/?start_date=${startOfMonth}&end_date=${endOfMonth}`
);
```

### 3. Category Performance

Fetch all draught beer sales for analysis:
```javascript
const draughtSales = await fetch(
  `/api/stock-tracker/hotel-killarney/sales/?category=D&start_date=2025-09-01&end_date=2025-09-30`
);
```

### 4. Link Sales to Stocktake

When creating sales during a stocktake period:
```javascript
const saleData = {
  item: 123,
  quantity: "50.0000",
  unit_cost: "2.1200",
  unit_price: "6.30",
  sale_date: "2025-11-11",
  stocktake: 42  // Link to stocktake ID 42
};
```

---

## Important Notes

1. **Standalone vs Linked Sales:**
   - Sales can be created without a stocktake (`stocktake: null`) for general tracking
   - Link sales to stocktakes for period-based reporting and inventory calculations

2. **Date Format:**
   - Always use `YYYY-MM-DD` format for dates
   - Example: `2025-11-11` for November 11, 2025

3. **Filtering:**
   - All filters can be combined
   - Date filtering works on `sale_date` field
   - Filtering by `item__hotel` ensures only hotel's sales are returned

4. **Automatic Calculations:**
   - `total_cost` = `quantity` × `unit_cost`
   - `total_revenue` = `quantity` × `unit_price`
   - These are calculated automatically on save

5. **Permissions:**
   - Some endpoints may require authentication
   - Check with your backend team for specific permission requirements

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid date format. Use YYYY-MM-DD"
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Server Error
```json
{
  "error": "Internal server error"
}
```

---

## Testing the API

You can test the API using:

1. **Browser:** Navigate to the endpoint URL directly
2. **Postman:** Import the endpoints and test with different parameters
3. **cURL:**
   ```bash
   curl "http://localhost:8000/api/stock-tracker/hotel-killarney/sales/?start_date=2025-09-01&end_date=2025-09-30"
   ```

4. **Python Script:** Use the provided test scripts in the repository

---

## Support

For issues or questions:
1. Check the Django admin panel for data verification
2. Review server logs for detailed error messages
3. Contact the backend development team

---

**Last Updated:** November 11, 2025
