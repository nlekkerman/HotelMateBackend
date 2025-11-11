# Sales API - Fixed & Independent from Stocktakes

## 🎉 What's Fixed

**Problem:** The sales summary endpoint crashed with `UnboundLocalError` when using date ranges.

**Root Cause:** Backend tried to return `stocktake_id` even when it wasn't defined (date-based queries).

**Solution:** Sales are now fully independent from stocktakes. You can query sales by date range without any stocktake relationship.

---

## 📡 Sales Summary Endpoint

### **Endpoint**
```
GET /api/stock_tracker/{hotel_slug}/sales/summary/
```

### **Authentication**
Required: Token authentication with hotel context

---

## 🔥 Option 1: Date Range Query (RECOMMENDED)

Use this for all new features - **NO STOCKTAKE REQUIRED**.

### **Request**
```http
GET /api/stock_tracker/hotel-killarney/sales/summary/?start_date=2025-09-01&end_date=2025-09-30
Authorization: Token your-token-here
X-Hotel-ID: 2
X-Hotel-Slug: hotel-killarney
```

### **Parameters**
| Parameter    | Type   | Required | Format     | Description                    |
|--------------|--------|----------|------------|--------------------------------|
| `start_date` | string | Yes*     | YYYY-MM-DD | Start date of sales period     |
| `end_date`   | string | Yes*     | YYYY-MM-DD | End date of sales period       |

*Required when not using `stocktake` parameter

### **Response**
```json
{
  "start_date": "2025-09-01",
  "end_date": "2025-09-30",
  "by_category": [
    {
      "item__category__code": "D",
      "item__category__name": "Draught Beer",
      "total_quantity": "450.5000",
      "total_cost": "1250.75",
      "total_revenue": "3200.00",
      "sale_count": 125
    },
    {
      "item__category__code": "B",
      "item__category__name": "Bottled Beer",
      "total_quantity": "340.0000",
      "total_cost": "850.50",
      "total_revenue": "2100.00",
      "sale_count": 85
    },
    {
      "item__category__code": "S",
      "item__category__name": "Spirits",
      "total_quantity": "180.0000",
      "total_cost": "720.00",
      "total_revenue": "1800.00",
      "sale_count": 45
    }
  ],
  "overall": {
    "total_quantity": "970.5000",
    "total_cost": "2821.25",
    "total_revenue": "7100.00",
    "sale_count": 255,
    "gross_profit": "4278.75",
    "gross_profit_percentage": 60.25
  }
}
```

### **Frontend Usage Example**

```javascript
// ✅ NEW WAY - Date-based (RECOMMENDED)
export const getSalesSummary = async (hotelSlug, startDate, endDate) => {
  try {
    const response = await api.get(
      `/stock_tracker/${hotelSlug}/sales/summary/`,
      {
        params: {
          start_date: startDate,  // "2025-09-01"
          end_date: endDate       // "2025-09-30"
        }
      }
    );
    
    console.log('✅ Sales data:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error fetching sales:', error);
    throw error;
  }
};

// Usage for a specific month
const getSalesForMonth = async (hotelSlug, year, month) => {
  const startDate = `${year}-${month.toString().padStart(2, '0')}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const endDate = `${year}-${month.toString().padStart(2, '0')}-${lastDay}`;
  
  return await getSalesSummary(hotelSlug, startDate, endDate);
};

