# 🛒🗑️ Purchases & Waste Validation - Frontend Implementation Guide

## ✅ Validation Rules Implemented (Backend)

### **PURCHASES = FULL UNITS ONLY**
Purchases must be recorded in complete physical units:
- **Kegs, Cases, Bottles, Boxes** - NO partial units allowed

### **WASTE = PARTIAL UNITS ONLY**
Waste must be recorded from opened/partial items:
- **Partial kegs, opened cases, partial bottles** - NO full units allowed

---

## 📋 API Endpoint & Payload

**Endpoint:** `POST /api/stocktake-lines/{line_id}/add_movement/`

**Payload Structure:**
```json
{
  "movement_type": "PURCHASE" | "WASTE",
  "quantity": number,  // EXACTLY as user enters - NO CONVERSION
  "notes": "optional string"
}
```

**CRITICAL:** Frontend sends EXACTLY what user enters - Backend does conversion!

**PURCHASES:**
- Draught: User enters KEGS → send kegs (e.g., 2, 5, 10)
- Bottled Beer: User enters CASES → send cases (e.g., 5, 10, 20)
- Spirits/Wine/Syrups: User enters BOTTLES → send bottles (e.g., 6, 10)
- BIB: User enters BOXES → send boxes (e.g., 3, 5)

**WASTE:**
- Draught: User enters PINTS → send pints (e.g., 25, 50)
- Bottled Beer: User enters BOTTLES → send bottles (e.g., 3, 7)
- Spirits/Wine/Syrups: User enters PARTIAL BOTTLES → send partial (e.g., 0.5, 0.7)
- BIB: User enters PARTIAL BOXES → send partial (e.g., 0.25, 0.5)

**Backend converts kegs→pints and cases→bottles automatically!**

### ✅ Success Response
```json
{
  "message": "Movement created successfully",
  "movement": {
    "id": 501,
    "movement_type": "PURCHASE",
    "quantity": "88.0000",
    "timestamp": "2024-11-20T10:00:00Z"
  },
  "line": {
    "id": 123,
    "purchases": "88.0000",
    "waste": "0.0000",
    "expected_qty": "136.0000"
    // ... full line data
  }
}
```

### ❌ Error Response
```json
{
  "error": "Purchases must be in full kegs only (88 pints per keg). Partial kegs should be recorded as waste."
}
```

---

## 🎯 Frontend Implementation by Category

### 1️⃣ **DRAUGHT BEER**

#### Purchases Input
```typescript
// User enters KEGS → send KEGS (backend converts)
function handleDraughtPurchase(kegs: number) {
  // Validate: must be whole kegs
  if (kegs % 1 !== 0) {
    showError("Purchases must be full kegs only");
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: kegs  // Send 2, 5, 10 (backend converts to pints)
  });
}

// Examples:
// ✅ User enters 2 kegs → send 2
// ✅ User enters 5 kegs → send 5
// ❌ User enters 1.5 kegs → rejected
```

#### Waste Input
```typescript
// User enters PINTS → send PINTS
function handleDraughtWaste(pints: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 88 pints per keg
  
  // Validate: must be less than full keg
  if (pints >= uom) {
    showError(`Waste must be less than ${uom} pints`);
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: pints  // Send 25, 50.5
  });
}

// Examples:
// ✅ User enters 25 pints → send 25
// ✅ User enters 50.5 pints → send 50.5
// ❌ User enters 88 pints → rejected

---

### 2️⃣ **BOTTLED BEER**

#### Purchases Input
```typescript
// User enters CASES → send CASES (backend converts)
function handleBottledPurchase(cases: number) {
  // Validate: must be whole cases
  if (cases % 1 !== 0) {
    showError("Purchases must be full cases only");
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: cases  // Send 5, 10, 20 (backend converts to bottles)
  });
}

// Examples:
// ✅ User enters 5 cases → send 5
// ✅ User enters 10 cases → send 10
// ❌ User enters 3.5 cases → rejected
```

#### Waste Input
```typescript
// User enters BOTTLES → send BOTTLES
function handleBottledWaste(bottles: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 12 bottles per case
  
  // Validate: must be less than full case
  if (bottles >= uom) {
    showError(`Waste must be less than ${uom} bottles`);
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: bottles  // Send 3, 7, 11
  });
}

