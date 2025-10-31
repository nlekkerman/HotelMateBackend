# Frontend Department/Role Fetching - Debugging Guide

**Issue:** Frontend receives `{count: 0, results: []}` from departments/roles endpoints

**Database Status:** ✅ 12 Departments and 53 Roles exist in the database

---

## Root Cause Analysis

The backend HAS data, but frontend gets empty results. Common causes:

### 1. ❌ Authentication Not Sent
**Problem:** Request missing Authorization header

**Check in Browser DevTools:**
```javascript
// Network tab -> Click request -> Headers
// Should see: Authorization: Token abc123...
```

**Fix:** Ensure token is included in fetch
```javascript
const token = localStorage.getItem('authToken'); // or however you store it
const response = await fetch('/api/staff/departments/', {
  headers: {
    'Authorization': `Token ${token}` // Must include this!
  }
});
```

### 2. ❌ Wrong URL
**Problem:** Calling wrong endpoint or wrong base URL

**Correct URLs:**
```
✓ http://localhost:8000/api/staff/departments/
✓ http://localhost:8000/api/staff/roles/
✗ http://localhost:8000/departments/  (missing /api/staff/)
✗ http://localhost:3000/api/staff/departments/  (calling frontend server)
```

**Fix:** Use environment variable for API base URL
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const response = await fetch(`${API_BASE_URL}/api/staff/departments/`, {
  headers: { 'Authorization': `Token ${token}` }
});
```

### 3. ❌ CORS Issues
**Problem:** Browser blocks cross-origin requests

**Symptoms in Console:**
```
Access to fetch at 'http://localhost:8000/api/staff/departments/' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Backend Fix:** Check `settings.py` has CORS configured:
```python
INSTALLED_APPS = [
    ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be FIRST
    'django.middleware.common.CommonMiddleware',
    ...
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Or for development only:
CORS_ALLOW_ALL_ORIGINS = True  # Remove in production!
```

### 4. ❌ Pagination Misunderstanding
**Problem:** Using wrong property from response

