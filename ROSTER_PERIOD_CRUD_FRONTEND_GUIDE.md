# 📅 **ROSTER PERIOD CRUD - Complete Frontend Implementation Guide**

## 🎯 **CORE OPERATIONS NOW AVAILABLE**

You now have the **essential roster management functionality** implemented:

### ✅ **1. CREATE ROSTER PERIODS**
- Create weekly periods automatically
- Create custom periods with flexible dates  
- Create periods by copying from existing ones

### ✅ **2. COPY ENTIRE PERIODS**
- Copy complete roster periods to new dates
- Copy with filtering options (departments, staff, locations)
- Automatic conflict detection and prevention

### ✅ **3. DUPLICATE PERIODS**
- Duplicate existing periods with new dates
- Maintains all shift structures and assignments
- Perfect for recurring weekly schedules

---

## 🔧 **API ENDPOINTS REFERENCE**

### **Period Creation**
```typescript
// 1. CREATE WEEKLY PERIOD (Auto Monday-Sunday)
POST /attendance/{hotel_slug}/periods/create-for-week/
{
  "date": "2025-12-15"  // Any date in the target week
}

// 2. CREATE CUSTOM PERIOD (Flexible dates)
POST /attendance/{hotel_slug}/periods/create-custom-period/
{
  "title": "Holiday Period",
  "start_date": "2025-12-20", 
  "end_date": "2025-12-27",
  "copy_from_period": 123  // Optional: copy shifts from existing period
}

// 3. DUPLICATE EXISTING PERIOD
POST /attendance/{hotel_slug}/periods/{period_id}/duplicate-period/
{
  "new_start_date": "2025-12-28",
  "new_title": "Holiday Week 2"  // Optional
}
```

### **Period Copying**
```typescript
// COPY ENTIRE PERIOD TO NEW DATES
POST /attendance/{hotel_slug}/shift-copy/copy-entire-period/
{
  "source_period_id": 123,
  "target_start_date": "2025-12-30",
  "target_title": "New Year Week",           // Optional
  "create_new_period": true,                 // Create target period automatically
  "copy_options": {                          // Optional filtering
    "departments": ["housekeeping", "reception"],
    "staff_ids": [1, 2, 3],
    "locations": [1, 2],
    "exclude_weekends": false
  }
}
```

---

## 🖥️ **FRONTEND COMPONENTS**

