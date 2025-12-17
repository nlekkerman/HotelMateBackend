# Booking Serializer Refactor Plan: Party as Single Source of Truth

**Objective**: Eliminate guest data duplication and establish `RoomBooking.party` as the canonical source for all guest information across HotelMate booking serializers.

## 🎯 Canonical Party Shape Contract

**CONFIRMED**: Use `BookingPartyGroupedSerializer` everywhere for consistent structure:

```python
party: {
    'primary': primary_guest_data,  // or null
    'companions': [companion_data...],
    'total_count': len(party_list)   // NOT total_party_size
}
```

**Rule**: Anything that looks like "primary guest" outside `party.primary` is deprecated output and must be removed (except booker/billing object).

## 📋 Implementation Checklist

### A) RoomBookingDetailSerializer (`booking_serializers.py`)

**Current Issues**:
- Lines 180-190: Exposes `primary_first_name`, `primary_last_name`, `primary_email`, `primary_phone`
- Lines 185-186: Exposes `adults`, `children`  
- Lines 340-353: Custom `get_party()` returns `total_party_size` (wrong key)
- Lines 280-295: `get_booking_summary()` uses `obj.adults + obj.children`

**Changes Required**:
- [ ] Remove from fields list: `primary_first_name`, `primary_last_name`, `primary_email`, `primary_phone`
- [ ] Remove from fields list: `adults`, `children`
- [ ] Replace `get_party()` method with: 
  ```python
  def get_party(self, obj):
      from .canonical_serializers import BookingPartyGroupedSerializer
      return BookingPartyGroupedSerializer().to_representation(obj)
  ```
- [ ] Update `get_booking_summary()` guest_count to use party data instead of `obj.adults + obj.children`
- [ ] Add import: `from .canonical_serializers import BookingPartyGroupedSerializer`

### B) StaffRoomBookingDetailSerializer (`canonical_serializers.py`)

**Current Issues**:
- Lines 235-240: Has `primary_guest` field + `get_primary_guest()` method
- Lines 260-265: Exposes `adults`, `children` in fields list
- Lines 290-300: `get_primary_guest()` duplicates party.primary data
- Lines 310-315: `get_in_house()` always returns data even when not checked in

**Changes Required**:
- [ ] Remove `primary_guest` from fields list (line ~240)
- [ ] Remove `get_primary_guest()` method completely (lines 290-300)
- [ ] Remove `adults`, `children` from fields list (lines 260-265)
- [ ] Update `get_in_house()` to return `None` when `checked_in_at is None`:
  ```python
  def get_in_house(self, obj):
      if not obj.checked_in_at:
          return None
      serializer = InHouseGuestsGroupedSerializer()
      return serializer.to_representation(obj)
  ```
- [ ] Verify `get_party()` uses canonical `BookingPartyGroupedSerializer` (already correct)

### C) RoomBookingListSerializer (`booking_serializers.py`)

**Current Issues**:
- Line 100: Has `guest_name` method field
- Lines 115-130: Exposes `adults`, `children` in fields list
- Line 135: `get_guest_name()` uses `obj.primary_guest_name`

**Changes Required**:
- [ ] Remove `guest_name` from fields list and method
- [ ] Remove `get_guest_name()` method completely
- [ ] Remove `adults`, `children` from fields list
- [ ] If display name needed, derive internally from `obj.primary_guest_name` but don't expose as separate field

### D) StaffRoomBookingListSerializer (`canonical_serializers.py`)

**Current Issues**:
- Lines 165-170: Has `primary_guest_name` method field
- Lines 185-190: Exposes `adults`, `children` in fields list
- Line 200: `get_primary_guest_name()` method

**Changes Required**:
- [ ] Remove `primary_guest_name` from fields list
- [ ] Remove `get_primary_guest_name()` method
- [ ] Remove `adults`, `children` from fields list
- [ ] Keep only: `party_total_count`, `party_complete`, `party_missing_count`

### E) ValidatePrecheckinTokenView (`public_views.py`)

**Current Issues**:
- Lines 330-350: Response uses `total_party_size` instead of `total_count`
- Lines 335-340: Booking object exposes `adults`, `children`, `total_guests`
- Line 338: `total_guests` calculated as `booking.adults + booking.children`

**Changes Required**:
- [ ] Change `total_party_size` to `total_count` in party response (line ~345)
- [ ] Remove `adults`, `children` from booking response object
- [ ] Remove or replace `total_guests` calculation to use party data
- [ ] Update party construction to use canonical format:
  ```python
  'party': {
      'primary': next((BookingGuestSerializer(member).data for member in party_list if member.role == 'PRIMARY'), None),
      'companions': [BookingGuestSerializer(member).data for member in party_list if member.role == 'COMPANION'],
      'total_count': len(party_list)  // Changed from total_party_size
  }
  ```

## 🚨 Critical Dependencies to Preserve

### Booker vs Primary Distinction
- **Keep**: Separate `booker` object (billing/contact info) 
- **Remove**: `primary_guest` object (staying guest info - use `party.primary`)

### Business Logic
- **Preserve**: `party_complete`, `party_missing_count` calculations
- **Preserve**: Room assignment validation requiring party completion
- **Preserve**: Precheckin field registry and validation logic

### API Contracts
- **Maintain**: All endpoint response structures (just remove duplicate fields)
- **Maintain**: Authentication and permission requirements
- **Maintain**: Error response formats

## 🔍 Current Duplication Issues Identified

1. **Primary Guest Data**: 
   - `RoomBooking.primary_*` fields → duplicated in serializer output
   - `StaffRoomBookingDetailSerializer.primary_guest` → duplicates `party.primary`

2. **Guest Count Data**:
   - `adults`/`children` exposed in multiple serializers
   - `total_guests` vs `total_party_size` vs `total_count` inconsistency
   - Booking summary guest count computed from wrong source

3. **Display Name Methods**:
   - `guest_name`, `primary_guest_name` methods compute similar values
   - Should derive from `party.primary.full_name` if needed

## 🧪 Validation Requirements

After implementation, verify:
- [ ] `primary_guest` key is absent from all staff responses
- [ ] `adults`/`children` keys are absent from detail responses  
- [ ] `party.total_count` exists and matches expected count
- [ ] `in_house` is null/absent when `checked_in_at` is null
- [ ] Precheckin flow works with new party-centric structure
- [ ] Room assignment enforcement still validates party completion
- [ ] Notification system still works with updated serializers

## 📁 Files to Modify

1. **`hotel/booking_serializers.py`**
   - `RoomBookingDetailSerializer`
   - `RoomBookingListSerializer`

2. **`hotel/canonical_serializers.py`**
   - `StaffRoomBookingDetailSerializer` 
   - `StaffRoomBookingListSerializer`

3. **`hotel/public_views.py`**
   - `ValidatePrecheckinTokenView.get()`

## ⚡ Migration Strategy

**Approach**: Implement all changes simultaneously in one PR to avoid mixed payload states that could break frontend logic.

**Testing Priority**:
1. Staff booking list/detail views
2. Public precheckin flow
3. Room assignment workflows  
4. Notification system integration

## 🎯 Success Criteria

- ✅ Single source of truth: `party` object contains all guest data
- ✅ No duplicate guest representations outside `party.primary`
- ✅ Consistent `total_count` field naming across all endpoints
- ✅ Preserved business logic for party validation and room assignment
- ✅ Maintained API backward compatibility (structure unchanged, just fields removed)

---

**Status**: Ready for implementation
**Created**: December 17, 2025
**Source of Truth**: This document defines the complete refactor scope