// Example: Get September 2025 sales
const septemberSales = await getSalesForMonth('hotel-killarney', 2025, 9);
```

---

## 🔙 Option 2: Stocktake-Based Query (LEGACY)

Only use this if you need sales linked to a specific stocktake period.

### **Request**
```http
GET /api/stock_tracker/hotel-killarney/sales/summary/?stocktake=123
Authorization: Token your-token-here
X-Hotel-ID: 2
X-Hotel-Slug: hotel-killarney
```

### **Parameters**
| Parameter   | Type    | Required | Description              |
|-------------|---------|----------|--------------------------|
| `stocktake` | integer | Yes*     | Stocktake ID to filter   |

*Required when not using date range

### **Response**
```json
{
  "stocktake_id": "123",
  "by_category": [
    // ... same structure as date-based
  ],
  "overall": {
    // ... same structure as date-based
  }
}
```

### **Frontend Usage Example**

```javascript
// ❌ OLD WAY - Stocktake-based (LEGACY - avoid if possible)
export const getSalesByStocktake = async (hotelSlug, stocktakeId) => {
  const response = await api.get(
    `/stock_tracker/${hotelSlug}/sales/summary/`,
    {
      params: { stocktake: stocktakeId }
    }
  );
  return response.data;
};
```

---

## 🔍 Other Sales Endpoints

### **List Sales**
Get detailed list of individual sales.

```http
GET /api/stock_tracker/{hotel_slug}/sales/
```

**Query Parameters:**
- `start_date` - Filter by sale date (YYYY-MM-DD)
- `end_date` - Filter by sale date (YYYY-MM-DD)
- `month` - Filter by month (YYYY-MM, e.g., "2025-09")
- `item` - Filter by item ID
- `category` - Filter by category code (D, B, S, W, M)
- `stocktake` - Filter by stocktake ID (legacy)

**Examples:**
```javascript
// Get all sales for September 2025
GET /api/stock_tracker/hotel-killarney/sales/?start_date=2025-09-01&end_date=2025-09-30

// Get sales for a specific month (shorthand)
GET /api/stock_tracker/hotel-killarney/sales/?month=2025-09

// Get sales for a specific item
GET /api/stock_tracker/hotel-killarney/sales/?item=456

