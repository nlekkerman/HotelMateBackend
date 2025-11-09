# Frontend Implementation: Sales, Waste & Variance Input Fields

## Overview
This guide explains how sales, waste, and other movements are calculated and stored in the backend, and how to implement input fields in the frontend that affect the variance calculations.

---

## 1. How Sales, Waste, and Variances Are Calculated

### Backend Data Flow

#### A. StockMovement Model
All stock movements are tracked via the `StockMovement` model with these types:
- **PURCHASE**: Stock added via deliveries
- **SALE**: Stock consumed/sold
- **WASTE**: Stock lost to breakage, spoilage, etc.
- **TRANSFER_IN**: Stock received from another location
- **TRANSFER_OUT**: Stock sent to another location
- **ADJUSTMENT**: Corrections from stocktake variances

Each movement has:
```python
{
  "movement_type": "SALE",  # or WASTE, PURCHASE, etc.
  "quantity": 45.50,        # Servings (pints, shots, bottles)
  "item": 123,              # StockItem ID
  "period": 5,              # StockPeriod ID
  "timestamp": "2025-10-15T14:30:00Z"
}
```

#### B. StocktakeLine Aggregation
When a stocktake is created, it aggregates all movements for the period:

```python
# Backend calculates these automatically from StockMovement records:
purchases = Sum of PURCHASE movements in period
sales = Sum of SALE movements in period  
waste = Sum of WASTE movements in period
transfers_in = Sum of TRANSFER_IN movements in period
transfers_out = Sum of TRANSFER_OUT movements in period
adjustments = Sum of ADJUSTMENT movements in period
```

#### C. Expected Quantity Formula
```
expected_qty = opening_qty + purchases + transfers_in 
               - sales - waste - transfers_out + adjustments
```

#### D. Variance Calculation
```
variance_qty = counted_qty - expected_qty
variance_value = (counted_qty - expected_qty) × valuation_cost
```

**Positive variance** = Surplus (more stock than expected)  
**Negative variance** = Shortage (less stock than expected)

---

## 2. Current Stocktake Line Structure

### API Response Example
```typescript
interface StocktakeLine {
  id: number;
  item: {
    id: number;
    sku: string;
    name: string;
    category: { code: string; name: string; };
    uom: number;  // Servings per full unit
  };
  
  // Opening balance (frozen at period start)
  opening_qty: string;  // e.g., "125.5000"
  
  // Period movements (read-only, calculated from StockMovement)
  purchases: string;     // e.g., "50.0000"
  sales: string;         // e.g., "80.0000" ← From SALE movements
  waste: string;         // e.g., "5.0000"  ← From WASTE movements
  transfers_in: string;  // e.g., "0.0000"
  transfers_out: string; // e.g., "0.0000"
  adjustments: string;   // e.g., "0.0000"
  
  // Counted quantities (user input fields)
  counted_full_units: string;    // e.g., "8.00"
  counted_partial_units: string; // e.g., "15.00"
  
  // Calculated properties (read-only)
  counted_qty: string;     // e.g., "143.0000"
  expected_qty: string;    // e.g., "90.5000"
  variance_qty: string;    // e.g., "52.5000"
  expected_value: string;  // e.g., "226.25"
  counted_value: string;   // e.g., "357.50"
  variance_value: string;  // e.g., "131.25"
  
  // Manual overrides (optional, nullable)
  manual_purchases_value: string | null;  // e.g., "1250.00"
  manual_sales_profit: string | null;     // e.g., "3500.00"
  
  valuation_cost: string;  // e.g., "2.5000"
}
```

---

## 3. Why Sales/Waste Are Read-Only in StocktakeLine

### Important Concept
The `sales`, `waste`, `purchases`, etc. fields in `StocktakeLine` are **calculated aggregates** from the `StockMovement` table. They are **NOT editable** directly.

### To add/edit sales or waste:
You must create or edit `StockMovement` records, which will then be aggregated into the stocktake.

---

## 4. Frontend Implementation Options

### Option A: Display-Only (Current State)
Simply display the calculated values without editing:

```tsx
// StocktakeLineRow.tsx
interface Props {
  line: StocktakeLine;
}

export const StocktakeLineRow: React.FC<Props> = ({ line }) => {
  return (
    <tr>
      <td>{line.item.sku}</td>
      <td>{line.item.name}</td>
      
      {/* Read-only movement display */}
      <td className="text-right">{parseFloat(line.opening_qty).toFixed(2)}</td>
      <td className="text-right">{parseFloat(line.purchases).toFixed(2)}</td>
      <td className="text-right text-danger">
        -{parseFloat(line.sales).toFixed(2)}
      </td>
      <td className="text-right text-warning">
        -{parseFloat(line.waste).toFixed(2)}
      </td>
      
      {/* Editable counted fields */}
      <td>
        <input
          type="number"
          value={line.counted_full_units}
          onChange={(e) => handleUpdateCounted(line.id, 'counted_full_units', e.target.value)}
          step="1"
        />
      </td>
      <td>
        <input
          type="number"
          value={line.counted_partial_units}
          onChange={(e) => handleUpdateCounted(line.id, 'counted_partial_units', e.target.value)}
          step="0.01"
        />
      </td>
      
      {/* Calculated variance */}
      <td className={parseFloat(line.variance_qty) < 0 ? 'text-danger' : 'text-success'}>
        {parseFloat(line.variance_qty).toFixed(2)}
      </td>
      <td className={parseFloat(line.variance_value) < 0 ? 'text-danger' : 'text-success'}>
        €{parseFloat(line.variance_value).toFixed(2)}
      </td>
    </tr>
  );
};
```

### Option B: Link to Movement Management
Add buttons to create/edit movements that affect sales/waste:

```tsx
// StocktakeLineRow.tsx with movement links
export const StocktakeLineRow: React.FC<Props> = ({ line }) => {
  const [showMovementModal, setShowMovementModal] = useState(false);
  
  return (
    <>
      <tr>
        {/* ... other columns ... */}
        
        <td className="text-right">
          {parseFloat(line.sales).toFixed(2)}
          <button
            className="btn btn-sm btn-link"
            onClick={() => setShowMovementModal(true)}
            title="View/Edit Sales Movements"
          >
            <i className="fas fa-edit" />
          </button>
        </td>
        
        <td className="text-right">
          {parseFloat(line.waste).toFixed(2)}
          <button
            className="btn btn-sm btn-link"
            onClick={() => setShowMovementModal(true)}
            title="View/Edit Waste Movements"
          >
            <i className="fas fa-edit" />
          </button>
        </td>
        
        {/* ... rest of row ... */}
      </tr>
      
      {showMovementModal && (
        <MovementModal
          item={line.item}
          periodId={line.stocktake.period_id}
          onClose={() => setShowMovementModal(false)}
          onSave={() => {
            // Refresh stocktake data to get updated aggregates
            refreshStocktake();
            setShowMovementModal(false);
          }}
        />
      )}
    </>
  );
};
```

### Option C: Quick Add Movement Buttons
Provide quick-add functionality for common movements:

```tsx
// QuickMovementButtons.tsx
interface Props {
  itemId: number;
  periodId: number;
  onMovementAdded: () => void;
}

export const QuickMovementButtons: React.FC<Props> = ({ 
  itemId, 
  periodId, 
  onMovementAdded 
}) => {
  const [quantity, setQuantity] = useState<string>('');
  
  const addMovement = async (movementType: string) => {
    if (!quantity || parseFloat(quantity) <= 0) {
      alert('Please enter a valid quantity');
      return;
    }
    
    try {
      const response = await fetch(
        `/api/stock_tracker/${hotelId}/stock-movements/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            item: itemId,
            period: periodId,
            movement_type: movementType,
            quantity: quantity,
            notes: `Quick add from stocktake ${new Date().toISOString()}`
          })
        }
      );
      
      if (response.ok) {
        setQuantity('');
        onMovementAdded();
        alert(`${movementType} movement added successfully`);
      }
    } catch (error) {
      console.error('Error adding movement:', error);
      alert('Failed to add movement');
    }
  };
  
  return (
    <div className="quick-movement">
      <input
        type="number"
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        placeholder="Qty"
        step="0.01"
        className="form-control form-control-sm d-inline-block"
        style={{ width: '80px' }}
      />
      
      <button
        className="btn btn-sm btn-primary ms-1"
        onClick={() => addMovement('SALE')}
        title="Add Sale"
      >
        <i className="fas fa-shopping-cart" /> Sale
      </button>
      
      <button
        className="btn btn-sm btn-warning ms-1"
        onClick={() => addMovement('WASTE')}
        title="Add Waste"
      >
        <i className="fas fa-trash" /> Waste
      </button>
      
      <button
        className="btn btn-sm btn-success ms-1"
        onClick={() => addMovement('PURCHASE')}
        title="Add Purchase"
      >
        <i className="fas fa-plus" /> Purchase
      </button>
    </div>
  );
};
```

---

## 5. Implementing Movement Management Modal

### Full Movement Modal Component

```tsx
// MovementModal.tsx
interface Movement {
  id?: number;
  movement_type: string;
  quantity: string;
  unit_cost?: string;
  reference?: string;
  notes?: string;
  timestamp: string;
}

interface Props {
  item: StockItem;
  periodId: number;
  onClose: () => void;
  onSave: () => void;
}

