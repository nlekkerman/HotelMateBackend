# Department Filtering with Dropdown Selection Guide

## Overview
This guide shows how to implement dropdown filtering for department-based staff management, including:
1. Staff needing approval for unrostered shifts
2. Currently logged-in/active staff
3. Interactive dropdown selection with real-time filtering

## 🎯 Core API Endpoints

### Primary Department Status Endpoint
```http
GET /api/staff/hotel/{hotel_slug}/attendance/clock-logs/department-status/
```

### Staff by Department Endpoint
```http
GET /api/staff/hotel/{hotel_slug}/by_department/?department={department_slug}
```

### Department Metadata Endpoint
```http
GET /api/staff/hotel/{hotel_slug}/metadata/
```

## 📋 Available Department Slugs

```javascript
const DEPARTMENT_OPTIONS = [
  { value: '', label: 'All Departments' },
  { value: 'front-office', label: 'Front Office' },
  { value: 'food-and-beverage', label: 'Food & Beverage' },
  { value: 'housekeeping', label: 'Housekeeping' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'management', label: 'Management' },
  { value: 'security', label: 'Security' },
  { value: 'unassigned', label: 'Unassigned Staff' }
];
```

## 🔧 Implementation Examples

### 1. React Component with Dropdown Filtering

```jsx
import React, { useState, useEffect } from 'react';

const StaffManagementDashboard = () => {
  const [departments, setDepartments] = useState({});
  const [selectedDepartment, setSelectedDepartment] = useState('');
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [activeStaff, setActiveStaff] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load department status data
  const loadDepartmentData = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setDepartments(data);
      filterByDepartment(selectedDepartment, data);
    } catch (error) {
      console.error('Error loading department data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter data by selected department
  const filterByDepartment = (deptSlug, data = departments) => {
    if (!deptSlug) {
      // Show all departments
      const allPending = Object.entries(data).flatMap(([dept, deptData]) => 
        (deptData.unrostered || []).map(staff => ({ ...staff, department: dept }))
      );
      const allActive = Object.entries(data).flatMap(([dept, deptData]) => 
        (deptData.currently_clocked_in || []).map(staff => ({ ...staff, department: dept }))
      );
      
      setPendingApprovals(allPending);
      setActiveStaff(allActive);
    } else {
      // Show specific department
      const deptData = data[deptSlug] || { unrostered: [], currently_clocked_in: [] };
      setPendingApprovals(deptData.unrostered.map(staff => ({ ...staff, department: deptSlug })));
      setActiveStaff(deptData.currently_clocked_in.map(staff => ({ ...staff, department: deptSlug })));
    }
  };

  // Handle department selection change
  const handleDepartmentChange = (event) => {
    const newDept = event.target.value;
    setSelectedDepartment(newDept);
    filterByDepartment(newDept);
  };

  // Approve unrostered shift
  const approveShift = async (logId) => {
    try {
      await fetch(`/api/staff/hotel/hotel-killarney/attendance/clock-logs/${logId}/approve/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      // Reload data after approval
      await loadDepartmentData();
    } catch (error) {
      console.error('Error approving shift:', error);
    }
  };

  useEffect(() => {
    loadDepartmentData();
    // Set up polling for real-time updates
    const interval = setInterval(loadDepartmentData, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="staff-management-dashboard">
      <h2>Staff Management Dashboard</h2>
      
      {/* Department Filter Dropdown */}
      <div className="filter-section">
        <label htmlFor="department-select">Filter by Department:</label>
        <select 
          id="department-select"
          value={selectedDepartment} 
          onChange={handleDepartmentChange}
          className="department-dropdown"
        >
          <option value="">All Departments</option>
          <option value="front-office">Front Office</option>
          <option value="food-and-beverage">Food & Beverage</option>
          <option value="housekeeping">Housekeeping</option>
          <option value="maintenance">Maintenance</option>
          <option value="management">Management</option>
          <option value="security">Security</option>
          <option value="unassigned">Unassigned Staff</option>
        </select>
      </div>

      {loading && <div className="loading">Loading...</div>}

      {/* Pending Approvals Section */}
      <div className="approvals-section">
        <h3>
          Pending Approvals ({pendingApprovals.length})
          {selectedDepartment && ` - ${selectedDepartment.replace('-', ' ')}`}
        </h3>
        
        {pendingApprovals.length === 0 ? (
          <p>No pending approvals for this department.</p>
        ) : (
          <div className="approval-list">
            {pendingApprovals.map(staff => (
              <div key={staff.log_id} className="approval-item">
                <div className="staff-info">
                  <strong>{staff.staff_name}</strong>
                  <span className="department-badge">{staff.department}</span>
                  <span>Clock-in: {staff.clock_in_time}</span>
                  <span>Hours: {staff.hours_worked}</span>
                </div>
                <button 
                  onClick={() => approveShift(staff.log_id)}
                  className="approve-btn"
                >
                  Approve
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Currently Active Staff Section */}
      <div className="active-staff-section">
        <h3>
          Currently Active Staff ({activeStaff.length})
          {selectedDepartment && ` - ${selectedDepartment.replace('-', ' ')}`}
        </h3>
        
        {activeStaff.length === 0 ? (
          <p>No active staff for this department.</p>
        ) : (
          <div className="staff-list">
            {activeStaff.map(staff => (
              <div key={staff.staff_id} className="staff-item">
                <div className="staff-info">
                  <strong>{staff.staff_name}</strong>
                  <span className="department-badge">{staff.department}</span>
                  <span>Clock-in: {staff.clock_in_time}</span>
                  <span>Hours: {staff.hours_worked}</span>
                  {staff.is_on_break && <span className="break-badge">On Break</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default StaffManagementDashboard;
```

### 2. Vue.js Component with Dropdown

```vue
<template>
  <div class="staff-management">
    <h2>Staff Management Dashboard</h2>
    
    <!-- Department Filter Dropdown -->
    <div class="filter-controls">
      <label for="dept-filter">Department:</label>
      <select 
        id="dept-filter" 
        v-model="selectedDepartment" 
        @change="onDepartmentChange"
        class="form-control"
      >
        <option value="">All Departments</option>
        <option 
          v-for="dept in departmentOptions" 
          :key="dept.value" 
          :value="dept.value"
        >
          {{ dept.label }}
        </option>
      </select>
      
      <span class="filter-info">
        {{ selectedDepartment ? `Showing: ${getDepartmentName(selectedDepartment)}` : 'Showing: All Departments' }}
      </span>
    </div>

    <!-- Statistics Summary -->
    <div class="stats-summary">
      <div class="stat-card">
        <h4>Pending Approvals</h4>
        <span class="stat-number">{{ filteredPendingApprovals.length }}</span>
      </div>
      <div class="stat-card">
        <h4>Active Staff</h4>
        <span class="stat-number">{{ filteredActiveStaff.length }}</span>
      </div>
    </div>

    <!-- Pending Approvals -->
    <div class="section">
      <h3>Pending Unrostered Shift Approvals</h3>
      <div v-if="filteredPendingApprovals.length === 0" class="no-data">
        No pending approvals {{ selectedDepartment ? `for ${getDepartmentName(selectedDepartment)}` : '' }}
      </div>
      
      <div v-else class="approval-grid">
        <div 
          v-for="staff in filteredPendingApprovals" 
          :key="staff.log_id" 
          class="approval-card"
        >
          <div class="card-header">
            <h4>{{ staff.staff_name }}</h4>
            <span class="department-tag">{{ getDepartmentName(staff.department) }}</span>
          </div>
          
          <div class="card-body">
            <p><strong>Clock-in:</strong> {{ staff.clock_in_time }}</p>
            <p><strong>Hours Worked:</strong> {{ staff.hours_worked }}</p>
            <p><strong>Status:</strong> 
              <span :class="staff.currently_active ? 'active' : 'clocked-out'">
                {{ staff.currently_active ? 'Currently Active' : 'Clocked Out' }}
              </span>
            </p>
          </div>
          
          <div class="card-actions">
            <button 
              @click="approveShift(staff.log_id)" 
              class="btn btn-success"
              :disabled="approving === staff.log_id"
            >
              {{ approving === staff.log_id ? 'Approving...' : 'Approve' }}
            </button>
            <button 
              @click="rejectShift(staff.log_id)" 
              class="btn btn-danger"
            >
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Currently Active Staff -->
    <div class="section">
      <h3>Currently Active Staff</h3>
      <div v-if="filteredActiveStaff.length === 0" class="no-data">
        No active staff {{ selectedDepartment ? `in ${getDepartmentName(selectedDepartment)}` : '' }}
      </div>
      
      <div v-else class="staff-grid">
        <div 
          v-for="staff in filteredActiveStaff" 
          :key="staff.staff_id" 
          class="staff-card"
        >
          <div class="card-header">
            <h4>{{ staff.staff_name }}</h4>
            <span class="department-tag">{{ getDepartmentName(staff.department) }}</span>
          </div>
          
          <div class="card-body">
            <p><strong>Clock-in:</strong> {{ staff.clock_in_time }}</p>
            <p><strong>Hours Worked:</strong> {{ staff.hours_worked }}</p>
            <p v-if="staff.is_on_break" class="break-status">🔶 On Break</p>
            <p><strong>Status:</strong> 
              <span class="approved">{{ staff.is_approved ? 'Approved' : 'Pending' }}</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StaffManagement',
  data() {
    return {
      departments: {},
      selectedDepartment: '',
      approving: null,
      loading: false,
      departmentOptions: [
        { value: 'front-office', label: 'Front Office' },
        { value: 'food-and-beverage', label: 'Food & Beverage' },
        { value: 'housekeeping', label: 'Housekeeping' },
        { value: 'maintenance', label: 'Maintenance' },
        { value: 'management', label: 'Management' },
        { value: 'security', label: 'Security' },
        { value: 'unassigned', label: 'Unassigned Staff' }
      ]
    };
  },
  
  computed: {
    filteredPendingApprovals() {
      if (!this.selectedDepartment) {
        // Return all pending approvals across departments
        return Object.entries(this.departments).flatMap(([dept, data]) => 
          (data.unrostered || []).map(staff => ({ ...staff, department: dept }))
        );
      }
      
      // Return specific department's pending approvals
      const deptData = this.departments[this.selectedDepartment] || {};
      return (deptData.unrostered || []).map(staff => ({ 
        ...staff, 
        department: this.selectedDepartment 
      }));
    },
    
    filteredActiveStaff() {
      if (!this.selectedDepartment) {
        // Return all active staff across departments
        return Object.entries(this.departments).flatMap(([dept, data]) => 
          (data.currently_clocked_in || []).map(staff => ({ ...staff, department: dept }))
        );
      }
      
      // Return specific department's active staff
      const deptData = this.departments[this.selectedDepartment] || {};
      return (deptData.currently_clocked_in || []).map(staff => ({ 
        ...staff, 
        department: this.selectedDepartment 
      }));
    }
  },
  
  methods: {
    async loadDepartmentData() {
      this.loading = true;
      try {
        const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/', {
          headers: {
            'Authorization': `Bearer ${this.$store.state.auth.token}`
          }
        });
        this.departments = await response.json();
      } catch (error) {
        console.error('Error loading data:', error);
        this.$toast.error('Failed to load department data');
      } finally {
        this.loading = false;
      }
    },
    
    onDepartmentChange() {
      // Trigger reactive updates - computed properties will automatically update
      console.log(`Filtering by department: ${this.selectedDepartment || 'All'}`);
    },
    
    async approveShift(logId) {
      this.approving = logId;
      try {
        await fetch(`/api/staff/hotel/hotel-killarney/attendance/clock-logs/${logId}/approve/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.$store.state.auth.token}`,
            'Content-Type': 'application/json'
          }
        });
        
        this.$toast.success('Shift approved successfully');
        await this.loadDepartmentData(); // Refresh data
      } catch (error) {
        console.error('Error approving shift:', error);
        this.$toast.error('Failed to approve shift');
      } finally {
        this.approving = null;
      }
    },
    
    async rejectShift(logId) {
      try {
        await fetch(`/api/staff/hotel/hotel-killarney/attendance/clock-logs/${logId}/reject/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.$store.state.auth.token}`,
            'Content-Type': 'application/json'
          }
        });
        
        this.$toast.success('Shift rejected');
        await this.loadDepartmentData(); // Refresh data
      } catch (error) {
        console.error('Error rejecting shift:', error);
        this.$toast.error('Failed to reject shift');
      }
    },
    
    getDepartmentName(slug) {
      const dept = this.departmentOptions.find(d => d.value === slug);
      return dept ? dept.label : slug.replace('-', ' ');
    }
  },
  
  mounted() {
    this.loadDepartmentData();
    
    // Set up polling for real-time updates
    this.pollInterval = setInterval(() => {
      this.loadDepartmentData();
    }, 30000); // Poll every 30 seconds
  },
  
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }
  }
};
</script>
```

### 3. Vanilla JavaScript Implementation

```html
<!DOCTYPE html>
<html>
<head>
    <title>Staff Management Dashboard</title>
    <style>
        .filter-section { margin: 20px 0; }
        .department-dropdown { padding: 8px; margin: 0 10px; }
        .section { margin: 30px 0; }
        .staff-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .staff-card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; }
        .department-badge { background: #007bff; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
        .approve-btn { background: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
        .no-data { padding: 20px; text-align: center; color: #666; }
    </style>
</head>
<body>
    <div id="app">
        <h2>Staff Management Dashboard</h2>
        
        <!-- Department Filter -->
        <div class="filter-section">
            <label for="department-filter">Filter by Department:</label>
            <select id="department-filter" class="department-dropdown">
                <option value="">All Departments</option>
                <option value="front-office">Front Office</option>
                <option value="food-and-beverage">Food & Beverage</option>
                <option value="housekeeping">Housekeeping</option>
                <option value="maintenance">Maintenance</option>
                <option value="management">Management</option>
                <option value="security">Security</option>
                <option value="unassigned">Unassigned Staff</option>
            </select>
            <span id="filter-info">Showing: All Departments</span>
        </div>

        <!-- Pending Approvals -->
        <div class="section">
            <h3 id="approvals-title">Pending Approvals (0)</h3>
            <div id="approvals-container"></div>
        </div>

        <!-- Active Staff -->
        <div class="section">
            <h3 id="active-title">Currently Active Staff (0)</h3>
            <div id="active-container"></div>
        </div>
    </div>

    <script>
        class StaffManagement {
            constructor() {
                this.departments = {};
                this.selectedDepartment = '';
                this.token = localStorage.getItem('token');
                
                this.init();
            }
            
            init() {
                // Set up event listeners
                document.getElementById('department-filter').addEventListener('change', (e) => {
                    this.selectedDepartment = e.target.value;
                    this.updateFilterInfo();
                    this.renderData();
                });
                
                // Load initial data
                this.loadDepartmentData();
                
                // Set up polling
                setInterval(() => this.loadDepartmentData(), 30000);
            }
            
            async loadDepartmentData() {
                try {
                    const response = await fetch('/api/staff/hotel/hotel-killarney/attendance/clock-logs/department-status/', {
                        headers: {
                            'Authorization': `Bearer ${this.token}`
                        }
                    });
                    this.departments = await response.json();
                    this.renderData();
                } catch (error) {
                    console.error('Error loading data:', error);
                }
            }
            
            getFilteredData() {
                if (!this.selectedDepartment) {
                    // All departments
                    const pendingApprovals = Object.entries(this.departments).flatMap(([dept, data]) => 
                        (data.unrostered || []).map(staff => ({ ...staff, department: dept }))
                    );
                    const activeStaff = Object.entries(this.departments).flatMap(([dept, data]) => 
                        (data.currently_clocked_in || []).map(staff => ({ ...staff, department: dept }))
                    );
                    return { pendingApprovals, activeStaff };
                } else {
                    // Specific department
                    const deptData = this.departments[this.selectedDepartment] || { unrostered: [], currently_clocked_in: [] };
                    const pendingApprovals = deptData.unrostered.map(staff => ({ ...staff, department: this.selectedDepartment }));
                    const activeStaff = deptData.currently_clocked_in.map(staff => ({ ...staff, department: this.selectedDepartment }));
                    return { pendingApprovals, activeStaff };
                }
            }
            
            renderData() {
                const { pendingApprovals, activeStaff } = this.getFilteredData();
                
                // Update titles
                document.getElementById('approvals-title').textContent = `Pending Approvals (${pendingApprovals.length})`;
                document.getElementById('active-title').textContent = `Currently Active Staff (${activeStaff.length})`;
                
                // Render pending approvals
                this.renderPendingApprovals(pendingApprovals);
                
                // Render active staff
                this.renderActiveStaff(activeStaff);
            }
            
            renderPendingApprovals(approvals) {
                const container = document.getElementById('approvals-container');
                
                if (approvals.length === 0) {
                    container.innerHTML = '<div class="no-data">No pending approvals for this department.</div>';
                    return;
                }
                
                container.innerHTML = approvals.map(staff => `
                    <div class="staff-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <strong>${staff.staff_name}</strong>
                            <span class="department-badge">${this.formatDepartmentName(staff.department)}</span>
                        </div>
                        <p><strong>Clock-in:</strong> ${staff.clock_in_time}</p>
                        <p><strong>Hours Worked:</strong> ${staff.hours_worked}</p>
                        <p><strong>Status:</strong> ${staff.currently_active ? 'Currently Active' : 'Clocked Out'}</p>
                        <button class="approve-btn" onclick="staffManagement.approveShift(${staff.log_id})">
                            Approve
                        </button>
                    </div>
                `).join('');
            }
            
            renderActiveStaff(staff) {
                const container = document.getElementById('active-container');
                
                if (staff.length === 0) {
                    container.innerHTML = '<div class="no-data">No active staff for this department.</div>';
                    return;
                }
                
                container.innerHTML = staff.map(s => `
                    <div class="staff-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <strong>${s.staff_name}</strong>
                            <span class="department-badge">${this.formatDepartmentName(s.department)}</span>
                        </div>
                        <p><strong>Clock-in:</strong> ${s.clock_in_time}</p>
                        <p><strong>Hours Worked:</strong> ${s.hours_worked}</p>
                        ${s.is_on_break ? '<p style="color: orange;"><strong>🔶 On Break</strong></p>' : ''}
                        <p><strong>Approved:</strong> ${s.is_approved ? 'Yes' : 'Pending'}</p>
                    </div>
                `).join('');
            }
            
            async approveShift(logId) {
                try {
                    await fetch(`/api/staff/hotel/hotel-killarney/attendance/clock-logs/${logId}/approve/`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${this.token}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    // Reload data
                    await this.loadDepartmentData();
                    alert('Shift approved successfully!');
                } catch (error) {
                    console.error('Error approving shift:', error);
                    alert('Failed to approve shift');
                }
            }
            
            updateFilterInfo() {
                const filterInfo = document.getElementById('filter-info');
                if (this.selectedDepartment) {
                    filterInfo.textContent = `Showing: ${this.formatDepartmentName(this.selectedDepartment)}`;
                } else {
                    filterInfo.textContent = 'Showing: All Departments';
                }
            }
            
            formatDepartmentName(slug) {
                return slug.split('-').map(word => 
                    word.charAt(0).toUpperCase() + word.slice(1)
                ).join(' ');
            }
        }
        
        // Initialize the application
        const staffManagement = new StaffManagement();
    </script>
</body>
</html>
```

## 🎨 CSS Styling for Dropdown

```css
/* Department Filter Dropdown Styles */
.filter-section {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 30px;
    display: flex;
    align-items: center;
    gap: 15px;
}

.department-dropdown {
    padding: 10px 15px;
    border: 2px solid #e9ecef;
    border-radius: 6px;
    font-size: 14px;
    background: white;
    cursor: pointer;
    transition: border-color 0.3s ease;
}

.department-dropdown:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.filter-info {
    color: #6c757d;
    font-style: italic;
    font-size: 14px;
}

/* Card Styling */
.staff-card, .approval-card {
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: box-shadow 0.3s ease;
}

.staff-card:hover, .approval-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.department-badge {
    background: linear-gradient(45deg, #007bff, #0056b3);
    color: white;
    padding: 4px 12px;
    border-radius: 15px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.approve-btn {
    background: linear-gradient(45deg, #28a745, #20c997);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s ease;
}

.approve-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
}

/* Grid Layouts */
.staff-grid, .approval-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .filter-section {
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
    }
    
    .staff-grid, .approval-grid {
        grid-template-columns: 1fr;
    }
    
    .department-dropdown {
        width: 100%;
    }
}
```

## 🔄 Real-time Updates with WebSockets

```javascript
// Add WebSocket integration for real-time updates
class RealTimeStaffManagement extends StaffManagement {
    constructor() {
        super();
        this.setupWebSocket();
    }
    
    setupWebSocket() {
        // Pusher integration for real-time updates
        const pusher = new Pusher('your-pusher-key', {
            cluster: 'your-cluster'
        });
        
        const channel = pusher.subscribe('attendance-hotel-killarney');
        
        // Listen for approval events
        channel.bind('clocklog-approved', (data) => {
            this.loadDepartmentData(); // Refresh data
            this.showNotification(`${data.staff_name} shift approved`, 'success');
        });
        
        // Listen for new unrostered requests
        channel.bind('unrostered-request', (data) => {
            this.loadDepartmentData(); // Refresh data
            this.showNotification(`New unrostered request from ${data.staff_name}`, 'info');
        });
    }
    
    showNotification(message, type) {
        // Implementation for showing notifications
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}
```

## 📱 Mobile-Responsive Design

The dropdown filtering system is fully responsive and works well on mobile devices. Key features:

- **Touch-friendly dropdowns** with appropriate sizing
- **Responsive grid layouts** that stack on smaller screens  
- **Swipe gestures** for navigating between sections
- **Optimized for portrait and landscape orientations**

This comprehensive guide provides everything needed to implement department-based filtering with dropdown selection for both staff approval management and active staff monitoring.