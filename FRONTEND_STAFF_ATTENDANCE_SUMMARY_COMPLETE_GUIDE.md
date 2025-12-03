# Frontend Staff Attendance Summary - Complete Implementation Guide

## 🎯 Overview

This guide provides comprehensive instructions for implementing staff attendance summaries in the frontend, including displaying the smallest durations, fetching roster data for departments and individual staff, and unlocking the full potential of attendance analytics.

## 📊 Core API Endpoints

### 1. Staff Attendance Summary (Enhanced Dashboard)

**Primary Endpoint:**
```http
GET /api/staff/{hotel_slug}/attendance-summary/
```

**Query Parameters:**
- `from` (required): Start date (YYYY-MM-DD)
- `to` (optional): End date (defaults to `from`)
- `department` (optional): Filter by department slug
- `status` (optional): Filter by attendance status (`active`, `completed`, `no_log`, `issue`)

**Response Structure:**
```javascript
{
  "results": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "department_name": "Housekeeping",
      "department_slug": "housekeeping",
      "duty_status": "on_duty",
      "avatar_url": "https://res.cloudinary.com/...",
      
      // Core Attendance Metrics
      "planned_shifts": 5,
      "worked_shifts": 4,
      "total_worked_minutes": 1920,  // Total minutes worked in period
      "issues_count": 1,
      "attendance_status": "active",
      
      // UI Badge Information
      "duty_status_badge": {
        "label": "On Duty",
        "color": "success",
        "bg_color": "#28a745",
        "status_type": "active"
      },
      "attendance_status_badge": {
        "label": "Currently Active",
        "color": "success",
        "bg_color": "#28a745",
        "priority": 1
      }
    }
  ],
  "count": 25,
  "date_range": {
    "from": "2025-12-03",
    "to": "2025-12-03"
  },
  "filters": {
    "hotel": "hotel-killarney",
    "department": "housekeeping",
    "status": "active"
  }
}
```

## 🔢 Duration Display & Calculations

### Converting Minutes to Display Format

**Smallest Duration Helper Function:**
```javascript
// Duration formatting utilities
const formatDuration = {
  // Convert minutes to hours and minutes
  toHoursMinutes: (minutes) => {
    if (!minutes || minutes === 0) return "0m";
    
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    if (hours === 0) return `${mins}m`;
    if (mins === 0) return `${hours}h`;
    return `${hours}h ${mins}m`;
  },

  // Convert minutes to decimal hours (for detailed view)
  toDecimalHours: (minutes) => {
    if (!minutes) return "0.00";
    return (minutes / 60).toFixed(2);
  },

  // Get the smallest duration from an array of staff
  getSmallestDuration: (staffList) => {
    if (!staffList || staffList.length === 0) return 0;
    
    const workingStaff = staffList.filter(staff => 
      staff.total_worked_minutes && staff.total_worked_minutes > 0
    );
    
    if (workingStaff.length === 0) return 0;
    
    return Math.min(...workingStaff.map(staff => staff.total_worked_minutes));
  },

  // Get duration statistics for dashboard
  getDurationStats: (staffList) => {
    const workingStaff = staffList.filter(staff => 
      staff.total_worked_minutes && staff.total_worked_minutes > 0
    );
    
    if (workingStaff.length === 0) {
      return {
        min: 0,
        max: 0,
        avg: 0,
        total: 0,
        count: 0
      };
    }
    
    const durations = workingStaff.map(staff => staff.total_worked_minutes);
    const total = durations.reduce((sum, duration) => sum + duration, 0);
    
    return {
      min: Math.min(...durations),
      max: Math.max(...durations),
      avg: Math.round(total / durations.length),
      total: total,
      count: durations.length
    };
  }
};

// Usage examples:
const staff = {
  total_worked_minutes: 485  // 8 hours 5 minutes
};

console.log(formatDuration.toHoursMinutes(staff.total_worked_minutes)); // "8h 5m"
console.log(formatDuration.toDecimalHours(staff.total_worked_minutes)); // "8.08"

// Find smallest duration in department
const housekeepingStaff = [
  { name: "John", total_worked_minutes: 480 },    // 8h
  { name: "Jane", total_worked_minutes: 240 },    // 4h
  { name: "Bob", total_worked_minutes: 90 },      // 1.5h
];

const smallestDuration = formatDuration.getSmallestDuration(housekeepingStaff);
console.log(`Smallest shift: ${formatDuration.toHoursMinutes(smallestDuration)}`); // "1h 30m"
```

