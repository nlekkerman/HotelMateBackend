// Complete React Component Example for Stocktake Line with Movement Entry

import React, { useState, useEffect } from 'react';

/**
 * Complete example showing:
 * 1. Display stocktake line data
 * 2. Input fields for adding movements
 * 3. Display all movements for the line
 * 4. Auto-refresh after adding movements
 */

const StocktakeLineWithMovements = ({ hotelSlug, lineId, initialLineData }) => {
  const [lineData, setLineData] = useState(initialLineData);
  const [movements, setMovements] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showMovements, setShowMovements] = useState(false);

  // Form state for adding new movement
  const [movementForm, setMovementForm] = useState({
    movement_type: 'PURCHASE',
    quantity: '',
    reference: '',
    notes: ''
  });

  // Fetch movements when component mounts or showMovements changes
  useEffect(() => {
    if (showMovements) {
      fetchMovements();
    }
  }, [showMovements, lineId]);

  const fetchMovements = async () => {
    try {
      const response = await fetch(
        `/api/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/movements/`
      );
      const data = await response.json();
      setMovements(data.movements);
      setSummary(data.summary);
    } catch (err) {
      console.error('Failed to fetch movements:', err);
    }
  };

  const addMovement = async (e) => {
    e.preventDefault();
    
    if (!movementForm.quantity) {
      alert('Please enter a quantity');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/add-movement/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            movement_type: movementForm.movement_type,
            quantity: parseFloat(movementForm.quantity),
            reference: movementForm.reference || undefined,
            notes: movementForm.notes || undefined
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to add movement');
      }

      const data = await response.json();
      
      // Update line data with new values
      setLineData(data.line);
      
      // Refresh movements list if visible
      if (showMovements) {
        await fetchMovements();
      }
      
      // Reset form
      setMovementForm({
        movement_type: 'PURCHASE',
        quantity: '',
        reference: '',
        notes: ''
      });
      
      alert(`${movementForm.movement_type} added successfully!`);
    } catch (err) {
      setError(err.message);
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const quickAddMovement = async (type, qty) => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/add-movement/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            movement_type: type,
            quantity: parseFloat(qty)
          })
        }
      );

      if (response.ok) {
        const data = await response.json();
        setLineData(data.line);
        if (showMovements) await fetchMovements();
        alert(`${type} added!`);
      }
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="stocktake-line-container">
      {/* Line Summary */}
      <div className="line-header">
        <h3>
          {lineData.item_sku} - {lineData.item_name}
        </h3>
        <span className="category-badge">{lineData.category_code}</span>
      </div>

      {/* Stock Levels */}
      <div className="stock-levels">
        <div className="level-box">
          <label>Opening</label>
          <div className="value">{lineData.opening_qty}</div>
        </div>
        <div className="level-box">
          <label>Expected</label>
          <div className="value">{lineData.expected_qty}</div>
        </div>
        <div className="level-box">
          <label>Counted</label>
          <div className="value">{lineData.counted_qty}</div>
        </div>
        <div className="level-box variance">
          <label>Variance</label>
          <div className={`value ${parseFloat(lineData.variance_qty) < 0 ? 'negative' : 'positive'}`}>
            {lineData.variance_qty}
          </div>
        </div>
      </div>

      {/* Movement Summary */}
      <div className="movement-summary">
        <div className="summary-row">
          <span>Purchases: {lineData.purchases}</span>
          <span>Sales: {lineData.sales}</span>
          <span>Waste: {lineData.waste}</span>
        </div>
        <div className="summary-row">
          <span>Transfer In: {lineData.transfers_in}</span>
          <span>Transfer Out: {lineData.transfers_out}</span>
          <span>Adjustments: {lineData.adjustments}</span>
        </div>
      </div>

      {/* Quick Add Buttons */}
      <div className="quick-add-section">
        <h4>Quick Add Movement</h4>
        <div className="quick-buttons">
          <button
            onClick={() => {
              const qty = prompt('Enter purchase quantity:');
              if (qty) quickAddMovement('PURCHASE', qty);
            }}
            disabled={loading}
          >
            + Purchase
          </button>
          <button
            onClick={() => {
              const qty = prompt('Enter sale quantity:');
              if (qty) quickAddMovement('SALE', qty);
            }}
            disabled={loading}
          >
            - Sale
          </button>
          <button
            onClick={() => {
              const qty = prompt('Enter waste quantity:');
              if (qty) quickAddMovement('WASTE', qty);
            }}
            disabled={loading}
          >
            ⚠ Waste
          </button>
        </div>
      </div>

      {/* Full Movement Form */}
      <div className="add-movement-form">
        <h4>Add Movement</h4>
        <form onSubmit={addMovement}>
          <div className="form-row">
            <select
              value={movementForm.movement_type}
              onChange={(e) => setMovementForm({ ...movementForm, movement_type: e.target.value })}
              disabled={loading}
            >
              <option value="PURCHASE">Purchase</option>
              <option value="SALE">Sale</option>
              <option value="WASTE">Waste</option>
              <option value="TRANSFER_IN">Transfer In</option>
              <option value="TRANSFER_OUT">Transfer Out</option>
              <option value="ADJUSTMENT">Adjustment</option>
            </select>

            <input
              type="number"
              step="0.01"
              placeholder="Quantity"
              value={movementForm.quantity}
              onChange={(e) => setMovementForm({ ...movementForm, quantity: e.target.value })}
              required
              disabled={loading}
            />

            <input
              type="text"
              placeholder="Reference (optional)"
              value={movementForm.reference}
              onChange={(e) => setMovementForm({ ...movementForm, reference: e.target.value })}
              disabled={loading}
            />

            <button type="submit" disabled={loading}>
              {loading ? 'Adding...' : 'Add Movement'}
            </button>
          </div>

          <div className="form-row">
            <input
              type="text"
              placeholder="Notes (optional)"
              value={movementForm.notes}
              onChange={(e) => setMovementForm({ ...movementForm, notes: e.target.value })}
              disabled={loading}
              style={{ width: '100%' }}
            />
          </div>
        </form>
        
        {error && <div className="error-message">{error}</div>}
      </div>

      {/* View Movements Toggle */}
      <button
        className="toggle-movements-btn"
        onClick={() => setShowMovements(!showMovements)}
      >
        {showMovements ? '▼' : '▶'} View All Movements ({summary.movement_count || '...'})
      </button>

      {/* Movements List */}
      {showMovements && (
        <div className="movements-list">
          {movements.length === 0 ? (
            <p>No movements found for this period</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Date/Time</th>
                  <th>Type</th>
                  <th>Quantity</th>
                  <th>Reference</th>
                  <th>Staff</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {movements.map((movement) => (
                  <tr key={movement.id}>
                    <td>{new Date(movement.timestamp).toLocaleString()}</td>
                    <td>
                      <span className={`movement-type ${movement.movement_type.toLowerCase()}`}>
                        {movement.movement_type}
                      </span>
                    </td>
                    <td>{movement.quantity}</td>
                    <td>{movement.reference || '-'}</td>
                    <td>{movement.staff_name || 'System'}</td>
                    <td>{movement.notes || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};

// Example CSS (put in separate file or styled-components)
const styles = `
.stocktake-line-container {
  border: 1px solid #ddd;
  padding: 20px;
  margin: 10px 0;
  border-radius: 8px;
  background: white;
}

.line-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.category-badge {
  background: #007bff;
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
}

.stock-levels {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.level-box {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: center;
  border-radius: 4px;
}

.level-box label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.level-box .value {
  font-size: 20px;
  font-weight: bold;
}

.level-box.variance .value.negative {
  color: #dc3545;
}

.level-box.variance .value.positive {
  color: #28a745;
}

.movement-summary {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin: 5px 0;
}

.quick-add-section {
  margin-bottom: 20px;
}

.quick-buttons {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.quick-buttons button {
  flex: 1;
  padding: 10px;
  cursor: pointer;
}

.add-movement-form {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.form-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.form-row input,
.form-row select,
.form-row button {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-row button {
  background: #007bff;
  color: white;
  cursor: pointer;
  border: none;
}

.form-row button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.error-message {
  color: #dc3545;
  margin-top: 10px;
}

.toggle-movements-btn {
  width: 100%;
  padding: 10px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 10px;
}

.movements-list table {
  width: 100%;
  border-collapse: collapse;
}

.movements-list th,
.movements-list td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.movements-list th {
  background: #f8f9fa;
  font-weight: bold;
}

.movement-type {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
  text-transform: uppercase;
}

.movement-type.purchase {
  background: #d4edda;
  color: #155724;
}

.movement-type.sale {
  background: #cce5ff;
  color: #004085;
}

.movement-type.waste {
  background: #f8d7da;
  color: #721c24;
}

.movement-type.transfer_in {
  background: #d1ecf1;
  color: #0c5460;
}

.movement-type.transfer_out {
  background: #fff3cd;
  color: #856404;
}

.movement-type.adjustment {
  background: #e2e3e5;
  color: #383d41;
}
`;

export default StocktakeLineWithMovements;

// Usage example:
/*
<StocktakeLineWithMovements
  hotelSlug="hotel-slug"
  lineId={45}
  initialLineData={lineData}
/>
*/
