# Room Booking API Payload Analysis

## Current Endpoint
```
POST /api/public/hotel/{hotel_slug}/bookings/
```

## Payload Validation Results

### ❌ Issues Found with Original Payload

#### 1. **Redundant Booker Fields for SELF Booking**
When `booker_type: "SELF"`, booker fields are unnecessary and should be omitted:

```json
{
  "booker_type": "SELF",
  // ❌ These are redundant for SELF bookings:
  "booker_first_name": "John",           // Remove
  "booker_last_name": "Doe",             // Remove  
  "booker_email": "john.doe@email.com",  // Remove
  "booker_phone": "+353871234567"        // Remove
}
```

#### 2. **Incorrect Companions Structure**
Backend expects `party` array with `role` field, not `companions`:

**❌ Original:**
```json
{
  "companions": [
    {
      "first_name": "Jane",
      "last_name": "Smith"
    }
  ]
}
```

**✅ Expected:**
```json
{
  "party": [
    {
      "role": "COMPANION",
      "first_name": "Jane",
      "last_name": "Smith"
    }
  ]
}
```

#### 3. **Missing PRIMARY Guest in Party**
If `party` array is provided, it must include the PRIMARY guest:

```json
{
  "party": [
    {
      "role": "PRIMARY",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@email.com",
      "phone": "+353871234567"
    },
    {
      "role": "COMPANION",
      "first_name": "Jane",
      "last_name": "Smith"
    }
  ]
}
```

## ✅ Corrected Payload Structure

### Required Fields
```json
{
  "room_type_code": "deluxe-suite",
  "check_in": "2025-12-20",
  "check_out": "2025-12-22",
  "booker_type": "SELF",
  
  "primary_first_name": "John",
  "primary_last_name": "Doe", 
  "primary_email": "john.doe@email.com",
  "primary_phone": "+353871234567"
}
```

### Optional Fields
```json
{
  "quote_id": "QT-2025-ABC123",
  "adults": 2,
  "children": 0,
  "special_requests": "Late check-in requested",
  "promo_code": "WINTER2025"
}
```

### Complete Corrected Payload
```json
{
  "quote_id": "QT-2025-ABC123",
  "room_type_code": "deluxe-suite",
  "check_in": "2025-12-20",
  "check_out": "2025-12-22", 
  "adults": 2,
  "children": 0,
  "booker_type": "SELF",
  
  "primary_first_name": "John",
  "primary_last_name": "Doe", 
  "primary_email": "john.doe@email.com",
  "primary_phone": "+353871234567",
  
  "special_requests": "Late check-in requested",
  "promo_code": "WINTER2025",
  
  "party": [
    {
      "role": "PRIMARY",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@email.com",
      "phone": "+353871234567"
    },
    {
      "role": "COMPANION",
      "first_name": "Jane",
      "last_name": "Smith"
    }
  ]
}
```

## Backend Field Validation Rules

### 1. **Booker Type Logic**
- `SELF`: No booker fields required (primary guest = booker)
- `THIRD_PARTY`: All booker fields required
- `COMPANY`: All booker fields + `booker_company` required

### 2. **Party Validation**
- Must include exactly one `PRIMARY` guest
- PRIMARY guest must match `primary_*` fields exactly
- COMPANION guests can have optional email/phone
- Party size should align with `adults + children`

### 3. **Required vs Optional**
**Always Required:**
- `room_type_code`, `check_in`, `check_out`
- `primary_first_name`, `primary_last_name`, `primary_email`, `primary_phone`
- `booker_type`

**Conditionally Required:**
- Booker fields (when `booker_type != "SELF"`)
- `booker_company` (when `booker_type == "COMPANY"`)

**Always Optional:**
- `quote_id`, `adults`, `children`, `special_requests`, `promo_code`, `party`

## Expected Response
```json
{
  "booking_id": "BK-2025-0016",
  "confirmation_number": "HOT-2025-0016", 
  "status": "PENDING_PAYMENT",
  "hotel": {
    "name": "Hotel Killarney",
    "slug": "hotel-killarney"
  },
  "room": {
    "type": "Deluxe Suite",
    "code": "deluxe-suite"
  },
  "dates": {
    "check_in": "2025-12-20",
    "check_out": "2025-12-22",
    "nights": 2
  },
  "guest": {
    "name": "John Doe",
    "email": "john.doe@email.com",
    "phone": "+353871234567"
  },
  "pricing": {
    "total": "450.00",
    "currency": "EUR"
  },
  "created_at": "2025-12-18T11:30:00Z",
  "payment_required": true
}
```

## Common Validation Errors

1. **400 Bad Request**: Missing required fields
2. **400 Bad Request**: Invalid `booker_type` value
3. **400 Bad Request**: Missing booker fields for non-SELF bookings
4. **400 Bad Request**: Party validation errors (missing PRIMARY, name mismatch)
5. **404 Not Found**: Invalid `room_type_code`
6. **400 Bad Request**: Invalid date format or logic