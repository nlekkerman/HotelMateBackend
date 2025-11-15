# StocktakeLines Component - Complete Field Reference

## Overview
This document explains **every field** displayed and used in the StocktakeLines component. The component displays stocktake line items in a table format, showing item details, opening stock, movements (purchases/waste), expected quantities, counted quantities, and variance calculations.

## ⚠️ Document Scope
This documentation covers **backend API fields and endpoints**. This is a backend repository providing REST API endpoints. Frontend implementation details are provided as guidance for integration.

## 📋 What's Covered (Complete)

### Core Stocktake Fields ✅
- Item identification (SKU, name, subcategory)
- Category and unit information (category_code, category_name, item_size, item_uom)
- Opening stock (opening_qty, opening_display_full_units, opening_display_partial_units)
- Purchases and waste (purchases, waste, movements tracking)
- Expected stock (expected_qty, expected_display_full_units/partial_units, expected_value)
- Counted stock (counted_full_units, counted_partial_units, counted_qty)
- Variance (variance_qty, variance_display_full_units/partial_units, variance_value)

### Advanced Features ✅
- **Cost breakdown fields** (case_cost, bottle_cost)
- **Manual override fields** (manual_purchases_value, manual_waste_value, manual_sales_value)
- **Cocktail consumption tracking** (available/merged quantities, display-only feature)
- **Sales tracking** (sales_qty, sales endpoint with profitability metrics)
- **Profitability metrics** (total_cogs, total_revenue, gross_profit_percentage, pour_cost_percentage)
- **Movement management** (add, delete, update movements via API)
- **Transfers and adjustments** (transfers_in, transfers_out, adjustments)

### Minerals Subcategories ✅
- SOFT_DRINKS (cases + bottles, dozen counting)
- SYRUPS (bottles + ml, 35ml servings)
- JUICES (bottles + ml, 200ml servings)
- CORDIALS (cases + bottles)
- BIB (boxes + liters, 200ml servings)

### Real-Time Features ✅
- Pusher event broadcasting (6 event types documented)
- Channel subscription patterns
- Multi-user synchronization

### API Endpoints ✅
- Complete CRUD operations for stocktake lines
- Movement management endpoints (add, delete, update)
- Sales detail endpoint
- Category totals endpoint
- Stocktake management (populate, approve, reopen)
- Cocktail consumption merging

---

## 🔍 **Item Identification Fields**

### `item_sku` (SKU Column)
- **What**: Unique Stock Keeping Unit identifier for the item
- **Display**: Shown in monospace code format (e.g., `BUD-BTL-330`)
- **Purpose**: Uniquely identifies each inventory item
- **Format**: Text/Code (e.g., `GUIN-KEG-50L`, `JACK-BTL-700ML`)

### `item_name` (Name Column)
- **What**: Human-readable name of the item
- **Display**: Bold text (e.g., "Budweiser 330ml", "Jack Daniels 700ml")
- **Purpose**: User-friendly identification
- **Format**: Text string

### `subcategory` (Name Column - Badge)
- **What**: Optional subcategory classification
- **Display**: Small colored badge below item name
- **Purpose**: Additional categorization (e.g., "Draft", "Premium Spirit")
- **Format**: Text with visual badge component
- **Examples**: "Draft Beer", "Premium Wine", "Soft Drink"

---

## 📦 **Category & Unit Information**

### `category_name` (Cat Column)
- **What**: Main category classification
- **Display**: Gray badge (e.g., "Draught", "Bottled Beer", "Spirits")
- **Purpose**: Groups items by type for totals and reporting
- **Format**: Text badge
- **Categories**: D (Draught), B (Bottled Beer), S (Spirits), W (Wine), M (Minerals)

### `category_code` (Used for calculations, not displayed directly)
- **What**: Single-letter code identifying category
- **Purpose**: Determines calculation rules and validation logic
- **Values**: 
  - `D` = Draught (kegs/pints)
  - `B` = Bottled Beer (cases/bottles)
  - `S` = Spirits (bottles/measures)
  - `W` = Wine (bottles/glasses)
  - `M` = Minerals (cases/bottles or dozens)

### `item_size` (Size Column)
- **What**: Physical size/volume of the item
- **Display**: Gray text (e.g., "330ml", "50L", "Doz 12")
- **Purpose**: Specifies item packaging size
- **Format**: Text (volume, weight, or count)
- **Examples**: "50L", "330ml", "700ml", "Doz 12", "187ml"

