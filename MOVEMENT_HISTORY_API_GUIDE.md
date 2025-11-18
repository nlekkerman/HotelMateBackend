# Movement History API - Complete Guide

## Overview

Every purchase and waste entry creates a permanent `StockMovement` record. Users can view, edit, and delete individual movements to correct mistakes.

---

## 📋 1. Get Movement History

**Endpoint:** `GET /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/movements/`

### Request Example

```javascript
const getMovementHistory = async (lineId) => {
  try {
    const response = await api.get(
      `/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/movements/`
    );
    return response.data;
  } catch (error) {
    console.error('Failed to load movement history:', error);
    throw error;
  }
};
```

### Response Example

```json
{
  "movements": [
    {
      "id": 4591,
      "movement_type": "PURCHASE",
      "quantity": "555.0000",
      "unit_cost": "2.50",
      "reference": "INV-12345",
      "notes": "Delivery from supplier",
      "timestamp": "2025-02-15T14:30:00Z",
      "staff": {
        "id": 5,
        "user": {
          "username": "john.doe",
          "first_name": "John",
          "last_name": "Doe"
        }
      }
    },
    {
      "id": 4590,
      "movement_type": "WASTE",
      "quantity": "12.0000",
      "unit_cost": null,
      "reference": "Stocktake-37",
      "notes": "Broken bottles",
      "timestamp": "2025-02-20T10:15:00Z",
      "staff": {
        "id": 5,
        "user": {
          "username": "john.doe"
        }
      }
    }
  ],
  "summary": {
    "total_purchases": "555.0000",
    "total_waste": "12.0000",
    "movement_count": 2
  }
}
```

### Frontend Display Component

```jsx
import React, { useState, useEffect } from 'react';
import api from '../services/api';

const MovementHistory = ({ lineId, hotelSlug }) => {
  const [movements, setMovements] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMovements();
  }, [lineId]);

  const loadMovements = async () => {
    try {
      setLoading(true);
      const response = await api.get(
        `/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/movements/`
      );
      setMovements(response.data.movements);
      setSummary(response.data.summary);
    } catch (error) {
      console.error('Failed to load movements:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading history...</div>;

  return (
    <div className="movement-history">
      <h3>Purchase & Waste History</h3>
      
      {/* Summary */}
      {summary && (
        <div className="summary">
          <div>Total Purchases: {summary.total_purchases}</div>
          <div>Total Waste: {summary.total_waste}</div>
          <div>Total Entries: {summary.movement_count}</div>
        </div>
      )}

      {/* Movement List */}
      <div className="movements-list">
        {movements.length === 0 ? (
          <p>No movements yet</p>
        ) : (
          movements.map(movement => (
            <MovementCard
              key={movement.id}
              movement={movement}
              onDelete={() => handleDelete(movement.id)}
              onEdit={() => handleEdit(movement)}
            />
          ))
        )}
      </div>
    </div>
  );
};

const MovementCard = ({ movement, onDelete, onEdit }) => {
  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const typeIcon = movement.movement_type === 'PURCHASE' ? '📦' : '🗑️';
  const typeColor = movement.movement_type === 'PURCHASE' 
    ? 'text-green-600' 
    : 'text-red-600';

  return (
    <div className="movement-card border rounded-lg p-4 mb-2">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{typeIcon}</span>
            <span className={`font-semibold ${typeColor}`}>
              {movement.movement_type}
            </span>
            <span className="text-lg font-bold">
              {movement.quantity}
            </span>
          </div>
          
          <div className="text-sm text-gray-600 mt-2">
            <div>📅 {formatDate(movement.timestamp)}</div>
            {movement.reference && (
              <div>📄 Ref: {movement.reference}</div>
            )}
            {movement.notes && (
              <div>💬 {movement.notes}</div>
            )}
            {movement.staff && (
              <div>👤 By: {movement.staff.user.first_name} {movement.staff.user.last_name}</div>
            )}
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={onEdit}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};
```

---

## ✏️ 2. Edit/Update a Movement

**Endpoint:** `PATCH /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/update-movement/{movement_id}/`

### Request Example

```javascript
const updateMovement = async (lineId, movementId, updates) => {
  try {
    const response = await api.patch(
      `/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/update-movement/${movementId}/`,
      updates
    );
    return response.data;
  } catch (error) {
    console.error('Failed to update movement:', error);
    throw error;
  }
};

// Example usage
const handleEditMovement = async (lineId, movementId) => {
  const updates = {
    movement_type: "PURCHASE",  // or "WASTE"
    quantity: 75.0,             // New quantity
    unit_cost: 2.50,            // Optional
    reference: "INV-99999",     // Optional
    notes: "Corrected quantity" // Optional
  };

  const result = await updateMovement(lineId, movementId, updates);
  
  // Backend returns updated line data
  console.log('Updated line:', result.line);
  console.log('Old values:', result.old_values);
  
  // Update your state with result.line
  updateLineInState(lineId, result.line);
};
```

