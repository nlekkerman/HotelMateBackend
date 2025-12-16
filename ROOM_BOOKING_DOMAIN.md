# RoomBooking Domain Definition

**Status**: Source of Truth  
**Last Updated**: December 16, 2025  
**Version**: 1.0

## Domain Scope

### What RoomBooking IS
- Guest room reservations/bookings for hotels
- Property stay bookings (overnight accommodation)
- Room assignment and check-in/check-out processes
- Guest party management (primary + companions)
- Booking lifecycle from payment to completion

### What RoomBooking is NOT
- Restaurant table bookings
- Spa service bookings  
- Event/conference bookings
- Activity/tour bookings
- Any non-accommodation booking type

**CRITICAL**: RoomBooking is a completely separate domain. Do not mix with other booking types.

## Booking Lifecycle States

```
PENDING_PAYMENT → CONFIRMED → CHECKED_IN → COMPLETED
                      ↓
                  CANCELLED / NO_SHOW
```

### State Definitions
- **PENDING_PAYMENT**: Booking created, awaiting payment
- **CONFIRMED**: Payment received, booking confirmed
- **CANCELLED**: Booking cancelled (any time before check-in)
- **NO_SHOW**: Guest failed to arrive on check-in date
- **COMPLETED**: Guest has checked out, booking finished

### State Transitions
- Only `PENDING_PAYMENT` can transition to `CONFIRMED`
- Only `CONFIRMED` can transition to `CHECKED_IN` 
- Only `CHECKED_IN` can transition to `COMPLETED`
- `CANCELLED` and `NO_SHOW` are terminal states
- Cancellation possible from `PENDING_PAYMENT` or `CONFIRMED`

## Booker vs Primary Staying Guest

### Booker (Payer)
- Person/entity making the payment
- May or may not be staying at the hotel
- Fields: `booker_first_name`, `booker_last_name`, `booker_email`, `booker_phone`, `booker_company`

### Primary Staying Guest (Required)
- Person who will stay in the room (room key holder)
- Always staying at the hotel
- Fields: `primary_first_name`, `primary_last_name`, `primary_email`, `primary_phone`

### Booker Types
- **SELF**: Booker is staying (booker = primary guest)
- **THIRD_PARTY**: Third-party booking (gift, agent)
- **COMPANY**: Corporate booking

**Rule**: Primary guest fields are always required. Booker fields only required when booker ≠ primary guest.

## Party Model

### Party Structure
```
BookingGuest (party member)
├── PRIMARY (exactly 1) - Main guest, matches booking primary_* fields
└── COMPANION (0+) - Additional staying guests
```

### Party Rules
- Every booking MUST have exactly 1 PRIMARY guest
- PRIMARY guest data syncs with booking `primary_*` fields
- Companions are optional additional staying guests
- All party members have `is_staying: true`
- Party size should align with `adults` + `children` count

## Room Assignment Rules

### Pre-Assignment (Booking Creation)
- `room_type`: Selected room category (required)
- `assigned_room`: null (no specific room assigned yet)

### Room Assignment (Check-in Process)
- `assigned_room`: Specific room assigned (Room instance)
- Assignment happens during check-in workflow
- Staff assigns available room of the booked room_type

### Assignment States
- **Unassigned**: `assigned_room = null` (normal for new bookings)
- **Assigned**: `assigned_room = Room instance` (ready for check-in)
- **Checked In**: `assigned_room` set + `checked_in_at` timestamp
- **Checked Out**: `checked_out_at` timestamp set

## Frontend Mutability Rules

### Immutable Fields (Never Change After Creation)
- `booking_id` - System generated, permanent
- `confirmation_number` - Guest-facing ID, permanent  
- `hotel` - Cannot change hotel
- `room_type` - Cannot change room category after booking
- `check_in` / `check_out` - Dates locked after payment
- `created_at` - Audit timestamp

### Mutable Fields (Staff Can Modify)
- `status` - Lifecycle progression
- `assigned_room` - Room assignment
- `checked_in_at` / `checked_out_at` - Check-in/out timestamps
- `internal_notes` - Staff annotations
- Party members (add/remove companions)
- Contact information (email, phone)

### Guest-Controlled Fields (Public API Only)
- `special_requests` - Guest notes
- Payment information (via payment flow)
- Primary guest contact info (limited updates)

## Data Consistency Rules

### Automatic Synchronization
- PRIMARY party member always syncs with booking `primary_*` fields
- Party changes trigger booking updates
- Room assignment updates occupancy status

### Validation Rules  
- Check-out date must be after check-in date
- Cannot check-in without room assignment
- Cannot modify booking after check-out (status = COMPLETED)
- Primary guest name must match PRIMARY party member

### Referential Integrity
- `hotel` → Hotel (PROTECT)
- `room_type` → RoomType (PROTECT) 
- `assigned_room` → Room (SET_NULL)
- Party members cascade delete with booking

## Domain Boundaries

### Public Domain (No Auth)
- Booking creation and payment
- Public booking details (limited fields)
- Availability checking
- Quote generation

### Staff Domain (Authenticated)  
- Full booking management
- Room assignment
- Check-in/check-out processing
- Party management
- Internal notes and operations

### Guest Portal Domain
- View own booking details
- Limited contact updates
- Check-in/check-out status

**RULE**: Each domain has specific field visibility and modification rights. Never expose internal fields to public APIs.