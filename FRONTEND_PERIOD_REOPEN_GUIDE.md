# FRONTEND GUIDE: Period Reopen & Permission Management

## ✅ IMPLEMENTED (November 2025)

Backend now supports:
1. **Reopening closed periods** (with permission check)
2. **Managing who can reopen periods** (superuser only)
3. **Automatic stocktake status change** (APPROVED → DRAFT when reopening)

---

## 🔓 Reopen Period API

### Endpoint
```
POST /api/stock_tracker/{hotel_identifier}/periods/{period_id}/reopen/
```

### Who Can Access?
- ✅ **Superusers** - Always can reopen
- ✅ **Staff with permission** - Must be granted by superuser

### Request
```javascript
// No body required
const response = await fetch(
  `/api/stock_tracker/hotel-killarney/periods/8/reopen/`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }
);
```

### Response (Success)
```json
{
  "success": true,
  "message": "Period \"September 2025\" has been reopened and stocktake changed to DRAFT",
  "stocktake_updated": true,
  "period": {
    "id": 8,
    "period_name": "September 2025",
    "is_closed": false,
    "closed_at": null,
    "closed_by": null,
    "reopened_at": "2025-11-09T21:00:00Z",
    "reopened_by": 35,
    "can_reopen": true,
    "can_manage_permissions": true,
    "stocktake": {
      "id": 8,
      "status": "DRAFT",
      "total_lines": 254
    }
  }
}
```

### Response (Error - No Permission)
```json
{
  "success": false,
  "error": "You do not have permission to reopen periods"
}
```
**HTTP Status:** `403 Forbidden`

### Response (Error - Already Open)
```json
{
  "success": false,
  "error": "Period is already open"
}
```
**HTTP Status:** `400 Bad Request`

### What Happens When Reopening?
1. ✅ Period `is_closed` set to `false`
2. ✅ Period `closed_at` and `closed_by` cleared
3. ✅ Period `reopened_at` set to current timestamp
4. ✅ Period `reopened_by` set to staff who reopened it
5. ✅ Related stocktake status changed from `APPROVED` → `DRAFT`
6. ✅ Stocktake `approved_at` and `approved_by` cleared

---

## 👥 Permission Management APIs

### 1. Check User Permissions (in Period Response)

Every period now includes permission flags:

```javascript
const period = await fetch('/api/periods/8/').then(r => r.json());

// Check if current user can reopen
if (period.can_reopen) {
  // Show "Reopen Period" button
}

// Check if current user can manage permissions
if (period.can_manage_permissions) {
  // Show "Manage Permissions" button (superuser only)
}
```

### 2. List Staff with Reopen Permission

**Endpoint:** `GET /api/stock_tracker/{hotel_identifier}/periods/reopen_permissions/`

**Access:** Superusers only

```javascript
// Get list of staff who can reopen periods
const response = await fetch(
  '/api/stock_tracker/hotel-killarney/periods/reopen_permissions/',
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);

const permissions = await response.json();
```

**Response:**
```json
[
  {
    "id": 1,
    "hotel": 1,
    "staff": 5,
    "staff_id": 5,
    "staff_name": "John Manager",
    "staff_email": "john@hotel.com",
    "granted_by": 1,
    "granted_by_name": "Admin User",
    "granted_at": "2025-11-09T20:30:00Z",
    "is_active": true,
    "notes": "Head manager - needs reopen access"
  },
  {
    "id": 2,
    "staff_id": 8,
    "staff_name": "Sarah Supervisor",
    "staff_email": "sarah@hotel.com",
    "is_active": false,
    "notes": "Permission revoked"
  }
]
```

### 3. Grant Reopen Permission to Staff

**Endpoint:** `POST /api/stock_tracker/{hotel_identifier}/periods/grant_reopen_permission/`

**Access:** Superusers only

```javascript
// Grant permission to staff member
const response = await fetch(
  '/api/stock_tracker/hotel-killarney/periods/grant_reopen_permission/',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      staff_id: 5,
      notes: "Head manager - needs reopen access"
    })
  }
);

const result = await response.json();
```

**Request Body:**
```json
{
  "staff_id": 5,
  "notes": "Optional notes about why permission was granted"
}
```

**Response (Success - New Permission):**
```json
{
  "success": true,
  "message": "Permission granted successfully",
  "permission": {
    "id": 1,
    "staff_id": 5,
    "staff_name": "John Manager",
    "staff_email": "john@hotel.com",
    "is_active": true,
    "granted_at": "2025-11-09T20:30:00Z"
  }
}
```
**HTTP Status:** `201 Created`