### `item_uom` / `uom` (UOM Column)
- **What**: Unit of Measure - number of servings per full unit
- **Display**: Light badge showing number (e.g., "24", "88", "12")
- **Purpose**: Conversion factor for calculating total servings
- **Format**: Numeric (integer)
- **Examples**:
  - Keg 50L = 88 pints
  - Case 24x330ml = 24 bottles
  - Bottle 700ml spirits = 28 measures (25ml each)
  - Dozen minerals = 12 bottles

---

## 📊 **Opening Stock Fields**

### `opening_qty` (Backend value, not displayed directly)
- **What**: Total opening stock in servings
- **Purpose**: Starting point for expected calculations
- **Format**: Decimal (servings)
- **Calculation**: `(opening_full_units × uom) + opening_partial_units`
- **Backend managed**: ✅ Yes

### `opening_display_full_units` (Opening Column - Top number)
- **What**: Opening stock FULL units (cases/kegs/bottles)
- **Display**: Blue bold number with unit label
- **Purpose**: Shows how many complete units were in opening stock
- **Format**: Integer (whole number)
- **Backend managed**: ✅ Yes (calculated from opening_qty)
- **Example**: "5 Cases" = 5 full cases of beer

### `opening_display_partial_units` (Opening Column - Bottom number)
- **What**: Opening stock PARTIAL units (bottles/pints/measures)
- **Display**: Light blue bold number with serving unit label
- **Purpose**: Shows partial/loose servings in opening stock
- **Format**: Decimal (2 places for most categories, 0 for B/M-Doz)
- **Backend managed**: ✅ Yes (calculated from opening_qty)
- **Example**: "8.50 Bottles" = 8.5 loose bottles

### Opening Stock Input Fields (Editable when not locked)
- **`openingFullUnits` (input)**: Manual entry for full units
- **`openingPartialUnits` (input)**: Manual entry for partial units
- **Purpose**: Allows staff to manually set opening stock
- **Validation**: Category-specific (whole numbers for B/M-Doz, decimals for D/S/W)
- **Action**: Clicking "💾 Save" sends PATCH request to update `opening_qty`

---

## 🛒 **Purchases Fields**

### `purchases` (Purchases Column - Display number)
- **What**: Cumulative total of all purchase movements in servings
- **Display**: Large bold number in green (if >0) or gray
- **Purpose**: Shows total stock added via purchases
- **Format**: Decimal (2 places)
- **Backend managed**: ✅ Yes (sum of all PURCHASE movements)
- **Example**: "48.00" = 48 servings added via purchases

### Purchases Input Field (Editable when not locked)
- **`purchasesQty` (input)**: Enter quantity of new purchase in servings
- **Purpose**: Add new purchase movement
- **Validation**: Must be >0, allows 2 decimals
- **Action**: Clicking "💾 Save" sends POST to `/add-movement/` with:
  ```json
  {
    "movement_type": "PURCHASE",
    "quantity": 48.00,
    "notes": "Added via stocktake"
  }
  ```

### Purchases Movement History Button
- **What**: Button to view all purchase movements
- **Display**: Shows modal with list of all purchases (date, qty, notes)
- **Purpose**: Audit trail of all purchases added during stocktake
- **Features**: Can delete individual movements if not locked

---

## 🗑️ **Waste Fields**

### `waste` (Waste Column - Display number)
- **What**: Cumulative total of all waste movements in servings
- **Display**: Large bold number in red (if >0) or gray
- **Purpose**: Shows total stock removed via waste
- **Format**: Decimal (2 places)
- **Backend managed**: ✅ Yes (sum of all WASTE movements)
- **Example**: "12.50" = 12.5 servings marked as waste

### Waste Input Field (Editable when not locked)
- **`wasteQuantity` (input)**: Enter quantity of waste in servings
- **Purpose**: Record stock damaged/expired/broken
- **Validation**: Must be >0, allows 2 decimals
- **Action**: Clicking "💾 Save" sends POST to `/add-movement/` with:
  ```json
  {
    "movement_type": "WASTE",
    "quantity": 12.50,
    "notes": "Added via stocktake"
  }
  ```

### Waste Movement History Button
- **What**: Button to view all waste movements
- **Display**: Shows modal with list of all waste entries (date, qty, notes)
- **Purpose**: Audit trail of all waste recorded during stocktake
- **Features**: Can delete individual movements if not locked

---

## 📈 **Expected Stock Fields**

### `expected_qty` (Backend calculation, servings)
- **What**: What SHOULD be in stock based on math
- **Calculation**: `opening_qty + purchases - waste`
- **Purpose**: Baseline for variance calculation
- **Format**: Decimal (servings)
- **Backend managed**: ✅ Yes
- **Example**: 100 opening + 50 purchases - 10 waste = 140 expected

