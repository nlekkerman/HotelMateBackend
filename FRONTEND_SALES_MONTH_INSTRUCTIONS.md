# Frontend: Month-based Sales Entry (UI + API)

This document explains how the frontend should let users create sales assigned to a month (not a specific creation date), how to query those sales by month, and how to link them later to a stocktake if needed.

## Goals
- Allow users to create sales and assign them to a month (e.g. "2025-09").
- Store sales as normal `Sale` records with `sale_date` set to a canonical date for the month (the backend uses the first day of month by default).
- Let the frontend query sales by month (e.g. `?month=2025-09`) and show them in lists and summaries.
- Provide guidance for linking these independent month-sales to stocktakes later.

## Key API endpoints (backend)
- Create sale (accepts `month`):
  - POST `/api/stock_tracker/<hotel_identifier>/sales/`
  - Body can include either `sale_date` (old) or `month` (new). Example body for month:
    ```json
    {
      "item": 123,
      "quantity": "100.0000",
      "unit_cost": "2.1200",
      "unit_price": "6.30",
      "month": "2025-09",
      "notes": "September sales entry"
    }
    ```
  - Backend will set `sale_date` = `2025-09-01` when `month` is provided.

- Query sales by month:
  - GET `/api/stock_tracker/<hotel_identifier>/sales/?month=2025-09`
  - Also supports existing filters: `item`, `category`, `start_date`, `end_date`.

- Sales summary by date range (useful for reporting):
  - GET `/api/stock_tracker/<hotel_identifier>/sales/summary/?start_date=2025-09-01&end_date=2025-09-30`

- (Future) Link sales to stocktake:
  - POST `/api/stock_tracker/<hotel_identifier>/stocktakes/<stocktake_id>/link-sales/`
  - Body: `{ "start_date": "2025-09-01", "end_date": "2025-09-30" }`
  - This will link unlinked sales in the range to the specified stocktake.

## Frontend UX patterns
- Use a month picker when creating sales so user chooses a month instead of a date.
- Show a friendly label: "Assign sale to month" -> display month name (e.g., "September 2025").
- Allow user to optionally pick a specific day if they prefer (keep backward compatibility with `sale_date`).
- When listing sales, provide toggles/filters: `By Month`, `By Date Range`.

## React: Create Sale form (example)
This example uses modern hooks and an HTML month input which returns `YYYY-MM`.

```jsx
import React, { useState } from 'react';

function CreateSaleForm({ hotelIdentifier }) {
  const [itemId, setItemId] = useState('');
  const [quantity, setQuantity] = useState('');
  const [month, setMonth] = useState(new Date().toISOString().slice(0,7)); // e.g. 2025-09
  const [unitCost, setUnitCost] = useState('');
  const [unitPrice, setUnitPrice] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError(null);

    try {
      const body = {
        item: Number(itemId),
        quantity: quantity,
        unit_cost: unitCost || undefined,
        unit_price: unitPrice || undefined,
        month: month, // key difference: send month instead of sale_date
        notes: notes
      };

      const res = await fetch(
        `/api/stock_tracker/${hotelIdentifier}/sales/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        }
      );

      if (!res.ok) throw new Error('Failed to create sale');
      const data = await res.json();
      // handle success (reset form, show toast, etc.)
      console.log('Sale created', data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>Item</label>
      <select value={itemId} onChange={e => setItemId(e.target.value)} required>
        {/* populate items from API */}
      </select>

      <label>Quantity</label>
      <input type="number" step="0.0001" value={quantity} onChange={e => setQuantity(e.target.value)} required />

      <label>Assign to month</label>
      <input type="month" value={month} onChange={e => setMonth(e.target.value)} required />

      <label>Unit cost (optional)</label>
      <input type="number" step="0.0001" value={unitCost} onChange={e => setUnitCost(e.target.value)} />

      <label>Unit price (optional)</label>
      <input type="number" step="0.01" value={unitPrice} onChange={e => setUnitPrice(e.target.value)} />

      <label>Notes</label>
      <textarea value={notes} onChange={e => setNotes(e.target.value)} />

      <button type="submit" disabled={loading}>Create Sale for {month}</button>
      {error && <div className="error">{error}</div>}
    </form>
  );
}

export default CreateSaleForm;
```

## Axios example (create sale for month)

```javascript
import axios from 'axios';

async function createSaleForMonth(hotelIdentifier, saleData) {
  // saleData must include: item, quantity, month (YYYY-MM)
  try {
    const res = await axios.post(
      `/api/stock_tracker/${hotelIdentifier}/sales/`,
      saleData
    );
    return res.data;
  } catch (err) {
    throw err.response?.data || err;
  }
}

// Usage
createSaleForMonth('hotel-killarney', {
  item: 123,
  quantity: '100.0000',
  month: '2025-09',
  unit_cost: '2.12',
  unit_price: '6.30',
  notes: 'September sales entry'
}).then(console.log).catch(console.error);
```

## Querying sales by month (frontend)
- Use endpoint: `GET /api/stock_tracker/<hotel_identifier>/sales/?month=2025-09`
- Use result to show lists, totals, and pass to summary endpoints.

## UX & Validation notes
- `month` should be in `YYYY-MM` format; validate on client-side.
- Show a confirmation dialog when creating many/large sales.
- Preferable default: set month picker to last month when doing historical entry.
- If user wants a specific day instead of month, allow `sale_date` field (backwards compatible).
- Show helpful message: "Sales saved to month — You can later link them to a stocktake for this month."

## Linking to stocktake (frontend workflow)
1. On the Stocktake detail page, show an action: "Link existing month sales"
2. Open modal with pre-filled date range (stocktake.period_start → period_end)
3. Call: `POST /api/stock_tracker/<hotel_identifier>/stocktakes/<id>/link-sales/` with `start_date` + `end_date` (or let backend match same-range)
4. Show the list of affected sales and a confirmation step before linking

## Edge cases
- If user creates sale for a month but later wishes to move to a different month, support editing the sale and changing `month` (which updates `sale_date`).
- If multiple users try to link the same sales to different stocktakes, block linking to closed stocktakes.

## Example flows
- Backfill September: select `month=2025-09`, enter many sales manually → query `?month=2025-09` to review → later link to September stocktake.
- Daily adjustments: allow user to add `sale_date` if they need a specific day.

## Implementation notes for frontend dev
- Ensure the API base path uses underscore `stock_tracker` (not hyphen).
- Reuse existing sale create endpoint; backend supports `month` in request and will set `sale_date`.
- Use `input[type=month]` for quick month selection (supported in modern browsers). For older browsers, provide fallback select boxes (year + month).

---

Created: November 11, 2025
