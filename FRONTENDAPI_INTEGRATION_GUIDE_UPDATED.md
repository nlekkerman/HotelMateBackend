# Frontend API Integration Guide: Precheckin Data & Individual Nationality

## 🎯 Objective
Define correct API contracts for staff and guest flows to detect precheckin completion, retrieve individual nationality data, and integrate with booking details.

## ⚠️ CRITICAL: Staff vs Guest API Separation
- **Staff flows**: Must use staff endpoints only - NO precheckin tokens or public endpoints
- **Guest flows**: Use public precheckin endpoints with tokens
- **Completion detection**: Use `precheckin_submitted_at != null` as single source of truth

## ✅ Current Status
- **Backend**: Nationality data saved per guest in `precheckin_payload` ✅
- **Admin**: Individual nationality display for each party member ✅ 
- **Staff API**: Exposes precheckin data in staff booking endpoints ✅
- **Guest API**: Public precheckin endpoints work with tokens ✅

## 🔍 Precheckin Completion Detection (STANDARDIZED)

### Single Source of Truth
```javascript
// ✅ CORRECT: Use precheckin_submitted_at as single completion indicator
const isPrecheckinComplete = (bookingData) => {
  return bookingData.precheckin_submitted_at != null;
};

// ✅ STAFF USAGE: From staff booking endpoints
const staffBookingData = await fetchStaffBooking(bookingId);
if (isPrecheckinComplete(staffBookingData)) {
  console.log('✅ Precheckin completed:', staffBookingData.precheckin_submitted_at);
} else {
  console.log('⏳ Precheckin not submitted yet');
}

// ✅ GUEST USAGE: From public precheckin endpoints
const guestPrecheckinData = await fetchGuestPrecheckin(token);
if (isPrecheckinComplete(guestPrecheckinData.booking)) {
  console.log('✅ Precheckin completed:', guestPrecheckinData.booking.precheckin_submitted_at);
}
```

## 📡 API Response Structures

### 🔵 Staff API Endpoints (NO TOKENS)

**Staff Booking List**
**GET** `/api/staff/bookings/` or `/api/staff/hotel/{hotel_id}/bookings/`

```json
{
  "results": [
    {
      "booking_id": "BK-2025-0012",
      "precheckin_submitted_at": "2025-12-19T11:05:46Z",
      "party_complete": true,
      "party_missing_count": 0,
      "primary_guest_name": "Nikola Simic",
      "check_in": "2025-12-18",
      "status": "CONFIRMED"
    }
  ]
}
```

**Staff Booking Detail**
**GET** `/api/staff/bookings/{booking_id}/`

```json
{
  "booking_id": "BK-2025-0012",
  "check_in": "2025-12-18",
  "check_out": "2025-12-26",
  "room_type_name": "Executive Suite",
  "hotel_name": "Hotel Killarney",
  "precheckin_submitted_at": "2025-12-19T11:05:46Z",
  "precheckin_payload": {
    "special_requests": "Early check-in please",
    "eta": "14:00",
    "consent_checkbox": true
  },
  "party": {
    "primary": {
      "id": 123,
      "role": "PRIMARY",
      "first_name": "Nikola",
      "last_name": "Simic", 
      "email": "nlekkerman@gmail.com",
      "phone": "0830945102",
      "is_staying": true,
      "precheckin_payload": {
        "nationality": "Afghanistan",
        "country_of_residence": "Serbia"
      }
    },
    "companions": [{
      "id": 124,
      "role": "COMPANION", 
      "first_name": "Sanja",
      "last_name": "Majsec",
      "email": "sa@mail.com", 
      "phone": "001122323",
      "is_staying": true,
      "precheckin_payload": {
        "nationality": "Afghanistan",
        "country_of_residence": "Belarus"
      }
    }]
  },
  "party_complete": true,
  "party_missing_count": 0
}
```

### 🟢 Guest API Endpoints (WITH TOKENS)

**Guest Precheckin Validation**
**GET** `/api/public/hotel/{hotel_slug}/precheckin/?token={token}`

```json
{
  "booking": {
    "id": "BK-2025-0012",
    "check_in": "2025-12-18",
    "check_out": "2025-12-26",
    "precheckin_submitted_at": "2025-12-19T11:05:46Z",
    "precheckin_payload": {
      "special_requests": "Early check-in please",
      "eta": "14:00"
    }
  },
  "party": {
    "primary": {
      "id": 123,
      "first_name": "Nikola",
      "last_name": "Simic",
      "precheckin_payload": {
        "nationality": "Afghanistan",
        "country_of_residence": "Serbia"
      }
    },
    "companions": [{
      "id": 124,
      "first_name": "Sanja",
      "last_name": "Majsec",
      "precheckin_payload": {
        "nationality": "Afghanistan",
        "country_of_residence": "Belarus"
      }
    }]
  },
  "precheckin_config": {
    "enabled": {"nationality": true, "eta": true},
    "required": {"consent_checkbox": true}
  },
  "precheckin_field_registry": {
    "nationality": {
      "label": "Nationality", 
      "type": "select",
      "scope": "guest",
      "choices": ["Afghanistan", "Albania", "..."]
    }
  }
}
```

