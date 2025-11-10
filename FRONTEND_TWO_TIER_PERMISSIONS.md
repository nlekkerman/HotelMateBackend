# FRONTEND GUIDE: Two-Tier Permission System

## 🎯 What Changed

Added a **manager level** permission system. Now there are 3 levels of access:

1. **Superuser** - Full control, can create managers
2. **Manager** - Can grant/revoke permissions (but not create other managers)
3. **Regular Staff** - Can only reopen periods/stocktakes

---

## 📡 API Changes

### 1. New Field: `can_grant_to_others`

All permission objects now include this field:

```json
{
  "id": 1,
  "staff_id": 5,
  "staff_name": "John Doe",
  "staff_email": "john@hotel.com",
  "can_grant_to_others": true,    // ← NEW! True = Manager level
  "is_active": true,
  "granted_at": "2025-11-09T23:00:00Z",
  "granted_by_name": "Nikola Simic",
  "notes": "General Manager"
}
```

---

### 2. Grant Permission API (Updated)

**POST** `/api/stock_tracker/{hotel}/periods/grant_reopen_permission/`

#### New Request Body:
```json
{
  "staff_id": 5,
  "can_grant_to_others": true,    // ← NEW! Only superusers can set to true
  "notes": "General Manager - can manage permissions"
}
```

#### Who Can Use This Endpoint:
- ✅ Superusers (always)
- ✅ Managers with `can_grant_to_others=true` (NEW!)

#### Important Rules:
- Only **superusers** can set `can_grant_to_others: true`
- **Managers** can grant permissions but must set `can_grant_to_others: false`
- If a manager tries to set it to `true`, they get error: `"Only superusers can grant manager-level permissions"`

---

### 3. Enhanced `can_manage_permissions` Flag

**GET** `/api/stock_tracker/{hotel}/periods/{id}/`

```json
{
  "id": 7,
  "period_name": "October 2025",
  "can_reopen": true,
  "can_manage_permissions": true    // ← Now true for superusers AND managers
}
```

**Use this to show/hide permission management UI:**
```javascript
// Show permission management if true
if (period.can_manage_permissions) {
  // User can view and manage permissions
  showPermissionManagement();
}
```

---

## 🎨 Frontend Implementation

### 1. Permission List with Manager Checkbox

**CRITICAL:** The manager checkbox should **ONLY** be visible to superusers.

```jsx
function PermissionList({ permissions, currentUser }) {
  // Only superusers see the manager checkbox
  const isSuperuser = currentUser.is_superuser;

  async function toggleManager(permission) {
    const response = await fetch(
      `/api/stock_tracker/hotel-killarney/periods/grant_reopen_permission/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          staff_id: permission.staff_id,
          can_grant_to_others: !permission.can_grant_to_others,
          notes: permission.notes
        })
      }
    );
    
    if (response.ok) {
      refreshPermissions();
    }
  }

  return (
    <table className="permissions-table">
      <thead>
        <tr>
          <th>Staff Name</th>
          <th>Email</th>
          <th>Granted By</th>
          <th>Date</th>
          {/* ONLY SHOW THIS COLUMN TO SUPERUSERS */}
          {isSuperuser && <th>Manager Level</th>}
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {permissions.map(permission => (
          <tr key={permission.id}>
            <td>
              {permission.staff_name}
              {/* Show manager badge to everyone */}
              {permission.can_grant_to_others && (
                <span className="badge badge-manager">👔 Manager</span>
              )}
            </td>
            <td>{permission.staff_email}</td>
            <td>{permission.granted_by_name}</td>
            <td>{formatDate(permission.granted_at)}</td>
            
            {/* ONLY SUPERUSERS SEE THIS CHECKBOX */}
            {isSuperuser && (
              <td>
                <label className="checkbox-wrapper">
                  <input
                    type="checkbox"
                    checked={permission.can_grant_to_others}
                    onChange={() => toggleManager(permission)}
                  />
                  <span>Can grant to others</span>
                </label>
              </td>
            )}
            
            <td>
              <button onClick={() => revoke(permission.staff_id)}>
                Revoke
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

### 2. Grant Permission Form

```jsx
function GrantPermissionForm({ currentUser }) {
  const [selectedStaff, setSelectedStaff] = useState(null);
  const [canGrantToOthers, setCanGrantToOthers] = useState(false);
  const [notes, setNotes] = useState('');
  
  const isSuperuser = currentUser.is_superuser;

  async function handleSubmit() {
    const response = await fetch(
      `/api/stock_tracker/hotel-killarney/periods/grant_reopen_permission/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          staff_id: selectedStaff.id,
          can_grant_to_others: isSuperuser ? canGrantToOthers : false,
          notes: notes
        })
      }
    );

    if (response.ok) {
      const data = await response.json();
      showSuccess(data.message);
      resetForm();
    } else {
      const error = await response.json();
      showError(error.error);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grant-form">
      <div className="form-group">
        <label>Select Staff</label>
        <StaffSelector 
          value={selectedStaff}
          onChange={setSelectedStaff}
        />
      </div>

      {/* ONLY SUPERUSERS SEE THIS CHECKBOX */}
      {isSuperuser && (
        <div className="form-group manager-option">
          <label className="checkbox-wrapper">
            <input
              type="checkbox"
              checked={canGrantToOthers}
              onChange={(e) => setCanGrantToOthers(e.target.checked)}
            />
            <div className="checkbox-label">
              <strong>Manager Level</strong>
              <p className="help-text">
                This staff member will be able to grant/revoke permissions 
                to other staff. Use this for General Managers or Department Heads.
              </p>
            </div>
          </label>
        </div>
      )}

      <div className="form-group">
        <label>Notes (optional)</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="e.g., General Manager, Head of Bar"
        />
      </div>

      <button type="submit" className="btn-primary">
        Grant Permission
      </button>
    </form>
  );
}
```

---

### 3. Show/Hide Permission Management

Use `can_manage_permissions` to control who sees the permission management UI:

```jsx
function PeriodDetailPage({ periodId }) {
  const [period, setPeriod] = useState(null);

  useEffect(() => {
    fetch(`/api/stock_tracker/hotel-killarney/periods/${periodId}/`)
      .then(r => r.json())
      .then(data => setPeriod(data));
  }, [periodId]);

  if (!period) return <div>Loading...</div>;

  return (
    <div className="period-detail">
      <h2>{period.period_name}</h2>

      {/* Reopen button - shown to anyone with permission */}
      {period.can_reopen && period.is_closed && (
        <button onClick={() => reopenPeriod(periodId)}>
          🔓 Reopen Period & Stocktake
        </button>
      )}

      {/* Permission management - only for superusers and managers */}
      {period.can_manage_permissions && (
        <div className="permission-section">
          <h3>Manage Reopen Permissions</h3>
          <PermissionList />
          <GrantPermissionForm />
        </div>
      )}
    </div>
  );
}
```

---

## 📊 Visual Guide

### Permission List (Superuser View)

```
┌─────────────────────────────────────────────────────────────────┐
│ Staff with Reopen Permission                                    │
├─────────────────────────────────────────────────────────────────┤
│ Name            Email          Granted By     Manager Level     │
├─────────────────────────────────────────────────────────────────┤
│ John Doe 👔     john@h.com     Nikola        ☑ Can grant       │
│ Jane Smith      jane@h.com     John Doe      ☐ Can grant       │
│ Bob Johnson     bob@h.com      John Doe      ☐ Can grant       │
└─────────────────────────────────────────────────────────────────┘
          ↑                                            ↑
   Manager badge                          Only superusers see this
   (visible to all)                                checkbox
