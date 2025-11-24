# HotelMate Phase 1 - Consolidated Status & Issues

**Date:** November 24, 2025  
**Project:** HotelMate CRUD & Public Page Phase 1  
**Status:** Backend Complete ✅ | Frontend Pending 📋

---

## Table of Contents
1. [Overall Status](#overall-status)
2. [Backend Issues Status](#backend-issues-status)
3. [Frontend Issues (F1-F9)](#frontend-issues-f1-f9)
4. [Implementation Checklist](#implementation-checklist)

---

## Overall Status

### Summary
- ✅ **Backend Implementation:** 100% Complete (8/8 issues)
- 📋 **Frontend Implementation:** 0% Complete (0/9 issues)
- ✅ **API Endpoints:** All ready for frontend consumption
- ✅ **Documentation:** Complete with examples

### What's Working
- All staff CRUD APIs for hotel content management
- Quote and booking persistence
- Settings with validation
- Permission-based access control
- Public page data endpoints

### What's Needed
- Frontend UI components for F1-F9
- Integration with backend APIs
- User testing and refinement

---

## Backend Issues Status

### ✅ COMPLETED - Backend Issues B1-B8

All backend issues from `issues_for_pase_on_pt_3.MD` are **COMPLETE** and production-ready.

| Issue | Title | Status | Implementation |
|-------|-------|--------|----------------|
| **B1** | Create/Update All Required Serializers | ✅ Complete | `hotel/serializers.py`, `rooms/serializers.py` |
| **B2** | Extend HotelPublicDetailSerializer | ✅ Complete | `hotel/serializers.py` - includes `public_settings` |
| **B3** | Update HotelPublicSettingsView | ✅ Complete | Already correct, no changes needed |
| **B4** | Extend HotelPublicSettingsStaffView | ✅ Complete | Added validation for colors, lists |
| **B5** | Add Staff CRUD Views | ✅ Complete | `hotel/staff_views.py` - 5 viewsets |
| **B6** | Wire HotelPricingQuoteView to Model | ✅ Complete | Persists to `PricingQuote` model |
| **B7** | Refactor HotelBookingCreateView | ✅ Complete | Persists to `RoomBooking` model |
| **B8** | Improve Staff Booking Views | ✅ Complete | Enhanced filters and validation |

**Documentation:** 
- Full details in `docs/PHASE1_IMPLEMENTATION_COMPLETE.md`
- API examples in `docs/PHASE1_IMPLEMENTATION_PLAN.md`

---

### 🔄 REVIEW NEEDED - Backend Issues 1-10 (new_issues_phase_one.MD)

These issues have significant overlap with B1-B8. Here's the reconciliation:

| Issue | Title | Status | Notes |
|-------|-------|--------|-------|
| **1** | Finalize HotelPublicSettings Model | ✅ Already Done | Model exists with all fields (B1, B4) |
| **2** | Public Read-Only Endpoint | ✅ Already Done | `HotelPublicSettingsView` exists (B3) |
| **3** | Staff-Only Update Endpoint | ✅ Already Done | `HotelPublicSettingsStaffView` with permissions (B4) |
| **4** | Adjust Auth/Me Endpoint | ⚠️ **NEEDED** | Frontend needs staff info in auth response |
| **5** | Tests for Public Settings API | ⚠️ **NEEDED** | No tests written yet |
| **6** | Django Admin Integration | ⚠️ **NEEDED** | Admin registration not done |
| **7** | Staff Bookings List Endpoint | ✅ Already Done | `StaffBookingsListView` exists (B8) |
| **8** | Booking Confirmation Endpoint | ✅ Already Done | `StaffBookingConfirmView` exists (B8) |
| **9** | Send Confirmation Email | ⚠️ **PARTIAL** | Stub exists, needs implementation |
| **10** | Tests for Booking APIs | ⚠️ **NEEDED** | No tests written yet |

### 📋 Remaining Backend Tasks

#### Issue 4: Auth/Me Endpoint Enhancement
**Priority:** HIGH (Required for frontend F2-F8)  
**File:** `staff/views.py` or equivalent auth view  
**Changes Needed:**
```python
# Add to auth/me serializer response:
{
    "is_staff_member": True,
    "staff": {
        "hotel_slug": "hotel-killarney",
        "access_level": "staff_admin",
        "role_slug": "manager",
        "can_edit_public_page": True
    }
}
```

#### Issue 6: Django Admin Registration
**Priority:** LOW (Nice to have)  
**File:** `hotel/admin.py`  
**Task:** Register `HotelPublicSettings`, `Offer`, `LeisureActivity` models

#### Issue 9: Email Confirmation Implementation
**Priority:** MEDIUM  
**File:** `hotel/email_utils.py` (create)  
**Task:** Implement actual email sending (currently stubbed)

#### Issues 5 & 10: Test Coverage
**Priority:** HIGH (Before production)  
**Files:** `hotel/tests/`, `bookings/tests/`  
**Task:** Write comprehensive API tests

---

## Frontend Issues (F1-F9)

All frontend issues are ready to implement. Backend APIs are complete and documented.

---

### 📋 Issue F1: Public Hotel Page Rendering

**Type:** Feature  
**Priority:** HIGH  
**Dependencies:** None (public API already exists)  
**Estimated Time:** 8-12 hours

#### Description
Build the complete public hotel page that displays all hotel information, room types, offers, and leisure activities using the consolidated public page API.

#### Backend API
**Endpoint:** `GET /api/public/hotels/<slug>/page/`

**Response Structure:**
```json
{
  "slug": "hotel-killarney",
  "name": "Hotel Killarney",
  "tagline": "Luxury in the Heart of Kerry",
  "hero_image_url": "https://...",
  "logo_url": "https://...",
  "short_description": "...",
  "long_description": "...",
  "city": "Killarney",
  "country": "Ireland",
  "address_line_1": "...",
  "phone": "+353...",
  "email": "...",
  "booking_options": {
    "primary_cta_label": "Book a Room",
    "primary_cta_url": "...",
    "secondary_cta_label": "Call to Book",
    "secondary_cta_phone": "..."
  },
  "public_settings": {
    "welcome_message": "...",
    "gallery": ["url1", "url2"],
    "amenities": ["WiFi", "Pool", "Spa"],
    "primary_color": "#3B82F6",
    "theme_mode": "light"
  },
  "room_types": [...],
  "offers": [...],
  "leisure_activities": [...]
}
```

#### Tasks
- [ ] Create `HotelPublicPage.jsx` component
- [ ] Implement data fetching using API endpoint
- [ ] **Hero Section:**
  - [ ] Display hero_image_url as background
  - [ ] Show hotel name and tagline overlay
  - [ ] Render primary and secondary CTAs
  - [ ] Display location (city, country)
- [ ] **About Section:**
  - [ ] Render welcome_message
  - [ ] Display long_description
  - [ ] Show amenities list with icons
- [ ] **Gallery Section:**
  - [ ] Create image carousel/grid from `public_settings.gallery`
  - [ ] Implement lightbox for full-size viewing
- [ ] **Rooms & Suites Section:**
  - [ ] Map through `room_types` array
  - [ ] Display room cards with:
    - Photo, name, description
    - Max occupancy, bed setup
    - Starting price
    - Availability message
    - Booking CTA
- [ ] **Special Offers Section:**
  - [ ] Map through `offers` array
  - [ ] Display offer cards with:
    - Photo, title, description
    - Tag (e.g., "Weekend Special")
    - Valid dates
    - Book Now CTA
  - [ ] Filter out expired offers (check valid_to)
- [ ] **Leisure & Facilities Section:**
  - [ ] Group activities by category
  - [ ] Display grouped sections:
    - Wellness, Family, Dining, Sports, etc.
  - [ ] Show activity cards with icon/image, name, description
- [ ] **Contact & Footer:**
  - [ ] Display contact info from `public_settings`
  - [ ] Show address, phone, email
  - [ ] Include map integration (optional)
  - [ ] Footer with policies links

#### Styling
- [ ] Apply branding colors from `public_settings`:
  - primary_color for main elements
  - secondary_color for accents
  - button_color for CTAs
- [ ] Support theme_mode (light/dark)
- [ ] Ensure responsive design (mobile, tablet, desktop)
- [ ] Add loading states
- [ ] Handle error states (404, network errors)

#### Acceptance Criteria
✅ Page fetches and displays all data from API  
✅ All sections render correctly with actual content  
✅ Branding colors are applied from settings  
✅ CTAs link to correct booking URLs  
✅ Gallery displays all images  
✅ Room types show accurate pricing  
✅ Offers display with date validation  
✅ Activities grouped by category  
✅ Page is fully responsive  
✅ Loading and error states handled  

#### Testing
- [ ] Load page for multiple hotels
- [ ] Verify all images load correctly
- [ ] Test all CTA buttons
- [ ] Verify mobile responsiveness
- [ ] Test with missing optional data
- [ ] Performance check (page load time)

---

### 📋 Issue F2: Hotel Settings - Public Page Content & Branding

**Type:** Feature  
**Priority:** HIGH  
**Dependencies:** Issue 4 (Auth/Me endpoint)  
**Estimated Time:** 10-15 hours

#### Description
Create a staff-only settings section where hotel staff can edit all public page content, branding colors, gallery, amenities, and contact information.

#### Backend API
**Endpoints:**
- `GET /api/staff/hotels/<hotel_slug>/hotel/settings/` - Fetch current settings
- `PUT/PATCH /api/staff/hotels/<hotel_slug>/hotel/settings/` - Update settings

**Request Body (PATCH example):**
```json
{
  "welcome_message": "Welcome to our beautiful hotel",
  "short_description": "...",
  "long_description": "...",
  "hero_image": "https://...",
  "gallery": ["url1", "url2", "url3"],
  "amenities": ["WiFi", "Pool", "Spa", "Gym"],
  "contact_email": "info@hotel.com",
  "contact_phone": "+353 1 234 5678",
  "contact_address": "123 Main St, Killarney",
  "primary_color": "#3B82F6",
  "secondary_color": "#10B981",
  "accent_color": "#F59E0B",
  "background_color": "#FFFFFF",
  "button_color": "#3B82F6",
  "theme_mode": "light"
}
```

**Validation:**
- Colors must be valid HEX format (#RRGGBB)
- Gallery must be array of strings
- Amenities must be array of strings

#### Tasks

**Page Structure:**
- [ ] Create `HotelSettingsPage.jsx` with tabbed layout
- [ ] Create `PublicContentTab.jsx` component
- [ ] Implement permission check (staff only, same hotel)
- [ ] Add navigation between settings sections

**Content Section:**
- [ ] **Welcome Message Field**
  - [ ] Textarea with character counter
  - [ ] Live preview option
- [ ] **Short Description Field**
  - [ ] Textarea (150-300 chars recommended)
- [ ] **Long Description Field**
  - [ ] Rich text editor OR large textarea
  - [ ] Formatting support (bold, italic, lists)
- [ ] **Hero Image**
  - [ ] Image upload widget OR URL input
  - [ ] Preview thumbnail
  - [ ] Clear/remove button

**Gallery Manager:**
- [ ] **Image List Display**
  - [ ] Show all gallery images as thumbnails
  - [ ] Display in sortable grid
- [ ] **Add Image**
  - [ ] Upload button OR URL input modal
  - [ ] Multiple upload support
- [ ] **Remove Image**
  - [ ] Delete button on each thumbnail
  - [ ] Confirmation dialog
- [ ] **Reorder Images**
  - [ ] Drag-and-drop reordering
  - [ ] Up/down buttons alternative

**Amenities Manager:**
- [ ] **Tag List Display**
  - [ ] Show amenities as removable tags/chips
- [ ] **Add Amenity**
  - [ ] Text input with "Add" button
  - [ ] Autocomplete suggestions (optional)
- [ ] **Remove Amenity**
  - [ ] X button on each tag
- [ ] **Common Amenities Quick-Add**
  - [ ] Preset buttons: WiFi, Pool, Spa, Gym, Restaurant, Bar, Parking

**Contact Information:**
- [ ] **Contact Email**
  - [ ] Email input with validation
- [ ] **Contact Phone**
  - [ ] Phone input with format validation
- [ ] **Contact Address**
  - [ ] Textarea for full address

**Branding Section:**
- [ ] **Color Pickers**
  - [ ] Primary Color picker
  - [ ] Secondary Color picker
  - [ ] Accent Color picker
  - [ ] Background Color picker
  - [ ] Button Color picker
  - [ ] Show HEX value input
  - [ ] Live preview of color changes
- [ ] **Theme Mode**
  - [ ] Radio buttons: Light / Dark / Custom
- [ ] **Preview Panel**
  - [ ] Show sample UI with current colors
  - [ ] Update in real-time as colors change

**Form Management:**
- [ ] Fetch current settings on mount
- [ ] Track dirty state (unsaved changes)
- [ ] **Save Button**
  - [ ] Disabled when no changes
  - [ ] Loading state during save
  - [ ] Success notification
  - [ ] Error handling with specific messages
- [ ] **Reset Button**
  - [ ] Revert to last saved state
  - [ ] Confirmation dialog
- [ ] **Validation**
  - [ ] HEX color format validation
  - [ ] Email format validation
  - [ ] Phone format validation
  - [ ] Gallery array validation
  - [ ] Show inline error messages

#### Component Structure
```
HotelSettingsPage/
├── HotelSettingsTabs.jsx
├── PublicContentTab/
│   ├── ContentSection.jsx
│   ├── GalleryManager.jsx
│   ├── AmenitiesManager.jsx
│   ├── ContactSection.jsx
│   └── BrandingSection.jsx
└── components/
    ├── ColorPicker.jsx
    ├── ImageUploader.jsx
    ├── TagInput.jsx
    └── RichTextEditor.jsx
```

#### Acceptance Criteria
✅ Only authenticated staff from correct hotel can access  
✅ All current settings load correctly  
✅ All fields are editable  
✅ Gallery supports add/remove/reorder  
✅ Amenities support add/remove  
✅ Color pickers validate HEX format  
✅ Form validation shows clear errors  
✅ Save successfully updates settings  
✅ Changes reflect on public page (F1)  
✅ Unsaved changes warning on navigation  
✅ Success/error notifications work  

#### Testing
- [ ] Load settings for staff's hotel
- [ ] Edit each field type
- [ ] Test color picker validation
- [ ] Add/remove gallery images
- [ ] Add/remove amenities
- [ ] Save with valid data
- [ ] Save with invalid data (verify errors)
- [ ] Verify changes appear on public page
- [ ] Test permission blocking (wrong hotel)

---

### 📋 Issue F3: Hotel Settings - Booking & CTA Options

**Type:** Feature  
**Priority:** MEDIUM  
**Dependencies:** F2 (Settings page structure)  
**Estimated Time:** 4-6 hours

#### Description
Create a settings section for managing booking call-to-action buttons, labels, and policy links that appear on the public hotel page.

#### Backend API
**Note:** This uses the existing `booking_options` relationship on the Hotel model.

**Endpoints:**
- `GET /api/staff/hotels/<hotel_slug>/hotel/settings/` - Already returns `booking_options`
- Update may need separate endpoint OR extend existing settings endpoint

**Data Structure:**
```json
{
  "booking_options": {
    "primary_cta_label": "Book a Room",
    "primary_cta_url": "https://booking.example.com",
    "secondary_cta_label": "Call to Book",
    "secondary_cta_phone": "+353 1 234 5678",
    "terms_url": "https://hotel.com/terms",
    "policies_url": "https://hotel.com/policies"
  }
}
```

#### Tasks

**Page Integration:**
- [ ] Add "Booking & CTAs" tab to `HotelSettingsPage`
- [ ] Create `BookingCTATab.jsx` component

**Primary CTA Section:**
- [ ] **Primary CTA Label**
  - [ ] Text input (e.g., "Book a Room", "Reserve Now")
  - [ ] Character limit (50 chars)
- [ ] **Primary CTA URL**
  - [ ] URL input with validation
  - [ ] Test link button (opens in new tab)
  - [ ] Placeholder suggestions

**Secondary CTA Section:**
- [ ] **Secondary CTA Label**
  - [ ] Text input (e.g., "Call to Book", "Contact Us")
  - [ ] Optional field
- [ ] **Secondary CTA Phone**
  - [ ] Phone input with format validation
  - [ ] Click-to-call preview
  - [ ] Format examples shown

**Policy Links:**
- [ ] **Terms & Conditions URL**
  - [ ] URL input with validation
  - [ ] Test link button
- [ ] **Booking Policies URL**
  - [ ] URL input with validation
  - [ ] Test link button

**Preview Section:**
- [ ] **Live CTA Preview**
  - [ ] Show how CTAs will appear on public page
  - [ ] Primary button preview with label
  - [ ] Secondary button/link preview
  - [ ] Update preview on field changes

**Form Management:**
- [ ] Load current booking options
- [ ] Track changes
- [ ] Validate all fields
- [ ] Save changes to backend
- [ ] Success/error notifications

#### Component Structure
```
BookingCTATab/
├── PrimaryCTASection.jsx
├── SecondaryCTASection.jsx
├── PolicyLinksSection.jsx
└── CTAPreview.jsx
```

#### Acceptance Criteria
✅ All booking option fields are editable  
✅ URL validation works correctly  
✅ Phone validation formats correctly  
✅ Preview shows accurate representation  
✅ Test links open correctly  
✅ Save updates booking options  
✅ Changes reflect on public page hero section  
✅ Optional fields can be empty  

#### Testing
- [ ] Load existing booking options
- [ ] Edit all fields
- [ ] Test URL validation (valid/invalid)
- [ ] Test phone validation
- [ ] Save with valid data
- [ ] Verify changes on public page
- [ ] Test with optional fields empty
- [ ] Test "Test link" buttons

---

### 📋 Issue F4: Hotel Settings - Rooms & Suites (Marketing)

**Type:** Feature  
**Priority:** HIGH  
**Dependencies:** F2 (Settings page structure)  
**Estimated Time:** 12-16 hours

#### Description
Create a CRUD interface for managing room types that appear on the public hotel page. These are marketing representations, not physical room inventory.

#### Backend API
**Endpoints:**
- `GET /api/staff/hotels/<hotel_slug>/hotel/staff/room-types/` - List all room types
- `POST /api/staff/hotels/<hotel_slug>/hotel/staff/room-types/` - Create new
- `GET /api/staff/hotels/<hotel_slug>/hotel/staff/room-types/{id}/` - Get one
- `PUT/PATCH /api/staff/hotels/<hotel_slug>/hotel/staff/room-types/{id}/` - Update
- `DELETE /api/staff/hotels/<hotel_slug>/hotel/staff/room-types/{id}/` - Delete

**Room Type Structure:**
```json
{
  "id": 1,
  "code": "DLX",
  "name": "Deluxe Suite",
  "short_description": "Spacious suite with lake view",
  "max_occupancy": 4,
  "bed_setup": "1 King Bed + 1 Sofa Bed",
  "photo": null,
  "photo_url": "https://...",
  "starting_price_from": "199.00",
  "currency": "EUR",
  "booking_code": "DELUXE",
  "booking_url": "https://booking.com/...",
  "availability_message": "High demand",
  "sort_order": 1,
  "is_active": true
}
```

#### Tasks

**Page Structure:**
- [ ] Add "Rooms & Suites" tab to `HotelSettingsPage`
- [ ] Create `RoomTypesTab.jsx` component

**List View:**
- [ ] **Room Types Table/Grid**
  - [ ] Display all room types sorted by sort_order
  - [ ] Show: Photo thumbnail, name, max occupancy, price, status
  - [ ] Active/Inactive badge
  - [ ] Actions: Edit, Delete, Reorder
- [ ] **Empty State**
  - [ ] Message when no room types exist
  - [ ] "Add First Room Type" CTA
- [ ] **Add Room Type Button**
  - [ ] Prominent button at top
  - [ ] Opens create modal/form

**Reordering:**
- [ ] **Drag-and-Drop**
  - [ ] Drag handle on each row
  - [ ] Visual feedback during drag
  - [ ] Auto-save new order
- [ ] **Alternative: Up/Down Buttons**
  - [ ] Move up/down one position
  - [ ] Save order after changes

**Create/Edit Form:**
- [ ] **Basic Information**
  - [ ] Room Type Name (required)
  - [ ] Code (optional, short identifier)
  - [ ] Short Description (textarea, 150-300 chars)
- [ ] **Occupancy Details**
  - [ ] Max Occupancy (number input)
  - [ ] Bed Setup (text input, e.g., "2 Queen Beds")
- [ ] **Photo Management**
  - [ ] Image upload widget
  - [ ] URL input alternative
  - [ ] Current photo preview
  - [ ] Remove photo option
- [ ] **Pricing Information**
  - [ ] Starting Price (decimal input)
  - [ ] Currency (select: EUR, USD, GBP, etc.)
  - [ ] Price display format preview
- [ ] **Booking Integration**
  - [ ] Booking Code (optional)
  - [ ] Booking URL (optional, external link)
- [ ] **Marketing**
  - [ ] Availability Message (text input)
    - Examples: "High demand", "Last rooms", "Best value"
- [ ] **Visibility**
  - [ ] Active toggle (show/hide on public page)
  - [ ] Sort Order (number input)

**Form Modal/Drawer:**
- [ ] Open modal for create/edit
- [ ] Form validation
- [ ] Save button (loading state)
- [ ] Cancel button (with unsaved changes warning)
- [ ] Delete button (edit mode only)

**Delete Functionality:**
- [ ] Confirmation dialog
- [ ] Warning message
- [ ] Soft delete if bookings exist (optional)
- [ ] Success notification

**Bulk Actions:**
- [ ] Select multiple room types (checkboxes)
- [ ] Bulk activate/deactivate
- [ ] Bulk delete (with confirmation)

#### Component Structure
```
RoomTypesTab/
├── RoomTypesList.jsx
├── RoomTypeCard.jsx
├── RoomTypeForm.jsx (modal)
├── RoomTypeFormFields/
│   ├── BasicInfoSection.jsx
│   ├── OccupancySection.jsx
│   ├── PhotoSection.jsx
│   ├── PricingSection.jsx
│   └── BookingSection.jsx
└── components/
    ├── DragDropList.jsx
    ├── DeleteConfirmDialog.jsx
    └── EmptyState.jsx
```

#### Acceptance Criteria
✅ Staff can view all room types for their hotel  
✅ Can create new room types with all fields  
✅ Can edit existing room types  
✅ Can delete room types with confirmation  
✅ Can reorder room types (affects public page display order)  
✅ Can toggle active/inactive status  
✅ Photo upload works correctly  
✅ Form validation prevents invalid data  
✅ Changes reflect immediately on public page  
✅ Inactive room types don't show on public page  

#### Testing
- [ ] Create new room type with all fields
- [ ] Create with minimal fields (only required)
- [ ] Edit existing room type
- [ ] Upload/change photo
- [ ] Delete room type
- [ ] Reorder room types (verify order on public page)
- [ ] Toggle active/inactive
- [ ] Test form validation (invalid data)
- [ ] Verify changes on public page (F1)

---

### 📋 Issue F5: Hotel Settings - Offers & Packages

**Type:** Feature  
**Priority:** HIGH  
**Dependencies:** F2 (Settings page structure)  
**Estimated Time:** 10-14 hours

#### Description
Create a CRUD interface for managing special offers, packages, and deals that appear on the public hotel page.

#### Backend API
**Endpoints:**
- `GET /api/staff/hotels/<hotel_slug>/hotel/staff/offers/` - List all offers
- `POST /api/staff/hotels/<hotel_slug>/hotel/staff/offers/` - Create new
- `GET /api/staff/hotels/<hotel_slug>/hotel/staff/offers/{id}/` - Get one
- `PUT/PATCH /api/staff/hotels/<hotel_slug>/hotel/staff/offers/{id}/` - Update
- `DELETE /api/staff/hotels/<hotel_slug>/hotel/staff/offers/{id}/` - Delete

**Offer Structure:**
```json
{
  "id": 1,
  "title": "Weekend Getaway Package",
  "short_description": "Save 20% on weekend stays",
  "details_text": "Plain text details...",
  "details_html": "<p>Rich HTML details...</p>",
  "valid_from": "2025-06-01",
  "valid_to": "2025-08-31",
  "tag": "Weekend Special",
  "book_now_url": "https://booking.com/...",
  "photo": null,
  "photo_url": "https://...",
  "sort_order": 1,
  "is_active": true,
  "created_at": "2025-11-24T10:00:00Z"
}
```

#### Tasks

**Page Structure:**
- [ ] Add "Offers & Packages" tab to `HotelSettingsPage`
- [ ] Create `OffersTab.jsx` component

**List View:**
- [ ] **Offers Table/Grid**
  - [ ] Display all offers sorted by sort_order
  - [ ] Show: Photo, title, tag, valid dates, status
  - [ ] Active/Inactive badge
  - [ ] Expired badge (when valid_to < today)
  - [ ] Actions: Edit, Delete, Duplicate, Reorder
- [ ] **Filters**
  - [ ] Active/Inactive filter
  - [ ] Valid/Expired filter
  - [ ] Search by title/tag
- [ ] **Empty State**
  - [ ] Message when no offers exist
  - [ ] "Create First Offer" CTA
- [ ] **Add Offer Button**
  - [ ] Opens create modal/form

**Reordering:**
- [ ] Drag-and-drop reordering
- [ ] Alternative: Up/down arrows
- [ ] Auto-save new order

**Create/Edit Form:**
- [ ] **Basic Information**
  - [ ] Offer Title (required, max 200 chars)
  - [ ] Tag (text input, e.g., "Summer Sale", "Family Deal")
  - [ ] Short Description (required, 150-300 chars)
    - Used for cards on public page
- [ ] **Detailed Description**
  - [ ] Details Text (plain textarea) OR
  - [ ] Details HTML (rich text editor)
  - [ ] Tab to switch between text/HTML
  - [ ] Preview pane for HTML
- [ ] **Validity Period**
  - [ ] Valid From (date picker, required)
  - [ ] Valid To (date picker, required)
  - [ ] Validation: valid_to must be after valid_from
  - [ ] Show "Currently Valid" or "Expired" status
- [ ] **Photo Management**
  - [ ] Image upload widget
  - [ ] URL input alternative
  - [ ] Photo preview
  - [ ] Remove photo option
  - [ ] Recommended dimensions shown
- [ ] **Booking Integration**
  - [ ] Book Now URL (optional)
  - [ ] Test link button
- [ ] **Display Settings**
  - [ ] Active toggle
  - [ ] Sort Order (number input)

**Form Modal/Drawer:**
- [ ] Larger modal/full-page drawer (more content)
- [ ] Tabbed sections or scrollable form
- [ ] Form validation
- [ ] Save button (loading state)
- [ ] Cancel button
- [ ] Duplicate button (creates copy)

**Date Management:**
- [ ] Visual indicator for expired offers
- [ ] Option to extend dates (quick action)
- [ ] Auto-hide expired offers (optional setting)

**Duplicate Feature:**
- [ ] Copy existing offer as template
- [ ] Open in edit mode
- [ ] Update title to "Copy of [Original]"
- [ ] Clear dates or adjust forward

#### Component Structure
```
OffersTab/
├── OffersList.jsx
├── OfferCard.jsx
├── OfferForm.jsx (modal/drawer)
├── OfferFormSections/
│   ├── BasicInfoSection.jsx
│   ├── DescriptionSection.jsx
│   ├── ValiditySection.jsx
│   ├── PhotoSection.jsx
│   └── BookingSection.jsx
└── components/
    ├── RichTextEditor.jsx
    ├── DateRangePicker.jsx
    └── ExpiredBadge.jsx
```

#### Acceptance Criteria
✅ Staff can view all offers with status indicators  
✅ Can create new offers with all fields  
✅ Can edit existing offers  
✅ Can delete offers with confirmation  
✅ Can duplicate offers  
✅ Can reorder offers  
✅ Can toggle active/inactive  
✅ Date validation prevents invalid ranges  
✅ Expired offers are visually distinct  
✅ Photo upload works correctly  
✅ Rich text editor works for details_html  
✅ Changes reflect on public page  
✅ Only valid, active offers show on public page  

#### Testing
- [ ] Create new offer with all fields
- [ ] Create with minimal fields
- [ ] Edit existing offer
- [ ] Upload/change photo
- [ ] Delete offer
- [ ] Duplicate offer
- [ ] Set dates (valid/invalid ranges)
- [ ] Test expired offers (valid_to in past)
- [ ] Reorder offers
- [ ] Toggle active/inactive
- [ ] Verify on public page (only valid, active shown)

---

### 📋 Issue F6: Hotel Settings - Leisure & Facilities

**Type:** Feature  
**Priority:** MEDIUM  
**Dependencies:** F2 (Settings page structure)  
**Estimated Time:** 8-12 hours

#### Description
Create a CRUD interface for managing leisure activities and hotel facilities that appear grouped by category on the public hotel page.

#### Backend API
**Endpoints:**
- `GET /api/staff/hotels/<hotel_slug>/hotel/staff/leisure-activities/` - List all
- `POST /api/staff/hotels/<hotel_slug>/hotel/staff/leisure-activities/` - Create
- `GET /api/staff/hotels/<hotel_slug>/hotel/staff/leisure-activities/{id}/` - Get one
- `PUT/PATCH /api/staff/hotels/<hotel_slug>/hotel/staff/leisure-activities/{id}/` - Update
- `DELETE /api/staff/hotels/<hotel_slug>/hotel/staff/leisure-activities/{id}/` - Delete

**Leisure Activity Structure:**
```json
{
  "id": 1,
  "name": "Indoor Pool",
  "category": "Wellness",
  "short_description": "Heated indoor pool open year-round",
  "details_html": "<p>Full details...</p>",
  "icon": "pool",
  "image": null,
  "image_url": "https://...",
  "sort_order": 1,
  "is_active": true
}
```

**Categories:**
- Wellness
- Family
- Dining
- Sports
- Entertainment
- Business
- Other

#### Tasks

**Page Structure:**
- [ ] Add "Leisure & Facilities" tab to `HotelSettingsPage`
- [ ] Create `LeisureActivitiesTab.jsx` component

**List View:**
- [ ] **Grouped Display**
  - [ ] Group activities by category
  - [ ] Collapsible category sections
  - [ ] Show count per category
  - [ ] Sort by sort_order within each category
- [ ] **Activity Cards**
  - [ ] Photo/icon thumbnail
  - [ ] Name and category badge
  - [ ] Short description preview
  - [ ] Active status indicator
  - [ ] Actions: Edit, Delete, Reorder
- [ ] **Category Filter**
  - [ ] Filter dropdown or tabs
  - [ ] "All" option to show everything
  - [ ] Count badges on category tabs
- [ ] **Add Activity Button**
  - [ ] Opens create modal

**Reordering:**
- [ ] Drag-and-drop within category
- [ ] Cannot drag between categories
- [ ] Up/down buttons alternative

**Create/Edit Form:**
- [ ] **Basic Information**
  - [ ] Activity Name (required)
  - [ ] Category (required dropdown)
    - Wellness, Family, Dining, Sports, Entertainment, Business, Other
  - [ ] Short Description (required, 100-200 chars)
    - For card display
- [ ] **Detailed Description**
  - [ ] Details HTML (rich text editor)
  - [ ] Preview pane
  - [ ] Optional field
- [ ] **Visual Elements**
  - [ ] Icon selector (text input or icon picker)
    - Material Icons, Font Awesome, or custom
  - [ ] Image upload
  - [ ] URL input alternative
  - [ ] Preview thumbnail
- [ ] **Display Settings**
  - [ ] Active toggle
  - [ ] Sort Order (within category)

**Icon Selector (Optional Enhancement):**
- [ ] Icon picker modal
- [ ] Search icons by keyword
- [ ] Preview selected icon
- [ ] Save icon name/class

**Bulk Actions:**
- [ ] Select multiple activities
- [ ] Bulk activate/deactivate
- [ ] Bulk delete
- [ ] Bulk move to different category

#### Component Structure
```
LeisureActivitiesTab/
├── ActivitiesList.jsx
├── CategoryGroup.jsx
├── ActivityCard.jsx
├── ActivityForm.jsx (modal)
├── ActivityFormSections/
│   ├── BasicInfoSection.jsx
│   ├── DescriptionSection.jsx
│   └── VisualSection.jsx
└── components/
    ├── IconPicker.jsx (optional)
    └── CategoryBadge.jsx
```

#### Acceptance Criteria
✅ Staff can view activities grouped by category  
✅ Can create new activities with all fields  
✅ Can edit existing activities  
✅ Can delete activities with confirmation  
✅ Can reorder within categories  
✅ Can toggle active/inactive  
✅ Category selection works correctly  
✅ Icon/image display works  
✅ Changes reflect on public page  
✅ Inactive activities don't show publicly  
✅ Activities display grouped by category on public page  

#### Testing
- [ ] Create activity in each category
- [ ] Edit existing activity
- [ ] Change category (move activity)
- [ ] Upload/change image
- [ ] Set icon
- [ ] Delete activity
- [ ] Reorder within category
- [ ] Toggle active/inactive
- [ ] Verify grouping on public page
- [ ] Test category filter

---

### 📋 Issue F7: Hotel Settings - Rooms (Inventory Management)

**Type:** Feature  
**Priority:** MEDIUM  
**Dependencies:** F2 (Settings page structure)  
**Estimated Time:** 10-14 hours

#### Description
Create a CRUD interface for managing physical room inventory, guest PINs, and QR codes for room services.

#### Backend API
**Endpoints:**
- `GET /api/staff/hotels/<hotel_slug>/hotel/staff/rooms/` - List all rooms
- `POST /api/staff/hotels/<hotel_slug>/hotel/staff/rooms/` - Create room
- `GET /api/staff/hotels/<hotel_slug>/hotel/staff/rooms/{id}/` - Get one
- `PUT/PATCH /api/staff/hotels/<hotel_slug>/hotel/staff/rooms/{id}/` - Update
- `DELETE /api/staff/hotels/<hotel_slug>/hotel/staff/rooms/{id}/` - Delete
- `POST /api/staff/hotels/<hotel_slug>/hotel/staff/rooms/{id}/generate_pin/` - Generate guest PIN
- `POST /api/staff/hotels/<hotel_slug>/hotel/staff/rooms/{id}/generate_qr/` - Generate QR code

**Room Structure:**
```json
{
  "id": 1,
  "room_number": 101,
  "is_occupied": false,
  "guest_id_pin": "a3f9",
  "room_service_qr_code": "https://cloudinary.../qr1.png",
  "in_room_breakfast_qr_code": "https://cloudinary.../qr2.png",
  "dinner_booking_qr_code": "https://cloudinary.../qr3.png",
  "chat_pin_qr_code": "https://cloudinary.../qr4.png"
}
```

**QR Code Types:**
- `room_service` - Room service menu ordering
- `breakfast` - In-room breakfast ordering
- `restaurant` - Restaurant booking (needs restaurant_slug param)
- `chat_pin` - Guest chat PIN validation

#### Tasks

**Page Structure:**
- [ ] Add "Room Inventory" tab to `HotelSettingsPage`
- [ ] Create `RoomInventoryTab.jsx` component

**List View:**
- [ ] **Rooms Table**
  - [ ] Display all rooms sorted by room_number
  - [ ] Columns: Room #, Status, Guest PIN, QR Codes, Actions
  - [ ] Status indicator (Occupied/Vacant)
  - [ ] QR code status (Generated/Missing)
- [ ] **Filters**
  - [ ] Occupied/Vacant filter
  - [ ] Search by room number
- [ ] **Add Room Button**
  - [ ] Opens create form
- [ ] **Bulk Actions**
  - [ ] Select multiple rooms
  - [ ] Bulk generate PINs
  - [ ] Bulk generate QR codes

**Create/Edit Form:**
- [ ] **Basic Information**
  - [ ] Room Number (required, unique per hotel)
  - [ ] Occupied Status (toggle/checkbox)
- [ ] **Guest PIN Section**
  - [ ] Display current PIN (if exists)
  - [ ] Generate New PIN button
  - [ ] Copy PIN button
  - [ ] PIN format display (4 chars, alphanumeric)
- [ ] **QR Codes Section**
  - [ ] Room Service QR
    - Generate button
    - Download button
    - Preview thumbnail
  - [ ] Breakfast QR
    - Generate button
    - Download button
    - Preview thumbnail
  - [ ] Restaurant Booking QR
    - Restaurant selector dropdown
    - Generate button
    - Download button
    - Preview thumbnail
  - [ ] Chat PIN QR
    - Generate button
    - Download button
    - Preview thumbnail

**Room Detail View:**
- [ ] Modal or drawer showing full room details
- [ ] All QR codes displayed large
- [ ] Download all QR codes (ZIP)
- [ ] Print view for QR codes
- [ ] PIN display with copy button

**PIN Generation:**
- [ ] Click "Generate PIN" button
- [ ] API call to generate endpoint
- [ ] Display new PIN immediately
- [ ] Show success notification
- [ ] Confirm dialog (PIN will change for guest)

**QR Code Generation:**
- [ ] QR type selector (for generate_qr action)
- [ ] Additional params modal (e.g., restaurant for dinner booking)
- [ ] Generate button triggers API
- [ ] Loading state during generation
- [ ] Display generated QR immediately
- [ ] Download individual QR code
- [ ] Regenerate option

**Bulk Operations:**
- [ ] Select rooms (checkboxes)
- [ ] Bulk Generate All QRs button
- [ ] Progress indicator for bulk operations
- [ ] Success/error summary

**Print/Export:**
- [ ] Print-friendly view for selected rooms
- [ ] Shows room number + all QR codes
- [ ] Download as PDF (optional)
- [ ] Download all QRs as ZIP

#### Component Structure
```
RoomInventoryTab/
├── RoomsList.jsx
├── RoomRow.jsx
├── RoomForm.jsx (modal)
├── RoomDetailView.jsx (modal)
├── RoomFormSections/
│   ├── BasicInfoSection.jsx
│   ├── GuestPINSection.jsx
│   └── QRCodesSection.jsx
└── components/
    ├── QRCodeCard.jsx
    ├── PINDisplay.jsx
    ├── QRGenerator.jsx
    └── PrintView.jsx
```

#### Acceptance Criteria
✅ Staff can view all rooms for their hotel  
✅ Can create new rooms with room number  
✅ Can edit room details  
✅ Can delete rooms with confirmation  
✅ Can generate guest PINs  
✅ Can generate individual QR codes  
✅ Can generate multiple QR code types  
✅ QR codes display and download correctly  
✅ Occupied status can be toggled  
✅ Bulk operations work for multiple rooms  
✅ Print view shows all QR codes clearly  

#### Testing
- [ ] Create new room
- [ ] Edit room number
- [ ] Toggle occupied status
- [ ] Generate guest PIN
- [ ] Generate room service QR
- [ ] Generate breakfast QR
- [ ] Generate restaurant booking QR (with restaurant param)
- [ ] Generate chat PIN QR
- [ ] Download individual QR code
- [ ] Download all QR codes for a room
- [ ] Delete room
- [ ] Bulk generate QRs for multiple rooms
- [ ] Test print view
- [ ] Verify QR codes scan correctly

---

### 📋 Issue F8: Hotel Settings - Access Configuration

**Type:** Feature  
**Priority:** LOW  
**Dependencies:** F2 (Settings page structure)  
**Estimated Time:** 4-6 hours

#### Description
Create a settings section for managing hotel portal access configuration, including guest/staff portal toggles, PIN requirements, and session limits.

#### Backend API
**Endpoints:**
- `GET /api/staff/hotels/<hotel_slug>/hotel/staff/access-config/` - Get config (may need ID)
- `PUT/PATCH /api/staff/hotels/<hotel_slug>/hotel/staff/access-config/{id}/` - Update

**Access Config Structure:**
```json
{
  "guest_portal_enabled": true,
  "staff_portal_enabled": true,
  "requires_room_pin": true,
  "room_pin_length": 4,
  "rotate_pin_on_checkout": true,
  "allow_multiple_guest_sessions": true,
  "max_active_guest_devices_per_room": 5
}
```

#### Tasks

**Page Structure:**
- [ ] Add "Access Configuration" tab to `HotelSettingsPage`
- [ ] Create `AccessConfigTab.jsx` component

**Portal Settings Section:**
- [ ] **Guest Portal Toggle**
  - [ ] Enabled/Disabled switch
  - [ ] Help text explaining impact
  - [ ] Warning if disabling (confirmation)
- [ ] **Staff Portal Toggle**
  - [ ] Enabled/Disabled switch
  - [ ] Help text
  - [ ] Warning if disabling

**Guest Access Settings:**
- [ ] **Requires Room PIN**
  - [ ] Toggle switch
  - [ ] Help text: "Guest must enter PIN to access portal"
- [ ] **Room PIN Length**
  - [ ] Number input (dropdown: 4, 6, 8)
  - [ ] Default: 4
  - [ ] Help text: "Length of generated guest PINs"
- [ ] **Rotate PIN on Checkout**
  - [ ] Toggle switch
  - [ ] Help text: "Generate new PIN after guest checks out"

**Session Management:**
- [ ] **Allow Multiple Guest Sessions**
  - [ ] Toggle switch
  - [ ] Help text: "Allow multiple people in same room to access portal"
- [ ] **Max Active Devices Per Room**
  - [ ] Number input (1-10)
  - [ ] Default: 5
  - [ ] Help text: "Maximum devices that can be logged in per room"
  - [ ] Only enabled if multiple sessions allowed

**Security Recommendations Panel:**
- [ ] Info box with recommended settings
- [ ] Warning for insecure configurations
- [ ] Best practices tips

**Form Management:**
- [ ] Load current config on mount
- [ ] Real-time validation
- [ ] Save button (disabled when no changes)
- [ ] Reset button
- [ ] Success notification
- [ ] Impact warnings for certain changes

**Confirmation Dialogs:**
- [ ] Disabling guest portal → confirm
- [ ] Disabling staff portal → confirm
- [ ] Changing PIN requirements → confirm

#### Component Structure
```
AccessConfigTab/
├── PortalSettingsSection.jsx
├── GuestAccessSection.jsx
├── SessionManagementSection.jsx
└── SecurityRecommendations.jsx
```

#### Acceptance Criteria
✅ All access config fields are editable  
✅ Toggles work correctly  
✅ Number inputs validate ranges  
✅ Dependent fields enable/disable correctly  
✅ Save updates configuration  
✅ Warnings shown for risky changes  
✅ Changes take effect immediately  
✅ Help text explains each setting clearly  

#### Testing
- [ ] Load current configuration
- [ ] Toggle each switch
- [ ] Change PIN length
- [ ] Change max devices
- [ ] Test dependent field logic
- [ ] Save with valid data
- [ ] Test confirmation dialogs
- [ ] Verify security warnings display

---

### 📋 Issue F9: Staff Bookings Management UI

**Type:** Feature  
**Priority:** HIGH  
**Dependencies:** Issue 4 (Auth/Me endpoint)  
**Estimated Time:** 12-16 hours

#### Description
Create a staff-only bookings management interface where hotel staff can view, filter, and confirm guest room bookings for their hotel.

#### Backend API
**Endpoints:**
- `GET /api/staff/hotels/<hotel_slug>/hotel/bookings/` - List bookings
  - Query params: `?status=PENDING_PAYMENT&start_date=2025-12-01&end_date=2025-12-31`
- `POST /api/staff/hotels/<hotel_slug>/hotel/bookings/<booking_id>/confirm/` - Confirm booking

**Booking Structure:**
```json
{
  "id": 1,
  "booking_id": "BK-2025-0001",
  "confirmation_number": "HOT-2025-0123",
  "hotel_name": "Hotel Killarney",
  "room_type_name": "Deluxe Suite",
  "guest_name": "John Doe",
  "guest_email": "john@example.com",
  "guest_phone": "+353 1 234 5678",
  "check_in": "2025-12-20",
  "check_out": "2025-12-22",
  "nights": 2,
  "adults": 2,
  "children": 0,
  "total_amount": "398.00",
  "currency": "EUR",
  "status": "PENDING_PAYMENT",
  "created_at": "2025-11-24T10:00:00Z",
  "paid_at": null
}
```

**Valid Status Values:**
- PENDING_PAYMENT
- CONFIRMED
- CANCELLED
- COMPLETED
- NO_SHOW

#### Tasks

**Page Structure:**
- [ ] Create `StaffBookingsPage.jsx` main component
- [ ] Implement responsive layout (table on desktop, cards on mobile)
- [ ] Permission check (staff only, correct hotel)

**Filters & Search:**
- [ ] **Status Filter**
  - [ ] Dropdown with status options
  - [ ] "All Statuses" option
  - [ ] Count badges per status
  - [ ] Default: show all
- [ ] **Date Range Filter**
  - [ ] Start Date picker
  - [ ] End Date picker
  - [ ] Quick filters: Today, This Week, This Month, Custom
  - [ ] Clear dates button
- [ ] **Search Bar**
  - [ ] Search by guest name, email, booking ID, confirmation number
  - [ ] Debounced search
  - [ ] Clear button
- [ ] **Active Filters Display**
  - [ ] Show applied filters as chips/tags
  - [ ] Remove individual filters
  - [ ] Clear all filters button

**Bookings List (Table View - Desktop):**
- [ ] **Columns:**
  - Booking ID
  - Confirmation Number
  - Guest Name
  - Room Type
  - Check-in Date
  - Check-out Date
  - Nights
  - Total Amount
  - Status (with badge)
  - Actions
- [ ] **Sortable Columns**
  - Sort by date, amount, status
  - Ascending/descending toggle
- [ ] **Status Badges**
  - Color-coded by status
  - PENDING_PAYMENT: yellow/warning
  - CONFIRMED: green/success
  - CANCELLED: red/danger
  - COMPLETED: blue/info
  - NO_SHOW: gray/muted
- [ ] **Pagination**
  - Page size selector (10, 25, 50, 100)
  - Page navigation
  - Total count display

**Bookings List (Card View - Mobile):**
- [ ] Responsive card layout
- [ ] Show key info: guest, dates, status, amount
- [ ] Tap card to view details

**Booking Detail Modal:**
- [ ] Open on row click
- [ ] **Guest Information Section**
  - Full name
  - Email (with mailto link)
  - Phone (with tel link)
  - Special requests
- [ ] **Booking Details Section**
  - Booking ID
  - Confirmation number
  - Created date
  - Paid date (if applicable)
- [ ] **Room Details Section**
  - Room type
  - Check-in/out dates
  - Number of nights
  - Adults/children count
- [ ] **Pricing Section**
  - Total amount
  - Currency
  - Promo code (if used)
- [ ] **Status Section**
  - Current status with badge
  - Status history (if tracked)
- [ ] **Actions**
  - Confirm button (if status = PENDING_PAYMENT)
  - Cancel button (future enhancement)
  - Print/Export button
  - Close button

**Confirm Booking Action:**
- [ ] Only visible for PENDING_PAYMENT status
- [ ] Confirmation dialog
  - Show booking details summary
  - "Are you sure?" message
  - Confirm/Cancel buttons
- [ ] API call to confirm endpoint
- [ ] Loading state during confirm
- [ ] Success notification
  - "Booking confirmed successfully"
  - "Confirmation email sent to guest"
- [ ] Error handling
  - Display error message
  - Suggest retry
- [ ] Update booking status in list without full reload
- [ ] Send booking to confirmed section

**Real-time Updates (Optional Enhancement):**
- [ ] Polling for new bookings
- [ ] Notification badge for new bookings
- [ ] Auto-refresh list

**Export/Print:**
- [ ] Export filtered bookings to CSV
- [ ] Print booking details
- [ ] Print booking list

**Empty States:**
- [ ] No bookings found
- [ ] No results for current filters
- [ ] Helpful messages and CTAs

#### Component Structure
```
StaffBookingsPage/
├── BookingsFilters.jsx
├── BookingsList/
│   ├── BookingsTable.jsx (desktop)
│   ├── BookingsCards.jsx (mobile)
│   ├── BookingRow.jsx
│   └── BookingCard.jsx
├── BookingDetailModal.jsx
├── BookingDetailSections/
│   ├── GuestInfoSection.jsx
│   ├── BookingInfoSection.jsx
│   ├── RoomInfoSection.jsx
│   ├── PricingSection.jsx
│   └── StatusSection.jsx
├── ConfirmBookingDialog.jsx
└── components/
    ├── StatusBadge.jsx
    ├── FilterChips.jsx
    └── EmptyState.jsx
```

#### Acceptance Criteria
✅ Only authenticated staff from correct hotel can access  
✅ All bookings for hotel display correctly  
✅ Status filter works (validates against valid statuses)  
✅ Date range filter works  
✅ Search works across guest name, email, booking ID  
✅ Can view full booking details in modal  
✅ Can confirm bookings in PENDING_PAYMENT status  
✅ Confirm action updates status immediately  
✅ Confirmation dialog prevents accidental confirms  
✅ Success/error notifications display correctly  
✅ Status badges color-coded correctly  
✅ Responsive layout works on mobile  
✅ Pagination works correctly  
✅ Empty states display when appropriate  

#### Testing
- [ ] Load bookings list
- [ ] Filter by each status
- [ ] Filter by date range
- [ ] Search by guest name
- [ ] Search by booking ID
- [ ] Sort by different columns
- [ ] View booking details
- [ ] Confirm pending booking
- [ ] Test with invalid status (verify error handling)
- [ ] Test permission blocking (wrong hotel staff)
- [ ] Test responsive layout on mobile
- [ ] Test with empty results
- [ ] Verify status badge colors

---

## Implementation Checklist

### Backend (Remaining Tasks)

- [ ] **Issue 4:** Enhance Auth/Me endpoint with staff info
  - [ ] Add `is_staff_member` flag
  - [ ] Include `hotel_slug` if staff
  - [ ] Include `access_level` and `role_slug`
  - [ ] Add `can_edit_public_page` derived field

- [ ] **Issue 6:** Register models in Django Admin
  - [ ] `HotelPublicSettings`
  - [ ] `Offer`
  - [ ] `LeisureActivity`
  - [ ] Configure list displays and filters

- [ ] **Issue 9:** Implement email confirmation
  - [ ] Create `hotel/email_utils.py`
  - [ ] Write `send_booking_confirmation_email(booking)` function
  - [ ] Integrate with `StaffBookingConfirmView`
  - [ ] Configure email templates
  - [ ] Test email delivery

- [ ] **Issues 5 & 10:** Write comprehensive tests
  - [ ] Public settings endpoint tests
  - [ ] Staff settings endpoint tests (permissions)
  - [ ] Booking list tests (filters, permissions)
  - [ ] Booking confirm tests
  - [ ] Email sending tests

### Frontend (All Issues Pending)

- [ ] **F1:** Public Hotel Page Rendering
- [ ] **F2:** Settings - Public Content & Branding
- [ ] **F3:** Settings - Booking & CTA Options
- [ ] **F4:** Settings - Rooms & Suites
- [ ] **F5:** Settings - Offers & Packages
- [ ] **F6:** Settings - Leisure & Facilities
- [ ] **F7:** Settings - Room Inventory
- [ ] **F8:** Settings - Access Configuration
- [ ] **F9:** Staff Bookings Management

### Documentation

- [x] Backend implementation complete documentation
- [x] API endpoint documentation
- [x] Frontend issues detailed specification
- [ ] Frontend component architecture
- [ ] Testing strategy document
- [ ] Deployment guide

---

## API Reference Quick Links

### Public Endpoints
- `GET /api/public/hotels/<slug>/page/` - Complete hotel page data
- `GET /api/public/hotels/<slug>/settings/` - Public settings only

### Staff Settings Endpoints
- `GET/PUT/PATCH /api/staff/hotels/<slug>/hotel/settings/` - Public settings management
- `GET/POST/PUT/DELETE /api/staff/hotels/<slug>/hotel/staff/offers/` - Offers CRUD
- `GET/POST/PUT/DELETE /api/staff/hotels/<slug>/hotel/staff/leisure-activities/` - Activities CRUD
- `GET/POST/PUT/DELETE /api/staff/hotels/<slug>/hotel/staff/room-types/` - Room types CRUD
- `GET/POST/PUT/DELETE /api/staff/hotels/<slug>/hotel/staff/rooms/` - Rooms CRUD
- `POST /api/staff/hotels/<slug>/hotel/staff/rooms/{id}/generate_pin/` - Generate PIN
- `POST /api/staff/hotels/<slug>/hotel/staff/rooms/{id}/generate_qr/` - Generate QR
- `GET/PUT/PATCH /api/staff/hotels/<slug>/hotel/staff/access-config/` - Access config

### Staff Booking Endpoints
- `GET /api/staff/hotels/<slug>/hotel/bookings/` - List bookings
- `POST /api/staff/hotels/<slug>/hotel/bookings/<booking_id>/confirm/` - Confirm booking

### Public Booking Endpoints
- `GET /api/<slug>/availability/` - Check availability
- `POST /api/<slug>/pricing/quote/` - Get pricing quote
- `POST /api/<slug>/bookings/` - Create booking

---

## Development Workflow

### For Backend Developers
1. Complete remaining backend tasks (Auth/Me, Admin, Email, Tests)
2. Review API responses match documentation
3. Test all permission scenarios
4. Document any API changes

### For Frontend Developers
1. Start with **F1** (Public Hotel Page) - no auth required
2. Then **F2** (Settings base) - establishes settings infrastructure
3. Then **F3-F8** in any order - all use same settings pattern
4. Then **F9** (Bookings) - separate from settings
5. Test each issue thoroughly before moving to next
6. Follow component structure guidelines
7. Use provided API examples

### Testing Strategy
- Unit tests for components
- Integration tests for API calls
- E2E tests for critical flows (booking, settings save)
- Permission tests for all staff routes
- Responsive design tests

---

## Success Metrics

### Backend
✅ All 8 backend issues (B1-B8) complete  
⚠️ 4 additional backend tasks needed (Auth, Admin, Email, Tests)  
✅ All APIs documented with examples  
✅ No breaking changes to existing endpoints  

### Frontend (Pending)
📋 0/9 frontend issues complete  
📋 Component architecture defined  
📋 Design system/styling approach needed  
📋 Testing framework setup needed  

### Overall Project
- ⚠️ Backend: 90% complete (core done, polish needed)
- 📋 Frontend: 0% complete (ready to start)
- 📋 Testing: 0% coverage (needed before production)
- ✅ Documentation: Comprehensive
- 🎯 Production Ready: Estimated 4-6 weeks for frontend + testing

---

**Status:** Backend is production-ready with minor polish needed. Frontend can begin immediately using documented APIs.

**Next Step:** Begin frontend implementation with Issue F1 (Public Hotel Page).
