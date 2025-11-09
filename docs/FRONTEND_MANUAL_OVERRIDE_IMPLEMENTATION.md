# Frontend Implementation Guide: Manual Override Fields

## Overview
Two new optional fields have been added to stocktake lines:
- `manual_purchases_value` - Total purchase value in euros
- `manual_sales_profit` - Sales profit in euros

These fields allow direct entry of financial data when detailed stock movement tracking is not available.

---

## API Response Structure

### StocktakeLine Object
```typescript
interface StocktakeLine {
  id: number;
  stocktake: number;
  item: number;
  item_sku: string;
  item_name: string;
  category_code: string;
  category_name: string;
  
  // Existing movement fields (auto-calculated)
  opening_qty: string;      // "120.0000"
  purchases: string;        // "80.0000"
  sales: string;           // "150.0000"
  waste: string;           // "0.0000"
  transfers_in: string;    // "0.0000"
  transfers_out: string;   // "0.0000"
  adjustments: string;     // "0.0000"
  
  // ✨ NEW: Manual override fields (optional)
  manual_purchases_value: string | null;  // "1250.50" or null
  manual_sales_profit: string | null;     // "850.75" or null
  
  // User count input
  counted_full_units: string;   // "5.00"
  counted_partial_units: string; // "3.00"
  
  // Calculated fields
  counted_qty: string;
  expected_qty: string;
  variance_qty: string;
  expected_value: string;
  counted_value: string;
  variance_value: string;
  valuation_cost: string;
}
```

---

## UI Implementation

### 1. Add Input Fields to Stocktake Form

```typescript
// StocktakeLineForm.tsx
import React, { useState } from 'react';

interface StocktakeLineFormProps {
  line: StocktakeLine;
  onUpdate: (lineId: number, data: Partial<StocktakeLine>) => void;
}

export const StocktakeLineForm: React.FC<StocktakeLineFormProps> = ({ 
  line, 
  onUpdate 
}) => {
  const [showManualFields, setShowManualFields] = useState(
    Boolean(line.manual_purchases_value || line.manual_sales_profit)
  );

  return (
    <div className="stocktake-line-form">
      {/* Existing fields: SKU, Name, Category */}
      <div className="item-info">
        <span>{line.item_sku}</span>
        <span>{line.item_name}</span>
      </div>

      {/* Stock count inputs */}
      <div className="count-inputs">
        <input
          type="number"
          step="0.01"
          value={line.counted_full_units}
          onChange={(e) => onUpdate(line.id, { 
            counted_full_units: e.target.value 
          })}
          placeholder="Full units"
        />
        <input
          type="number"
          step="0.01"
          value={line.counted_partial_units}
          onChange={(e) => onUpdate(line.id, { 
            counted_partial_units: e.target.value 
          })}
          placeholder="Partial units"
        />
      </div>

      {/* Toggle for manual override fields */}
      <button 
        type="button"
        onClick={() => setShowManualFields(!showManualFields)}
        className="toggle-manual-btn"
      >
        {showManualFields ? '− Hide' : '+ Add'} Manual Values
      </button>

      {/* ✨ Manual override fields (conditional) */}
      {showManualFields && (
        <div className="manual-override-section">
          <h4>Manual Financial Data (Optional)</h4>
          
          <div className="input-group">
            <label htmlFor={`purchases-${line.id}`}>
              Total Purchases Value (€)
            </label>
            <input
              id={`purchases-${line.id}`}
              type="number"
              step="0.01"
              value={line.manual_purchases_value || ''}
              onChange={(e) => onUpdate(line.id, { 
                manual_purchases_value: e.target.value || null 
              })}
              placeholder="e.g., 1250.50"
            />
            <small>
              Enter total purchase cost for this item during the period
            </small>
          </div>

          <div className="input-group">
            <label htmlFor={`profit-${line.id}`}>
              Sales Profit (€)
            </label>
            <input
              id={`profit-${line.id}`}
              type="number"
              step="0.01"
              value={line.manual_sales_profit || ''}
              onChange={(e) => onUpdate(line.id, { 
                manual_sales_profit: e.target.value || null 
              })}
              placeholder="e.g., 850.75"
            />
            <small>
              Enter profit from sales for this item during the period
            </small>
          </div>
        </div>
      )}

      {/* Display calculated values */}
      <div className="calculated-values">
        <span>Expected: {line.expected_qty}</span>
        <span>Counted: {line.counted_qty}</span>
        <span>Variance: {line.variance_qty}</span>
      </div>
    </div>
  );
};
```

---

### 2. API Update Function

