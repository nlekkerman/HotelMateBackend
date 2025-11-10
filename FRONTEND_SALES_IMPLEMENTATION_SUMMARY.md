# Frontend Sales Integration - Implementation Summary

## ✅ Backend Status: READY

All backend endpoints, models, and logic are **complete and tested**. No backend changes needed.

---

## 📚 Documentation Files

### 1. **SALES_API_QUICK_REFERENCE.md**
**Use for:** Quick lookup of API endpoints
- All endpoints with request/response examples
- Query parameters
- Error codes
- Data validation rules

### 2. **FRONTEND_SALES_ENTRY_GUIDE.md**
**Use for:** Building the UI components
- Complete React component examples
- Modal design with code
- Data fetching patterns
- Styling recommendations
- Testing checklist

### 3. **SALES_ARCHITECTURE_DECISION.md**
**Use for:** Understanding the system design
- Why sales are separate from variance
- Data model explanation
- Entry point locations
- Priority system logic
- Benefits and migration path

---

## 🎯 What You Need to Build

### 1. Sales Entry Button (Stocktake Line)
**Where:** Each stocktake line row
**Action:** Opens sales entry modal
**Display:** Shows current sales total below button

### 2. Sales Entry Modal
**Features:**
- Form to create new sale
- List of existing sales for item
- Delete button for each sale
- Summary totals (quantity, revenue, GP%)
- Pre-filled values from item

### 3. Sales Summary (Stocktake Page)
**Features:**
- Overall metrics (revenue, COGS, GP%)
- Category breakdown table
- Sales count display

### 4. Manual Entry Form (Optional)
**Features:**
- Period-level total sales input
- Period-level total COGS input
- Alternative to itemized entry

---

## 🔗 API Endpoints (Already Built)

```javascript
// List sales for stocktake
GET /api/stock-tracker/{hotel}/sales/?stocktake={id}

// Create sale
POST /api/stock-tracker/{hotel}/sales/
Body: {stocktake, item, quantity, unit_cost, unit_price, sale_date}

// Update sale
PATCH /api/stock-tracker/{hotel}/sales/{id}/
Body: {quantity, unit_price, ...}

// Delete sale
DELETE /api/stock-tracker/{hotel}/sales/{id}/

// Get sales summary
GET /api/stock-tracker/{hotel}/sales/summary/?stocktake={id}

// Get sales for specific line (NEW!)
GET /api/stock-tracker/{hotel}/stocktake-lines/{line_id}/sales/
```

---

## 💡 Key Concepts

### Variance vs Sales
- **Variance** = Physical loss (theft, spillage, errors)
- **Sales** = Business performance (revenue, GP%)
- **Separate** = Better analysis and clarity

### Data Entry
- **Itemized** = Create individual sale records (recommended)
- **Manual** = Enter totals only (simpler, less detail)
- **Priority** = Manual overrides itemized if both exist

### Display Format
- Quantity: Show with serving unit (e.g., "350 pints")
- Currency: Always 2 decimals (e.g., "€7.00")
- Percentages: 1-2 decimals (e.g., "96.8%")

---

## 🚀 Quick Start

### Step 1: Add Sales Button
```jsx
<button onClick={() => openSalesModal(line.item)}>
  📊 Enter Sales
</button>
```

### Step 2: Create Sales Modal Component
See **FRONTEND_SALES_ENTRY_GUIDE.md** for complete code

### Step 3: Fetch Sales Data
```javascript
const response = await fetch(
  `/api/stock-tracker/${hotel}/stocktake-lines/${lineId}/sales/`
);
const {sales, summary, item} = await response.json();
```

### Step 4: Create Sale
```javascript
await fetch(`/api/stock-tracker/${hotel}/sales/`, {
  method: 'POST',
  body: JSON.stringify({
    stocktake: 5,
    item: 123,
    quantity: "350.0000",
    unit_cost: item.cost_per_serving,
    unit_price: item.menu_price,
    sale_date: "2024-11-10"
  })
});
```

---

## ✅ Pre-Implementation Checklist

### Backend Review
- [x] Sale model exists with all fields
- [x] CRUD endpoints working
- [x] Summary endpoint working
- [x] Line sales endpoint working (NEW)
- [x] Manual override fields in models
- [x] Priority calculation system
- [x] Serializers with profitability metrics

### Frontend Planning
- [ ] Identify where to add "Enter Sales" button
- [ ] Design modal layout
- [ ] Plan state management approach
- [ ] Decide on styling framework/CSS
- [ ] Set up API client/fetch logic
- [ ] Plan error handling strategy

### Testing Plan
- [ ] Create sale successfully
- [ ] Update sale
- [ ] Delete sale
- [ ] View sales list
- [ ] Calculate totals correctly
- [ ] Handle errors gracefully
- [ ] Test with locked stocktakes
- [ ] Validate data formats

---

## 🎨 UI/UX Recommendations

### Button Placement
Place sales button **below** variance row, distinct from counting inputs:

```
┌─────────────────────────────────────────────┐
│ Guinness Draught (50L Keg)                  │
├─────────────────────────────────────────────┤
│ Opening:    2 kegs + 15 pints               │
│ Purchases:  3 kegs                          │
│ Waste:      0.5 kegs                        │
│ Expected:   4 kegs + 15 pints               │
│ Counted:    [4] kegs + [10] pints [Edit]   │ ← Physical count
│ Variance:   -5 pints (€11.25 loss)          │ ← Physical loss
├─────────────────────────────────────────────┤
│ [📊 Enter Sales]  Sales: 350 pints (€2,450) │ ← Sales data
└─────────────────────────────────────────────┘
```

### Color Coding
- **Variance (red/green)** - Physical loss/gain
- **Sales (blue/neutral)** - Business metrics
- Keep them visually distinct

### Validation Messages
- "Quantity must be greater than 0"
- "Date must be within stocktake period"
- "Price must be a valid number"

---

## 🆘 Need Help?

### Common Questions

**Q: Where is the selling price stored?**
A: In three places:
1. `StockItem.menu_price` (current price)
2. `Sale.unit_price` (price at time of sale)
3. `StockSnapshot.menu_price` (price at period end)

**Q: How do I prevent editing approved stocktakes?**
A: Check `stocktake.is_locked` property. If true, disable all inputs.

**Q: What if item has no menu_price?**
A: Pre-fill unit_price with empty value. Revenue will be null if not provided.

**Q: Should I use itemized or manual entry?**
A: Start with itemized (more detail). Add manual as fallback option later.

**Q: How do real-time updates work?**
A: Refetch sales data after create/update/delete. Consider adding Pusher for multi-user scenarios.

---

## 📞 Contact

If you encounter issues or need clarification:
1. Check the three documentation files
2. Review API endpoint examples
3. Test endpoints with Postman/curl
4. Verify authentication tokens
5. Check browser console for errors

---

## 🎉 You're Ready!

Everything is prepared on the backend. Just build the UI components following the guides, and you'll have a complete sales tracking system integrated with your stocktake workflow.

**Good luck!** 🚀