export const MovementModal: React.FC<Props> = ({ 
  item, 
  periodId, 
  onClose, 
  onSave 
}) => {
  const [movements, setMovements] = useState<Movement[]>([]);
  const [loading, setLoading] = useState(true);
  const [newMovement, setNewMovement] = useState<Movement>({
    movement_type: 'SALE',
    quantity: '',
    reference: '',
    notes: '',
    timestamp: new Date().toISOString()
  });
  
  useEffect(() => {
    fetchMovements();
  }, []);
  
  const fetchMovements = async () => {
    try {
      const response = await fetch(
        `/api/stock_tracker/${hotelId}/stock-movements/?` +
        `item=${item.id}&period=${periodId}`,
        {
          headers: { 'Authorization': `Bearer ${authToken}` }
        }
      );
      const data = await response.json();
      setMovements(data.results || []);
    } catch (error) {
      console.error('Error fetching movements:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleAddMovement = async () => {
    if (!newMovement.quantity || parseFloat(newMovement.quantity) <= 0) {
      alert('Please enter a valid quantity');
      return;
    }
    
    try {
      const response = await fetch(
        `/api/stock_tracker/${hotelId}/stock-movements/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({
            ...newMovement,
            item: item.id,
            period: periodId
          })
        }
      );
      
      if (response.ok) {
        await fetchMovements();
        setNewMovement({
          movement_type: 'SALE',
          quantity: '',
          reference: '',
          notes: '',
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Error adding movement:', error);
      alert('Failed to add movement');
    }
  };
  
  const handleDeleteMovement = async (movementId: number) => {
    if (!confirm('Delete this movement?')) return;
    
    try {
      const response = await fetch(
        `/api/stock_tracker/${hotelId}/stock-movements/${movementId}/`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${authToken}` }
        }
      );
      
      if (response.ok) {
        await fetchMovements();
      }
    } catch (error) {
      console.error('Error deleting movement:', error);
    }
  };
  
  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              Movements for {item.sku} - {item.name}
            </h5>
            <button className="btn-close" onClick={onClose} />
          </div>
          
          <div className="modal-body">
            {/* Existing movements */}
            <h6>Existing Movements</h6>
            {loading ? (
              <p>Loading...</p>
            ) : movements.length === 0 ? (
              <p className="text-muted">No movements found for this period</p>
            ) : (
              <table className="table table-sm">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Quantity</th>
                    <th>Date</th>
                    <th>Reference</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {movements.map(movement => (
                    <tr key={movement.id}>
                      <td>
                        <span className={`badge bg-${getMovementColor(movement.movement_type)}`}>
                          {movement.movement_type}
                        </span>
                      </td>
                      <td>{parseFloat(movement.quantity).toFixed(2)}</td>
                      <td>{new Date(movement.timestamp).toLocaleString()}</td>
                      <td>{movement.reference}</td>
                      <td>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => handleDeleteMovement(movement.id!)}
                        >
                          <i className="fas fa-trash" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            
            <hr />
            
            {/* Add new movement */}
            <h6>Add New Movement</h6>
            <div className="row g-2">
              <div className="col-md-4">
                <label className="form-label">Type</label>
                <select
                  className="form-select"
                  value={newMovement.movement_type}
                  onChange={(e) => setNewMovement({
                    ...newMovement,
                    movement_type: e.target.value
                  })}
                >
                  <option value="SALE">Sale</option>
                  <option value="WASTE">Waste</option>
                  <option value="PURCHASE">Purchase</option>
                  <option value="TRANSFER_IN">Transfer In</option>
                  <option value="TRANSFER_OUT">Transfer Out</option>
                </select>
              </div>
              
              <div className="col-md-4">
                <label className="form-label">Quantity (servings)</label>
                <input
                  type="number"
                  className="form-control"
                  value={newMovement.quantity}
                  onChange={(e) => setNewMovement({
                    ...newMovement,
                    quantity: e.target.value
                  })}
                  step="0.01"
                  placeholder="0.00"
                />
              </div>
              
              <div className="col-md-4">
                <label className="form-label">Reference (optional)</label>
                <input
                  type="text"
                  className="form-control"
                  value={newMovement.reference}
                  onChange={(e) => setNewMovement({
                    ...newMovement,
                    reference: e.target.value
                  })}
                  placeholder="Invoice #, etc."
                />
              </div>
              
              <div className="col-12">
                <label className="form-label">Notes (optional)</label>
                <textarea
                  className="form-control"
                  value={newMovement.notes}
                  onChange={(e) => setNewMovement({
                    ...newMovement,
                    notes: e.target.value
                  })}
                  rows={2}
                />
              </div>
            </div>
          </div>
          
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleAddMovement}>
              Add Movement
            </button>
            <button className="btn btn-success" onClick={onSave}>
              Save & Refresh
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function for badge colors
function getMovementColor(type: string): string {
  switch (type) {
    case 'PURCHASE': return 'success';
    case 'SALE': return 'primary';
    case 'WASTE': return 'warning';
    case 'TRANSFER_IN': return 'info';
    case 'TRANSFER_OUT': return 'secondary';
    case 'ADJUSTMENT': return 'dark';
    default: return 'light';
  }
}
```

---

## 6. API Endpoints Reference

### StockMovement Endpoints

```typescript
// GET - List movements
GET /api/stock_tracker/{hotel_id}/stock-movements/
GET /api/stock_tracker/{hotel_id}/stock-movements/?item={item_id}
GET /api/stock_tracker/{hotel_id}/stock-movements/?period={period_id}
GET /api/stock_tracker/{hotel_id}/stock-movements/?item={item_id}&period={period_id}

// POST - Create movement
POST /api/stock_tracker/{hotel_id}/stock-movements/
Body: {
  "item": 123,
  "period": 5,
  "movement_type": "SALE",
  "quantity": "45.50",
  "unit_cost": "2.50",
  "reference": "Invoice-2025-001",
  "notes": "Evening service"
}

// DELETE - Remove movement
DELETE /api/stock_tracker/{hotel_id}/stock-movements/{movement_id}/

// PATCH - Update movement
PATCH /api/stock_tracker/{hotel_id}/stock-movements/{movement_id}/
Body: { "quantity": "50.00" }
```

### StocktakeLine Endpoints

```typescript
// PATCH - Update counted quantities or manual overrides
PATCH /api/stock_tracker/{hotel_id}/stocktake-lines/{line_id}/
Body: {
  "counted_full_units": "10.00",
  "counted_partial_units": "5.50",
  "manual_purchases_value": "1250.00",
  "manual_sales_profit": "3500.00"
}

// GET - Refresh stocktake to see updated aggregates
GET /api/stock_tracker/{hotel_id}/stocktakes/{stocktake_id}/
```

---

## 7. How Variances Are Affected

### Direct Impact Flow

```
1. User adds SALE movement (50 servings)
   ↓
2. StockMovement record created with movement_type="SALE", quantity=50
   ↓
3. Stocktake aggregates all SALE movements
   ↓
4. StocktakeLine.sales increases by 50
   ↓
5. expected_qty = opening + purchases - sales (now -50) - waste...
   ↓
6. Expected decreases by 50 servings
   ↓
7. variance_qty = counted_qty - expected_qty
   ↓
8. Variance becomes MORE POSITIVE (surplus) or LESS NEGATIVE
```

### Example Scenario

```
Initial State:
- Opening: 100 servings
- Purchases: 0
- Sales: 0
- Waste: 0
- Expected: 100 servings
- Counted: 80 servings
- Variance: -20 servings (shortage)

User adds SALE movement of 25 servings:
- Opening: 100 servings
- Purchases: 0
- Sales: 25 servings (NEW!)
- Waste: 0
- Expected: 75 servings (reduced by 25)
- Counted: 80 servings (unchanged)
- Variance: +5 servings (NOW A SURPLUS!)
```

---

## 8. Important Notes

1. **Movements affect expected, not counted**: Adding sales/waste movements reduces the expected quantity. The counted quantity is only changed by editing `counted_full_units` / `counted_partial_units`.

2. **Aggregation timing**: After adding/editing movements, you must refresh the stocktake data to see updated aggregates.

3. **Period locking**: Movements can only be added to the current period or draft stocktakes. Approved stocktakes are locked.

4. **Manual overrides**: The `manual_purchases_value` and `manual_sales_profit` fields are for financial reporting only and don't affect quantity calculations.

5. **Automatic updates**: When movements are created, the item's `current_partial_units` is automatically updated in real-time.

---

## 9. Recommended Implementation

**Best approach**: Combine Options B and C
- Show read-only sales/waste in main table
- Add edit icon that opens movement modal
- Include quick-add buttons for common operations
- Refresh stocktake after movements are added

This provides:
- ✅ Full audit trail of all movements
- ✅ Easy correction of errors
- ✅ Quick workflow for common tasks
- ✅ Clear visibility of what affects variance
- ✅ Prevents accidental data corruption

---

## 10. Testing Checklist

- [ ] Display sales/waste totals correctly in stocktake table
- [ ] Open movement modal and see existing movements
- [ ] Add new SALE movement and verify expected_qty decreases
- [ ] Add new WASTE movement and verify expected_qty decreases
- [ ] Add new PURCHASE movement and verify expected_qty increases
- [ ] Delete a movement and verify values recalculate
- [ ] Refresh stocktake after adding movements
- [ ] Verify variance changes appropriately
- [ ] Test with different movement types
- [ ] Verify only current period movements can be added
- [ ] Test error handling for invalid quantities