// Examples:
// ✅ User enters 3 bottles → send 3
// ✅ User enters 7 bottles → send 7
// ❌ User enters 12 bottles → rejected

---

### 3️⃣ **SPIRITS & WINE**

#### Purchases Input
```typescript
// User enters BOTTLES → send BOTTLES
function handleSpiritsPurchase(bottles: number) {
  // Validate: must be whole bottles
  if (bottles % 1 !== 0) {
    showError("Purchases must be full bottles only");
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: bottles  // Send 3, 6, 10
  });
}

// Examples:
// ✅ User enters 3 bottles → send 3
// ✅ User enters 10 bottles → send 10
// ❌ User enters 2.5 bottles → rejected
```

#### Waste Input
```typescript
// User enters PARTIAL BOTTLES → send PARTIAL
function handleSpiritsWaste(partialBottle: number) {
  // Validate: must be less than 1 bottle
  if (partialBottle >= 1) {
    showError("Waste must be partial bottles only (less than 1)");
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: partialBottle  // Send 0.5, 0.7
  });
}

// Examples:
// ✅ User enters 0.5 → send 0.5
// ✅ User enters 0.7 → send 0.7
// ❌ User enters 1.0 → rejected

---

### 4️⃣ **SOFT DRINKS**

**Same as Bottled Beer:** User enters CASES for purchases, BOTTLES for waste.

---

### 5️⃣ **CORDIALS**

**Same as Bottled Beer:** User enters CASES for purchases, BOTTLES for waste.

---

### 6️⃣ **SYRUPS**

**Same as Spirits & Wine:** User enters BOTTLES for purchases (send as-is, must be whole), PARTIAL BOTTLES for waste (send as-is, must be < 1).

---

### 7️⃣ **BIB (Bag-in-Box)**

**Same as Spirits & Wine:** User enters BOXES for purchases (send as-is, must be whole), PARTIAL BOXES for waste (send as-is, must be < 1).

---

### 8️⃣ **BULK JUICES**

**Same as Spirits & Wine:** User enters CONTAINERS for purchases (send as-is, must be whole), PARTIAL for waste (send as-is, must be < 1).

---

## 🎨 UI Components

### Purchases Input Component

```typescript
interface PurchasesInputProps {
  item: StockItem;
  onAdd: (quantity: number) => void;
}

export function PurchasesInput({ item, onAdd }: PurchasesInputProps) {
  const [value, setValue] = useState("");
  const category = item.category_code;
  const uom = item.item_uom;
  
  // Determine input label (NO CONVERSION!)
  const getInputConfig = () => {
    if (category === 'D') {
      return { label: 'Pints', placeholder: 'e.g., 88, 176' };
    }
    if (category === 'B' || 
        (category === 'M' && ['SOFT_DRINKS', 'CORDIALS'].includes(item.subcategory))) {
      return { label: 'Bottles', placeholder: 'e.g., 12, 24' };
    }
    if (category === 'S' || category === 'W' || 
        (category === 'M' && ['SYRUPS'].includes(item.subcategory))) {
      return { label: 'Bottles', placeholder: 'e.g., 6, 10' };
    }
    if (category === 'M' && ['BIB', 'BULK_JUICES'].includes(item.subcategory)) {
      return { label: 'Boxes', placeholder: 'e.g., 3, 5' };
    }
    return { label: 'Units', placeholder: '0' };
  };
  
  const config = getInputConfig();
  
  const handleSubmit = () => {
    const numValue = parseFloat(value);
    
    // Validate based on UOM
    if (uom === 1) {
      // Must be whole numbers
      if (numValue % 1 !== 0) {
        showError(`Purchases must be whole ${config.label.toLowerCase()}`);
        return;
      }
    } else {
      // Must be multiples of UOM
      if (numValue % uom !== 0) {
        showError(`Purchases must be multiples of ${uom} ${config.label.toLowerCase()}`);
        return;
      }
    }
    
    // Send EXACTLY as entered - NO CONVERSION!
    onAdd(numValue);
    setValue("");
  };
  
  return (
    <div className="purchases-input">
      <label>Add Purchases ({config.label})</label>
      <input
        type="number"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={config.placeholder}
        step="1"
        min="1"
      />
      <button onClick={handleSubmit}>💾 Add Purchase</button>
    </div>
  );
}
```

### Waste Input Component

```typescript
interface WasteInputProps {
  item: StockItem;
  onAdd: (quantity: number) => void;
}

