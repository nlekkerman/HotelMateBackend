# Beer Update Handling Analysis - Bottled & Draft Beers

## Overview
This document analyzes how the system handles **COUNT**, **PURCHASE**, and **WASTE** updates for **Bottled Beers (B)** and **Draft Beers (D)** based on the actual implementation in models, views, and serializers.

---

## 1. COUNT Updates (Manual Stocktake Entry)

### What Happens When User Counts Stock

#### Data Storage (StocktakeLine Model)
```python
# Fields that store counted values
counted_full_units = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=Decimal('0.00'),
    help_text="Full cases/kegs/bottles counted"
)
counted_partial_units = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=Decimal('0.00'),
    help_text="Partial units (e.g., 7 bottles from a case)"
)
```

#### Frontend Input Fields (Serializer)

**Draft Beer (Category D):**
```python
{
    'full': {'name': 'counted_full_units', 'label': 'Kegs'},
    'partial': {'name': 'counted_partial_units', 'label': 'Pints', 'step': 0.25}
}
```

**Bottled Beer (Category B):**
```python
{
    'full': {'name': 'counted_full_units', 'label': 'Cases'},
    'partial': {'name': 'counted_partial_units', 'label': 'Bottles', 'max': 23}
}
```

### Conversion Logic (Model Property)

#### Draft Beer Conversion
```python
# category == 'D':
# counted_full_units = kegs (e.g., 2)
# counted_partial_units = pints (e.g., 20.5)

full_servings = self.counted_full_units * self.item.uom  # 2 * 88 = 176 pints
return full_servings + self.counted_partial_units        # 176 + 20.5 = 196.5 pints
```

**Example:**
- User enters: **2 kegs + 20.5 pints**
- Stored as: `counted_full_units=2`, `counted_partial_units=20.5`
- Calculated: `counted_qty = 196.5 pints` (assuming 88 pints per keg)

#### Bottled Beer Conversion
```python
# category == 'B':
# counted_full_units = cases (e.g., 5)
# counted_partial_units = bottles (e.g., 7)

full_servings = self.counted_full_units * self.item.uom  # 5 * 12 = 60 bottles
return full_servings + self.counted_partial_units        # 60 + 7 = 67 bottles
```

**Example:**
- User enters: **5 cases + 7 bottles**
- Stored as: `counted_full_units=5`, `counted_partial_units=7`
- Calculated: `counted_qty = 67 bottles` (assuming 12 bottles per case)

### Update Endpoint (Views)

**Endpoint:** `PATCH /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/`

**Request Body:**
```json
{
  "counted_full_units": 5,
  "counted_partial_units": 7
}
```

**Process:**
1. Validates stocktake is not locked (status != APPROVED)
2. Updates `counted_full_units` and `counted_partial_units` directly
3. Model automatically recalculates `counted_qty` via property
4. Recalculates variance: `variance_qty = counted_qty - expected_qty`
5. Broadcasts update via Pusher to other users viewing the stocktake

**Key Code (views.py):**
```python
def update(self, request, *args, **kwargs):
    instance = self.get_object()
    
    if instance.stocktake.is_locked:
        return Response({"error": "Cannot edit approved stocktake"})
    
    # Update the fields
    serializer = self.get_serializer(instance, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    self.perform_update(serializer)
    
    # Refresh to get calculated values
    instance.refresh_from_db()
    response_serializer = self.get_serializer(instance)
    
    # Broadcast to other users
    broadcast_line_counted_updated(hotel_identifier, instance.stocktake.id, ...)
    
    return Response(response_serializer.data)
```

---

## 2. PURCHASE Updates (Add Inventory Movement)

### What Happens When User Records a Purchase

#### Data Storage (StockMovement Model)
Purchases create **permanent audit records** in the `StockMovement` table:
```python
movement = StockMovement.objects.create(
    hotel=line.stocktake.hotel,
    item=line.item,
    period=period,              # Linked to StockPeriod (not individual line)
    movement_type='PURCHASE',
    quantity=quantity_decimal,  # In servings (pints/bottles)
    unit_cost=unit_cost,
    reference=reference,
    notes=notes,
    staff=staff_user,
    timestamp=movement_timestamp
)
```

### Purchase Validation Rules

#### Draft Beer (Category D)
```python
# User enters: KEGS
# Backend expects: WHOLE NUMBERS only

if quantity_decimal % 1 != 0:
    return Response({
        "error": "Purchases must be in full kegs only. "
                 "Partial kegs should be recorded as waste."
    })

# CONVERSION: kegs → pints
quantity_decimal = quantity_decimal * uom  # e.g., 2 kegs * 88 = 176 pints
```