### `expected_display_full_units` (Expected Column - Top number)
- **What**: Expected stock in FULL units (cases/kegs/bottles)
- **Display**: Red/orange bold number with unit label
- **Purpose**: Shows expected complete units
- **Format**: Integer (whole number)
- **Backend managed**: ✅ Yes (calculated from expected_qty)
- **Example**: "5 Cases"

### `expected_display_partial_units` (Expected Column - Bottom number)
- **What**: Expected stock in PARTIAL units (bottles/pints/measures)
- **Display**: Red/orange bold number with serving unit label
- **Purpose**: Shows expected partial/loose servings
- **Format**: Decimal (category-specific rounding)
- **Backend managed**: ✅ Yes (calculated from expected_qty)
- **Example**: "8.50 Bottles"

### `expected_value` (Expected Column - Money)
- **What**: Euro value of expected stock
- **Display**: Green text showing €X.XX
- **Purpose**: Financial value of what should be in stock
- **Format**: Currency (2 decimal places)
- **Backend managed**: ✅ Yes
- **Calculation**: `expected_qty × valuation_cost`

---

## 📋 **Counted Stock Fields**

### `counted_full_units` (Counted Cases Column - Input & Display)
- **What**: ACTUAL full units (cases/kegs/bottles) physically counted
- **Display**: Input field when active, bold number when locked
- **Purpose**: User enters what they physically counted
- **Format**: Integer (whole numbers only)
- **Validation**: Must be ≥0, no decimals allowed
- **Frontend validates**: ✅ Format only
- **Backend calculates**: ✅ Converts to counted_qty

### `counted_partial_units` (Counted Bottles Column - Input & Display)
- **What**: ACTUAL partial units (bottles/pints/measures) physically counted
- **Display**: Input field when active, bold number when locked
- **Purpose**: User enters loose/partial servings counted
- **Format**: Category-specific:
  - **B** (Bottled Beer): Whole numbers only (0-23 for case of 24)
  - **M-Doz** (Dozen Minerals): Whole numbers only (0-11)
  - **D/S/W**: Decimals allowed (max 2 decimal places)
