# Registration Code Admin - Hierarchical Navigation Guide

## Overview
The Registration Code admin panel now features a hierarchical, hotel-organized navigation system for easy management of registration codes across multiple hotels.

## Navigation Flow

### Level 1: Hotels Overview
When you click "Registration codes" in the Django admin sidebar:

```
/admin/staff/registrationcode/
```

**You will see:**
- List of all hotels with registration code statistics
- Each hotel card shows:
  - Hotel name and slug
  - Total codes
  - Used codes
  - Available codes
  - Percentage used
- Color-coded status indicators:
  - Green: Codes available
  - Orange: Low availability (>80% used)
  - Red: No codes available

**Actions:**
- Click any hotel card to view its registration codes

---

### Level 2: Hotel's Registration Codes
When you click a hotel card:

```
/admin/staff/registrationcode/?hotel={hotel_slug}
```

**You will see:**
- Table of all registration codes for that specific hotel
- Columns displayed:
  - Code
  - Status (Available/Used)
  - QR Status (✓ QR Ready / ⚠ Token only / ✗ No QR)
  - Created date
  - Used by
  - Actions
- Back to Hotels button to return to overview

**Actions:**
- Click "View Details" on any code to see full information
- Use the back button to return to hotels overview
- Filter and search codes using standard Django filters

---

### Level 3: Code Details
When you click "View Details" on a code:

```
/admin/staff/registrationcode/{code_id}/change/
```

**You will see:**
Complete details organized in sections:

#### Registration Code Information
- Code
- Hotel slug
- Created date

#### QR Code Information
- QR Token (secure token for validation)
- QR Code URL (Cloudinary link)
- QR Code Preview (visual preview of QR code)
- Registration URL (full URL with token)

#### Usage Information
- Used by (staff member who used this code)
- Used at (timestamp of usage)

**Actions:**
- Edit code details
- Delete code (if not used)
- Return to code list using breadcrumbs

---

## Features

### Visual Indicators

**Status Colors:**
- 🟢 Green: Code available
- 🔴 Red: Code used

**QR Status:**
- ✓ Green: QR code generated and ready
- ⚠ Orange: Token generated but QR image missing
- ✗ Red: No QR code or token

### Statistics Dashboard
Each hotel card shows:
- Progress bar indicating usage percentage
- Exact counts (e.g., "5 used / 20 total")
- Quick visual assessment of code availability

### Clean Interface
- No background colors cluttering the view
- Minimal, professional styling
- Clear typography and spacing
- Responsive design

---

## Common Tasks

### View All Codes for a Hotel
1. Go to Registration codes admin
2. Click the hotel card
3. Browse or filter codes

### Check Code Details
1. Navigate to hotel's codes
2. Click "View Details" on the code
3. View all information including QR preview

### Find Available Codes
1. Check hotels overview
2. Look for hotels with green status
3. Click hotel to see available codes
4. Filter by "is_used = False" if needed

### Generate QR Codes
1. Navigate to specific code details
2. If QR is missing, use the API or admin action
3. Refresh to see updated QR status

---

## Tips

**Quick Navigation:**
- Use browser back button to navigate levels
- Bookmark specific hotel views for quick access
- Use Django admin breadcrumbs for navigation

**Filtering:**
- At hotel level, use standard Django filters
- Filter by status, date, or usage
- Search by code or staff member name

**Bulk Operations:**
- Select multiple codes at hotel level
- Use admin actions for bulk operations
- Export filtered results if needed

---

## Technical Notes

### URL Structure
```
Level 1: /admin/staff/registrationcode/
Level 2: /admin/staff/registrationcode/?hotel={slug}
Level 3: /admin/staff/registrationcode/{id}/change/
```

### Template
Custom template: `staff/templates/admin/staff/registrationcode_changelist.html`

### Context Data
- `hotel_stats`: Aggregated statistics per hotel
- `codes_for_hotel`: Filtered codes for selected hotel
- `selected_hotel`: Currently selected hotel slug

---

## Troubleshooting

**Can't see hotels?**
- Ensure registration codes exist
- Check if codes have hotel_slug set
- Verify you have view permissions

**QR codes not showing?**
- QR images stored in Cloudinary
- Check if qr_code_url field is populated
- Verify Cloudinary credentials

**Statistics wrong?**
- Stats calculated in real-time
- Refresh page for latest data
- Check database for orphaned codes

---

## Related Documentation
- [QR Registration Implementation](QR_IMPLEMENTATION_SUMMARY.md)
- [Admin Registration Codes Guide](ADMIN_REGISTRATION_CODES_GUIDE.md)
- [Frontend QR Guide](FRONTEND_QR_REGISTRATION_GUIDE.md)
