# Manual Movement Entry for Stocktake Lines

## Overview

You can now create **Purchases, Sales, Transfers, Waste, and Adjustments** directly from stocktake line items through the API. These movements are stored as real `StockMovement` records and are immediately reflected in the line's calculations.

## How It Works

### Two Ways Movements Are Tracked

1. **Automatic Calculation** (existing): Movements created through the `/movements/` endpoint are automatically summed up for each stocktake line during populate
2. **Manual Entry from Lines** (new): Create movements directly from a stocktake line item, which are also stored as `StockMovement` records

Both approaches use the **same underlying data** - they create real `StockMovement` records that affect calculations.

## API Endpoints

### 1. Add Movement to Line Item

**Endpoint:** `POST /api/stock_tracker/{hotel_identifier}/stocktake-lines/{line_id}/add-movement/`

**Purpose:** Create a new stock movement directly from a stocktake line.

**Request Body:**
```json
{
  "movement_type": "PURCHASE",
  "quantity": 24.0,
  "unit_cost": 2.50,
  "reference": "INV-12345",
  "notes": "Manual entry for delivery"
}
```

**Movement Types:**
- `PURCHASE` - Purchase/Delivery
- `SALE` - Sale/Consumption  
- `WASTE` - Waste/Breakage
- `TRANSFER_IN` - Transfer In
- `TRANSFER_OUT` - Transfer Out
- `ADJUSTMENT` - Stocktake Adjustment

**Required Fields:**
- `movement_type` (string)
- `quantity` (decimal)

**Optional Fields:**
- `unit_cost` (decimal) - Cost per serving
- `reference` (string) - Invoice number, order ID, etc.
- `notes` (string) - Additional information

**Response:**
```json
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
    "purchases": "72.0000",  // Updated with new movement
    "sales": "120.0000",
    "expected_qty": "40.0000",
    "counted_qty": "42.0000",
    "variance_qty": "2.0000",
    // ... all other fields
  }
}
```

### 2. View All Movements for a Line

**Endpoint:** `GET /api/stock_tracker/{hotel_identifier}/stocktake-lines/{line_id}/movements/`

**Purpose:** Get all movements affecting this line item within the stocktake period.

**Response:**
```json
{
  "summary": {
    "total_purchases": "72.0000",
    "total_sales": "120.0000",
    "total_waste": "3.0000",
    "total_transfers_in": "0.0000",
    "total_transfers_out": "12.0000",
    "total_adjustments": "0.0000",
    "movement_count": 15
  },
  "movements": [
    {
      "id": 156,
      "item_sku": "D001",
      "item_name": "Guinness Keg",
      "movement_type": "PURCHASE",
      "quantity": "24.0000",
      "unit_cost": "2.5000",
      "reference": "INV-12345",
      "notes": "Manual entry for delivery",
      "staff_name": "John Smith",
      "timestamp": "2025-11-09T14:30:00Z"
    },
    {
      "id": 155,
      "item_sku": "D001",
      "item_name": "Guinness Keg",
      "movement_type": "SALE",
      "quantity": "45.0000",
      "unit_cost": null,
      "reference": "POS-Daily",
      "notes": "Automated from POS",
      "staff_name": null,
      "timestamp": "2025-11-08T23:59:00Z"
    }
    // ... more movements
  ]
}
```

## Frontend Implementation Examples

### Example 1: Add Purchase Input Field

```javascript
// In your stocktake line component
const [purchaseQty, setPurchaseQty] = useState('');
const [reference, setReference] = useState('');

const handleAddPurchase = async () => {
  try {
    const response = await fetch(
      `/api/stock_tracker/hotel-slug/stocktake-lines/${lineId}/add-movement/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movement_type: 'PURCHASE',
          quantity: parseFloat(purchaseQty),
          reference: reference,
          notes: 'Manual entry from stocktake UI'
        })
      }
    );
    
    const data = await response.json();
    
    // Update the line data in your state
    updateLineData(data.line);
    
    // Show success message
    alert('Purchase added successfully!');
    
    // Reset form
    setPurchaseQty('');
    setReference('');
  } catch (error) {
    console.error('Error adding purchase:', error);
  }
};
```

### Example 2: Display Movements Table

```javascript
const [movements, setMovements] = useState([]);
const [summary, setSummary] = useState({});

useEffect(() => {
  fetchMovements();
}, [lineId]);

const fetchMovements = async () => {
  const response = await fetch(
    `/api/stock_tracker/hotel-slug/stocktake-lines/${lineId}/movements/`
  );
  const data = await response.json();
  setMovements(data.movements);
  setSummary(data.summary);
};

