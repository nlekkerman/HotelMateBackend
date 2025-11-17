# Frontend Implementation Guide: Syrups Input (Individual Bottles)

## 📋 Overview

Syrups are cocktail mixers tracked as **individual bottles with decimal input** (like Spirits/Wine).

**Examples:**
- `4.7` bottles = 4 full + 0.7 partial
- `10.5` bottles = 10 full + 0.5 partial  
- `3.25` bottles = 3 full + 0.25 partial

---

## 🔧 Backend API Response

### `input_fields` for SYRUPS

```json
{
  "input_fields": {
    "full": {
      "name": "counted_full_units",
      "label": "Bottles"
    },
    "partial": {
      "name": "counted_partial_units",
      "label": "Fractional (0-0.99)",
      "max": 0.99,
      "step": 0.01
    }
  }
}
```

### Current API Fields

**Read:**
- `counted_full_units`: Whole bottles (e.g., `4`)
- `counted_partial_units`: Fractional part (e.g., `0.7`)

**Write (Option 1 - Separate Fields):**
```json
{
  "counted_full_units": 4,
  "counted_partial_units": 0.7
}
```

**Write (Option 2 - Single Field Helper):**
```json
{
  "syrup_bottles_input": 4.7
}
```
Backend auto-splits to `full=4`, `partial=0.7`

---

## 🎨 Frontend Implementation

### Option A: Two Input Fields (Like Spirits/Wine)

```tsx
// For SYRUPS subcategory
if (item.subcategory === 'SYRUPS') {
  return (
    <div className="syrup-input">
      <div className="input-group">
        <label>Bottles</label>
        <input
          type="number"
          min="0"
          step="1"
          value={countedFullUnits}
          onChange={(e) => setCountedFullUnits(parseInt(e.target.value) || 0)}
        />
      </div>
      
      <div className="input-group">
        <label>Fractional (0-0.99)</label>
        <input
          type="number"
          min="0"
          max="0.99"
          step="0.01"
          value={countedPartialUnits}
          onChange={(e) => {
            const val = parseFloat(e.target.value) || 0;
            if (val >= 0 && val < 1) {
              setCountedPartialUnits(val);
            }
          }}
        />
      </div>
    </div>
  );
}
```

---

### Option B: Single Decimal Input (Recommended!)

```tsx
// For SYRUPS subcategory
if (item.subcategory === 'SYRUPS') {
  return (
    <div className="syrup-input">
      <label>Total Bottles (e.g., 4.7)</label>
      <input
        type="number"
        min="0"
        step="0.01"
        value={syrupBottlesInput}
        onChange={(e) => setSyrupBottlesInput(e.target.value)}
        placeholder="Enter total bottles (e.g., 4.7)"
      />
      <small className="help-text">
        Enter decimal bottles (e.g., 4.7 = 4 bottles + 70% of a bottle)
      </small>
    </div>
  );
}

// On save/submit:
const totalBottles = parseFloat(syrupBottlesInput) || 0;
const payload = {
  syrup_bottles_input: totalBottles  // Backend handles split
};
```

---

## 📊 Display Logic

### Showing Current Stock

```tsx
// Display as single decimal
if (item.subcategory === 'SYRUPS') {
  const totalBottles = (
    parseFloat(item.current_full_units) + 
    parseFloat(item.current_partial_units)
  ).toFixed(2);
  
  return <span>{totalBottles} bottles</span>;
}
```

### Display Examples:
- `4 + 0.7 = 4.70 bottles`
- `10 + 0.5 = 10.50 bottles`
- `3 + 0.0 = 3.00 bottles`

---

## ✅ Validation Rules

```typescript
function validateSyrupInput(value: number): boolean {
  // Must be non-negative
  if (value < 0) return false;
  
  // Must be a valid number
  if (isNaN(value)) return false;
  
  // Max 2 decimal places
  const decimals = value.toString().split('.')[1];
  if (decimals && decimals.length > 2) return false;
  
  return true;
}
```

---

## 📝 Complete Example Component

```tsx
interface SyrupInputProps {
  line: StocktakeLine;
  onUpdate: (lineId: number, data: any) => void;
}

const SyrupInput: React.FC<SyrupInputProps> = ({ line, onUpdate }) => {
  const [bottles, setBottles] = useState<string>(
    (line.counted_full_units + line.counted_partial_units).toFixed(2)
  );
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setBottles(value);
    
    const numValue = parseFloat(value);
    if (!isNaN(numValue) && numValue >= 0) {
      // Send update with helper field
      onUpdate(line.id, {
        syrup_bottles_input: numValue
      });
    }
  };
  
  return (
    <div className="syrup-input-container">
      <label htmlFor={`syrup-${line.id}`}>
        {line.item_name}
      </label>
      <input
        id={`syrup-${line.id}`}
        type="number"
        min="0"
        step="0.01"
        value={bottles}
        onChange={handleChange}
        placeholder="0.00"
        className="form-input"
      />
      <span className="unit-label">bottles</span>
      
      <div className="help-text">
        <small>
          Enter as decimal (e.g., 4.7 = 4 full + 0.7 partial)
        </small>
      </div>
    </div>
  );
};
```

---

## 🔄 Backend Calculations

The backend automatically:

1. **Splits decimal input:**
   - `4.7` → `full=4`, `partial=0.7`

2. **Calculates servings:**
   - `(4 + 0.7) × 700ml ÷ 35ml = 94 servings`

3. **Calculates value:**
   - `(4 + 0.7) × €10.25 = €48.18`

4. **Returns display values:**
   - `counted_display_full_units: "4"`
   - `counted_display_partial_units: "0.70"`

---

## 🎯 Key Points

1. ✅ **Simple for users**: One decimal input (like "4.7 bottles")
2. ✅ **Accurate costing**: Partial bottles tracked for valuation
3. ✅ **Consistent with Spirits/Wine**: Same logic pattern
4. ✅ **Backend handles complexity**: Frontend just sends decimal
5. ✅ **Alternative available**: Can also send separate `counted_full_units` and `counted_partial_units`

---

## 🚀 Recommended Approach

**Use Option B (Single Decimal Input)** because:
- ✅ Simpler user experience
- ✅ Less validation complexity
- ✅ Backend already supports it via `syrup_bottles_input`
- ✅ Matches how bartenders think ("We have 4 and a half bottles")