```

### Permission List (Manager View)

```
┌─────────────────────────────────────────────────────────────────┐
│ Staff with Reopen Permission                                    │
├─────────────────────────────────────────────────────────────────┤
│ Name            Email          Granted By                       │
├─────────────────────────────────────────────────────────────────┤
│ John Doe 👔     john@h.com     Nikola                           │
│ Jane Smith      jane@h.com     John Doe                         │
│ Bob Johnson     bob@h.com      John Doe                         │
└─────────────────────────────────────────────────────────────────┘
          ↑
   Manager badge still visible,
   but NO checkbox column
```

---

## ⚠️ Critical Rules

### Rule 1: Checkbox Visibility
```javascript
// CORRECT ✅
{currentUser.is_superuser && (
  <input type="checkbox" ... />
)}

// WRONG ❌
{period.can_manage_permissions && (
  <input type="checkbox" ... />  // Managers would see this!
)}
```

### Rule 2: Manager Badge Visibility
```javascript
// Manager badge is visible to EVERYONE
{permission.can_grant_to_others && (
  <span className="badge">👔 Manager</span>
)}
```

### Rule 3: Permission Management UI
```javascript
// Show management UI to superusers AND managers
{period.can_manage_permissions && (
  <PermissionManagementSection />
)}
```

---

## 🧪 Testing Checklist

### As Superuser:
- [ ] Can see "Manager Level" checkbox column
- [ ] Can check/uncheck manager checkbox
- [ ] Can grant manager-level permissions
- [ ] Can grant regular permissions
- [ ] Manager badge displays correctly

### As Manager:
- [ ] Can see permission list
- [ ] **CANNOT** see manager checkbox column
- [ ] Can grant permissions (but they're always regular)
- [ ] Can revoke permissions
- [ ] Manager badge visible on others

### As Regular Staff with Permission:
- [ ] Can see reopen button
- [ ] **CANNOT** see permission management UI
- [ ] **CANNOT** see permission list

### As Regular Staff without Permission:
- [ ] **CANNOT** see reopen button
- [ ] **CANNOT** see any permission UI

---

## 🔄 Migration Path

If you already have permission management UI:

1. Add `is_superuser` check to manager checkbox
2. Update `can_manage_permissions` logic (already done in API)
3. Add manager badge display
4. Update grant form to include checkbox for superusers only

---

## 💻 Quick Copy-Paste Examples

### Check if Superuser:
```javascript
const isSuperuser = currentUser.is_superuser;
```

### Show Manager Checkbox:
```jsx
{isSuperuser && (
  <label>
    <input type="checkbox" checked={permission.can_grant_to_others} />
    Can grant to others
  </label>
)}
```

### Show Manager Badge:
```jsx
{permission.can_grant_to_others && (
  <span className="badge badge-manager">👔 Manager</span>
)}
```

### Grant with Manager Level:
```javascript
fetch('/api/.../grant_reopen_permission/', {
  method: 'POST',
  body: JSON.stringify({
    staff_id: 5,
    can_grant_to_others: isSuperuser ? true : false,  // Only if superuser
    notes: "General Manager"
  })
});
```

---

## ✅ Summary

**What to Implement:**

1. ✅ Add manager checkbox (visible only to superusers)
2. ✅ Add manager badge (visible to everyone)
3. ✅ Update grant form to include `can_grant_to_others`
4. ✅ Use `period.can_manage_permissions` to show/hide UI
5. ✅ Test with superuser, manager, and regular staff accounts

**Key Points:**

- Manager checkbox = superusers only
- Manager badge = visible to everyone
- Permission management UI = superusers + managers
- Backend handles all security validation

---

## 📅 Implementation Date
**November 10, 2025**

## 🚀 Status
**Ready for Frontend Implementation**
