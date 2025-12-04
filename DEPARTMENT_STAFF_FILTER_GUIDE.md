# CURRENTLY LOGGED IN STAFF BY DEPARTMENT - API GUIDE

## Available Endpoints

### 1. Department Status Overview
**URL**: `/api/staff/hotel/{hotel_slug}/attendance/clock-logs/department-status/`  
**Method**: `GET`  
**Returns**: All departments with currently clocked in staff + unrostered staff

```json
{
  "front-office": {
    "currently_clocked_in": [
      {
        "staff_id": 35,
        "staff_name": "Nikola Simic", 
        "clock_in_time": "14:52",
        "clock_out_time": null,
        "is_on_break": false,
        "hours_worked": 2.5,
        "is_approved": true,
        "currently_active": true
      }
    ],
    "unrostered": []
  },
  "kitchen": {
    "currently_clocked_in": [],
    "unrostered": []
  }
}
```

### 2. Department Logs Filter
**URL**: `/api/staff/hotel/{hotel_slug}/attendance/clock-logs/department-logs/`  
**Method**: `GET`  
**Query Parameters**: `department_slug` (optional)  
**Returns**: Clock logs filtered by department

```
GET /api/staff/hotel/hotel-killarney/attendance/clock-logs/department-logs/?department_slug=front-office
```

### 3. Currently Clocked In (All)
**URL**: `/api/staff/hotel/{hotel_slug}/attendance/clock-logs/currently-clocked-in/`  
**Method**: `GET`  
**Returns**: All currently clocked in staff across all departments

## Frontend Usage Examples

### Get All Departments Status
```javascript
const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/', {
    headers: {
        'Authorization': `Token ${localStorage.getItem('authToken')}`,
        'Content-Type': 'application/json'
    }
});

const departmentData = await response.json();

// Access specific department
const frontOfficeStaff = departmentData['front-office']?.currently_clocked_in || [];
const kitchenStaff = departmentData['kitchen']?.currently_clocked_in || [];
```

### Filter by Specific Department
```javascript
async function getCurrentlyLoggedInByDepartment(departmentSlug) {
    const url = `/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-logs/?department_slug=${departmentSlug}`;
    
    const response = await fetch(url, {
        headers: {
            'Authorization': `Token ${localStorage.getItem('authToken')}`,
            'Content-Type': 'application/json'
        }
    });
    
    return await response.json();
}

// Usage
const frontOfficeStaff = await getCurrentlyLoggedInByDepartment('front-office');
const kitchenStaff = await getCurrentlyLoggedInByDepartment('kitchen');
const housekeepingStaff = await getCurrentlyLoggedInByDepartment('housekeeping');
```

### Get Count by Department
```javascript
async function getStaffCountsByDepartment() {
    const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/', {
        headers: {
            'Authorization': `Token ${localStorage.getItem('authToken')}`,
            'Content-Type': 'application/json'
        }
    });
    
    const data = await response.json();
    const counts = {};
    
    for (const [deptSlug, deptData] of Object.entries(data)) {
        counts[deptSlug] = {
            currently_clocked_in: deptData.currently_clocked_in.length,
            unrostered: deptData.unrostered.length,
            total: deptData.currently_clocked_in.length + deptData.unrostered.length
        };
    }
    
    return counts;
}

// Result:
// {
//   "front-office": { currently_clocked_in: 2, unrostered: 0, total: 2 },
//   "kitchen": { currently_clocked_in: 1, unrostered: 1, total: 2 }
// }
```

## Common Department Slugs
- `front-office`
- `kitchen`  
- `housekeeping`
- `maintenance`
- `bar`
- `restaurant`
- `reception`
- `security`
- `management`

## Filter in Frontend Component
```jsx
const DepartmentStaffList = ({ selectedDepartment }) => {
    const [departmentData, setDepartmentData] = useState({});
    
    useEffect(() => {
        const fetchDepartmentStatus = async () => {
            const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/', {
                headers: {
                    'Authorization': `Token ${localStorage.getItem('authToken')}`,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            setDepartmentData(data);
        };
        
        fetchDepartmentStatus();
    }, []);
    
    // Filter by selected department
    const currentStaff = selectedDepartment 
        ? departmentData[selectedDepartment]?.currently_clocked_in || []
        : Object.values(departmentData).flatMap(dept => dept.currently_clocked_in);
    
    return (
        <div>
            <h3>Currently Logged In Staff</h3>
            {selectedDepartment && <p>Department: {selectedDepartment}</p>}
            
            {currentStaff.map(staff => (
                <div key={staff.staff_id} className="staff-card">
                    <h4>{staff.staff_name}</h4>
                    <p>Clocked in: {staff.clock_in_time}</p>
                    <p>Hours worked: {staff.hours_worked}</p>
                    {staff.is_on_break && <span className="badge">On Break</span>}
                </div>
            ))}
        </div>
    );
};
```