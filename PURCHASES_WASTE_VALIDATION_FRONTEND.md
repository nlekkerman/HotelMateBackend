# 🛒🗑️ Purchases & Waste Validation - Frontend Implementation Guide

## ✅ Validation Rules Implemented (Backend)

### **PURCHASES = FULL UNITS ONLY**
Purchases must be recorded in complete physical units:
- **Kegs, Cases, Bottles, Boxes** - NO partial units allowed

### **WASTE = PARTIAL UNITS ONLY**
Waste must be recorded from opened/partial items:
- **Partial kegs, opened cases, partial bottles** - NO full units allowed

---

## 📋 API Response Format

When adding purchases or waste, the backend will validate and return:

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

### 1️⃣ **DRAUGHT BEER** (Quantity in Pints)

#### Purchases Input
```typescript
// User enters KEGS, backend receives PINTS
function handleDraughtPurchase(kegs: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 88 pints per keg
  const quantity = kegs * uom;  // Convert kegs to pints
  
  // Validate: must be whole kegs
  if (kegs % 1 !== 0) {
    showError("Purchases must be in full kegs only");
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: quantity  // e.g., 88, 176, 264
  });
}

// Examples:
// ✅ 1 keg → 88 pints
// ✅ 2 kegs → 176 pints
// ❌ 1.5 kegs → rejected
// ❌ 50 pints → rejected (not a full keg)
```

#### Waste Input
```typescript
// User enters PINTS (from opened keg)
function handleDraughtWaste(pints: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 88 pints per keg
  
  // Validate: must be less than full keg
  if (pints >= uom) {
    showError(`Waste must be partial keg only (less than ${uom} pints)`);
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: pints  // e.g., 15, 25.5, 50
  });
}

// Examples:
// ✅ 25 pints (partial keg)
// ✅ 50.5 pints (partial keg)
// ❌ 88 pints (full keg - use adjustment instead)
```

---

### 2️⃣ **BOTTLED BEER** (Quantity in Bottles)

#### Purchases Input
```typescript
// User enters CASES, backend receives BOTTLES
function handleBottledPurchase(cases: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 12 bottles per case
  const quantity = cases * uom;  // Convert cases to bottles
  
  // Validate: must be whole cases
  if (cases % 1 !== 0) {
    showError("Purchases must be in full cases only");
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: quantity  // e.g., 12, 24, 36
  });
}

// Examples:
// ✅ 2 cases → 24 bottles
// ✅ 5 cases → 60 bottles
// ❌ 1.5 cases → rejected
// ❌ 7 bottles → rejected (not full case)
```

#### Waste Input
```typescript
// User enters BOTTLES (from opened case)
function handleBottledWaste(bottles: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 12 bottles per case
  
  // Validate: must be less than full case
  if (bottles >= uom) {
    showError(`Waste must be partial case only (less than ${uom} bottles)`);
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: bottles  // e.g., 2, 5, 11
  });
}

// Examples:
// ✅ 3 bottles (from opened case)
// ✅ 7 bottles (from opened case)
// ❌ 12 bottles (full case - use adjustment instead)
```

---

### 3️⃣ **SPIRITS & WINE** (Quantity = Bottles, UOM=1)

#### Purchases Input
```typescript
// User enters BOTTLES, backend receives BOTTLES (1:1)
function handleSpiritsPurchase(bottles: number) {
  // Validate: must be whole bottles
  if (bottles % 1 !== 0) {
    showError("Purchases must be in full bottles only");
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: bottles  // e.g., 1, 5, 10
  });
}

// Examples:
// ✅ 3 bottles
// ✅ 10 bottles
// ❌ 2.5 bottles → rejected
// ❌ 5.75 bottles → rejected
```

#### Waste Input
```typescript
// User enters PARTIAL BOTTLE (0.00 - 0.99)
function handleSpiritsWaste(partialBottle: number) {
  // Validate: must be less than 1 bottle
  if (partialBottle >= 1) {
    showError("Waste must be partial bottles only (less than 1)");
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: partialBottle  // e.g., 0.25, 0.50, 0.75
  });
}

// Examples:
// ✅ 0.5 bottle
// ✅ 0.25 bottle
// ✅ 0.99 bottle
// ❌ 1.0 bottle (full bottle - use adjustment instead)
```

---

### 4️⃣ **SOFT DRINKS** (Quantity in Bottles)

#### Purchases Input
```typescript
// User enters CASES, backend receives BOTTLES
function handleSoftDrinksPurchase(cases: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 12 bottles per case
  const quantity = cases * uom;
  
  // Validate: must be whole cases
  if (cases % 1 !== 0) {
    showError("Purchases must be in full cases only");
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: quantity  // e.g., 12, 24, 36
  });
}
```

#### Waste Input
```typescript
// User enters BOTTLES (from opened case)
function handleSoftDrinksWaste(bottles: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 12 bottles per case
  
  if (bottles >= uom) {
    showError(`Waste must be partial case only (less than ${uom} bottles)`);
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: bottles
  });
}
```

---

### 5️⃣ **CORDIALS** (Quantity in Bottles)

Same logic as **Soft Drinks** above.

---

