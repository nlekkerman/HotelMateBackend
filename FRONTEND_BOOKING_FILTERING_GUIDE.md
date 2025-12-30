# Frontend Booking List Filtering Guide

## 📊 Main API Endpoint
```
GET /api/staff/hotel/{hotel_slug}/room-bookings/
```
*Used by: Staff frontend for managing hotel bookings*

---

## 🎯 Filter Categories

### 1. Operational Buckets (`bucket=`)
Industry-standard operational filtering:
- **`arrivals`** - Guests checking in (today or date range)
- **`in_house`** - Currently checked-in guests  
- **`departures`** - Guests checking out (today or date range)
- **`pending`** - Bookings awaiting payment/approval
- **`checked_out`** - Completed stays
- **`cancelled`** - Cancelled bookings

### 2. Date Range Filters
- **`date_from=YYYY-MM-DD`** - Start date filter
- **`date_to=YYYY-MM-DD`** - End date filter
- **Legacy**: `start_date`, `end_date` (maintained for compatibility)

### 3. Search Functionality (`q=`)
Searches across multiple fields:
- Booking ID/reference
- Primary guest name (first/last)
- Primary guest email/phone
- Booker name (first/last)
- Booker email/phone

### 4. Boolean Filters
- **`assigned=true|false`** - Room assignment status
- **`precheckin=complete|pending`** - Pre-checkin completion status

### 5. Sorting (`ordering=`)
Available sort options:
- `check_in`, `-check_in`
- `check_out`, `-check_out` 
- `created_at`, `-created_at`
- `booking_id`, `-booking_id`
- `status`, `-status`

---

## 📱 Frontend Usage Examples

```javascript
// Get today's arrivals
const arrivals = await api.get(`/staff/hotel/${hotelSlug}/room-bookings/?bucket=arrivals`);

// Get unassigned bookings pending payment
const unassigned = await api.get(`/staff/hotel/${hotelSlug}/room-bookings/?bucket=pending&assigned=false`);

// Search for guest "John Smith"
const searchResults = await api.get(`/staff/hotel/${hotelSlug}/room-bookings/?q=john`);

// Get departures for date range
const departures = await api.get(`/staff/hotel/${hotelSlug}/room-bookings/?bucket=departures&date_from=2025-12-30&date_to=2025-12-31`);

// Complex filter: Arrivals without room assignment
const complexFilter = await api.get(`/staff/hotel/${hotelSlug}/room-bookings/?bucket=arrivals&assigned=false&ordering=-check_in`);
```

---

## 🔢 Dashboard Count Badges - Correct Implementation

### API Response Structure
When **NO** specific `bucket` parameter is used, the API returns booking counts:

```json
{
  "results": [...],
  "counts": {
    "arrivals": 8,
    "in_house": 15, 
    "departures": 6,
    "pending": 3,
    "checked_out": 12,
    "cancelled": 1
  }
}
```

### ⚠️ CRITICAL: Count Badge Update Rules

#### ✅ DO - Fetch Counts
```javascript
// CORRECT: Fetch counts without bucket filter
const fetchDashboardCounts = async () => {
  const response = await api.get(`/staff/hotel/${hotelSlug}/room-bookings/`);
  return response.data.counts; // { arrivals: 8, in_house: 15, ... }
};
```

#### ❌ DON'T - Fetch Counts with Bucket
```javascript
// WRONG: This will NOT return counts
const response = await api.get(`/staff/hotel/${hotelSlug}/room-bookings/?bucket=arrivals`);
// response.data.counts will be undefined
```

### Frontend Count Badge Implementation

#### 1. Store Structure
```javascript
const bookingStore = {
  counts: {
    arrivals: 0,
    in_house: 0,
    departures: 0,
    pending: 0,
    checked_out: 0,
    cancelled: 0
  },
  countsBadgeLoading: false,
  countsLastUpdated: null
}
```

#### 2. Count Fetching Function
```javascript
const fetchBookingCounts = async (hotelSlug) => {
  try {
    bookingStore.countsBadgeLoading = true;
    
    // IMPORTANT: No bucket parameter to get counts
    const response = await api.get(`/staff/hotel/${hotelSlug}/room-bookings/`);
    
    if (response.data.counts) {
      bookingStore.counts = response.data.counts;
      bookingStore.countsLastUpdated = new Date();
    }
  } catch (error) {
    console.error('Failed to fetch booking counts:', error);
  } finally {
    bookingStore.countsBadgeLoading = false;
  }
};
```

