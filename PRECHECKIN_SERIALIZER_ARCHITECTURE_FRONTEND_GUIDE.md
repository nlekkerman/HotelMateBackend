# Precheckin Serializer Architecture - Frontend Guide

## 🚨 Important: NO Traditional Precheckin Serializer

**The precheckin system does NOT use traditional DRF serializers.** Instead, it uses a **flexible field registry approach** for dynamic hotel-configurable fields.

## 📍 File Locations

### 1. Field Registry (Main Logic)
**File**: `hotel/precheckin/field_registry.py`
- **Purpose**: Defines all available precheckin fields dynamically
- **Contains**: `PRECHECKIN_FIELD_REGISTRY` dictionary
- **Replaces**: Traditional serializer field definitions

### 2. Party Data Serializer  
**File**: `hotel/booking_serializers.py`
- **Class**: `BookingGuestSerializer`
- **Purpose**: Handles guest party member data (names, emails, phones)
- **Usage**: Only for basic guest information, NOT precheckin fields

### 3. API Processing
**File**: `hotel/public_views.py`
- **Views**: `ValidatePrecheckinTokenView`, `SubmitPrecheckinDataView`
- **Purpose**: Manual field validation and processing
- **Usage**: Processes precheckin form submissions

## 🏗️ Architecture Overview

### Traditional DRF Approach (NOT Used)
```python
# ❌ This does NOT exist for precheckin
class PrecheckinSerializer(serializers.ModelSerializer):
    drivers_license = serializers.FileField()
    passport = serializers.FileField()
    # ... more fields
```

### Actual Field Registry Approach (USED)
```python
# ✅ hotel/precheckin/field_registry.py
PRECHECKIN_FIELD_REGISTRY = {
    "eta": {
        "label": "Estimated Time of Arrival",
        "type": "text",
        "scope": "booking"
    },
    "special_requests": {
        "label": "Special Requests",
        "type": "textarea", 
        "scope": "booking"
    },
    "consent_checkbox": {
        "label": "I agree to the terms and conditions",
        "type": "checkbox",
        "scope": "booking"
    },
    "nationality": {
        "label": "Nationality",
        "type": "select",
        "scope": "guest",  # ✅ Each guest can have different nationality!
        "choices": "COUNTRIES_CHOICES"  # ✅ Comprehensive list of ~195 countries!
    },
    "country_of_residence": {
        "label": "Country of Residence", 
        "type": "select",
        "scope": "guest",  # ✅ Each guest can have different residence!
        "choices": "COUNTRIES_CHOICES"  # ✅ Full country names, not abbreviations
    },
    "date_of_birth": {
        "label": "Date of Birth",
        "type": "date",
        "scope": "booking"
    },
    "id_document_type": {
        "label": "ID Document Type",
        "type": "select", 
        "scope": "booking",
        "choices": ["passport", "drivers_license", "national_id", "other"]
    },
    "id_document_number": {
        "label": "ID Document Number",
        "type": "text",
        "scope": "booking"
    }
    # ... more fields
}
```

## 🎯 Field Scoping: Guest vs Booking Level

### Guest-Scoped Fields (Per Individual)
```python
# ✅ Each guest has their own values
"nationality": {"scope": "guest"},           # John: "Ireland", Jane: "France"
"country_of_residence": {"scope": "guest"},  # John: "United States", Jane: "Germany"
"date_of_birth": {"scope": "guest"}          # John: "1990-01-01", Jane: "1992-05-15"
```
**Storage**: `BookingGuest.precheckin_payload` JSON field per guest

### Booking-Scoped Fields (Whole Booking)
```python
# ✅ Shared across all guests in the booking
"eta": {"scope": "booking"},                 # "15:30" (arrival time for whole party)
"special_requests": {"scope": "booking"},    # "Late checkout requested" (for booking)
"consent_checkbox": {"scope": "booking"}     # true (legal consent for booking)
```
**Storage**: `RoomBooking.precheckin_payload` JSON field for entire booking

### Frontend Data Structure
```json
{
  "booking_fields": {
    "eta": "15:30",
    "special_requests": "Late checkout please",
    "consent_checkbox": true
  },
  "guest_fields": {
    "guest_123": {
      "nationality": "Ireland", 
      "country_of_residence": "United States",
      "date_of_birth": "1990-01-01"
    },
    "guest_456": {
      "nationality": "France",
      "country_of_residence": "Germany", 
      "date_of_birth": "1992-05-15"
    }
  }
}
```

## 🔄 Data Flow

### 1. Field Configuration (Hotel-Specific)
```python
# hotel/models.py - HotelPrecheckinConfig
class HotelPrecheckinConfig(models.Model):
    fields_enabled = models.JSONField(default=dict)  # Which fields are shown
    fields_required = models.JSONField(default=dict)  # Which fields are required
```

