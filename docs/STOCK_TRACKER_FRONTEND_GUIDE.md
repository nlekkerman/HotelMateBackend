# Stock Tracker Frontend Integration Guide

---

## ⚠️⚠️⚠️ MOST IMPORTANT: QUANTITIES ARE IN MILLILITERS (ml), NOT BOTTLES! ⚠️⚠️⚠️

```
Backend Returns:    current_qty: 1400  (this is 1400ml, NOT 1400 bottles!)
Frontend Displays:  "2 bottles" (after conversion: 1400ml ÷ 700ml/bottle)
```

**You MUST convert ml to bottles in your frontend!**
- 70cl bottle = 700ml
- current_qty: 1400 = **2 bottles** (1400 ÷ 700)
- current_qty: 2100 = **3 bottles** (2100 ÷ 700)

---

## 🚀 Quick Start Summary

### Critical Information

**🚨 NO PAGINATION**
- All endpoints return complete datasets in a single request
- Response is a plain array: `[{...}, {...}, {...}]`
- No `count`, `next`, `previous`, or `results` wrapper

**🔍 Category Filtering**
- Single category: `?category=1`
- Multiple categories: `?category=1&category=2&category=3`
- With search: `?category=1&search=vodka`

**📍 URL Pattern**
- Base: `/api/stock_tracker/{hotel_identifier}/`
- hotel_identifier = hotel `slug` OR `subdomain`
- Example: `/api/stock_tracker/hotel-killarney/items/`

**🔧 Available Filters**
- `?category=1` - Filter by category ID
- `?search=vodka` - Search SKU, name, description
- Combine: `?category=1&category=2&search=absolut`

