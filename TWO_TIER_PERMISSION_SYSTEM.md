# TWO-TIER PERMISSION SYSTEM - Implementation Guide

## 📅 Date: November 9, 2025

---

## 🎯 Feature Overview

Implemented a **two-tier permission system** for period/stocktake reopening:

1. **Tier 1**: Regular staff with reopen permission (can reopen only)
2. **Tier 2**: Manager-level staff (can reopen AND grant permissions to others)

Only **superusers** can promote staff to Tier 2 (manager level).

---

## 🏗️ Database Changes

### New Field Added: `can_grant_to_others`

**Model**: `PeriodReopenPermission`

```python
can_grant_to_others = models.BooleanField(
    default=False,
    help_text="If True, this staff can grant permissions to other staff (like a manager). Only superusers can set this."
)
```

**Migration**: `0012_add_can_grant_to_others_field.py`

---

## 👥 Permission Levels

### Level 1: Superuser (Owner)
**is_superuser = True**

✅ Can reopen periods/stocktakes  
✅ Can grant reopen permission to staff  
✅ Can set `can_grant_to_others = True` (promote to manager)  
✅ Can revoke permissions  
✅ Can view all permissions  
✅ Full control over everything

---

### Level 2: Manager
**PeriodReopenPermission with can_grant_to_others = True**

✅ Can reopen periods/stocktakes  
✅ Can grant reopen permission to other staff  
✅ Can revoke permissions from other staff  
❌ **CANNOT** set `can_grant_to_others = True` (cannot create other managers)  
❌ **CANNOT** see the manager checkbox (only superusers see it)

**Use Case**: General Manager, Bar Manager, Head of Department

---

### Level 3: Regular Staff with Permission
**PeriodReopenPermission with can_grant_to_others = False**

✅ Can reopen periods/stocktakes  
❌ Cannot grant permissions to others  
❌ Cannot revoke permissions  
❌ Cannot view permissions list  
❌ Cannot see permission management UI

**Use Case**: Assistant Manager, Supervisor, Senior Staff

---

### Level 4: Regular Staff (No Permission)

❌ Cannot reopen periods/stocktakes  
❌ Cannot grant/revoke permissions  
❌ Cannot see reopen buttons

---

## 📡 API Changes

### 1. Grant Permission Endpoint

**POST** `/api/stock_tracker/{hotel}/periods/grant_reopen_permission/`

#### Request Body:
```json
{
  "staff_id": 5,
  "can_grant_to_others": true,    // ← NEW! Only superusers can set to true
  "notes": "General Manager - can manage permissions"
}
```

#### Who Can Access:
- ✅ Superusers
- ✅ Staff with `can_grant_to_others=True` (but cannot set it to true for others)

#### Response:
```json
{
  "success": true,
  "message": "Permission granted successfully",
  "permission": {
    "id": 1,
    "staff_id": 5,
    "staff_name": "John Doe",
    "can_grant_to_others": true,    // ← NEW!
    "is_active": true,
    "granted_at": "2025-11-09T23:00:00Z",
    "granted_by_name": "Nikola Simic"
  }
}
```

---

### 2. List Permissions Endpoint

**GET** `/api/stock_tracker/{hotel}/periods/reopen_permissions/`

#### Response:
```json
[
  {
    "id": 1,
    "staff_id": 5,
    "staff_name": "John Doe",
    "staff_email": "john@hotel.com",
    "can_grant_to_others": true,      // ← NEW! Shows manager level
    "is_active": true,
    "granted_at": "2025-11-09T23:00:00Z",
    "granted_by_name": "Nikola Simic",
    "notes": "General Manager"
  },
  {
    "id": 2,
    "staff_id": 8,
    "staff_name": "Jane Smith",
    "can_grant_to_others": false,     // ← Regular staff
    "is_active": true,
    "granted_at": "2025-11-09T23:05:00Z",
    "granted_by_name": "John Doe",    // Granted by manager
    "notes": "Assistant Manager"
  }
]
```

---

### 3. Period API Enhancement

**GET** `/api/stock_tracker/{hotel}/periods/{id}/`

#### Response:
```json
{
  "id": 7,
  "period_name": "October 2025",
  "can_reopen": true,
  "can_manage_permissions": true    // ← UPDATED! True if superuser OR manager
}
```

