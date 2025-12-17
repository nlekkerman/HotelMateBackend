# Hotel Precheckin Field Configuration - Source of Truth

## Hard Rules

**Hotel App Only**: All backend changes must be inside the hotel app only.
- Models live in hotel/models.py  
- Views live in hotel/staff_views.py and existing public views in the hotel app
- New helper files may be added only under hotel/ (e.g. hotel/precheckin/field_registry.py)
- Do not create or modify any other Django app (room_bookings, notifications, etc.)

**Snapshot Required**: Config changes after a token is issued must not affect that token's required fields.

## Scope

**V1 Implementation**: Hotel-level configuration system for guest precheckin field visibility and requirements.

**Booking-Level Only**: Store extra fields in `RoomBooking.precheckin_payload` JSONField. No per-guest field storage in V1.

**Preserve Existing Flow**: All current endpoints, token flow, and party completeness logic remain unchanged.

## Backend Contracts

### Models

#### HotelPrecheckinConfig (hotel/models.py)
```python
class HotelPrecheckinConfig(models.Model):
    hotel = models.OneToOneField(Hotel, related_name="precheckin_config", on_delete=models.CASCADE)
    fields_enabled = models.JSONField(default=dict, blank=True)
    fields_required = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @classmethod
    def get_or_create_default(cls, hotel):
        # Auto-create with minimal default config
```

#### RoomBooking Extensions (hotel/models.py)
```python
# Add these fields to the existing RoomBooking model in its current module:
precheckin_payload = models.JSONField(default=dict, blank=True)
precheckin_submitted_at = models.DateTimeField(null=True, blank=True)
```

#### BookingPrecheckinToken Extensions (hotel/models.py)
```python
# Add these fields to the existing BookingPrecheckinToken model in its current module:
config_snapshot_enabled = models.JSONField(default=dict, blank=True)
config_snapshot_required = models.JSONField(default=dict, blank=True)
```

### Field Registry (hotel/precheckin/field_registry.py)
```python
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
        "scope": "booking",
        "choices": ["US", "UK", "CA", "AU", "DE", "FR", "ES", "IT", "NL", "Other"]
    },
    "country_of_residence": {
        "label": "Country of Residence", 
        "type": "select",
        "scope": "booking",
        "choices": ["US", "UK", "CA", "AU", "DE", "FR", "ES", "IT", "NL", "Other"]
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
    },
    "address_line_1": {
        "label": "Address Line 1",
        "type": "text",
        "scope": "booking"
    },
    "city": {
        "label": "City", 
        "type": "text",
        "scope": "booking"
    },
    "postcode": {
        "label": "Postal Code",
        "type": "text",
        "scope": "booking"
    }
}

# Default minimal config (high completion rate)
DEFAULT_CONFIG = {
    "enabled": {
        "eta": True,
        "special_requests": True, 
        "consent_checkbox": True
    },
    "required": {
        "consent_checkbox": True
    }
}
```

## Endpoints

### Public Endpoints (NO CHANGES to URLs)

#### GET /api/public/hotel/{hotel_slug}/precheckin/?token=...
**Enhanced Response Contract**:
```json
{
  "booking": {
    "id": "BK123",
    "check_in": "2025-12-20",
    "check_out": "2025-12-22",
    "room_type_name": "Deluxe Room",
    "total_guests": 2
  },
  "party": {
    "primary": {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe", 
      "role": "PRIMARY",
      "is_staying": true
    },
    "companions": [
      {
        "id": 2,
        "first_name": "",
        "last_name": "",
        "role": "COMPANION", 
        "is_staying": true
      }
    ],
    "total_party_size": 2
  },
  "party_complete": false,
  "party_missing_count": 1,
  "precheckin_config": {
    "enabled": {
      "eta": true,
      "special_requests": true,
      "consent_checkbox": true
    },
    "required": {
      "consent_checkbox": true
    }
  },
  "precheckin_field_registry": {
    "eta": {
      "label": "Estimated Time of Arrival",
      "type": "text",
      "scope": "booking"
    },
    "consent_checkbox": {
      "label": "I agree to the terms and conditions", 
      "type": "checkbox",
      "scope": "booking"
    }
  }
}
```

#### POST /api/public/hotel/{hotel_slug}/precheckin/submit/
**Enhanced Request Validation**:
- Validate existing party data (names only)
- Validate required config fields separately
- Store enabled fields in `RoomBooking.precheckin_payload`
- Set `RoomBooking.precheckin_submitted_at`
- Reject unknown field keys

### Staff Endpoints (NEW)

