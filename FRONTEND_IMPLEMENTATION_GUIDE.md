# Frontend Implementation Guide - Minerals & Syrups Subcategories

## API Response Changes

### StockItem Endpoint
**GET** `/api/stock-tracker/items/`

```json
{
  "id": 123,
  "sku": "M0320",
  "name": "Grenadine Syrup",
  "category_code": "M",
  "category_name": "Minerals & Syrups",
  "subcategory": "SYRUPS",
  "subcategory_display": "Syrups & Flavourings",
  "size": "70cl",
  "uom": "700.00",
  "current_full_units": "7.00",
  "current_partial_units": "350.0000"
}
```

### StocktakeLine Endpoint
**GET** `/api/stock-tracker/stocktakes/{id}/`

```json
{
  "lines": [
    {
      "id": 1523,
      "item_sku": "M0320",
      "item_name": "Grenadine Syrup",
      "category_code": "M",
      "subcategory": "SYRUPS",
      "input_fields": {
        "full": {
          "name": "counted_full_units",
          "label": "Bottles"
        },
        "partial": {
          "name": "counted_partial_units",
          "label": "ml",
          "max": 1000
        }
      },
      "counted_full_units": "5.00",
      "counted_partial_units": "250.00",
      "counted_display_full_units": "5",
      "counted_display_partial_units": "250"
    }
  ]
}
```

**Example for Draught Beer:**
```json
{
  "item_sku": "D0101",
  "item_name": "Guinness 50L",
  "category_code": "D",
  "input_fields": {
    "full": {"name": "counted_full_units", "label": "Kegs"},
    "partial": {"name": "counted_partial_units", "label": "Pints", "step": 0.25}
  }
}
```

**Example for Spirits:**
```json
{
  "item_sku": "S0610",
  "item_name": "Smirnoff 1Ltr",
  "category_code": "S",
  "input_fields": {
    "full": {"name": "counted_full_units", "label": "Bottles"},
    "partial": {"name": "counted_partial_units", "label": "Fractional (0-0.99)", "max": 0.99, "step": 0.05}
  }
}
```

---

## Frontend Components to Update

### 1. Stocktake Counting Form

Replace generic input fields with subcategory-specific inputs.

#### Current Implementation (Generic)
```tsx
// ❌ OLD - Don't use this anymore
<Input label="Full Units" name="counted_full_units" />
<Input label="Partial Units" name="counted_partial_units" />
```

#### New Implementation (Universal - All Categories)
```tsx
// ✅ NEW - Works for ALL categories using input_fields from API
function UniversalCountingInputs({ line }) {
  const { input_fields } = line;
  
  // API provides everything needed - just render it!
  if (!input_fields) {
    // Fallback if API doesn't provide input_fields
    return (
      <>
        <Input label="Full Units" name="counted_full_units" type="number" />
        <Input label="Partial Units" name="counted_partial_units" type="number" />
      </>
    );
  }
  
  return (
    <>
      <Input 
        label={input_fields.full.label}
        name={input_fields.full.name}
        type="number" 
        min="0"
        step={input_fields.full.step}
        max={input_fields.full.max}
      />
      <Input 
        label={input_fields.partial.label}
        name={input_fields.partial.name}
        type="number" 
        min="0"
        step={input_fields.partial.step}
        max={input_fields.partial.max}
      />
    </>
  );
}

// Example Usage:
// Draught: "Kegs" and "Pints" (step 0.25)
// Bottled: "Cases" and "Bottles" (max 23)
// Spirits: "Bottles" and "Fractional (0-0.99)" (step 0.05, max 0.99)
// Minerals SYRUPS: "Bottles" and "ml" (max 1000)
// Minerals BIB: "Boxes" and "Liters" (step 0.1, max 18)
```

---

### 2. Display Labels (Simplified!)

The API now provides labels directly - no need for complex logic:

```tsx
// ✅ SIMPLE - Just use the labels from API
function StocktakeLineDisplay({ line }) {
  const { input_fields, counted_display_full_units, counted_display_partial_units } = line;
  
  return (
    <div>
      <p>{counted_display_full_units} {input_fields.full.label}</p>
      <p>{counted_display_partial_units} {input_fields.partial.label}</p>
    </div>
  );
}

// Examples of what you'll see:
// Draught: "6 Kegs + 39.75 Pints"
// Bottled: "12 Cases + 7 Bottles"
// Spirits: "2 Bottles + 0.30 Fractional (0-0.99)"
// Syrups: "5 Bottles + 250 ml"
// BIB: "1 Boxes + 0.80 Liters"
```

---