**`can_manage_permissions`** now returns `true` for:
- Superusers
- Staff with `can_grant_to_others=True`

---

## 🎨 Frontend Implementation

### 1. Permission List with Manager Checkbox

```jsx
function PermissionList({ permissions, currentUser }) {
  const [selectedPermissions, setSelectedPermissions] = useState({});

  // Only superusers see the checkbox
  const showManagerCheckbox = currentUser.is_superuser;

  async function handleToggleManager(permission) {
    const newValue = !permission.can_grant_to_others;
    
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
          can_grant_to_others: newValue,
          notes: permission.notes
        })
      }
    );

    if (response.ok) {
      // Refresh list
      await loadPermissions();
    }
  }

  return (
    <div className="permissions-list">
      <h3>Staff with Reopen Permission</h3>
      
      <table>
        <thead>
          <tr>
            <th>Staff Name</th>
            <th>Email</th>
            <th>Granted By</th>
            <th>Date</th>
            {showManagerCheckbox && <th>Can Grant to Others</th>}
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {permissions.map(permission => (
            <tr key={permission.id}>
              <td>{permission.staff_name}</td>
              <td>{permission.staff_email}</td>
              <td>{permission.granted_by_name}</td>
              <td>{formatDate(permission.granted_at)}</td>
              
              {/* ONLY SUPERUSERS SEE THIS CHECKBOX */}
              {showManagerCheckbox && (
                <td>
                  <label className="manager-checkbox">
                    <input
                      type="checkbox"
                      checked={permission.can_grant_to_others}
                      onChange={() => handleToggleManager(permission)}
                    />
                    <span className="checkbox-label">
                      Manager (can grant to others)
                    </span>
                  </label>
                  
                  {permission.can_grant_to_others && (
                    <span className="badge badge-manager">👔 Manager</span>
                  )}
                </td>
              )}
              
              <td>
                <button 
                  onClick={() => handleRevoke(permission.staff_id)}
                  className="btn-danger"
                >
                  Revoke
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
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

  // Only superusers see the manager checkbox
  const showManagerCheckbox = currentUser.is_superuser;

  async function handleGrant() {
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
          can_grant_to_others: canGrantToOthers,  // Only sent if superuser
          notes: notes
        })
      }
    );

    if (response.ok) {
      showSuccess('Permission granted successfully');
      resetForm();
    } else {
      const error = await response.json();
      showError(error.error);
    }
  }

  return (
    <div className="grant-permission-form">
      <h3>Grant Reopen Permission</h3>
      
      <div className="form-group">
        <label>Select Staff:</label>
        <StaffSelector 
          value={selectedStaff}
          onChange={setSelectedStaff}
        />
      </div>

      {/* ONLY SUPERUSERS SEE THIS CHECKBOX */}
      {showManagerCheckbox && (
        <div className="form-group manager-option">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={canGrantToOthers}
              onChange={(e) => setCanGrantToOthers(e.target.checked)}
            />
            <span>
              <strong>Manager Level</strong>
              <br/>
              <small>
                This staff member will be able to grant/revoke permissions to other staff.
                Use this for General Managers or Department Heads.
              </small>
            </span>
          </label>
        </div>
      )}

      <div className="form-group">
        <label>Notes:</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="e.g., General Manager, Head of Bar"
        />
      </div>

      <button onClick={handleGrant} className="btn-primary">
        Grant Permission
      </button>
    </div>
  );
}
```

---

### 3. Show/Hide Permission Management UI

```jsx
function PeriodManagementPage({ period }) {
  const [canManage, setCanManage] = useState(false);

  useEffect(() => {
    // period.can_manage_permissions returns true for superusers AND managers
    setCanManage(period.can_manage_permissions);
  }, [period]);

  return (
    <div>
      <h2>{period.period_name}</h2>

      {/* Permission management - only shown to superusers and managers */}
      {canManage && (
        <div className="permission-management-section">
          <h3>Manage Reopen Permissions</h3>
          <PermissionList />
          <GrantPermissionForm />
        </div>
      )}

      {/* Reopen button - shown to anyone with can_reopen */}
      {period.can_reopen && (
        <button onClick={() => handleReopen(period.id)}>
          🔓 Reopen Period
        </button>
      )}
    </div>
  );
}
```

---