**⚠️ CRITICAL: Quantities Are in ml (Not Bottles!)**
- `current_qty`: Stored in **milliliters (ml)** for liquids
- `par_level`: Also in **ml**
- Frontend MUST convert to bottles for display
- Formula: `bottles = Math.floor(current_qty_ml / bottle_size_ml)`
- Example: `current_qty: 1400` = 2 bottles of 70cl (700ml each)
- See full section: [Understanding Quantities](#️-critical-understanding-quantities-ml-vs-bottles)

---

## Table of Contents
1. [Overview](#overview)
2. [API Endpoints](#api-endpoints)
3. [Data Models](#data-models)
4. [⚠️ CRITICAL: Understanding Quantities (ml vs Bottles)](#️-critical-understanding-quantities-ml-vs-bottles)
5. [No Pagination - Important](#-important-no-pagination---all-results-returned)
6. [Category Filtering](#-filtering-stock-items-by-category)
7. [Getting All Stock Items](#getting-all-stock-items)
8. [Complete Category Filter Implementation](#-complete-category-filtering-implementation)
9. [Displaying Item Data](#displaying-item-data)
10. [Creating New Items](#creating-new-items)
11. [Filtering and Searching](#filtering-and-searching)
12. [Stock Movements](#stock-movements)
13. [Stocktake Workflow](#stocktake-workflow)
14. [Error Handling](#error-handling)

---

## Overview

The Stock Tracker app manages inventory for hotels including:
- **Stock Categories**: Organize items (Spirits, Wines, Beers, etc.)
- **Locations**: Physical storage locations/bins
- **Stock Items**: Comprehensive product inventory with pricing, quantities, and metadata
- **Stock Movements**: Track purchases, sales, waste, transfers, and adjustments
- **Stocktakes**: Period-based inventory counting and variance tracking

**Base URL**: `/api/stock_tracker/{hotel_identifier}/`

**Note**: `{hotel_identifier}` can be either the hotel's `slug` or `subdomain`

**Example URLs**:
- `/api/stock_tracker/hotel-killarney/items/` - Using hotel slug
- `/api/stock_tracker/hilton/categories/` - Using hotel subdomain

**Important Notes**:
- ⚠️ **NO PAGINATION**: All endpoints return complete results without pagination
- 🔍 **Filtering**: Use query parameters to filter results (see examples below)
- 📊 **All Data Returned**: You get all items, categories, movements, etc. in a single request

---

## API Endpoints

### Stock Categories
```
GET    /api/stock_tracker/{hotel_identifier}/categories/          # List all categories
POST   /api/stock_tracker/{hotel_identifier}/categories/          # Create category
GET    /api/stock_tracker/{hotel_identifier}/categories/{id}/     # Get category detail
PUT    /api/stock_tracker/{hotel_identifier}/categories/{id}/     # Update category
PATCH  /api/stock_tracker/{hotel_identifier}/categories/{id}/     # Partial update
DELETE /api/stock_tracker/{hotel_identifier}/categories/{id}/     # Delete category
```

### Stock Items
```
GET    /api/stock_tracker/{hotel_identifier}/items/               # List all items
POST   /api/stock_tracker/{hotel_identifier}/items/               # Create item
GET    /api/stock_tracker/{hotel_identifier}/items/{id}/          # Get item detail
PUT    /api/stock_tracker/{hotel_identifier}/items/{id}/          # Update item
PATCH  /api/stock_tracker/{hotel_identifier}/items/{id}/          # Partial update
DELETE /api/stock_tracker/{hotel_identifier}/items/{id}/          # Delete item
```

### Stock Movements
```
GET    /api/stock_tracker/{hotel_identifier}/movements/           # List movements
POST   /api/stock_tracker/{hotel_identifier}/movements/           # Create movement
GET    /api/stock_tracker/{hotel_identifier}/movements/{id}/      # Get movement detail
PUT    /api/stock_tracker/{hotel_identifier}/movements/{id}/      # Update movement
DELETE /api/stock_tracker/{hotel_identifier}/movements/{id}/      # Delete movement
```

### Stocktakes
```
GET    /api/stock_tracker/{hotel_identifier}/stocktakes/                    # List stocktakes
POST   /api/stock_tracker/{hotel_identifier}/stocktakes/                    # Create stocktake
GET    /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/               # Get stocktake detail
PUT    /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/               # Update stocktake
POST   /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/populate/      # Populate stocktake lines
POST   /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/approve/       # Approve stocktake
GET    /api/stock_tracker/{hotel_identifier}/stocktakes/{id}/category-totals/ # Get category totals
```

### Stocktake Lines
```
GET    /api/stock_tracker/{hotel_identifier}/stocktake-lines/              # List lines
GET    /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/         # Get line detail
PUT    /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/         # Update line (if not locked)
PATCH  /api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/         # Partial update
```

---

## Data Models

### StockCategory
```typescript
interface StockCategory {
  id: number;
  hotel: number;
  name: string;              // "Spirits", "Wines", "Beers"
  sort_order: number;        // Display order
}
```

### Location
```typescript
interface Location {
  id: number;
  hotel: number;
  name: string;              // "Spirits Shelf", "Cellar A-12"
  active: boolean;
}
```

### StockItem (Full Model)
```typescript
interface StockItem {
  // Core fields
  id: number;
  hotel: number;
  category: number | null;
  category_name?: string;    // Read-only, from category relationship
  sku: string;               // "S0001", "S0002"
  name: string;              // "Dingle Vodka", "Jameson"
  description?: string;
  
  // Classification
  product_type: string;      // "Vodka", "Whiskey", "Beer", "Wine"
  subtype: string;           // "Irish", "Scotch Blended", "IPA"
  tag?: string;              // "special", "promo"
  
  // Size & Units
  size: string;              // "70cl", "30L Keg", "500ml Bottle"
  size_value: number | null; // 70, 30, 500
  size_unit: string;         // "cl", "L", "ml"
  uom: number;               // Units of measure (12 bottles/case, 24 cans/case)
  base_unit: string;         // "ml", "L", "g"
  
  // Cost & Pricing
  unit_cost: number;         // Cost per full unit (case/bottle/keg)
  cost_per_base: number | null; // Calculated: cost per ml/g/piece
  case_cost: number | null;  // Total case cost
  selling_price: number | null; // Selling price per unit
  
  // Inventory
  current_qty: number;       // ⚠️ IMPORTANT: Current stock in BASE UNITS (ml for liquids, not bottles!)
  par_level: number;         // Minimum stock level in BASE UNITS
  
  // Storage
  bin: number | null;        // Location/bin ID
  bin_name?: string;         // Read-only location name
  
  // Vendor/Origin
  vendor?: string;
  country?: string;
  region?: string;
  subregion?: string;
  producer?: string;
  vineyard?: string;
  
  // Product attributes
  abv_percent: number | null;
  vintage?: string;
  
  // Barcodes
  unit_upc?: string;
  case_upc?: string;
  
  // Serving/Pour (for price calculator)
  serving_size: number | null;  // 25ml, 150ml
  serving_unit: string;          // "ml", "oz", "cl"
  menu_price: number | null;     // Menu price per serving
  
  // Flags
  active: boolean;
  hide_on_menu: boolean;
  
  // Calculated properties (read-only)
  gp_percentage?: number;           // Gross profit %
  is_below_par?: boolean;           // current_qty < par_level
  pour_cost?: number;               // serving_size × cost_per_base
  pour_cost_percentage?: number;    // (pour_cost / menu_price) × 100
  profit_per_serving?: number;      // menu_price - pour_cost
  profit_margin_percentage?: number; // (profit / menu_price) × 100
}
```

---

## ⚠️ CRITICAL: Understanding Quantities (ml vs Bottles)

### How Quantities Are Stored

**All quantities are stored in BASE UNITS (not bottles/cases!)**

- **`current_qty`**: Stored in **ml** (milliliters) for liquids
- **`par_level`**: Also in **ml**
- **`quantity` in movements**: Also in **ml**

### Example: Vodka Bottle

```javascript
{
  "sku": "S0001",
  "name": "Dingle Vodka",
  "size": "70cl",           // Display size
  "size_value": 70,         // Numeric value
  "size_unit": "cl",        // Unit (centiliters)
  "base_unit": "ml",        // All quantities in ml
  "current_qty": 1400,      // ← THIS IS 1400ml (2 bottles × 700ml)
  "par_level": 700          // ← THIS IS 700ml (1 bottle)
}
```

### Converting ml to Bottles

To display quantities in bottles, you MUST convert:

```javascript
// Helper function to convert ml to bottles
function convertToBottles(currentQtyInMl, sizeValue, sizeUnit) {
  // Convert size to ml
  let bottleSizeInMl;
  
  switch (sizeUnit.toLowerCase()) {
    case 'cl':
      bottleSizeInMl = sizeValue * 10; // 70cl = 700ml
      break;
    case 'l':
      bottleSizeInMl = sizeValue * 1000; // 1L = 1000ml
      break;
    case 'ml':
      bottleSizeInMl = sizeValue; // already in ml
      break;
    default:
      bottleSizeInMl = sizeValue;
  }
  
  // Calculate full bottles
  const fullBottles = Math.floor(currentQtyInMl / bottleSizeInMl);
  
  // Calculate remaining ml
  const remainingMl = currentQtyInMl % bottleSizeInMl;
  
  return {
    fullBottles,
    remainingMl,
    totalMl: currentQtyInMl,
    display: `${fullBottles} bottles + ${remainingMl.toFixed(0)}ml`
  };
}

// Example usage
const item = {
  current_qty: 1450,  // ml
  size_value: 70,     // cl
  size_unit: 'cl'
};

const result = convertToBottles(item.current_qty, item.size_value, item.size_unit);
console.log(result);
// Output: {
//   fullBottles: 2,
//   remainingMl: 50,
//   totalMl: 1450,
//   display: "2 bottles + 50ml"
// }
```

### React Component for Displaying Quantities

```javascript
function StockQuantityDisplay({ item }) {
  const getBottleSizeInMl = () => {
    switch (item.size_unit?.toLowerCase()) {
      case 'cl': return item.size_value * 10;
      case 'l': return item.size_value * 1000;
      case 'ml': return item.size_value;
      default: return item.size_value;
    }
  };

  const bottleSizeInMl = getBottleSizeInMl();
  const fullBottles = Math.floor(item.current_qty / bottleSizeInMl);
  const remainingMl = item.current_qty % bottleSizeInMl;

  return (
    <div className="stock-quantity">
      <div className="bottles">
        <strong>{fullBottles}</strong> bottles
      </div>
      {remainingMl > 0 && (
        <div className="partial">
          + {remainingMl.toFixed(0)}ml
        </div>
      )}
      <div className="total-ml">
        Total: {item.current_qty}ml
      </div>
      <div className="par-level">
        Par: {Math.floor(item.par_level / bottleSizeInMl)} bottles 
        ({item.par_level}ml)
      </div>
    </div>
  );
}
```

### Quantity Display Examples

```javascript
// Example 1: Vodka (70cl bottles)
{
  size: "70cl",
  size_value: 70,
  size_unit: "cl",
  current_qty: 2100,  // ml
  // Display: "3 bottles (2100ml)"
}

// Example 2: Wine (750ml bottles)
{
  size: "750ml",
  size_value: 750,
  size_unit: "ml",
  current_qty: 2250,  // ml
  // Display: "3 bottles (2250ml)"
}

// Example 3: Partial bottle
{
  size: "70cl",
  size_value: 70,
  size_unit: "cl",
  current_qty: 1550,  // ml
  // Display: "2 bottles + 150ml (1550ml total)"
}

// Example 4: Keg (50L)
{
  size: "50L",
  size_value: 50,
  size_unit: "L",
  current_qty: 125000,  // ml (2.5 kegs)
  // Display: "2 kegs + 25000ml (125000ml total)"
}
```

### Important Notes

1. **Backend stores everything in ml** - Never assume bottles
2. **Frontend converts for display** - Calculate bottles from ml
3. **Partial quantities exist** - Handle remainders (opened bottles)
4. **Different container sizes** - Wine (750ml), Spirits (700ml), Kegs (50L)
5. **Stock movements in ml** - When creating movements, use ml not bottles

### Creating Movement with Bottle Conversion

```javascript
// User enters: "Add 3 bottles of vodka"
function createPurchaseMovement(item, numberOfBottles) {
  // Convert bottles to ml
  const bottleSizeInMl = item.size_unit === 'cl' 
    ? item.size_value * 10 
    : item.size_value;
  
  const quantityInMl = numberOfBottles * bottleSizeInMl;
  
  // Create movement with ml quantity
  return {
    item: item.id,
    movement_type: 'PURCHASE',
    quantity: quantityInMl,  // ← MUST BE IN ML
    unit_cost: item.unit_cost,
    reference: 'PO-12345'
  };
}

// Example: 3 bottles of 70cl vodka
const movement = createPurchaseMovement(vodkaItem, 3);
// movement.quantity = 2100 (ml)
```

---

### StockMovement
```typescript
interface StockMovement {
  id: number;
  hotel: number;
  item: number;
  item_code?: string;          // Read-only
  movement_type: 'PURCHASE' | 'SALE' | 'WASTE' | 
                 'TRANSFER_IN' | 'TRANSFER_OUT' | 'ADJUSTMENT';
  quantity: number;            // In base units (ml, g, pieces)
  unit_cost: number | null;    // Cost per base unit at time of movement
  reference?: string;          // Invoice #, PO #, Stocktake ID
  notes?: string;
  staff: number | null;
  staff_name?: string;         // Read-only
  timestamp: string;           // ISO datetime (read-only)
}
```

### Stocktake
```typescript
interface Stocktake {
  id: number;
  hotel: number;
  period_start: string;        // Date (YYYY-MM-DD)
  period_end: string;          // Date (YYYY-MM-DD)
  status: 'DRAFT' | 'APPROVED';
  is_locked: boolean;          // Read-only (true if APPROVED)
  created_at: string;          // ISO datetime
  approved_at: string | null;
  approved_by: number | null;
  approved_by_name?: string;   // Read-only
  notes?: string;
  lines?: StocktakeLine[];     // Included in detail view
  total_lines?: number;        // Read-only count
}
```

### StocktakeLine
```typescript
interface StocktakeLine {
  id: number;
  stocktake: number;
  item: number;
  item_code?: string;          // Read-only (SKU)
  item_description?: string;   // Read-only (name)
  category_name?: string;      // Read-only
  
  // Frozen opening values (set at populate)
  opening_qty: number;         // Read-only
  
  // Period movements (calculated, read-only)
  purchases: number;
  sales: number;
  waste: number;
  transfers_in: number;
  transfers_out: number;
  adjustments: number;
  
  // User input (editable if not locked)
  counted_full_units: number;  // Full cases/kegs/bottles
  counted_partial_units: number; // Partial units (e.g., 7 bottles)
  
  // Calculated quantities (read-only)
  counted_qty: number;         // = (full_units × uom) + partial_units
  expected_qty: number;        // = opening + purchases + transfers_in - sales - waste - transfers_out + adjustments
  variance_qty: number;        // = counted_qty - expected_qty
  
  // Valuation (frozen at populate, read-only)
  valuation_cost: number;
  expected_value: number;      // = expected_qty × valuation_cost
  counted_value: number;       // = counted_qty × valuation_cost
  variance_value: number;      // = counted_value - expected_value
}
```

---

## Getting Categories (Required First)

Before fetching items, you'll typically need to fetch categories for filtering and organization.

### Fetch All Categories

**JavaScript/Fetch:**
```javascript
async function getStockCategories(hotelIdentifier) {
  const response = await fetch(
    `/api/stock_tracker/${hotelIdentifier}/categories/`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const categories = await response.json();
  return categories;
}
```

**Axios:**
```javascript
async function getStockCategories(hotelIdentifier) {
  try {
    const response = await axios.get(
      `/api/stock_tracker/${hotelIdentifier}/categories/`,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching categories:', error);
    throw error;
  }
}
```

### React Hook Example

```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

function useStockCategories(hotelIdentifier) {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        setLoading(true);
        const response = await axios.get(
          `/api/stock_tracker/${hotelIdentifier}/categories/`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );
        setCategories(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (hotelIdentifier) {
      fetchCategories();
    }
  }, [hotelIdentifier]);

  return { categories, loading, error };
}

// Usage in component
function StockManagement({ hotelIdentifier }) {
  const { categories, loading, error } = useStockCategories(hotelIdentifier);

  if (loading) return <div>Loading categories...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Categories</h2>
      <ul>
        {categories.map(cat => (
          <li key={cat.id}>
            {cat.name} (Order: {cat.sort_order})
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### Category Response Example

```json
[
  {
    "id": 1,
    "hotel": 1,
    "name": "Spirits",
    "sort_order": 1
  },
  {
    "id": 2,
    "hotel": 1,
    "name": "Aperitif",
    "sort_order": 2
  },
  {
    "id": 3,
    "hotel": 1,
    "name": "Fortified",
    "sort_order": 3
  },
  {
    "id": 4,
    "hotel": 1,
    "name": "Liqueurs",
    "sort_order": 4
  },
  {
    "id": 5,
    "hotel": 1,
    "name": "Minerals",
    "sort_order": 5
  },
  {
    "id": 6,
    "hotel": 1,
    "name": "Wines",
    "sort_order": 6
  },
  {
    "id": 7,
    "hotel": 1,
    "name": "Beers",
    "sort_order": 7
  }
]
```

---

## 🚨 Important: No Pagination - All Results Returned

**All stock tracker endpoints return complete datasets without pagination.**

- ✅ **No page limits**: Get all items, categories, movements, etc. in one request
- ✅ **No page parameters**: No need for `?page=1`, `?offset=0`, or `?limit=100`
- ✅ **Full dataset**: Response is a plain array, not a paginated object
- ⚠️ **Client-side filtering**: Handle large datasets with local filtering/search
- ⚠️ **Performance**: Consider implementing virtual scrolling for large lists

**Response Format:**
```json
// ✅ Direct array - NO pagination wrapper
[
  { "id": 1, "name": "Item 1", ... },
  { "id": 2, "name": "Item 2", ... },
  { "id": 3, "name": "Item 3", ... }
]

// ❌ NOT like this (no pagination object):
{
  "count": 100,
  "next": "...",
  "previous": "...",
  "results": [...]
}
```

---

## 🔍 Filtering Stock Items by Category

### Single Category Filter

**Endpoint:** `GET /api/stock_tracker/{hotel_identifier}/items/?category={categoryId}`

```javascript
// Filter by single category
async function getItemsByCategory(hotelIdentifier, categoryId) {
  const response = await fetch(
    `/api/stock_tracker/${hotelIdentifier}/items/?category=${categoryId}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const items = await response.json();
  return items; // Returns ALL items for this category
}

// Example: Get all spirits
const spirits = await getItemsByCategory('hotel-killarney', 1);
```

### Multiple Categories Filter

**Endpoint:** `GET /api/stock_tracker/{hotel_identifier}/items/?category=1&category=2&category=3`

```javascript
// Filter by multiple categories
async function getItemsByMultipleCategories(hotelIdentifier, categoryIds) {
  const categoryParams = categoryIds.map(id => `category=${id}`).join('&');
  const url = `/api/stock_tracker/${hotelIdentifier}/items/?${categoryParams}`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  
  return await response.json();
}

// Example: Get spirits, wines, and beers
const beverages = await getItemsByMultipleCategories('hotel-killarney', [1, 6, 7]);
```

### Category Filter with React Hooks

```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

function useFilteredStockItems(hotelIdentifier, selectedCategoryIds = []) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchItems = async () => {
      if (!hotelIdentifier) return;
      
      try {
        setLoading(true);
        setError(null);
        
        // Build query params
        let url = `/api/stock_tracker/${hotelIdentifier}/items/`;
        
        if (selectedCategoryIds.length > 0) {
          const params = selectedCategoryIds.map(id => `category=${id}`).join('&');
          url += `?${params}`;
        }
        
        const response = await axios.get(url, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        
        setItems(response.data); // All items returned, no pagination
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchItems();
  }, [hotelIdentifier, selectedCategoryIds]);

  return { items, loading, error };
}

// Usage in component
function StockItemsWithCategoryFilter({ hotelIdentifier }) {
  const [selectedCategories, setSelectedCategories] = useState([]);
  const { items, loading, error } = useFilteredStockItems(hotelIdentifier, selectedCategories);

  const handleCategoryToggle = (categoryId) => {
    setSelectedCategories(prev => 
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  if (loading) return <div>Loading items...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Stock Items</h2>
      <p>Total items: {items.length}</p>
      {/* Category checkboxes would go here */}
      <ul>
        {items.map(item => (
          <li key={item.id}>{item.name} - {item.category_name}</li>
        ))}
      </ul>
    </div>
  );
}
```

### Combined Filters: Category + Search

```javascript
async function filterItemsByCategoryAndSearch(hotelIdentifier, categoryIds, searchTerm) {
  const params = new URLSearchParams();
  
  // Add category filters
  categoryIds.forEach(id => params.append('category', id));
  
  // Add search term
  if (searchTerm) {
    params.append('search', searchTerm);
  }
  
  const url = `/api/stock_tracker/${hotelIdentifier}/items/?${params.toString()}`;
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  
  return await response.json();
}

// Example: Get vodka items from spirits and liqueurs categories
const vodkaItems = await filterItemsByCategoryAndSearch(
  'hotel-killarney',
  [1, 4], // Spirits and Liqueurs
  'vodka'
);
```

---

## Getting All Stock Items

### Basic GET Request (All Items)

**JavaScript/Fetch:**
```javascript
async function getAllStockItems(hotelIdentifier) {
  const response = await fetch(
    `/api/stock_tracker/${hotelIdentifier}/items/`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const items = await response.json();
  // items is a plain array with ALL stock items - no pagination
  console.log(`Loaded ${items.length} items`);
  return items;
}
```

**Axios:**
```javascript
import axios from 'axios';

async function getAllStockItems(hotelIdentifier) {
  try {
    const response = await axios.get(
      `/api/stock_tracker/${hotelIdentifier}/items/`,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    // response.data is a plain array with ALL items
    console.log(`Loaded ${response.data.length} items`);
    return response.data;
  } catch (error) {
    console.error('Error fetching stock items:', error);
    throw error;
  }
}
```

### Search Filtering

**Search by SKU, name, or description:**
```javascript
async function searchItems(hotelIdentifier, searchTerm) {
  const response = await fetch(
    `/api/stock_tracker/${hotelIdentifier}/items/?search=${encodeURIComponent(searchTerm)}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  return await response.json();
}
```

### React Example with State

```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function StockItemsList({ hotelIdentifier }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchItems = async () => {
      try {
        setLoading(true);
        const response = await axios.get(
          `/api/stock_tracker/${hotelIdentifier}/items/`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );
        setItems(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (hotelIdentifier) {
      fetchItems();
    }
  }, [hotelIdentifier]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Stock Items ({items.length})</h2>
      <table>
        <thead>
          <tr>
            <th>SKU</th>
            <th>Name</th>
            <th>Category</th>
            <th>Current Qty</th>
            <th>Unit Cost</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map(item => (
            <tr key={item.id}>
              <td>{item.sku}</td>
              <td>{item.name}</td>
              <td>{item.category_name || 'N/A'}</td>
              <td>{item.current_qty} {item.base_unit}</td>
              <td>€{item.unit_cost}</td>
              <td>
                <button onClick={() => handleEdit(item.id)}>Edit</button>
                <button onClick={() => handleDelete(item.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Displaying Item Data

### All Fields Display Component

```javascript
function StockItemDetail({ item }) {
  return (
    <div className="stock-item-detail">
      {/* Basic Info */}
      <section>
        <h3>Basic Information</h3>
        <div className="field">
          <label>SKU:</label>
          <span>{item.sku}</span>
        </div>
        <div className="field">
          <label>Name:</label>
          <span>{item.name}</span>
        </div>
        <div className="field">
          <label>Description:</label>
          <span>{item.description || 'N/A'}</span>
        </div>
        <div className="field">
          <label>Category:</label>
          <span>{item.category_name || 'N/A'}</span>
        </div>
      </section>

      {/* Classification */}
      <section>
        <h3>Classification</h3>
        <div className="field">
          <label>Product Type:</label>
          <span>{item.product_type}</span>
        </div>
        <div className="field">
          <label>Subtype:</label>
          <span>{item.subtype || 'N/A'}</span>
        </div>
        {item.tag && (
          <div className="field">
            <label>Tag:</label>
            <span className="badge">{item.tag}</span>
          </div>
        )}
      </section>

      {/* Size & Units */}
      <section>
        <h3>Size & Units</h3>
        <div className="field">
          <label>Size:</label>
          <span>{item.size}</span>
        </div>
        <div className="field">
          <label>Size Value:</label>
          <span>{item.size_value} {item.size_unit}</span>
        </div>
        <div className="field">
          <label>Units per Case (UOM):</label>
          <span>{item.uom}</span>
        </div>
        <div className="field">
          <label>Base Unit:</label>
          <span>{item.base_unit}</span>
        </div>
      </section>

      {/* Inventory */}
      <section>
        <h3>Inventory</h3>
        <div className="field">
          <label>Current Quantity:</label>
          <span className={item.is_below_par ? 'alert' : ''}>
            {item.current_qty} {item.base_unit}
          </span>
          {item.is_below_par && <span className="warning">⚠️ Below Par</span>}
        </div>
        <div className="field">
          <label>Par Level:</label>
          <span>{item.par_level} {item.base_unit}</span>
        </div>
        {item.bin_name && (
          <div className="field">
            <label>Location:</label>
            <span>{item.bin_name}</span>
          </div>
        )}
      </section>

      {/* Cost & Pricing */}
      <section>
        <h3>Cost & Pricing</h3>
        <div className="field">
          <label>Unit Cost:</label>
          <span>€{item.unit_cost.toFixed(2)}</span>
        </div>
        {item.cost_per_base && (
          <div className="field">
            <label>Cost per {item.base_unit}:</label>
            <span>€{item.cost_per_base.toFixed(4)}</span>
          </div>
        )}
        {item.case_cost && (
          <div className="field">
            <label>Case Cost:</label>
            <span>€{item.case_cost.toFixed(2)}</span>
          </div>
        )}
        {item.selling_price && (
          <div className="field">
            <label>Selling Price:</label>
            <span>€{item.selling_price.toFixed(2)}</span>
          </div>
        )}
        {item.gp_percentage && (
          <div className="field">
            <label>GP %:</label>
            <span className="highlight">{item.gp_percentage}%</span>
          </div>
        )}
      </section>

      {/* Pour Cost Calculator */}
      {item.serving_size && (
        <section>
          <h3>Pour Cost Calculator</h3>
          <div className="field">
            <label>Serving Size:</label>
            <span>{item.serving_size} {item.serving_unit}</span>
          </div>
          {item.menu_price && (
            <div className="field">
              <label>Menu Price:</label>
              <span>€{item.menu_price.toFixed(2)}</span>
            </div>
          )}
          {item.pour_cost && (
            <div className="field">
              <label>Pour Cost:</label>
              <span>€{item.pour_cost.toFixed(4)}</span>
            </div>
          )}
          {item.pour_cost_percentage && (
            <div className="field">
              <label>Pour Cost %:</label>
              <span>{item.pour_cost_percentage.toFixed(2)}%</span>
            </div>
          )}
          {item.profit_per_serving && (
            <div className="field">
              <label>Profit per Serving:</label>
              <span>€{item.profit_per_serving.toFixed(2)}</span>
            </div>
          )}
          {item.profit_margin_percentage && (
            <div className="field">
              <label>Profit Margin %:</label>
              <span className="success">{item.profit_margin_percentage.toFixed(2)}%</span>
            </div>
          )}
        </section>
      )}

      {/* Vendor/Origin */}
      {(item.vendor || item.country || item.region || item.producer) && (
        <section>
          <h3>Vendor & Origin</h3>
          {item.vendor && (
            <div className="field">
              <label>Vendor:</label>
              <span>{item.vendor}</span>
            </div>
          )}
          {item.country && (
            <div className="field">
              <label>Country:</label>
              <span>{item.country}</span>
            </div>
          )}
          {item.region && (
            <div className="field">
              <label>Region:</label>
              <span>{item.region}</span>
            </div>
          )}
          {item.subregion && (
            <div className="field">
              <label>Sub-region:</label>
              <span>{item.subregion}</span>
            </div>
          )}
          {item.producer && (
            <div className="field">
              <label>Producer:</label>
              <span>{item.producer}</span>
            </div>
          )}
          {item.vineyard && (
            <div className="field">
              <label>Vineyard:</label>
              <span>{item.vineyard}</span>
            </div>
          )}
        </section>
      )}

      {/* Product Attributes */}
      {(item.abv_percent || item.vintage) && (
        <section>
          <h3>Product Attributes</h3>
          {item.abv_percent && (
            <div className="field">
              <label>ABV:</label>
              <span>{item.abv_percent}%</span>
            </div>
          )}
          {item.vintage && (
            <div className="field">
              <label>Vintage:</label>
              <span>{item.vintage}</span>
            </div>
          )}
        </section>
      )}

      {/* Barcodes */}
      {(item.unit_upc || item.case_upc) && (
        <section>
          <h3>Barcodes</h3>
          {item.unit_upc && (
            <div className="field">
              <label>Unit UPC:</label>
              <span>{item.unit_upc}</span>
            </div>
          )}
          {item.case_upc && (
            <div className="field">
              <label>Case UPC:</label>
              <span>{item.case_upc}</span>
            </div>
          )}
        </section>
      )}

      {/* Status */}
      <section>
        <h3>Status</h3>
        <div className="field">
          <label>Active:</label>
          <span>{item.active ? '✅ Yes' : '❌ No'}</span>
        </div>
        <div className="field">
          <label>Hide on Menu:</label>
          <span>{item.hide_on_menu ? 'Yes' : 'No'}</span>
        </div>
      </section>
    </div>
  );
}
```

### Table View with Computed Properties

```javascript
function StockItemsTable({ items }) {
  return (
    <table className="stock-table">
      <thead>
        <tr>
          <th>SKU</th>
          <th>Name</th>
          <th>Category</th>
          <th>Type</th>
          <th>Size</th>
          <th>Qty</th>
          <th>Par</th>
          <th>Cost</th>
          <th>Price</th>
          <th>GP%</th>
          <th>Pour Cost</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {items.map(item => (
          <tr key={item.id} className={item.is_below_par ? 'below-par' : ''}>
            <td><code>{item.sku}</code></td>
            <td><strong>{item.name}</strong></td>
            <td>{item.category_name}</td>
            <td>
              {item.product_type}
              {item.subtype && <small><br/>{item.subtype}</small>}
            </td>
            <td>{item.size}</td>
            <td>
              {item.current_qty}
              {item.is_below_par && <span className="warning"> ⚠️</span>}
            </td>
            <td>{item.par_level}</td>
            <td>€{item.unit_cost.toFixed(2)}</td>
            <td>{item.selling_price ? `€${item.selling_price.toFixed(2)}` : 'N/A'}</td>
            <td>{item.gp_percentage ? `${item.gp_percentage}%` : 'N/A'}</td>
            <td>
              {item.pour_cost 
                ? `€${item.pour_cost.toFixed(4)}` 
                : 'N/A'
              }
            </td>
            <td>
              {item.active 
                ? <span className="badge success">Active</span>
                : <span className="badge inactive">Inactive</span>
              }
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

## Creating New Items

### POST Request

```javascript
async function createStockItem(hotelIdentifier, itemData, accessToken) {
  try {
    const response = await axios.post(
      `/api/stock_tracker/${hotelIdentifier}/items/`,
      itemData,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error creating stock item:', error.response?.data);
    throw error;
  }
}
```

### Form Component Example

```javascript
function CreateStockItemForm({ hotelId, hotelIdentifier, categories, onSuccess }) {
  const [formData, setFormData] = useState({
    hotel: hotelId,
    sku: '',
    name: '',
    category: null,
    product_type: '',
    subtype: '',
    size: '',
    size_value: '',
    size_unit: 'cl',
    uom: 1,
    base_unit: 'ml',
    unit_cost: 0,
    current_qty: 0,
    par_level: 0,
    active: true
  });

  const [errors, setErrors] = useState({});

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const accessToken = localStorage.getItem('access_token');
      const newItem = await createStockItem(
        hotelIdentifier,
        formData,
        accessToken
      );
      alert('Stock item created successfully!');
      onSuccess(newItem);
    } catch (error) {
      if (error.response?.data) {
        setErrors(error.response.data);
      }
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Create Stock Item</h2>
      
      {/* Core fields */}
      <div className="form-group">
        <label>SKU *</label>
        <input
          type="text"
          name="sku"
          value={formData.sku}
          onChange={handleChange}
          required
        />
        {errors.sku && <span className="error">{errors.sku[0]}</span>}
      </div>

      <div className="form-group">
        <label>Name *</label>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
        />
        {errors.name && <span className="error">{errors.name[0]}</span>}
      </div>

      <div className="form-group">
        <label>Category</label>
        <select
          name="category"
          value={formData.category || ''}
          onChange={handleChange}
        >
          <option value="">-- Select Category --</option>
          {categories.map(cat => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>Product Type</label>
        <input
          type="text"
          name="product_type"
          value={formData.product_type}
          onChange={handleChange}
          placeholder="Vodka, Whiskey, Beer, Wine"
        />
      </div>

      <div className="form-group">
        <label>Subtype</label>
        <input
          type="text"
          name="subtype"
          value={formData.subtype}
          onChange={handleChange}
          placeholder="Irish, IPA, Red, Sparkling"
        />
      </div>

      {/* Size fields */}
      <div className="form-row">
        <div className="form-group">
          <label>Size *</label>
          <input
            type="text"
            name="size"
            value={formData.size}
            onChange={handleChange}
            placeholder="70cl, 30L, 500ml"
            required
          />
        </div>
        
        <div className="form-group">
          <label>Size Value</label>
          <input
            type="number"
            step="0.01"
            name="size_value"
            value={formData.size_value}
            onChange={handleChange}
            placeholder="70"
          />
        </div>
        
        <div className="form-group">
          <label>Size Unit</label>
          <select
            name="size_unit"
            value={formData.size_unit}
            onChange={handleChange}
          >
            <option value="ml">ml</option>
            <option value="cl">cl</option>
            <option value="L">L</option>
            <option value="g">g</option>
            <option value="kg">kg</option>
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>UOM (Units per Case) *</label>
          <input
            type="number"
            step="0.01"
            name="uom"
            value={formData.uom}
            onChange={handleChange}
            placeholder="12, 24, 1"
            required
          />
        </div>
        
        <div className="form-group">
          <label>Base Unit</label>
          <select
            name="base_unit"
            value={formData.base_unit}
            onChange={handleChange}
          >
            <option value="ml">ml</option>
            <option value="L">L</option>
            <option value="g">g</option>
            <option value="kg">kg</option>
            <option value="pieces">pieces</option>
          </select>
        </div>
      </div>

      {/* Cost & Inventory */}
      <div className="form-row">
        <div className="form-group">
          <label>Unit Cost *</label>
          <input
            type="number"
            step="0.0001"
            name="unit_cost"
            value={formData.unit_cost}
            onChange={handleChange}
            required
          />
        </div>
        
        <div className="form-group">
          <label>Current Quantity</label>
          <input
            type="number"
            step="0.0001"
            name="current_qty"
            value={formData.current_qty}
            onChange={handleChange}
          />
        </div>
        
        <div className="form-group">
          <label>Par Level</label>
          <input
            type="number"
            step="0.0001"
            name="par_level"
            value={formData.par_level}
            onChange={handleChange}
          />
        </div>
      </div>

      <div className="form-group">
        <label>
          <input
            type="checkbox"
            name="active"
            checked={formData.active}
            onChange={handleChange}
          />
          Active
        </label>
      </div>

      <button type="submit" className="btn-primary">Create Item</button>
    </form>
  );
}
```

---

## 📋 Complete Category Filtering Implementation

### Full React Component with Multi-Category Selection

```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function StockInventoryWithCategoryFilter({ hotelIdentifier }) {
  const [categories, setCategories] = useState([]);
  const [selectedCategoryIds, setSelectedCategoryIds] = useState([]);
  const [items, setItems] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);

  // 1. Fetch categories on mount
  useEffect(() => {
    fetchCategories();
  }, [hotelIdentifier]);

  // 2. Fetch items when filters change
  useEffect(() => {
    fetchFilteredItems();
  }, [selectedCategoryIds, searchTerm]);

  const fetchCategories = async () => {
    try {
      const response = await axios.get(
        `/api/stock_tracker/${hotelIdentifier}/categories/`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );
      setCategories(response.data); // All categories, no pagination
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchFilteredItems = async () => {
    try {
      setLoading(true);
      
      // Build URL with category filters
      const params = new URLSearchParams();
      
      // Add each selected category
      selectedCategoryIds.forEach(id => {
        params.append('category', id);
      });
      
      // Add search term if present
      if (searchTerm.trim()) {
        params.append('search', searchTerm);
      }
      
      const url = `/api/stock_tracker/${hotelIdentifier}/items/?${params.toString()}`;
      
      const response = await axios.get(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      setItems(response.data); // All matching items, no pagination
    } catch (error) {
      console.error('Error fetching items:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryToggle = (categoryId) => {
    setSelectedCategoryIds(prev => 
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId) // Remove if already selected
        : [...prev, categoryId] // Add if not selected
    );
  };

  const handleSelectAllCategories = () => {
    setSelectedCategoryIds(categories.map(cat => cat.id));
  };

  const handleDeselectAllCategories = () => {
    setSelectedCategoryIds([]);
  };

  return (
    <div className="stock-inventory">
      <h1>Stock Inventory</h1>
      
      {/* Category Filters */}
      <div className="filters-section">
        <h2>Filter by Category</h2>
        
        <div className="category-actions">
          <button onClick={handleSelectAllCategories}>Select All</button>
          <button onClick={handleDeselectAllCategories}>Clear All</button>
        </div>
        
        <div className="category-checkboxes">
          {categories.map(category => (
            <label key={category.id} className="category-checkbox">
              <input
                type="checkbox"
                checked={selectedCategoryIds.includes(category.id)}
                onChange={() => handleCategoryToggle(category.id)}
              />
              {category.name}
            </label>
          ))}
        </div>
        
        {/* Search Box */}
        <div className="search-box">
          <input
            type="text"
            placeholder="Search by SKU, name, or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Results */}
      <div className="results-section">
        <h2>
          Stock Items 
          <span className="count">
            ({loading ? '...' : items.length} items)
          </span>
        </h2>
        
        {loading ? (
          <div>Loading items...</div>
        ) : (
          <table className="items-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Name</th>
                <th>Category</th>
                <th>Stock</th>
                <th>Par Level</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center' }}>
                    No items found
                  </td>
                </tr>
              ) : (
                items.map(item => (
                  <tr key={item.id}>
                    <td>{item.sku}</td>
                    <td>{item.name}</td>
                    <td>{item.category_name || 'N/A'}</td>
                    <td>{item.quantity_in_stock}</td>
                    <td>{item.par_level}</td>
                    <td>
                      {item.is_below_par ? (
                        <span className="status-warning">Below Par</span>
                      ) : (
                        <span className="status-ok">OK</span>
                      )}
                    </td>
                    <td>
                      <button onClick={() => viewDetails(item.id)}>View</button>
                      <button onClick={() => editItem(item.id)}>Edit</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default StockInventoryWithCategoryFilter;
```

### URL Examples Generated by Component

```
# No filters - all items
GET /api/stock_tracker/hotel-killarney/items/

# Single category
GET /api/stock_tracker/hotel-killarney/items/?category=1

# Multiple categories (Spirits + Wines)
GET /api/stock_tracker/hotel-killarney/items/?category=1&category=6

# Multiple categories with search
GET /api/stock_tracker/hotel-killarney/items/?category=1&category=4&search=vodka

# Search only
GET /api/stock_tracker/hotel-killarney/items/?search=jameson
```

### Key Points About Category Filtering

1. **No Pagination**: All endpoints return complete results
2. **Multiple Categories**: Use `?category=1&category=2&category=3` format
3. **Combine Filters**: Mix category filters with search terms
4. **Client-Side Filtering**: For complex logic (below par, date ranges), filter on client after receiving all data
5. **Performance**: All data loads at once - use debouncing for search, consider virtual scrolling for large lists

---

## Filtering and Searching

### Multiple Filters (Complete Example)

```javascript
function StockItemsWithFilters({ hotelIdentifier }) {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    category: '',
    search: '',
    belowPar: false
  });

  // Fetch categories on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch(
          `/api/stock_tracker/${hotelIdentifier}/categories/`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );
        const data = await response.json();
        setCategories(data);
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    };

    if (hotelIdentifier) {
      fetchCategories();
    }
  }, [hotelIdentifier]);

  // Fetch items when filters change
  useEffect(() => {
    fetchFilteredItems();
  }, [filters, hotelIdentifier]);

  const fetchFilteredItems = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        ...(filters.category && { category: filters.category }),
        ...(filters.search && { search: filters.search })
      });

      const response = await fetch(
        `/api/stock_tracker/${hotelIdentifier}/items/?${params.toString()}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      let data = await response.json();
      
      // Client-side filter for below par (if needed)
      if (filters.belowPar) {
        data = data.filter(item => item.is_below_par);
      }

      setItems(data);
    } catch (error) {
      console.error('Error fetching items:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="filters">
        <select
          value={filters.category}
          onChange={(e) => setFilters({...filters, category: e.target.value})}
        >
          <option value="">All Categories</option>
          {categories.map(cat => (
            <option key={cat.id} value={cat.id}>
              {cat.name}
            </option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Search SKU or name..."
          value={filters.search}
          onChange={(e) => setFilters({...filters, search: e.target.value})}
        />

        <label>
          <input
            type="checkbox"
            checked={filters.belowPar}
            onChange={(e) => setFilters({...filters, belowPar: e.target.checked})}
          />
          Below Par Only
        </label>
      </div>

      {loading ? (
        <div>Loading items...</div>
      ) : (
        <StockItemsTable items={items} />
      )}
    </div>
  );
}
```

### Organized by Category

```javascript
function StockItemsByCategory({ hotelIdentifier }) {
  const [categories, setCategories] = useState([]);
  const [itemsByCategory, setItemsByCategory] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const accessToken = localStorage.getItem('access_token');
        const headers = { 'Authorization': `Bearer ${accessToken}` };

        // Fetch categories
        const catResponse = await fetch(
          `/api/stock_tracker/${hotelIdentifier}/categories/`,
          { headers }
        );
        const cats = await catResponse.json();
        setCategories(cats);

        // Fetch all items
        const itemsResponse = await fetch(
          `/api/stock_tracker/${hotelIdentifier}/items/`,
          { headers }
        );
        const items = await itemsResponse.json();

        // Group items by category
        const grouped = {};
        cats.forEach(cat => {
          grouped[cat.id] = {
            category: cat,
            items: items.filter(item => item.category === cat.id)
          };
        });

        // Add uncategorized items
        const uncategorized = items.filter(item => !item.category);
        if (uncategorized.length > 0) {
          grouped['uncategorized'] = {
            category: { name: 'Uncategorized' },
            items: uncategorized
          };
        }

        setItemsByCategory(grouped);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (hotelIdentifier) {
      fetchData();
    }
  }, [hotelIdentifier]);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="stock-by-category">
      {categories
        .sort((a, b) => a.sort_order - b.sort_order)
        .map(category => {
          const categoryData = itemsByCategory[category.id];
          if (!categoryData || categoryData.items.length === 0) return null;

          return (
            <div key={category.id} className="category-section">
              <h2>{category.name}</h2>
              <div className="items-count">
                {categoryData.items.length} items
              </div>
              <StockItemsTable items={categoryData.items} />
            </div>
          );
        })}
    </div>
  );
}
```

---

## Stock Movements

### Recording a Purchase

```javascript
async function recordPurchase(hotelIdentifier, purchaseData, accessToken) {
  try {
    const response = await axios.post(
      `/api/stock_tracker/${hotelIdentifier}/movements/`,
      {
        hotel: purchaseData.hotelId,
        item: purchaseData.itemId,
        movement_type: 'PURCHASE',
        quantity: purchaseData.quantity,
        unit_cost: purchaseData.unitCost,
        reference: purchaseData.invoiceNumber,
        notes: purchaseData.notes,
        staff: purchaseData.staffId
      },
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('Error recording purchase:', error);
    throw error;
  }
}

// Usage
const purchaseData = {
  hotelId: 1,
  itemId: 58,  // Dingle Whiskey
  quantity: 840,  // 840ml (12 × 70ml bottles)
  unitCost: 0.05,
  invoiceNumber: 'INV-2024-001',
  notes: 'December stock delivery',
  staffId: 5
};

const movement = await recordPurchase(
  'hotel-killarney',
  purchaseData,
  accessToken
);
console.log('Purchase recorded:', movement);
// This automatically updates item.current_qty
```

### Recording Waste

```javascript
async function recordWaste(hotelIdentifier, wasteData, accessToken) {
  const response = await axios.post(
    `/api/stock_tracker/${hotelIdentifier}/movements/`,
    {
      hotel: wasteData.hotelId,
      item: wasteData.itemId,
      movement_type: 'WASTE',
      quantity: wasteData.quantity,  // Negative automatically applied
      notes: wasteData.reason,
      staff: wasteData.staffId
    },
    {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }
  );
  return response.data;
}
```

### Movement History

```javascript
async function getItemMovements(hotelIdentifier, itemId) {
  const response = await fetch(
    `/api/stock_tracker/${hotelIdentifier}/movements/?item=${itemId}`,
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return await response.json();
}

// Display movements
function MovementHistory({ movements }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Type</th>
          <th>Quantity</th>
          <th>Reference</th>
          <th>Staff</th>
        </tr>
      </thead>
      <tbody>
        {movements.map(mov => (
          <tr key={mov.id}>
            <td>{new Date(mov.timestamp).toLocaleString()}</td>
            <td>{mov.movement_type}</td>
            <td>{mov.quantity}</td>
            <td>{mov.reference || 'N/A'}</td>
            <td>{mov.staff_name || 'System'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

## Stocktake Workflow

### 1. Create Stocktake

```javascript
async function createStocktake(
  hotelIdentifier,
  hotelId,
  periodStart,
  periodEnd,
  accessToken
) {
  const response = await axios.post(
    `/api/stock_tracker/${hotelIdentifier}/stocktakes/`,
    {
      hotel: hotelId,
      period_start: periodStart,  // "2024-11-01"
      period_end: periodEnd,      // "2024-11-30"
      notes: 'Monthly stocktake November 2024'
    },
    {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }
  );
  return response.data;
}
```

### 2. Populate Stocktake Lines

```javascript
async function populateStocktake(
  hotelIdentifier,
  stocktakeId,
  accessToken
) {
  try {
    const response = await axios.post(
      `/api/stock_tracker/${hotelIdentifier}/stocktakes/${stocktakeId}/populate/`,
      {},
      {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      }
    );
    
    console.log(response.data.message);
    // "Created 120 stocktake lines"
    return response.data;
  } catch (error) {
    console.error('Error populating stocktake:', error.response?.data);
    throw error;
  }
}
```

### 3. Count & Update Lines

```javascript
async function updateStocktakeLine(
  hotelIdentifier,
  lineId,
  counts,
  accessToken
) {
  try {
    const response = await axios.patch(
      `/api/stock_tracker/${hotelIdentifier}/stocktake-lines/${lineId}/`,
      {
        counted_full_units: counts.fullUnits,
        counted_partial_units: counts.partialUnits
      },
      {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      }
    );
    return response.data;
  } catch (error) {
    if (error.response?.data?.error) {
      alert(error.response.data.error);  // "Cannot edit approved stocktake"
    }
    throw error;
  }
}

// Example: Count 10 full cases + 5 loose bottles
await updateStocktakeLine(
  'hotel-killarney',
  123,
  { fullUnits: 10, partialUnits: 5 },
  token
);
```

### 4. View Stocktake Lines

```javascript
async function getStocktakeLines(hotelIdentifier, stocktakeId) {
  const response = await fetch(
    `/api/stock_tracker/${hotelIdentifier}/stocktake-lines/?stocktake=${stocktakeId}`,
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return await response.json();
}

// Display stocktake lines
function StocktakeLines({ lines }) {
  return (
    <table>
      <thead>
        <tr>
          <th>SKU</th>
          <th>Item</th>
          <th>Opening</th>
          <th>Expected</th>
          <th>Counted</th>
          <th>Variance</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        {lines.map(line => (
          <tr key={line.id} className={line.variance_qty !== 0 ? 'has-variance' : ''}>
            <td>{line.item_code}</td>
            <td>{line.item_description}</td>
            <td>{line.opening_qty}</td>
            <td>{line.expected_qty.toFixed(2)}</td>
            <td>{line.counted_qty.toFixed(2)}</td>
            <td className={line.variance_qty > 0 ? 'surplus' : 'shortage'}>
              {line.variance_qty > 0 ? '+' : ''}{line.variance_qty.toFixed(2)}
            </td>
            <td>€{line.variance_value.toFixed(2)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### 5. Approve Stocktake

```javascript
async function approveStocktake(
  hotelIdentifier,
  stocktakeId,
  accessToken
) {
  try {
    const response = await axios.post(
      `/api/stock_tracker/${hotelIdentifier}/stocktakes/${stocktakeId}/approve/`,
      {},
      {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      }
    );
    
    console.log(response.data.message);
    // "Stocktake approved"
    console.log(`${response.data.adjustments_created} adjustments created`);
    return response.data;
  } catch (error) {
    alert(error.response?.data?.error || 'Error approving stocktake');
    throw error;
  }
}
```

### 6. Category Totals

```javascript
async function getCategoryTotals(
  hotelIdentifier,
  stocktakeId,
  accessToken
) {
  const response = await axios.get(
    `/api/stock_tracker/${hotelIdentifier}/stocktakes/${stocktakeId}/category-totals/`,
    {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }
  );
  return response.data;
}

// Display category totals
function CategoryTotals({ totals }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Category</th>
          <th>Expected Value</th>
          <th>Counted Value</th>
          <th>Variance</th>
        </tr>
      </thead>
      <tbody>
        {totals.map(cat => (
          <tr key={cat.category_name}>
            <td>{cat.category_name}</td>
            <td>€{cat.expected_value.toFixed(2)}</td>
            <td>€{cat.counted_value.toFixed(2)}</td>
            <td className={cat.variance_value > 0 ? 'surplus' : 'shortage'}>
              €{cat.variance_value.toFixed(2)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

## Error Handling

### Common Error Responses

```javascript
async function handleApiCall(apiFunction, ...args) {
  try {
    return await apiFunction(...args);
  } catch (error) {
    if (error.response) {
      // Server responded with error
      const status = error.response.status;
      const data = error.response.data;

      switch (status) {
        case 400:
          // Validation errors
          console.error('Validation errors:', data);
          if (data.error) {
            alert(data.error);
          } else {
            // Field-specific errors
            Object.keys(data).forEach(field => {
              console.error(`${field}: ${data[field]}`);
            });
          }
          break;

        case 401:
          // Unauthorized - token expired
          alert('Session expired. Please log in again.');
          // Redirect to login
          break;

        case 403:
          // Forbidden
          alert('You do not have permission to perform this action.');
          break;

        case 404:
          // Not found
          alert('Resource not found.');
          break;

        case 500:
          // Server error
          alert('Server error. Please try again later.');
          break;

        default:
          alert(`Error: ${status}`);
      }
    } else if (error.request) {
      // Request made but no response
      alert('Network error. Please check your connection.');
    } else {
      // Something else happened
      alert('An unexpected error occurred.');
    }
    
    throw error;
  }
}

// Usage
try {
  const item = await handleApiCall(createStockItem, itemData, token);
  console.log('Success:', item);
} catch (error) {
  // Error already handled
}
```

### Field Validation Example

```javascript
function validateStockItemForm(formData) {
  const errors = {};

  // Required fields
  if (!formData.sku || formData.sku.trim() === '') {
    errors.sku = 'SKU is required';
  }

  if (!formData.name || formData.name.trim() === '') {
    errors.name = 'Name is required';
  }

  if (!formData.size || formData.size.trim() === '') {
    errors.size = 'Size is required';
  }

  // Numeric validations
  if (formData.uom <= 0) {
    errors.uom = 'UOM must be greater than 0';
  }

  if (formData.unit_cost < 0) {
    errors.unit_cost = 'Unit cost cannot be negative';
  }

  if (formData.current_qty < 0) {
    errors.current_qty = 'Current quantity cannot be negative';
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

// In your form
const handleSubmit = async (e) => {
  e.preventDefault();
  
  const validation = validateStockItemForm(formData);
  
  if (!validation.isValid) {
    setErrors(validation.errors);
    return;
  }

  // Proceed with API call...
};
```

---

## Summary

### Key Points

1. **All fields are accessible** - Even if not saved in DB, all model fields defined in `StockItem` are available via the API
2. **Computed properties** - Fields like `gp_percentage`, `is_below_par`, `pour_cost`, etc. are auto-calculated server-side
3. **Filtering** - Use query params: `?hotel=1&category=5&search=vodka`
4. **Stock movements automatically update** - Creating movements updates `current_qty` automatically
5. **Stocktake workflow** - Create → Populate → Count → Approve (locked after approval)
6. **Error handling** - Check status codes and handle field-specific validation errors

### Quick Reference

| Action | Endpoint | Method |
|--------|----------|--------|
| Get all items | `/api/stock_tracker/{hotel_identifier}/items/` | GET |
| Get item detail | `/api/stock_tracker/{hotel_identifier}/items/{id}/` | GET |
| Create item | `/api/stock_tracker/{hotel_identifier}/items/` | POST |
| Update item | `/api/stock_tracker/{hotel_identifier}/items/{id}/` | PUT/PATCH |
| Delete item | `/api/stock_tracker/{hotel_identifier}/items/{id}/` | DELETE |
| Record movement | `/api/stock_tracker/{hotel_identifier}/movements/` | POST |
| Create stocktake | `/api/stock_tracker/{hotel_identifier}/stocktakes/` | POST |
| Populate stocktake | `/api/stock_tracker/{hotel_identifier}/stocktakes/{id}/populate/` | POST |
| Update line | `/api/stock_tracker/{hotel_identifier}/stocktake-lines/{id}/` | PATCH |
| Approve stocktake | `/api/stock_tracker/{hotel_identifier}/stocktakes/{id}/approve/` | POST |

---

## Next Steps

- Implement pagination if you have large inventories
- Add real-time updates with WebSockets for collaborative counting
- Build reporting dashboards for variance analysis
- Create mobile-friendly counting interfaces
- Add barcode scanning for faster stocktaking

For more details, refer to the Stock Tracker models and serializers in the backend codebase.
