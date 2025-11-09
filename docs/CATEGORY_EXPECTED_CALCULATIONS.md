# Category-Level Expected Quantity Calculations

## Overview

You can now calculate the **expected quantity** (using the full formula) for entire categories instead of just individual items. This sums up all items in a category to give you category-level totals.

## The Formula

```
expected_qty = opening + purchases + transfers_in - sales - waste - transfers_out + adjustments
```

This formula is applied to **all items in a category** and totaled.

---

## API Usage

### Get All Categories

**Endpoint:** `GET /api/stock_tracker/{hotel_id}/stocktakes/{stocktake_id}/category_totals/`

**Example:**
```bash
GET /api/stock_tracker/1/stocktakes/4/category_totals/
```

**Response:**
```json
{
  "D": {
    "category_code": "D",
    "category_name": "Draught Beer",
    "opening_qty": "1250.0000",
    "purchases": "500.0000",
    "sales": "800.0000",
    "waste": "25.0000",
    "transfers_in": "0.0000",
    "transfers_out": "0.0000",
    "adjustments": "0.0000",
    "expected_qty": "925.0000",
    "counted_qty": "920.0000",
    "variance_qty": "-5.0000",
    "expected_value": "2312.50",
    "counted_value": "2300.00",
    "variance_value": "-12.50",
    "manual_purchases_value": "0.00",
    "manual_sales_profit": "0.00",
    "item_count": 15
  },
  "B": {
    "category_code": "B",
    "category_name": "Bottled Beer",
    ...
  },
  "S": {
    "category_code": "S",
    "category_name": "Spirits",
    ...
  }
}
```

### Get Single Category

**Endpoint:** `GET /api/stock_tracker/{hotel_id}/stocktakes/{stocktake_id}/category_totals/?category=D`

**Example:**
```bash
GET /api/stock_tracker/1/stocktakes/4/category_totals/?category=S
```

**Response:**
```json
{
  "category_code": "S",
  "category_name": "Spirits",
  "opening_qty": "5240.0000",
  "purchases": "800.0000",
  "sales": "3200.0000",
  "waste": "40.0000",
  "transfers_in": "0.0000",
  "transfers_out": "100.0000",
  "adjustments": "0.0000",
  "expected_qty": "2700.0000",
  "counted_qty": "2680.0000",
  "variance_qty": "-20.0000",
  "expected_value": "6750.00",
  "counted_value": "6700.00",
  "variance_value": "-50.00",
  "manual_purchases_value": "1250.50",
  "manual_sales_profit": "850.75",
  "item_count": 45
}
```

---

## Python/Django Usage

### Using the Model Method

```python
from stock_tracker.models import Stocktake

# Get stocktake
stocktake = Stocktake.objects.get(id=4)

# Get all category totals
all_categories = stocktake.get_category_totals()

# Display all categories
for category_code, totals in all_categories.items():
    print(f"{category_code}: {totals['category_name']}")
    print(f"  Expected: {totals['expected_qty']} servings")
    print(f"  Counted: {totals['counted_qty']} servings")
    print(f"  Variance: {totals['variance_qty']} servings")
    print()

# Get specific category (e.g., Spirits)
spirits_totals = stocktake.get_category_totals(category_code='S')
if spirits_totals:
    print(f"Spirits Category:")
    print(f"  Opening: {spirits_totals['opening_qty']}")
    print(f"  + Purchases: {spirits_totals['purchases']}")
    print(f"  + Transfers In: {spirits_totals['transfers_in']}")
    print(f"  - Sales: {spirits_totals['sales']}")
    print(f"  - Waste: {spirits_totals['waste']}")
    print(f"  - Transfers Out: {spirits_totals['transfers_out']}")
    print(f"  + Adjustments: {spirits_totals['adjustments']}")
    print(f"  = Expected: {spirits_totals['expected_qty']}")
```

### Using the Helper Script

```bash
# Show all categories
python calculate_category_expected.py 4

# Show specific category
python calculate_category_expected.py 4 D  # Draught
python calculate_category_expected.py 4 S  # Spirits
python calculate_category_expected.py 4 W  # Wine
```

**Output Example:**
```
================================================================================
CATEGORY: S - Spirits
Items: 45
================================================================================

QUANTITY BREAKDOWN (in servings):
--------------------------------------------------------------------------------
  Opening Stock:              5,240.0000
  + Purchases:                  800.0000
  + Transfers In:                 0.0000
  - Sales:                    3,200.0000
  - Waste:                       40.0000
  - Transfers Out:              100.0000
  + Adjustments:                  0.0000
--------------------------------------------------------------------------------
  = EXPECTED:                 2,700.0000
  Counted:                    2,680.0000
  Variance:                     -20.0000

VALUE BREAKDOWN (in €):
--------------------------------------------------------------------------------
  Expected Value:          € 6,750.00
  Counted Value:           € 6,700.00
  Variance Value:          €   -50.00

Variance: -0.74%
```

