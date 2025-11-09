# Frontend Implementation Guide - Waste, Purchase, Sale Movements

## 🎯 Complete Flow with Optimistic Updates

### Overview
When user enters waste (or purchase/sale), the UI updates **immediately** (optimistic), then sends to backend which saves to database and returns confirmed data.

---

## 📱 React Component Example

```jsx
import { useState } from 'react';
import axios from 'axios';

function StocktakeLine({ line, onUpdate }) {
  const [isLoading, setIsLoading] = useState(false);
  const [wasteQuantity, setWasteQuantity] = useState('');
  const [wasteNotes, setWasteNotes] = useState('');

  // Calculate current expected and variance
  const expected = line.opening_qty + line.purchases - line.sales - line.waste;
  const variance = line.counted_qty - expected;

  const handleAddWaste = async () => {
    if (!wasteQuantity || wasteQuantity <= 0) return;

    setIsLoading(true);

    // 1️⃣ OPTIMISTIC UPDATE - Update UI immediately
    const newWaste = parseFloat(line.waste) + parseFloat(wasteQuantity);
    const newExpected = line.opening_qty + line.purchases - line.sales - newWaste;
    const newVariance = line.counted_qty - newExpected;

    // Update parent component immediately (optimistic)
    onUpdate({
      ...line,
      waste: newWaste,
      expected_qty: newExpected,
      variance_qty: newVariance
    });

    try {
      // 2️⃣ SEND TO BACKEND
      const response = await axios.post(
        `/api/hotels/${line.hotel}/stock-tracker/stocktake-lines/${line.id}/add-movement/`,
        {
          movement_type: 'WASTE',
          quantity: parseFloat(wasteQuantity),
          notes: wasteNotes || `Waste entry: ${wasteQuantity} units`
        }
      );

      // 3️⃣ CONFIRM WITH REAL DATA from backend
      onUpdate(response.data.line);

      // Clear form
      setWasteQuantity('');
      setWasteNotes('');

      alert('✅ Waste recorded successfully!');
    } catch (error) {
      // 4️⃣ ROLLBACK on error - revert to original
      onUpdate(line);
      alert('❌ Failed to save waste: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="stocktake-line">
      {/* Display current data */}
      <div className="line-info">
        <h3>{line.item_name}</h3>
        <p>Opening: {line.opening_qty}</p>
        <p>Purchases: {line.purchases}</p>
        <p>Sales: {line.sales}</p>
        <p>Waste: {line.waste}</p>
        <p><strong>Expected: {expected}</strong></p>
        <p>Counted: {line.counted_qty}</p>
        <p className={variance < 0 ? 'shortage' : 'surplus'}>
          <strong>Variance: {variance > 0 ? '+' : ''}{variance}</strong>
        </p>
      </div>

      {/* Waste input form */}
      <div className="waste-form">
        <h4>Record Waste</h4>
        <input
          type="number"
          placeholder="Quantity"
          value={wasteQuantity}
          onChange={(e) => setWasteQuantity(e.target.value)}
          min="0"
          step="0.1"
          disabled={isLoading}
        />
        <input
          type="text"
          placeholder="Notes (e.g., 'Dropped 5 bottles')"
          value={wasteNotes}
          onChange={(e) => setWasteNotes(e.target.value)}
          disabled={isLoading}
        />
        <button 
          onClick={handleAddWaste}
          disabled={isLoading || !wasteQuantity}
        >
          {isLoading ? 'Saving...' : '💥 Add Waste'}
        </button>
      </div>
    </div>
  );
}

export default StocktakeLine;
```

---

## 🔄 Optimistic Update Flow Explained

### Step-by-Step Process:

```
USER ACTION
    ↓
1. User enters: "5 bottles broke"
    ↓
2. OPTIMISTIC UPDATE (instant)
   - Calculate new waste: 0 + 5 = 5
   - Calculate new expected: 69 + 24 - 12 - 5 = 76
   - Calculate new variance: 76 - 76 = 0
   - Update UI immediately ⚡
    ↓
3. SEND TO BACKEND
   POST /stocktake-lines/123/add-movement/
   { "movement_type": "WASTE", "quantity": 5 }
    ↓
4a. SUCCESS ✅
   - Backend saves to database
   - Returns confirmed data
   - Update UI with real data
    ↓
4b. ERROR ❌
   - Backend failed
   - Rollback to original values
   - Show error message
```

