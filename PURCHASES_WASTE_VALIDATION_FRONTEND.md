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

**CRITICAL:** Frontend sends quantity **EXACTLY** as entered by user:
- Draught: pints (e.g., 88, 176)
- Bottled Beer: bottles (e.g., 12, 24, 3)
- Spirits/Wine: bottles (e.g., 6, 0.5)
- Syrups: bottles (e.g., 5, 0.7)
- BIB: boxes (e.g., 3, 0.5)

**NO CONVERSION, NO CALCULATION - just validation!**

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

### 1️⃣ **DRAUGHT BEER** (User enters PINTS)

#### Purchases Input
```typescript
// User enters PINTS - send EXACTLY as entered
function handleDraughtPurchase(pints: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 88 pints per keg
  
  // Validate: must be multiple of 88 (full kegs)
  if (pints % uom !== 0) {
    showError(`Purchases must be full kegs (multiples of ${uom} pints)`);
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: pints  // Send EXACTLY as entered
  });
}

// Examples:
// ✅ User enters 88 pints → send 88
// ✅ User enters 176 pints → send 176
// ❌ User enters 50 pints → rejected (not full keg)
```

#### Waste Input
```typescript
// User enters PINTS - send EXACTLY as entered
function handleDraughtWaste(pints: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 88 pints per keg
  
  // Validate: must be less than full keg
  if (pints >= uom) {
    showError(`Waste must be partial keg only (less than ${uom} pints)`);
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: pints  // Send EXACTLY as entered
  });
}

// Examples:
// ✅ User enters 25 pints → send 25
// ✅ User enters 50.5 pints → send 50.5
// ❌ User enters 88 pints → rejected (full keg)

---

### 2️⃣ **BOTTLED BEER** (User enters BOTTLES)

#### Purchases Input
```typescript
// User enters BOTTLES - send EXACTLY as entered
function handleBottledPurchase(bottles: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 12 bottles per case
  
  // Validate: must be multiple of 12 (full cases)
  if (bottles % uom !== 0) {
    showError(`Purchases must be full cases (multiples of ${uom} bottles)`);
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: bottles  // Send EXACTLY as entered
  });
}

// Examples:
// ✅ User enters 12 bottles → send 12
// ✅ User enters 24 bottles → send 24
// ❌ User enters 7 bottles → rejected (not full case)
```

#### Waste Input
```typescript
// User enters BOTTLES - send EXACTLY as entered
function handleBottledWaste(bottles: number, item: StockItem) {
  const uom = item.item_uom; // e.g., 12 bottles per case
  
  // Validate: must be less than full case
  if (bottles >= uom) {
    showError(`Waste must be partial case only (less than ${uom} bottles)`);
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: bottles  // Send EXACTLY as entered
  });
}

// Examples:
// ✅ User enters 3 bottles → send 3
// ✅ User enters 7 bottles → send 7
// ❌ User enters 12 bottles → rejected (full case)

---

### 3️⃣ **SPIRITS & WINE** (User enters BOTTLES)

#### Purchases Input
```typescript
// User enters BOTTLES - send EXACTLY as entered
function handleSpiritsPurchase(bottles: number) {
  // Validate: must be whole bottles
  if (bottles % 1 !== 0) {
    showError("Purchases must be in full bottles only");
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: bottles  // Send EXACTLY as entered
  });
}

// Examples:
// ✅ User enters 3 bottles → send 3
// ✅ User enters 10 bottles → send 10
// ❌ User enters 2.5 bottles → rejected
```

