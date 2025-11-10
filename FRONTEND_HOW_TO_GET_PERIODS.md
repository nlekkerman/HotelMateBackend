# Frontend Guide: How to Get Periods for Comparison

## Step 1: Get Available Closed Periods

**Endpoint:** `GET /stock_tracker/<hotel_identifier>/periods/?is_closed=true`

### Example Request
```javascript
const response = await fetch(
  `${API_BASE_URL}/stock_tracker/hotel-killarney/periods/?is_closed=true`,
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);
const periods = await response.json();
```

### Example Response
```json
[
  {
    "id": 1,
    "period_name": "September 2024",
    "period_type": "MONTHLY",
    "start_date": "2024-09-01",
    "end_date": "2024-09-30",
    "is_closed": true,
    "closed_at": "2024-10-01T10:30:00Z",
    "year": 2024,
    "month": 9
  },
  {
    "id": 2,
    "period_name": "October 2024",
    "period_type": "MONTHLY",
    "start_date": "2024-10-01",
    "end_date": "2024-10-31",
    "is_closed": true,
    "closed_at": "2024-11-01T09:15:00Z",
    "year": 2024,
    "month": 10
  },
  {
    "id": 3,
    "period_name": "November 2024",
    "period_type": "MONTHLY",
    "start_date": "2024-11-01",
    "end_date": "2024-11-30",
    "is_closed": true,
    "closed_at": "2024-12-01T08:45:00Z",
    "year": 2024,
    "month": 11
  }
]
```

## Step 2: Use Period IDs in Comparison Endpoints

### Option A: Compare Multiple Periods (Category Analysis, Trends, Heatmap)

**Format:** `?periods=<id1>,<id2>,<id3>,...`

```javascript
// Get periods array from Step 1
const periodIds = periods.map(p => p.id).join(','); // "1,2,3"

// Compare categories across multiple periods
const categoryComparison = await fetch(
  `${API_BASE_URL}/stock_tracker/hotel-killarney/compare/categories/?periods=${periodIds}`
);

// Trend analysis
const trends = await fetch(
  `${API_BASE_URL}/stock_tracker/hotel-killarney/compare/trend-analysis/?periods=${periodIds}`
);

// Variance heatmap
const heatmap = await fetch(
  `${API_BASE_URL}/stock_tracker/hotel-killarney/compare/variance-heatmap/?periods=${periodIds}`
);
```

### Option B: Compare Two Specific Periods (Top Movers, Cost Analysis, Performance)

**Format:** `?period1=<id1>&period2=<id2>`

```javascript
// Compare last two periods
const period1 = periods[periods.length - 2].id; // Second to last
const period2 = periods[periods.length - 1].id; // Last

// Top movers
const topMovers = await fetch(
  `${API_BASE_URL}/stock_tracker/hotel-killarney/compare/top-movers/?period1=${period1}&period2=${period2}&limit=10`
);

// Cost analysis
const costAnalysis = await fetch(
  `${API_BASE_URL}/stock_tracker/hotel-killarney/compare/cost-analysis/?period1=${period1}&period2=${period2}`
);

// Performance scorecard
const scorecard = await fetch(
  `${API_BASE_URL}/stock_tracker/hotel-killarney/compare/performance-scorecard/?period1=${period1}&period2=${period2}`
);
```

## Complete React Example

```jsx
import { useState, useEffect } from 'react';

function PeriodComparison() {
  const [periods, setPeriods] = useState([]);
  const [selectedPeriods, setSelectedPeriods] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);

  // Step 1: Load available closed periods
  useEffect(() => {
    const loadPeriods = async () => {
      try {
        const response = await fetch(
          '/api/stock_tracker/hotel-killarney/periods/?is_closed=true'
        );
        const data = await response.json();
        setPeriods(data);
        
        // Auto-select last 3 periods
        if (data.length >= 3) {
          setSelectedPeriods(data.slice(-3).map(p => p.id));
        }
      } catch (error) {
        console.error('Failed to load periods:', error);
      }
    };
    
    loadPeriods();
  }, []);

  // Step 2: Load comparison when periods selected
  useEffect(() => {
    const loadComparison = async () => {
      if (selectedPeriods.length < 2) return;
      
      try {
        const periodIds = selectedPeriods.join(',');
        const response = await fetch(
          `/api/stock_tracker/hotel-killarney/compare/categories/?periods=${periodIds}`
        );
        const data = await response.json();
        setComparisonData(data);
      } catch (error) {
        console.error('Failed to load comparison:', error);
      }
    };
    
    loadComparison();
  }, [selectedPeriods]);

  return (
    <div>
      <h2>Period Comparison</h2>
      
      {/* Period Selector */}
      <div className="period-selector">
        <label>Select Periods to Compare (2+):</label>
        <select 
          multiple 
          value={selectedPeriods}
          onChange={(e) => {
            const selected = Array.from(e.target.selectedOptions, opt => Number(opt.value));
            setSelectedPeriods(selected);
          }}
        >
          {periods.map(period => (
            <option key={period.id} value={period.id}>
              {period.period_name} ({period.start_date} to {period.end_date})
            </option>
          ))}
        </select>
      </div>

      {/* Comparison Results */}
      {comparisonData && (
        <div className="comparison-results">
          <h3>Category Comparison</h3>
          {comparisonData.categories.map(cat => (
            <div key={cat.code} className="category-card">
              <h4>{cat.name}</h4>
              {cat.periods_data.map(pd => (
                <div key={pd.period_id}>
                  {pd.period_name}: ${pd.total_value}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

## Vue.js Example

```vue
<template>
  <div>
    <h2>Period Comparison</h2>
    
    <!-- Period Selector -->
    <div class="period-selector">
      <label>Select Periods to Compare (2+):</label>
      <select v-model="selectedPeriods" multiple>
        <option v-for="period in periods" :key="period.id" :value="period.id">
          {{ period.period_name }} ({{ period.start_date }} to {{ period.end_date }})
        </option>
      </select>
    </div>

    <!-- Comparison Results -->
    <div v-if="comparisonData" class="comparison-results">
      <h3>Category Comparison</h3>
      <div v-for="cat in comparisonData.categories" :key="cat.code" class="category-card">
        <h4>{{ cat.name }}</h4>
        <div v-for="pd in cat.periods_data" :key="pd.period_id">
          {{ pd.period_name }}: ${{ pd.total_value }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      periods: [],
      selectedPeriods: [],
      comparisonData: null
    };
  },
  
  async mounted() {
    // Load available closed periods
    const response = await fetch(
      '/api/stock_tracker/hotel-killarney/periods/?is_closed=true'
    );
    this.periods = await response.json();
    
    // Auto-select last 3 periods
    if (this.periods.length >= 3) {
      this.selectedPeriods = this.periods.slice(-3).map(p => p.id);
    }
  },
  
  watch: {
    async selectedPeriods(newVal) {
      if (newVal.length < 2) return;
      
      const periodIds = newVal.join(',');
      const response = await fetch(
        `/api/stock_tracker/hotel-killarney/compare/categories/?periods=${periodIds}`
      );
      this.comparisonData = await response.json();
    }
  }
};
</script>
```

## Vanilla JavaScript Example

```javascript
// Step 1: Load available periods
async function loadPeriods() {
  const response = await fetch(
    '/api/stock_tracker/hotel-killarney/periods/?is_closed=true'
  );
  const periods = await response.json();
  
  // Populate dropdown
  const select = document.getElementById('period-select');
  periods.forEach(period => {
    const option = document.createElement('option');
    option.value = period.id;
    option.textContent = `${period.period_name} (${period.start_date} to ${period.end_date})`;
    select.appendChild(option);
  });
  
  return periods;
}