### 3. Validation Rules (Universal!)

Use the `max` value from input_fields for validation:

```tsx
function validateCountingInput(inputFields, fullUnits, partialUnits) {
  const partial = parseFloat(partialUnits);
  
  // Check max value if provided
  if (inputFields.partial.max && partial > inputFields.partial.max) {
    return { 
      valid: false, 
      error: `${inputFields.partial.label} cannot exceed ${inputFields.partial.max}` 
    };
  }
  
  // Check if should be whole number (no step specified or step = 1)
  const step = inputFields.partial.step || 1;
  if (step === 1 && partial % 1 !== 0) {
    return { 
      valid: false, 
      error: `${inputFields.partial.label} must be whole numbers` 
    };
  }
  
  return { valid: true };
}

// Examples of validation messages:
// Soft Drinks: "Bottles cannot exceed 11"
// Spirits: "Fractional (0-0.99) cannot exceed 0.99"
// BIB: "Liters cannot exceed 18"
// Syrups: "ml cannot exceed 1000"
```

---

### 4. Helper Text / Instructions

Show contextual help based on subcategory:

```tsx
function MineralsHelpText({ subcategory }) {
  const helpText = {
    SOFT_DRINKS: 'Count full cases (12 bottles each) and loose bottles (0-11)',
    SYRUPS: 'Count full bottles (700ml or 1L) and ml in any open bottle',
    JUICES: 'Count full bottles (1L or 1.5L) and ml in any open bottle',
    CORDIALS: 'Count full cases and individual bottles (no serving calculation)',
    BIB: 'Count full boxes (18L each) and liters remaining in current box'
  };
  
  return (
    <div className="help-text">
      <InfoIcon />
      <span>{helpText[subcategory] || 'Enter counted quantities'}</span>
    </div>
  );
}
```

---

### 5. Category Filter / Grouping

Update category filters to show subcategories:

```tsx
function StocktakeCategoryFilter({ onFilterChange }) {
  return (
    <select onChange={(e) => onFilterChange(e.target.value)}>
      <option value="">All Categories</option>
      <option value="D">Draught Beer</option>
      <option value="B">Bottled Beer</option>
      <option value="S">Spirits</option>
      <option value="W">Wine</option>
      
      {/* Minerals with subcategories */}
      <optgroup label="Minerals & Syrups">
        <option value="M:SOFT_DRINKS">→ Soft Drinks (Bottled)</option>
        <option value="M:SYRUPS">→ Syrups & Flavourings</option>
        <option value="M:JUICES">→ Juices & Lemonades</option>
        <option value="M:CORDIALS">→ Cordials</option>
        <option value="M:BIB">→ Bag-in-Box (18L)</option>
      </optgroup>
    </select>
  );
}
```

---

### 6. Visual Indicators

Add icons or badges to identify subcategories:

```tsx
function SubcategoryBadge({ subcategory }) {
  const config = {
    SOFT_DRINKS: { icon: '🥤', color: 'blue', label: 'Soft Drinks' },
    SYRUPS: { icon: '🍯', color: 'amber', label: 'Syrups' },
    JUICES: { icon: '🧃', color: 'orange', label: 'Juices' },
    CORDIALS: { icon: '🍶', color: 'purple', label: 'Cordials' },
    BIB: { icon: '📦', color: 'green', label: 'BIB' }
  };
  
  const { icon, color, label } = config[subcategory] || {};
  
  if (!subcategory) return null;
  
  return (
    <span className={`badge badge-${color}`}>
      {icon} {label}
    </span>
  );
}
```

---

## Complete Example: Stocktake Line Row Component

