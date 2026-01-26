# Overstay System - Frontend User Instructions

## Overview
The overstay detection system automatically monitors bookings and alerts staff when guests exceed their checkout time past noon. Staff can manage overstays through the booking management interface.

## How Overstay Detection Works

### Automatic Detection
- ✅ **System checks every 10 minutes** for new overstay incidents
- ✅ **Noon Rule**: Overstays are detected at 12:00 PM hotel time on checkout day
- ✅ **Real-time Updates**: Staff dashboard updates automatically via Pusher events
- ✅ **Status Tracking**: Shows overstay duration (e.g., "Checkout CRITICAL +1506m" = 25 hours overdue)

### Booking Status Flow
1. **CONFIRMED** → Guest has paid and confirmed booking
2. **IN_HOUSE** → Guest has checked in (assigned room) ✅ **FIXED**
3. **OVERSTAY** → Guest has exceeded noon checkout time
4. **COMPLETED** → Guest has checked out properly

## Staff Interface Usage

### 1. Viewing Overstay Bookings

#### Dashboard Overview
- Navigate to **Room Bookings** section
- Look for bookings with **red "CRITICAL"** indicators
- Overstay duration shows as **"+XXXXm"** (minutes overdue)

#### Booking Details
- Click on overstay booking to view details
- **Overstay Status** section shows:
  - Current overstay duration
  - When overstay was first detected
  - Any acknowledgments or extensions

### 2. Managing Overstays

#### Acknowledge Overstay
```
Purpose: Mark that staff is aware of the overstay
Action: Click "Acknowledge Overstay" button
Result: Overstay is marked as staff-acknowledged but still active
```

#### Extend Overstay (Approved Late Checkout)
```
Purpose: Grant official extension when guest requests late checkout
Steps:
1. Click "Extend Overstay" button
2. Select extension duration:
   - 1 hour
   - 2 hours  
   - 4 hours
   - 8 hours
   - Custom duration
3. Add optional notes for reasoning
4. Click "Extend Overstay"

Result: 
- Overstay timer resets with new deadline
- Guest gets additional time before next overstay detection
- Extension is logged with timestamp and staff member
```

#### Complete Checkout
```
Purpose: Mark guest as properly checked out
Action: Use normal checkout process in booking management
Result: Booking status changes to COMPLETED, overstay ends
```

### 3. Overstay Notifications

#### Real-time Alerts
- **New overstays** appear automatically on dashboard
- **Status changes** update in real-time (no page refresh needed)
- **Critical indicators** show visually with red styling

#### Overstay Information Display
- **Duration**: How long past noon checkout (e.g., "+1506m" = 25+ hours)
- **Status**: OVERSTAY with severity indicator
- **Room**: Which room is occupied past checkout
- **Guest**: Primary guest information

## Common Workflows

### Scenario 1: Guest Requests Late Checkout
```
1. Guest calls/asks for late checkout at 11:30 AM
2. Staff checks availability and approves 2-hour extension
3. Before noon overstay detection:
   - Find guest's booking in system
   - Click "Extend Overstay" (proactive)
   - Select "2 hours" extension
   - Add note: "Guest requested late checkout - approved"
4. Guest can checkout until 2:00 PM without triggering overstay
```

### Scenario 2: Unplanned Overstay Detected
```
1. System detects overstay at 12:00 PM (automatic)
2. Staff sees red CRITICAL indicator on dashboard
3. Staff contacts guest to check status:
   
   Option A - Guest forgot and will checkout immediately:
   - Click "Acknowledge Overstay" to mark as handled
   - Guide guest through checkout process
   
   Option B - Guest needs more time:
   - Click "Extend Overstay" 
   - Select appropriate duration based on guest need
   - Add note explaining situation
   
   Option C - Guest already left but forgot to checkout:
   - Process manual checkout for guest
   - Booking status changes to COMPLETED
```

### Scenario 3: Multiple Day Overstays
```
1. If guest extends stay beyond original dates:
2. Use booking modification to extend booking dates
3. Do NOT use overstay extension for multi-day extensions
4. Overstay extensions are for same-day late checkouts only
```

## Important Notes

### ✅ System Reliability
- Overstay detection runs **every 10 minutes automatically**
- All status changes sync in **real-time** to staff dashboards
- Extensions are **logged with timestamps** for audit trail
- **Booking expiry** system handles unpaid/unapproved bookings separately

### ⚠️ Staff Guidelines
- **Acknowledge overstays promptly** when you become aware
- **Use extensions judiciously** - they reset the overstay timer
- **Document reasoning** in extension notes for accountability
- **Complete checkouts** as soon as guest leaves to free up rooms

### 🔧 Technical Details
- System uses **Europe/Dublin timezone** for noon calculations
- Overstay duration updates **every 10 minutes** with fresh calculations
- **409 Conflict errors** have been resolved ✅
- **Booking status transitions** work correctly ✅

## Troubleshooting

### If Overstay Not Showing
- Verify booking status is **IN_HOUSE** (not CONFIRMED)
- Check that checkout date is today and time is past noon
- Refresh browser if real-time updates seem stuck

### If Extension Fails
- Try again - system now handles concurrent updates properly ✅
- Check that booking is in correct status (IN_HOUSE + OVERSTAY)
- Contact tech support if "409 Conflict" errors persist

### If Status Seems Wrong
- Booking must be **IN_HOUSE** status to trigger overstay detection
- Check that room assignment was completed during check-in ✅
- System automatically updates booking status during room assignment ✅

## Contact & Support

For technical issues or questions about the overstay system:
- All scheduled background jobs are running correctly ✅
- Real-time notifications are functioning ✅  
- Status transitions have been fixed ✅
- Overstay extensions work properly ✅

The overstay management system is fully operational and monitoring all bookings automatically.