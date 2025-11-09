# FRONTEND GUIDE: Stocktake Reopen

## ✅ IMPLEMENTED (November 2025)

Backend supports reopening approved stocktakes to change them back to DRAFT status.

---

## 🔓 Reopen Stocktake API

### Endpoint
```
POST /api/stock_tracker/{hotel_identifier}/stocktakes/{stocktake_id}/reopen/
```

### Who Can Access?
- ✅ **Superusers** - Always can reopen
- ✅ **Staff with PeriodReopenPermission** - Can reopen stocktakes (same permission as period reopen)

### Authorization
Requires authentication token. Uses the same permission system as period reopening.

---

## 📡 API Request & Response

### Request
```javascript
// No body required
const response = await fetch(
  `/api/stock_tracker/hotel-killarney/stocktakes/8/reopen/`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }
);

const result = await response.json();
```

### Response (Success)
```json
{
  "success": true,
  "message": "Stocktake for 2025-09-01 to 2025-09-30 has been reopened",
  "stocktake": {
    "id": 8,
    "hotel": 1,
    "period_start": "2025-09-01",
    "period_end": "2025-09-30",
    "status": "DRAFT",
    "approved_at": null,
    "approved_by": null,
    "total_lines": 254,
    "created_at": "2025-09-01T10:00:00Z",
    "notes": "September 2025 stocktake"
  }
}
```

### Response (Error - No Permission)
```json
{
  "success": false,
  "error": "You do not have permission to reopen stocktakes"
}
```
**HTTP Status:** `403 Forbidden`

### Response (Error - Already DRAFT)
```json
{
  "success": false,
  "error": "Stocktake is already in DRAFT status"
}
```
**HTTP Status:** `400 Bad Request`

---

## 🔄 What Happens When Reopening?

1. ✅ Stocktake `status` changes from `APPROVED` → `DRAFT`
2. ✅ Stocktake `approved_at` field cleared (set to `null`)
3. ✅ Stocktake `approved_by` field cleared (set to `null`)
4. ✅ Stocktake becomes editable again
5. ✅ Status change is broadcasted to all connected clients (real-time update)

---

## 🎨 Frontend Implementation

### 1. Check if User Can Reopen

```javascript
// Fetch stocktake
const stocktake = await fetch(
  `/api/stock_tracker/hotel-killarney/stocktakes/${stocktakeId}/`
).then(r => r.json());

// Check permission (get from period or user context)
const period = await fetch(
  `/api/stock_tracker/hotel-killarney/periods/${periodId}/`
).then(r => r.json());

// Show reopen button only if approved AND user has permission
if (stocktake.status === 'APPROVED' && period.can_reopen) {
  // Show reopen button
}
```

### 2. Display Reopen Button

```jsx
// React example
{stocktake.status === 'APPROVED' && userCanReopen && (
  <button 
    onClick={() => handleReopenStocktake(stocktake.id)}
    className="btn-warning"
  >
    🔓 Reopen Stocktake
  </button>
)}
```

```vue
<!-- Vue example -->
<button 
  v-if="stocktake.status === 'APPROVED' && userCanReopen"
  @click="handleReopenStocktake(stocktake.id)"
  class="btn-warning"
>
  🔓 Reopen Stocktake
</button>
```

### 3. Reopen Handler with Confirmation

```javascript
async function handleReopenStocktake(stocktakeId) {
  // Show confirmation dialog
  const confirmed = confirm(
    '⚠️ Warning: Reopening this stocktake will change its status from APPROVED to DRAFT.\n\n' +
    'This will:\n' +
    '- Clear approval timestamp\n' +
    '- Make the stocktake editable again\n' +
    '- Allow modifications to counted values\n\n' +
    'Do you want to continue?'
  );
  
  if (!confirmed) return;
  
  try {
    const response = await fetch(
      `/api/stock_tracker/hotel-killarney/stocktakes/${stocktakeId}/reopen/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      // Show success message
      showSuccessNotification(data.message);
      
      // Refresh stocktake data
      await refreshStocktakeData();
      
      // Optional: Navigate or update UI
      updateStocktakeStatus('DRAFT');
      
    } else {
      // Handle error
      showErrorNotification(data.error || 'Failed to reopen stocktake');
    }
    
  } catch (error) {
    console.error('Error reopening stocktake:', error);
    showErrorNotification('Network error: Failed to reopen stocktake');
  }
}
```

### 4. Display Stocktake Status

```javascript
// Status badge component
function StocktakeStatusBadge({ stocktake }) {
  const statusConfig = {
    'DRAFT': {
      color: 'orange',
      icon: '📝',
      label: 'Draft',
      description: 'Stocktake is being edited'
    },
    'APPROVED': {
      color: 'green',
      icon: '✅',
      label: 'Approved',
      description: 'Stocktake is locked and finalized'
    }
  };
  
  const config = statusConfig[stocktake.status];
  
  return (
    <div className={`badge badge-${config.color}`}>
      <span>{config.icon}</span>
      <span>{config.label}</span>
      {stocktake.approved_at && (
        <small>
          Approved: {formatDate(stocktake.approved_at)}
        </small>
      )}
    </div>
  );
}
```

### 5. Complete Example with State Management

```javascript
// React component example
import { useState, useEffect } from 'react';