## 🔧 Frontend Implementation

### 1. Staff: Fill Booking Details with Precheckin Data

```javascript
// ✅ STAFF: Update booking details from staff API response
const fillStaffBookingWithPrecheckin = (staffBookingData, setBookingDetails) => {
  if (!isPrecheckinComplete(staffBookingData)) {
    console.log('No precheckin data to fill');
    return;
  }
  
  // Extract booking-level precheckin data from canonical location
  const bookingUpdates = {
    special_requests: staffBookingData.precheckin_payload?.special_requests || '',
    eta: staffBookingData.precheckin_payload?.eta || '',
    consent_confirmed: staffBookingData.precheckin_payload?.consent_checkbox || false,
  };
  
  // Extract guest information for booking contact details
  const primary = staffBookingData.party.primary;
  if (primary) {
    bookingUpdates.primary_guest = {
      name: `${primary.first_name} ${primary.last_name}`,
      email: primary.email,
      phone: primary.phone,
      nationality: primary.precheckin_payload?.nationality || '',
      residence: primary.precheckin_payload?.country_of_residence || '',
    };
  }
  
  // Add party info from staff API
  bookingUpdates.party_size = 1 + (staffBookingData.party.companions?.length || 0);
  bookingUpdates.party_complete = staffBookingData.party_complete;
  bookingUpdates.party_missing_count = staffBookingData.party_missing_count;
  
  // Update booking details state
  setBookingDetails(prevDetails => ({
    ...prevDetails,
    ...bookingUpdates,
    precheckin_completed: true,
    precheckin_submitted_at: staffBookingData.precheckin_submitted_at
  }));
  
  console.log('✅ Staff booking details filled from precheckin data');
};

// ✅ STAFF USAGE: Single endpoint contains everything
useEffect(() => {
  const loadStaffBookingData = async () => {
    try {
      // Staff booking detail includes all precheckin data
      const staffBookingData = await fetchStaffBooking(bookingId);
      setBookingDetails(staffBookingData);
      
      // Fill precheckin data if available (no separate API call needed)
      fillStaffBookingWithPrecheckin(staffBookingData, setBookingDetails);
    } catch (error) {
      console.error('Failed to load staff booking data:', error);
    }
  };
  
  loadStaffBookingData();
}, [bookingId]);
```

### 2. Guest: Fill Precheckin Form with Existing Data

```javascript
// ✅ GUEST: Load and populate precheckin form
const fillGuestPrecheckinForm = async (token) => {
  try {
    const guestData = await fetchGuestPrecheckin(token);
    
    if (isPrecheckinComplete(guestData.booking)) {
      // Pre-populate form with existing data
      populateFormFromGuestData(guestData);
    }
  } catch (error) {
    console.error('Failed to load guest precheckin data:', error);
  }
};
```

### 3. Extract Guest Data from API Responses

```javascript
// Extract guest data from either API response format
const extractGuestData = (apiResponse) => {
  const { party } = apiResponse;
  
  // ✅ Guest-scoped fields are ALWAYS in guest.precheckin_payload
  const primaryNationality = party.primary?.precheckin_payload?.nationality || '';
  const primaryCountryRes = party.primary?.precheckin_payload?.country_of_residence || '';
  
  // Get companion nationalities from their individual precheckin_payload
  const companionData = party.companions?.map(companion => ({
    id: companion.id,
    name: `${companion.first_name} ${companion.last_name}`,
    nationality: companion.precheckin_payload?.nationality || '',
    country_of_residence: companion.precheckin_payload?.country_of_residence || ''
  })) || [];
  
  return {
    primary: {
      nationality: primaryNationality,
      country_of_residence: primaryCountryRes
    },
    companions: companionData
  };
};

// Extract booking-scoped fields from canonical location
const extractBookingData = (apiResponse) => {
  // ✅ Booking-scoped fields from booking.precheckin_payload
  const precheckinPayload = apiResponse.precheckin_payload || {};
  
  return {
    special_requests: precheckinPayload.special_requests || '',
    eta: precheckinPayload.eta || '',
    consent_checkbox: precheckinPayload.consent_checkbox || false
  };
};
```

