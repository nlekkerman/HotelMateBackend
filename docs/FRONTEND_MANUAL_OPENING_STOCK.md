# Manual Opening Stock Entry - Frontend Implementation Guide

## Overview
Allow superusers to manually update opening stock quantities for stocktake lines when automatic population from previous period is incorrect or unavailable.

## Backend API Endpoint

### PATCH `/api/stock-tracker/stocktake-lines/{id}/update-opening/`

**Permission:** Superuser only  
**Purpose:** Manually update opening stock for a specific stocktake line

**Request Body:**
```json
{
  "opening_full_units": 10.00,
  "opening_partial_units": 5.50
}
```

**Response 200 OK:**
```json
{
  "id": 12345,
  "item_sku": "M0004",
  "item_name": "Split Fanta Lemon",
  "opening_full_units": 10.00,
  "opening_partial_units": 5.50,
  "opening_qty": 245.50,
  "opening_value": 117.54,
  "expected_qty": 245.50,
  "expected_value": 117.54,
  "message": "Opening stock updated successfully"
}
```

**Response 403 Forbidden:**
```json
{
  "error": "Only superusers can manually update opening stock"
}
```

**Response 400 Bad Request:**
```json
{
  "error": "Cannot update opening stock for approved stocktake"
}
```

---

## Frontend Implementation

### 1. UI Component - Opening Stock Edit Modal

**Location:** Stocktake counting page, accessible per line item

**Button:** Only visible to superusers
```jsx
{user.is_superuser && stocktake.status !== 'APPROVED' && (
  <button 
    onClick={() => openEditOpeningModal(line)}
    className="edit-opening-btn"
  >
    ✏️ Edit Opening
  </button>
)}
```

**Modal Form:**
```jsx
import React, { useState } from 'react';

const EditOpeningStockModal = ({ line, onClose, onSave }) => {
  const [openingFull, setOpeningFull] = useState(line.opening_full_units || 0);
  const [openingPartial, setOpeningPartial] = useState(line.opening_partial_units || 0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSave = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/stock-tracker/stocktake-lines/${line.id}/update-opening/`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken()}`,
          },
          body: JSON.stringify({
            opening_full_units: parseFloat(openingFull),
            opening_partial_units: parseFloat(openingPartial),
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update opening stock');
      }

      const updatedLine = await response.json();
      console.log('✅ Opening stock updated:', updatedLine);
      
      onSave(updatedLine);
      onClose();
    } catch (err) {
      console.error('❌ Error updating opening stock:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Edit Opening Stock</h3>
        <p><strong>Item:</strong> {line.item_name} ({line.item_sku})</p>
        
        <div className="form-group">
          <label>Full Units (Cases/Kegs):</label>
          <input
            type="number"
            step="0.01"
            value={openingFull}
            onChange={(e) => setOpeningFull(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label>Partial Units (Bottles/Servings):</label>
          <input
            type="number"
            step="0.01"
            value={openingPartial}
            onChange={(e) => setOpeningPartial(e.target.value)}
            disabled={loading}
          />
        </div>

        <div className="calculated-preview">
          <p><strong>Calculated Opening Qty:</strong> 
            {(parseFloat(openingFull) * line.item_uom + parseFloat(openingPartial)).toFixed(2)} servings
          </p>
          <p><strong>Calculated Opening Value:</strong> 
            €{((parseFloat(openingFull) * line.item_uom + parseFloat(openingPartial)) * line.item_cost_per_serving).toFixed(2)}
          </p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="modal-actions">
          <button onClick={onClose} disabled={loading}>Cancel</button>
          <button onClick={handleSave} disabled={loading} className="primary">
            {loading ? 'Saving...' : 'Save Opening Stock'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EditOpeningStockModal;
```

---

### 2. Integration in Stocktake Counting Page

