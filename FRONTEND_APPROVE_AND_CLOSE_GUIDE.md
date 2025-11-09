# FRONTEND GUIDE: Approve & Close Combined Action

## ✅ IMPLEMENTED (November 2025)

New combined endpoint that **approves stocktake AND closes period in ONE button click**.

---

## 🎯 Purpose

Users need one button to:
1. ✅ Approve the stocktake (finalize counting)
2. ✅ Close the period (lock it)

This is the **normal workflow** when finishing a period.

---

## 📡 API Endpoint

### Approve & Close (Combined Action)

```
POST /api/stock_tracker/{hotel_identifier}/periods/{period_id}/approve-and-close/
```

#### Order of Operations:
1. **First**: Approve stocktake (DRAFT → APPROVED)
2. **Then**: Close period (OPEN → CLOSED)

This ensures stocktake is finalized before period is locked.

---

## 🔧 Request & Response

### Request
```javascript
const response = await fetch(
  `/api/stock_tracker/hotel-killarney/periods/7/approve-and-close/`,
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
  "message": "Stocktake approved and period \"October 2025\" closed successfully",
  "period": {
    "id": 7,
    "period_name": "October 2025",
    "start_date": "2025-10-01",
    "end_date": "2025-10-31",
    "is_closed": true,
    "closed_at": "2025-11-09T23:00:00Z",
    "closed_by": "Nikola",
    "reopened_at": null,
    "reopened_by": null,
    "can_reopen": true,
    "can_manage_permissions": true
  },
  "stocktake": {
    "id": 5,
    "status": "APPROVED",
    "approved_at": "2025-11-09T23:00:00Z",
    "approved_by": "nikola"
  }
}
```

### Response (Error - Already Closed)
```json
{
  "success": false,
  "error": "Period is already closed"
}
```
**HTTP Status:** `400 Bad Request`

### Response (Error - No Stocktake)
```json
{
  "success": false,
  "error": "No stocktake found for this period"
}
```
**HTTP Status:** `404 Not Found`

### Response (Error - No Staff Profile)
```json
{
  "success": false,
  "error": "User must be associated with a staff profile"
}
```
**HTTP Status:** `403 Forbidden`

---

## 🔄 Reopen (Combined Action)

The existing reopen endpoint already does both actions:

```
POST /api/stock_tracker/{hotel_identifier}/periods/{period_id}/reopen/
```

#### Order of Operations:
1. **First**: Reopen period (CLOSED → OPEN)
2. **Then**: Reopen stocktake (APPROVED → DRAFT)

This makes the period editable and stocktake modifiable.

---

## 🎨 Frontend Implementation

### Single Button for Close

```jsx
// React example
function PeriodActions({ period, stocktake }) {
  const [loading, setLoading] = useState(false);

  async function handleApproveAndClose() {
    const confirmed = confirm(
      `⚠️ This will:\n` +
      `1. Approve the stocktake (lock counting)\n` +
      `2. Close the period "${period.period_name}"\n\n` +
      `Are you sure?`
    );
    
    if (!confirmed) return;
    
    setLoading(true);
    
    try {
      const response = await fetch(
        `/api/stock_tracker/hotel-killarney/periods/${period.id}/approve-and-close/`,
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
        showSuccessNotification(data.message);
        // Refresh data
        await refreshPeriodData();
      } else {
        showErrorNotification(data.error);
      }
      
    } catch (error) {
      showErrorNotification('Failed to approve and close');
    } finally {
      setLoading(false);
    }
  }

  // Show button only if period is OPEN and stocktake is DRAFT
  if (!period.is_closed && stocktake.status === 'DRAFT') {
    return (
      <button 
        onClick={handleApproveAndClose}
        disabled={loading}
        className="btn-success"
      >
        {loading ? '⏳ Processing...' : '✅ Approve & Close Period'}
      </button>
    );
  }

  return null;
}
```

### Single Button for Reopen

```jsx
// React example
function PeriodReopenButton({ period, userCanReopen }) {
  const [loading, setLoading] = useState(false);

  async function handleReopen() {
    const confirmed = confirm(
      `⚠️ This will:\n` +
      `1. Reopen the period "${period.period_name}"\n` +
      `2. Change stocktake from APPROVED to DRAFT\n\n` +
      `Are you sure?`
    );
    
    if (!confirmed) return;
    
    setLoading(true);
    
    try {
      const response = await fetch(
        `/api/stock_tracker/hotel-killarney/periods/${period.id}/reopen/`,
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
        showSuccessNotification(data.message);
        await refreshPeriodData();
      } else {
        showErrorNotification(data.error);
      }
      
    } catch (error) {
      showErrorNotification('Failed to reopen');
    } finally {
      setLoading(false);
    }
  }

  // Show button only if period is CLOSED and user has permission
  if (period.is_closed && userCanReopen) {
    return (
      <button 
        onClick={handleReopen}
        disabled={loading}
        className="btn-warning"
      >
        {loading ? '⏳ Reopening...' : '🔓 Reopen Period & Stocktake'}
      </button>
    );
  }

  return null;
}
```

### Complete UI Example