### 4. Pre-populate Form Fields (GUEST ONLY)
```javascript
// ⚠️ GUEST FLOW ONLY: Pre-populate precheckin form with existing data
const loadGuestPrecheckinData = async (token) => {
  // ✅ Use guest precheckin endpoint with token
  const response = await fetch(`/api/public/hotel/${hotelSlug}/precheckin/?token=${token}`);
  const data = await response.json();
  
  const guestData = extractGuestData(data);
  const bookingData = extractBookingData(data.booking);
  
  // Set primary guest state from guest API
  setPartyPrimary(prev => ({
    ...prev,
    first_name: data.party.primary?.first_name || '',
    last_name: data.party.primary?.last_name || '',
    email: data.party.primary?.email || '',
    phone: data.party.primary?.phone || '',
    nationality: guestData.primary.nationality,
    country_of_residence: guestData.primary.country_of_residence
  }));
  
  // Set companion states from guest API
  const updatedCompanions = data.party.companions?.map((companion, index) => ({
    first_name: companion.first_name || '',
    last_name: companion.last_name || '',
    email: companion.email || '',
    phone: companion.phone || '',
    nationality: guestData.companions[index]?.nationality || '',
    country_of_residence: guestData.companions[index]?.country_of_residence || ''
  })) || [];
  
  setCompanionSlots(updatedCompanions);
  
  // Set booking-level fields
  setBookingFields(bookingData);
};
```

### 5. Display Nationality in Form
```jsx
// In PrimaryGuestCard component
const PrimaryGuestCard = ({ values, onChange, errors, precheckinData }) => {
  const handleFieldChange = (fieldKey, value) => {
    onChange('primary', {
      ...values.primary,
      [fieldKey]: value
    });
  };

  return (
    <Card>
      <Card.Header>Primary Guest</Card.Header>
      <Card.Body>
        {/* Existing fields: first_name, last_name, email, phone */}
        
        {/* Guest-scoped fields (nationality, etc.) */}
        {renderGuestScopedFields()}
      </Card.Body>
    </Card>
  );
  
  const renderGuestScopedFields = () => {
    const { precheckin_field_registry: registry, precheckin_config: config } = precheckinData || {};
    if (!registry || !config) return null;

    return Object.entries(registry)
      .filter(([fieldKey, meta]) => 
        config.enabled[fieldKey] === true && meta.scope === 'guest'
      )
      .map(([fieldKey, meta]) => (
        <Form.Group key={fieldKey} className="mb-3">
          <Form.Label>
            {meta.label}
            {config.required[fieldKey] && <span className="text-danger"> *</span>}
          </Form.Label>
          <Form.Select
            value={values.primary?.[fieldKey] || ''}
            onChange={(e) => handleFieldChange(fieldKey, e.target.value)}
            isInvalid={!!errors[fieldKey]}
            required={config.required[fieldKey]}
          >
            <option value="">-- Select {meta.label} --</option>
            {meta.choices?.map((choice, index) => (
              <option key={index} value={choice}>
                {choice}
              </option>
            ))}
          </Form.Select>
          {values.primary?.[fieldKey] && (
            <Form.Text className="text-muted">
              Current: {values.primary[fieldKey]}
            </Form.Text>
          )}
        </Form.Group>
      ));
  };
};
```

### 6. Show Pre-filled Data
```jsx
// Show existing nationality data to user
const NationalityStatus = ({ guestData }) => {
  if (!guestData.primary.nationality && !guestData.companions.some(c => c.nationality)) {
    return null;
  }

  return (
    <Alert variant="info">
      <Alert.Heading>Previously Submitted Nationalities</Alert.Heading>
      <ul className="mb-0">
        {guestData.primary.nationality && (
          <li><strong>Primary Guest:</strong> {guestData.primary.nationality}</li>
        )}
        {guestData.companions.map((companion, index) => 
          companion.nationality && (
            <li key={index}>
              <strong>Companion {index + 1}:</strong> {companion.nationality}
            </li>
          )
        )}
      </ul>
    </Alert>
  );
};
```

## 🧪 Testing & Verification

### 1. API Response Check
```javascript
// Console log to verify API response
console.log('🌍 Primary nationality:', data.party.primary?.precheckin_payload?.nationality);
console.log('🌍 Companion nationalities:', 
  data.party.companions?.map(c => c.precheckin_payload?.nationality)
);
```

### 2. Form Pre-population Check
```javascript
// Verify form fields are pre-populated
console.log('📋 Primary form nationality:', values.primary?.nationality);
console.log('📋 Companion form nationalities:', 
  companionSlots.map(c => c.nationality)
);
```

