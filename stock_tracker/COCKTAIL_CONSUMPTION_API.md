# Cocktail Consumption & Merge API Documentation

## Overview
This document describes the backend API endpoints for tracking cocktail ingredient consumption and merging them into stocktakes.

## Key Concepts

### Automatic Tracking
When a `CocktailConsumption` is created (e.g., "Made 10 Mojitos"), the system automatically creates `CocktailIngredientConsumption` records for each ingredient used.

### Optional Merging
Cocktail ingredient usage is tracked separately from stocktake. Frontend can merge these into stocktake calculations ONLY when user clicks a merge button.

### Merge Status
- **Available/Unmerged**: Tracked but not yet included in stocktake
- **Merged**: Included in stocktake purchases, creates `StockMovement` with type `COCKTAIL_CONSUMPTION`

---

## API Endpoints

### 1. Ingredient Consumptions (Read-Only)

#### List All Ingredient Consumptions
```
GET /api/stock_tracker/{hotel}/ingredient-consumptions/
```

**Query Parameters:**
- `merged` - Filter by merge status: `true`, `false`
- `stock_item` - Filter by stock item ID
- `ingredient` - Filter by ingredient ID
- `stocktake` - Filter by stocktake ID (shows merged items)
- `start_date` - Filter from date (YYYY-MM-DD)
- `end_date` - Filter to date (YYYY-MM-DD)

**Response:**
```json
[
  {
    "id": 1,
    "cocktail_consumption_id": 5,
    "cocktail_name": "Mojito",
    "quantity_made": 10,
    "ingredient": 3,
    "ingredient_name": "White Rum",
    "quantity_used": "250.0000",
    "unit": "ml",
    "stock_item": 42,
    "stock_item_sku": "S001",
    "stock_item_name": "Havana Club 3 Year",
    "unit_cost": null,
    "total_cost": null,
    "is_merged_to_stocktake": false,
    "merged_at": null,
    "merged_by": null,
    "merged_by_name": null,
    "stocktake_id": null,
    "can_be_merged": true,
    "timestamp": "2025-11-10T14:30:00Z"
  }
]
```

#### Get Single Ingredient Consumption
```
GET /api/stock_tracker/{hotel}/ingredient-consumptions/{id}/
```

#### Get Available (Unmerged) Consumptions
```
GET /api/stock_tracker/{hotel}/ingredient-consumptions/available/
```

**Response:**
```json
{
  "count": 15,
  "total_quantity": "1250.5000",
  "consumptions": [...]
}
```

#### Get Grouped by Stock Item
```
GET /api/stock_tracker/{hotel}/ingredient-consumptions/by-stock-item/
```

Shows unmerged quantities grouped by stock item.

**Response:**
```json
{
  "items": [
    {
      "stock_item__id": 42,
      "stock_item__sku": "S001",
      "stock_item__name": "Havana Club 3 Year",
      "unit": "ml",
      "total_quantity": "500.0000",
      "consumption_count": 5
    }
  ]
}
```

---

### 2. Cocktail Consumptions (Enhanced)

#### Create Cocktail Consumption
```
POST /api/stock_tracker/{hotel}/consumptions/
```

**Request:**
```json
{
  "cocktail_id": 5,
  "quantity_made": 10,
  "unit_price": 8.50
}
```

**Response:** Includes `ingredient_consumptions` array showing auto-created records
```json
{
  "id": 15,
  "cocktail": "Mojito",
  "cocktail_id": 5,
  "quantity_made": 10,
  "timestamp": "2025-11-10T14:30:00Z",
  "unit_price": "8.50",
  "total_revenue": "85.00",
  "total_cost": "0.00",
  "profit": "85.00",
  "total_ingredient_usage": {...},
  "ingredient_consumptions": [
    {
      "id": 45,
      "ingredient_name": "White Rum",
      "quantity_used": "250.0000",
      "unit": "ml",
      "stock_item_sku": "S001",
      "is_merged": false,
      "can_be_merged": true
    },
    {
      "id": 46,
      "ingredient_name": "Fresh Mint",
      "quantity_used": "50.0000",
      "unit": "g",
      "stock_item_sku": null,
      "is_merged": false,
      "can_be_merged": false
    }
  ]
}
```

---

### 3. Stocktake Line - Display Cocktail Data

#### Get Stocktake Lines
```
GET /api/stock_tracker/{hotel}/stocktake-lines/?stocktake={id}
```

**Response includes cocktail consumption fields:**
```json
{
  "id": 150,
  "item_sku": "S001",
  "item_name": "Havana Club 3 Year",
  "opening_qty": "1000.0000",
  "purchases": "500.0000",
  "expected_qty": "1500.0000",
  "counted_qty": "1450.0000",
  "variance_qty": "-50.0000",
  
  // COCKTAIL CONSUMPTION TRACKING (DISPLAY ONLY)
  "available_cocktail_consumption_qty": "250.0000",
  "available_cocktail_consumption_value": "75.00",
  "merged_cocktail_consumption_qty": "100.0000",
  "merged_cocktail_consumption_value": "30.00",
  "can_merge_cocktails": true
}
```

**Frontend Display Logic:**
- If `can_merge_cocktails` is `true`: Show "Merge Cocktails" button
- `available_cocktail_consumption_qty`: Show in yellow/warning (pending merge)
- `merged_cocktail_consumption_qty`: Show in green/success (already in purchases)