export function WasteInput({ item, onAdd }: WasteInputProps) {
  const [value, setValue] = useState("");
  const category = item.category_code;
  const uom = item.item_uom;
  
  // Determine input label (NO CONVERSION!)
  const getInputConfig = () => {
    if (category === 'D') {
      return { label: 'Pints', max: uom - 0.01, step: 0.5, placeholder: 'e.g., 15, 25.5' };
    }
    if (category === 'B' || 
        (category === 'M' && ['SOFT_DRINKS', 'CORDIALS'].includes(item.subcategory))) {
      return { label: 'Bottles', max: uom - 1, step: 1, placeholder: 'e.g., 3, 7' };
    }
    if (category === 'S' || category === 'W' || 
        (category === 'M' && ['SYRUPS'].includes(item.subcategory))) {
      return { label: 'Partial Bottles', max: 0.99, step: 0.01, placeholder: 'e.g., 0.5, 0.7' };
    }
    if (category === 'M' && ['BIB', 'BULK_JUICES'].includes(item.subcategory)) {
      return { label: 'Partial Boxes', max: 0.99, step: 0.01, placeholder: 'e.g., 0.5, 0.25' };
    }
    return { label: 'Partial units', max: uom - 0.01, step: 0.01, placeholder: '0' };
  };
  
  const config = getInputConfig();
  
  const handleSubmit = () => {
    const numValue = parseFloat(value);
    
    // Validate: must be less than threshold
    if (numValue >= (uom === 1 ? 1 : uom)) {
      showError(`Waste must be partial only (less than ${uom === 1 ? '1' : uom})`);
      return;
    }
    
    // Send EXACTLY as entered - NO CONVERSION!
    onAdd(numValue);
    setValue("");
  };
  
  return (
    <div className="waste-input">
      <label>Add Waste ({config.label})</label>
      <input
        type="number"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={config.placeholder}
        step={config.step}
        max={config.max}
        min="0.01"
      />
      <button onClick={handleSubmit}>🗑️ Add Waste</button>
    </div>
  );
}
```

---

## 📊 Validation Summary Table

| Category | Purchases | Waste |
|----------|-----------|-------|
| **Draught (D)** | User enters: **KEGS**<br>Send: kegs (backend converts)<br>Example: 2 kegs → send 2 | User enters: **PINTS**<br>Send: pints (must be < 88)<br>Example: 25 pints → send 25 |
| **Bottled Beer (B)** | User enters: **CASES**<br>Send: cases (backend converts)<br>Example: 5 cases → send 5 | User enters: **BOTTLES**<br>Send: bottles (must be < 12)<br>Example: 3 bottles → send 3 |
| **Spirits (S)** | User enters: **BOTTLES**<br>Send: bottles (must be whole)<br>Example: 6 bottles → send 6 | User enters: **PARTIAL**<br>Send: partial (must be < 1)<br>Example: 0.7 → send 0.7 |
| **Wine (W)** | User enters: **BOTTLES**<br>Send: bottles (must be whole)<br>Example: 4 bottles → send 4 | User enters: **PARTIAL**<br>Send: partial (must be < 1)<br>Example: 0.5 → send 0.5 |
| **Soft Drinks (M)** | User enters: **CASES**<br>Send: cases (backend converts)<br>Example: 3 cases → send 3 | User enters: **BOTTLES**<br>Send: bottles (must be < UOM)<br>Example: 5 → send 5 |
| **Syrups (M)** | User enters: **BOTTLES**<br>Send: bottles (must be whole)<br>Example: 10 bottles → send 10 | User enters: **PARTIAL**<br>Send: partial (must be < 1)<br>Example: 0.7 → send 0.7 |
| **Cordials (M)** | User enters: **CASES**<br>Send: cases (backend converts)<br>Example: 2 cases → send 2 | User enters: **BOTTLES**<br>Send: bottles (must be < UOM)<br>Example: 7 → send 7 |
| **BIB (M)** | User enters: **BOXES**<br>Send: boxes (must be whole)<br>Example: 3 boxes → send 3 | User enters: **PARTIAL**<br>Send: partial (must be < 1)<br>Example: 0.5 → send 0.5 |
| **Bulk Juices (M)** | User enters: **CONTAINERS**<br>Send: containers (must be whole)<br>Example: 2 → send 2 | User enters: **PARTIAL**<br>Send: partial (must be < 1)<br>Example: 0.75 → send 0.75 |

**SIMPLE:** Frontend sends EXACTLY what user enters - Backend does ALL conversion!

---

## 🔍 Error Handling

### Client-Side Validation (Pre-Submit)
```typescript
function validatePurchase(quantity: number, item: StockItem): boolean {
  const uom = item.item_uom;
  
  if (uom === 1) {
    // UOM=1: Must be whole number
    if (quantity % 1 !== 0) {
      showError("Purchases must be in full units only");
      return false;
    }
  } else {
    // UOM>1: Must be multiple of UOM
    if (quantity % uom !== 0) {
      showError(`Purchases must be in full units (multiples of ${uom})`);
      return false;
    }
  }
  
  return true;
}

