"""
Create GitHub issues for Public Hotel Page API + Booking Logic implementation.
Based on backend_public_hotel_page_and_booking.md
"""

import subprocess

# Issue definitions based on backend_public_hotel_page_and_booking.md
issues = [
    {
        "title": "[Hotel Public API] Extend Hotel model with public page fields",
        "body": """### Description
Add marketing and location fields to the Hotel model to support public hotel pages.

### Requirements

#### Marketing Fields
- `tagline` (CharField, max 200, blank=True)
- `hero_image` (CloudinaryField, blank=True, null=True)
- `long_description` (TextField, blank=True)

#### Location Fields
- `address_line_1` (CharField, max 255, blank=True)
- `address_line_2` (CharField, max 255, blank=True)
- `postal_code` (CharField, max 20, blank=True)
- `latitude` (DecimalField, max_digits=9, decimal_places=6, null=True, blank=True)
- `longitude` (DecimalField, max_digits=9, decimal_places=6, null=True, blank=True)

#### Contact Fields
- `phone` (CharField, max 30, blank=True)
- `email` (EmailField, blank=True)
- `website_url` (URLField, blank=True)
- `booking_url` (URLField, blank=True, help_text="Primary booking URL")

### Acceptance Criteria
- [ ] All fields added to `hotel/models.py` Hotel model
- [ ] Migration created and tested
- [ ] Fields accessible in Django admin
- [ ] No breaking changes to existing Hotel functionality
- [ ] Fields have sensible defaults (blank=True where appropriate)

### Related Files
- `hotel/models.py`
- `hotel/admin.py`

### Notes
This extends the existing Hotel model which already has:
- name, slug, subdomain
- logo (CloudinaryField)
- is_active, sort_order
- city, country, short_description
""",
        "labels": ["backend", "model", "hotel-public-api"]
    },
    {
        "title": "[Hotel Public API] Create BookingOptions model",
        "body": """### Description
Create a new model to store booking call-to-action configuration for each hotel's public page.

### Requirements

Create `BookingOptions` model in `hotel/models.py` with:

#### Fields
- `hotel` (OneToOneField to Hotel, related_name='booking_options')
- `primary_cta_label` (CharField, max 100, default="Book a Room")
- `primary_cta_url` (URLField, blank=True)
- `secondary_cta_label` (CharField, max 100, blank=True, e.g. "Call to Book")
- `secondary_cta_phone` (CharField, max 30, blank=True)
- `terms_url` (URLField, blank=True)
- `policies_url` (URLField, blank=True)

#### Methods
- `__str__()` returning hotel name

### Acceptance Criteria
- [ ] BookingOptions model created
- [ ] OneToOneField relationship with Hotel
- [ ] Migration created and applied
- [ ] Model registered in admin
- [ ] Default values set appropriately
- [ ] Can be accessed via `hotel.booking_options`

### Related Files
- `hotel/models.py`
- `hotel/admin.py`

### Notes
This will be included in the public hotel API response under a nested `booking_options` object.
""",
        "labels": ["backend", "model", "hotel-public-api"]
    },
    {
        "title": "[Hotel Public API] Create RoomType model for marketing",
        "body": """### Description
Create a RoomType model to store marketing information about room categories (not live inventory).

### Requirements

Create `RoomType` model in `rooms/models.py` with:

#### Fields
- `hotel` (ForeignKey to Hotel, related_name='room_types')
- `code` (CharField, max 50, blank=True, help_text="Optional identifier")
- `name` (CharField, max 200, e.g. "Deluxe Suite")
- `short_description` (TextField, blank=True)
- `max_occupancy` (PositiveSmallIntegerField, default=2)
- `bed_setup` (CharField, max 100, blank=True, e.g. "King Bed")
- `photo` (CloudinaryField, blank=True, null=True)
- `starting_price_from` (DecimalField, max_digits=10, decimal_places=2, help_text="Marketing 'from' price")
- `currency` (CharField, max 3, default="EUR")
- `booking_code` (CharField, max 50, blank=True)
- `booking_url` (URLField, blank=True, help_text="Deep link for booking this room type")
- `availability_message` (CharField, max 100, blank=True, e.g. "High demand")
- `sort_order` (PositiveIntegerField, default=0)
- `is_active` (BooleanField, default=True)

#### Meta
- `ordering = ['sort_order', 'name']`
- `unique_together = ('hotel', 'code')` if code provided

#### Methods
- `__str__()` returning hotel + room type name

### Acceptance Criteria
- [ ] RoomType model created in `rooms/models.py`
- [ ] All fields implemented with proper types
- [ ] Migration created and applied
- [ ] Model registered in admin
- [ ] Ordering by sort_order works
- [ ] Can filter by hotel and is_active

### Related Files
- `rooms/models.py`
- `rooms/admin.py`

### Notes
This is separate from the existing Room model (which tracks physical rooms).
RoomType is purely for marketing/public display purposes.
""",
        "labels": ["backend", "model", "hotel-public-api"]
    },
    {
        "title": "[Hotel Public API] Create Offer model for packages and deals",
        "body": """### Description
Create an Offer model to store marketing offers, packages, and deals for each hotel's public page.

### Requirements

Create `Offer` model in new or existing app (suggest `hotel/models.py`) with:

#### Fields
- `hotel` (ForeignKey to Hotel, related_name='offers')
- `title` (CharField, max 200, e.g. "Weekend Getaway Package")
- `short_description` (TextField)
- `details_text` (TextField, blank=True)
- `details_html` (TextField, blank=True, help_text="Rich HTML for details")
- `valid_from` (DateField, null=True, blank=True)
- `valid_to` (DateField, null=True, blank=True)
- `tag` (CharField, max 50, blank=True, e.g. "Family Deal", "Weekend Offer")
- `book_now_url` (URLField, blank=True, help_text="Link to book this offer")
- `photo` (CloudinaryField, blank=True, null=True)
- `sort_order` (PositiveIntegerField, default=0)
- `is_active` (BooleanField, default=True)
- `created_at` (DateTimeField, auto_now_add=True)

#### Meta
- `ordering = ['sort_order', '-created_at']`

#### Methods
- `__str__()` returning hotel + offer title
- `is_valid()` method checking if current date is within valid_from/valid_to range

### Acceptance Criteria
- [ ] Offer model created
- [ ] All fields implemented
- [ ] Migration created and applied
- [ ] Model registered in admin
- [ ] is_valid() method works correctly
- [ ] Can filter active offers by hotel

### Related Files
- `hotel/models.py` (or new `offers/models.py`)
- `hotel/admin.py`

### Notes
Offers are marketing-level only, not connected to live booking inventory.
""",
        "labels": ["backend", "model", "hotel-public-api"]
    },
    {
        "title": "[Hotel Public API] Create LeisureActivity model",
        "body": """### Description
Create a LeisureActivity model to store information about hotel facilities, amenities, and activities for public pages.

### Requirements

Create `LeisureActivity` model in `hotel/models.py` or new app with:

#### Fields
- `hotel` (ForeignKey to Hotel, related_name='leisure_activities')
- `name` (CharField, max 200, e.g. "Indoor Pool", "Spa & Wellness")
- `category` (CharField, max 50, choices, e.g. "Wellness", "Family", "Dining", "Sports")
- `short_description` (TextField)
- `details_html` (TextField, blank=True)
- `icon` (CharField, max 50, blank=True, help_text="Icon name or class")
- `image` (CloudinaryField, blank=True, null=True)
- `sort_order` (PositiveIntegerField, default=0)
- `is_active` (BooleanField, default=True)

#### Category Choices
- "Wellness"
- "Family"
- "Dining"
- "Sports"
- "Entertainment"
- "Business"
- "Other"

#### Meta
- `ordering = ['category', 'sort_order', 'name']`

#### Methods
- `__str__()` returning hotel + activity name

### Acceptance Criteria
- [ ] LeisureActivity model created
- [ ] Category choices implemented
- [ ] Migration created and applied
- [ ] Model registered in admin with category filter
- [ ] Ordering works correctly
- [ ] Can group by category for frontend display

### Related Files
- `hotel/models.py`
- `hotel/admin.py`

### Notes
This covers all leisure/facility information shown on the public hotel page.
""",
        "labels": ["backend", "model", "hotel-public-api"]
    },
    {
        "title": "[Hotel Public API] Create HotelPublicDetailSerializer",
        "body": """### Description
Create a comprehensive serializer for the public hotel page API endpoint.

### Requirements

Create `HotelPublicDetailSerializer` in `hotel/serializers.py` that includes:

#### Hotel Basics
- slug, name, tagline
- hero_image_url, logo_url
- short_description, long_description

#### Location
- city, country
- address_line_1, address_line_2, postal_code
- latitude, longitude

#### Contact
- phone, email
- website_url, booking_url

#### Nested Objects
- `booking_options` (nested BookingOptionsSerializer)
- `room_types` (nested list, RoomTypeSerializer, only active)
- `offers` (nested list, OfferSerializer, only active)
- `leisure_activities` (nested list, LeisureActivitySerializer, only active)

### Implementation Details

```python
class BookingOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingOptions
        fields = [
            'primary_cta_label', 'primary_cta_url',
            'secondary_cta_label', 'secondary_cta_phone',
            'terms_url', 'policies_url'
        ]

class RoomTypeSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = RoomType
        fields = [
            'code', 'name', 'short_description',
            'max_occupancy', 'bed_setup', 'photo_url',
            'starting_price_from', 'currency',
            'booking_code', 'booking_url', 'availability_message'
        ]

class OfferSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'title', 'short_description', 'details_html',
            'valid_from', 'valid_to', 'tag',
            'book_now_url', 'photo_url'
        ]

class LeisureActivitySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LeisureActivity
        fields = [
            'name', 'category', 'short_description',
            'details_html', 'icon', 'image_url'
        ]

class HotelPublicDetailSerializer(serializers.ModelSerializer):
    # SerializerMethodFields for URLs
    # Nested serializers
    # Filter active items only
```

### Acceptance Criteria
- [ ] All four nested serializers created
- [ ] HotelPublicDetailSerializer includes all required fields
- [ ] Cloudinary URLs properly serialized
- [ ] Only active room_types, offers, leisure_activities included
- [ ] No sensitive/internal fields exposed
- [ ] No guest/stay/booking records included

### Related Files
- `hotel/serializers.py`

### Security Notes
MUST NOT expose:
- Live availability or PMS pricing
- Guest/stay/booking records
- Staff or internal config
- Sensitive internal IDs
""",
        "labels": ["backend", "serializer", "hotel-public-api"]
    },
    {
        "title": "[Hotel Public API] Implement public hotel detail endpoint",
        "body": """### Description
Create the main public API endpoint for hotel page content.

### Requirements

#### Endpoint
- `GET /api/hotels/<slug>/public/`
- Anonymous access (AllowAny)
- Lookup by hotel slug
- Use HotelPublicDetailSerializer

#### Implementation

In `hotel/views.py`:

```python
class HotelPublicPageView(generics.RetrieveAPIView):
    \"\"\"
    Public API endpoint for hotel page content.
    Returns full hotel details including booking options,
    room types, offers, and leisure activities.
    \"\"\"
    serializer_class = HotelPublicDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    
    def get_queryset(self):
        return Hotel.objects.filter(
            is_active=True
        ).select_related(
            'booking_options'
        ).prefetch_related(
            'room_types',
            'offers',
            'leisure_activities'
        )
```

#### URL Configuration

In `hotel/urls.py`:
```python
path('<slug>/public/', HotelPublicPageView.as_view(), name='hotel-public-page'),
```

### Acceptance Criteria
- [ ] View class created in `hotel/views.py`
- [ ] URL pattern registered
- [ ] Endpoint accessible without authentication
- [ ] Returns 200 for valid slug
- [ ] Returns 404 for invalid/inactive hotel
- [ ] Response includes all nested objects
- [ ] Query optimization with select_related/prefetch_related
- [ ] Only active hotels returned

### Related Files
- `hotel/views.py`
- `hotel/urls.py`

### Testing
- Valid slug returns full data
- Invalid slug returns 404
- Inactive hotel returns 404
- No authentication required
""",
        "labels": ["backend", "api", "hotel-public-api"]
    },
    {
        "title": "[Hotel Public API] Add admin interfaces for new models",
        "body": """### Description
Create Django admin interfaces for managing booking options, room types, offers, and leisure activities.

### Requirements

#### BookingOptions Admin
- Inline on Hotel admin
- All fields editable
- Help text visible

#### RoomType Admin
- List display: hotel, name, starting_price_from, currency, is_active, sort_order
- List filter: hotel, is_active
- Search: name, code
- Ordering: sort_order, name
- Photo preview in form

#### Offer Admin
- List display: hotel, title, tag, valid_from, valid_to, is_active, sort_order
- List filter: hotel, is_active, tag, valid_from
- Search: title, short_description
- Ordering: sort_order, -created_at
- Photo preview in form
- Date validation (valid_to >= valid_from)

#### LeisureActivity Admin
- List display: hotel, name, category, is_active, sort_order
- List filter: hotel, category, is_active
- Search: name, short_description
- Ordering: category, sort_order, name
- Image preview in form

### Acceptance Criteria
- [ ] All models registered in `hotel/admin.py`
- [ ] List displays configured with useful columns
- [ ] Filters and search implemented
- [ ] Cloudinary images display as previews
- [ ] Inline editing works where appropriate
- [ ] Admin is user-friendly for content managers

### Related Files
- `hotel/admin.py`

### Notes
Make it easy for non-technical users to manage hotel marketing content.
""",
        "labels": ["backend", "admin", "hotel-public-api"]
    },
    {
        "title": "[Hotel Public API] Write comprehensive tests",
        "body": """### Description
Create test suite for public hotel page API functionality.

### Requirements

Create `hotel/tests_public_api.py` with:

#### Model Tests
- BookingOptions creation and relationships
- RoomType creation, ordering, filtering
- Offer creation, is_valid() method, filtering
- LeisureActivity creation, category choices

#### Serializer Tests
- HotelPublicDetailSerializer includes all fields
- Nested serializers work correctly
- Cloudinary URLs properly serialized
- Only active items included in nested lists
- No sensitive fields exposed

#### View Tests
- Valid slug returns 200 with full data
- Invalid slug returns 404
- Inactive hotel returns 404
- No authentication required
- Response structure matches spec
- Multiple room types returned
- Multiple offers returned
- Multiple leisure activities returned

#### Security Tests
- No guest/stay/booking records in response
- No staff fields in response
- No internal config exposed
- No sensitive IDs leaked

#### Edge Cases
- Hotel with no booking_options
- Hotel with no room types
- Hotel with no offers
- Hotel with no leisure activities
- Hotel with all optional fields blank

### Test Data
Create test hotel with:
- 3 room types (1 inactive)
- 2 offers (1 expired, 1 inactive)
- 4 leisure activities across different categories

### Acceptance Criteria
- [ ] All test categories covered
- [ ] Tests pass with 100% coverage of new code
- [ ] Test data is realistic
- [ ] Edge cases handled
- [ ] Security assertions pass
- [ ] Tests run fast (use fixtures efficiently)

### Related Files
- `hotel/tests_public_api.py`

### Command
```bash
python manage.py test hotel.tests_public_api
```
""",
        "labels": ["backend", "tests", "hotel-public-api"]
    },
    {
        "title": "[Hotel Public API] Create data migration for test hotels",
        "body": """### Description
Create a data migration to populate test/demo data for the public hotel API.

### Requirements

Create data migration that adds:

#### For Each Test Hotel
- BookingOptions with sample CTAs
- 2-3 RoomType entries with realistic data
- 2-3 Offer entries (packages, deals)
- 4-5 LeisureActivity entries across categories

#### Sample Data

**Room Types:**
- Standard Room (from €89/night)
- Deluxe Suite (from €159/night)
- Family Room (from €129/night)

**Offers:**
- Weekend Getaway Package
- Family Summer Deal
- Romantic Dinner & Stay

**Leisure Activities:**
- Indoor Pool (Wellness)
- Kids Club (Family)
- Restaurant (Dining)
- Fitness Center (Sports)
- Spa (Wellness)

### Implementation

```bash
python manage.py makemigrations hotel --empty --name populate_public_hotel_data
```

Then edit migration to use `RunPython` with forward/reverse functions.

### Acceptance Criteria
- [ ] Data migration created
- [ ] Forward function populates realistic data
- [ ] Reverse function cleans up data
- [ ] Migration is idempotent (can run multiple times)
- [ ] All hotels get sample content
- [ ] Photos/images can be added later (optional in migration)

### Related Files
- `hotel/migrations/XXXX_populate_public_hotel_data.py`

### Notes
This is for development/testing only. Production hotels will add their own content via admin.
""",
        "labels": ["backend", "migration", "hotel-public-api"]
    },
    {
        "title": "[Hotel Public API] Update API documentation",
        "body": """### Description
Document the new public hotel page API endpoint for frontend integration.

### Requirements

Create or update `docs/HOTEL_PUBLIC_API.md` with:

#### Overview
- Purpose: Power public hotel marketing pages
- Authentication: None required (anonymous)
- Target users: Non-staying guests browsing hotels

#### Endpoint Documentation

**GET /api/hotels/{slug}/public/**

Request:
- Method: GET
- Path parameter: `slug` (hotel slug)
- Auth: None

Response (200 OK):
```json
{
  "slug": "grand-hotel-dublin",
  "name": "Grand Hotel Dublin",
  "tagline": "Luxury in the heart of the city",
  "hero_image_url": "https://...",
  "logo_url": "https://...",
  "short_description": "...",
  "long_description": "...",
  
  "city": "Dublin",
  "country": "Ireland",
  "address_line_1": "123 Main St",
  "address_line_2": "",
  "postal_code": "D01 ABC1",
  "latitude": 53.3498,
  "longitude": -6.2603,
  
  "phone": "+353 1 234 5678",
  "email": "info@grandhotel.ie",
  "website_url": "https://grandhotel.ie",
  "booking_url": "https://booking.grandhotel.ie",
  
  "booking_options": {
    "primary_cta_label": "Book a Room",
    "primary_cta_url": "https://...",
    "secondary_cta_label": "Call to Book",
    "secondary_cta_phone": "+353 1 234 5678",
    "terms_url": "https://...",
    "policies_url": "https://..."
  },
  
  "room_types": [
    {
      "code": "STD",
      "name": "Standard Room",
      "short_description": "...",
      "max_occupancy": 2,
      "bed_setup": "Queen Bed",
      "photo_url": "https://...",
      "starting_price_from": "89.00",
      "currency": "EUR",
      "booking_code": "STD-ROOM",
      "booking_url": "https://...",
      "availability_message": "High demand"
    }
  ],
  
  "offers": [
    {
      "title": "Weekend Getaway Package",
      "short_description": "...",
      "details_html": "<p>...</p>",
      "valid_from": "2025-01-01",
      "valid_to": "2025-03-31",
      "tag": "Weekend Offer",
      "book_now_url": "https://...",
      "photo_url": "https://..."
    }
  ],
  
  "leisure_activities": [
    {
      "name": "Indoor Pool",
      "category": "Wellness",
      "short_description": "...",
      "details_html": "<p>...</p>",
      "icon": "swimming-pool",
      "image_url": "https://..."
    }
  ]
}
```

#### Error Responses
- 404: Hotel not found or inactive

#### Frontend Integration Notes
- Use for hotel public landing pages
- This is marketing content only (no live booking)
- Safe to call from browser (CORS configured)
- All URLs are absolute for deep linking

#### Security
- No authentication required
- No sensitive data exposed
- No guest/booking records
- No live availability/pricing

### Acceptance Criteria
- [ ] Documentation file created
- [ ] Full request/response example included
- [ ] All fields documented
- [ ] Error cases covered
- [ ] Frontend integration notes clear
- [ ] Security considerations noted

### Related Files
- `docs/HOTEL_PUBLIC_API.md`
""",
        "labels": ["documentation", "hotel-public-api"]
    }
]


