# Manual Opening Stock & Purchases Entry - Frontend Implementation Guide

## Overview

Users can now update **opening stock** (`opening_qty`) and **purchases** directly in stocktake lines using the standard PATCH endpoint. All changes are:
- ✅ **Real-time**: Broadcast via Pusher to all users viewing the same stocktake
- ✅ **Automatic**: Backend recalculates `expected_qty`, `variance_qty`, and all values
- ✅ **Simple**: Uses existing `/api/stock-tracker/{hotel}/stocktake-lines/{id}/` endpoint

**Use cases:**
- First period setup (no previous period exists)
- Correcting historical data entry errors
- Fixing discrepancies found in audits
- Recording purchases alongside counted values

## Backend API Endpoint

### PATCH `/api/stock-tracker/{hotel_identifier}/stocktake-lines/{id}/`

**Permission:** Authenticated users (hotel staff)  
**Purpose:** Update any editable fields on a stocktake line including opening_qty, purchases, counted units, and manual values

**URL Parameters:**
- `hotel_identifier`: Hotel slug or subdomain (e.g., `the-grand-hotel` or `grand`)
- `id`: Stocktake line ID

**Request Body (all fields optional):**
```json
{
  "opening_qty": "100.0000",
  "purchases": "50.0000",
  "counted_full_units": "12.00",
  "counted_partial_units": "8.00",
  "manual_purchases_value": "150.00",
  "manual_waste_value": "25.00",
  "manual_sales_value": "500.00"
}
```

**Response 200 OK:**
```json
{
  "id": 12345,
  "stocktake": 16,
  "item": 42,
  "item_sku": "M0004",
  "item_name": "Split Fanta Lemon",
  "category_code": "M",
  "category_name": "Minerals & Syrups",
  
  "opening_qty": "100.0000",
  "purchases": "50.0000",
  "waste": "0.0000",
  "sales_qty": "75.0000",
  
  "expected_qty": "150.0000",
  "counted_qty": "148.0000",
  "variance_qty": "-2.0000",
  
  "opening_display_full_units": "8",
  "opening_display_partial_units": "4",
  "expected_display_full_units": "12",
  "expected_display_partial_units": "6",
  
  "opening_value": "117.54",
  "expected_value": "176.31",
  "counted_value": "173.96",
  "variance_value": "-2.35",
  
  "counted_full_units": "12.00",
  "counted_partial_units": "8.00",
  "valuation_cost": "1.1754"
}
```

**Response 400 Bad Request:**
```json
{
  "error": "Cannot update stocktake line for approved stocktake"
}
```

---

**Response 200 OK:**
```json
{
  "id": 12345,
  "stocktake": 16,
  "item": 42,
  "item_sku": "M0004",
  "item_name": "Split Fanta Lemon",
  "category_code": "M",
  
  "opening_qty": "100.0000",
  "purchases": "50.0000",
  "expected_qty": "150.0000",
  "counted_qty": "148.0000",
  "variance_qty": "-2.0000",
  
  "opening_value": "117.54",
  "expected_value": "176.31",
  "variance_value": "-2.35",
  
  "counted_full_units": "12.00",
  "counted_partial_units": "8.00"
}
```

---

## Real-Time Updates via Pusher

**Channel:** `{hotel_identifier}-stocktake-{stocktake_id}`  
**Event:** `line-counted-updated`

When any user updates `opening_qty`, `purchases`, or counted values, all users viewing the same stocktake receive real-time updates via Pusher.

**Event Payload:**
```json
{
  "line_id": 12345,
  "item_sku": "M0004",
  "line": { /* full line data */ }
}
```

**Frontend Subscription:**
```javascript
const channel = pusher.subscribe(`${hotelIdentifier}-stocktake-${stocktakeId}`);

channel.bind('line-counted-updated', (data) => {
  console.log('Line updated:', data.line_id, data.item_sku);
  // Update the line in your state
  updateLineInState(data.line);
});
```

---

## Frontend Implementation

### 1. UI Component - Inline Editing

**Location:** Stocktake counting page, editable fields in the table

