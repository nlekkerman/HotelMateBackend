"""
Precheckin Field Registry

Defines all available precheckin fields with their metadata and default configurations.
Supports both booking-scope (whole booking) and guest-scope (per individual) fields.
"""

# Comprehensive list of countries/nationalities
COUNTRIES_CHOICES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia", "Australia",
    "Austria", "Azerbaijan", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize",
    "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
    "Burkina Faso", "Burma", "Burundi", "Cambodia", "Cameroon", "Canada", "Cape Verde", "Central African Republic",
    "Chad", "Chile", "China", "Colombia", "Comoros", "Congo, Democratic Republic", "Congo, Republic of the",
    "Costa Rica", "Cote d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti",
    "Dominica", "Dominican Republic", "East Timor", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea",
    "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany",
    "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras",
    "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica",
    "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Korea, North", "Korea, South", "Kuwait",
    "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania",
    "Luxembourg", "Macedonia", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands",
    "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco",
    "Mozambique", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria",
    "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines",
    "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia",
    "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal",
    "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia",
    "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Swaziland", "Sweden", "Switzerland",
    "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia",
    "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States",
    "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
]

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
        "scope": "guest",  # ✅ Each guest can have different nationality
        "choices": COUNTRIES_CHOICES
    },
    "country_of_residence": {
        "label": "Country of Residence", 
        "type": "select",
        "scope": "guest",  # ✅ Each guest can have different residence
        "choices": COUNTRIES_CHOICES
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