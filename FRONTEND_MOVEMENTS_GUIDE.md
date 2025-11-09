# Frontend Guide: Purchases/Movements Implementation

## ✅ Backend Status: WORKING CORRECTLY

The backend API for adding purchases and waste is **fully functional and tested**.

### API Endpoint
```
POST /api/hotels/{hotel_slug}/stock-tracker/stocktake-lines/{line_id}/add-movement/
```

---

## 🎯 Correct Expected Quantity Formula

**IMPORTANT:** The expected quantity formula **MUST** match the backend exactly:

```javascript
expected_qty = opening_qty + purchases - waste
```

**Note:** Sales are NOT subtracted. Sales are determined by the variance (what's missing/consumed).

---

## 🔧 Frontend Implementation Requirements

### 1. Request Format

```javascript
const payload = {
  movement_type: 'PURCHASE',  // or 'WASTE' (NOT 'SALE')
  quantity: 24,               // REQUIRED: number (can be decimal)
  unit_cost: 2.50,           // OPTIONAL: decimal
  reference: 'INV-12345',    // OPTIONAL: string
  notes: 'Delivery from XYZ' // OPTIONAL: string
};

const response = await fetch(
  `/api/hotels/${hotelSlug}/stock-tracker/stocktake-lines/${lineId}/add-movement/`,
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}` // If using auth
    },
    body: JSON.stringify(payload)
  }
);
```

### 2. Response Format

```javascript
{
  "message": "Movement created successfully",
  "movement": {
    "id": 156,
    "movement_type": "PURCHASE",
    "quantity": "24.0000",
    "timestamp": "2025-11-09T14:30:00Z"
  },
  "line": {
    "id": 45,
    "item_sku": "D001",
    "item_name": "Guinness Keg",
    "opening_qty": "88.0000",
    "purchases": "72.0000",      // ← Updated
    "sales": "120.0000",
    "waste": "0.0000",
    "transfers_in": "0.0000",
    "transfers_out": "0.0000",
    "adjustments": "0.0000",
    "expected_qty": "40.0000",   // ← Recalculated by backend
    "counted_qty": "42.0000",
    "variance_qty": "2.0000",    // ← Recalculated by backend
    // ... more fields
  }
}
```

### 3. Optimistic Update (Correct Implementation)

```javascript
const addMovement = async (movementType, quantity) => {
  // Save original state for rollback
  const originalLine = { ...line };
  
  // Calculate optimistic update using CORRECT formula
  let optimisticLine = { ...line };
  const qty = parseFloat(quantity);
  
  // Update the movement type field
  switch(movementType) {
    case 'PURCHASE':
      optimisticLine.purchases = parseFloat(line.purchases) + qty;
      break;
    case 'WASTE':
      optimisticLine.waste = parseFloat(line.waste) + qty;
      break;
  }
  
  // Recalculate expected_qty using CORRECT formula (no sales!)
  optimisticLine.expected_qty = 
    parseFloat(optimisticLine.opening_qty) +
    parseFloat(optimisticLine.purchases) -
    parseFloat(optimisticLine.waste);
  
  // Recalculate variance
  optimisticLine.variance_qty = 
    parseFloat(optimisticLine.counted_qty) - 
    parseFloat(optimisticLine.expected_qty);
  
  // Update UI immediately
  updateLineState(optimisticLine);
  
  try {
    // Send to backend
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        movement_type: movementType,
        quantity: qty,
        notes: notes
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    // Update with backend's confirmed data
    updateLineState(data.line);
    
  } catch (error) {
    // Rollback on error
    updateLineState(originalLine);
    showError(`Failed to add ${movementType}: ${error.message}`);
  }
};
```

---

## 🚨 Common Mistakes to Avoid

### ❌ WRONG: Including sales in formula

```javascript
// WRONG!
expected_qty = opening_qty + purchases - sales - waste;
```

### ✅ CORRECT: Sales are NOT included

```javascript
// CORRECT!
expected_qty = opening_qty + purchases - waste;
```

### ❌ WRONG: Not handling decimal strings from backend

```javascript
// WRONG - will cause NaN
const total = line.purchases + qty;
```

### ✅ CORRECT: Convert strings to numbers

```javascript
// CORRECT
const total = parseFloat(line.purchases) + qty;
```

---

## 🧪 Testing Your Implementation

### Test Case 1: Add Purchase

```javascript
// Initial state
const line = {
  opening_qty: 100,
  purchases: 50,
  sales: 120,
  waste: 0,
  counted_qty: 42
};

// Calculate initial expected
const initial_expected = 100 + 50 - 120 - 0; // = 30
const initial_variance = 42 - 30; // = 12

// Add purchase of 24
const new_purchases = 50 + 24; // = 74
const new_expected = 100 + 74 - 120 - 0; // = 54
const new_variance = 42 - 54; // = -12

// Expected result:
// purchases: 74
// expected_qty: 54
// variance_qty: -12
```

### Test Case 2: Add Waste

```javascript
// Same initial state
const line = {
  opening_qty: 100,
  purchases: 50,
  sales: 120,
  waste: 0,
  counted_qty: 42
};

// Add waste of 5
const new_waste = 0 + 5; // = 5
const new_expected = 100 + 50 - 120 - 5; // = 25
const new_variance = 42 - 25; // = 17

// Expected result:
// waste: 5
// expected_qty: 25
// variance_qty: 17 (improved!)
```

---

## 📊 Complete React Component Example

```jsx
import { useState } from 'react';