---

## 📊 State Management (React)

### Option 1: Component State (Simple)

```jsx
function StocktakeList() {
  const [lines, setLines] = useState([]);

  const handleLineUpdate = (updatedLine) => {
    setLines(lines.map(line => 
      line.id === updatedLine.id ? updatedLine : line
    ));
  };

  return (
    <div>
      {lines.map(line => (
        <StocktakeLine 
          key={line.id}
          line={line}
          onUpdate={handleLineUpdate}
        />
      ))}
    </div>
  );
}
```

### Option 2: Redux/Context (Advanced)

```jsx
// actions.js
export const updateLineOptimistic = (lineId, changes) => ({
  type: 'UPDATE_LINE_OPTIMISTIC',
  payload: { lineId, changes }
});

export const confirmLineUpdate = (lineData) => ({
  type: 'CONFIRM_LINE_UPDATE',
  payload: lineData
});

export const rollbackLineUpdate = (lineId, originalData) => ({
  type: 'ROLLBACK_LINE_UPDATE',
  payload: { lineId, originalData }
});

// In component
const dispatch = useDispatch();

const handleAddWaste = async () => {
  const originalLine = { ...line };
  
  // Optimistic
  dispatch(updateLineOptimistic(line.id, { waste: newWaste }));
  
  try {
    const response = await api.addMovement(line.id, data);
    dispatch(confirmLineUpdate(response.data.line));
  } catch (error) {
    dispatch(rollbackLineUpdate(line.id, originalLine));
  }
};
```

---

## 🚀 Complete Example with All 3 Movement Types

```jsx
function MovementButtons({ line, onUpdate }) {
  const [quantity, setQuantity] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);

  const addMovement = async (movementType) => {
    if (!quantity) return;

    setLoading(true);
    const originalLine = { ...line };
    const qty = parseFloat(quantity);

    // Calculate optimistic update
    let optimisticLine = { ...line };
    
    switch(movementType) {
      case 'PURCHASE':
        optimisticLine.purchases = line.purchases + qty;
        break;
      case 'SALE':
        optimisticLine.sales = line.sales + qty;
        break;
      case 'WASTE':
        optimisticLine.waste = line.waste + qty;
        break;
    }

    // Recalculate expected and variance
    optimisticLine.expected_qty = 
      line.opening_qty + 
      optimisticLine.purchases - 
      optimisticLine.sales - 
      optimisticLine.waste;
    
    optimisticLine.variance_qty = 
      line.counted_qty - optimisticLine.expected_qty;

    // Update UI immediately
    onUpdate(optimisticLine);

    try {
      // Send to backend
      const response = await axios.post(
        `/api/hotels/${line.hotel}/stock-tracker/stocktake-lines/${line.id}/add-movement/`,
        {
          movement_type: movementType,
          quantity: qty,
          notes: notes
        }
      );

      // Confirm with real data
      onUpdate(response.data.line);
      setQuantity('');
      setNotes('');
      
    } catch (error) {
      // Rollback on error
      onUpdate(originalLine);
      alert(`Failed to add ${movementType}: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="movement-controls">
      <input
        type="number"
        placeholder="Quantity"
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        disabled={loading}
      />
      <input
        type="text"
        placeholder="Notes"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        disabled={loading}
      />
      
      <div className="button-group">
        <button 
          onClick={() => addMovement('PURCHASE')}
          disabled={loading || !quantity}
          className="btn-purchase"
        >
          📥 Purchase
        </button>
        
        <button 
          onClick={() => addMovement('SALE')}
          disabled={loading || !quantity}
          className="btn-sale"
        >
          💰 Sale
        </button>
        
        <button 
          onClick={() => addMovement('WASTE')}
          disabled={loading || !quantity}
          className="btn-waste"
        >
          💥 Waste
        </button>
      </div>
    </div>
  );
}
```

---

## 📡 API Request/Response

### Request Format

```javascript
// POST /api/hotels/{hotel}/stock-tracker/stocktake-lines/{line_id}/add-movement/