### 2. Frontend API Call
```javascript
// GET /api/guest/hotel/{hotel_slug}/precheckin/validate-token/{token}/
{
  "booking": {...},
  "party": [...],
  "precheckin_fields": {
    "drivers_license": {
      "enabled": true,
      "required": false,
      "label": "Driver's License",
      "type": "file_upload"
    },
    "emergency_contact_name": {
      "enabled": true, 
      "required": true,
      "label": "Emergency Contact Name",
      "type": "text"
    }
  }
}
```

### 3. Form Submission Processing
```python
# hotel/public_views.py - SubmitPrecheckinDataView
def post(self, request, hotel_slug, token):
    # Manual field validation using registry
    for field_key, field_config in PRECHECKIN_FIELD_REGISTRY.items():
        if field_key in request.data:
            # Apply validation rules from registry
            validate_field(request.data[field_key], field_config)
    
    # Save to booking.precheckin_payload
    booking.precheckin_payload = validated_data
    booking.precheckin_submitted_at = now()
    booking.save()
```

## 📊 Frontend Integration Points

### API Endpoints
```
GET  /api/guest/hotel/{hotel_slug}/precheckin/validate-token/{token}/
POST /api/guest/hotel/{hotel_slug}/precheckin/submit/{token}/
```

### Expected Response Format
```json
{
  "success": true,
  "booking": {
    "booking_id": "BK-2025-001",
    "primary_first_name": "John",
    "primary_last_name": "Doe", 
    "check_in": "2025-12-20",
    "check_out": "2025-12-22"
  },
  "party": [
    {
      "id": 123,
      "role": "PRIMARY",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "phone": "+353871234567",
      "is_staying": true
    }
  ],
  "precheckin_fields": {
    "drivers_license": {
      "enabled": true,
      "required": false,
      "label": "Driver's License",
      "type": "file_upload",
      "help_text": "Upload your driver's license"
    },
    "emergency_contact_name": {
      "enabled": true,
      "required": true, 
      "label": "Emergency Contact Name",
      "type": "text",
      "help_text": "Full name of emergency contact"
    }
  },
  "precheckin_complete": false,
  "party_complete": true
}
```

## 🚀 Frontend Implementation Guide

### 1. Dynamic Form Generation
```javascript
// Generate form fields based on precheckin_fields response
const generateFormFields = (precheckinFields) => {
  return Object.entries(precheckinFields).map(([fieldKey, config]) => {
    if (!config.enabled) return null;
    
    return {
      name: fieldKey,
      label: config.label,
      type: config.type,
      required: config.required,
      helpText: config.help_text,
      validation: config.validation
    };
  }).filter(Boolean);
};
```

### 2. Form Validation
```javascript
const validateField = (fieldKey, value, fieldConfig) => {
  const { validation, required } = fieldConfig;
  
  // Required validation
  if (required && (!value || value.trim() === '')) {
    return `${fieldConfig.label} is required`;
  }
  
  // Type-specific validation
  if (validation) {
    if (validation.max_length && value.length > validation.max_length) {
      return `${fieldConfig.label} must be less than ${validation.max_length} characters`;
    }
    
    if (validation.pattern && !new RegExp(validation.pattern).test(value)) {
      return `${fieldConfig.label} format is invalid`;
    }
  }
  
  return null;
};
```

### 3. Form Submission
```javascript
const submitPrecheckin = async (formData, token) => {
  const response = await fetch(
    `/api/guest/hotel/${hotelSlug}/precheckin/submit/${token}/`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData)
    }
  );
  
  return response.json();
};
```

## ⚠️ Key Points for Frontend

### DO:
- ✅ Use the field registry response to generate forms dynamically
- ✅ Validate fields based on registry validation rules
- ✅ Handle file uploads for `file_upload` type fields
- ✅ Show/hide fields based on `enabled` flag
- ✅ Mark fields as required based on `required` flag

### DON'T:
- ❌ Look for a traditional "PrecheckinSerializer" - it doesn't exist
- ❌ Hardcode field definitions in frontend
- ❌ Assume all hotels have the same fields enabled
- ❌ Skip validation - the registry provides all validation rules

## 🔍 Debugging Tips

### Check Field Configuration
```python
# Django shell
from hotel.models import Hotel, HotelPrecheckinConfig
hotel = Hotel.objects.get(slug='hotel-killarney')
config = HotelPrecheckinConfig.objects.get(hotel=hotel)
print(config.fields_enabled)  # See which fields are enabled
print(config.fields_required)  # See which fields are required
```

### View Registry
```python
# Django shell
from hotel.precheckin.field_registry import PRECHECKIN_FIELD_REGISTRY
import json
print(json.dumps(PRECHECKIN_FIELD_REGISTRY, indent=2))
```

## 🎯 Summary

The precheckin system is **architecturally different** from typical DRF patterns:

1. **No Traditional Serializers**: Uses field registry instead
2. **Dynamic Fields**: Each hotel configures which fields to show
3. **Manual Validation**: Custom validation logic in views
4. **Flexible Schema**: Registry allows easy addition of new field types

**For Frontend**: Always fetch field configuration from the API rather than hardcoding form definitions.