**Backend Returns:**
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    { "id": 1, "name": "Front Office", "slug": "front-office" },
    ...
  ]
}
```

**Fix:** Access `.results` not the root object
```javascript
const response = await fetch('/api/staff/departments/', {
  headers: { 'Authorization': `Token ${token}` }
});
const data = await response.json();
const departments = data.results; // ← Use .results!
setDepartments(departments);
```

---

## Defensive Frontend Code

### StaffCreate.jsx (Safe Version)

```javascript
import React, { useState, useEffect } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function StaffCreate({ hotelSlug }) {
  const [departments, setDepartments] = useState([]);
  const [roles, setRoles] = useState([]);
  const [filteredRoles, setFilteredRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [formData, setFormData] = useState({
    user_id: '',
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    department: '',
    role: '',
    access_level: 'regular_staff',
    is_active: true,
    is_on_duty: false
  });

  // Get auth token from localStorage (or your auth context)
  const getAuthToken = () => {
    return localStorage.getItem('authToken') || 
           sessionStorage.getItem('authToken');
  };

  // Fetch departments on component mount
  useEffect(() => {
    fetchDepartments();
    fetchAllRoles();
  }, []);

  // Filter roles when department changes
  useEffect(() => {
    if (formData.department) {
      const filtered = roles.filter(
        role => role.department === parseInt(formData.department)
      );
      setFilteredRoles(filtered);
    } else {
      setFilteredRoles([]);
    }
  }, [formData.department, roles]);

  const fetchDepartments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = getAuthToken();
      
      if (!token) {
        throw new Error('No authentication token found. Please login.');
      }

      const response = await fetch(`${API_BASE_URL}/api/staff/departments/`, {
        method: 'GET',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Unauthorized. Please login again.');
        }
        throw new Error(`Failed to fetch departments: ${response.status}`);
      }

      const data = await response.json();
      
      // Defensive: Ensure results is an array
      const departmentList = Array.isArray(data.results) ? data.results : [];
      
      console.log('Fetched departments:', departmentList);
      setDepartments(departmentList);
      
      if (departmentList.length === 0) {
        console.warn('No departments found in database');
      }
      
    } catch (err) {
      console.error('Error fetching departments:', err);
      setError(err.message);
      setDepartments([]); // Ensure it's always an array
    } finally {
      setLoading(false);
    }
  };

  const fetchAllRoles = async () => {
    try {
      const token = getAuthToken();
      
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch(`${API_BASE_URL}/api/staff/roles/`, {
        method: 'GET',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch roles: ${response.status}`);
      }

      const data = await response.json();
      
      // Defensive: Ensure results is an array
      const roleList = Array.isArray(data.results) ? data.results : [];
      
      console.log('Fetched roles:', roleList);
      setRoles(roleList);
      
    } catch (err) {
      console.error('Error fetching roles:', err);
      setRoles([]); // Ensure it's always an array
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch(`${API_BASE_URL}/api/staff/${hotelSlug}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: parseInt(formData.user_id),
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email,
          phone_number: formData.phone_number,
          department: formData.department ? parseInt(formData.department) : null,
          role: formData.role ? parseInt(formData.role) : null,
          access_level: formData.access_level,
          is_active: formData.is_active,
          is_on_duty: formData.is_on_duty
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(JSON.stringify(errorData));
      }

      const newStaff = await response.json();
      console.log('Staff created successfully:', newStaff);
      
      // Reset form or redirect
      alert('Staff member created successfully!');
      
    } catch (err) {
      console.error('Error creating staff:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="staff-create-form">
      <h2>Create New Staff Member</h2>
      
      {error && (
        <div className="error-message" style={{ color: 'red', padding: '10px', marginBottom: '10px', border: '1px solid red' }}>
          Error: {error}
        </div>
      )}

      {loading && <div className="loading">Loading...</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>User ID *</label>
          <input
            type="number"
            name="user_id"
            value={formData.user_id}
            onChange={handleInputChange}
            required
            placeholder="Enter user ID"
          />
        </div>

        <div className="form-group">
          <label>First Name</label>
          <input
            type="text"
            name="first_name"
            value={formData.first_name}
            onChange={handleInputChange}
            placeholder="John"
          />
        </div>

        <div className="form-group">
          <label>Last Name</label>
          <input
            type="text"
            name="last_name"
            value={formData.last_name}
            onChange={handleInputChange}
            placeholder="Doe"
          />
        </div>

        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            placeholder="john.doe@hotel.com"
          />
        </div>

        <div className="form-group">
          <label>Phone Number</label>
          <input
            type="tel"
            name="phone_number"
            value={formData.phone_number}
            onChange={handleInputChange}
            placeholder="+1234567890"
          />
        </div>

        <div className="form-group">
          <label>Department</label>
          <select
            name="department"
            value={formData.department}
            onChange={handleInputChange}
          >
            <option value="">-- Select Department --</option>
            {Array.isArray(departments) && departments.length > 0 ? (
              departments.map(dept => (
                <option key={dept.id} value={dept.id}>
                  {dept.name}
                </option>
              ))
            ) : (
              <option disabled>No departments available</option>
            )}
          </select>
          {departments.length === 0 && !loading && (
            <small style={{ color: 'orange' }}>
              No departments found. Please contact administrator.
            </small>
          )}
        </div>

        <div className="form-group">
          <label>Role</label>
          <select
            name="role"
            value={formData.role}
            onChange={handleInputChange}
            disabled={!formData.department}
          >
            <option value="">-- Select Role --</option>
            {Array.isArray(filteredRoles) && filteredRoles.length > 0 ? (
              filteredRoles.map(role => (
                <option key={role.id} value={role.id}>
                  {role.name}
                </option>
              ))
            ) : formData.department ? (
              <option disabled>No roles for this department</option>
            ) : (
              <option disabled>Select a department first</option>
            )}
          </select>
        </div>

        <div className="form-group">
          <label>Access Level</label>
          <select
            name="access_level"
            value={formData.access_level}
            onChange={handleInputChange}
          >
            <option value="regular_staff">Regular Staff</option>
            <option value="staff_admin">Staff Admin</option>
            <option value="super_staff_admin">Super Staff Admin</option>
          </select>
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              name="is_active"
              checked={formData.is_active}
              onChange={handleInputChange}
            />
            Active
          </label>
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              name="is_on_duty"
              checked={formData.is_on_duty}
              onChange={handleInputChange}
            />
            On Duty
          </label>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Staff Member'}
        </button>
        
        <button type="button" onClick={() => {
          fetchDepartments();
          fetchAllRoles();
        }}>
          Refresh Data
        </button>
      </form>

      {/* Debug Info (remove in production) */}
      <details style={{ marginTop: '20px', padding: '10px', background: '#f5f5f5' }}>
        <summary>Debug Info</summary>
        <pre style={{ fontSize: '12px' }}>
          {JSON.stringify({
            departmentsCount: departments.length,
            rolesCount: roles.length,
            filteredRolesCount: filteredRoles.length,
            selectedDepartment: formData.department,
            selectedRole: formData.role,
            authToken: getAuthToken() ? 'Present' : 'Missing',
            apiBaseUrl: API_BASE_URL
          }, null, 2)}
        </pre>
      </details>
    </div>
  );
}

export default StaffCreate;
```

---

## Quick Test Commands

### Test from Browser Console

```javascript
// 1. Check if you have a token
console.log('Token:', localStorage.getItem('authToken'));

// 2. Test departments endpoint
fetch('http://localhost:8000/api/staff/departments/', {
  headers: {
    'Authorization': `Token ${localStorage.getItem('authToken')}`
  }
})
.then(r => r.json())
.then(data => {
  console.log('Departments:', data);
  console.log('Count:', data.count);
  console.log('Results:', data.results);
});

// 3. Test roles endpoint
fetch('http://localhost:8000/api/staff/roles/', {
  headers: {
    'Authorization': `Token ${localStorage.getItem('authToken')}`
  }
})
.then(r => r.json())
.then(data => {
  console.log('Roles:', data);
  console.log('Count:', data.count);
});
```

### Test with cURL (Windows PowerShell)

```powershell
# Replace YOUR_TOKEN with actual token
$token = "YOUR_TOKEN"
$headers = @{ "Authorization" = "Token $token" }

# Test departments
Invoke-WebRequest -Uri "http://localhost:8000/api/staff/departments/" -Headers $headers | Select-Object -ExpandProperty Content | ConvertFrom-Json

# Test roles
Invoke-WebRequest -Uri "http://localhost:8000/api/staff/roles/" -Headers $headers | Select-Object -ExpandProperty Content | ConvertFrom-Json
```

---

## Common Fixes Checklist

- [ ] ✅ Backend server is running (`python manage.py runserver`)
- [ ] ✅ Authentication token is stored and retrieved correctly
- [ ] ✅ Token is included in fetch headers: `Authorization: Token abc123...`
- [ ] ✅ Using correct URL: `http://localhost:8000/api/staff/departments/`
- [ ] ✅ CORS is configured in Django settings
- [ ] ✅ Using `data.results` not just `data` from response
- [ ] ✅ Defensive coding: `Array.isArray()` checks before `.map()`
- [ ] ✅ Error handling in place for failed requests
- [ ] ✅ Network tab in DevTools shows 200 OK status

---

## Expected Response Format

```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 13,
      "name": "Front Office",
      "slug": "front-office",
      "description": "Oversees guest check-in/check-out, reservations..."
    },
    {
      "id": 14,
      "name": "Kitchen",
      "slug": "kitchen",
      "description": "Responsible for food preparation..."
    }
    // ... 10 more departments
  ]
}
```

If you're getting `{count: 0, results: []}`, the most likely cause is **missing authentication token** in the request headers.