**Example:** Show `opening_qty` and `purchases` as editable inputs
```jsx
<tr>
  <td>{line.item_sku}</td>
  <td>{line.item_name}</td>
  <td>
    <input
      type="number"
      step="0.0001"
      value={line.opening_qty}
      onChange={(e) => handleOpeningQtyChange(line.id, e.target.value)}
      onBlur={() => saveLineUpdates(line.id)}
      disabled={stocktake.status === 'APPROVED'}
    />
  </td>
  <td>
    <input
      type="number"
      step="0.0001"
      value={line.purchases}
      onChange={(e) => handlePurchasesChange(line.id, e.target.value)}
      onBlur={() => saveLineUpdates(line.id)}
      disabled={stocktake.status === 'APPROVED'}
    />
  </td>
  <td>{line.counted_full_units}</td>
  <td>{line.counted_partial_units}</td>
  <td className="calculated">{line.expected_qty}</td>
  <td className="calculated">{line.variance_qty}</td>
</tr>
```

### 2. API Call Handler

```javascript
import React, { useState } from 'react';

const StocktakeCountingPage = ({ hotelIdentifier, stocktakeId }) => {
  const [lines, setLines] = useState([]);
  const [loading, setLoading] = useState(false);

  // Update a single line via API
  const updateLine = async (lineId, updates) => {
    setLoading(true);
    
    try {
      // hotelIdentifier = hotel slug (e.g., 'the-grand-hotel')
      // or subdomain (e.g., 'grand')
      const response = await fetch(
        `/api/stock-tracker/${hotelIdentifier}/stocktake-lines/${lineId}/`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`,
          },
          body: JSON.stringify(updates),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update line');
      }

      const updatedLine = await response.json();
      console.log('✅ Line updated:', updatedLine);
      
      // Update local state
      setLines(prev => prev.map(line => 
        line.id === lineId ? updatedLine : line
      ));
      
      return updatedLine;
    } catch (err) {
      console.error('❌ Error updating line:', err);
      alert(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Handler for opening_qty changes
  const handleOpeningQtyChange = async (lineId, newValue) => {
    await updateLine(lineId, {
      opening_qty: parseFloat(newValue) || 0
    });
  };

  // Handler for purchases changes
  const handlePurchasesChange = async (lineId, newValue) => {
    await updateLine(lineId, {
      purchases: parseFloat(newValue) || 0
    });
  };

  // Handler for counted units changes
  const handleCountedUnitsChange = async (lineId, fullUnits, partialUnits) => {
    await updateLine(lineId, {
      counted_full_units: parseFloat(fullUnits) || 0,
      counted_partial_units: parseFloat(partialUnits) || 0
    });
  };

  // Batch update multiple fields at once
  const handleBatchUpdate = async (lineId, updates) => {
    await updateLine(lineId, {
      opening_qty: updates.opening_qty,
      purchases: updates.purchases,
      counted_full_units: updates.counted_full_units,
      counted_partial_units: updates.counted_partial_units,
      manual_purchases_value: updates.manual_purchases_value
    });
  };

  return (
    <div>
      {/* Your table with inline editing */}
    </div>
  );
};
```

### 3. Pusher Real-Time Integration

```javascript
import React, { useEffect, useState } from 'react';
import Pusher from 'pusher-js';

const StocktakeCountingPage = ({ hotelIdentifier, stocktakeId }) => {
  const [lines, setLines] = useState([]);

  useEffect(() => {
    // Subscribe to Pusher channel
    const pusher = new Pusher(PUSHER_KEY, {
      cluster: PUSHER_CLUSTER,
      encrypted: true
    });

    const channel = pusher.subscribe(
      `${hotelIdentifier}-stocktake-${stocktakeId}`
    );

    // Listen for line updates
    channel.bind('line-counted-updated', (data) => {
      console.log('📡 Received Pusher update:', data.line_id, data.item_sku);
      
      // Update the specific line in state
      setLines(prevLines => 
        prevLines.map(line => 
          line.id === data.line_id ? data.line : line
        )
      );
      
      // Optional: Show toast notification
      showToast(`${data.item_sku} updated by another user`);
    });

    // Cleanup on unmount
    return () => {
      channel.unbind_all();
      channel.unsubscribe();
      pusher.disconnect();
    };
  }, [hotelIdentifier, stocktakeId]);

  return (
    <div>
      {/* Your stocktake counting UI */}
    </div>
  );
};
```

### 4. Monitoring & Logging

**Console Logs to Include:**
```javascript
// Before API call
console.log('📝 Updating stocktake line:', {
  line_id: lineId,
  sku: line.item_sku,
  updates: updates,
  old_values: {
    opening_qty: line.opening_qty,
    purchases: line.purchases,
    counted_full: line.counted_full_units
  }
});

// After successful update
console.log('✅ Line updated:', {
  line_id: updatedLine.id,
  sku: updatedLine.item_sku,
  new_opening_qty: updatedLine.opening_qty,
  new_purchases: updatedLine.purchases,
  new_expected_qty: updatedLine.expected_qty,
  new_variance: updatedLine.variance_qty
});

// Pusher event received
console.log('📡 Received real-time update from Pusher:', {
  line_id: data.line_id,
  item_sku: data.item_sku,
  source: 'another_user'
});

// Error handling
console.error('❌ Failed to update line:', {
  line_id: lineId,
  sku: line.item_sku,
  error: error.message
});
```

---

### 5. User Flow

1. **User opens stocktake counting page**
2. **Sees editable fields for opening_qty, purchases, and counted units**
3. **Clicks on an input field and enters new value**
4. **On blur/Enter, API call is triggered**
5. **Backend:**
   - Updates the field(s)
   - Recalculates expected_qty, variance_qty
   - Broadcasts update via Pusher
   - Returns updated line data
6. **Frontend:**
   - Updates local state with response
   - All other users viewing same stocktake receive Pusher event
   - Their displays update in real-time
7. **User sees updated expected and variance values instantly**

---

### 6. Use Cases

**When to update opening_qty:**
- ✅ First period setup (no previous period exists)
- ✅ Correcting historical data entry errors
- ✅ Migrating from another system
- ✅ Fixing discrepancies found in audits

**When to update purchases:**
- ✅ Recording deliveries/purchases during the period
- ✅ Correcting purchase entry errors
- ✅ Adding missing purchase data

**When NOT to edit:**
- ❌ Stocktake already approved (locked)
- ❌ Trying to manipulate variance artificially

---

### 7. Validation Rules

**Backend validates:**
- Stocktake must not be approved
- Values must be numeric
- No negative values (implied by Decimal fields)

**Frontend should validate:**
- Numeric input only
- Disable inputs if stocktake.status === 'APPROVED'
- Show warning if drastically different from expected
- Debounce rapid changes to avoid excessive API calls

---

## Testing Checklist

- [ ] Can edit opening_qty and see expected_qty update
- [ ] Can edit purchases and see expected_qty update
- [ ] Can edit counted units and see variance update
- [ ] Cannot edit approved stocktake (inputs disabled)
- [ ] Pusher events received when another user edits
- [ ] Console logs show before/after values
- [ ] API errors display properly to user
- [ ] Multiple simultaneous edits handled gracefully
- [ ] Real-time updates don't overwrite current user's typing
- [ ] Values persist after page reload

---

## Quick Start Example

```javascript
// Update opening stock
await updateLine(lineId, { opening_qty: "150.0000" });

// Update purchases
await updateLine(lineId, { purchases: "25.0000" });

// Update counted units
await updateLine(lineId, {
  counted_full_units: "10.00",
  counted_partial_units: "5.00"
});

// Batch update multiple fields
await updateLine(lineId, {
  opening_qty: "150.0000",
  purchases: "25.0000",
  counted_full_units: "10.00",
  counted_partial_units: "5.00",
  manual_purchases_value: "75.00"
});
```

---

## Backend Implementation

✅ **Backend is ready** - The standard PATCH endpoint at `/api/stock-tracker/{hotel}/stocktake-lines/{id}/` now accepts `opening_qty` and `purchases` as writable fields. All calculations update automatically, and Pusher broadcasts are sent to all connected users.
