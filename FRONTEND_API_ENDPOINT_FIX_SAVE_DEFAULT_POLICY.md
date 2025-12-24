# Frontend API Endpoint Issue: Save Default Policy Button

## Problem Description

The "save default policy" button is sending requests to the wrong API endpoint, causing incorrect behavior.

## Current (Incorrect) Behavior

**Button Action:** Save Default Policy  
**Current Request:**
```
PATCH /api/staff/hotel/hotel-killarney/settings/
```

**Response Data:** Hotel settings JSON (colors, contact info, etc.)
```json
{
    "id": 2,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney",
    "main_color": "#a1389b",
    "secondary_color": "#3f15f9",
    // ... hotel settings data
}
```

## Expected (Correct) Behavior

**Button Action:** Save Default Policy  
**Correct Request:**
```
POST /api/staff/hotel/hotel-killarney/cancellation-policies/
```

## Available Cancellation Policy Endpoints

### 1. List & Create Policies
```
GET  /api/staff/hotel/{hotel_slug}/cancellation-policies/
POST /api/staff/hotel/{hotel_slug}/cancellation-policies/
```

### 2. Get, Update, Delete Specific Policy
```
GET    /api/staff/hotel/{hotel_slug}/cancellation-policies/{policy_id}/
PUT    /api/staff/hotel/{hotel_slug}/cancellation-policies/{policy_id}/
PATCH  /api/staff/hotel/{hotel_slug}/cancellation-policies/{policy_id}/
DELETE /api/staff/hotel/{hotel_slug}/cancellation-policies/{policy_id}/
```

### 3. Policy Templates
```
GET /api/staff/hotel/{hotel_slug}/cancellation-policies/templates/
```

## Frontend Fix Required

### For Creating New Default Policy

```javascript
// ❌ WRONG - Currently sending to settings endpoint
fetch('/api/staff/hotel/hotel-killarney/settings/', {
  method: 'PATCH',
  // ... hotel data
})

// ✅ CORRECT - Should send to cancellation policies endpoint
fetch('/api/staff/hotel/hotel-killarney/cancellation-policies/', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}` // if using JWT
  },
  body: JSON.stringify({
    name: "Default Cancellation Policy",
    code: "DEFAULT",
    description: "Default hotel cancellation policy",
    template_type: "FLEXIBLE", // Options: FLEXIBLE, MODERATE, NON_REFUNDABLE, CUSTOM
    is_active: true,
    free_until_hours: 24, // Free cancellation until 24 hours before check-in
    penalty_type: "PERCENTAGE", // Options: NONE, FIXED, PERCENTAGE, FIRST_NIGHT, FULL_STAY
    penalty_percentage: 50.00, // 50% penalty after free cancellation period
    no_show_penalty_type: "FULL_STAY"
  })
})
```

### For Updating Existing Default Policy

```javascript
// If policy already exists and you want to update it
fetch(`/api/staff/hotel/hotel-killarney/cancellation-policies/${policyId}/`, {
  method: 'PATCH',
  headers: { 
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    // Only include fields you want to update
    free_until_hours: 48,
    penalty_percentage: 25.00
  })
})
```

## Expected Request/Response Examples

### Creating a New Policy

**Request:**
```http
POST /api/staff/hotel/hotel-killarney/cancellation-policies/
Content-Type: application/json

{
  "name": "Flexible Cancellation",
  "code": "FLEX",
  "template_type": "FLEXIBLE",
  "free_until_hours": 24,
  "penalty_type": "PERCENTAGE",
  "penalty_percentage": 50.00,
  "is_active": true
}
```

**Response (201 Created):**
```json
{
  "id": 15,
  "hotel": 2,
  "name": "Flexible Cancellation",
  "code": "FLEX", 
  "description": "",
  "is_active": true,
  "template_type": "FLEXIBLE",
  "free_until_hours": 24,
  "penalty_type": "PERCENTAGE",
  "penalty_amount": null,
  "penalty_percentage": "50.00",
  "no_show_penalty_type": "FULL_STAY",
  "created_at": "2025-12-24T15:30:00Z",
  "updated_at": "2025-12-24T15:30:00Z",
  "tiers": []
}
```

## Policy Template Types

### 1. FLEXIBLE Template
- Free cancellation until X hours before check-in
- After deadline: penalty (percentage, fixed amount, first night, or full stay)

### 2. MODERATE Template  
- Shorter free cancellation window
- Higher penalties after deadline

### 3. NON_REFUNDABLE Template
- No free cancellation
- Full stay penalty from booking time

### 4. CUSTOM Template
- Multiple penalty tiers based on time before check-in
- Uses `CancellationPolicyTier` model for complex rules

## Policy Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | Yes | Human-readable policy name |
| `code` | String | Yes | Unique short code (e.g., "FLEX", "NRF") |
| `template_type` | String | Yes | FLEXIBLE, MODERATE, NON_REFUNDABLE, CUSTOM |
| `description` | Text | No | Policy description for guests |
| `is_active` | Boolean | No | Whether policy is available (default: true) |
| `free_until_hours` | Integer | No | Hours before check-in for free cancellation |
| `penalty_type` | String | No | NONE, FIXED, PERCENTAGE, FIRST_NIGHT, FULL_STAY |
| `penalty_amount` | Decimal | No | Fixed penalty amount (for FIXED type) |
| `penalty_percentage` | Decimal | No | Penalty percentage (for PERCENTAGE type) |
| `no_show_penalty_type` | String | No | Penalty for no-shows |

## Implementation Steps

1. **Identify the Frontend Component** - Find where the "save default policy" button is defined
2. **Update API Endpoint** - Change from `/settings/` to `/cancellation-policies/`
3. **Update Request Method** - Use POST for creation, PATCH for updates
4. **Update Request Payload** - Send policy data instead of hotel settings
5. **Update Response Handling** - Handle cancellation policy response format
6. **Test the Fix** - Verify button creates/updates policies correctly

## Debugging Tips

- Check browser network tab to see actual API calls
- Verify the button's click handler is calling the correct function
- Ensure proper authentication headers are included
- Check if policy creation requires specific permissions
- Validate request payload matches expected policy schema