### 3. Display Precheckin Status in Staff Booking Details
```jsx
// Component to show precheckin completion status in staff view
const StaffPrecheckinStatus = ({ bookingDetails }) => {
  const { precheckin_submitted_at, primary_guest, party_complete } = bookingDetails;
  
  if (!precheckin_submitted_at) {
    return (
      <Alert variant="warning">
        <Alert.Heading>⏳ Pre-check-in Pending</Alert.Heading>
        <p>Guest has not completed pre-check-in yet.</p>
      </Alert>
    );
  }
  
  return (
    <Alert variant="success">
      <Alert.Heading>✅ Pre-check-in Completed</Alert.Heading>
      <Row>
        <Col md={6}>
          <strong>Primary Guest:</strong> {primary_guest?.name}<br/>
          <strong>Nationality:</strong> {primary_guest?.nationality}<br/>
          <strong>Email:</strong> {primary_guest?.email}
        </Col>
        <Col md={6}>
          <strong>Party Complete:</strong> {party_complete ? '✅ Yes' : '⚠️ Missing guests'}<br/>
          <strong>Special Requests:</strong> {bookingDetails.special_requests || 'None'}<br/>
          <strong>Completed:</strong> {new Date(precheckin_submitted_at).toLocaleDateString()}
        </Col>
      </Row>
    </Alert>
  );
};
```

### 4. Backend Verification Methods
```javascript
// Method 1: Check staff API response flags
const checkStaffPrecheckinStatus = (staffBookingData) => {
  return {
    completed: staffBookingData.precheckin_submitted_at != null,
    submitted_at: staffBookingData.precheckin_submitted_at,
    party_complete: staffBookingData.party_complete,
    has_guest_data: staffBookingData.party?.primary?.precheckin_payload != null
  };
};

// Method 2: Check Django admin
// - Go to Hotel > Room Bookings > [Booking ID]
// - Look for "Pre-check-in: ✅ Completed" status
// - Check "Booking Party" table for nationality data

// Method 3: Database verification
// - BookingGuest.precheckin_payload contains nationality data ✅
// - RoomBooking.precheckin_submitted_at shows completion timestamp ✅
```

## 🚀 Expected User Experience

### For Staff/Admin (Booking Details View) ✅ Ready
- **No Precheckin**: Shows "Pre-check-in Pending" warning with timestamp
- **Completed Precheckin**: Shows guest details, nationality, party info automatically filled from staff API
- **Updated Info**: Staff booking details reflect latest precheckin data without tokens
- **Individual Nationality**: Each guest's nationality displayed from `precheckin_payload`

### For Guests (Precheckin Form)
- **First Visit**: Empty form, all fields need to be filled
- **Return Visit**: Form pre-populated with previous selections from guest API
- **Edit Mode**: Can modify previously submitted data

## 📋 Implementation Checklist

### Staff Implementation
- [ ] Use `precheckin_submitted_at != null` as single completion check
- [ ] Call staff booking endpoints only (no tokens)
- [ ] Read guest nationality from `party.*.precheckin_payload`
- [ ] Read booking data from `booking.precheckin_payload`
- [ ] Display precheckin status in staff booking views

### Guest Implementation  
- [ ] Use guest precheckin endpoints with tokens
- [ ] Pre-populate form fields from existing `precheckin_payload` data
- [ ] Allow guests to edit existing precheckin data
- [ ] Show completion status in guest precheckin form

### Backend Requirements (COMPLETED ✅)
- [x] Staff booking list includes `precheckin_submitted_at`
- [x] Staff booking detail includes `precheckin_payload` (booking-scoped)
- [x] Staff booking detail includes `party.*.precheckin_payload` (guest-scoped)
- [x] Booking-scoped fields moved to `precheckin_payload` canonical location

### Status Display
- [ ] Add precheckin status alerts (pending/completed) based on timestamp
- [ ] Show guest nationality in booking summaries from staff API
- [ ] Display completion timestamps and party details without tokens

### Verification ✅
- [x] Backend staff serializers updated with precheckin fields
- [x] Staff booking list includes `precheckin_submitted_at` for badges
- [x] Staff booking detail includes booking and guest precheckin data
- [x] Individual nationality working: Afghanistan nationality confirmed in testing
- [x] Completion detection standardized: `precheckin_submitted_at != null` only

## 🎯 Result

### Staff/Admin Benefits:
1. **Single API endpoint** contains all precheckin data (no tokens needed) ✅
2. **Clear completion status** based on `precheckin_submitted_at` timestamp ✅
3. **Guest nationality visible** from staff booking detail API ✅
4. **Real-time data sync** between precheckin and staff booking systems ✅
5. **Individual per-guest nationality** from each guest's `precheckin_payload` ✅

### Guest Benefits:
1. **Form pre-population** with previously entered data from guest API
2. **Individual nationality** per guest stored in `precheckin_payload`
3. **Edit capability** for correcting mistakes
4. **Persistent data** across form sessions

### System Integration:
1. **Standardized completion detection** using timestamp only
2. **API separation** - staff endpoints vs guest endpoints with tokens
3. **Canonical data locations** - `booking.precheckin_payload` and `guest.precheckin_payload`
4. **Complete data flow** from guest submission to staff view

**Backend Status: ✅ COMPLETE** - Staff API endpoints now include all precheckin data without tokens!