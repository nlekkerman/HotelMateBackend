# Frontend Individual Nationality Implementation Guide

## 🎯 Objective
Implement per-guest nationality selection in the precheckin form so each guest can have their own nationality instead of sharing one booking-level nationality.

## 🚨 Current Problem

**Backend Configuration:**
- Nationality field has `scope: "guest"` (individual per guest)
- Backend expects nationality data inside each party member object

**Frontend Issue:**
- Nationality is currently collected as booking-level field in ExtrasSection
- Payload sends nationality at top level, not per guest
- Result: Nationality data is ignored and not saved

## 📊 Required Payload Structure

### ❌ Current (Wrong):
```json
{
  "party": {
    "primary": {
      "first_name": "Nikola",
      "last_name": "Simic",
      "email": "hotelsmatesapp@gmail.com",
      "phone": "0830945102"
    },
    "companions": [{
      "first_name": "Sanja",
      "last_name": "Majsec", 
      "email": "xzmil@mail.com",
      "phone": "00011223344"
    }]
  },
  "nationality": "Jordan",  ← Wrong: booking-level nationality
  "eta": "14:49",
  "consent_checkbox": true,
  "special_requests": "es"
}
```

### ✅ Required (Correct):
```json
{
  "party": {
    "primary": {
      "first_name": "Nikola",
      "last_name": "Simic",
      "email": "hotelsmatesapp@gmail.com", 
      "phone": "0830945102",
      "nationality": "Jordan",  ← Individual nationality
      "country_of_residence": "Serbia"
    },
    "companions": [{
      "first_name": "Sanja",
      "last_name": "Majsec",
      "email": "xzmil@mail.com",
      "phone": "00011223344",
      "nationality": "Belarus",  ← Individual nationality
      "country_of_residence": "Belarus"
    }]
  },
  "eta": "14:49",
  "consent_checkbox": true,
  "special_requests": "es"
}
```

## 🔧 Frontend Changes Required

### 1. Remove from ExtrasSection

**File:** `hotelmate-frontend/src/components/guest/ExtrasSection.jsx`

Remove nationality from booking-scoped fields rendering:
```jsx
// Filter out guest-scoped fields from ExtrasSection
const enabledFields = Object.entries(registry)
  .filter(([fieldKey, meta]) => 
    enabled[fieldKey] === true && 
    meta.scope === 'booking' &&
    !['nationality', 'country_of_residence'].includes(fieldKey)  // ← Add this filter
  )
  .sort(([, a], [, b]) => (a.order || 0) - (b.order || 0));
```

### 2. Add to PrimaryGuestCard

**File:** `hotelmate-frontend/src/components/guest/PrimaryGuestCard.jsx`

Add nationality dropdown to primary guest form:
```jsx
// Add nationality state to primary guest
const handlePrimaryFieldChange = (fieldKey, value) => {
  onChange('primary', {
    ...values.primary,
    [fieldKey]: value
  });
};

// Add after phone field
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
          value={values.primary[fieldKey] || ''}
          onChange={(e) => handlePrimaryFieldChange(fieldKey, e.target.value)}
          isInvalid={!!errors[fieldKey]}
          required={config.required[fieldKey]}
        >
          <option value="">-- Select --</option>
          {meta.choices?.map((choice, index) => (
            <option key={index} value={choice}>
              {choice}
            </option>
          ))}
        </Form.Select>
      </Form.Group>
    ));
};

// Add in JSX after existing fields
{renderGuestScopedFields()}
```

### 3. Add to CompanionCard

**File:** `hotelmate-frontend/src/components/guest/CompanionCard.jsx`