## 🏢 Department Roster Analytics

### 2. Department-Level Roster Data

**Endpoint:**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/department-summary/
```

**Query Parameters:**
- `start_date`: YYYY-MM-DD (required)
- `end_date`: YYYY-MM-DD (required)
- `department`: department slug (optional)

**Response:**
```javascript
[
  {
    "dept_id": 1,
    "department_name": "Housekeeping",
    "department_slug": "housekeeping",
    "total_rostered_hours": 420.0,
    "shifts_count": 52,
    "avg_shift_length": 8.08,
    "unique_staff": 10
  },
  {
    "dept_id": 2,
    "department_name": "Reception",
    "department_slug": "reception",
    "total_rostered_hours": 280.0,
    "shifts_count": 35,
    "avg_shift_length": 8.0,
    "unique_staff": 7
  }
]
```

**Frontend Implementation:**
```javascript
// Department roster analytics service
const departmentRosterService = {
  // Fetch department summaries
  async fetchDepartmentSummaries(hotelSlug, startDate, endDate, department = null) {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate
    });
    
    if (department) {
      params.append('department', department);
    }
    
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/attendance/roster-analytics/department-summary/?${params}`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to fetch department summaries: ${response.statusText}`);
    }
    
    return await response.json();
  },

  // Get daily breakdown by department
  async fetchDailyByDepartment(hotelSlug, startDate, endDate) {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate
    });
    
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/attendance/roster-analytics/daily-by-department/?${params}`
    );
    
    return await response.json();
  },

  // Get weekly breakdown by department
  async fetchWeeklyByDepartment(hotelSlug, startDate, endDate) {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate
    });
    
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/attendance/roster-analytics/weekly-by-department/?${params}`
    );
    
    return await response.json();
  }
};

// Department analytics component
const DepartmentAnalytics = {
  data() {
    return {
      departmentSummaries: [],
      loading: false,
      selectedDateRange: {
        start: new Date().toISOString().split('T')[0],
        end: new Date().toISOString().split('T')[0]
      }
    };
  },

  methods: {
    async loadDepartmentData() {
      this.loading = true;
      try {
        this.departmentSummaries = await departmentRosterService.fetchDepartmentSummaries(
          this.hotelSlug,
          this.selectedDateRange.start,
          this.selectedDateRange.end
        );
      } catch (error) {
        console.error('Error loading department data:', error);
        this.$toast.error('Failed to load department analytics');
      } finally {
        this.loading = false;
      }
    },

    // Calculate smallest average shift in all departments
    getSmallestAvgShift() {
      if (!this.departmentSummaries.length) return 0;
      
      const avgShifts = this.departmentSummaries.map(dept => dept.avg_shift_length);
      return Math.min(...avgShifts);
    },

    // Format department statistics
    formatDepartmentStats(department) {
      return {
        name: department.department_name,
        slug: department.department_slug,
        totalHours: department.total_rostered_hours.toFixed(1),
        shiftsCount: department.shifts_count,
        avgShiftLength: formatDuration.toHoursMinutes(department.avg_shift_length * 60),
        staffCount: department.unique_staff,
        hoursPerStaff: (department.total_rostered_hours / department.unique_staff).toFixed(1)
      };
    }
  }
};
```

## 👤 Individual Staff Roster Data

### 3. Individual Staff Analytics

**Endpoint:**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/staff-summary/
```

**Response:**
```javascript
[
  {
    "staff_id": 123,
    "first_name": "John",
    "last_name": "Doe",
    "dept_id": 1,
    "department_name": "Housekeeping",
    "department_slug": "housekeeping",
    "total_rostered_hours": 42.0,
    "shifts_count": 6,
    "avg_shift_length": 7.0
  }
]
```