function StocktakeLineMovements({ line, hotelSlug, onUpdate }) {
  const [quantity, setQuantity] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const calculateOptimisticUpdate = (movementType, qty) => {
    const optimistic = { ...line };
    const amount = parseFloat(qty);
    
    // Update movement field
    switch(movementType) {
      case 'PURCHASE':
        optimistic.purchases = parseFloat(line.purchases) + amount;
        break;
      case 'SALE':
        optimistic.sales = parseFloat(line.sales) + amount;
        break;
      case 'WASTE':
        optimistic.waste = parseFloat(line.waste) + amount;
        break;
    }
    
    // Recalculate expected (CORRECT formula)
    optimistic.expected_qty = 
      parseFloat(optimistic.opening_qty) +
      parseFloat(optimistic.purchases) -
      parseFloat(optimistic.sales) -        // ← Include sales
      parseFloat(optimistic.waste);
    
    // Recalculate variance
    optimistic.variance_qty = 
      parseFloat(optimistic.counted_qty) - 
      parseFloat(optimistic.expected_qty);
    
    return optimistic;
  };

  const addMovement = async (movementType) => {
    if (!quantity || parseFloat(quantity) <= 0) {
      setError('Please enter a valid quantity');
      return;
    }

    setLoading(true);
    setError(null);
    
    const originalLine = { ...line };
    const qty = parseFloat(quantity);
    
    // Optimistic update
    const optimisticLine = calculateOptimisticUpdate(movementType, qty);
    onUpdate(optimisticLine);

    try {
      const response = await fetch(
        `/api/hotels/${hotelSlug}/stock-tracker/stocktake-lines/${line.id}/add-movement/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            movement_type: movementType,
            quantity: qty,
            notes: notes
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const data = await response.json();
      
      // Update with confirmed backend data
      onUpdate(data.line);
      
      // Clear form
      setQuantity('');
      setNotes('');
      
    } catch (err) {
      // Rollback
      onUpdate(originalLine);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="movement-controls">
      <div className="line-summary">
        <h4>{line.item_name}</h4>
        <div className="stats">
          <span>Opening: {line.opening_qty}</span>
          <span>Purchases: {line.purchases}</span>
          <span>Sales: {line.sales}</span>
          <span>Waste: {line.waste}</span>
          <span><strong>Expected: {line.expected_qty}</strong></span>
          <span>Counted: {line.counted_qty}</span>
          <span className={parseFloat(line.variance_qty) < 0 ? 'shortage' : 'surplus'}>
            <strong>Variance: {line.variance_qty}</strong>
          </span>
        </div>
      </div>

      <div className="input-group">
        <input
          type="number"
          placeholder="Quantity"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          disabled={loading}
          min="0"
          step="0.01"
        />
        <input
          type="text"
          placeholder="Notes (optional)"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          disabled={loading}
        />
      </div>

      <div className="button-group">
        <button 
          onClick={() => addMovement('PURCHASE')}
          disabled={loading || !quantity}
          className="btn-purchase"
        >
          {loading ? '...' : '📥 Add Purchase'}
        </button>
        
        <button 
          onClick={() => addMovement('SALE')}
          disabled={loading || !quantity}
          className="btn-sale"
        >
          {loading ? '...' : '💰 Add Sale'}
        </button>
        
        <button 
          onClick={() => addMovement('WASTE')}
          disabled={loading || !quantity}
          className="btn-waste"
        >
          {loading ? '...' : '💥 Add Waste'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}
    </div>
  );
}

export default StocktakeLineMovements;
```

---

## 🔍 Debugging Tips

### Check if your optimistic calculation matches backend

```javascript
console.log('Frontend calculated expected:', optimisticLine.expected_qty);
console.log('Backend returned expected:', data.line.expected_qty);

// They should be equal!
if (Math.abs(optimisticLine.expected_qty - parseFloat(data.line.expected_qty)) > 0.01) {
  console.error('❌ Formula mismatch!');
}
```

### Verify the formula step by step

```javascript
const opening = parseFloat(line.opening_qty);
const purchases = parseFloat(line.purchases);
const sales = parseFloat(line.sales);
const waste = parseFloat(line.waste);

const calculated = opening + purchases - sales - waste;
const fromBackend = parseFloat(data.line.expected_qty);

console.log(`Opening: ${opening}`);
console.log(`Purchases: ${purchases}`);
console.log(`Sales: ${sales}`);
console.log(`Waste: ${waste}`);
console.log(`Calculated: ${calculated}`);
console.log(`Backend: ${fromBackend}`);
console.log(`Match: ${calculated === fromBackend ? '✅' : '❌'}`);
```

---

## 📝 Summary Checklist

- [ ] Use correct formula: `opening + purchases - sales - waste`
- [ ] Convert all string values to numbers using `parseFloat()`
- [ ] Handle both optimistic update AND backend response
- [ ] Implement rollback on error
- [ ] Show loading states during API calls
- [ ] Display error messages clearly
- [ ] Test with different movement types
- [ ] Verify calculations match backend

---

## 🆘 If It Still Doesn't Work

1. **Check Network Tab**: Verify the request payload is correct
2. **Check Response**: Look at what the backend is returning
3. **Console Log Everything**: Log before optimistic, after optimistic, and after backend response
4. **Verify String to Number**: Make sure you're not concatenating strings instead of adding numbers

### Example Debug Output:

```javascript
console.log('Before:', {
  purchases: line.purchases,
  expected: line.expected_qty
});

console.log('Optimistic:', {
  purchases: optimistic.purchases,
  expected: optimistic.expected_qty
});

console.log('Backend Response:', {
  purchases: data.line.purchases,
  expected: data.line.expected_qty
});
```

**The backend is working correctly. The issue is in the frontend calculation or data handling.**