- **Validation**: 
  - Must be ≥0
  - Must be < uom (can't have 24 bottles in a 24-case)
  - Category-specific decimal rules
- **Frontend validates**: ✅ Format and max value
- **Backend calculates**: ✅ Converts to counted_qty

### `counted_qty` (Backend value, not displayed directly)
- **What**: Total counted stock in servings
- **Purpose**: Used for variance calculation
- **Format**: Decimal (servings)
- **Backend calculation**: `(counted_full_units × uom) + counted_partial_units`
- **Backend managed**: ✅ Yes

### Counted Input Labels
- **`labels.unit`**: Dynamic label for full units (e.g., "Cases", "Kegs", "Bottles")
- **`labels.servingUnit`**: Dynamic label for partial units (e.g., "Bottles", "Pints", "Measures")
- **`labels.partialMax`**: Maximum allowed value for partial units (from backend API)
- **Source**: Generated by `getCountingLabels()` helper function

---

## 📉 **Variance Fields**

### `variance_qty` (Backend calculation, servings)
- **What**: Difference between counted and expected (in servings)
- **Calculation**: `counted_qty - expected_qty`
- **Purpose**: Shows shortage/surplus in raw serving units
- **Format**: Decimal (servings, can be negative)
- **Backend managed**: ✅ Yes
- **Example**: 
  - -10.50 = shortage of 10.5 servings
  - +5.25 = surplus of 5.25 servings

### `variance_display_full_units` (Variance Column - Top number)
- **What**: Variance in FULL units (cases/kegs/bottles)
- **Display**: Green (surplus) or Red (shortage) bold number with +/- sign
- **Purpose**: Shows variance in complete units
- **Format**: Integer with sign
- **Backend managed**: ✅ Yes (calculated from variance_qty with category-specific rounding)
- **Example**: "+2 Cases" or "-1 Keg"

### `variance_display_partial_units` (Variance Column - Bottom number)
- **What**: Variance in PARTIAL units (bottles/pints/measures)
- **Display**: Green (surplus) or Red (shortage) bold number with +/- sign
- **Purpose**: Shows variance in partial servings
- **Format**: Decimal with sign (category-specific rounding)
- **Backend managed**: ✅ Yes (calculated from variance_qty)
- **Example**: "+8.50 Bottles" or "-3.75 Pints"

### `variance_value` (Variance Column - Money)
- **What**: Euro value of variance (shortage or surplus)
- **Display**: Green/Red bold text with +/- and € symbol
- **Purpose**: Financial impact of variance
- **Format**: Currency (2 decimal places, can be negative)
- **Backend managed**: ✅ Yes
- **Calculation**: `variance_qty × valuation_cost`
- **Visual indicators**:
  - **Red background**: Shortage (negative value)
  - **Green background**: Surplus (positive value)
  - **⚠️ Icon**: Significant variance (absolute value >€10)

### Variance Display Logic
- **Not counted yet**: Shows "-" (gray)
- **Shortage**: Red text, red background, negative values
- **Surplus**: Green text, green background, positive values
- **Significant**: Bold text if absolute variance value >€10

---

## 💰 **Cost Breakdown Fields**

### `case_cost` (API field, not always present)
- **What**: Total cost of a full case/dozen
- **Display**: Used for dozen/case items only
- **Purpose**: Shows full case/dozen price for easier inventory valuation
- **Format**: Decimal (2 places)
- **Backend managed**: ✅ Yes
- **Calculation**: `valuation_cost × uom`
- **Available for**: Items with "Doz" in size (dozen minerals, case items)
- **Example**: If valuation_cost = €0.25/bottle and uom = 12, case_cost = €3.00

### `bottle_cost` (API field, spirits only)
- **What**: Total cost of a full bottle of spirits
- **Display**: Used for spirits category only
- **Purpose**: Shows full bottle cost (since spirits are valued per measure)
- **Format**: Decimal (2 places)
- **Backend managed**: ✅ Yes
- **Calculation**: `valuation_cost × uom`
- **Available for**: Category S (Spirits) only
- **Example**: If valuation_cost = €2.50/measure and uom = 28, bottle_cost = €70.00
- **Note**: Wine is NOT included (wine is sold by bottle, not serving)

---

## 💵 **Manual Override Fields** (Optional Direct Entry)

These fields allow manual entry of financial values instead of relying on system calculations:

### `manual_purchases_value` (Backend field)
- **What**: Manual override for total purchase value in period
- **Purpose**: Allows direct entry of purchase costs (€) instead of using movement calculations
- **Format**: Decimal (2 places), nullable
- **Backend managed**: ✅ Yes
- **Usage**: Optional alternative to purchase movement tracking
- **Example**: Enter €1,250.00 directly instead of tracking individual purchases

### `manual_waste_value` (Backend field)
- **What**: Manual override for total waste value in period
- **Purpose**: Allows direct entry of waste costs (€)
- **Format**: Decimal (2 places), nullable
- **Backend managed**: ✅ Yes
- **Usage**: Optional alternative to waste movement tracking

### `manual_sales_value` (Backend field)
- **What**: Manual override for total sales revenue in period
- **Purpose**: Allows direct entry of sales revenue (€)
- **Format**: Decimal (2 places), nullable
- **Backend managed**: ✅ Yes
- **Usage**: Optional alternative to automated sales tracking

---

## 🍹 **Cocktail Consumption Tracking** (Display Only)

These fields track ingredients used in cocktails but **DO NOT affect stocktake calculations**:

### `available_cocktail_consumption_qty` (API field, read-only)
- **What**: Quantity of this item used in cocktails that hasn't been merged yet
- **Display**: Shows unmerged cocktail usage
- **Purpose**: Allows viewing cocktail ingredient usage separately
- **Format**: Decimal (4 places, servings)
- **Backend managed**: ✅ Yes
- **IMPORTANT**: Display only - does NOT affect expected_qty or variance
- **Use case**: Track bar cocktail ingredient consumption separately from main stock

### `merged_cocktail_consumption_qty` (API field, read-only)
- **What**: Quantity that has already been merged from cocktails
- **Display**: Shows what was previously merged
- **Purpose**: Audit trail of merged cocktail consumption
- **Format**: Decimal (4 places, servings)
- **Backend managed**: ✅ Yes
- **IMPORTANT**: Display only - historical record

### `available_cocktail_consumption_value` (API field, read-only)
- **What**: Euro value of unmerged cocktail consumption
- **Display**: Shows potential value if merged
- **Purpose**: Financial tracking of cocktail ingredient usage
- **Format**: Decimal (2 places)
- **Backend managed**: ✅ Yes
- **Calculation**: `available_cocktail_consumption_qty × valuation_cost`

### `merged_cocktail_consumption_value` (API field, read-only)
- **What**: Euro value of merged cocktail consumption
- **Display**: Shows value that was merged
- **Purpose**: Historical financial record
- **Format**: Decimal (2 places)
- **Backend managed**: ✅ Yes
- **Calculation**: `merged_cocktail_consumption_qty × valuation_cost`

### `can_merge_cocktails` (API field, read-only)
- **What**: Boolean flag indicating if unmerged cocktail consumption exists
- **Display**: Controls visibility of "Merge Cocktails" button
- **Purpose**: UI helper to show merge option
- **Format**: Boolean
- **Backend managed**: ✅ Yes
- **True when**: `available_cocktail_consumption_qty > 0`

---

## 📊 **Sales Tracking Fields**

### `sales_qty` (Backend calculation, servings)
- **What**: Total quantity sold during stocktake period
- **Display**: Can be shown separately from stocktake variance
- **Purpose**: Track sales separately from stock counting
- **Format**: Decimal (4 places, servings)
- **Backend managed**: ✅ Yes
- **Calculation**: Sum of all Sale records for this item in the stocktake period
- **IMPORTANT**: Sales are tracked but NOT included in expected_qty formula
- **Note**: `expected_qty = opening + purchases - waste` (sales excluded)

### Sales Endpoint: `GET /stocktake-lines/{id}/sales/`
- **What**: Detailed sales data for this line item
- **Returns**:
  - List of all Sale records
  - Summary totals (quantity, revenue, cost, GP%)
  - Item pricing information
- **Purpose**: View detailed sales breakdown for the item during period
- **Use case**: Analyze item profitability separately from stock variance

---

## 🔐 **Backend-Only Calculation Fields**

These fields are **NEVER edited by frontend** - backend calculates and returns them:

### `valuation_cost` (Not displayed directly)
- **What**: Frozen cost per serving at stocktake start
- **Purpose**: Used for all value calculations
- **Format**: Decimal (cost per serving)
- **Backend managed**: ✅ Yes
- **Usage**: Multiplied by quantities to get euro values

### `input_fields` (API metadata)
- **What**: Backend-provided configuration for input fields
- **Purpose**: Tells frontend what labels/limits to use
- **Format**: JSON object
- **Contains**:
  - `full`: `{name, label, max, step}` for full units
  - `partial`: `{name, label, max, step}` for partial units
- **Backend managed**: ✅ Yes
- **Example**:
  ```json
  {
    "full": {"name": "counted_full_units", "label": "Cases"},
    "partial": {"name": "counted_partial_units", "label": "Bottles", "max": 23}
  }
  ```

### `transfers_in` (Backend field)
- **What**: Stock transferred IN from other locations during period
- **Format**: Decimal (4 places, servings)
- **Backend managed**: ✅ Yes
- **Read-only**: Cannot be edited via stocktake lines

### `transfers_out` (Backend field)
- **What**: Stock transferred OUT to other locations during period
- **Format**: Decimal (4 places, servings)
- **Backend managed**: ✅ Yes
- **Read-only**: Cannot be edited via stocktake lines

### `adjustments` (Backend field)
- **What**: Prior stock adjustments in period
- **Format**: Decimal (4 places, servings)
- **Backend managed**: ✅ Yes
- **Read-only**: Cannot be edited via stocktake lines

### `opening_value` (Backend property)
- **What**: Euro value of opening stock
- **Format**: Decimal (2 places)
- **Backend managed**: ✅ Yes
- **Calculation**: `opening_qty × valuation_cost`

### `purchases_value` (Backend property)
- **What**: Euro value of purchases
- **Format**: Decimal (2 places)
- **Backend managed**: ✅ Yes
- **Calculation**: `purchases × valuation_cost`

---

## 🎯 **State Management Fields (Frontend Only)**

### `lineInputs` (Component state)
- **What**: Local state tracking all input field values
- **Purpose**: Manages user input before saving
- **Structure**:
  ```javascript
  {
    [lineId]: {
      fullUnits: '5',           // Counted cases input
      partialUnits: '8.50',     // Counted bottles input
      wasteQuantity: '2.00',    // Waste input
      purchasesQty: '24.00',    // Purchases input
      openingFullUnits: '10',   // Opening cases input
      openingPartialUnits: '0'  // Opening bottles input
    }
  }
  ```

### `validationErrors` (Component state)
- **What**: Tracks validation errors for each line/field
- **Purpose**: Shows error messages to user
- **Structure**:
  ```javascript
  {
    [lineId]: {
      fullUnits: 'Must be whole number',
      partialUnits: 'Must be 0-23 bottles',
      wasteQuantity: 'Must be greater than 0'
    }
  }
  ```

---

## 🚀 **Action Buttons & Operations**

### Save Count Button
- **Trigger**: "💾 Save" in Actions column
- **Sends**: `counted_full_units` and `counted_partial_units`
- **Endpoint**: `PATCH /stocktake-lines/{id}/`
- **Backend calculates**: All display values, variance, totals
- **Frontend updates**: From backend response (no optimistic updates)

### Save Purchases Button
- **Trigger**: "💾 Save" in Purchases section
- **Sends**: `{ movement_type: 'PURCHASE', quantity, notes }`
- **Endpoint**: `POST /stocktake-lines/{id}/add-movement/`
- **Backend updates**: Purchases total, expected values, variance
- **Frontend updates**: From backend response

### Save Waste Button
- **Trigger**: "💾 Save" in Waste section
- **Sends**: `{ movement_type: 'WASTE', quantity, notes }`
- **Endpoint**: `POST /stocktake-lines/{id}/add-movement/`
- **Backend updates**: Waste total, expected values, variance
- **Frontend updates**: From backend response

### Save Opening Stock Button
- **Trigger**: "💾 Save" in Opening section
- **Sends**: Calculated `opening_qty` from full + partial inputs
- **Endpoint**: `PATCH /stocktake-lines/{id}/`
- **Backend updates**: Opening values, expected values, variance
- **Frontend updates**: From backend response

### Delete Movement Button
- **Trigger**: "Delete" in Movement history modal
- **Action**: Deletes specific movement record
- **Endpoint**: `DELETE /stocktake-lines/{id}/delete-movement/{movement_id}/`
- **Backend updates**: Recalculates totals after deletion
- **Returns**: Updated line data with recalculated values

### Update Movement Button
- **Trigger**: "Edit" in Movement history modal (if implemented)
- **Action**: Updates existing movement record
- **Endpoint**: `PATCH /stocktake-lines/{id}/update-movement/{movement_id}/`
- **Sends**: `{ movement_type, quantity, unit_cost, reference, notes }`
- **Backend updates**: Recalculates totals after update
- **Use case**: Correct mistakes in previously entered movements

### View Sales Button (Optional)
- **Trigger**: Button to view sales detail for this item
- **Action**: Fetches detailed sales breakdown
- **Endpoint**: `GET /stocktake-lines/{id}/sales/`
- **Returns**:
  - List of all Sale records for this item in the period
  - Summary totals (quantity, revenue, cost, GP%)
  - Item pricing information
- **Use case**: Analyze sales performance and profitability per item

### Merge Cocktails Button (Optional)
- **Trigger**: Shown when `can_merge_cocktails === true`
- **Action**: Merges unmerged cocktail consumption into stocktake
- **Endpoint**: `POST /stocktakes/{id}/merge-cocktail-consumption/`
- **Effect**: Updates cocktail consumption tracking (display only)
- **Note**: Does NOT affect stocktake calculations

### Clear Button
- **Trigger**: "Clear" in Actions column
- **Action**: Resets all input fields to current saved values
- **No API call**: Local state reset only

---

## 📏 **Validation Rules by Category**

### Bottled Beer (B)
- **Full Units**: Whole numbers only (0, 1, 2, ...)
- **Partial Units**: Whole numbers only, max = uom - 1
- **Example**: Case of 24 → partial can be 0-23 bottles

### Dozen Minerals (M with "Doz" in size)
- **Full Units**: Whole numbers only
- **Partial Units**: Whole numbers only, max = 11
- **Example**: Dozen → partial can be 0-11 bottles

### Draught (D), Spirits (S), Wine (W)
- **Full Units**: Whole numbers only
- **Partial Units**: Decimals allowed (max 2 decimal places)
- **Example**: Keg 88 pints → partial can be 0.00-87.99 pints

### Minerals (M) - Subcategory Specific Rules

Minerals have different counting rules based on subcategory:

#### SOFT_DRINKS (Doz)
- **Full Units**: Cases (whole numbers)
- **Partial Units**: Bottles (whole numbers, 0-11)
- **Example**: Case of 12 → partial can be 0-11 bottles
- **Conversion**: `servings = (cases × 12) + bottles` (servings = bottles)

#### SYRUPS
- **Full Units**: Bottles (whole numbers)
- **Partial Units**: ml (whole numbers, 0-999)
- **Example**: 1L bottle → partial can be 0-1000 ml
- **Conversion**: `servings = ((bottles × bottle_size_ml) + partial_ml) / 35`
- **Serving size**: 35ml per serving

#### JUICES
- **Full Units**: Bottles (whole numbers)
- **Partial Units**: ml (whole numbers, 0-1499)
- **Example**: 1.5L bottle → partial can be 0-1500 ml
- **Conversion**: `servings = ((bottles × bottle_size_ml) + partial_ml) / 200`
- **Serving size**: 200ml per serving

#### CORDIALS
- **Full Units**: Cases (whole numbers)
- **Partial Units**: Bottles (whole numbers)
- **Conversion**: `servings = (cases × uom) + bottles` (servings = bottles)

#### BIB (Bag-in-Box)
- **Full Units**: Boxes (whole numbers)
- **Partial Units**: Liters (decimals allowed, 0.1 step, max 18.0)
- **Example**: 18L box → partial can be 0.0-18.0 liters
- **Conversion**: `servings = ((boxes × 18) + partial_liters) / 0.2`
- **Serving size**: 200ml (0.2L) per serving

---

## 🔄 **Real-Time Updates (Pusher)**

All calculations are done by backend. When any user saves changes:
1. Backend calculates all values
2. Backend saves to database
3. Backend broadcasts via Pusher
4. **All connected clients** receive update
5. Frontend updates UI with backend values

**No optimistic updates** - UI always shows backend-calculated values.

### Pusher Events

The backend broadcasts these events to keep all connected clients synchronized:

#### `stocktake-created`
- **When**: New stocktake is created
- **Channel**: `hotel-{hotel_identifier}`
- **Payload**: New stocktake data
- **Frontend action**: Add to stocktake list

#### `stocktake-status-changed`
- **When**: Stocktake status changes (DRAFT → APPROVED, etc.)
- **Channel**: `hotel-{hotel_identifier}`
- **Payload**: Stocktake ID, new status
- **Frontend action**: Update UI to reflect locked/unlocked state

#### `stocktake-populated`
- **When**: Stocktake lines are populated
- **Channel**: `hotel-{hotel_identifier}`
- **Payload**: Stocktake ID, line count
- **Frontend action**: Refresh stocktake lines list

#### `line-counted-updated`
- **When**: Counted values are saved for a line
- **Channel**: `stocktake-{stocktake_id}`
- **Payload**: Line ID, item SKU, full updated line data
- **Frontend action**: Update specific line in table

#### `line-movement-added`
- **When**: Purchase or waste movement is added
- **Channel**: `stocktake-{stocktake_id}`
- **Payload**: Line ID, item SKU, movement data, updated line data
- **Frontend action**: Update line and refresh movement history

#### `line-movement-deleted`
- **When**: Purchase or waste movement is deleted
- **Channel**: `stocktake-{stocktake_id}`
- **Payload**: Line ID, item SKU, deleted movement ID, updated line data
- **Frontend action**: Update line and refresh movement history

### Pusher Channel Subscription
- **Hotel-wide events**: Subscribe to `hotel-{hotel_identifier}`
- **Stocktake-specific events**: Subscribe to `stocktake-{stocktake_id}`
- **Frontend responsibility**: Subscribe when viewing stocktake, unsubscribe when leaving

---

## 🎨 **Display States**

### Active/Draft Stocktake
- All input fields shown
- Edit buttons enabled
- Movement history buttons visible
- Full interactive UI

### Locked/Closed Stocktake
- No input fields (display only)
- Clean, stylish view
- Larger, bold numbers
- No edit buttons
- Movement history hidden
- Read-only presentation

---

## 📊 **Category Totals Row**

Each category table shows footer totals:
- **Total Opening Value**: Sum of all line opening_value
- **Total Expected Value**: Sum of all line expected_value
- **Total Counted Value**: Sum of all line counted_value
- **Total Variance Value**: Sum of all line variance_value

Backend calculates all category totals via dedicated endpoint:
- **Endpoint**: `GET /stocktakes/{id}/category-totals/?category={code}`
- **Returns**: Aggregated totals for specified category or all categories

---

## 💼 **Profitability Metrics** (Stocktake Level)

These metrics are calculated at the **Stocktake level** (not per-line):

### `total_cogs` (Cost of Goods Sold)
- **What**: Total cost of all items sold during period
- **Source**: Aggregated from Sale records
- **Format**: Decimal (2 places)
- **Calculation**: Sum of `total_cost` from all Sale records
- **Backend managed**: ✅ Yes

### `total_revenue`
- **What**: Total sales revenue during period
- **Source**: Aggregated from Sale records
- **Format**: Decimal (2 places)
- **Calculation**: Sum of `total_revenue` from all Sale records
- **Backend managed**: ✅ Yes

### `gross_profit_percentage` (GP%)
- **What**: Gross profit margin percentage
- **Format**: Decimal (2 places)
- **Calculation**: `((total_revenue - total_cogs) / total_revenue) × 100`
- **Backend managed**: ✅ Yes
- **Display**: Shows profitability of sales during stocktake period

### `pour_cost_percentage`
- **What**: Pour cost (beverage cost) percentage
- **Format**: Decimal (2 places)
- **Calculation**: `(total_cogs / total_revenue) × 100`
- **Backend managed**: ✅ Yes
- **Display**: Industry standard metric for bar profitability
- **Ideal range**: Typically 18-24% for bars

### Accessing Profitability Metrics
- **Available in**: StocktakeSerializer (detail view)
- **Endpoint**: `GET /stocktakes/{id}/`
- **Display**: Usually shown in stocktake summary/header section
- **Use case**: Assess overall bar/restaurant performance for the period

---

## 🎯 **Key Architecture Principles**

1. **Backend Calculates Everything**: Frontend never does math
2. **No Optimistic Updates**: Wait for backend response
3. **Frontend Validates Format Only**: Business logic on backend
4. **Pusher for Real-Time Sync**: All clients stay synchronized
5. **Display Values from Backend**: Use `*_display_*` fields directly
6. **Frozen Valuation Cost**: Financial values stable during stocktake
7. **Sales Tracked Separately**: Sales don't affect expected_qty calculation
8. **Cocktails Display Only**: Cocktail consumption tracking doesn't affect variance
9. **Movement-Based Purchases/Waste**: Purchases and waste derived from StockMovement records
10. **Read-Only Calculated Fields**: Never send calculated fields in POST/PATCH requests

---

## 🌐 **Complete API Endpoints Reference**

### Stocktake Line Endpoints

#### Get Line Details
```
GET /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/
```
Returns complete line data with all calculated fields.

#### Update Counted Values
```
PATCH /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/
Body: {
  "counted_full_units": 5,
  "counted_partial_units": 8.5
}
```
Updates counted quantities. Backend recalculates all derived values.

#### Update Opening Stock
```
PATCH /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/
Body: {
  "opening_qty": 150.00  // OR use opening_full_units + opening_partial_units
}
```
Updates opening stock. Backend recalculates expected and variance.

#### Add Purchase/Waste Movement
```
POST /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/add-movement/
Body: {
  "movement_type": "PURCHASE",  // or "WASTE"
  "quantity": 48.00,
  "unit_cost": 2.50,  // optional
  "reference": "INV-12345",  // optional
  "notes": "Manual entry from stocktake"  // optional
}
```
Creates StockMovement record. Backend updates line totals automatically.

#### Get Movement History
```
GET /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/movements/
```
Returns all movements for this item in the stocktake period.

#### Delete Movement
```
DELETE /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/delete-movement/{movement_id}/
```
Deletes movement and recalculates line totals.

#### Update Movement
```
PATCH /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/update-movement/{movement_id}/
Body: {
  "movement_type": "PURCHASE",
  "quantity": 75.0,
  "unit_cost": 2.50,
  "reference": "Updated ref",
  "notes": "Corrected quantity"
}
```
Updates existing movement and recalculates line totals.

#### Get Sales Detail
```
GET /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/sales/
```
Returns all Sale records and summary for this item in the period.

### Stocktake Endpoints

#### Get Stocktake with Lines
```
GET /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/
```
Returns complete stocktake with all lines and profitability metrics.

#### Get Category Totals
```
GET /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/category-totals/
GET /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/category-totals/?category=D
```
Returns aggregated totals by category or all categories.

#### Populate Stocktake
```
POST /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/populate/
```
Generates stocktake lines from current stock items.

#### Approve Stocktake
```
POST /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/approve/
```
Locks stocktake and prevents further edits.

#### Reopen Stocktake
```
POST /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/reopen/
```
Unlocks stocktake for additional edits.

#### Merge Cocktail Consumption
```
POST /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/merge-cocktail-consumption/
```
Merges unmerged cocktail consumption (display only feature).

#### Merge Single Line Cocktail Consumption
```
POST /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/merge-cocktail-consumption/
Body: {
  "line_id": 123
}
```
Merges cocktail consumption for specific line only.

---

## 📖 **Related Documentation**

- `BACKEND_API_COMPLETE_REFERENCE_FOR_FRONTEND.md` - Complete API reference
- `FRONTEND_IMPLEMENTATION_GUIDE.md` - Frontend implementation patterns
- `STOCK_SERIALIZERS_DOCUMENTATION.md` - Serializer field details
- `categoryHelpers.js` - Label generation logic (frontend)
- `stocktakeCalculations.js` - Frontend validation helpers (frontend)
- `CategoryTotalsRow.jsx` - Category summary component (frontend)
- `MovementsList.jsx` - Purchase/waste history component (frontend)
