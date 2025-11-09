# API Reference: Stocktake Line Movements

## Endpoints

### 1. Add Movement to Line
```
POST /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/add-movement/
```

**Creates a new StockMovement record and updates line calculations**

#### Request
```json
{
  "movement_type": "PURCHASE",      // Required: PURCHASE|SALE|WASTE|TRANSFER_IN|TRANSFER_OUT|ADJUSTMENT
  "quantity": 24.0,                  // Required: Decimal
  "unit_cost": 2.50,                 // Optional: Decimal
  "reference": "INV-12345",          // Optional: String
  "notes": "Manual entry"            // Optional: String
}
```

#### Response (201 Created)
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
    "purchases": "72.0000",           // ← Updated
    "sales": "120.0000",
    "waste": "0.0000",
    "transfers_in": "0.0000",
    "transfers_out": "0.0000",
    "adjustments": "0.0000",
    "expected_qty": "40.0000",        // ← Recalculated
    "counted_qty": "42.0000",
    "variance_qty": "2.0000"          // ← Recalculated
  }
}
```

#### Errors
```json
// 400 Bad Request - Missing required fields
{
  "error": "movement_type and quantity are required"
}

// 400 Bad Request - Invalid movement type
{
  "error": "Invalid movement_type. Must be one of: PURCHASE, SALE, WASTE, ..."
}

// 400 Bad Request - Stocktake is locked
{
  "error": "Cannot add movements to approved stocktake"
}
```

---

### 2. Get Line Movements
```
GET /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/movements/
```

**Returns all movements for this line within the stocktake period**

#### Response (200 OK)
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
      "hotel": 1,
      "item": 23,
      "item_sku": "D001",
      "item_name": "Guinness Keg",
      "period": 4,
      "movement_type": "PURCHASE",
      "quantity": "24.0000",
      "unit_cost": "2.5000",
      "reference": "INV-12345",
      "notes": "Manual entry for delivery",
      "staff": 5,
      "staff_name": "John Smith",
      "timestamp": "2025-11-09T14:30:00Z"
    },
    {
      "id": 155,
      "hotel": 1,
      "item": 23,
      "item_sku": "D001",
      "item_name": "Guinness Keg",
      "period": 4,
      "movement_type": "SALE",
      "quantity": "45.0000",
      "unit_cost": null,
      "reference": "POS-Daily",
      "notes": "Automated from POS",
      "staff": null,
      "staff_name": null,
      "timestamp": "2025-11-08T23:59:00Z"
    }
  ]
}
```

---

## Movement Types

| Type | Description | Use Case |
|------|-------------|----------|
| `PURCHASE` | Purchase/Delivery | Adding new stock |
| `SALE` | Sale/Consumption | Stock sold to customers |
| `WASTE` | Waste/Breakage | Damaged or expired stock |
| `TRANSFER_IN` | Transfer In | Stock received from another location |
| `TRANSFER_OUT` | Transfer Out | Stock sent to another location |
| `ADJUSTMENT` | Stocktake Adjustment | Manual corrections |

---

## Calculation Formula

After adding a movement, the line's `expected_qty` is recalculated:

```
expected_qty = opening_qty 
             + purchases 
             - sales 
             - waste 
             + transfers_in 
             - transfers_out 
             + adjustments
```

---

## JavaScript/TypeScript Examples

### Add Movement (Fetch API)
```typescript
async function addMovement(
  hotelSlug: string,
  lineId: number,
  movementData: {
    movement_type: string;
    quantity: number;
    reference?: string;
    notes?: string;
  }
) {
  const response = await fetch(
    `/api/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/add-movement/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${yourAuthToken}`
      },
      body: JSON.stringify(movementData)
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error);
  }
  
  return await response.json();
}

// Usage
try {
  const result = await addMovement('hotel-slug', 45, {
    movement_type: 'PURCHASE',
    quantity: 24,
    reference: 'INV-12345'
  });
  
  console.log('Movement added:', result.movement);
  console.log('Updated line data:', result.line);
} catch (error) {
  console.error('Failed to add movement:', error.message);
}
```

### Get Movements (Axios)
```typescript
import axios from 'axios';

async function getLineMovements(hotelSlug: string, lineId: number) {
  const { data } = await axios.get(
    `/api/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/movements/`
  );
  
  return data;
}

// Usage
const { summary, movements } = await getLineMovements('hotel-slug', 45);
console.log(`Total purchases: ${summary.total_purchases}`);
console.log(`${movements.length} movements found`);
```

### React Hook
```typescript
import { useState, useCallback } from 'react';

function useLineMovements(hotelSlug: string, lineId: number) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const addMovement = useCallback(async (movementData: any) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `/api/stock_tracker/${hotelSlug}/stocktake-lines/${lineId}/add-movement/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(movementData)
        }
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error);
      }
      
      return await response.json();
    } catch (err: any) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [hotelSlug, lineId]);
  
  return { addMovement, loading, error };
}

// Usage in component
function StocktakeLine({ hotelSlug, lineId }) {
  const { addMovement, loading, error } = useLineMovements(hotelSlug, lineId);
  
  const handleAddPurchase = async () => {
    try {
      const result = await addMovement({
        movement_type: 'PURCHASE',
        quantity: 24,
        reference: 'INV-12345'
      });
      
      // Update your state with result.line
    } catch (err) {
      console.error('Failed:', err);
    }
  };
  
  return (
    <button onClick={handleAddPurchase} disabled={loading}>
      {loading ? 'Adding...' : 'Add Purchase'}
    </button>
  );
}
```

---

## Python Examples (for testing)

### Using requests
```python
import requests

def add_movement(hotel_slug, line_id, movement_data):
    url = f'http://localhost:8000/api/stock_tracker/{hotel_slug}/stocktake-lines/{line_id}/add-movement/'
    response = requests.post(url, json=movement_data)
    response.raise_for_status()
    return response.json()

# Usage
result = add_movement('hotel-slug', 45, {
    'movement_type': 'PURCHASE',
    'quantity': 24,
    'reference': 'INV-12345'
})

print(f"Movement created: {result['movement']['id']}")
print(f"New purchases total: {result['line']['purchases']}")
```

### Using curl
```bash
# Add purchase
curl -X POST \
  http://localhost:8000/api/stock_tracker/hotel-slug/stocktake-lines/45/add-movement/ \
  -H "Content-Type: application/json" \
  -d '{
    "movement_type": "PURCHASE",
    "quantity": 24,
    "reference": "INV-12345",
    "notes": "Manual entry"
  }'

# Get movements
curl http://localhost:8000/api/stock_tracker/hotel-slug/stocktake-lines/45/movements/
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | GET successful |
| 201 | Movement created successfully |
| 400 | Bad request (validation error) |
| 401 | Unauthorized |
| 404 | Line not found |

---

## Notes

- Movements are **permanent** once stocktake is approved
- Staff member is automatically recorded from authentication
- Timestamp is automatically set to current time
- Quantities are in **base units** (servings/pints/shots)
- All decimals support 4 decimal places