#### 3. React Component Example
```jsx
const BookingDashboard = () => {
  const [counts, setCounts] = useState({
    arrivals: 0,
    in_house: 0,
    departures: 0,
    pending: 0,
    checked_out: 0,
    cancelled: 0
  });
  
  const fetchCounts = useCallback(async () => {
    try {
      // CRITICAL: No bucket parameter
      const response = await api.get(`/staff/hotel/${hotelSlug}/room-bookings/`);
      
      if (response.data.counts) {
        setCounts(response.data.counts);
      }
    } catch (error) {
      console.error('Count fetch failed:', error);
    }
  }, [hotelSlug]);
  
  useEffect(() => {
    fetchCounts();
    
    // Auto-refresh counts every 30 seconds
    const interval = setInterval(fetchCounts, 30000);
    return () => clearInterval(interval);
  }, [fetchCounts]);
  
  return (
    <div className="booking-dashboard">
      <NavButton badge={counts.arrivals}>Arrivals</NavButton>
      <NavButton badge={counts.in_house}>In House</NavButton>
      <NavButton badge={counts.departures}>Departures</NavButton>
      <NavButton badge={counts.pending}>Pending</NavButton>
      <NavButton badge={counts.checked_out}>Checked Out</NavButton>
      <NavButton badge={counts.cancelled}>Cancelled</NavButton>
    </div>
  );
};
```

#### 4. Vue/Nuxt Example
```javascript
// store/booking.js
export const actions = {
  async fetchCounts({ commit }, hotelSlug) {
    try {
      // IMPORTANT: No bucket parameter
      const response = await this.$api.get(`/staff/hotel/${hotelSlug}/room-bookings/`);
      
      if (response.data.counts) {
        commit('SET_COUNTS', response.data.counts);
      }
    } catch (error) {
      console.error('Count fetch failed:', error);
    }
  }
}

// pages/dashboard.vue
export default {
  async mounted() {
    // Fetch initial counts
    await this.$store.dispatch('booking/fetchCounts', this.$route.params.hotelSlug);
    
    // Auto-refresh every 30 seconds
    this.countInterval = setInterval(() => {
      this.$store.dispatch('booking/fetchCounts', this.$route.params.hotelSlug);
    }, 30000);
  },
  
  beforeDestroy() {
    if (this.countInterval) {
      clearInterval(this.countInterval);
    }
  }
}
```

### ⏰ Count Badge Refresh Strategies

#### 1. Auto-Refresh (Recommended)
```javascript
// Refresh counts every 30 seconds
const autoRefreshCounts = (hotelSlug) => {
  setInterval(() => {
    fetchBookingCounts(hotelSlug);
  }, 30000); // 30 seconds
};
```

#### 2. Manual Refresh
```javascript
// Refresh on user action (pull-to-refresh, button click)
const handleRefresh = async () => {
  await fetchBookingCounts(hotelSlug);
  showSuccessMessage('Counts updated');
};
```

#### 3. WebSocket Updates (Advanced)
```javascript
// Real-time updates via WebSocket/Pusher
const subscribeToBookingUpdates = (hotelSlug) => {
  pusher.subscribe(`hotel-${hotelSlug}-bookings`)
    .bind('booking-updated', () => {
      fetchBookingCounts(hotelSlug);
    });
};
```

---

## 🔧 Key Implementation Details

1. **Hotel-Scoped**: All filters automatically scoped to staff member's hotel
2. **Pagination**: Uses `PageNumberPagination` for performance
3. **Optimized Queries**: Uses `select_related()` for efficient database access
4. **Backward Compatible**: Maintains legacy filter parameters
5. **Error Handling**: Validates date formats and filter values
6. **Security**: Requires staff authentication and hotel matching

---

## 🚨 Common Mistakes to Avoid

### ❌ Wrong Count Fetching
```javascript
// WRONG - Using bucket parameter prevents counts
const response = await api.get(`/staff/hotel/${hotelSlug}/room-bookings/?bucket=arrivals`);
console.log(response.data.counts); // undefined
```

### ❌ Wrong Badge Update Logic
```javascript
// WRONG - Don't manually calculate counts
const arrivals = bookings.filter(b => b.bucket === 'arrivals').length; // Inaccurate
```

### ❌ Wrong Auto-Refresh
```javascript
// WRONG - Too frequent updates (performance issue)
setInterval(fetchCounts, 1000); // Every 1 second is too much
```

### ✅ Correct Implementation
```javascript
// CORRECT - Dedicated count endpoint without filters
const response = await api.get(`/staff/hotel/${hotelSlug}/room-bookings/`);
const counts = response.data.counts; // Always accurate server-side counts
```

---

## 🎯 Alternative Endpoints

- **Safe Booking List**: `/api/staff/hotel/{hotel_slug}/room-bookings/safe/` - Additional filtering options
- **Public Booking Detail**: `/api/public/hotel/{hotel_slug}/room-bookings/{booking_id}/` - For external booking lookups

---

## 📋 Frontend Integration Checklist

- [ ] Count badges fetch WITHOUT bucket parameter
- [ ] Auto-refresh counts every 30 seconds
- [ ] Handle count loading states properly
- [ ] Display count badges on navigation tabs
- [ ] Update counts after booking operations (check-in, cancel, etc.)
- [ ] Handle count fetch errors gracefully
- [ ] Cache counts to avoid unnecessary API calls
- [ ] Use real-time updates when available (WebSocket/Pusher)