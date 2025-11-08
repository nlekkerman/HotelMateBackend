# Frontend: How to Display Full and Partial Units

## Overview

The API returns **both raw and display-friendly** stock values for each snapshot. Use the **display** fields for the UI.

---

## API Response Structure

```json
{
  "id": 3308,
  "item_sku": "B0075",
  "item_name": "Bulmers 33cl",
  "category_code": "B",
  
  // RAW VALUES (backend storage)
  "closing_full_units": "0.00",
  "closing_partial_units": "121.0000",
  
  // DISPLAY VALUES (UI-friendly)
  "display_full_units": "10",      // ← Use this in UI (dozens)
  "display_partial_units": "1",     // ← Use this in UI (bottles)
  
  "total_servings": "121.0000",
  "closing_stock_value": "209.63"
}
```

---

## How Display Values Work

### For Items Sold in **Dozens** (Bottles/Beers)

**Item:** Bulmers 33cl (12 bottles per dozen)  
**Total:** 121 bottles

**Display Conversion:**
- `display_full_units` = `10` dozens (10 × 12 = 120 bottles)
- `display_partial_units` = `1` bottle (121 - 120 = 1 remaining)

### For Items Sold **Individually** (Spirits/Wine)

**Item:** Jameson 70cl  
**Total:** 3.5 bottles

**Display As-Is:**
- `display_full_units` = `3` bottles
- `display_partial_units` = `0.5` bottle

### For **Draught Beer** (Kegs)

**Item:** Guinness 50L Keg  
**Total:** 2.75 kegs

**Display As-Is:**
- `display_full_units` = `2` kegs
- `display_partial_units` = `0.75` keg

---

## Frontend UI Implementation

### Table Display

```javascript
// Fetch period snapshots
const response = await fetch('/api/stock_tracker/1/periods/10/');
const period = await response.json();

// Display each item
period.snapshots.forEach(snapshot => {
  displayRow({
    sku: snapshot.item_sku,
    name: snapshot.item_name,
    
    // ✅ USE DISPLAY FIELDS FOR UI
    fullUnits: snapshot.display_full_units,    // Dozens/Cases/Kegs
    partialUnits: snapshot.display_partial_units, // Bottles/Overflow
    
    value: snapshot.closing_stock_value,
    
    // Store snapshot ID for updates
    snapshotId: snapshot.id
  });
});
```

### Example Table

| SKU | Item | Full Units | Partial Units | Value |
|-----|------|------------|---------------|-------|
| B0075 | Bulmers 33cl | `10` dozens | `1` bottle | €209.63 |
| S0120 | Jameson 70cl | `3` bottles | `0.5` bottle | €82.50 |
| D0001 | Guinness 50L | `2` kegs | `0.75` keg | €340.00 |

---

## Input Fields for Staff Counts

```html
<table>
  <thead>
    <tr>
      <th>Item</th>
      <th>Opening Full</th>
      <th>Opening Partial</th>
      <th>Actual Full</th>
      <th>Actual Partial</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Bulmers 33cl</td>
      
      <!-- Opening (pre-filled, read-only) -->
      <td>
        <input type="number" 
               value="10" 
               readonly 
               class="opening-full" />
        <span class="unit-label">dozens</span>
      </td>
      <td>
        <input type="number" 
               value="1" 
               readonly 
               class="opening-partial" />
        <span class="unit-label">bottles</span>
      </td>
      
      <!-- Actual Count (editable) -->
      <td>
        <input type="number" 
               id="actual-full-3308"
               placeholder="Enter dozens"
               class="actual-full" />
        <span class="unit-label">dozens</span>
      </td>
      <td>
        <input type="number" 
               id="actual-partial-3308"
               placeholder="Enter bottles"
               step="1"
               class="actual-partial" />
        <span class="unit-label">bottles</span>
      </td>
    </tr>
  </tbody>
</table>
```

---

## Saving Updated Counts

### Converting Back to Backend Format