**Response (Permission Already Exists):**
```json
{
  "success": true,
  "message": "Permission already exists"
}
```
**HTTP Status:** `200 OK`

**Response (Permission Reactivated):**
```json
{
  "success": true,
  "message": "Permission reactivated"
}
```
**HTTP Status:** `200 OK`

### 4. Revoke Reopen Permission from Staff

**Endpoint:** `POST /api/stock_tracker/{hotel_identifier}/periods/revoke_reopen_permission/`

**Access:** Superusers only

```javascript
// Revoke permission from staff member
const response = await fetch(
  '/api/stock_tracker/hotel-killarney/periods/revoke_reopen_permission/',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      staff_id: 5
    })
  }
);

const result = await response.json();
```

**Request Body:**
```json
{
  "staff_id": 5
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Permission revoked successfully"
}
```
**HTTP Status:** `200 OK`

**Response (Error - Not Found):**
```json
{
  "error": "Permission not found for this staff member"
}
```
**HTTP Status:** `404 Not Found`

---

## 🎨 Frontend Implementation Guide

### Show Reopen Button (Conditionally)

```javascript
// In your Period detail view
const period = await fetchPeriod(periodId);

// Only show button if period is closed AND user can reopen
if (period.is_closed && period.can_reopen) {
  return (
    <button onClick={handleReopenPeriod}>
      🔓 Reopen Period
    </button>
  );
}
```

### Reopen Period Handler

```javascript
async function handleReopenPeriod(periodId) {
  // Show confirmation dialog
  const confirmed = await confirm(
    'Are you sure you want to reopen this period? ' +
    'The stocktake will be changed to DRAFT.'
  );
  
  if (!confirmed) return;
  
  try {
    const response = await fetch(
      `/api/stock_tracker/hotel-killarney/periods/${periodId}/reopen/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const data = await response.json();
    
    if (data.success) {
      // Show success message
      alert(data.message);
      
      // Refresh period data
      await refreshPeriod();
      
      // Show what changed
      if (data.stocktake_updated) {
        console.log('Stocktake changed to DRAFT');
      }
    } else {
      alert(`Error: ${data.error}`);
    }
  } catch (error) {
    alert('Failed to reopen period');
    console.error(error);
  }
}
```

### Manage Permissions Modal (Superuser Only)

```javascript
// In your Period list/detail view
if (userIsSuperuser) {
  return (
    <button onClick={openPermissionsModal}>
      👥 Manage Reopen Permissions
    </button>
  );
}

async function openPermissionsModal() {
  // 1. Fetch current permissions
  const permissions = await fetch(
    '/api/stock_tracker/hotel-killarney/periods/reopen_permissions/'
  ).then(r => r.json());
  
  // 2. Fetch all staff
  const allStaff = await fetch(
    '/api/staff/hotel-killarney/'
  ).then(r => r.json());
  
  // 3. Show modal with:
  //    - List of staff with permission (with revoke button)
  //    - Dropdown to select new staff (with grant button)
  
  showModal({
    title: 'Manage Period Reopen Permissions',
    permissions: permissions,
    allStaff: allStaff
  });
}
```

### Grant Permission in Modal

```javascript
async function grantPermission(staffId, notes = '') {
  const response = await fetch(
    '/api/stock_tracker/hotel-killarney/periods/grant_reopen_permission/',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        staff_id: staffId,
        notes: notes
      })
    }
  );
  
  const data = await response.json();
  
  if (data.success) {
    alert(data.message);
    // Refresh permissions list
    await refreshPermissions();
  } else {
    alert(`Error: ${data.error}`);
  }
}
```

### Revoke Permission in Modal

```javascript
async function revokePermission(staffId) {
  const confirmed = await confirm(
    'Are you sure you want to revoke this permission?'
  );
  
  if (!confirmed) return;
  
  const response = await fetch(
    '/api/stock_tracker/hotel-killarney/periods/revoke_reopen_permission/',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        staff_id: staffId
      })
    }
  );
  
  const data = await response.json();
  
  if (data.success) {
    alert(data.message);
    // Refresh permissions list
    await refreshPermissions();
  } else {
    alert(`Error: ${data.error}`);
  }
}
```

---

## 🔒 Permission Logic Summary

| User Type | Can Reopen Periods? | Can Manage Permissions? |
|-----------|-------------------|------------------------|
| **Superuser** | ✅ Always | ✅ Always |
| **Staff with permission** | ✅ Yes | ❌ No |
| **Regular staff** | ❌ No | ❌ No |

### How Permissions Work

1. **By default**, only superusers can reopen periods
2. **Superusers** can grant permission to specific staff members
3. **Staff with permission** can reopen any period in their hotel
4. **Permissions are hotel-specific** - staff can have permission in one hotel but not another
5. **Permissions can be revoked** by setting `is_active` to `false`

---

## 📋 Complete Workflow Example

### Scenario: Manager needs to reopen September 2025

```javascript
// 1. Admin grants permission to manager (one-time setup)
await grantPermission(managerId, "Head manager needs reopen access");