#### GET /api/staff/hotel/{hotel_slug}/precheckin-config/
**Response**:
```json
{
  "enabled": {
    "eta": true,
    "special_requests": true,
    "consent_checkbox": true
  },
  "required": {
    "consent_checkbox": true  
  },
  "field_registry": {
    "eta": {"label": "Estimated Time of Arrival", "type": "text"},
    "special_requests": {"label": "Special Requests", "type": "textarea"},
    "consent_checkbox": {"label": "I agree to terms", "type": "checkbox"}
  }
}
```

#### POST /api/staff/hotel/{hotel_slug}/precheckin-config/
**Request Body**:
```json
{
  "enabled": {
    "eta": true,
    "special_requests": true,
    "nationality": true,
    "consent_checkbox": true
  },
  "required": {
    "nationality": true,
    "consent_checkbox": true
  }
}
```

**Permission**: `IsSuperStaffAdminForHotel`

## Snapshot Rules

**Snapshot is required:**

### Token Creation (SendPrecheckinLinkView)
1. Get or create hotel's precheckin config
2. Store `config_snapshot_enabled` and `config_snapshot_required` on `BookingPrecheckinToken`
3. Continue with existing token generation flow

### Token Usage (GET/SUBMIT precheckin)
1. **Primary**: Use token's `config_snapshot_enabled`/`config_snapshot_required` if present
2. **Fallback**: If snapshot missing (legacy tokens), use HotelPrecheckinConfig defaults
3. Never modify party completeness logic

**Config changes after a token is issued must not affect that token's required fields.**

## Validation Rules

### Config Validation
1. **Subset Rule**: `required` must be subset of `enabled`
   - `required[key] = true` only if `enabled[key] = true`
2. **Registry Keys Only**: Reject unknown field keys in both `enabled` and `required`
3. **Guest Name Fields**: Never configurable (always required via party model)

### Submit Validation 
1. **Party Names**: Validate via existing logic (drives `party_complete`)
2. **Config Fields**: Validate required fields from snapshot/config separately
3. **Unknown Keys**: Reject any field keys not in registry
4. **Enabled Check**: Only store fields that are enabled in config

## Response JSON Contract

### Public GET Response Extensions
```json
{
  // ... existing booking/party fields unchanged ...
  "precheckin_config": {
    "enabled": {<field_key>: <boolean>, ...},
    "required": {<field_key>: <boolean>, ...}
  },
  "precheckin_field_registry": {
    <field_key>: {
      "label": <string>,
      "type": <"text"|"date"|"select"|"textarea"|"checkbox">,
      "scope": <"booking">,
      "choices": [<string>, ...] // optional, for select fields
    }
  }
}
```

**Note**: Party structure is unchanged and follows `RoomBookingDetailSerializer.get_party()`.

### Staff Config Response
```json
{
  "enabled": {<field_key>: <boolean>, ...},
  "required": {<field_key>: <boolean>, ...}, 
  "field_registry": {<field_key>: {<metadata>}, ...}
}
```

## Test Checklist

### Model Tests
- [ ] `HotelPrecheckinConfig.get_or_create_default()` creates minimal config
- [ ] Default config has `eta`, `special_requests`, `consent_checkbox` enabled
- [ ] Default config only requires `consent_checkbox`

### Validation Tests  
- [ ] **Reject required=true when enabled=false**
- [ ] **Reject unknown keys in POST config update**
- [ ] **Reject unknown keys in precheckin submit**
- [ ] Accept valid subset configurations

### Integration Tests
- [ ] Public GET includes `precheckin_config` and `field_registry`
- [ ] Public SUBMIT validates required config fields
- [ ] Public SUBMIT stores enabled fields in `precheckin_payload`
- [ ] Config snapshot preserved from token creation to usage
- [ ] Old tokens without snapshots use current HotelPrecheckinConfig (auto-created default if missing)

### Staff Endpoint Tests
- [ ] GET returns current config + registry
- [ ] POST updates config with validation
- [ ] Proper `IsSuperStaffAdminForHotel` permission enforcement

## Non-Goals

### V1 Scope Limitations
- No per-guest storage in V1 (booking-level only via `RoomBooking.precheckin_payload`)
- No changes to party completeness logic
- No new apps/modules outside hotel
- No changes to email link format

### Party Completeness Separation
- **DO NOT** tie extra fields to `party_complete` property
- **DO NOT** modify `party_missing_count` calculation  
- **DO NOT** gate room assignment on legal/ID fields

### Scope Limitations
- **DO NOT** implement per-guest field storage in V1
- **DO NOT** validate guest-scoped or party_member-scoped fields
- Registry can include scope metadata but only booking-scope validation

### Endpoint Preservation
- **DO NOT** change existing public endpoint URLs
- **DO NOT** break existing token validation logic
- **DO NOT** modify existing party submission flow

### Field Configurability
- **DO NOT** make guest name fields configurable
- **DO NOT** allow disabling party name requirements
- Guest names always drive party completeness via existing model logic