**Daily Staff Breakdown:**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/daily-by-staff/
```

**Weekly Staff Breakdown:**
```http
GET /api/staff/hotel/{hotel_slug}/attendance/roster-analytics/weekly-by-staff/
```

**Frontend Implementation:**
```javascript
// Individual staff roster service
const staffRosterService = {
  // Fetch individual staff summaries
  async fetchStaffSummaries(hotelSlug, startDate, endDate, department = null) {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate
    });
    
    if (department) {
      params.append('department', department);
    }
    
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/attendance/roster-analytics/staff-summary/?${params}`
    );
    
    return await response.json();
  },

  // Get daily breakdown by staff
  async fetchDailyByStaff(hotelSlug, startDate, endDate, department = null) {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate
    });
    
    if (department) {
      params.append('department', department);
    }
    
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/attendance/roster-analytics/daily-by-staff/?${params}`
    );
    
    return await response.json();
  },

  // Get staff roster for specific date
  async fetchStaffRosterForDate(hotelSlug, date, department = null) {
    const params = new URLSearchParams({
      shift_date: date
    });
    
    if (department) {
      params.append('department', department);
    }
    
    const response = await fetch(
      `/api/staff/hotel/${hotelSlug}/attendance/shifts/?${params}`
    );
    
    return await response.json();
  }
};

