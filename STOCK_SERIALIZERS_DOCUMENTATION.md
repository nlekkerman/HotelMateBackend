# Stock Tracker Serializers Documentation

Complete reference for all serializers in the stock tracking system. The serializers are organized across three files based on functionality.

---

## File Structure

```
stock_tracker/
├── stock_serializers.py         # Core stock tracking serializers
├── comparison_serializers.py    # Period comparison & analytics
└── cocktail_serializers.py      # Cocktail tracking serializers
```

---

## 1. Core Stock Serializers (`stock_serializers.py`)

### 1.1 StockCategorySerializer
**Purpose**: Serialize stock categories (D=Draught, B=Bottled Beer, S=Spirits, W=Wine, M=Minerals)

**Fields**:
- `code` (read-only): Single letter category code
- `name` (read-only): Category name
- `item_count`: Number of items in category

**Use Cases**:
- Category dropdowns in UI
- Category filtering
- Dashboard statistics

---

### 1.2 LocationSerializer
**Purpose**: Serialize physical storage locations (Bar, Cellar, Storage, etc.)

**Fields**:
- `id`: Location ID
- `hotel` (read-only): Hotel FK
- `name`: Location name
- `active`: Whether location is in use

**Use Cases**:
- Location management
- Bin/shelf organization
- Stock placement tracking

---

### 1.3 StockSnapshotNestedSerializer
**Purpose**: Detailed snapshot data for period views with opening/closing stock comparison

**Key Features**:
- Displays both opening stock (from previous period) and closing stock
- Category-specific display formatting (kegs+pints, cases+bottles, bottles+fractional)
- Profitability metrics (GP%, markup%, pour cost%)