Add nationality dropdown to each companion form:
```jsx
// Add guest-scoped field handler
const handleGuestField = (fieldKey, value) => {
  onChange(companionIndex, {
    ...companion,
    [fieldKey]: value
  });
};

// Add after phone field in companion form
const renderCompanionGuestFields = () => {
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
          value={companion[fieldKey] || ''}
          onChange={(e) => handleGuestField(fieldKey, e.target.value)}
          required={config.required[fieldKey]}
        >
          <option value="">-- Select --</option>
          {meta.choices?.map((choice, index) => (
            <option key={index} value={choice}>
              {choice}
            </option>
          ))}
        </Form.Select>
      </Form.Group>
    ));
};

// Add in companion form JSX
{renderCompanionGuestFields()}
```

### 4. Update Payload Builder

**File:** `hotelmate-frontend/src/pages/guest/GuestPrecheckinPage.jsx`

Modify `buildPayload()` to exclude guest-scoped fields from top level:
```jsx
const buildPayload = () => {
  const { precheckin_field_registry: registry, precheckin_config: config } = normalizedData;
  
  const payload = {
    party: {
      primary: {
        first_name: partyPrimary.first_name,
        last_name: partyPrimary.last_name,
        email: partyPrimary.email,
        phone: partyPrimary.phone,
        is_staying: partyPrimary.is_staying !== false,
        // Guest-scoped fields are already in partyPrimary object
        ...Object.fromEntries(
          Object.entries(registry)
            .filter(([fieldKey, meta]) => 
              config.enabled[fieldKey] === true && meta.scope === 'guest'
            )
            .map(([fieldKey]) => [fieldKey, partyPrimary[fieldKey] || ''])
        )
      },
      companions: companionSlots.map(companion => ({
        first_name: companion.first_name,
        last_name: companion.last_name,
        email: companion.email,
        phone: companion.phone,
        is_staying: companion.is_staying !== false,
        // Guest-scoped fields are already in companion object
        ...Object.fromEntries(
          Object.entries(registry)
            .filter(([fieldKey, meta]) => 
              config.enabled[fieldKey] === true && meta.scope === 'guest'
            )
            .map(([fieldKey]) => [fieldKey, companion[fieldKey] || ''])
        )
      }))
    }
  };
  
  // Add only booking-scoped fields to top level
  Object.entries(registry)
    .filter(([fieldKey, meta]) => 
      config.enabled[fieldKey] === true && meta.scope === 'booking'
    )
    .forEach(([fieldKey, meta]) => {
      payload[fieldKey] = extrasValues[fieldKey] || '';
    });
    
  return payload;
};
```

## 🧪 Testing Checklist

### 1. Field Appearance
- [ ] Nationality dropdown appears in Primary Guest section
- [ ] Nationality dropdown appears in each Companion section  
- [ ] Nationality dropdown does NOT appear in Additional Information section
- [ ] All nationality dropdowns show full country names (not abbreviations)

### 2. Data Submission
- [ ] Select different nationalities for primary and companion guests
- [ ] Submit form successfully (no 404 errors)
- [ ] Check browser network tab - payload should show nationality inside party member objects

### 3. Backend Verification
- [ ] Check Django admin - each guest shows their individual nationality
- [ ] Primary guest nationality column shows selected country
- [ ] Companion guest nationality column shows selected country

## 🎯 Expected Result

After implementation:
- **Primary Guest (Nikola)**: Shows "Jordan" in nationality column
- **Companion (Sanja)**: Shows "Belarus" in nationality column  
- **Each guest has individual nationality** stored in their `precheckin_payload`

## 📍 Files to Modify

1. `hotelmate-frontend/src/components/guest/ExtrasSection.jsx` - Remove nationality
2. `hotelmate-frontend/src/components/guest/PrimaryGuestCard.jsx` - Add nationality
3. `hotelmate-frontend/src/components/guest/CompanionCard.jsx` - Add nationality  
4. `hotelmate-frontend/src/pages/guest/GuestPrecheckinPage.jsx` - Update payload builder

## 🚀 Backend Status

✅ **Backend is ready** - no changes needed on backend side:
- Field registry has nationality with `scope: "guest"`
- Submission logic saves guest-scoped data to individual `BookingGuest.precheckin_payload`
- Django admin displays individual guest nationality columns

Frontend implementation is the only remaining step!