```jsx
import React, { useState } from 'react';
import EditOpeningStockModal from './EditOpeningStockModal';

const StocktakeLine = ({ line, user, onLineUpdate }) => {
  const [showEditModal, setShowEditModal] = useState(false);

  const handleOpeningSave = (updatedLine) => {
    // Update the line in parent state
    onLineUpdate(updatedLine);
    
    // Log for monitoring
    console.log('📊 Opening stock manually updated:', {
      sku: updatedLine.item_sku,
      old_opening: line.opening_qty,
      new_opening: updatedLine.opening_qty,
      difference: updatedLine.opening_qty - line.opening_qty,
    });
  };

  return (
    <tr>
      <td>{line.item_sku}</td>
      <td>{line.item_name}</td>
      <td>
        {line.opening_qty.toFixed(2)}
        {user.is_superuser && line.stocktake_status !== 'APPROVED' && (
          <button 
            onClick={() => setShowEditModal(true)}
            className="edit-icon-btn"
            title="Edit opening stock"
          >
            ✏️
          </button>
        )}
      </td>
      <td>{line.purchases.toFixed(2)}</td>
      <td>{line.expected_qty.toFixed(2)}</td>
      {/* ... rest of columns ... */}

      {showEditModal && (
        <EditOpeningStockModal
          line={line}
          onClose={() => setShowEditModal(false)}
          onSave={handleOpeningSave}
        />
      )}
    </tr>
  );
};
```

---

### 3. CSS Styling

```css
.edit-opening-btn {
  background-color: #2196F3;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-left: 8px;
}

.edit-opening-btn:hover {
  background-color: #1976D2;
}

.edit-icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  margin-left: 8px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.edit-icon-btn:hover {
  opacity: 1;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 24px;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.form-group {
  margin: 16px 0;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.calculated-preview {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  margin: 16px 0;
}

.calculated-preview p {
  margin: 4px 0;
  font-size: 14px;
}

.error-message {
  color: #d32f2f;
  background: #ffebee;
  padding: 8px;
  border-radius: 4px;
  margin: 12px 0;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.modal-actions button {
  padding: 8px 16px;
  border-radius: 4px;
  border: 1px solid #ddd;
  cursor: pointer;
  font-size: 14px;
}

.modal-actions button.primary {
  background: #4CAF50;
  color: white;
  border: none;
}

.modal-actions button.primary:hover {
  background: #45a049;
}

.modal-actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

### 4. Monitoring & Logging

**Console Logs to Include:**
```javascript
// Before API call
console.log('📝 Updating opening stock:', {
  line_id: line.id,
  sku: line.item_sku,
  old_full: line.opening_full_units,
  old_partial: line.opening_partial_units,
  new_full: openingFull,
  new_partial: openingPartial,
});

// After successful update
console.log('✅ Opening stock updated:', {
  line_id: updatedLine.id,
  sku: updatedLine.item_sku,
  new_opening_qty: updatedLine.opening_qty,
  new_opening_value: updatedLine.opening_value,
  new_expected: updatedLine.expected_qty,
});

// Error handling
console.error('❌ Failed to update opening stock:', {
  line_id: line.id,
  sku: line.item_sku,
  error: error.message,
});
```

---

### 5. User Flow

1. **User opens stocktake counting page**
2. **Sees opening stock column with values**
3. **If superuser & stocktake not approved, sees ✏️ icon next to opening values**
4. **Clicks edit icon**
5. **Modal opens showing:**
   - Current opening full units
   - Current opening partial units
   - Real-time calculation preview
6. **User enters correct values**
7. **Clicks "Save Opening Stock"**
8. **Backend updates opening_qty, recalculates expected_qty**
9. **Frontend refreshes line data**
10. **User sees updated opening and expected values**

---

### 6. Use Cases

**When to use:**
- ✅ First period setup (no previous period exists)
- ✅ Correcting historical data entry errors
- ✅ Migrating from another system
- ✅ Fixing discrepancies found in audits

**When NOT to use:**
- ❌ Stocktake already approved (immutable)
- ❌ Normal operations (should use previous period closing)
- ❌ Non-superuser accounts (lacks permission)

---

### 7. Validation Rules

**Backend will validate:**
- User must be superuser
- Stocktake must not be approved
- Values must be >= 0
- Values must be numeric

**Frontend should validate:**
- Values >= 0
- Numeric input only
- Show warning if drastically different from expected

---

## Testing Checklist

- [ ] Superuser can see edit button
- [ ] Non-superuser cannot see edit button
- [ ] Modal opens with current values pre-filled
- [ ] Calculation preview updates in real-time
- [ ] Save button disabled while loading
- [ ] Error messages display properly
- [ ] Success updates the line in parent state
- [ ] Cannot edit approved stocktake
- [ ] Console logs show before/after values
- [ ] Expected qty updates after opening changes

---

## Backend Implementation Required

I'll create the actual Django endpoint next. This guide shows the frontend team exactly what to build while I implement the backend API.
