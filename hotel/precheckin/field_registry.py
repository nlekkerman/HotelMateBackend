"""
Precheckin Field Registry

Defines all available precheckin fields with their metadata and default configurations.
Only booking-scope fields are supported in V1.
"""

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