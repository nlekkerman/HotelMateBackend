# FRONTEND GUIDE: Getting Stocktake from Period

## Problem
`StockPeriod` and `Stocktake` are **separate models** with **different IDs**.

Example:
- September 2025 Period ID: **8**
- September 2025 Stocktake ID: **8** (coincidentally the same)
- October 2025 Period ID: **5**
- October 2025 Stocktake ID: **5** (coincidentally the same)

But IDs are **NOT guaranteed to match**!

## Solution: Get Stocktake by Date Range

### Method 1: Search Stocktakes by Period Dates (RECOMMENDED)

When you have a `StockPeriod`, use its dates to find the matching `Stocktake`:

```javascript
// Step 1: Get the Period
const periodResponse = await fetch(
  `/api/stock_tracker/hotel-killarney/periods/${periodId}/`
);
const period = await periodResponse.json();

// period.id = 8
// period.start_date = "2025-09-01"
// period.end_date = "2025-09-30"

// Step 2: Get ALL Stocktakes and filter by dates
const stocktakesResponse = await fetch(
  `/api/stock_tracker/hotel-killarney/stocktakes/`
);
const stocktakes = await stocktakesResponse.json();

// Step 3: Find matching stocktake by date range
const matchingStocktake = stocktakes.find(
  st => st.period_start === period.start_date && 
        st.period_end === period.end_date
);

if (matchingStocktake) {
  console.log(`Stocktake ID: ${matchingStocktake.id}`);
  console.log(`Status: ${matchingStocktake.status}`);
  console.log(`Total COGS: €${matchingStocktake.total_cogs}`);
  console.log(`Total Revenue: €${matchingStocktake.total_revenue}`);
  console.log(`GP%: ${matchingStocktake.gross_profit_percentage}%`);
} else {
  console.log('No stocktake found for this period');
}
```

### Method 2: Add Stocktake ID to Period Response (BACKEND MODIFICATION)

**Option A: Modify Period Serializer to include stocktake_id**

Add this to `stock_tracker/stock_serializers.py`:

```python
class StockPeriodSerializer(serializers.ModelSerializer):
    stocktake_id = serializers.SerializerMethodField()
    
    class Meta:
        model = StockPeriod
        fields = [
            'id',
            'period_name',
            'start_date',
            'end_date',
            'is_closed',
            'manual_purchases_amount',
            'manual_sales_amount',
            'stocktake_id',  # NEW FIELD
            # ... other fields
        ]
    
    def get_stocktake_id(self, obj):
        """Get the ID of the stocktake for this period"""
        try:
            stocktake = Stocktake.objects.get(
                hotel=obj.hotel,
                period_start=obj.start_date,
                period_end=obj.end_date
            )
            return stocktake.id
        except Stocktake.DoesNotExist:
            return None
```

Then frontend can directly access:

```javascript
const periodResponse = await fetch(
  `/api/stock_tracker/hotel-killarney/periods/${periodId}/`
);
const period = await periodResponse.json();

if (period.stocktake_id) {
  // Use the stocktake_id directly!
  const stocktakeResponse = await fetch(
    `/api/stock_tracker/hotel-killarney/stocktakes/${period.stocktake_id}/`
  );
  const stocktake = await stocktakeResponse.json();
}
```

### Method 3: Query Stocktakes with Date Parameters (BACKEND NEW ENDPOINT)

**Option B: Add query parameters to Stocktakes endpoint**

Modify `stock_tracker/views.py`:

```python
class StocktakeViewSet(viewsets.ModelViewSet):
    # ... existing code ...
    
    def get_queryset(self):
        queryset = Stocktake.objects.filter(hotel=hotel)
        
        # NEW: Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date and end_date:
            queryset = queryset.filter(
                period_start=start_date,
                period_end=end_date
            )
        
        return queryset
```

Then frontend can query:

```javascript
const period = await getPeriod(periodId);

// Query stocktake by date range
const response = await fetch(
  `/api/stock_tracker/hotel-killarney/stocktakes/` +
  `?start_date=${period.start_date}&end_date=${period.end_date}`
);
const stocktakes = await response.json();

if (stocktakes.length > 0) {
  const stocktake = stocktakes[0];
  console.log(`Found stocktake ID: ${stocktake.id}`);
}
```

## Real Examples

### September 2025
```javascript
// Period ID: 8
// Dates: 2025-09-01 to 2025-09-30
// Stocktake ID: 8

const period = await fetch('/api/stock_tracker/hotel-killarney/periods/8/');
// period.start_date = "2025-09-01"
// period.end_date = "2025-09-30"

// Find stocktake by dates
const stocktakes = await fetch('/api/stock_tracker/hotel-killarney/stocktakes/');
const sept = stocktakes.find(
  st => st.period_start === "2025-09-01" && st.period_end === "2025-09-30"
);
// sept.id = 8
```

### October 2025
```javascript
// Period ID: 5
// Dates: 2025-10-01 to 2025-10-31
// Stocktake ID: 5

const period = await fetch('/api/stock_tracker/hotel-killarney/periods/5/');
// period.start_date = "2025-10-01"
// period.end_date = "2025-10-31"

const stocktakes = await fetch('/api/stock_tracker/hotel-killarney/stocktakes/');
const oct = stocktakes.find(
  st => st.period_start === "2025-10-01" && st.period_end === "2025-10-31"
);
// oct.id = 5
```

## Recommendation

**Use Method 2 (Modify Period Serializer)** - It's the cleanest solution:

1. Modify the backend serializer once
2. Frontend gets `stocktake_id` directly in period response
3. No extra API calls needed
4. No date matching logic needed in frontend

## Important Notes

⚠️ **Period and Stocktake are separate!**
- A Period can exist WITHOUT a Stocktake
- A Stocktake is created when you perform a stock count
- Always check if `stocktake_id` is `null` before using it

✅ **Always match by dates, NOT by ID**
- IDs are auto-incremented and can differ
- Dates are the true link between Period and Stocktake