### 6️⃣ **SYRUPS** (Quantity = Bottles, UOM=1)

Same logic as **Spirits & Wine** above.

---

### 7️⃣ **BIB (Bag-in-Box)** (Quantity = Boxes, UOM=1)

#### Purchases Input
```typescript
// User enters BOXES, backend receives BOXES (1:1)
function handleBIBPurchase(boxes: number) {
  // Validate: must be whole boxes
  if (boxes % 1 !== 0) {
    showError("Purchases must be in full boxes only");
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: boxes  // e.g., 2, 5, 10
  });
}

// Examples:
// ✅ 3 boxes
// ✅ 5 boxes
// ❌ 2.5 boxes → rejected
```

#### Waste Input
```typescript
// User enters PARTIAL BOX (0.00 - 0.99)
function handleBIBWaste(partialBox: number) {
  // Validate: must be less than 1 box
  if (partialBox >= 1) {
    showError("Waste must be partial boxes only (less than 1)");
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: partialBox  // e.g., 0.25, 0.50
  });
}

// Examples:
// ✅ 0.5 box (half empty)
// ✅ 0.25 box
// ❌ 1.0 box (use adjustment instead)
```

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
  
  // Determine input label and conversion
  const getInputConfig = () => {
    if (category === 'D') {
      return { label: 'Kegs', convert: (v: number) => v * uom };
    }
    if (category === 'B' || 
        (category === 'M' && ['SOFT_DRINKS', 'CORDIALS'].includes(item.subcategory))) {
      return { label: 'Cases', convert: (v: number) => v * uom };
    }
    if (category === 'S' || category === 'W' || 
        (category === 'M' && ['SYRUPS', 'BIB', 'BULK_JUICES'].includes(item.subcategory))) {
      return { label: 'Bottles/Boxes', convert: (v: number) => v };
    }
    return { label: 'Units', convert: (v: number) => v };
  };
  
  const config = getInputConfig();
  
  const handleSubmit = () => {
    const numValue = parseFloat(value);
    
    // Validation: must be whole number
    if (numValue % 1 !== 0) {
      showError(`Purchases must be in full ${config.label.toLowerCase()} only`);
      return;
    }
    
    const quantity = config.convert(numValue);
    onAdd(quantity);
    setValue("");
  };
  
  return (
    <div className="purchases-input">
      <label>Add Purchases ({config.label})</label>
      <input
        type="number"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="0"
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
  
  // Determine input label and validation
  const getInputConfig = () => {
    if (category === 'D') {
      return { label: 'Pints (from opened keg)', max: uom - 0.01, step: 0.5 };
    }
    if (category === 'B' || 
        (category === 'M' && ['SOFT_DRINKS', 'CORDIALS'].includes(item.subcategory))) {
      return { label: 'Bottles (from opened case)', max: uom - 1, step: 1 };
    }
    if (category === 'S' || category === 'W' || 
        (category === 'M' && ['SYRUPS', 'BIB', 'BULK_JUICES'].includes(item.subcategory))) {
      return { label: 'Partial bottle/box', max: 0.99, step: 0.01 };
    }
    return { label: 'Partial units', max: uom - 0.01, step: 0.01 };
  };
  
  const config = getInputConfig();
  
  const handleSubmit = () => {
    const numValue = parseFloat(value);
    
    // Validation: must be less than max
    if (numValue > config.max) {
      showError(`Waste must be less than full unit (max: ${config.max})`);
      return;
    }
    
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
        placeholder="0"
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
| **Draught (D)** | Full kegs only<br>(88, 176, 264 pints) | Partial keg only<br>(< 88 pints) |
| **Bottled Beer (B)** | Full cases only<br>(12, 24, 36 bottles) | Partial case only<br>(< 12 bottles) |
| **Spirits (S)** | Full bottles only<br>(1, 2, 3... bottles) | Partial bottle only<br>(< 1 bottle) |
| **Wine (W)** | Full bottles only<br>(1, 2, 3... bottles) | Partial bottle only<br>(< 1 bottle) |
| **Soft Drinks (M)** | Full cases only<br>(12, 24 bottles) | Partial case only<br>(< 12 bottles) |
| **Syrups (M)** | Full bottles only<br>(1, 2, 3... bottles) | Partial bottle only<br>(< 1 bottle) |
| **Cordials (M)** | Full cases only<br>(12, 24 bottles) | Partial case only<br>(< 12 bottles) |
| **BIB (M)** | Full boxes only<br>(1, 2, 3... boxes) | Partial box only<br>(< 1 box) |
| **Bulk Juices (M)** | Full bottles only<br>(1, 2, 3... bottles) | Partial bottle only<br>(< 1 bottle) |

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
3. **Update input labels** based on category (kegs vs cases vs bottles)
4. **Set appropriate step values** (1 for whole numbers, 0.01 for decimals)
5. **Test all categories** with both valid and invalid values
6. **Ensure error messages** are user-friendly and actionable

---

## 📝 Notes

- **Backend handles all validation** - client-side is just for UX
- **Always convert to base units** before sending to backend
- **Trust backend response** - don't calculate locally
- **Display clear error messages** when validation fails
- **Use appropriate input steps** (whole numbers vs decimals)