```typescript
// api/stocktake.ts

export const updateStocktakeLine = async (
  hotelId: string,
  lineId: number,
  data: Partial<StocktakeLine>
): Promise<StocktakeLine> => {
  const response = await fetch(
    `/api/stock_tracker/${hotelId}/stocktake-lines/${lineId}/`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify(data)
    }
  );

  if (!response.ok) {
    throw new Error('Failed to update stocktake line');
  }

  return response.json();
};

// Usage example
const handleUpdateLine = async (lineId: number, updates: Partial<StocktakeLine>) => {
  try {
    const updated = await updateStocktakeLine('1', lineId, {
      counted_full_units: '5.00',
      counted_partial_units: '3.00',
      manual_purchases_value: '1250.50',  // ✨ NEW
      manual_sales_profit: '850.75'        // ✨ NEW
    });
    
    console.log('Updated:', updated);
  } catch (error) {
    console.error('Update failed:', error);
  }
};
```

---

### 3. Bulk Update for Multiple Items

```typescript
// For updating multiple stocktake lines at once

interface ManualValueUpdate {
  lineId: number;
  manual_purchases_value?: string | null;
  manual_sales_profit?: string | null;
}

export const bulkUpdateManualValues = async (
  hotelId: string,
  updates: ManualValueUpdate[]
): Promise<void> => {
  const promises = updates.map(update => 
    updateStocktakeLine(hotelId, update.lineId, {
      manual_purchases_value: update.manual_purchases_value,
      manual_sales_profit: update.manual_sales_profit
    })
  );

  await Promise.all(promises);
};

// Usage: Import from CSV or bulk entry form
const handleBulkImport = async (csvData: ManualValueUpdate[]) => {
  try {
    await bulkUpdateManualValues('1', csvData);
    alert('Bulk update successful!');
  } catch (error) {
    alert('Bulk update failed: ' + error.message);
  }
};
```

---

### 4. CSV Import Feature (Optional)

```typescript
// CSVImportDialog.tsx
import React, { useState } from 'react';
import Papa from 'papaparse';

interface CSVRow {
  item_sku: string;
  manual_purchases_value?: string;
  manual_sales_profit?: string;
}

export const CSVImportDialog: React.FC<{
  stocktakeLines: StocktakeLine[];
  onImport: (updates: ManualValueUpdate[]) => void;
}> = ({ stocktakeLines, onImport }) => {
  const [file, setFile] = useState<File | null>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0];
    if (!uploadedFile) return;

    Papa.parse<CSVRow>(uploadedFile, {
      header: true,
      complete: (results) => {
        const updates: ManualValueUpdate[] = results.data
          .map(row => {
            const line = stocktakeLines.find(l => l.item_sku === row.item_sku);
            if (!line) return null;

            return {
              lineId: line.id,
              manual_purchases_value: row.manual_purchases_value || null,
              manual_sales_profit: row.manual_sales_profit || null
            };
          })
          .filter(Boolean) as ManualValueUpdate[];

        onImport(updates);
      }
    });
  };

  return (
    <div className="csv-import-dialog">
      <h3>Import Manual Values from CSV</h3>
      <p>Expected format:</p>
      <pre>
{`item_sku,manual_purchases_value,manual_sales_profit
S001,1250.50,850.75
S002,890.00,620.30
B015,2500.00,1800.00`}
      </pre>
      
      <input
        type="file"
        accept=".csv"
        onChange={handleFileUpload}
      />
    </div>
  );
};
```

---

### 5. Display in Summary/Report View

```typescript
// StocktakeSummary.tsx

export const StocktakeSummary: React.FC<{ line: StocktakeLine }> = ({ line }) => {
  const hasManualValues = line.manual_purchases_value || line.manual_sales_profit;

  return (
    <div className="stocktake-summary-row">
      <div className="item-info">
        <strong>{line.item_sku}</strong> - {line.item_name}
      </div>

      <div className="values">
        <div>Expected: €{line.expected_value}</div>
        <div>Counted: €{line.counted_value}</div>
        <div>Variance: €{line.variance_value}</div>
      </div>

      {/* Show manual values if present */}
      {hasManualValues && (
        <div className="manual-values-badge">
          <span className="badge">Manual Data</span>
          {line.manual_purchases_value && (
            <div>Purchases: €{line.manual_purchases_value}</div>
          )}
          {line.manual_sales_profit && (
            <div>Profit: €{line.manual_sales_profit}</div>
          )}
        </div>
      )}
    </div>
  );
};
```

---

## Styling Recommendations