---

## Frontend Implementation

### Display Category Totals

```typescript
// Fetch category totals
const fetchCategoryTotals = async (hotelId: string, stocktakeId: number) => {
  const response = await fetch(
    `/api/stock_tracker/${hotelId}/stocktakes/${stocktakeId}/category_totals/`
  );
  return response.json();
};

// Usage
const CategorySummary: React.FC<{ stocktakeId: number }> = ({ stocktakeId }) => {
  const [totals, setTotals] = useState<any>(null);

  useEffect(() => {
    fetchCategoryTotals('1', stocktakeId).then(setTotals);
  }, [stocktakeId]);

  if (!totals) return <div>Loading...</div>;

  return (
    <div className="category-summary">
      <h2>Stocktake Summary by Category</h2>
      
      {Object.entries(totals).map(([code, data]: [string, any]) => (
        <div key={code} className="category-card">
          <h3>{data.category_name}</h3>
          <div className="totals">
            <div>Opening: {data.opening_qty}</div>
            <div>Purchases: +{data.purchases}</div>
            <div>Sales: -{data.sales}</div>
            <div>Waste: -{data.waste}</div>
            <div className="expected">Expected: {data.expected_qty}</div>
            <div className="counted">Counted: {data.counted_qty}</div>
            <div className={`variance ${data.variance_qty < 0 ? 'negative' : 'positive'}`}>
              Variance: {data.variance_qty}
            </div>
          </div>
          <div className="values">
            <span>Expected: €{data.expected_value}</span>
            <span>Variance: €{data.variance_value}</span>
          </div>
        </div>
      ))}
    </div>
  );
};
```

### Fetch Single Category

```typescript
const fetchSingleCategory = async (
  hotelId: string,
  stocktakeId: number,
  categoryCode: string
) => {
  const response = await fetch(
    `/api/stock_tracker/${hotelId}/stocktakes/${stocktakeId}/category_totals/?category=${categoryCode}`
  );
  return response.json();
};

// Usage
const spiritsTotals = await fetchSingleCategory('1', 4, 'S');
console.log('Spirits expected:', spiritsTotals.expected_qty);
```

---

## Data Structure

### CategoryTotals Object

```typescript
interface CategoryTotals {
  category_code: string;        // "D", "B", "S", "W", "M"
  category_name: string;        // "Draught Beer", "Spirits", etc.
  
  // Movement totals (all in servings)
  opening_qty: string;          // "1250.0000"
  purchases: string;            // "500.0000"
  sales: string;                // "800.0000"
  waste: string;                // "25.0000"
  transfers_in: string;         // "0.0000"
  transfers_out: string;        // "0.0000"
  adjustments: string;          // "0.0000"
  
  // Calculated totals
  expected_qty: string;         // Formula result: "925.0000"
  counted_qty: string;          // User counted: "920.0000"
  variance_qty: string;         // Difference: "-5.0000"
  
  // Monetary values
  expected_value: string;       // "2312.50"
  counted_value: string;        // "2300.00"
  variance_value: string;       // "-12.50"
  
  // Manual overrides (if any)
  manual_purchases_value: string;  // "0.00" or actual value
  manual_sales_profit: string;     // "0.00" or actual value
  
  // Item count
  item_count: number;           // 15
}
```

---

## Use Cases

### 1. **Category Performance Dashboard**
Show how each category is performing in terms of variance

### 2. **Waste Analysis**
Compare waste across categories:
```python
categories = stocktake.get_category_totals()
for code, data in categories.items():
    waste_pct = (data['waste'] / data['opening_qty']) * 100
    print(f"{data['category_name']}: {waste_pct:.2f}% waste")
```

### 3. **High-Level Reports**
Generate management reports showing category-level summaries instead of item-level details

### 4. **Variance Alerts**
Identify categories with significant variances:
```python
categories = stocktake.get_category_totals()
for code, data in categories.items():
    if abs(data['variance_value']) > 100:  # Over €100 variance
        print(f"⚠️ {data['category_name']}: €{data['variance_value']} variance")
```

---

## Notes

- All quantities are in **servings** (base units)
- The formula accounts for all movements during the period
- Manual override values are also totaled at category level
- Category codes: **D**=Draught, **B**=Bottled, **S**=Spirits, **W**=Wine, **M**=Mixers

---

## See Also

- Individual item calculations: `StocktakeLine.expected_qty` property
- API documentation: `docs/MANUAL_OVERRIDE_FIELDS.md`
- Frontend guide: `docs/FRONTEND_MANUAL_OVERRIDE_IMPLEMENTATION.md`
