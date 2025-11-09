# FRONTEND GUIDE: How to Enter Manual Values for Stocktake

## Overview
When closing a stocktake period, you can manually enter total purchase costs and sales revenue instead of calculating item-by-item.

---

## API ENDPOINTS

### 1. Get Stocktake Details
```
GET /api/stock/{hotel_identifier}/stocktakes/{stocktake_id}/
```

**Response includes:**
```json
{
  "id": 5,
  "period_start": "2025-10-01",
  "period_end": "2025-10-31",
  "status": "DRAFT",
  "total_cogs": 19000.00,
  "total_revenue": 62000.00,
  "gross_profit_percentage": 69.35,
  "pour_cost_percentage": 30.65
}
```

---

### 2. Update Period with Manual Values
```
PATCH /api/stock/{hotel_identifier}/periods/{period_id}/
```

**Request Body:**
```json
{
  "manual_purchases_amount": "19000.00",
  "manual_sales_amount": "62000.00"
}
```

**Example:**
```javascript
// October 2025 Period ID: 7
const response = await fetch(
  '/api/stock/hotel-killarney/periods/7/',
  {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Token YOUR_TOKEN'
    },
    body: JSON.stringify({
      manual_purchases_amount: "19000.00",
      manual_sales_amount: "62000.00"
    })
  }
);
```

---

### 3. Approve/Close the Stocktake
```
POST /api/stock/{hotel_identifier}/stocktakes/{stocktake_id}/approve/
```

**Request Body:** (empty or optional notes)
```json
{
  "notes": "October 2025 - Manual values entered"
}
```

---

## WORKFLOW IN FRONTEND

### Step 1: Show Manual Values Form
When user clicks "Close Stocktake", show a modal/form with:

```jsx
<Form>
  <h3>Enter Period Totals</h3>
  
  <FormField>
    <label>Total Purchases (COGS)</label>
    <input 
      type="number" 
      step="0.01"
      name="manual_purchases_amount"
      placeholder="19000.00"
    />
    <span>Total cost of all purchases for this period</span>
  </FormField>
  
  <FormField>
    <label>Total Sales Revenue</label>
    <input 
      type="number" 
      step="0.01"
      name="manual_sales_amount"
      placeholder="62000.00"
    />
    <span>Total sales revenue for this period</span>
  </FormField>
  
  <Button type="submit">Save & Close Stocktake</Button>
</Form>
```

---

### Step 2: Submit Manual Values to Period
```javascript
const handleCloseStocktake = async (stocktake) => {
  // 1. Update period with manual values
  const periodResponse = await fetch(
    `/api/stock/${hotelSlug}/periods/${stocktake.period_id}/`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
      },
      body: JSON.stringify({
        manual_purchases_amount: formData.purchases,
        manual_sales_amount: formData.sales
      })
    }
  );
  
  if (!periodResponse.ok) {
    throw new Error('Failed to save manual values');
  }
  
  // 2. Approve the stocktake
  const approveResponse = await fetch(
    `/api/stock/${hotelSlug}/stocktakes/${stocktake.id}/approve/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
      },
      body: JSON.stringify({
        notes: 'Manual values entered'
      })
    }
  );
  
  if (approveResponse.ok) {
    // Success! Refresh stocktake data
    showSuccess('Stocktake closed successfully!');
    refreshStocktakeData();
  }
};
```

---

### Step 3: Display Results
After closing, show the calculated metrics:

```jsx
<StocktakeResults>
  <h3>October 2025 - Results</h3>
  
  <MetricCard>
    <label>Total COGS</label>
    <value>€19,000.00</value>
  </MetricCard>
  
  <MetricCard>
    <label>Total Revenue</label>
    <value>€62,000.00</value>
  </MetricCard>
  
  <MetricCard>
    <label>Gross Profit</label>
    <value>€43,000.00</value>
  </MetricCard>
  
  <MetricCard highlight>
    <label>Gross Profit %</label>
    <value>69.35%</value>
  </MetricCard>
  
  <MetricCard>
    <label>Pour Cost %</label>
    <value>30.65%</value>
  </MetricCard>
</StocktakeResults>
```

---

## CALCULATION PRIORITY

The system automatically uses manual values if present:

### For COGS (Cost of Goods Sold):
1. **StockPeriod.manual_purchases_amount** ← Use this (€19,000)
2. Sum of StocktakeLine.manual_purchases_value + manual_waste_value
3. Sum of Sale records (auto-calculated)

### For Revenue:
1. Sum of StocktakeLine.manual_sales_value
2. **StockPeriod.manual_sales_amount** ← Use this (€62,000)
3. Sum of Sale records (auto-calculated)

---

## COMPLETE EXAMPLE

```javascript
// Complete workflow
const closeStocktakeWithManualValues = async () => {
  try {
    // Get stocktake details
    const stocktake = await getStocktake(stocktakeId);
    
    // Find the period for this stocktake
    const period = await getPeriodByDates(
      stocktake.period_start,
      stocktake.period_end
    );
    
    // Update period with manual values
    await updatePeriod(period.id, {
      manual_purchases_amount: "19000.00",
      manual_sales_amount: "62000.00"
    });
    
    // Approve stocktake
    await approveStocktake(stocktake.id);
    
    // Refresh to get calculated metrics
    const updatedStocktake = await getStocktake(stocktakeId);
    
    console.log('Results:', {
      cogs: updatedStocktake.total_cogs,
      revenue: updatedStocktake.total_revenue,
      gp_percent: updatedStocktake.gross_profit_percentage
    });
    
  } catch (error) {
    console.error('Error closing stocktake:', error);
  }
};
```

---

## TESTING

You can test with October 2025:
- **Stocktake ID**: 5
- **Period ID**: 7
- **Hotel**: Hotel Killarney
- **Status**: Currently DRAFT (reopened for testing)

Try these values:
- Manual Purchases: €19,000.00
- Manual Sales: €62,000.00
- Expected GP%: 69.35%

---

## NOTES

- Both fields are **optional** - leave empty to use auto-calculated values
- Values are in **Decimal** format (max 12 digits, 2 decimal places)
- Once stocktake is APPROVED, it's locked (must reopen to edit)
- Manual values override any item-by-item calculations