### Request Body (all fields optional)

```json
{
  "movement_type": "PURCHASE",
  "quantity": 75.0,
  "unit_cost": 2.50,
  "reference": "INV-99999",
  "notes": "Corrected quantity"
}
```

### Response Example

```json
{
  "message": "Movement updated successfully",
  "movement": {
    "id": 4591,
    "movement_type": "PURCHASE",
    "quantity": "75.0000",
    "unit_cost": "2.50",
    "reference": "INV-99999",
    "notes": "Corrected quantity",
    "timestamp": "2025-02-15T14:30:00Z"
  },
  "old_values": {
    "movement_type": "PURCHASE",
    "quantity": "555.0000",
    "unit_cost": "2.50",
    "reference": "INV-12345",
    "notes": "Delivery from supplier"
  },
  "line": {
    "id": 8853,
    "item_sku": "B0070",
    "opening_qty": "22.0000",
    "purchases": "75.0000",      // Recalculated from all movements
    "waste": "12.0000",
    "expected_qty": "85.0000",   // Recalculated
    "counted_qty": "80.0000",
    "variance_qty": "-5.0000",   // Recalculated
    "variance_value": "-12.50"
  }
}
```

### Edit Modal Component

```jsx
const EditMovementModal = ({ movement, lineId, hotelSlug, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    movement_type: movement.movement_type,
    quantity: movement.quantity,
    unit_cost: movement.unit_cost || '',
    reference: movement.reference || '',
    notes: movement.notes || ''
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const response = await api.patch(
        `/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/update-movement/${movement.id}/`,
        formData
      );

      // Update parent component with new line data
      onSuccess(response.data.line);
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update movement');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>Edit Movement</h2>
        
        {error && (
          <div className="error-message">{error}</div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Type */}
          <div className="form-group">
            <label>Type</label>
            <select
              value={formData.movement_type}
              onChange={(e) => setFormData({...formData, movement_type: e.target.value})}
              required
            >
              <option value="PURCHASE">Purchase</option>
              <option value="WASTE">Waste</option>
            </select>
          </div>

          {/* Quantity */}
          <div className="form-group">
            <label>Quantity *</label>
            <input
              type="number"
              step="0.01"
              value={formData.quantity}
              onChange={(e) => setFormData({...formData, quantity: e.target.value})}
              required
            />
          </div>

          {/* Unit Cost */}
          <div className="form-group">
            <label>Unit Cost (optional)</label>
            <input
              type="number"
              step="0.01"
              value={formData.unit_cost}
              onChange={(e) => setFormData({...formData, unit_cost: e.target.value})}
            />
          </div>

          {/* Reference */}
          <div className="form-group">
            <label>Reference (e.g., Invoice #)</label>
            <input
              type="text"
              value={formData.reference}
              onChange={(e) => setFormData({...formData, reference: e.target.value})}
              placeholder="INV-12345"
            />
          </div>

          {/* Notes */}
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              rows={3}
              placeholder="Add any notes..."
            />
          </div>

          {/* Buttons */}
          <div className="button-group">
            <button type="button" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button type="submit" disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

---

## 🗑️ 3. Delete a Movement

**Endpoint:** `DELETE /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/delete-movement/{movement_id}/`

### Request Example

```javascript
const deleteMovement = async (lineId, movementId) => {
  try {
    const response = await api.delete(
      `/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/delete-movement/${movementId}/`
    );
    return response.data;
  } catch (error) {
    console.error('Failed to delete movement:', error);
    throw error;
  }
};