def create_issue(issue_data):
    """Create a GitHub issue using gh CLI"""
    title = issue_data["title"]
    body = issue_data["body"]
    labels = issue_data["labels"]
    
    # Build command
    cmd = [
        "gh", "issue", "create",
        "--repo", "nlekkerman/HotelMateBackend",
        "--title", title,
        "--body", body,
        "--assignee", "@me"
    ]
    
    # Add labels individually
    for label in labels:
        cmd.extend(["--label", label])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issue_url = result.stdout.strip()
        print(f"✓ Created: {title}")
        print(f"  URL: {issue_url}\n")
        return {"title": title, "url": issue_url}
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create: {title}")
        print(f"  Error: {e.stderr}\n")
        return None


def main():
    print("Creating GitHub issues for Public Hotel Page API + Booking Logic...\n")
    print("=" * 80)
    print()
    
    created_issues = []
    
    for issue in issues:
        result = create_issue(issue)
        if result:
            created_issues.append(result)
    
    print("=" * 80)
    print(f"\n✓ Created {len(created_issues)} issues\n")
    
    # Output Markdown list
    print("## Created Issues\n")
    for issue in created_issues:
        # Extract issue number from URL
        issue_num = issue["url"].split("/")[-1]
        print(f"- #{issue_num}: [{issue['title']}]({issue['url']})")


if __name__ == "__main__":
    main()