const payload = {
  movement_type: 'WASTE',      // Required: PURCHASE, SALE, or WASTE
  quantity: 5,                 // Required: number
  unit_cost: 2.50,             // Optional: for purchases
  reference: 'INV-001',        // Optional: invoice/reference number
  notes: 'Dropped 5 bottles'   // Optional: explanation
};

const response = await axios.post(url, payload);
```

### Response Format

```json
{
  "message": "Movement created successfully",
  "movement": {
    "id": 456,
    "movement_type": "WASTE",
    "quantity": "5.00",
    "timestamp": "2024-11-09T14:30:00Z"
  },
  "line": {
    "id": 123,
    "item_name": "Cronin's 0.0%",
    "opening_qty": "69.00",
    "purchases": "24.00",
    "sales": "12.00",
    "waste": "5.00",
    "expected_qty": "76.00",
    "counted_qty": "76.00",
    "variance_qty": "0.00"
  }
}
```

---

## 🎨 UI/UX Recommendations

### Visual Feedback

```jsx
function VarianceDisplay({ variance }) {
  const getVarianceColor = (v) => {
    if (v === 0) return 'green';
    if (v < 0) return 'red';
    return 'orange';
  };

  const getVarianceIcon = (v) => {
    if (v === 0) return '✅';
    if (v < 0) return '⚠️';
    return '📈';
  };

  return (
    <div style={{ color: getVarianceColor(variance) }}>
      {getVarianceIcon(variance)} Variance: {variance > 0 ? '+' : ''}{variance}
    </div>
  );
}
```

### Loading States

```jsx
<button disabled={loading}>
  {loading ? (
    <>
      <Spinner /> Saving...
    </>
  ) : (
    <>
      💥 Add Waste
    </>
  )}
</button>
```

### Success/Error Messages

```jsx
const [toast, setToast] = useState(null);

// After successful save
setToast({ type: 'success', message: '✅ Waste recorded!' });

// After error
setToast({ type: 'error', message: '❌ Failed to save' });

// Clear after 3 seconds
setTimeout(() => setToast(null), 3000);
```

---

## 🧪 Testing the Flow

### Test in Browser Console

```javascript
// Test optimistic update
async function testWasteEntry() {
  const lineId = 123;
  const hotel = 'your-hotel';
  
  console.log('1️⃣ Before:', lineData);
  
  // Optimistic update
  lineData.waste += 5;
  lineData.expected_qty = lineData.opening_qty + lineData.purchases - lineData.sales - lineData.waste;
  lineData.variance_qty = lineData.counted_qty - lineData.expected_qty;
  
  console.log('2️⃣ Optimistic:', lineData);
  
  // API call
  try {
    const response = await fetch(
      `/api/hotels/${hotel}/stock-tracker/stocktake-lines/${lineId}/add-movement/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movement_type: 'WASTE',
          quantity: 5,
          notes: 'Test waste entry'
        })
      }
    );
    
    const data = await response.json();
    console.log('3️⃣ Confirmed:', data.line);
    
  } catch (error) {
    console.log('4️⃣ Error - Rolling back:', error);
  }
}
```

---

## 📋 Complete Integration Checklist

- [ ] Install axios or fetch for API calls
- [ ] Create API service/utility functions
- [ ] Implement optimistic update logic
- [ ] Add rollback on error
- [ ] Show loading states during API calls
- [ ] Display success/error messages
- [ ] Update variance display in real-time
- [ ] Test with different movement types
- [ ] Handle edge cases (negative values, locked stocktakes)
- [ ] Add form validation
- [ ] Style buttons and forms
- [ ] Add keyboard shortcuts (optional)
- [ ] Test on mobile devices

---

## 🎯 Summary

**The Flow:**
1. User enters quantity → UI updates instantly (optimistic)
2. Send to backend → Backend saves to database
3. Backend recalculates → Returns confirmed data
4. Update UI with real data → Perfect sync!

**Backend is ready!** Just POST to:
```
/api/hotels/{hotel}/stock-tracker/stocktake-lines/{line_id}/add-movement/
```

**Your UI gets instant feedback**, database gets the truth! 🚀