// Example usage with confirmation
const handleDeleteMovement = async (lineId, movementId) => {
  const confirmed = window.confirm(
    'Are you sure you want to delete this movement? This will recalculate purchases/waste.'
  );
  
  if (!confirmed) return;

  try {
    const result = await deleteMovement(lineId, movementId);
    
    // Backend returns updated line data
    console.log('Deleted:', result.deleted_movement);
    console.log('Updated line:', result.line);
    
    // Update your state with result.line
    updateLineInState(lineId, result.line);
    
    // Refresh movement history
    await loadMovements();
    
    alert('Movement deleted successfully');
  } catch (error) {
    alert('Failed to delete movement');
  }
};
```

### Response Example

```json
{
  "message": "Movement deleted successfully",
  "deleted_movement": {
    "id": 4591,
    "movement_type": "PURCHASE",
    "quantity": "555.0000"
  },
  "line": {
    "id": 8853,
    "item_sku": "B0070",
    "opening_qty": "22.0000",
    "purchases": "0.0000",        // Recalculated (no more purchases)
    "waste": "12.0000",
    "expected_qty": "10.0000",    // Recalculated
    "counted_qty": "10.0000",
    "variance_qty": "0.0000",     // Recalculated
    "variance_value": "0.00"
  }
}
```

### Delete with Confirmation Component

```jsx
const DeleteMovementButton = ({ movement, lineId, hotelSlug, onSuccess }) => {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    const message = `Delete this ${movement.movement_type.toLowerCase()}?\n\n` +
      `Quantity: ${movement.quantity}\n` +
      `Reference: ${movement.reference || 'N/A'}\n\n` +
      `This will recalculate the line totals.`;

    const confirmed = window.confirm(message);
    if (!confirmed) return;

    setDeleting(true);

    try {
      const response = await api.delete(
        `/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/delete-movement/${movement.id}/`
      );

      // Notify parent to update line data
      onSuccess(response.data.line);
      
      // Show success message
      toast.success('Movement deleted successfully');
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Failed to delete movement';
      toast.error(errorMsg);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <button
      onClick={handleDelete}
      disabled={deleting}
      className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
    >
      {deleting ? 'Deleting...' : 'Delete'}
    </button>
  );
};
```

---

## 🔄 4. Complete Integration Example

```jsx
const StocktakeLineWithHistory = ({ line, hotelSlug }) => {
  const [movements, setMovements] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [editingMovement, setEditingMovement] = useState(null);
  const [lineData, setLineData] = useState(line);

  // Load movement history
  const loadMovements = async () => {
    try {
      const response = await api.get(
        `/stock_tracker/${hotelSlug}/stocktake-lines/${line.id}/movements/`
      );
      setMovements(response.data.movements);
    } catch (error) {
      console.error('Failed to load movements:', error);
    }
  };

  // Handle line updates from backend
  const handleLineUpdated = (updatedLine) => {
    setLineData(updatedLine);
    loadMovements(); // Refresh history
  };

  // Handle edit
  const handleEdit = (movement) => {
    setEditingMovement(movement);
  };

  // Handle delete
  const handleDelete = async (movementId) => {
    const confirmed = window.confirm('Delete this movement?');
    if (!confirmed) return;

    try {
      const response = await api.delete(
        `/stock_tracker/${hotelSlug}/stocktake-lines/${line.id}/delete-movement/${movementId}/`
      );
      
      handleLineUpdated(response.data.line);
      toast.success('Movement deleted');
    } catch (error) {
      toast.error('Failed to delete movement');
    }
  };

  return (
    <div className="stocktake-line">
      {/* Line display with current totals */}
      <div className="line-header">
        <h3>{lineData.item_name}</h3>
        <div className="totals">
          <div>Purchases: {lineData.purchases}</div>
          <div>Waste: {lineData.waste}</div>
          <div>Expected: {lineData.expected_qty}</div>
        </div>
      </div>

      {/* Toggle history button */}
      <button onClick={() => {
        setShowHistory(!showHistory);
        if (!showHistory) loadMovements();
      }}>
        {showHistory ? 'Hide' : 'Show'} Movement History
      </button>

      {/* Movement history */}
      {showHistory && (
        <div className="movement-history">
          {movements.map(movement => (
            <MovementCard
              key={movement.id}
              movement={movement}
              onEdit={() => handleEdit(movement)}
              onDelete={() => handleDelete(movement.id)}
            />
          ))}
        </div>
      )}

      {/* Edit modal */}
      {editingMovement && (
        <EditMovementModal
          movement={editingMovement}
          lineId={line.id}
          hotelSlug={hotelSlug}
          onClose={() => setEditingMovement(null)}
          onSuccess={handleLineUpdated}
        />
      )}
    </div>
  );
};
```

---

## 📝 Summary

### Get History
- **Endpoint:** `GET /stocktake-lines/{line_id}/movements/`
- **Returns:** List of movements + summary totals
- **Use when:** User clicks "View History" button

### Edit Movement
- **Endpoint:** `PATCH /stocktake-lines/{line_id}/update-movement/{movement_id}/`
- **Body:** Any fields to update (quantity, type, notes, etc.)
- **Returns:** Updated movement + updated line data
- **Use when:** User corrects a mistake

### Delete Movement
- **Endpoint:** `DELETE /stocktake-lines/{line_id}/delete-movement/{movement_id}/`
- **Returns:** Deleted movement info + updated line data
- **Use when:** User removes incorrect entry

### Key Principles
1. ✅ **Always use backend response** - Line data is automatically recalculated
2. ✅ **Update UI with response.data.line** - Don't calculate locally
3. ✅ **Refresh movement list** after edit/delete
4. ✅ **Show confirmation** before deleting
5. ✅ **Display audit info** (who, when, reference)

---

## 🚫 Error Handling

```javascript
// Cannot edit/delete on locked stocktakes
try {
  await api.patch(url, data);
} catch (error) {
  if (error.response?.status === 400) {
    const msg = error.response.data.error;
    if (msg.includes('approved')) {
      alert('Cannot edit movements on approved stocktakes');
    }
  }
}
```

Common errors:
- `"Cannot add movements to approved stocktake"` - Stocktake is locked
- `"Movement {id} not found for this line"` - Wrong movement ID
- `"movement_type must be 'PURCHASE' or 'WASTE'"` - Invalid type
- `"Quantity must be greater than 0"` - Invalid quantity