// Step 2: Compare selected periods
async function compareSelectedPeriods() {
  const select = document.getElementById('period-select');
  const selectedIds = Array.from(select.selectedOptions).map(opt => opt.value);
  
  if (selectedIds.length < 2) {
    alert('Please select at least 2 periods');
    return;
  }
  
  const periodIds = selectedIds.join(',');
  const response = await fetch(
    `/api/stock_tracker/hotel-killarney/compare/categories/?periods=${periodIds}`
  );
  const data = await response.json();
  
  // Display results
  displayComparisonResults(data);
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await loadPeriods();
  
  document.getElementById('compare-btn').addEventListener('click', compareSelectedPeriods);
});
```

## Common Patterns

### 1. Last 3 Months Comparison
```javascript
const periods = await fetchPeriods();
const last3Months = periods.slice(-3).map(p => p.id).join(',');
const comparison = await fetch(`/compare/categories/?periods=${last3Months}`);
```

### 2. Quarter vs Quarter
```javascript
const periods = await fetchPeriods();
const q3 = periods.filter(p => p.quarter === 3 && p.year === 2024);
const q4 = periods.filter(p => p.quarter === 4 && p.year === 2024);

const q3Ids = q3.map(p => p.id).join(',');
const q4Ids = q4.map(p => p.id).join(',');
```

### 3. Month-over-Month
```javascript
const periods = await fetchPeriods();
const currentMonth = periods[periods.length - 1];
const previousMonth = periods[periods.length - 2];

const comparison = await fetch(
  `/compare/top-movers/?period1=${previousMonth.id}&period2=${currentMonth.id}`
);
```

### 4. Year-over-Year
```javascript
const periods = await fetchPeriods();
const currentYear = periods.filter(p => p.year === 2024);
const previousYear = periods.filter(p => p.year === 2023);

const currentIds = currentYear.map(p => p.id).join(',');
const previousIds = previousYear.map(p => p.id).join(',');
```

## Error Handling

```javascript
async function loadComparisonSafely(periodIds) {
  try {
    const response = await fetch(
      `/api/stock_tracker/hotel-killarney/compare/categories/?periods=${periodIds}`
    );
    
    if (!response.ok) {
      const error = await response.json();
      console.error('Comparison failed:', error);
      
      // Show helpful error to user
      if (error.example) {
        alert(`Error: ${error.error}\nExample: ${error.example}\nHint: ${error.hint}`);
      }
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error('Network error:', error);
    return null;
  }
}
```

## Quick Reference

| You Want To... | Endpoint | Parameters |
|----------------|----------|------------|
| Get available periods | `/periods/?is_closed=true` | None |
| Compare categories | `/compare/categories/` | `periods=1,2,3` |
| Find top movers | `/compare/top-movers/` | `period1=1&period2=2` |
| Analyze costs | `/compare/cost-analysis/` | `period1=1&period2=2` |
| View trends | `/compare/trend-analysis/` | `periods=1,2,3,4` |
| See variance heatmap | `/compare/variance-heatmap/` | `periods=1,2,3` |
| Check performance | `/compare/performance-scorecard/` | `period1=1&period2=2` |

## Notes

- ✅ **Always use closed periods** - Open periods will return 404
- ✅ **Minimum 2 periods** required for all comparisons
- ✅ **Multi-period endpoints** accept 2+ periods (no maximum)
- ✅ **Two-period endpoints** only accept exactly 2 periods
- ✅ **Period IDs are integers** - join with commas, no spaces
