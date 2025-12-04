# Finalized Roster Instructions

## Backend API Endpoints

### 1. Fetch Finalized Periods
```http
GET http://localhost:8000/api/staff/hotel/{hotel_slug}/attendance/roster-periods/?is_finalized=true
```
**Frontend should use:** `/api/staff/hotel/{hotel_slug}/attendance/roster-periods/?is_finalized=true`
**Note:** Frontend dev server should proxy API calls to Django backend (port 8000)
**Response:**
```json
[
  {
    "id": 12,
    "title": "Week of Nov 25",
    "start_date": "2025-11-25",
    "end_date": "2025-12-01",
    "is_finalized": true,
    "finalized_by": 45,
    "finalized_by_name": "Manager Smith",
    "finalized_at": "2025-11-30T15:30:00Z"
  }
]
```

### 2. Check Finalization Status
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-periods/{period_id}/finalization-status/
```
**Response (finalized):**
```json
{
  "is_finalized": true,
  "finalized_at": "2025-11-30T15:30:00Z",
  "finalized_by": "Manager Smith",
  "can_unfinalize": false
}
```

### 3. Finalize a Period
```http
POST /api/staff/hotel/{hotel_slug}/attendance/roster-periods/{period_id}/finalize/
```
**Body:**
```json
{
  "confirm": true,
  "force": false
}
```

### 4. Get Finalized Rosters by Department
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-periods/{period_id}/finalized-rosters/
GET /api/staff/hotel/{hotel_slug}/attendance/roster-periods/{period_id}/finalized-rosters/?department=housekeeping
```

## Frontend Setup Required

### Vite Proxy Configuration
Add this to your `vite.config.js`:
```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
```
**Response:**
```json
{
  "period": {
    "id": 12,
    "title": "Week of Nov 25",
    "is_finalized": true,
    "finalized_by": "Manager Smith",
    "finalized_at": "2025-11-30T15:30:00Z"
  },
  "rosters": [...],
  "count": 45
}
```

## Frontend Implementation

### 1. Disable Editing for Finalized Rosters
When `period.is_finalized === true`:
- **Disable ALL buttons** in roster grid
- **Show read-only mode**
- **Display finalization info**: "Finalized by {finalized_by_name} on {finalized_at}"

### 2. Roster Grid Behavior
```javascript
// Check if period is finalized
const isFinalized = period.is_finalized;

// Disable all editing buttons
const editButtonsDisabled = isFinalized;
const addShiftDisabled = isFinalized;
const deleteShiftDisabled = isFinalized;
const bulkSaveDisabled = isFinalized;

// Show finalization status
if (isFinalized) {
  showFinalizationBanner(period.finalized_by_name, period.finalized_at);
}
```

### 3. Finalization Process
1. **End of week**: Manager clicks "Finalize Period"
2. **Validation**: Backend checks for unresolved issues
3. **Success**: All roster editing becomes disabled
4. **Frontend**: Switch to read-only mode, show finalization info

### 4. Key Frontend Rules
- ❌ **NO editing** of shifts in finalized periods
- ❌ **NO adding** new shifts to finalized periods  
- ❌ **NO deleting** shifts from finalized periods
- ❌ **NO bulk operations** on finalized periods
- ✅ **READ-ONLY** access to finalized roster data
- ✅ **Display finalization info** (who/when finalized)

## Usage Scenario
- **Weekly process**: At end of week, managers finalize the roster
- **Lock-down**: Once finalized, NO changes allowed
- **Audit trail**: Track who finalized and when
- **Department filtering**: View finalized rosters by department