// Staff roster component
const StaffRosterAnalytics = {
  data() {
    return {
      staffSummaries: [],
      dailyBreakdown: [],
      selectedStaff: null,
      filterDepartment: null
    };
  },

  methods: {
    async loadStaffData() {
      try {
        // Load staff summaries
        this.staffSummaries = await staffRosterService.fetchStaffSummaries(
          this.hotelSlug,
          this.selectedDateRange.start,
          this.selectedDateRange.end,
          this.filterDepartment
        );

        // Load daily breakdown
        this.dailyBreakdown = await staffRosterService.fetchDailyByStaff(
          this.hotelSlug,
          this.selectedDateRange.start,
          this.selectedDateRange.end,
          this.filterDepartment
        );
      } catch (error) {
        console.error('Error loading staff data:', error);
      }
    },

    // Find staff with smallest average shift
    findStaffWithSmallestShifts() {
      if (!this.staffSummaries.length) return null;
      
      return this.staffSummaries.reduce((smallest, current) => {
        return current.avg_shift_length < smallest.avg_shift_length ? current : smallest;
      });
    },

    // Get staff roster performance metrics
    getStaffPerformanceMetrics(staffId) {
      const summary = this.staffSummaries.find(s => s.staff_id === staffId);
      const dailyData = this.dailyBreakdown.filter(d => d.staff_id === staffId);
      
      if (!summary) return null;

      return {
        name: `${summary.first_name} ${summary.last_name}`,
        department: summary.department_name,
        totalHours: summary.total_rostered_hours,
        shiftsCount: summary.shifts_count,
        avgShiftLength: formatDuration.toHoursMinutes(summary.avg_shift_length * 60),
        dailyBreakdown: dailyData.map(day => ({
          date: day.date,
          hours: day.total_rostered_hours,
          shifts: day.shifts_count
        }))
      };
    }
  }
};
```

## 📈 Enhanced Dashboard Components

### 4. Complete Dashboard Implementation

```javascript
// Main attendance dashboard component
const AttendanceDashboard = {
  data() {
    return {
      // Core data
      staffSummaries: [],
      departmentAnalytics: [],
      rosterAnalytics: [],
      
      // Filters
      selectedDepartment: null,
      selectedStatus: null,
      dateRange: {
        start: new Date().toISOString().split('T')[0],
        end: new Date().toISOString().split('T')[0]
      },
      
      // UI state
      loading: false,
      view: 'summary', // summary, departments, individuals
      
      // Analytics
      durationStats: null,
      performanceMetrics: null
    };
  },

  computed: {
    // Filter staff by selected criteria
    filteredStaff() {
      let filtered = [...this.staffSummaries];
      
      if (this.selectedDepartment) {
        filtered = filtered.filter(staff => 
          staff.department_slug === this.selectedDepartment
        );
      }
      
      if (this.selectedStatus) {
        filtered = filtered.filter(staff => 
          staff.attendance_status === this.selectedStatus
        );
      }
      
      return filtered;
    },

    // Calculate duration statistics
    durationStatistics() {
      return formatDuration.getDurationStats(this.filteredStaff);
    },

    // Get departments list
    availableDepartments() {
      const departments = new Set();
      this.staffSummaries.forEach(staff => {
        if (staff.department_name) {
          departments.add(JSON.stringify({
            name: staff.department_name,
            slug: staff.department_slug
          }));
        }
      });
      
      return Array.from(departments).map(dept => JSON.parse(dept));
    }
  },

  methods: {
    // Load all dashboard data
    async loadDashboardData() {
      this.loading = true;
      try {
        // Load staff attendance summaries
        await this.loadAttendanceSummaries();
        
        // Load department analytics
        await this.loadDepartmentAnalytics();
        
        // Load individual staff roster data
        await this.loadStaffRosterData();
        
        // Calculate performance metrics
        this.calculatePerformanceMetrics();
        
      } catch (error) {
        console.error('Error loading dashboard data:', error);
        this.$toast.error('Failed to load dashboard data');
      } finally {
        this.loading = false;
      }
    },

    // Load attendance summaries
    async loadAttendanceSummaries() {
      const params = new URLSearchParams({
        from: this.dateRange.start,
        to: this.dateRange.end
      });
      
      if (this.selectedDepartment) {
        params.append('department', this.selectedDepartment);
      }
      
      if (this.selectedStatus) {
        params.append('status', this.selectedStatus);
      }
      
      const response = await fetch(
        `/api/staff/${this.hotelSlug}/attendance-summary/?${params}`
      );
      
      const data = await response.json();
      this.staffSummaries = data.results;
    },

    // Load department analytics
    async loadDepartmentAnalytics() {
      this.departmentAnalytics = await departmentRosterService.fetchDepartmentSummaries(
        this.hotelSlug,
        this.dateRange.start,
        this.dateRange.end
      );
    },

    // Load staff roster analytics
    async loadStaffRosterData() {
      this.rosterAnalytics = await staffRosterService.fetchStaffSummaries(
        this.hotelSlug,
        this.dateRange.start,
        this.dateRange.end
      );
    },

    // Calculate performance metrics
    calculatePerformanceMetrics() {
      const stats = this.durationStatistics;
      
      this.performanceMetrics = {
        // Duration metrics
        smallestDuration: formatDuration.toHoursMinutes(stats.min),
        largestDuration: formatDuration.toHoursMinutes(stats.max),
        averageDuration: formatDuration.toHoursMinutes(stats.avg),
        totalWorkHours: formatDuration.toHoursMinutes(stats.total),
        
        // Staff metrics
        totalStaff: this.filteredStaff.length,
        activeStaff: this.filteredStaff.filter(s => s.attendance_status === 'active').length,
        staffWithIssues: this.filteredStaff.filter(s => s.issues_count > 0).length,
        
        // Department metrics
        departmentCount: this.availableDepartments.length,
        departmentWithSmallestAvg: this.getDepartmentWithSmallestAvg()
      };
    },

    // Get department with smallest average shift
    getDepartmentWithSmallestAvg() {
      if (!this.departmentAnalytics.length) return null;
      
      return this.departmentAnalytics.reduce((smallest, current) => {
        return current.avg_shift_length < smallest.avg_shift_length ? current : smallest;
      });
    },

    // Format staff for display
    formatStaffForDisplay(staff) {
      return {
        ...staff,
        formattedDuration: formatDuration.toHoursMinutes(staff.total_worked_minutes),
        decimalHours: formatDuration.toDecimalHours(staff.total_worked_minutes),
        isSmallestDuration: staff.total_worked_minutes === this.durationStatistics.min,
        efficiency: this.calculateStaffEfficiency(staff)
      };
    },

    // Calculate staff efficiency
    calculateStaffEfficiency(staff) {
      if (!staff.planned_shifts || staff.planned_shifts === 0) return 0;
      return Math.round((staff.worked_shifts / staff.planned_shifts) * 100);
    }
  },

  // Load data when component mounts
  async mounted() {
    await this.loadDashboardData();
  }
};
```

## 🎨 UI Components & Templates

### 5. Vue.js Template Examples

**Main Dashboard Template:**
```vue
<template>
  <div class="attendance-dashboard">
    <!-- Header Controls -->
    <div class="dashboard-header">
      <h2>Staff Attendance Summary</h2>
      
      <!-- Date Range Picker -->
      <div class="date-controls">
        <input 
          v-model="dateRange.start" 
          type="date" 
          @change="loadDashboardData"
        />
        <span>to</span>
        <input 
          v-model="dateRange.end" 
          type="date" 
          @change="loadDashboardData"
        />
      </div>
      
      <!-- Department Filter -->
      <select v-model="selectedDepartment" @change="loadDashboardData">
        <option value="">All Departments</option>
        <option 
          v-for="dept in availableDepartments" 
          :key="dept.slug"
          :value="dept.slug"
        >
          {{ dept.name }}
        </option>
      </select>
      
      <!-- Status Filter -->
      <select v-model="selectedStatus" @change="loadDashboardData">
        <option value="">All Status</option>
        <option value="active">Active</option>
        <option value="completed">Completed</option>
        <option value="issue">Has Issues</option>
        <option value="no_log">No Log</option>
      </select>
    </div>

    <!-- Performance Metrics Summary -->
    <div class="metrics-summary" v-if="performanceMetrics">
      <div class="metric-card">
        <h3>Smallest Duration</h3>
        <div class="metric-value highlight-smallest">
          {{ performanceMetrics.smallestDuration }}
        </div>
      </div>
      
      <div class="metric-card">
        <h3>Average Duration</h3>
        <div class="metric-value">
          {{ performanceMetrics.averageDuration }}
        </div>
      </div>
      
      <div class="metric-card">
        <h3>Total Work Hours</h3>
        <div class="metric-value">
          {{ performanceMetrics.totalWorkHours }}
        </div>
      </div>
      
      <div class="metric-card">
        <h3>Active Staff</h3>
        <div class="metric-value">
          {{ performanceMetrics.activeStaff }} / {{ performanceMetrics.totalStaff }}
        </div>
      </div>
    </div>

    <!-- View Selector -->
    <div class="view-selector">
      <button 
        :class="{ active: view === 'summary' }"
        @click="view = 'summary'"
      >
        Staff Summary
      </button>
      <button 
        :class="{ active: view === 'departments' }"
        @click="view = 'departments'"
      >
        Department Analytics
      </button>
      <button 
        :class="{ active: view === 'individuals' }"
        @click="view = 'individuals'"
      >
        Individual Rosters
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading attendance data...</p>
    </div>

    <!-- Staff Summary View -->
    <div v-else-if="view === 'summary'" class="staff-summary">
      <div class="staff-grid">
        <div 
          v-for="staff in filteredStaff" 
          :key="staff.id"
          class="staff-card"
          :class="{ 
            'smallest-duration': formatStaffForDisplay(staff).isSmallestDuration,
            'has-issues': staff.issues_count > 0
          }"
        >
          <!-- Staff Avatar -->
          <div class="staff-avatar">
            <img 
              :src="staff.avatar_url || '/default-avatar.png'" 
              :alt="staff.full_name"
            />
          </div>
          
          <!-- Staff Info -->
          <div class="staff-info">
            <h4>{{ staff.full_name }}</h4>
            <p class="department">{{ staff.department_name }}</p>
            
            <!-- Duration Display -->
            <div class="duration-display">
              <span class="duration-label">Work Time:</span>
              <span 
                class="duration-value"
                :class="{ 'smallest': formatStaffForDisplay(staff).isSmallestDuration }"
              >
                {{ formatStaffForDisplay(staff).formattedDuration }}
              </span>
            </div>
            
            <!-- Shifts Info -->
            <div class="shifts-info">
              <span>{{ staff.worked_shifts }}/{{ staff.planned_shifts }} shifts</span>
              <div class="efficiency-bar">
                <div 
                  class="efficiency-fill"
                  :style="{ width: formatStaffForDisplay(staff).efficiency + '%' }"
                ></div>
              </div>
            </div>
          </div>
          
          <!-- Status Badges -->
          <div class="status-badges">
            <span 
              class="badge duty-status"
              :style="{ 
                backgroundColor: staff.duty_status_badge.bg_color,
                color: staff.duty_status_badge.color
              }"
            >
              {{ staff.duty_status_badge.label }}
            </span>
            
            <span 
              class="badge attendance-status"
              :style="{ 
                backgroundColor: staff.attendance_status_badge.bg_color,
                color: staff.attendance_status_badge.color
              }"
            >
              {{ staff.attendance_status_badge.label }}
            </span>
            
            <span v-if="staff.issues_count > 0" class="badge issues">
              {{ staff.issues_count }} issue{{ staff.issues_count > 1 ? 's' : '' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Department Analytics View -->
    <div v-else-if="view === 'departments'" class="department-analytics">
      <div class="department-grid">
        <div 
          v-for="dept in departmentAnalytics" 
          :key="dept.dept_id"
          class="department-card"
        >
          <h3>{{ dept.department_name }}</h3>
          
          <div class="department-stats">
            <div class="stat">
              <label>Total Hours:</label>
              <span>{{ dept.total_rostered_hours.toFixed(1) }}</span>
            </div>
            
            <div class="stat">
              <label>Staff Count:</label>
              <span>{{ dept.unique_staff }}</span>
            </div>
            
            <div class="stat">
              <label>Shifts:</label>
              <span>{{ dept.shifts_count }}</span>
            </div>
            
            <div class="stat highlight">
              <label>Avg Shift:</label>
              <span>{{ formatDuration.toHoursMinutes(dept.avg_shift_length * 60) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Individual Rosters View -->
    <div v-else-if="view === 'individuals'" class="individual-rosters">
      <div class="roster-table">
        <table>
          <thead>
            <tr>
              <th>Staff Name</th>
              <th>Department</th>
              <th>Total Hours</th>
              <th>Shifts</th>
              <th>Avg Shift Length</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="staff in rosterAnalytics" 
              :key="staff.staff_id"
            >
              <td>{{ staff.first_name }} {{ staff.last_name }}</td>
              <td>{{ staff.department_name }}</td>
              <td>{{ staff.total_rostered_hours.toFixed(1) }}</td>
              <td>{{ staff.shifts_count }}</td>
              <td class="avg-shift">
                {{ formatDuration.toHoursMinutes(staff.avg_shift_length * 60) }}
              </td>
              <td>
                <button @click="viewStaffDetails(staff.staff_id)">
                  View Details
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
```

## 📱 Real-time Updates & Notifications

### 6. Live Data Updates

```javascript
// Real-time attendance updates service
const realtimeAttendanceService = {
  // WebSocket connection for live updates
  websocket: null,
  
  // Initialize real-time connection
  connect(hotelSlug) {
    const wsUrl = `wss://your-domain.com/ws/attendance/${hotelSlug}/`;
    this.websocket = new WebSocket(wsUrl);
    
    this.websocket.onopen = () => {
      console.log('Connected to attendance updates');
    };
    
    this.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleAttendanceUpdate(data);
    };
  },
  
  // Handle incoming updates
  handleAttendanceUpdate(data) {
    switch (data.type) {
      case 'staff_clocked_in':
        this.updateStaffStatus(data.staff_id, 'on_duty');
        break;
        
      case 'staff_clocked_out':
        this.updateStaffStatus(data.staff_id, 'off_duty');
        this.updateWorkedMinutes(data.staff_id, data.session_duration);
        break;
        
      case 'roster_updated':
        this.refreshRosterData(data.affected_dates);
        break;
    }
  },
  
  // Update staff status in real-time
  updateStaffStatus(staffId, status) {
    // Update staff status in dashboard
    const staffIndex = this.staffSummaries.findIndex(s => s.id === staffId);
    if (staffIndex !== -1) {
      this.staffSummaries[staffIndex].duty_status = status;
      this.staffSummaries[staffIndex].duty_status_badge = 
        formatDuration.getStatusBadge(status);
    }
  }
};
```

## 🔧 Advanced Features & Optimizations

### 7. Performance Optimizations

```javascript
// Optimized data loading with caching
const dataCache = {
  cache: new Map(),
  
  // Generate cache key
  getCacheKey(endpoint, params) {
    return `${endpoint}_${JSON.stringify(params)}`;
  },
  
  // Get cached data
  get(key) {
    const cached = this.cache.get(key);
    if (!cached) return null;
    
    // Check if cache is still valid (5 minutes)
    const now = Date.now();
    if (now - cached.timestamp > 5 * 60 * 1000) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data;
  },
  
  // Set cache data
  set(key, data) {
    this.cache.set(key, {
      data: data,
      timestamp: Date.now()
    });
  }
};

// Optimized attendance service with caching
const optimizedAttendanceService = {
  // Fetch with caching
  async fetchWithCache(endpoint, params = {}) {
    const cacheKey = dataCache.getCacheKey(endpoint, params);
    const cached = dataCache.get(cacheKey);
    
    if (cached) {
      return cached;
    }
    
    const response = await fetch(endpoint);
    const data = await response.json();
    
    dataCache.set(cacheKey, data);
    return data;
  },
  
  // Batch load multiple endpoints
  async batchLoad(requests) {
    const promises = requests.map(req => 
      this.fetchWithCache(req.endpoint, req.params)
    );
    
    return await Promise.all(promises);
  }
};
```

### 8. Export & Reporting Features

```javascript
// Export attendance data
const exportService = {
  // Export to CSV
  exportToCSV(data, filename) {
    const csvContent = this.convertToCSV(data);
    this.downloadFile(csvContent, filename, 'text/csv');
  },
  
  // Export to Excel
  async exportToExcel(data, filename) {
    // Using SheetJS library
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Attendance Summary');
    XLSX.writeFile(wb, filename);
  },
  
  // Convert data to CSV format
  convertToCSV(data) {
    if (!data.length) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    
    data.forEach(row => {
      const values = headers.map(header => {
        const value = row[header];
        return typeof value === 'string' ? `"${value}"` : value;
      });
      csvRows.push(values.join(','));
    });
    
    return csvRows.join('\n');
  },
  
  // Download file
  downloadFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }
};
```

## 🎯 Complete Implementation Checklist

### ✅ Essential Features to Implement:

1. **Core Dashboard**
   - [ ] Staff attendance summary grid
   - [ ] Department filter dropdown
   - [ ] Date range picker
   - [ ] Status filter (active/completed/issues)
   - [ ] Duration statistics display

2. **Smallest Duration Features**
   - [ ] Calculate smallest worked duration
   - [ ] Highlight staff with smallest shifts
   - [ ] Department comparison for smallest averages
   - [ ] Duration formatting (hours/minutes)

3. **Department Analytics**
   - [ ] Department summary cards
   - [ ] Total hours per department
   - [ ] Average shift length per department
   - [ ] Staff count per department
   - [ ] Department performance comparison

4. **Individual Staff Data**
   - [ ] Individual staff roster summaries
   - [ ] Daily breakdown by staff
   - [ ] Weekly breakdown by staff
   - [ ] Staff performance metrics
   - [ ] Efficiency calculations

5. **Advanced Features**
   - [ ] Real-time updates via WebSocket
   - [ ] Data caching for performance
   - [ ] Export to CSV/Excel
   - [ ] Mobile-responsive design
   - [ ] Loading states and error handling

### 🚀 Getting Started:

1. **Set up the basic dashboard structure**
2. **Implement the attendance summary API calls**
3. **Add duration formatting utilities**
4. **Create department analytics components**
5. **Build individual staff roster views**
6. **Add real-time updates and optimizations**

This comprehensive guide provides everything needed to implement a full-featured staff attendance summary system with smallest duration tracking and complete roster analytics for both departments and individual staff members.