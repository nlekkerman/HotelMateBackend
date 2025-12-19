# Frontend API Integration Guide: Precheckin Data & Individual Nationality

## 🎯 Objective
Define correct API contracts for staff and guest flows to detect precheckin completion, retrieve individual nationality data, and integrate with booking details.

## ⚠️ CRITICAL: Staff vs Guest API Separation
- **Staff flows**: Must use staff endpoints only - NO precheckin tokens or public endpoints
- **Guest flows**: Use public precheckin endpoints with tokens
- **Completion detection**: Use `precheckin_submitted_at != null` as single source of truth

## ✅ Current Status
- **Backend**: Nationality data saved per guest in `precheckin_payload`
- **Admin**: Individual nationality display for each party member  
- **Staff API**: Must expose precheckin data in staff booking endpoints
- **Guest API**: Public precheckin endpoints work with tokens

## � Detecting Precheckin Completion

### How to Know if Precheckin Data Exists

```javascript
// Check if precheckin is completed
const isPrecheckinComplete = (apiResponse) => {
  const { party, booking } = apiResponse;
  
  // Method 1: Check if any guest has precheckin data
  const hasGuestData = party.primary?.precheckin_payload || 
    party.companions?.some(c => c.precheckin_payload && Object.keys(c.precheckin_payload).length > 0);
    
  // Method 2: Check booking-level completion flag (if available)
  const bookingComplete = booking.precheckin_complete || false;
  
  // Method 3: Check submitted timestamp (if available) 
  const hasSubmissionDate = booking.precheckin_submitted_at != null;
  
  return hasGuestData || bookingComplete || hasSubmissionDate;
};

// Usage
const data = await fetchPrecheckinData(token);
if (isPrecheckinComplete(data)) {
  console.log('✅ Precheckin data exists - can fill booking details');
} else {
  console.log('⏳ No precheckin data yet');
}
```

## 📡 API Response Structure

### Validation Endpoint
**GET** `/api/public/hotel/{hotel_slug}/precheckin/?token={token}`

**Complete Response Structure:**
```json
{
  "booking": {
    "id": "BK-2025-0012",
    "check_in": "2025-12-18",
    "check_out": "2025-12-26",
    "room_type_name": "Executive Suite",
    "hotel_name": "Hotel Killarney",
    "special_requests": "Early check-in please",
    "precheckin_complete": true,
    "precheckin_submitted_at": "2025-12-19T11:05:46Z"
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
  "precheckin_config": {
    "enabled": {"nationality": true, "eta": true, ...},
    "required": {"consent_checkbox": true, ...}
  },
  "precheckin_field_registry": {
    "nationality": {
      "label": "Nationality", 
      "type": "select",
      "scope": "guest",
      "choices": ["Afghanistan", "Albania", ...]
    }
  }
}
```

## 🔧 Frontend Implementation

### 1. Fill Booking Details with Precheckin Data

```javascript
// Update booking details automatically with precheckin data
const fillBookingDetailsFromPrecheckin = (apiResponse, setBookingDetails) => {
  const { booking, party } = apiResponse;
  
  if (!isPrecheckinComplete(apiResponse)) {
    console.log('No precheckin data to fill');
    return;
  }
  
  // Extract booking-level data from booking object
  const bookingUpdates = {
    special_requests: booking.special_requests || '',
    eta: booking.eta || '', // If available in booking response
  };
  
  // Extract guest information for booking contact details
  const primary = party.primary;
  if (primary) {
    bookingUpdates.primary_guest = {
      name: `${primary.first_name} ${primary.last_name}`,
      email: primary.email,
      phone: primary.phone,
      nationality: primary.precheckin_payload?.nationality || '',
    };
  }
  
  // Add companion info for booking reference
  bookingUpdates.party_size = 1 + (party.companions?.length || 0);
  bookingUpdates.companions_count = party.companions?.length || 0;
  
  // Update booking details state
  setBookingDetails(prevDetails => ({
    ...prevDetails,
    ...bookingUpdates,
    precheckin_completed: true,
    last_updated: new Date().toISOString()
  }));
  
  console.log('✅ Booking details filled from precheckin data');
};

// Usage in booking details component
useEffect(() => {
  const loadBookingWithPrecheckin = async () => {
    try {
      const data = await fetchBookingData(bookingId);
      setBookingDetails(data);
      
      // If booking has precheckin token, try to get precheckin data
      if (data.precheckin_token) {
        const precheckinData = await fetchPrecheckinData(data.precheckin_token);
        fillBookingDetailsFromPrecheckin(precheckinData, setBookingDetails);
      }
    } catch (error) {
      console.error('Failed to load booking data:', error);
    }
  };
  
  loadBookingWithPrecheckin();
}, [bookingId]);
```