// 2. Manager logs in and views September period
const period = await fetch('/api/periods/8/').then(r => r.json());
console.log(period.can_reopen); // true

// 3. Manager clicks "Reopen Period" button
await fetch('/api/stock_tracker/hotel-killarney/periods/8/reopen/', {
  method: 'POST'
});

// 4. System automatically:
//    - Changes period.is_closed to false
//    - Changes stocktake.status to DRAFT
//    - Clears approval timestamps

// 5. Manager can now edit stocktake and period data
```

---

## ⚠️ Important Notes

1. **Reopening clears stocktake approval** - The stocktake will change from APPROVED to DRAFT automatically
2. **Permissions are hotel-specific** - Staff need permission for each hotel separately
3. **Only superusers manage permissions** - Regular staff cannot grant/revoke permissions
4. **Period must be closed to reopen** - Cannot reopen an already open period
5. **Authorization required** - All endpoints require authentication token

---

## 🎯 Quick Reference

| Action | Endpoint | Method | Access |
|--------|----------|--------|--------|
| Check permissions | Period detail | GET | All authenticated |
| Reopen period | `/periods/{id}/reopen/` | POST | Superuser or permitted staff |
| List permissions | `/periods/reopen_permissions/` | GET | Superuser only |
| Grant permission | `/periods/grant_reopen_permission/` | POST | Superuser only |
| Revoke permission | `/periods/revoke_reopen_permission/` | POST | Superuser only |

---

---

## � Period & Stocktake Serializer Fields

### Period Response Fields (StockPeriodSerializer)

Every period response now includes these fields:

```javascript
{
  // Basic info
  "id": 8,
  "hotel": 1,
  "period_name": "September 2025",
  "period_type": "MONTHLY",
  "start_date": "2025-09-01",
  "end_date": "2025-09-30",
  "year": 2025,
  "month": 9,
  
  // Status tracking
  "is_closed": false,
  "closed_at": "2025-10-01T10:00:00Z",  // When closed
  "closed_by": 12,                       // Staff ID who closed
  "reopened_at": "2025-11-09T21:00:00Z", // When last reopened
  "reopened_by": 35,                     // Staff ID who reopened
  
  // Manual values
  "manual_sales_amount": "51207.00",
  "manual_purchases_amount": "18265.03",
  
  // Stocktake relationship
  "stocktake_id": 8,
  "stocktake": {
    "id": 8,
    "status": "DRAFT",
    "total_lines": 254,
    "lines_counted": 220,
    "lines_at_zero": 34,
    "total_cogs": 18265.03,
    "total_revenue": 51207.00,
    "gross_profit_percentage": 64.33,
    "pour_cost_percentage": 35.67,
    "approved_at": null,
    "notes": ""
  },
  
  // Permission flags (for current user)
  "can_reopen": true,
  "can_manage_permissions": true
}
```

### Key Fields for Frontend UI

**Display Period Status:**
```javascript
if (period.is_closed) {
  status = "Closed";
  if (period.closed_by && period.closed_at) {
    details = `Closed by Staff #${period.closed_by} on ${formatDate(period.closed_at)}`;
  }
  if (period.reopened_at) {
    details += `\nLast reopened by Staff #${period.reopened_by} on ${formatDate(period.reopened_at)}`;
  }
} else {
  status = "Open";
}
```

**Display Stocktake Status:**
```javascript
if (period.stocktake) {
  statusBadge = period.stocktake.status; // "DRAFT" or "APPROVED"
  itemsSummary = `${period.stocktake.lines_counted}/${period.stocktake.total_lines} items counted`;
  financials = {
    cogs: period.stocktake.total_cogs,
    revenue: period.stocktake.total_revenue,
    gp: period.stocktake.gross_profit_percentage
  };
}
```

---

## 📅 Last Updated
**November 9, 2025** - Added reopen tracking (reopened_at, reopened_by)
