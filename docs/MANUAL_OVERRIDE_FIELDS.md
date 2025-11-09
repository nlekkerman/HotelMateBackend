# Manual Override Fields for Stocktake

## Overview

Two optional fields have been added to `StocktakeLine` to allow manual entry of financial data when automatic calculation from stock movements is not available or desired.

## New Fields

### 1. `manual_purchases_value`
- **Type**: DecimalField (15 digits, 2 decimal places)
- **Purpose**: Manually enter total purchase value for an item during the stocktake period
- **Format**: Euro amount (e.g., 1250.50)
- **Optional**: Yes (null=True, blank=True)

### 2. `manual_sales_profit`
- **Type**: DecimalField (15 digits, 2 decimal places)
- **Purpose**: Manually enter profit from sales for an item during the stocktake period
- **Format**: Euro amount (e.g., 850.75)
- **Optional**: Yes (null=True, blank=True)

## API Usage

### Creating/Updating Stocktake Lines with Manual Values

**PATCH** `/api/stock_tracker/{hotel_id}/stocktake-lines/{line_id}/`

```json
{
  "counted_full_units": 5,
  "counted_partial_units": 3,
  "manual_purchases_value": "1250.50",
  "manual_sales_profit": "850.75"
}
```

### Example Response

```json
{
  "id": 123,
  "stocktake": 4,
  "item": 45,
  "item_sku": "S001",
  "item_name": "Jameson Whiskey 70cl",
  
  "opening_qty": "120.0000",
  "purchases": "80.0000",
  "sales": "150.0000",
  "waste": "0.0000",
  
  "manual_purchases_value": "1250.50",
  "manual_sales_profit": "850.75",
  
  "counted_full_units": "5.00",
  "counted_partial_units": "3.00",
  "counted_qty": "103.0000",
  "expected_qty": "50.0000",
  "variance_qty": "53.0000",
  
  "valuation_cost": "2.5000",
  "expected_value": "125.00",
  "counted_value": "257.50",
  "variance_value": "132.50"
}
```

## Use Cases

### 1. **No Detailed Movement Records**
When you don't have individual stock movement entries but have invoice totals:
```json
{
  "manual_purchases_value": "5600.00"
}
```

### 2. **Period-End Financial Summary**
When you have end-of-period reports showing profit:
```json
{
  "manual_sales_profit": "3200.50"
}
```

### 3. **Bulk Import from External Systems**
When importing data from POS or accounting systems that only provide totals:
```json
{
  "manual_purchases_value": "1250.50",
  "manual_sales_profit": "850.75"
}
```

### 4. **Mixed Data Entry**
Use automatic calculations for most items, manual entry for exceptions:
- Items with auto-calculated movements: Leave manual fields null
- Items with manual data: Populate manual fields as needed

## Important Notes

1. **Optional Fields**: These fields are completely optional - the system continues to work as before if they're not used
2. **No Automatic Calculation**: The system does NOT automatically populate these fields - they must be manually entered when needed
3. **Independent of Stock Movements**: These values are stored separately and don't affect the automatic purchase/sales calculations from `StockMovement` records
4. **Editable Until Approved**: Can be edited while stocktake status is 'DRAFT', locked after 'APPROVED'
5. **Display Only**: Currently these fields are for record-keeping; they don't affect variance calculations (which still use counted vs expected quantities)

## API Endpoints

- **List all stocktake lines**: `GET /api/stock_tracker/{hotel_id}/stocktake-lines/`
- **Get specific line**: `GET /api/stock_tracker/{hotel_id}/stocktake-lines/{line_id}/`
- **Update line**: `PATCH /api/stock_tracker/{hotel_id}/stocktake-lines/{line_id}/`
- **Filter by stocktake**: `GET /api/stock_tracker/{hotel_id}/stocktake-lines/?stocktake={stocktake_id}`

## Migration

Run the migration:
```bash
python manage.py migrate stock_tracker
```

This adds the two new optional columns to the `stock_tracker_stocktakeline` table.