function validateWaste(quantity: number, item: StockItem): boolean {
  const uom = item.item_uom;
  
  if (uom === 1) {
    // UOM=1: Must be < 1
    if (quantity >= 1) {
      showError("Waste must be partial units only (less than 1)");
      return false;
    }
  } else {
    // UOM>1: Must be < UOM
    if (quantity >= uom) {
      showError(`Waste must be partial units only (less than ${uom})`);
      return false;
    }
  }
  
  return true;
}
```

### Server-Side Validation (Backend Response)
```typescript
async function addMovement(lineId: number, data: MovementData) {
  try {
    const response = await api.post(
      `/stocktake-lines/${lineId}/add-movement/`,
      data
    );
    
    // Success: Update UI with new values
    updateLine(response.data.line);
    showSuccess("Movement added successfully");
    
  } catch (error) {
    // Backend validation failed
    if (error.response?.data?.error) {
      showError(error.response.data.error);
    } else {
      showError("Failed to add movement");
    }
  }
}
```

---

## ✅ Testing Checklist

- [ ] Draught purchases: accepts full kegs only
- [ ] Draught waste: accepts partial kegs only
- [ ] Bottled purchases: accepts full cases only
- [ ] Bottled waste: accepts partial cases only
- [ ] Spirits purchases: accepts whole bottles only
- [ ] Spirits waste: accepts partial bottles only
- [ ] Wine purchases: accepts whole bottles only
- [ ] Wine waste: accepts partial bottles only
- [ ] Soft Drinks purchases: accepts full cases only
- [ ] Soft Drinks waste: accepts partial cases only
- [ ] Syrups purchases: accepts whole bottles only
- [ ] Syrups waste: accepts partial bottles only
- [ ] BIB purchases: accepts whole boxes only
- [ ] BIB waste: accepts partial boxes only
- [ ] Error messages display correctly
- [ ] Backend validation works when client-side bypassed

---

## 🚀 Quick Implementation Steps

1. **Add client-side validation** to input fields (prevent invalid submissions)
2. **Handle backend error responses** (display validation errors)
3. **Update input labels** based on category (pints vs bottles vs boxes)
4. **Set appropriate step values** (1 for whole numbers, 0.01 for decimals)
5. **Test all categories** with both valid and invalid values
6. **Ensure error messages** are user-friendly and actionable

---

## 📝 Notes

- **NO CONVERSION ON FRONTEND** - send exactly what user enters
- **Backend does ALL conversion** (kegs→pints, cases→bottles) and validation
- **User-friendly input labels** (show "Cases" for purchases, "Bottles" for waste)
- **Simple frontend validation** - just check whole numbers for purchases
- **Display clear error messages** when backend validation fails
- **Use appropriate input steps** (1 for cases/kegs/bottles, 0.01 for partials)