// Get draught beer sales only
GET /api/stock_tracker/hotel-killarney/sales/?category=D
```

### **Create Sale**
```http
POST /api/stock_tracker/{hotel_slug}/sales/
Content-Type: application/json
```

**Request Body:**
```json
{
  "item": 123,                    // Required: Item ID
  "quantity": "45.5000",          // Required: Quantity sold
  "sale_date": "2025-09-15",      // Required: Date of sale
  "unit_cost": "2.5000",          // Optional: Auto-populated from item
  "unit_price": "6.00",           // Optional: Auto-populated from item
  "stocktake": null,              // Optional: Leave null for independent sales
  "notes": "Happy hour sales"     // Optional
}
```

**Response:**
```json
{
  "id": 789,
  "item": 123,
  "item_sku": "D001",
  "item_name": "Guinness Keg 50Lt",
  "category_code": "D",
  "category_name": "Draught Beer",
  "quantity": "45.5000",
  "unit_cost": "2.5000",
  "unit_price": "6.00",
  "total_cost": "113.75",
  "total_revenue": "273.00",
  "gross_profit": "159.25",
  "gross_profit_percentage": "58.35",
  "pour_cost_percentage": "41.65",
  "sale_date": "2025-09-15",
  "stocktake": null,
  "stocktake_period": null,
  "notes": "Happy hour sales",
  "created_by": 5,
  "created_by_name": "John Manager",
  "created_at": "2025-11-11T18:30:00Z",
  "updated_at": "2025-11-11T18:30:00Z"
}
```

### **Bulk Create Sales**
```http
POST /api/stock_tracker/{hotel_slug}/sales/bulk_create/
Content-Type: application/json
```

**Request Body:**
```json
{
  "sales": [
    {
      "item": 123,
      "quantity": "45.5000",
      "sale_date": "2025-09-15"
    },
    {
      "item": 124,
      "quantity": "30.0000",
      "sale_date": "2025-09-15"
    }
  ]
}
```

---

## 📊 Response Field Explanations

### **by_category Array**
Each category contains aggregated sales data:

| Field                      | Type    | Description                                    |
|----------------------------|---------|------------------------------------------------|
| `item__category__code`     | string  | Category code (D/B/S/W/M)                      |
| `item__category__name`     | string  | Category name (e.g., "Draught Beer")           |
| `total_quantity`           | decimal | Total quantity sold in servings                |
| `total_cost`               | decimal | Total COGS (Cost of Goods Sold)                |
| `total_revenue`            | decimal | Total sales revenue                            |
| `sale_count`               | integer | Number of sale records                         |

### **overall Object**
Aggregated totals across all categories:

| Field                      | Type    | Description                                    |
|----------------------------|---------|------------------------------------------------|
| `total_quantity`           | decimal | Total servings sold                            |
| `total_cost`               | decimal | Total COGS                                     |
| `total_revenue`            | decimal | Total revenue                                  |
| `sale_count`               | integer | Total number of sales                          |
| `gross_profit`             | decimal | Revenue - COGS (calculated)                    |
| `gross_profit_percentage`  | decimal | (Gross Profit / Revenue) × 100 (calculated)    |

---

## ⚠️ Error Handling

### **400 Bad Request - Missing Parameters**
```json
{
  "error": "Either start_date & end_date OR stocktake parameter is required",
  "examples": [
    "?start_date=2025-10-01&end_date=2025-10-31",
    "?stocktake=123"
  ]
}
```

### **400 Bad Request - Invalid Date Format**
```json
{
  "error": "Invalid date format. Use YYYY-MM-DD"
}
```

### **404 Not Found - Hotel Not Found**
```json
{
  "detail": "Not found."
}
```

---

## 🎯 Frontend Migration Checklist

### **Remove Deprecated Code**
- [ ] Remove any code that fetches stocktake just to get sales data
- [ ] Remove `getSalesAnalysis()` function (marked as LEGACY)
- [ ] Remove period-based sales queries

### **Implement New Pattern**
- [ ] Use `getSalesSummary(hotelSlug, startDate, endDate)` for all sales queries
- [ ] Convert month selection to date range in frontend:
  ```javascript
  const monthToDateRange = (year, month) => {
    const start = `${year}-${month.padStart(2, '0')}-01`;
    const lastDay = new Date(year, month, 0).getDate();
    const end = `${year}-${month.padStart(2, '0')}-${lastDay}`;
    return { start, end };
  };
  ```
- [ ] Handle empty data gracefully (no sales in date range)
- [ ] Display date range in UI instead of stocktake period

### **Update Components**
- [ ] `SalesReport.jsx` - Use date range selector
- [ ] `SalesDashboard.jsx` - Fetch by date, not stocktake
- [ ] Any reports showing sales data - Use date-based queries

---

## 💡 Best Practices

### **DO ✅**
- Use date ranges for querying sales
- Let backend auto-populate `unit_cost` and `unit_price` from items
- Create sales with `stocktake: null` for independent tracking
- Convert month selection to date range in frontend
- Cache sales data by date range, not stocktake

### **DON'T ❌**
- Don't require stocktake to exist before creating sales
- Don't fetch stocktake just to get stocktake ID for sales query
- Don't use `getSalesAnalysis()` (deprecated)
- Don't assume `stocktake_id` is always in response
- Don't couple sales UI to stocktake UI

---

## 🐛 Debugging

### **Check Request**
```javascript
console.log('📡 Fetching Sales Summary:', {
  endpoint: `/stock_tracker/${hotelSlug}/sales/summary/`,
  params: { start_date: startDate, end_date: endDate }
});
```

### **Check Response**
```javascript
console.log('📊 Sales Summary Response:', {
  hasData: response.data.overall.sale_count > 0,
  dateRange: `${response.data.start_date} to ${response.data.end_date}`,
  totalRevenue: response.data.overall.total_revenue,
  categories: response.data.by_category.length
});
```

### **Common Issues**
1. **Still getting 500 error?** 
   - Make sure backend changes are deployed
   - Check date format is YYYY-MM-DD
   - Verify both start_date AND end_date are provided

2. **Empty data returned?**
   - Check if sales exist for that date range in database
   - Verify hotel context is correct
   - Check date range is valid (start < end)

3. **Missing stocktake_id in response?**
   - This is expected when using date ranges
   - Only legacy stocktake queries return stocktake_id
   - Update frontend to not expect this field

---

## 📞 Support

For backend issues:
- Check Django logs for errors
- Verify Sale model has data for date range
- Test endpoint in Postman/Thunder Client

For frontend issues:
- Check browser console for request/response
- Verify axios headers include hotel context
- Test with curl to isolate frontend vs backend

---

**Last Updated:** November 11, 2025  
**Backend Version:** Fixed UnboundLocalError in SaleViewSet.summary()  
**Status:** ✅ Production Ready