#### Waste Input
```typescript
// User enters PARTIAL BOTTLES - send EXACTLY as entered
function handleSpiritsWaste(partialBottle: number) {
  // Validate: must be less than 1 bottle
  if (partialBottle >= 1) {
    showError("Waste must be partial bottles only (less than 1)");
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: partialBottle  // Send EXACTLY as entered
  });
}

// Examples:
// ✅ User enters 0.5 → send 0.5
// ✅ User enters 0.7 → send 0.7
// ❌ User enters 1.0 → rejected (full bottle)

---

### 4️⃣ **SOFT DRINKS** (User enters BOTTLES)

Same validation as **Bottled Beer** - must be multiples of UOM for purchases, less than UOM for waste.

---

### 5️⃣ **CORDIALS** (User enters BOTTLES)

Same validation as **Bottled Beer** - must be multiples of UOM for purchases, less than UOM for waste.

---

### 6️⃣ **SYRUPS** (User enters BOTTLES)

Same validation as **Spirits & Wine** - whole bottles for purchases, partial (< 1) for waste.

---

### 7️⃣ **BIB (Bag-in-Box)** (User enters BOXES)

#### Purchases Input
```typescript
// User enters BOXES - send EXACTLY as entered
function handleBIBPurchase(boxes: number) {
  // Validate: must be whole boxes
  if (boxes % 1 !== 0) {
    showError("Purchases must be in full boxes only");
    return;
  }
  
  addMovement({
    movement_type: "PURCHASE",
    quantity: boxes  // Send EXACTLY as entered
  });
}

// Examples:
// ✅ User enters 3 boxes → send 3
// ✅ User enters 5 boxes → send 5
// ❌ User enters 2.5 boxes → rejected
```

#### Waste Input
```typescript
// User enters PARTIAL BOXES - send EXACTLY as entered
function handleBIBWaste(partialBox: number) {
  // Validate: must be less than 1 box
  if (partialBox >= 1) {
    showError("Waste must be partial boxes only (less than 1)");
    return;
  }
  
  addMovement({
    movement_type: "WASTE",
    quantity: partialBox  // Send EXACTLY as entered
  });
}

// Examples:
// ✅ User enters 0.5 → send 0.5
// ✅ User enters 0.25 → send 0.25
// ❌ User enters 1.0 → rejected (full box)

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

| Category | User Enters | Purchases Validation | Waste Validation |
|----------|-------------|---------------------|------------------|
| **Draught (D)** | Pints | Must be multiples of 88<br>(88, 176, 264) | Must be < 88<br>(15, 25.5, 50) |
| **Bottled Beer (B)** | Bottles | Must be multiples of 12<br>(12, 24, 36) | Must be < 12<br>(3, 7, 11) |
| **Spirits (S)** | Bottles | Must be whole numbers<br>(1, 2, 6, 10) | Must be < 1<br>(0.5, 0.7, 0.25) |
| **Wine (W)** | Bottles | Must be whole numbers<br>(1, 2, 4, 6) | Must be < 1<br>(0.3, 0.5, 0.6) |
| **Soft Drinks (M)** | Bottles | Must be multiples of UOM<br>(12, 24) | Must be < UOM<br>(3, 7) |
| **Syrups (M)** | Bottles | Must be whole numbers<br>(1, 5, 10) | Must be < 1<br>(0.5, 0.7) |
| **Cordials (M)** | Bottles | Must be multiples of UOM<br>(12, 24) | Must be < UOM<br>(3, 7) |
| **BIB (M)** | Boxes | Must be whole numbers<br>(1, 3, 5) | Must be < 1<br>(0.25, 0.5) |
| **Bulk Juices (M)** | Boxes | Must be whole numbers<br>(1, 2, 3) | Must be < 1<br>(0.5, 0.75) |

**CRITICAL:** Frontend sends **EXACTLY** what user enters - **NO CONVERSION OR CALCULATION!**

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

- **NO CONVERSION OR CALCULATION** - send EXACTLY what user enters
- **Backend handles all validation** - client-side is just for UX
- **User enters the actual unit backend expects** (pints, bottles, boxes)
- **Trust backend response** - don't calculate locally
- **Display clear error messages** when validation fails
- **Use appropriate input steps** (1 for whole numbers, 0.01 for decimals)