function StocktakeDetail({ stocktakeId }) {
  const [stocktake, setStocktake] = useState(null);
  const [userCanReopen, setUserCanReopen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStocktakeData();
  }, [stocktakeId]);

  async function loadStocktakeData() {
    try {
      // Fetch stocktake
      const stocktakeData = await fetch(
        `/api/stock_tracker/hotel-killarney/stocktakes/${stocktakeId}/`
      ).then(r => r.json());
      
      setStocktake(stocktakeData);
      
      // Check permissions from period
      const period = await fetch(
        `/api/stock_tracker/hotel-killarney/periods/${stocktakeData.period_id}/`
      ).then(r => r.json());
      
      setUserCanReopen(period.can_reopen);
      
    } catch (error) {
      console.error('Error loading stocktake:', error);
    }
  }

  async function handleReopen() {
    const confirmed = confirm(
      'Are you sure you want to reopen this stocktake?\n\n' +
      'It will change from APPROVED to DRAFT.'
    );
    
    if (!confirmed) return;
    
    setLoading(true);
    
    try {
      const response = await fetch(
        `/api/stock_tracker/hotel-killarney/stocktakes/${stocktakeId}/reopen/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      const data = await response.json();
      
      if (data.success) {
        alert(data.message);
        await loadStocktakeData(); // Refresh
      } else {
        alert(`Error: ${data.error}`);
      }
      
    } catch (error) {
      alert('Failed to reopen stocktake');
    } finally {
      setLoading(false);
    }
  }

  if (!stocktake) return <div>Loading...</div>;

  return (
    <div className="stocktake-detail">
      <h2>Stocktake: {stocktake.period_start} to {stocktake.period_end}</h2>
      
      <div className="status-section">
        <span className={`badge badge-${stocktake.status.toLowerCase()}`}>
          {stocktake.status}
        </span>
        
        {stocktake.approved_at && (
          <small>Approved: {formatDate(stocktake.approved_at)}</small>
        )}
      </div>
      
      <div className="actions">
        {stocktake.status === 'APPROVED' && userCanReopen && (
          <button 
            onClick={handleReopen}
            disabled={loading}
            className="btn-warning"
          >
            {loading ? '⏳ Reopening...' : '🔓 Reopen Stocktake'}
          </button>
        )}
      </div>
      
      {/* Rest of stocktake content */}
    </div>
  );
}
```

---

## 🔒 Permission System

Stocktake reopen uses the **same permission system** as period reopen:

| User Type | Can Reopen Stocktakes? |
|-----------|----------------------|
| **Superuser** | ✅ Always |
| **Staff with PeriodReopenPermission** | ✅ Yes |
| **Regular staff** | ❌ No |

### How to Check Permission

```javascript
// Method 1: Check from period
const period = await fetch(`/api/periods/${periodId}/`).then(r => r.json());
const canReopen = period.can_reopen;

// Method 2: Check from user context
const currentUser = getCurrentUser();
const canReopen = currentUser.is_superuser || currentUser.has_reopen_permission;
```

---

## ⚠️ Important Notes

1. **APPROVED → DRAFT Only**: Can only reopen stocktakes that are in APPROVED status
2. **Same Permissions**: Uses PeriodReopenPermission (same as period reopen)
3. **Real-time Broadcast**: Status change is automatically broadcasted to all connected users
4. **Reversible**: Can approve again after reopening
5. **No Data Loss**: Reopening preserves all counted values and stocktake lines
6. **Audit Trail**: While approved_at/approved_by are cleared, create/update timestamps remain

---

## 🎯 Use Cases

### When to Reopen Stocktake:

1. **Correction Needed**: Found counting errors after approval
2. **Missing Items**: Need to add items that were missed
3. **Wrong Values**: Incorrect values were entered
4. **Period Reopened**: When period is reopened, stocktake should be reopened too (automatic)
5. **Recalculation**: Need to recalculate costs or values

### Workflow:

```
1. Stocktake is APPROVED
   ↓
2. User clicks "Reopen Stocktake"
   ↓
3. Confirmation dialog appears
   ↓
4. User confirms
   ↓
5. Status changes to DRAFT
   ↓
6. User makes corrections
   ↓
7. User approves again
```

---

## 📊 Related Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /stocktakes/{id}/` | Get stocktake details |
| `POST /stocktakes/{id}/reopen/` | Reopen approved stocktake |
| `POST /stocktakes/{id}/approve/` | Approve draft stocktake |
| `GET /periods/{id}/` | Get period with can_reopen flag |
| `POST /periods/{id}/reopen/` | Reopen period (also reopens stocktake) |

---

## 🧪 Testing Checklist

### Frontend Tests
- [ ] Reopen button only shows for APPROVED stocktakes
- [ ] Reopen button only shows if user has permission
- [ ] Confirmation dialog displays before reopen
- [ ] Success message shows after reopen
- [ ] Stocktake status changes to DRAFT in UI
- [ ] Approved timestamp disappears
- [ ] Stocktake becomes editable
- [ ] Error handling works (no permission, already DRAFT)
- [ ] Real-time update received by other users

### Backend Tests
- [ ] Reopen endpoint returns 200 for authorized users
- [ ] Returns 403 for unauthorized users
- [ ] Returns 400 if already DRAFT
- [ ] Status changes from APPROVED to DRAFT
- [ ] approved_at and approved_by are cleared
- [ ] Broadcast notification sent

---

## 🚀 Quick Reference

### Minimal Implementation

```javascript
// 1. Show button
if (stocktake.status === 'APPROVED' && userCanReopen) {
  <button onClick={() => reopenStocktake(stocktake.id)}>Reopen</button>
}

// 2. Reopen function
async function reopenStocktake(id) {
  if (!confirm('Reopen stocktake?')) return;
  
  await fetch(`/api/stock_tracker/hotel-killarney/stocktakes/${id}/reopen/`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  refreshStocktake();
}
```

---

## 📅 Last Updated
**November 9, 2025** - Stocktake reopen feature implementation