## 🔄 Workflow Examples

### Example 1: Superuser Grants Manager Permission

1. **Superuser** logs in
2. Goes to permissions management
3. Selects "John Doe (General Manager)"
4. ✅ **Checks** "Can grant to others" checkbox
5. Clicks "Grant Permission"
6. John is now a **Manager** (Tier 2)

---

### Example 2: Manager Grants Regular Permission

1. **John (Manager)** logs in
2. Goes to permissions management
3. Selects "Jane Smith (Assistant Manager)"
4. ❌ **Does NOT see** "Can grant to others" checkbox (only superusers see it)
5. Clicks "Grant Permission"
6. Jane can now **reopen** but cannot grant to others (Tier 3)

---

### Example 3: Manager Tries to Create Another Manager

1. **John (Manager)** logs in
2. Tries to set `can_grant_to_others: true` via API
3. ❌ **Backend rejects** with error: "Only superusers can grant manager-level permissions"
4. Protection successful ✅

---

## 🔒 Security Rules

### Rule 1: Only Superusers Can Create Managers
```python
if can_grant_to_others and not is_superuser:
    return Response({
        'error': 'Only superusers can grant manager-level permissions'
    }, status=status.HTTP_403_FORBIDDEN)
```

### Rule 2: Managers Can Grant Regular Permissions
```python
if is_superuser or has_can_grant_to_others:
    # Can grant permissions
    pass
else:
    # Denied
    return 403
```

### Rule 3: Checkbox Only Visible to Superusers
```jsx
// Frontend
{currentUser.is_superuser && (
  <input type="checkbox" ... />
)}
```

---

## 📊 Permission Matrix

| Action | Superuser | Manager (Tier 2) | Staff (Tier 3) | No Permission |
|--------|-----------|------------------|----------------|---------------|
| Reopen periods/stocktakes | ✅ | ✅ | ✅ | ❌ |
| View permissions list | ✅ | ✅ | ❌ | ❌ |
| Grant regular permission | ✅ | ✅ | ❌ | ❌ |
| Grant manager permission | ✅ | ❌ | ❌ | ❌ |
| Revoke permissions | ✅ | ✅ | ❌ | ❌ |
| See manager checkbox | ✅ | ❌ | ❌ | ❌ |

---

## 🧪 Testing Checklist

### Backend Tests
- [ ] Superuser can set `can_grant_to_others=True`
- [ ] Manager cannot set `can_grant_to_others=True`
- [ ] Manager can grant regular permissions
- [ ] Manager can revoke permissions
- [ ] Regular staff cannot grant permissions
- [ ] API returns correct `can_manage_permissions` flag

### Frontend Tests
- [ ] Manager checkbox only shows for superusers
- [ ] Manager badge displays for staff with `can_grant_to_others=True`
- [ ] Grant form works for both superusers and managers
- [ ] Superusers can toggle manager checkbox
- [ ] Managers don't see manager checkbox at all

---

## 🚀 Deployment

### 1. Apply Migration
```bash
python manage.py migrate stock_tracker
```

### 2. Commit Changes
```bash
git add stock_tracker/models.py
git add stock_tracker/views.py
git add stock_tracker/stock_serializers.py
git add stock_tracker/migrations/0012_add_can_grant_to_others_field.py
git commit -m "Add two-tier permission system with manager level"
git push heroku main
```

### 3. Update Frontend
- Add manager checkbox (only visible to superusers)
- Update permission list to show manager badge
- Update `can_manage_permissions` check to show UI for managers

---

## ✅ Summary

**What We Built:**
- Two-tier permission system
- Managers can grant permissions (but not create other managers)
- Checkbox only visible to superusers
- Backend security prevents privilege escalation
- API returns who can manage permissions

**Key Security:**
- ✅ Only superusers can create managers
- ✅ Managers cannot promote others to manager level
- ✅ Checkbox hidden from managers in frontend
- ✅ Backend validates all permission changes

**Use Cases:**
- **General Manager**: Gets manager permission, can grant to assistant managers
- **Assistant Manager**: Gets regular permission from manager
- **Supervisor**: Gets regular permission, can only reopen

---

## 📅 Implementation Date
**November 9, 2025**

## 👤 Implemented By
GitHub Copilot

## ✅ Status
**Complete** - Ready for deployment
