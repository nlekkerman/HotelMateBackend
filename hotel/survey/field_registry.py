"""
Survey Field Registry

Defines all available survey fields with their metadata and default configurations.
All survey fields use booking-scope (whole booking level feedback).
Following precheckin pattern: registry defines what's possible, hotel config defines what's used.
"""

SURVEY_FIELD_REGISTRY = {
    "overall_rating": {
        "label": "Overall Rating",
        "type": "rating", 
        "scope": "survey",
        "order": 1,
        "help_text": "Rate your overall experience",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": True,
        "default_required": True
    },
    "comment": {
        "label": "Comments & Feedback",
        "type": "textarea",
        "scope": "survey",
        "order": 20,
        "help_text": "Share your thoughts about your stay",
        "placeholder": "Share your experience with us...",
        "default_enabled": True,
        "default_required": False
    },
    "contact_permission": {
        "label": "May we contact you about your feedback?",
        "type": "checkbox", 
        "scope": "survey",
        "order": 21,
        "help_text": "Allow us to follow up on your feedback",
        "default_enabled": True,
        "default_required": False
    },
    
    # Room & Accommodation
    "room_rating": {
        "label": "Room Quality",
        "type": "rating",
        "scope": "survey",
        "order": 2,
        "help_text": "Rate the quality and comfort of your room",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "cleanliness_rating": {
        "label": "Cleanliness",
        "type": "rating",
        "scope": "survey", 
        "order": 3,
        "help_text": "Rate the cleanliness of your room and public areas",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "bed_comfort_rating": {
        "label": "Bed Comfort",
        "type": "rating",
        "scope": "survey",
        "order": 4,
        "help_text": "Rate the comfort of your bed and pillows",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "bathroom_rating": {
        "label": "Bathroom Quality",
        "type": "rating",
        "scope": "survey",
        "order": 5,
        "help_text": "Rate your bathroom facilities and amenities",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    
    # Service & Staff
    "staff_rating": {
        "label": "Staff Service",
        "type": "rating",
        "scope": "survey",
        "order": 6,
        "help_text": "Rate the friendliness and helpfulness of our staff",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "checkin_rating": {
        "label": "Check-in Experience",
        "type": "rating",
        "scope": "survey",
        "order": 7,
        "help_text": "Rate the check-in process and front desk service",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "checkout_rating": {
        "label": "Check-out Experience", 
        "type": "rating",
        "scope": "survey",
        "order": 8,
        "help_text": "Rate the check-out process and any assistance received",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    
    # Amenities & Facilities
    "breakfast_rating": {
        "label": "Breakfast Quality",
        "type": "rating",
        "scope": "survey",
        "order": 9,
        "help_text": "Rate the breakfast quality and variety (if applicable)",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "wifi_rating": {
        "label": "Wi-Fi Quality",
        "type": "rating", 
        "scope": "survey",
        "order": 10,
        "help_text": "Rate the Wi-Fi speed and reliability",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "parking_rating": {
        "label": "Parking Experience",
        "type": "rating",
        "scope": "survey", 
        "order": 11,
        "help_text": "Rate the parking availability and convenience (if applicable)",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "gym_rating": {
        "label": "Fitness Facilities",
        "type": "rating",
        "scope": "survey",
        "order": 12, 
        "help_text": "Rate the gym/fitness facilities (if applicable)",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "pool_rating": {
        "label": "Pool & Spa",
        "type": "rating",
        "scope": "survey",
        "order": 13,
        "help_text": "Rate the pool and spa facilities (if applicable)", 
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    
    # Environment & Atmosphere
    "noise_rating": {
        "label": "Noise Level",
        "type": "rating",
        "scope": "survey",
        "order": 14,
        "help_text": "Rate the noise levels and quietness of your room",
        "choices": [
            (1, "1 - Very Noisy"), 
            (2, "2 - Somewhat Noisy"), 
            (3, "3 - Acceptable"), 
            (4, "4 - Quiet"), 
            (5, "5 - Very Quiet")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "location_rating": {
        "label": "Location",
        "type": "rating",
        "scope": "survey",
        "order": 15,
        "help_text": "Rate the hotel location and accessibility to attractions",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "atmosphere_rating": {
        "label": "Hotel Atmosphere",
        "type": "rating",
        "scope": "survey",
        "order": 16,
        "help_text": "Rate the overall atmosphere and ambiance",
        "choices": [
            (1, "1 - Poor"), 
            (2, "2 - Fair"), 
            (3, "3 - Good"), 
            (4, "4 - Very Good"), 
            (5, "5 - Excellent")
        ],
        "default_enabled": False,
        "default_required": False
    },
    
    # Value & Recommendation  
    "value_rating": {
        "label": "Value for Money",
        "type": "rating",
        "scope": "survey",
        "order": 17,
        "help_text": "Rate if the experience was worth the price paid",
        "choices": [
            (1, "1 - Poor Value"), 
            (2, "2 - Fair Value"), 
            (3, "3 - Good Value"), 
            (4, "4 - Very Good Value"), 
            (5, "5 - Excellent Value")
        ],
        "default_enabled": False,
        "default_required": False
    },
    "recommendation": {
        "label": "Would you recommend us?",
        "type": "select",
        "scope": "survey",
        "order": 18,
        "help_text": "Would you recommend this hotel to others?",
        "choices": [
            ("yes", "Yes, definitely"),
            ("maybe", "Maybe"),  
            ("no", "No, probably not")
        ],
        "default_enabled": False,
        "default_required": False
    },
    
    # Open-ended feedback
    "improvement_suggestions": {
        "label": "Suggestions for Improvement",
        "type": "textarea",
        "scope": "survey", 
        "order": 19,
        "help_text": "What could we improve for future guests?",
        "placeholder": "Tell us what we could do better...",
        "default_enabled": False,
        "default_required": False
    }
}

# Default configuration (high completion rate - only essential fields)
DEFAULT_SURVEY_CONFIG = {
    "enabled": {
        "overall_rating": True,
        "comment": True, 
        "contact_permission": True
    },
    "required": {
        "overall_rating": True  # Only rating required by default
    },
    "send_mode": "AUTO_DELAYED",
    "delay_hours": 24
}