**Examples:**
- ✅ User enters **2 kegs** → Stored as **176 pints** (2 × 88)
- ✅ User enters **5 kegs** → Stored as **440 pints** (5 × 88)
- ❌ User enters **2.5 kegs** → **REJECTED** (must be whole kegs)

#### Bottled Beer (Category B)
```python
# User enters: CASES
# Backend expects: WHOLE NUMBERS only

if quantity_decimal % 1 != 0:
    return Response({
        "error": "Purchases must be in full cases only. "
                 "Partial cases should be recorded as waste."
    })

# CONVERSION: cases → bottles
quantity_decimal = quantity_decimal * uom  # e.g., 5 cases * 12 = 60 bottles
```

**Examples:**
- ✅ User enters **5 cases** → Stored as **60 bottles** (5 × 12)
- ✅ User enters **10 cases** → Stored as **120 bottles** (10 × 12)
- ❌ User enters **3.5 cases** → **REJECTED** (must be whole cases)

### Purchase Endpoint

**Endpoint:** `POST /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/add-movement/`

**Request Body (Draft Beer):**
```json
{
  "movement_type": "PURCHASE",
  "quantity": 2,           // 2 KEGS (user-friendly)
  "unit_cost": 150.00,
  "reference": "INV-12345",
  "notes": "Weekly delivery"
}
```

**Backend Process:**
1. Validates: `quantity % 1 == 0` (whole kegs/cases only)
2. Converts: `quantity = 2 kegs * 88 = 176 pints`
3. Creates `StockMovement` record with `quantity=176`
4. Recalculates line totals from ALL movements in period
5. Updates `line.purchases` field with SUM of all PURCHASE movements
6. Recalculates `expected_qty` and `variance_qty`

**Key Code (views.py):**
```python
if movement_type == 'PURCHASE':
    if uom == Decimal('1'):
        # Spirits, Wine - quantity is bottles (1:1)
        if quantity_decimal % 1 != 0:
            return Response({"error": "Must be whole bottles"})
    else:
        # Draught, Bottled Beer - quantity is kegs/cases
        if quantity_decimal % 1 != 0:
            unit_name = 'kegs' if category == 'D' else 'cases'
            return Response({
                "error": f"Purchases must be in full {unit_name} only"
            })
        
        # CONVERT: kegs/cases → pints/bottles
        quantity_decimal = quantity_decimal * uom

# Create movement
movement = StockMovement.objects.create(...)

# Recalculate from ALL movements
from .stocktake_service import _calculate_period_movements
movements = _calculate_period_movements(
    line.item,
    line.stocktake.period_start,
    line.stocktake.period_end
)

line.purchases = movements['purchases']  # SUM of all PURCHASE movements
line.waste = movements['waste']          # SUM of all WASTE movements
line.save()
```

### How Purchases are Aggregated

**Calculation Logic (stocktake_service.py):**
```python
def _calculate_period_movements(item, period_start, period_end):
    """Sum ALL movements in the period"""
    
    movements = item.movements.filter(
        timestamp__gte=start_dt,
        timestamp__lte=end_dt
    ).aggregate(
        purchases=Sum('quantity', filter=Q(movement_type='PURCHASE')),
        waste=Sum('quantity', filter=Q(movement_type='WASTE')),
        ...
    )
    
    return {
        'purchases': movements['purchases'] or Decimal('0'),
        'waste': movements['waste'] or Decimal('0'),
        ...
    }
```

**Example Timeline:**
- Movement 1: PURCHASE 176 pints (2 kegs)
- Movement 2: PURCHASE 88 pints (1 keg)
- Movement 3: PURCHASE 264 pints (3 kegs)
- **Result:** `line.purchases = 528 pints` (SUM of all)

---

## 3. WASTE Updates (Record Spoilage/Loss)

### What Happens When User Records Waste

#### Data Storage (StockMovement Model)
Same as purchases - creates permanent audit record:
```python
movement = StockMovement.objects.create(
    hotel=line.stocktake.hotel,
    item=line.item,
    period=period,
    movement_type='WASTE',    # Different type
    quantity=quantity_decimal,
    reference=reference,
    notes=notes,
    staff=staff_user
)
```

### Waste Validation Rules

#### Draft Beer (Category D)
```python
# User enters: PINTS (partial kegs)
# Backend expects: LESS THAN FULL KEG

if quantity_decimal >= uom:  # Must be < 88 pints
    return Response({
        "error": f"Waste must be partial keg only "
                 f"(less than {int(uom)} pints)"
    })

# NO CONVERSION - quantity stays as pints
```