### 2. Extract All Guest Data
```javascript
// In your precheckin page component
const extractGuestData = (apiResponse) => {
  const { party } = apiResponse;
  
  // Get primary guest nationality
  const primaryNationality = party.primary?.precheckin_payload?.nationality || '';
  const primaryCountryRes = party.primary?.precheckin_payload?.country_of_residence || '';
  
  // Get companion nationalities
  const companionData = party.companions?.map(companion => ({
    id: companion.id,
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
```

### 2. Pre-populate Form Fields
```javascript
// When loading precheckin data
const loadPrecheckinData = async (token) => {
  const response = await fetch(`/api/public/hotel/${hotelSlug}/precheckin/?token=${token}`);
  const data = await response.json();
  
  const guestData = extractGuestData(data);
  
  // Set primary guest state
  setPartyPrimary(prev => ({
    ...prev,
    first_name: data.party.primary?.first_name || '',
    last_name: data.party.primary?.last_name || '',
    email: data.party.primary?.email || '',
    phone: data.party.primary?.phone || '',
    nationality: guestData.primary.nationality,
    country_of_residence: guestData.primary.country_of_residence
  }));
  
  // Set companion states
  const updatedCompanions = data.party.companions?.map((companion, index) => ({
    first_name: companion.first_name || '',
    last_name: companion.last_name || '',
    email: companion.email || '',
    phone: companion.phone || '',
    nationality: guestData.companions[index]?.nationality || '',
    country_of_residence: guestData.companions[index]?.country_of_residence || ''
  })) || [];
  
  setCompanionSlots(updatedCompanions);
};
```

### 3. Display Nationality in Form
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

### 4. Show Pre-filled Data
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

### 3. Display Precheckin Status in Booking Details
```jsx
// Component to show precheckin completion status
const PrecheckinStatus = ({ bookingDetails }) => {
  const { precheckin_completed, primary_guest, last_updated } = bookingDetails;
  
  if (!precheckin_completed) {
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
          <strong>Party Size:</strong> {bookingDetails.party_size} guests<br/>
          <strong>Special Requests:</strong> {bookingDetails.special_requests || 'None'}<br/>
          <strong>Completed:</strong> {new Date(last_updated).toLocaleDateString()}
        </Col>
      </Row>
    </Alert>
  );
};
```

### 4. Backend Verification Methods
```javascript
// Method 1: Check API response flags
const checkPrecheckinFromAPI = (data) => {
  return {
    completed: data.booking?.precheckin_complete || false,
    submitted_at: data.booking?.precheckin_submitted_at,
    has_guest_data: data.party?.primary?.precheckin_payload != null
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

### For Staff/Admin (Booking Details View)
- **No Precheckin**: Shows "Pre-check-in Pending" warning
- **Completed Precheckin**: Shows guest details, nationality, party info automatically filled
- **Updated Info**: Booking details reflect latest precheckin submissions

### For Guests (Precheckin Form)
- **First Visit**: Empty form, all fields need to be filled
- **Return Visit**: Form pre-populated with previous selections
- **Edit Mode**: Can modify previously submitted data

## 📋 Implementation Checklist

### Precheckin Detection
- [ ] Add `isPrecheckinComplete()` function to detect existing data
- [ ] Check for `precheckin_payload` in API responses
- [ ] Handle cases where precheckin data doesn't exist yet

### Booking Details Integration  
- [ ] Create `fillBookingDetailsFromPrecheckin()` function
- [ ] Update booking details state with precheckin data automatically
- [ ] Show precheckin completion status in booking views
- [ ] Display guest nationality and party information

### Form Pre-population
- [ ] Extract `precheckin_payload` data from API responses
- [ ] Pre-populate nationality dropdowns with existing selections  
- [ ] Show current nationality and guest data to users
- [ ] Allow editing of existing precheckin data

### Status Display
- [ ] Add precheckin status alerts (pending/completed)
- [ ] Show guest nationality in booking summaries
- [ ] Display completion timestamps and party details

## 🎯 Result

### Staff/Admin Benefits:
1. **Automatic booking updates** with precheckin data (nationality, requests, party info)
2. **Clear precheckin status** indicators (completed/pending)
3. **Guest nationality visible** in booking details without manual entry
4. **Real-time data sync** between precheckin and booking systems

### Guest Benefits:
1. **Form pre-population** with previously entered data
2. **Individual nationality** per guest instead of shared booking-level
3. **Edit capability** for correcting mistakes
4. **Persistent data** across form sessions

### System Integration:
1. **API detection** of precheckin completion status
2. **Automatic data filling** from precheckin to booking details
3. **Nationality tracking** per individual party member
4. **Complete data flow** from form submission to admin display

**Backend Status: ✅ Complete** - Individual nationality data is saved, returned, and integrated with booking details!