When staff enters counts, convert back to raw format:

```javascript
async function saveCount(snapshotId, actualFullDozens, actualPartialBottles) {
  // For DOZENS items: convert back to servings
  // Full: dozens × 12 = bottles
  // Partial: remaining bottles
  
  const snapshot = snapshots.find(s => s.id === snapshotId);
  const item = snapshot.item;
  
  let closingFull, closingPartial;
  
  if (item.size && item.size.includes('Doz')) {
    // Convert dozens back to servings
    closingFull = 0;  // We store everything in partial for dozens
    closingPartial = (actualFullDozens * item.uom) + actualPartialBottles;
  } else {
    // For non-dozen items, use as-is
    closingFull = actualFullDozens;
    closingPartial = actualPartialBottles;
  }
  
  // Update snapshot
  await fetch(`/api/stock_tracker/1/snapshots/${snapshotId}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      closing_full_units: closingFull,
      closing_partial_units: closingPartial
    })
  });
}

// Example: Staff counted 11 dozens + 5 bottles of Bulmers
saveCount(3308, 11, 5);  
// Backend stores: closing_full_units=0, closing_partial_units=137 (11×12+5)
```

---

## Unit Labels by Category

Add appropriate labels based on category:

```javascript
function getUnitLabels(categoryCode, itemSize) {
  if (categoryCode === 'D') {
    return { full: 'kegs', partial: 'kegs' };
  }
  
  if (categoryCode === 'B' && itemSize && itemSize.includes('Doz')) {
    return { full: 'dozens', partial: 'bottles' };
  }
  
  if (categoryCode === 'B') {
    return { full: 'cases', partial: 'bottles' };
  }
  
  if (categoryCode === 'S' || categoryCode === 'W') {
    return { full: 'bottles', partial: 'bottles' };
  }
  
  if (categoryCode === 'M') {
    return { full: 'units', partial: 'units' };
  }
  
  return { full: 'units', partial: 'units' };
}
```

---

## Complete Example

```javascript
// 1. Fetch period with snapshots
const period = await fetch('/api/stock_tracker/1/periods/10/')
  .then(r => r.json());

// 2. Display each item
period.snapshots.forEach(snapshot => {
  const labels = getUnitLabels(
    snapshot.category_code,
    snapshot.item.size
  );
  
  // Create UI row
  const row = document.createElement('tr');
  row.innerHTML = `
    <td>${snapshot.item_name}</td>
    <td>${snapshot.display_full_units} ${labels.full}</td>
    <td>${snapshot.display_partial_units} ${labels.partial}</td>
    <td>
      <input type="number" 
             data-snapshot-id="${snapshot.id}"
             data-type="full"
             placeholder="${labels.full}" />
    </td>
    <td>
      <input type="number" 
             data-snapshot-id="${snapshot.id}"
             data-type="partial"
             placeholder="${labels.partial}" />
    </td>
  `;
  
  tableBody.appendChild(row);
});

// 3. Save button handler
document.getElementById('save-counts').addEventListener('click', async () => {
  const inputs = document.querySelectorAll('input[data-snapshot-id]');
  
  // Group by snapshot ID
  const updates = {};
  inputs.forEach(input => {
    const id = input.dataset.snapshotId;
    const type = input.dataset.type;
    const value = parseFloat(input.value) || 0;
    
    if (!updates[id]) updates[id] = {};
    updates[id][type] = value;
  });
  
  // Save each snapshot
  for (const [id, counts] of Object.entries(updates)) {
    await saveCount(id, counts.full, counts.partial);
  }
  
  alert('✅ All counts saved!');
});
```

---

## Key Points

✅ **Use `display_full_units` and `display_partial_units` for UI display**  
✅ **Backend handles conversion automatically**  
✅ **Different categories have different unit labels**  
✅ **Dozens items show: X dozens + Y bottles**  
✅ **Other items show: X units + Y.decimal units**  

The backend does all the math—frontend just displays and collects input! 🎯