### **1. Period Creation Form**
```typescript
interface PeriodCreationForm {
  mode: 'weekly' | 'custom' | 'duplicate';
  
  // For weekly mode
  weekDate?: string;
  
  // For custom mode  
  title?: string;
  startDate?: string;
  endDate?: string;
  copyFromPeriod?: number;
  
  // For duplicate mode
  sourcePeriodId?: number;
  newStartDate?: string;
  newTitle?: string;
}

const PeriodCreationComponent = () => {
  const [mode, setMode] = useState<'weekly' | 'custom' | 'duplicate'>('weekly');
  const [form, setForm] = useState<PeriodCreationForm>({});

  const handleCreateWeekly = async () => {
    const response = await fetch(`/attendance/${hotelSlug}/periods/create-for-week/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date: form.weekDate })
    });
    
    if (response.ok) {
      const period = await response.json();
      console.log('Created weekly period:', period);
      // Refresh period list or navigate to new period
    }
  };

  const handleCreateCustom = async () => {
    const response = await fetch(`/attendance/${hotelSlug}/periods/create-custom-period/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: form.title,
        start_date: form.startDate,
        end_date: form.endDate,
        copy_from_period: form.copyFromPeriod
      })
    });
    
    if (response.ok) {
      const period = await response.json();
      console.log('Created custom period:', period);
    }
  };

  const handleDuplicate = async () => {
    const response = await fetch(
      `/attendance/${hotelSlug}/periods/${form.sourcePeriodId}/duplicate-period/`, 
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_start_date: form.newStartDate,
          new_title: form.newTitle
        })
      }
    );
    
    if (response.ok) {
      const result = await response.json();
      console.log('Duplicated period:', result.period);
      console.log('Shifts copied:', result.shifts_copied);
    }
  };

  return (
    <div className="period-creation-form">
      <div className="mode-selector">
        <button 
          className={mode === 'weekly' ? 'active' : ''}
          onClick={() => setMode('weekly')}
        >
          📅 Create Weekly Period
        </button>
        <button 
          className={mode === 'custom' ? 'active' : ''}
          onClick={() => setMode('custom')}
        >
          🗓️ Create Custom Period
        </button>
        <button 
          className={mode === 'duplicate' ? 'active' : ''}
          onClick={() => setMode('duplicate')}
        >
          📋 Duplicate Period
        </button>
      </div>

      {mode === 'weekly' && (
        <div className="weekly-form">
          <input 
            type="date" 
            value={form.weekDate || ''}
            onChange={(e) => setForm({...form, weekDate: e.target.value})}
            placeholder="Select any date in the target week"
          />
          <button onClick={handleCreateWeekly}>Create Weekly Period</button>
        </div>
      )}

      {mode === 'custom' && (
        <div className="custom-form">
          <input 
            type="text" 
            placeholder="Period Title"
            value={form.title || ''}
            onChange={(e) => setForm({...form, title: e.target.value})}
          />
          <input 
            type="date" 
            placeholder="Start Date"
            value={form.startDate || ''}
            onChange={(e) => setForm({...form, startDate: e.target.value})}
          />
          <input 
            type="date" 
            placeholder="End Date"
            value={form.endDate || ''}
            onChange={(e) => setForm({...form, endDate: e.target.value})}
          />
          <select 
            value={form.copyFromPeriod || ''}
            onChange={(e) => setForm({...form, copyFromPeriod: parseInt(e.target.value)})}
          >
            <option value="">Copy from existing period (optional)</option>
            {existingPeriods.map(period => (
              <option key={period.id} value={period.id}>
                {period.title} ({period.start_date} - {period.end_date})
              </option>
            ))}
          </select>
          <button onClick={handleCreateCustom}>Create Custom Period</button>
        </div>
      )}

      {mode === 'duplicate' && (
        <div className="duplicate-form">
          <select 
            value={form.sourcePeriodId || ''}
            onChange={(e) => setForm({...form, sourcePeriodId: parseInt(e.target.value)})}
          >
            <option value="">Select period to duplicate</option>
            {existingPeriods.map(period => (
              <option key={period.id} value={period.id}>
                {period.title} ({period.start_date} - {period.end_date})
              </option>
            ))}
          </select>
          <input 
            type="date" 
            placeholder="New Start Date"
            value={form.newStartDate || ''}
            onChange={(e) => setForm({...form, newStartDate: e.target.value})}
          />
          <input 
            type="text" 
            placeholder="New Title (optional)"
            value={form.newTitle || ''}
            onChange={(e) => setForm({...form, newTitle: e.target.value})}
          />
          <button onClick={handleDuplicate}>Duplicate Period</button>
        </div>
      )}
    </div>
  );
};
```

### **2. Period Copy Component**
```typescript
interface PeriodCopyOptions {
  departments?: string[];
  staffIds?: number[];
  locations?: number[];
  excludeWeekends?: boolean;
}

const PeriodCopyComponent = () => {
  const [sourcePeriodId, setSourcePeriodId] = useState<number>();
  const [targetStartDate, setTargetStartDate] = useState<string>('');
  const [targetTitle, setTargetTitle] = useState<string>('');
  const [createNewPeriod, setCreateNewPeriod] = useState<boolean>(true);
  const [copyOptions, setCopyOptions] = useState<PeriodCopyOptions>({});

  const handleCopyPeriod = async () => {
    const response = await fetch(`/attendance/${hotelSlug}/shift-copy/copy-entire-period/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_period_id: sourcePeriodId,
        target_start_date: targetStartDate,
        target_title: targetTitle,
        create_new_period: createNewPeriod,
        copy_options: copyOptions
      })
    });

    if (response.ok) {
      const result = await response.json();
      console.log('Copy successful:', result);
      
      // Show success notification
      alert(`Successfully copied ${result.shifts_copied} shifts to ${result.target_period.title}`);
      
      if (result.skipped_shifts?.length > 0) {
        console.warn('Some shifts were skipped:', result.skipped_shifts);
      }
    } else {
      const error = await response.json();
      alert(`Copy failed: ${error.detail}`);
    }
  };

  return (
    <div className="period-copy-form">
      <h3>📋 Copy Entire Period</h3>
      
      <div className="form-group">
        <label>Source Period:</label>
        <select 
          value={sourcePeriodId || ''}
          onChange={(e) => setSourcePeriodId(parseInt(e.target.value))}
        >
          <option value="">Select source period</option>
          {periods.map(period => (
            <option key={period.id} value={period.id}>
              {period.title} ({period.start_date} - {period.end_date})
            </option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>Target Start Date:</label>
        <input 
          type="date" 
          value={targetStartDate}
          onChange={(e) => setTargetStartDate(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Target Period Title:</label>
        <input 
          type="text" 
          value={targetTitle}
          onChange={(e) => setTargetTitle(e.target.value)}
          placeholder="Auto-generated if empty"
        />
      </div>

      <div className="form-group">
        <label>
          <input 
            type="checkbox"
            checked={createNewPeriod}
            onChange={(e) => setCreateNewPeriod(e.target.checked)}
          />
          Create New Period (uncheck to use existing period)
        </label>
      </div>

      <div className="copy-options">
        <h4>Copy Options (Optional Filters)</h4>
        
        <div className="form-group">
          <label>Departments:</label>
          <DepartmentMultiSelect 
            selected={copyOptions.departments || []}
            onChange={(depts) => setCopyOptions({...copyOptions, departments: depts})}
          />
        </div>

        <div className="form-group">
          <label>Staff Members:</label>
          <StaffMultiSelect 
            selected={copyOptions.staffIds || []}
            onChange={(staff) => setCopyOptions({...copyOptions, staffIds: staff})}
          />
        </div>

        <div className="form-group">
          <label>
            <input 
              type="checkbox"
              checked={copyOptions.excludeWeekends || false}
              onChange={(e) => setCopyOptions({...copyOptions, excludeWeekends: e.target.checked})}
            />
            Exclude Weekends
          </label>
        </div>
      </div>

      <button 
        onClick={handleCopyPeriod}
        disabled={!sourcePeriodId || !targetStartDate}
        className="btn-primary"
      >
        Copy Period
      </button>
    </div>
  );
};
```

### **3. Period Management Dashboard**
```typescript
const PeriodManagementDashboard = () => {
  const [periods, setPeriods] = useState<RosterPeriod[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showCopyForm, setShowCopyForm] = useState(false);

  const fetchPeriods = async () => {
    const response = await fetch(`/attendance/${hotelSlug}/periods/`);
    const data = await response.json();
    setPeriods(data);
  };

  useEffect(() => {
    fetchPeriods();
  }, []);

  return (
    <div className="period-management-dashboard">
      <div className="dashboard-header">
        <h2>📅 Roster Period Management</h2>
        
        <div className="action-buttons">
          <button 
            onClick={() => setShowCreateForm(true)}
            className="btn-primary"
          >
            ➕ Create New Period
          </button>
          
          <button 
            onClick={() => setShowCopyForm(true)}
            className="btn-secondary"
          >
            📋 Copy Period
          </button>
        </div>
      </div>

      <div className="periods-grid">
        {periods.map(period => (
          <div key={period.id} className="period-card">
            <div className="period-header">
              <h3>{period.title}</h3>
              <span className={`status ${period.published ? 'published' : 'draft'}`}>
                {period.published ? '🔒 Published' : '📝 Draft'}
              </span>
            </div>
            
            <div className="period-details">
              <p><strong>📅 Period:</strong> {period.start_date} - {period.end_date}</p>
              <p><strong>👤 Created by:</strong> {period.created_by?.name || 'System'}</p>
            </div>

            <div className="period-actions">
              <button 
                onClick={() => navigateToPeriod(period.id)}
                className="btn-view"
              >
                👁️ View Roster
              </button>
              
              <button 
                onClick={() => duplicatePeriod(period.id)}
                className="btn-duplicate"
              >
                📋 Duplicate
              </button>
              
              <button 
                onClick={() => exportPeriodPDF(period.id)}
                className="btn-export"
              >
                📄 Export PDF
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Modal Forms */}
      {showCreateForm && (
        <Modal onClose={() => setShowCreateForm(false)}>
          <PeriodCreationComponent onSuccess={() => {
            setShowCreateForm(false);
            fetchPeriods();
          }} />
        </Modal>
      )}

      {showCopyForm && (
        <Modal onClose={() => setShowCopyForm(false)}>
          <PeriodCopyComponent onSuccess={() => {
            setShowCopyForm(false);
            fetchPeriods();
          }} />
        </Modal>
      )}
    </div>
  );
};
```

---

## 🎨 **UI/UX RECOMMENDATIONS**

### **Quick Actions Bar**
```typescript
const QuickActionsBar = ({ currentPeriod }: { currentPeriod?: RosterPeriod }) => {
  return (
    <div className="quick-actions-bar">
      <button onClick={() => createWeeklyPeriod(getNextWeekDate())}>
        ⚡ Create Next Week
      </button>
      
      {currentPeriod && (
        <button onClick={() => duplicateCurrentPeriod(currentPeriod)}>
          📋 Duplicate This Week
        </button>
      )}
      
      <button onClick={() => copyFromLastWeek()}>
        ↩️ Copy From Last Week
      </button>
    </div>
  );
};
```

### **Period Timeline View**
```typescript
const PeriodTimeline = ({ periods }: { periods: RosterPeriod[] }) => {
  return (
    <div className="period-timeline">
      {periods.map(period => (
        <div key={period.id} className="timeline-item">
          <div className="timeline-marker"></div>
          <div className="timeline-content">
            <h4>{period.title}</h4>
            <span>{period.start_date} - {period.end_date}</span>
            <div className="period-stats">
              {/* Show shift counts, staff counts, etc. */}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
```

---

## ⚡ **COMMON WORKFLOWS**

### **1. Weekly Roster Creation**
```typescript
// Create next week's roster by copying this week
const createNextWeekRoster = async (currentPeriodId: number) => {
  // 1. Get next Monday's date  
  const nextMonday = getNextMonday();
  
  // 2. Copy entire period to next week
  const response = await fetch(`/attendance/${hotelSlug}/shift-copy/copy-entire-period/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_period_id: currentPeriodId,
      target_start_date: nextMonday,
      create_new_period: true
    })
  });
  
  if (response.ok) {
    const result = await response.json();
    alert(`✅ Created next week's roster with ${result.shifts_copied} shifts!`);
  }
};
```

### **2. Holiday Period Setup**
```typescript
// Create a custom period for holidays
const createHolidayPeriod = async () => {
  // 1. Create custom period
  const periodResponse = await fetch(`/attendance/${hotelSlug}/periods/create-custom-period/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: "Christmas Holiday Period",
      start_date: "2025-12-23",
      end_date: "2025-12-29"
    })
  });
  
  if (periodResponse.ok) {
    const period = await periodResponse.json();
    
    // 2. Copy shifts from a template period (optional)
    await fetch(`/attendance/${hotelSlug}/shift-copy/copy-entire-period/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_period_id: templatePeriodId,
        target_start_date: "2025-12-23",
        create_new_period: false, // Use the period we just created
        copy_options: {
          exclude_weekends: false // Include weekends for holiday coverage
        }
      })
    });
  }
};
```

### **3. Department-Only Copy**
```typescript
// Copy only housekeeping shifts to new period
const copyDepartmentOnly = async (sourcePeriodId: number, targetDate: string) => {
  const response = await fetch(`/attendance/${hotelSlug}/shift-copy/copy-entire-period/`, {
    method: 'POST', 
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_period_id: sourcePeriodId,
      target_start_date: targetDate,
      create_new_period: true,
      copy_options: {
        departments: ["housekeeping"], // Only copy housekeeping
        exclude_weekends: true         // Skip weekends
      }
    })
  });
  
  const result = await response.json();
  console.log(`Copied ${result.shifts_copied} housekeeping shifts`);
};
```

---

## 🚀 **YOU NOW HAVE COMPLETE ROSTER CRUD!**

✅ **Create** - Weekly, custom, and duplicate periods  
✅ **Read** - List and view all periods with filters  
✅ **Update** - Edit period details and individual shifts  
✅ **Delete** - Remove periods and bulk shift operations  
✅ **Copy** - Complete period copying with advanced options  

This gives you the **core functionality** needed for professional roster management! 🎉