**Examples:**
- ✅ User enters **25 pints** → Stored as **25 pints**
- ✅ User enters **50.5 pints** → Stored as **50.5 pints**
- ✅ User enters **87.99 pints** → Stored as **87.99 pints**
- ❌ User enters **88 pints** → **REJECTED** (full keg, use negative adjustment)
- ❌ User enters **176 pints** → **REJECTED** (2 full kegs)

#### Bottled Beer (Category B)
```python
# User enters: BOTTLES (partial cases)
# Backend expects: LESS THAN FULL CASE

if quantity_decimal >= uom:  # Must be < 12 bottles
    return Response({
        "error": f"Waste must be partial case only "
                 f"(less than {int(uom)} bottles)"
    })

# NO CONVERSION - quantity stays as bottles
```

**Examples:**
- ✅ User enters **3 bottles** → Stored as **3 bottles**
- ✅ User enters **7 bottles** → Stored as **7 bottles**
- ✅ User enters **11 bottles** → Stored as **11 bottles**
- ❌ User enters **12 bottles** → **REJECTED** (full case, use negative adjustment)
- ❌ User enters **24 bottles** → **REJECTED** (2 full cases)

### Waste Endpoint

**Endpoint:** `POST /api/stock_tracker/{hotel}/stocktake-lines/{line_id}/add-movement/`

**Request Body (Bottled Beer):**
```json
{
  "movement_type": "WASTE",
  "quantity": 7,           // 7 BOTTLES (from opened case)
  "reference": "Broken bottles",
  "notes": "Dropped case during delivery"
}
```

**Backend Process:**
1. Validates: `quantity < uom` (partial units only)
2. NO conversion - stores bottles as-is
3. Creates `StockMovement` record with `quantity=7`
4. Recalculates line totals from ALL movements in period
5. Updates `line.waste` field with SUM of all WASTE movements
6. Recalculates `expected_qty` and `variance_qty`

**Key Code (views.py):**
```python
elif movement_type == 'WASTE':
    if uom == Decimal('1'):
        # Spirits, Wine - waste must be < 1 bottle
        if quantity_decimal >= 1:
            return Response({
                "error": "Waste must be partial bottles only (less than 1)"
            })
    else:
        # Draught, Bottled Beer - waste must be < full unit
        if quantity_decimal >= uom:
            if category == 'D':
                unit_name = f'partial keg only (less than {int(uom)} pints)'
            elif category == 'B':
                unit_name = f'partial case only (less than {int(uom)} bottles)'
            
            return Response({
                "error": f"Waste must be {unit_name}"
            })

# NO conversion for waste - use quantity as-is
movement = StockMovement.objects.create(
    movement_type='WASTE',
    quantity=quantity_decimal  # Stored directly
)
```

---

## 4. Expected Quantity & Variance Calculation

### Formula (Model Property)

```python
@property
def expected_qty(self):
    """
    Formula: expected = opening + purchases - waste
    Sales are NOT included - calculated separately
    """
    return (
        self.opening_qty +
        self.purchases -
        self.waste
    )

@property
def variance_qty(self):
    """
    Variance = counted - expected
    Positive = surplus, Negative = shortage
    """
    return self.counted_qty - self.expected_qty
```

### Complete Example (Draft Beer)

**Scenario:**
- Opening: 176 pints (2 kegs)
- Purchase 1: 2 kegs → +176 pints
- Purchase 2: 1 keg → +88 pints
- Waste 1: 25 pints (spoiled)
- Waste 2: 10 pints (spilled)
- Counted: 3 kegs + 20 pints = 284 pints

**Calculation:**
```
opening_qty = 176 pints
purchases = 176 + 88 = 264 pints
waste = 25 + 10 = 35 pints

expected_qty = 176 + 264 - 35 = 405 pints
counted_qty = (3 * 88) + 20 = 284 pints
variance_qty = 284 - 405 = -121 pints (shortage)
```

### Complete Example (Bottled Beer)

**Scenario:**
- Opening: 60 bottles (5 cases)
- Purchase 1: 5 cases → +60 bottles
- Purchase 2: 3 cases → +36 bottles
- Waste 1: 7 bottles (broken)
- Waste 2: 3 bottles (expired)
- Counted: 8 cases + 5 bottles = 101 bottles

**Calculation:**
```
opening_qty = 60 bottles
purchases = 60 + 36 = 96 bottles
waste = 7 + 3 = 10 bottles

expected_qty = 60 + 96 - 10 = 146 bottles
counted_qty = (8 * 12) + 5 = 101 bottles
variance_qty = 101 - 146 = -45 bottles (shortage)
```

---

