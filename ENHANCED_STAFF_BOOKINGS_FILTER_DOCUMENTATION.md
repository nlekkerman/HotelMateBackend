# Enhanced Staff Bookings Filter Implementation

## Overview
Added industry-standard operational bucket filtering to the existing `StaffBookingsListView` endpoint at:
- **Endpoint**: `/api/staff/hotels/{hotel_slug}/room-bookings/`
- **Method**: GET

## Query Parameters

### 1. Operational Buckets (`bucket=`)
Filter bookings by operational status categories:

- **`arrivals`**: Bookings with check-in today (or date range), not checked in, status CONFIRMED/PENDING_APPROVAL
- **`in_house`**: Currently checked in guests (checked_in_at NOT NULL, checked_out_at NULL)  
- **`departures`**: Bookings with check-out today (or date range), not checked out
- **`pending`**: Bookings awaiting payment or approval (PENDING_PAYMENT/PENDING_APPROVAL)
- **`checked_out`**: Checked out guests or COMPLETED status
- **`cancelled`**: Cancelled bookings

### 2. Date Filters
- **`date_from=YYYY-MM-DD`**: Start date for arrivals/departures (defaults to today)
- **`date_to=YYYY-MM-DD`**: End date for arrivals/departures (defaults to today)

### 3. Search (`q=`)
Text search across:
- Booking ID / reference
- Primary guest name (first/last)
- Primary guest email/phone
- Booker name (first/last)  
- Booker email/phone

### 4. Boolean Filters
- **`assigned=true|false`**: Filter by room assignment status
- **`precheckin=complete|pending`**: Filter by precheckin completion status

### 5. Ordering (`ordering=`)
- `check_in`, `-check_in`
- `check_out`, `-check_out`  
- `created_at`, `-created_at`
- `booking_id`, `-booking_id`
- `status`, `-status`

Default: `-created_at` (newest first)

### 6. Legacy Parameters (Backwards Compatibility)
- `status`: Filter by booking status
- `start_date`: Filter check-in >= date
- `end_date`: Filter check-out <= date

## Example Requests

```bash
# Today's arrivals
GET /api/staff/hotels/myhotel/room-bookings/?bucket=arrivals

# Arrivals for date range
GET /api/staff/hotels/myhotel/room-bookings/?bucket=arrivals&date_from=2025-12-29&date_to=2025-12-31

# Currently in-house guests
GET /api/staff/hotels/myhotel/room-bookings/?bucket=in_house

# Search for guest named "John"
GET /api/staff/hotels/myhotel/room-bookings/?q=john

# Unassigned pending bookings
GET /api/staff/hotels/myhotel/room-bookings/?bucket=pending&assigned=false

# Complex filter: Arrivals without room assignment, search "Smith"
GET /api/staff/hotels/myhotel/room-bookings/?bucket=arrivals&assigned=false&q=smith
```

## Response Format

### Standard Response
```json
{
  "count": 45,
  "next": "http://...",
  "previous": null,
  "results": [
    {
      "booking_id": "BK-2025-1234",
      "status": "CONFIRMED",
      "check_in": "2025-12-29",
      "check_out": "2025-12-31",
      "assigned_room_number": "101",
      "primary_email": "guest@email.com",
      // ... other booking fields
    }
  ]
}
```

### Response with Bucket Counts (when no bucket specified)
```json
{
  "count": 45,
  "next": "http://...",
  "previous": null,
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

## Implementation Details

### Key Features
- ✅ **Additive only**: No breaking changes to existing logic
- ✅ **Backwards compatible**: All legacy parameters still work
- ✅ **Efficient queries**: Uses Django Q objects with proper indexing
- ✅ **Hotel-scoped**: Respects existing hotel filtering  
- ✅ **Paginated**: Maintains existing pagination behavior
- ✅ **Safe aggregates**: Bucket counts only computed when safe

### Bucket Logic Implementation
Uses existing `RoomBooking` model fields - no schema changes required:

```python
# arrivals
Q(check_in__gte=start_dt) & Q(check_in__lte=end_dt) &
Q(checked_in_at__isnull=True) &
Q(status__in=['CONFIRMED', 'PENDING_APPROVAL'])

# in_house  
Q(checked_in_at__isnull=False) & Q(checked_out_at__isnull=True)

# departures
Q(check_out__gte=start_dt) & Q(check_out__lte=end_dt) &
Q(checked_out_at__isnull=True)

# pending
Q(status__in=['PENDING_PAYMENT', 'PENDING_APPROVAL'])

# checked_out
Q(checked_out_at__isnull=False) | Q(status='COMPLETED')

# cancelled
Q(status='CANCELLED')
```

### Error Handling
- Invalid bucket names return 400 Bad Request
- Invalid date formats return 400 Bad Request with clear messages
- Database errors are handled gracefully
- Bucket counts fail silently if unsafe to compute

## Frontend Integration Examples

```javascript
// Get today's arrivals
const arrivals = await api.get(`/staff/hotels/${hotelSlug}/room-bookings/?bucket=arrivals`);

// Get unassigned pending bookings
const unassigned = await api.get(`/staff/hotels/${hotelSlug}/room-bookings/?bucket=pending&assigned=false`);

// Search across all bookings
const searchResults = await api.get(`/staff/hotels/${hotelSlug}/room-bookings/?q=${searchTerm}`);

// Get dashboard counts
const dashboard = await api.get(`/staff/hotels/${hotelSlug}/room-bookings/`);
console.log(dashboard.counts); // { arrivals: 8, in_house: 15, departures: 6, pending: 3, checked_out: 12, cancelled: 1 }
```

## Performance Notes
- Queries use existing database indexes
- Bucket counts only computed for dashboard view (no bucket parameter)
- Search uses `icontains` which is reasonably efficient for typical datasets
- Pagination prevents large result sets from impacting performance

## Testing
All existing functionality preserved. Test with:
- Legacy parameters (status, start_date, end_date)
- New bucket filtering
- Combined filters
- Edge cases (invalid dates, unknown buckets)
- Empty result sets
- Large result sets with pagination