```jsx
function PeriodManagement({ periodId }) {
  const [period, setPeriod] = useState(null);
  const [stocktake, setStocktake] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [periodId]);

  async function loadData() {
    setLoading(true);
    try {
      // Fetch period (includes can_reopen flag)
      const periodData = await fetch(
        `/api/stock_tracker/hotel-killarney/periods/${periodId}/`
      ).then(r => r.json());
      
      setPeriod(periodData);
      setStocktake(periodData.stocktake);
      
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div>Loading...</div>;
  if (!period) return <div>Period not found</div>;

  return (
    <div className="period-management">
      <h2>{period.period_name}</h2>
      
      <div className="status-section">
        <div className="period-status">
          <span className={`badge ${period.is_closed ? 'closed' : 'open'}`}>
            {period.is_closed ? '🔒 CLOSED' : '🔓 OPEN'}
          </span>
          {period.closed_at && (
            <small>Closed: {formatDate(period.closed_at)}</small>
          )}
        </div>
        
        <div className="stocktake-status">
          <span className={`badge ${stocktake.status.toLowerCase()}`}>
            📦 {stocktake.status}
          </span>
          {stocktake.approved_at && (
            <small>Approved: {formatDate(stocktake.approved_at)}</small>
          )}
        </div>
      </div>

      <div className="actions">
        {/* Show "Approve & Close" button if OPEN */}
        {!period.is_closed && stocktake.status === 'DRAFT' && (
          <ApproveAndCloseButton 
            period={period} 
            stocktake={stocktake}
            onSuccess={loadData}
          />
        )}

        {/* Show "Reopen" button if CLOSED and has permission */}
        {period.is_closed && period.can_reopen && (
          <ReopenButton 
            period={period}
            onSuccess={loadData}
          />
        )}
      </div>
    </div>
  );
}
```

---

## 📊 Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  NORMAL WORKFLOW: Close Period                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. User finishes counting stocktake (DRAFT)                │
│  2. User clicks "Approve & Close Period" button             │
│  3. Confirmation dialog appears                              │
│  4. User confirms                                            │
│                                                              │
│  ⬇️  Backend executes in order:                              │
│                                                              │
│  STEP 1: Approve Stocktake                                  │
│    - status: DRAFT → APPROVED                               │
│    - approved_at: set timestamp                             │
│    - approved_by: set staff                                 │
│    - broadcast status change                                │
│                                                              │
│  STEP 2: Close Period                                       │
│    - is_closed: False → True                                │
│    - closed_at: set timestamp                               │
│    - closed_by: set staff                                   │
│                                                              │
│  5. Success message displayed                                │
│  6. UI updates to show CLOSED status                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  CORRECTION WORKFLOW: Reopen Period                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Period is CLOSED, Stocktake is APPROVED                 │
│  2. User finds error, needs to correct                      │
│  3. User clicks "Reopen Period & Stocktake" button          │
│  4. Confirmation dialog appears                              │
│  5. User confirms                                            │
│                                                              │
│  ⬇️  Backend executes in order:                              │
│                                                              │
│  STEP 1: Reopen Period                                      │
│    - is_closed: True → False                                │
│    - reopened_at: set timestamp                             │
│    - reopened_by: set staff                                 │
│    - KEEP closed_at and closed_by (audit trail)             │
│                                                              │
│  STEP 2: Reopen Stocktake                                   │
│    - status: APPROVED → DRAFT                               │
│    - approved_at: cleared (null)                            │
│    - approved_by: cleared (null)                            │
│    - broadcast status change                                │
│                                                              │
│  6. User makes corrections                                   │
│  7. User clicks "Approve & Close Period" again              │
│  8. Cycle repeats                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Benefits

1. **Simpler UX**: One button instead of two separate actions
2. **Correct Order**: Backend ensures proper sequence (approve → close, reopen period → reopen stocktake)
3. **Atomic Operation**: Both actions succeed or fail together
4. **Real-time Updates**: Broadcasts notify all connected users
5. **Audit Trail**: Keeps track of who closed/reopened and when

---

## ⚠️ Important Notes

1. **Approve & Close**: Can only be done if period is OPEN
2. **Reopen**: Can only be done if period is CLOSED and user has permission
3. **Audit Trail**: `closed_at` and `closed_by` are kept when reopening (not cleared)
4. **Permission Check**: Same permission system applies (superuser or PeriodReopenPermission)
5. **Broadcasting**: Real-time updates sent to all connected clients

---

## 🧪 Testing Checklist

### Approve & Close
- [ ] Button shows only when period is OPEN and stocktake is DRAFT
- [ ] Confirmation dialog appears
- [ ] Stocktake changes to APPROVED
- [ ] Period changes to CLOSED
- [ ] Timestamps recorded correctly
- [ ] Success message displayed
- [ ] UI updates to show new status
- [ ] Error handling works (already closed, no stocktake)

### Reopen
- [ ] Button shows only when period is CLOSED and user has permission
- [ ] Confirmation dialog appears
- [ ] Period changes to OPEN
- [ ] Stocktake changes to DRAFT
- [ ] Audit trail preserved (closed_at/closed_by remain)
- [ ] reopened_at and reopened_by recorded
- [ ] Success message displayed
- [ ] UI updates to show new status

---

## 📅 Last Updated
**November 9, 2025** - Combined approve & close endpoint implementation