```css
/* styles/stocktake.css */

.manual-override-section {
  background: #f8f9fa;
  border: 1px dashed #dee2e6;
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
}

.manual-override-section h4 {
  margin-top: 0;
  color: #495057;
  font-size: 14px;
  font-weight: 600;
}

.manual-override-section .input-group {
  margin-bottom: 16px;
}

.manual-override-section label {
  display: block;
  font-weight: 500;
  margin-bottom: 4px;
  color: #495057;
}

.manual-override-section input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.manual-override-section small {
  display: block;
  margin-top: 4px;
  color: #6c757d;
  font-size: 12px;
}

.toggle-manual-btn {
  background: transparent;
  border: 1px solid #007bff;
  color: #007bff;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  margin-top: 8px;
}

.toggle-manual-btn:hover {
  background: #007bff;
  color: white;
}

.manual-values-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: #e7f3ff;
  border-radius: 4px;
  font-size: 12px;
}

.manual-values-badge .badge {
  background: #007bff;
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 600;
}
```

---

## Validation Rules

```typescript
// validation/stocktake.ts

export const validateManualValues = (
  manual_purchases_value: string | null,
  manual_sales_profit: string | null
): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];

  // Purchase value validation
  if (manual_purchases_value !== null) {
    const purchaseValue = parseFloat(manual_purchases_value);
    
    if (isNaN(purchaseValue)) {
      errors.push('Purchase value must be a valid number');
    } else if (purchaseValue < 0) {
      errors.push('Purchase value cannot be negative');
    } else if (purchaseValue > 999999.99) {
      errors.push('Purchase value is too large');
    }
  }

  // Profit validation
  if (manual_sales_profit !== null) {
    const profitValue = parseFloat(manual_sales_profit);
    
    if (isNaN(profitValue)) {
      errors.push('Sales profit must be a valid number');
    } else if (profitValue > 999999.99) {
      errors.push('Sales profit is too large');
    }
    // Note: Profit CAN be negative (loss)
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};
```

---

## Complete Usage Example

```typescript
// pages/StocktakePage.tsx
import React, { useState, useEffect } from 'react';
import { StocktakeLineForm } from '../components/StocktakeLineForm';
import { fetchStocktake, updateStocktakeLine } from '../api/stocktake';

export const StocktakePage: React.FC = () => {
  const [stocktake, setStocktake] = useState<Stocktake | null>(null);
  const hotelId = '1';
  const stocktakeId = '4';

  useEffect(() => {
    loadStocktake();
  }, []);

  const loadStocktake = async () => {
    const data = await fetchStocktake(hotelId, stocktakeId);
    setStocktake(data);
  };

  const handleUpdateLine = async (
    lineId: number, 
    updates: Partial<StocktakeLine>
  ) => {
    try {
      const updated = await updateStocktakeLine(hotelId, lineId, updates);
      
      // Update local state
      setStocktake(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          lines: prev.lines.map(line => 
            line.id === lineId ? updated : line
          )
        };
      });
    } catch (error) {
      console.error('Failed to update line:', error);
      alert('Update failed');
    }
  };

  if (!stocktake) return <div>Loading...</div>;

  return (
    <div className="stocktake-page">
      <h1>Stocktake: {stocktake.period_start} to {stocktake.period_end}</h1>
      
      <div className="stocktake-lines">
        {stocktake.lines.map(line => (
          <StocktakeLineForm
            key={line.id}
            line={line}
            onUpdate={handleUpdateLine}
          />
        ))}
      </div>
    </div>
  );
};
```

---

## Key Points for Frontend Team

### ✅ DO:
- Make manual fields **optional and collapsible** (hidden by default)
- Use clear labels: "Total Purchases Value (€)" and "Sales Profit (€)"
- Allow **null values** (clearing the field removes the manual override)
- Show visual indicator when manual values are present
- Validate input before sending to API
- Handle decimal numbers (2 decimal places for euro amounts)

### ❌ DON'T:
- Don't make these fields required
- Don't overwrite user data without confirmation
- Don't show these fields prominently - they're for special cases only
- Don't confuse with the auto-calculated `purchases` and `sales` fields

### 📱 Mobile Considerations:
- Use appropriate input types: `type="number"` with `step="0.01"`
- Ensure fields are easily tappable (min 44px height)
- Consider a separate "Advanced" tab for manual fields on mobile

---

## Testing Checklist

- [ ] Can create stocktake line without manual values
- [ ] Can add manual purchase value
- [ ] Can add manual sales profit
- [ ] Can update both values together
- [ ] Can clear manual values (set to null)
- [ ] Manual values persist after page reload
- [ ] Validation prevents invalid input
- [ ] CSV import works correctly
- [ ] Locked stocktakes prevent editing
- [ ] API errors are handled gracefully

---

## Support

For questions or issues, refer to:
- Backend API: `docs/MANUAL_OVERRIDE_FIELDS.md`
- API endpoints: `/api/stock_tracker/{hotel_id}/stocktake-lines/`
- Serializer: `stock_tracker/stock_serializers.py`
