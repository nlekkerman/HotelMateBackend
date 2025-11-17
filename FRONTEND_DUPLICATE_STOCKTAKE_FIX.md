# Frontend: Handling Duplicate Stocktake Error

## The Error

When trying to create a stocktake that already exists for a period, you'll get:

```
Status: 500
Error: IntegrityError
Message: duplicate key value violates unique constraint 
"stock_tracker_stocktake_hotel_id_period_start_pe_7d16c4a2_uniq"
```

---

## Quick Fix (Frontend)

### Option 1: Check Before Creating

```javascript
// stocktakeService.js or similar

async function createStocktake(periodStart, periodEnd) {
  // 1. Check if stocktake already exists
  const existing = await checkExistingStocktake(periodStart, periodEnd);
  
  if (existing) {
    // Show user-friendly message
    throw new Error(
      `A stocktake already exists for ${periodStart} to ${periodEnd}. ` +
      `Opening existing stocktake...`
    );
    // OR navigate to existing:
    // navigate(`/stocktakes/${existing.id}`);
  }
  
  // 2. Safe to create new stocktake
  const response = await fetch('/api/stock_tracker/hotel-killarney/stocktakes/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${authToken}`,
    },
    body: JSON.stringify({
      period_start: periodStart,
      period_end: periodEnd,
      status: 'DRAFT'
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create stocktake');
  }
  
  return await response.json();
}

async function checkExistingStocktake(periodStart, periodEnd) {
  const response = await fetch(
    `/api/stock_tracker/hotel-killarney/stocktakes/` +
    `?period_start=${periodStart}&period_end=${periodEnd}`
  );
  
  if (!response.ok) return null;
  
  const data = await response.json();
  return data.results?.length > 0 ? data.results[0] : null;
}
```

### Option 2: Catch Error and Navigate to Existing

```javascript
try {
  const stocktake = await createStocktake(periodStart, periodEnd);
  navigate(`/stocktakes/${stocktake.id}`);
} catch (error) {
  if (error.message.includes('duplicate key') || 
      error.message.includes('already exists')) {
    // Fetch existing stocktake
    const existing = await checkExistingStocktake(periodStart, periodEnd);
    
    if (existing) {
      toast.warning(
        `Stocktake for ${periodStart} already exists. Opening...`
      );
      navigate(`/stocktakes/${existing.id}`);
    } else {
      toast.error('Failed to create stocktake. Please try again.');
    }
  } else {
    toast.error(error.message);
  }
}
```

---

## React Component Example

```jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

function CreateStocktakeButton({ periodStart, periodEnd }) {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  
  const handleCreate = async () => {
    setLoading(true);
    
    try {
      // Check for existing stocktake first
      const existing = await fetch(
        `/api/stock_tracker/hotel-killarney/stocktakes/` +
        `?period_start=${periodStart}&period_end=${periodEnd}`,
        {
          headers: {
            'Authorization': `Token ${localStorage.getItem('authToken')}`
          }
        }
      ).then(r => r.json());
      
      if (existing.results?.length > 0) {
        // Stocktake already exists
        toast.info('Opening existing stocktake...');
        navigate(`/stocktakes/${existing.results[0].id}`);
        return;
      }
      
      // Create new stocktake
      const response = await fetch(
        '/api/stock_tracker/hotel-killarney/stocktakes/',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${localStorage.getItem('authToken')}`
          },
          body: JSON.stringify({
            period_start: periodStart,
            period_end: periodEnd,
            status: 'DRAFT'
          })
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to create stocktake');
      }
      
      const newStocktake = await response.json();
      toast.success('Stocktake created successfully!');
      navigate(`/stocktakes/${newStocktake.id}`);
      
    } catch (error) {
      console.error('Error creating stocktake:', error);
      toast.error('Failed to create stocktake. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <button 
      onClick={handleCreate}
      disabled={loading}
      className="btn btn-primary"
    >
      {loading ? 'Creating...' : 'Create Stocktake'}
    </button>
  );
}

export default CreateStocktakeButton;
```

---

## API Endpoint for Checking

If you need a dedicated endpoint to check for existing stocktakes:

```
GET /api/stock_tracker/hotel-killarney/stocktakes/
  ?period_start=2025-02-01
  &period_end=2025-02-28
```

**Response (if exists):**
```json
{
  "count": 1,
  "results": [
    {
      "id": 42,
      "period_start": "2025-02-01",
      "period_end": "2025-02-28",
      "status": "DRAFT",
      "created_at": "2025-11-17T14:14:21Z",
      ...
    }
  ]
}
```

**Response (if not exists):**
```json
{
  "count": 0,
  "results": []
}
```

---

## User Experience Flow

### Before Fix (Bad UX):
1. User clicks "Create Stocktake" for February
2. 500 error appears
3. User is confused
4. User tries again → same error
5. 😞

### After Fix (Good UX):
1. User clicks "Create Stocktake" for February
2. System checks if February stocktake exists
3. If exists: "Stocktake already exists. Opening..."
4. Navigate to existing stocktake
5. 😊

---

## Testing

**Test Case 1: Create New Stocktake**
- Period: March 2025 (doesn't exist)
- Expected: Successfully creates and navigates to new stocktake

**Test Case 2: Duplicate Stocktake**
- Period: February 2025 (already exists)
- Expected: Shows message and navigates to existing stocktake

**Test Case 3: Multiple Rapid Clicks**
- Click "Create Stocktake" twice quickly
- Expected: Only one stocktake created, or navigate to existing

---

## Summary

**Root Cause:** Database constraint prevents duplicate stocktakes for same period

**Backend:** No changes needed - constraint is correct

**Frontend Fix:** Check for existing stocktake before creating new one

**Files to Update:**
- Stocktake creation service/hook
- Create stocktake button/form component
- Period list component (if it has create button)

**Estimated Effort:** 30 minutes to 1 hour