**Fields**:
- `item`: Item details (SKU, name, category, size, costs)
- **Opening Stock** (from previous period's closing):
  - `opening_full_units`: Kegs/cases/bottles at period start
  - `opening_partial_units`: Pints/bottles/fractional at period start
  - `opening_stock_value`: Value at period start
  - `opening_display_full_units`: Display format (kegs/cases)
  - `opening_display_partial_units`: Display format (pints/bottles)
- **Closing Stock** (counted at period end):
  - `closing_full_units`: Raw full units
  - `closing_partial_units`: Raw partial units  
  - `closing_stock_value`: Total value
  - `closing_display_full_units`: Display format
  - `closing_display_partial_units`: Display format
- **Costing**:
  - `unit_cost`: Cost per full unit (keg/case/bottle)
  - `cost_per_serving`: Cost per serving (pint/bottle/shot)
- **Profitability**:
  - `gp_percentage`: Gross profit %
  - `markup_percentage`: Markup %
  - `pour_cost_percentage`: Pour cost %

**Display Logic**:
- **Draught (D)**: kegs + pints
- **Bottled Beer (Doz)**: cases + bottles (0-11)
- **Spirits/Wine**: bottles + fractional (0.00-0.99)

---

### 1.4 StockPeriodSerializer
**Purpose**: List view serializer for stock periods with basic info

**Fields**:
- `id`, `hotel`, `period_type`, `start_date`, `end_date`
- `year`, `month`, `quarter`, `week`, `period_name`
- `is_closed`, `closed_at`, `closed_by`, `closed_by_name`
- `reopened_at`, `reopened_by`, `reopened_by_name`
- `manual_sales_amount`: Manual total sales entry
- `manual_purchases_amount`: Manual total COGS entry
- `stocktake_id`: Related stocktake ID (if exists)
- `stocktake`: Detailed stocktake info
- `can_reopen`: User permission to reopen period
- `can_manage_permissions`: User permission to grant reopen rights

**Stocktake Info** (nested):
```python
{
    'id': 18,
    'status': 'DRAFT',
    'total_lines': 250,
    'lines_counted': 245,
    'lines_at_zero': 5,
    'total_cogs': 12500.50,
    'total_revenue': 45000.00,
    'gross_profit_percentage': 72.22,
    'pour_cost_percentage': 27.78,
    'approved_at': None,
    'notes': ''
}
```

**Use Cases**:
- Period list view
- Period selection dropdowns
- Quick period stats

---

### 1.5 StockPeriodDetailSerializer
**Purpose**: Complete period data with all snapshots for detailed analysis

**Extends**: StockPeriodSerializer

**Additional Fields**:
- `snapshots`: Full snapshot data for all items (StockSnapshotNestedSerializer)
- `snapshot_ids`: List of snapshot IDs
- `stocktake_id`: Related stocktake
- `stocktake_status`: DRAFT or APPROVED
- `total_items`: Item count
- `total_value`: Total stock value

**Use Cases**:
- Period detail page
- Opening/closing stock comparison
- Complete period analysis

---

### 1.6 StockItemSerializer
**Purpose**: Serialize stock items with profitability calculations

**Fields**:
- **Identification**: `id`, `hotel`, `sku`, `name`
- **Category**: `category`, `category_code`, `category_name`
- **Size**: `size`, `size_value`, `size_unit`, `uom`
- **Costing**: `unit_cost`
- **Current Stock**: 
  - `current_full_units`: Kegs/cases/bottles
  - `current_partial_units`: Pints/bottles/fractional
- **Pricing**: 
  - `menu_price`: Standard serving price
  - `menu_price_large`: Large serving price
  - `bottle_price`: Whole bottle price
  - `promo_price`: Promotional price
- **Flags**: `available_on_menu`, `available_by_bottle`, `active`
- **Calculated Fields**:
  - `total_stock_in_servings`: Total servings available
  - `total_stock_value`: Value at cost
  - `cost_per_serving`: Unit economics
  - `gross_profit_per_serving`: Profit per serving
  - `gross_profit_percentage`: GP%
  - `markup_percentage`: Markup%
  - `pour_cost_percentage`: Pour cost%
- **Display Helpers**:
  - `display_full_units`: UI-friendly full units
  - `display_partial_units`: UI-friendly partial units

**Use Cases**:
- Item management
- Pricing setup
- Profitability analysis
- Inventory views

---

### 1.7 StockSnapshotSerializer
**Purpose**: Simple snapshot serializer for basic snapshot views

**Fields**:
- `id`, `hotel`, `item`, `item_sku`, `item_name`
- `category_code`, `period`, `period_name`
- `closing_full_units`, `closing_partial_units`, `total_servings`
- `display_full_units`, `display_partial_units`
- `unit_cost`, `cost_per_serving`, `closing_stock_value`
- `gp_percentage`, `markup_percentage`, `pour_cost_percentage`
- `created_at`

**Use Cases**:
- Snapshot lists
- Simple period views
- Historical stock queries

---

### 1.8 StockMovementSerializer
**Purpose**: Track stock movements (purchases, waste, transfers, adjustments)

**Movement Types**:
- `PURCHASE`: Deliveries/purchases
- `SALE`: Sales/consumption
- `WASTE`: Breakage/spoilage
- `TRANSFER_IN`: Received from another location
- `TRANSFER_OUT`: Sent to another location
- `ADJUSTMENT`: Stocktake corrections
- `COCKTAIL_CONSUMPTION`: Merged cocktail usage

**Fields**:
- `id`, `hotel`, `item`, `item_sku`, `item_name`
- `period`: Period this movement belongs to
- `movement_type`: Type of movement
- `quantity`: Quantity in servings
- `unit_cost`: Cost per serving
- `reference`: Invoice number, etc.
- `notes`: Additional info
- `staff`, `staff_name`: Who made the movement
- `timestamp`: When it occurred

**Use Cases**:
- Movement tracking
- Purchase logging
- Waste management
- Audit trails

---

### 1.9 StocktakeLineSerializer
**Purpose**: Individual line in stocktake with counted vs expected comparison

**Key Features**:
- Display conversions (kegs+pints, cases+bottles, bottles+fractional)
- Variance calculations
- Manual override support
- Cocktail consumption tracking (display only)

**Fields**:

**Identification**:
- `id`, `stocktake`, `item`, `item_sku`, `item_name`
- `category_code`, `category_name`
- `item_size`, `item_uom`

**Cost Breakdown**:
- `case_cost`: Cost per case (for Doz items)
- `bottle_cost`: Cost per bottle (for spirits)

**Raw Quantities** (in servings):
- `opening_qty`: Opening stock
- `purchases`: Purchases in period
- `sales_qty`: Sales (calculated from Sale records)
- `waste`: Waste/breakage
- `transfers_in`, `transfers_out`: Transfers
- `adjustments`: Previous adjustments

**Manual Overrides**:
- `manual_purchases_value`: €€€ total purchases
- `manual_waste_value`: €€€ total waste
- `manual_sales_value`: €€€ total sales revenue

**Counted Stock**:
- `counted_full_units`: Full units counted
- `counted_partial_units`: Partial units counted
- `counted_qty`: Total servings (calculated)

**Calculated Values**:
- `expected_qty`: Opening + purchases - waste
- `variance_qty`: Counted - expected
- `expected_value`: Expected stock value
- `counted_value`: Counted stock value (Stock at Cost in Excel)
- `variance_value`: Variance in €€€

**Display Fields** (UI-friendly format):
- Opening: `opening_display_full_units`, `opening_display_partial_units`
- Expected: `expected_display_full_units`, `expected_display_partial_units`
- Counted: `counted_display_full_units`, `counted_display_partial_units`
- Variance: `variance_display_full_units`, `variance_display_partial_units`

**Cocktail Consumption** (DISPLAY ONLY - does NOT affect stocktake):
- `available_cocktail_consumption_qty`: Unmerged cocktail usage
- `merged_cocktail_consumption_qty`: Already merged usage
- `available_cocktail_consumption_value`: Value of unmerged
- `merged_cocktail_consumption_value`: Value of merged
- `can_merge_cocktails`: True if unmerged consumption exists

**Display Logic**:
```python
# Draught (D)
opening_display_full_units = "6"      # kegs
opening_display_partial_units = "39.75"  # pints

# Bottled Beer (Doz)
counted_display_full_units = "12"     # cases
counted_display_partial_units = "7"   # bottles (0-11)

# Spirits (S)
counted_display_full_units = "2"      # bottles
counted_display_partial_units = "0.30" # fractional bottle (0.00-0.99)
```

**Use Cases**:
- Stocktake counting interface
- Variance reporting
- Stock valuation
- Period closing

---

### 1.10 StocktakeSerializer
**Purpose**: Complete stocktake with all lines, snapshots, and summary data

**Fields**:

**Basic Info**:
- `id`, `hotel`, `period_start`, `period_end`
- `status`: DRAFT or APPROVED
- `is_locked`: Read-only, true if approved
- `created_at`, `approved_at`, `approved_by`, `approved_by_name`
- `notes`

**Period Connection**:
- `period_id`: Related StockPeriod ID
- `period_name`: Period display name
- `period_is_closed`: Whether period is closed

**Snapshot Data** (opening/closing stock for all items):
- `snapshots`: Complete snapshot data
- `snapshot_ids`: List of IDs

**Stocktake Lines** (counted data):
- `lines`: All StocktakeLine records
- `total_lines`: Line count

**Summary**:
- `total_items`: Item count
- `total_value`: Expected stock value
- `total_counted_value`: Counted stock value (Stock at Cost)
- `total_variance_value`: Total variance

**Profitability**:
- `total_cogs`: Cost of goods sold
- `total_revenue`: Sales revenue
- `gross_profit_percentage`: GP%
- `pour_cost_percentage`: Pour cost%

**COGS Calculation Priority**:
1. `StockPeriod.manual_purchases_amount` (single total)
2. Sum of `manual_purchases_value` + `manual_waste_value` from lines
3. Sum of `total_cost` from Sale records

**Revenue Calculation Priority**:
1. Sum of `manual_sales_value` from lines
2. `StockPeriod.manual_sales_amount`
3. Sum of `total_revenue` from Sale records

**Use Cases**:
- Stocktake detail page
- Period closing
- Financial reporting
- Variance analysis

---

### 1.11 StocktakeListSerializer
**Purpose**: Lightweight serializer for stocktake list views

**Fields**:
- `id`, `hotel`, `period_start`, `period_end`
- `status`, `is_locked`, `created_at`, `total_lines`

**Use Cases**:
- Stocktake list
- Quick navigation
- Status overview

---

### 1.12 SaleSerializer
**Purpose**: Track individual sales/consumption records

**Key Features**:
- Auto-populates `unit_cost` and `unit_price` from StockItem
- Calculates totals automatically
- Can be linked to stocktake or standalone

**Fields**:
- `id`, `stocktake`, `stocktake_period`, `item`
- `item_sku`, `item_name`, `category_code`, `category_name`
- `quantity`: Servings sold
- `unit_cost`: Cost per serving (auto-populated)
- `unit_price`: Selling price (auto-populated)
- `total_cost`: COGS (auto-calculated)
- `total_revenue`: Revenue (auto-calculated)
- `gross_profit`: Profit (calculated property)
- `gross_profit_percentage`: GP% (calculated property)
- `pour_cost_percentage`: Pour cost% (calculated property)
- `sale_date`: When sale occurred
- `notes`, `created_by`, `created_by_name`
- `created_at`, `updated_at`

**Auto-Population**:
```python
# On create, if not provided:
unit_cost = item.cost_per_serving
unit_price = item.menu_price
total_cost = unit_cost * quantity
total_revenue = unit_price * quantity
```

**Use Cases**:
- Sales tracking
- COGS calculation
- Revenue tracking
- Profitability analysis

---

### 1.13 PeriodReopenPermissionSerializer
**Purpose**: Manage permissions for reopening closed periods

**Fields**:
- `id`, `hotel`, `staff`, `staff_id`, `staff_name`, `staff_email`
- `granted_by`, `granted_by_name`, `granted_at`
- `is_active`: Permission status
- `can_grant_to_others`: Can grant to other staff (manager)
- `notes`

**Permission Levels**:
1. **Superuser**: Can always reopen, grant, and revoke
2. **Manager** (`can_grant_to_others=True`): Can reopen and grant to others
3. **Staff** (basic permission): Can reopen only

**Use Cases**:
- Period reopening control
- Permission management
- Audit compliance

---

### 1.14 SalesAnalysisSerializer
**Purpose**: Combined sales analysis for stock items + cocktails

**Important**: FOR ANALYSIS/REPORTING ONLY - does not modify data

**Structure**:
```python
{
    'period_id': 5,
    'period_name': 'October 2025',
    'period_start': '2025-10-01',
    'period_end': '2025-10-31',
    'period_is_closed': True,
    
    'general_sales': {
        'revenue': 45000.00,
        'cost': 12500.50,
        'count': 2500,
        'profit': 32499.50,
        'gp_percentage': 72.22
    },
    
    'cocktail_sales': {
        'revenue': 8500.00,
        'cost': 2100.00,
        'count': 350,
        'profit': 6400.00,
        'gp_percentage': 75.29
    },
    
    'combined_sales': {
        'total_revenue': 53500.00,
        'total_cost': 14600.50,
        'total_count': 2850,
        'profit': 38899.50,
        'gp_percentage': 72.71
    },
    
    'breakdown_percentages': {
        'stock_revenue_percentage': 84.11,
        'cocktail_revenue_percentage': 15.89,
        'stock_cost_percentage': 85.62,
        'cocktail_cost_percentage': 14.38
    },
    
    'category_breakdown': [
        {
            'code': 'D',
            'name': 'Draught Beer',
            'revenue': 15000.00,
            'cost': 3750.00,
            'count': 1200,
            'gp_percentage': 75.00
        },
        # ... other categories
        {
            'code': 'COCKTAILS',
            'name': 'Cocktails',
            'revenue': 8500.00,
            'cost': 2100.00,
            'count': 350,
            'gp_percentage': 75.29
        }
    ]
}
```

**Use Cases**:
- Period financial analysis
- Revenue breakdown
- Stock vs cocktail comparison
- Business intelligence dashboards

---

## 2. Comparison Serializers (`comparison_serializers.py`)

These serializers support period comparison and trend analysis endpoints.

### 2.1 CategoryComparisonSerializer
**Purpose**: Compare categories between two periods

**Fields**:
- `code`: Category code (D, B, S, W, M)
- `name`: Category name
- `period1`: Period 1 data (value, servings, etc.)
- `period2`: Period 2 data
- `change`: Absolute and percentage changes

### 2.2 CategoryComparisonResponseSerializer
**Purpose**: Full response for category comparison

**Fields**:
- `period1`: Period 1 info
- `period2`: Period 2 info
- `categories`: CategoryComparisonSerializer list
- `summary`: Overall comparison summary

### 2.3 TopMoverItemSerializer
**Purpose**: Items with biggest changes between periods

**Fields**:
- `item_id`, `sku`, `name`, `category`
- `period1_value`, `period2_value`
- `absolute_change`, `percentage_change`
- `reason`: Why it changed

### 2.4 TopMoversResponseSerializer
**Purpose**: Complete top movers analysis

**Fields**:
- `biggest_increases`: Top increasing items
- `biggest_decreases`: Top decreasing items
- `new_items`: Items added in period 2
- `discontinued_items`: Items removed in period 2

### 2.5 CostAnalysisResponseSerializer
**Purpose**: Cost structure analysis between periods

**Fields**:
- `period1`: Period 1 cost breakdown
- `period2`: Period 2 cost breakdown
- `comparison`: Side-by-side comparison
- `waterfall_data`: Waterfall chart data

### 2.6 TrendDataPointSerializer
**Purpose**: Single data point in trend analysis

**Fields**:
- `period_id`: Period identifier
- `value`: Stock value
- `servings`: Quantity
- `waste`: Waste amount

### 2.7 TrendItemSerializer
**Purpose**: Item trend over multiple periods

**Fields**:
- `item_id`, `sku`, `name`, `category`
- `trend_data`: TrendDataPointSerializer list
- `trend_direction`: UP, DOWN, STABLE
- `average_value`: Average across periods
- `volatility`: HIGH, MEDIUM, LOW

### 2.8 TrendAnalysisResponseSerializer
**Purpose**: Complete trend analysis

**Fields**:
- `periods`: Period list with details
- `items`: TrendItemSerializer list

### 2.9 VarianceHeatmapResponseSerializer
**Purpose**: Variance heatmap visualization data

**Fields**:
- `periods`: Period names
- `categories`: Category codes
- `heatmap_data`: 2D array of variance values
- `color_scale`: Color mapping for visualization

### 2.10 PerformanceMetricSerializer
**Purpose**: Individual performance metric

**Fields**:
- `name`: Metric name
- `period1_score`: Score (0-100)
- `period2_score`: Score (0-100)
- `weight`: Importance weight
- `status`: IMPROVED, DECLINED, STABLE

### 2.11 PerformanceScorecardResponseSerializer
**Purpose**: Complete performance scorecard

**Fields**:
- `overall_score`: Weighted average scores
- `metrics`: PerformanceMetricSerializer list
- `radar_chart_data`: Radar chart visualization data

---

## 3. Cocktail Serializers (`cocktail_serializers.py`)

### 3.1 IngredientSerializer
**Purpose**: Serialize cocktail ingredients

**Fields**:
- `id`, `name`, `unit`
- `hotel_id`: Hotel FK (write-only)
- `linked_stock_item_id`: Optional stock item link (write-only)
- `linked_stock_item`: Stock item details (read-only)

**Stock Item Link** (optional):
```python
{
    'id': 42,
    'sku': 'S0610',
    'name': 'Smirnoff 1Ltr'
}
```

**Use Cases**:
- Ingredient management
- Recipe creation
- Stock linkage for consumption tracking

---

### 3.2 RecipeIngredientSerializer
**Purpose**: Link ingredients to recipes with quantities

**Fields**:
- `id`
- `ingredient`: Full ingredient details (read-only)
- `ingredient_id`: Ingredient FK (write-only)
- `quantity_per_cocktail`: Amount needed per cocktail

**Use Cases**:
- Recipe composition
- Ingredient usage calculation
- Cost calculation

---

### 3.3 CocktailRecipeSerializer
**Purpose**: Complete cocktail recipe with ingredients

**Fields**:
- `id`, `name`, `price`
- `hotel_id`: Hotel FK (write-only)
- `ingredients`: RecipeIngredientSerializer list

**Use Cases**:
- Recipe management
- Menu pricing
- Ingredient planning

---

### 3.4 CocktailConsumptionSerializer
**Purpose**: Track cocktail production batches

**Key Features**:
- Auto-creates CocktailIngredientConsumption records on save
- Calculates revenue and cost
- Links to stock items (if configured)

**Fields**:
- `id`, `cocktail`, `cocktail_id`
- `quantity_made`: Number of cocktails produced
- `timestamp`: When made
- `unit_price`: Price per cocktail (auto-populated from recipe)
- `total_revenue`: Revenue (auto-calculated)
- `total_cost`: Ingredient cost (auto-calculated)
- `profit`: Profit (calculated property)
- `total_ingredient_usage`: Ingredient breakdown
- `ingredient_consumptions`: CocktailIngredientConsumption records

**Auto-Creation Flow**:
```python
# When you create a CocktailConsumption:
consumption = CocktailConsumption.objects.create(
    cocktail=mojito_recipe,
    quantity_made=50  # Made 50 mojitos
)

# Automatically creates CocktailIngredientConsumption for each ingredient:
# - 50 × 50ml rum = 2500ml rum consumed
# - 50 × 20ml lime juice = 1000ml lime juice consumed
# - etc.
```

**Use Cases**:
- Batch production tracking
- Ingredient depletion
- Revenue tracking
- Optional merging into stocktake

---

### 3.5 CocktailIngredientConsumptionSerializer
**Purpose**: Individual ingredient consumption from cocktails

**CRITICAL**: This is COMPLETELY SEPARATE from stocktake logic

**Purpose**:
- Track which ingredients were used
- Link to stock items (optional)
- Enable manual merging into stocktake (via explicit user action)

**Fields**:
- **Cocktail Info**:
  - `cocktail_consumption_id`
  - `cocktail_name`
  - `quantity_made`: Number of cocktails in batch
- **Ingredient Info**:
  - `ingredient`, `ingredient_name`
  - `quantity_used`: Total amount consumed
  - `unit`: Unit of measurement
- **Stock Item Link** (optional):
  - `stock_item`, `stock_item_sku`, `stock_item_name`
- **Cost Tracking**:
  - `unit_cost`: Cost per unit (optional)
  - `total_cost`: Total cost (optional)
- **Merge Tracking**:
  - `is_merged_to_stocktake`: Has been merged
  - `merged_at`: When merged
  - `merged_by`, `merged_by_name`: Who merged
  - `stocktake_id`: Which stocktake
  - `can_be_merged`: Can be merged now
- **Metadata**:
  - `timestamp`: When recorded

**Merge Flow**:
```python
# 1. Cocktail consumption creates ingredient records
consumption = CocktailConsumption.objects.create(...)
# Creates CocktailIngredientConsumption records automatically

# 2. Optional: User manually merges into stocktake
ingredient_consumption.merge_to_stocktake(
    stocktake=october_stocktake,
    staff=current_staff
)
# Sets is_merged_to_stocktake=True

# 3. Prevents double-counting
# Once merged, cannot be merged again
```

**Use Cases**:
- Display cocktail ingredient usage
- Optional manual merging into stocktake
- Cost tracking for cocktails
- Prevent double-counting

---

## Common Patterns

### Display Unit Conversion

All serializers handle category-specific display formatting:

```python
# Draught (D)
{
    'display_full_units': '6',      # kegs
    'display_partial_units': '39.75' # pints (2 decimals)
}

# Bottled Beer with Doz
{
    'display_full_units': '12',     # cases
    'display_partial_units': '7'    # bottles (0-11, integer)
}

# Spirits (S)
{
    'display_full_units': '2',      # bottles
    'display_partial_units': '0.30' # fractional (2 decimals)
}
```

### Auto-Calculation

Many serializers auto-calculate values on `create()`:

```python
# SaleSerializer
def create(self, validated_data):
    item = validated_data['item']
    
    # Auto-populate if not provided
    if 'unit_cost' not in validated_data:
        validated_data['unit_cost'] = item.cost_per_serving
    
    if 'unit_price' not in validated_data:
        validated_data['unit_price'] = item.menu_price
    
    # Calculate totals
    validated_data['total_cost'] = (
        validated_data['unit_cost'] * validated_data['quantity']
    )
    validated_data['total_revenue'] = (
        validated_data['unit_price'] * validated_data['quantity']
    )
    
    return super().create(validated_data)
```

### Permission Checking

Period and stocktake serializers check user permissions:

```python
# Can reopen closed periods?
def get_can_reopen(self, obj):
    request = self.context.get('request')
    
    # Superusers can always reopen
    if request.user.is_superuser:
        return True
    
    # Check PeriodReopenPermission
    return PeriodReopenPermission.objects.filter(
        hotel=obj.hotel,
        staff=request.user.staff_profile,
        is_active=True
    ).exists()
```

---

## API Response Examples

### StocktakeLine Response
```json
{
    "id": 1523,
    "item_sku": "S0610",
    "item_name": "Smirnoff 1Ltr",
    "category_code": "S",
    "item_size": "1 Lt",
    "item_uom": "28.2",
    "case_cost": null,
    "bottle_cost": "615.41",
    "opening_qty": "1100.0000",
    "purchases": "0.0000",
    "sales_qty": "0.0000",
    "waste": "0.0000",
    "counted_full_units": "41.00",
    "counted_partial_units": "0.30",
    "counted_qty": "1164.7200",
    "expected_qty": "1100.0000",
    "variance_qty": "64.7200",
    "opening_display_full_units": "39",
    "opening_display_partial_units": "0.20",
    "counted_display_full_units": "41",
    "counted_display_partial_units": "0.30",
    "variance_display_full_units": "2",
    "variance_display_partial_units": "0.30",
    "valuation_cost": "0.7740",
    "expected_value": "851.40",
    "counted_value": "901.58",
    "variance_value": "50.09",
    "available_cocktail_consumption_qty": "150.0000",
    "merged_cocktail_consumption_qty": "0.0000",
    "can_merge_cocktails": true
}
```

### Stocktake Summary Response
```json
{
    "id": 18,
    "period_name": "October 2025",
    "status": "DRAFT",
    "total_lines": 250,
    "total_items": 250,
    "total_value": "85432.50",
    "total_counted_value": "84567.30",
    "total_variance_value": "-865.20",
    "total_cogs": "14235.60",
    "total_revenue": "52400.00",
    "gross_profit_percentage": "72.83",
    "pour_cost_percentage": "27.17"
}
```

---

## Best Practices

1. **Read-Only Fields**: Use `read_only=True` for calculated/derived fields
2. **Write-Only Fields**: Use `write_only=True` for sensitive/internal data
3. **SerializerMethodField**: Use for complex calculations or lookups
4. **Context**: Pass `request` in context for permission checking
5. **Nested Serializers**: Use for related data, but beware of N+1 queries
6. **select_related/prefetch_related**: Always optimize queries in views
7. **Decimal Fields**: Always use for money/quantities to avoid floating-point errors

---

## Related Documentation

- **Models**: See `stock_tracker/models.py` for model definitions
- **Views**: See `stock_tracker/views.py` for API endpoints
- **URLs**: See `stock_tracker/urls.py` for endpoint mapping
- **Frontend**: See frontend docs for API consumption patterns