---

### 4. Merge Cocktails (User Action Required)

#### Merge Single Line
```
POST /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/merge-cocktail-consumption/
```

Merges all unmerged cocktail consumption for ONE stocktake line item.

**Response:**
```json
{
  "message": "Cocktail consumption merged successfully",
  "merged_count": 3,
  "total_quantity_merged": "250.0000",
  "movement_id": 456,
  "line": {
    // Updated line data with recalculated purchases
    "purchases": "750.0000",
    "available_cocktail_consumption_qty": "0.0000",
    "merged_cocktail_consumption_qty": "350.0000",
    "can_merge_cocktails": false
  }
}
```

**What Happens:**
1. Gets all unmerged `CocktailIngredientConsumption` for this stock item
2. Creates ONE `StockMovement` with type `COCKTAIL_CONSUMPTION`
3. Marks all consumptions as `is_merged_to_stocktake=true`
4. Recalculates `line.purchases` to include merged quantity
5. Updates `expected_qty` and `variance_qty`

#### Merge All (Bulk)
```
POST /api/stock_tracker/{hotel}/stocktakes/{stocktake_id}/merge-all-cocktail-consumption/
```

Merges cocktail consumption for ALL lines in the stocktake at once.

**Response:**
```json
{
  "message": "Successfully merged cocktail consumption for 8 lines",
  "summary": {
    "lines_affected": 8,
    "total_items_merged": 25,
    "total_quantity_merged": "1250.5000",
    "total_value_merged": "375.50",
    "details": [
      {
        "line_id": 150,
        "item_sku": "S001",
        "item_name": "Havana Club 3 Year",
        "quantity_merged": "250.0000",
        "value_merged": "75.00",
        "records_merged": 3
      }
    ]
  }
}
```

---

### 5. Ingredients - Link to Stock Items

#### Update Ingredient to Link Stock Item
```
PATCH /api/stock_tracker/{hotel}/ingredients/{id}/
```

**Request:**
```json
{
  "linked_stock_item_id": 42
}
```

Links ingredient to stock item so consumption can be tracked in inventory.

**Get Ingredient with Stock Link:**
```json
{
  "id": 3,
  "name": "White Rum",
  "unit": "ml",
  "hotel_id": 1,
  "linked_stock_item_id": 42,
  "linked_stock_item": {
    "id": 42,
    "sku": "S001",
    "name": "Havana Club 3 Year"
  }
}
```

---

## Frontend Implementation Guide

### Display Unmerged Cocktails in Stocktake Line
```javascript
if (line.can_merge_cocktails) {
  // Show yellow badge with quantity
  <Badge color="warning">
    {line.available_cocktail_consumption_qty} {line.item.unit} 
    from cocktails (pending)
  </Badge>
  
  // Show merge button
  <Button onClick={() => mergeCocktails(line.id)}>
    Merge Cocktails
  </Button>
}
```

### Display Merged Cocktails
```javascript
if (line.merged_cocktail_consumption_qty > 0) {
  // Show green badge (informational only)
  <Badge color="success">
    {line.merged_cocktail_consumption_qty} {line.item.unit} 
    from cocktails (merged)
  </Badge>
}
```

### Merge Button Handler
```javascript
async function mergeCocktails(lineId) {
  const response = await POST(
    `/api/stock_tracker/{hotel}/stocktake-lines/${lineId}/merge-cocktail-consumption/`
  );
  
  // Show success message
  toast.success(`Merged ${response.merged_count} cocktail records`);
  
  // Refresh line data
  refreshStocktakeLine(lineId);
}
```

### Bulk Merge Button (Stocktake Header)
```javascript
async function mergeAllCocktails(stocktakeId) {
  const response = await POST(
    `/api/stock_tracker/{hotel}/stocktakes/${stocktakeId}/merge-all-cocktail-consumption/`
  );
  
  const { summary } = response;
  
  // Show detailed summary
  toast.success(
    `Merged ${summary.total_items_merged} consumption records ` +
    `across ${summary.lines_affected} items`
  );
  
  // Refresh entire stocktake
  refreshStocktake(stocktakeId);
}
```

---

## Important Notes

1. **Automatic Creation**: Ingredient consumptions are created automatically when cocktails are made
2. **Optional Linking**: Ingredients can optionally be linked to stock items via `linked_stock_item_id`
3. **Manual Merge Only**: Cocktail data NEVER automatically affects stocktake - requires button click
4. **No Double Merge**: System prevents merging already-merged consumptions
5. **Locked Stocktakes**: Cannot merge into approved/locked stocktakes
6. **Audit Trail**: All merges track who merged and when
7. **Display Fields**: Available/merged quantities are for display only - don't manually calculate

---

## Testing Checklist

- [ ] Create cocktail consumption → ingredient consumptions auto-created
- [ ] Link ingredient to stock item → `can_be_merged` becomes true
- [ ] Merge single line → purchases increase, variance updates
- [ ] Merge all → multiple lines updated, correct summary
- [ ] Try merging locked stocktake → gets error
- [ ] Try merging already-merged → gets error
- [ ] Check audit trail → merged_by, merged_at populated