```tsx
import React from 'react';

interface StocktakeLineRowProps {
  line: {
    id: number;
    item_sku: string;
    item_name: string;
    category_code: string;
    subcategory?: string;
    item_size: string;
    counted_full_units: string;
    counted_partial_units: string;
    counted_display_full_units: string;
    counted_display_partial_units: string;
    variance_qty: string;
  };
  onUpdate: (id: number, data: any) => void;
}

export function StocktakeLineRow({ line, onUpdate }: StocktakeLineRowProps) {
  const [fullUnits, setFullUnits] = React.useState(line.counted_full_units);
  const [partialUnits, setPartialUnits] = React.useState(line.counted_partial_units);
  
  const labels = getUnitLabels(line.category_code, line.subcategory);
  
  const handleSave = () => {
    const validation = validateMineralsInput(
      line.subcategory, 
      fullUnits, 
      partialUnits
    );
    
    if (!validation.valid) {
      alert(validation.error);
      return;
    }
    
    onUpdate(line.id, {
      counted_full_units: fullUnits,
      counted_partial_units: partialUnits
    });
  };
  
  return (
    <tr>
      <td>
        {line.item_sku}
        {line.subcategory && <SubcategoryBadge subcategory={line.subcategory} />}
      </td>
      <td>{line.item_name}</td>
      <td>{line.item_size}</td>
      
      {/* Counting Inputs */}
      <td>
        <Input
          label={labels.full}
          value={fullUnits}
          onChange={(e) => setFullUnits(e.target.value)}
          type="number"
          min="0"
        />
      </td>
      <td>
        <Input
          label={labels.partial}
          value={partialUnits}
          onChange={(e) => setPartialUnits(e.target.value)}
          type="number"
          min="0"
          step={line.subcategory === 'BIB' ? '0.1' : '1'}
          max={getMaxPartialUnits(line.subcategory)}
        />
      </td>
      
      {/* Help Text */}
      <td>
        <MineralsHelpText subcategory={line.subcategory} />
      </td>
      
      {/* Display Values */}
      <td>
        {line.counted_display_full_units} {labels.full} + 
        {line.counted_display_partial_units} {labels.partial}
      </td>
      
      {/* Variance */}
      <td className={parseFloat(line.variance_qty) < 0 ? 'text-red' : 'text-green'}>
        {line.variance_qty}
      </td>
      
      <td>
        <button onClick={handleSave}>Save</button>
      </td>
    </tr>
  );
}

function getMaxPartialUnits(subcategory?: string) {
  switch (subcategory) {
    case 'SOFT_DRINKS':
    case 'CORDIALS':
      return 11; // Max 11 bottles in a dozen
    case 'BIB':
      return 18; // Max 18 liters per box
    case 'SYRUPS':
      return 1000; // Max 1000ml per bottle
    case 'JUICES':
      return 1500; // Max 1500ml per bottle
    default:
      return undefined; // No max
  }
}
```

---

## Testing Checklist

### Frontend Testing
- [ ] SOFT_DRINKS: Can enter cases (0-99) and bottles (0-11)
- [ ] SOFT_DRINKS: Validation prevents bottles > 11
- [ ] SYRUPS: Can enter bottles and ml (0-1000)
- [ ] JUICES: Can enter bottles and ml (0-1500)
- [ ] CORDIALS: Can enter cases and bottles (no serving display)
- [ ] BIB: Can enter boxes and liters (0-18 with decimals)
- [ ] BIB: Step size allows 0.1 liter increments
- [ ] Display labels change based on subcategory
- [ ] Help text shows correct instructions
- [ ] Validation errors display correctly
- [ ] Category filters include subcategories
- [ ] Subcategory badges display with correct icons

### API Integration Testing
- [ ] `subcategory` field is read from API response
- [ ] `input_fields` array is used for dynamic form generation
- [ ] `counted_full_units` saves correctly for all subcategories
- [ ] `counted_partial_units` saves correctly for all subcategories
- [ ] Display values (`counted_display_full_units`, `counted_display_partial_units`) format correctly
- [ ] Variance calculations are correct
- [ ] Filtering by subcategory works

---

## Optional: Mobile-Optimized Input

For mobile/tablet stocktaking:

```tsx
function MobileCountingInput({ line }) {
  const { subcategory } = line;
  
  // Use number pad keyboards for better mobile UX
  return (
    <div className="mobile-counter">
      <div className="counter-group">
        <label>{getUnitLabels(line.category_code, subcategory).full}</label>
        <input 
          type="number" 
          inputMode="numeric" 
          pattern="[0-9]*"
          placeholder="0"
        />
      </div>
      
      <div className="counter-group">
        <label>{getUnitLabels(line.category_code, subcategory).partial}</label>
        <input 
          type="number" 
          inputMode="decimal"
          step={subcategory === 'BIB' ? '0.1' : '1'}
          placeholder="0"
        />
      </div>
      
      <MineralsHelpText subcategory={subcategory} />
    </div>
  );
}
```

---

## Summary of Frontend Changes Required

1. ✅ **Read** `subcategory` and `input_fields` from API
2. ✅ **Display** correct input labels (Cases/Bottles/ml/Liters/Boxes)
3. ✅ **Validate** inputs based on subcategory rules
4. ✅ **Show** contextual help text for each subcategory
5. ✅ **Add** subcategory badges/icons for visual identification
6. ✅ **Update** category filters to include subcategories
7. ✅ **Test** all 5 subcategories with real data

**No breaking changes** - the API is backward compatible. If `subcategory` is null/undefined, fall back to generic inputs.