## 5. Voice Command Integration

### How Voice Commands Apply Updates

Voice commands use the **exact same logic** as manual updates but with automated parsing.

**Voice Command Flow:**
1. **Transcribe audio** → text
2. **Parse command** → extract action, item, value
3. **Confirm with user** → show preview
4. **Apply update** → use standard endpoints

### Count via Voice

```python
# Command: "count guinness three kegs and twenty pints"
# Parsed: action=count, item=guinness, full_units=3, partial_units=20

if action == 'count':
    line.counted_full_units = full_units    # 3
    line.counted_partial_units = partial_units  # 20
    line.save()
    # Same as manual entry!
```

### Purchase via Voice

```python
# Command: "purchase two kegs of guinness"
# Parsed: action=purchase, item=guinness, value=2

if action == 'purchase':
    # Creates StockMovement with quantity=2 (will be converted to pints)
    # Uses add_movement endpoint logic
    movement = StockMovement.objects.create(
        movement_type='PURCHASE',
        quantity=Decimal(str(value))  # 2 kegs
    )
    # Backend converts and recalculates
```

### Waste via Voice

```python
# Command: "waste five bottles of heineken"
# Parsed: action=waste, item=heineken, value=5

if action == 'waste':
    # Creates StockMovement with quantity=5 bottles
    movement = StockMovement.objects.create(
        movement_type='WASTE',
        quantity=Decimal(str(value))  # 5 bottles
    )
    # Backend validates and recalculates
```

---

## 6. Key Differences: Draft vs Bottled Beer

| Aspect | Draft Beer (D) | Bottled Beer (B) |
|--------|---------------|------------------|
| **UOM** | 88 pints (keg size varies) | 12 bottles (standard case) |
| **Count Input** | Kegs + Pints | Cases + Bottles |
| **Count Storage** | `full_units=kegs`, `partial_units=pints` | `full_units=cases`, `partial_units=bottles` |
| **Count Conversion** | `(kegs × 88) + pints` | `(cases × 12) + bottles` |
| **Purchase Input** | Kegs (whole numbers) | Cases (whole numbers) |
| **Purchase Validation** | Must be integer (no 2.5 kegs) | Must be integer (no 3.5 cases) |
| **Purchase Conversion** | `kegs × 88 = pints` | `cases × 12 = bottles` |
| **Waste Input** | Pints (from opened keg) | Bottles (from opened case) |
| **Waste Validation** | Must be < 88 pints | Must be < 12 bottles |
| **Waste Conversion** | None (stays as pints) | None (stays as bottles) |
| **Base Unit** | Pints | Bottles |

---

## 7. Critical Implementation Notes

### 1. Two-Phase Conversion for Purchases
- **Frontend sends:** User-friendly units (kegs/cases)
- **Backend converts:** To base units (pints/bottles)
- **Database stores:** Base units only

### 2. No Conversion for Waste
- **Frontend sends:** Base units (pints/bottles)
- **Backend stores:** As-is (no conversion)
- **Reason:** Waste is from opened containers

### 3. Aggregation via SUM
- Multiple movements are **summed**, not concatenated
- Each movement is a separate audit record
- Line fields (`purchases`, `waste`) store totals

### 4. Automatic Recalculation
- Every movement triggers recalculation of line totals
- `expected_qty` and `variance_qty` update automatically
- Broadcast to all users via Pusher

### 5. Validation Prevents Errors
- Purchases: Only full units (prevents fractional kegs/cases)
- Waste: Only partial units (prevents full units as waste)
- Locked stocktakes: Cannot be modified

---

## 8. Summary

### COUNT Updates
- **User enters:** Kegs+Pints or Cases+Bottles
- **System stores:** Two separate fields (`counted_full_units`, `counted_partial_units`)
- **System calculates:** Total servings via model property
- **Update method:** Direct field update + recalculation

### PURCHASE Updates
- **User enters:** Whole kegs/cases only
- **System validates:** Must be integer (no partials)
- **System converts:** Kegs→Pints or Cases→Bottles
- **System stores:** `StockMovement` record in base units
- **System aggregates:** SUM of all PURCHASE movements
- **Update method:** Create movement + recalculate all movements

### WASTE Updates
- **User enters:** Partial pints/bottles only
- **System validates:** Must be less than full unit
- **System stores:** `StockMovement` record (no conversion)
- **System aggregates:** SUM of all WASTE movements
- **Update method:** Create movement + recalculate all movements

### Result
- **Expected:** `opening + purchases - waste`
- **Variance:** `counted - expected`
- **All calculations:** Automatic via model properties
- **All updates:** Broadcast to other users in real-time