return (
  <div>
    <h3>Movement Summary</h3>
    <ul>
      <li>Purchases: {summary.total_purchases}</li>
      <li>Sales: {summary.total_sales}</li>
      <li>Waste: {summary.total_waste}</li>
      <li>Transfer In: {summary.total_transfers_in}</li>
      <li>Transfer Out: {summary.total_transfers_out}</li>
      <li>Adjustments: {summary.total_adjustments}</li>
    </ul>
    
    <h3>Individual Movements ({summary.movement_count})</h3>
    <table>
      <thead>
        <tr>
          <th>Date/Time</th>
          <th>Type</th>
          <th>Quantity</th>
          <th>Reference</th>
          <th>Staff</th>
        </tr>
      </thead>
      <tbody>
        {movements.map(movement => (
          <tr key={movement.id}>
            <td>{new Date(movement.timestamp).toLocaleString()}</td>
            <td>{movement.movement_type}</td>
            <td>{movement.quantity}</td>
            <td>{movement.reference}</td>
            <td>{movement.staff_name || 'System'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
```

### Example 3: Quick Movement Input Form

```javascript
const MovementInputForm = ({ lineId, onSuccess }) => {
  const [formData, setFormData] = useState({
    movement_type: 'PURCHASE',
    quantity: '',
    reference: '',
    notes: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch(
        `/api/stock_tracker/hotel-slug/stocktake-lines/${lineId}/add-movement/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...formData,
            quantity: parseFloat(formData.quantity)
          })
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        onSuccess(data.line); // Update parent component
        setFormData({ movement_type: 'PURCHASE', quantity: '', reference: '', notes: '' });
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <select 
        value={formData.movement_type}
        onChange={(e) => setFormData({...formData, movement_type: e.target.value})}
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
        value={formData.quantity}
        onChange={(e) => setFormData({...formData, quantity: e.target.value})}
        required
      />
      
      <input
        type="text"
        placeholder="Reference (optional)"
        value={formData.reference}
        onChange={(e) => setFormData({...formData, reference: e.target.value})}
      />
      
      <button type="submit">Add Movement</button>
    </form>
  );
};
```

## UI Design Recommendations

### Option 1: Inline Input Fields
Add input fields directly in each line item row:
```
Item: Guinness Keg (D001)
Opening: 88  |  Expected: 40  |  Counted: 42  |  Variance: +2

Quick Add:
[Purchase: ____] [Ref: ____] [Add]
[Sale: ____] [Ref: ____] [Add]
[Waste: ____] [Ref: ____] [Add]

View Movements (15) ▼
```

### Option 2: Modal/Drawer
Click "Add Movement" button to open a modal with full form:
```
Add Movement to Guinness Keg (D001)

Type: [Dropdown: Purchase/Sale/Waste/Transfer In/Transfer Out/Adjustment]
Quantity: [_____]
Unit Cost: [_____] (optional)
Reference: [_____] (optional)
Notes: [___________] (optional)

[Cancel] [Add Movement]
```

### Option 3: Expandable Section
Each line has an expandable section showing all movements:
```
▶ Guinness Keg (D001) - Opening: 88, Expected: 40, Counted: 42

[Expand]

▼ Guinness Keg (D001)
  
  Movements (15 total):
  Purchases: 72 | Sales: 120 | Waste: 3
  
  [Add Purchase] [Add Sale] [Add Waste] [Add Transfer] [Add Adjustment]
  
  Date          Type      Qty    Reference    Staff
  Nov 9, 2PM    PURCHASE  24     INV-12345    John Smith
  Nov 8, 11PM   SALE      45     POS-Daily    System
  ...
```

## Important Notes

### Security
- Only works on **unlocked stocktakes** (not yet approved)
- Automatically records which staff member created the movement
- All movements are timestamped

### Data Integrity
- Movements are **real StockMovement records** in the database
- They affect all calculations (expected_qty, variance, etc.)
- They're included in the stocktake period totals
- Cannot be edited or deleted once approved

### Calculation Flow
1. User adds movement via line item endpoint
2. StockMovement record is created
3. Line totals are recalculated from all movements
4. Updated line data is returned to frontend
5. UI displays new totals immediately

### Best Practices
- Use meaningful references (invoice numbers, order IDs)
- Add notes for manual adjustments
- Fetch movements list to show audit trail
- Refresh line data after adding movements
- Validate quantity inputs on frontend

## Testing

You can test the endpoints using curl or Postman:

```bash
# Add a purchase
curl -X POST \
  http://localhost:8000/api/stock_tracker/hotel-slug/stocktake-lines/45/add-movement/ \
  -H "Content-Type: application/json" \
  -d '{
    "movement_type": "PURCHASE",
    "quantity": 24,
    "reference": "INV-12345"
  }'

# Get all movements
curl http://localhost:8000/api/stock_tracker/hotel-slug/stocktake-lines/45/movements/
```

## Future Enhancements

Potential additions:
- Bulk movement creation (add multiple movements at once)
- Movement editing (before stocktake approval)
- Movement deletion (with audit log)
- Movement templates for common entries
- Import movements from CSV
- Movement approval workflow
