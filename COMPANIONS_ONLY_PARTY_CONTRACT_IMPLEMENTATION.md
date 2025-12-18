# Unified Companions-Only Party Contract Implementation

## 🎯 Implementation Summary

Successfully implemented the unified companions-only party contract across both booking creation and precheckin submission endpoints. **PRIMARY guests are never sent in party payloads** - they are always inferred from `RoomBooking.primary_*` fields.

---

## ✅ New Canonical Party Contract

### Input Rule (Both Endpoints)
```json
{
  "party": [
    {
      "first_name": "Jane",
      "last_name": "Smith", 
      "email": "jane@example.com",
      "phone": "+353871234568"
    }
  ]
}
```

- **`role` field**: Not required, ignored if provided
- **PRIMARY rejection**: Returns 400 if any party item has `role: "PRIMARY"`
- **Companion validation**: `first_name` and `last_name` required, `email`/`phone` optional
- **Empty party allowed**: PRIMARY-only bookings work with `party: []`

---

## 📝 Implementation Details

### Part A: Booking Create ([hotel/booking_views.py](hotel/booking_views.py))

**Changes Made:**
- ✅ **PRIMARY rejection**: Return 400 with message "Do not include PRIMARY in party; primary guest is inferred from primary_* fields."
- ✅ **Companions-only processing**: All party payload items forced to `role="COMPANION"`
- ✅ **Validation**: Require `first_name`/`last_name`, optional `email`/`phone`
- ✅ **Party count fix**: `party_count = 1 + len(party_data)` (1 PRIMARY + companions)

**Before:**
```python
# Required exactly 1 PRIMARY in party
if primary_count != 1:
    return Response({"detail": "Party must include exactly one PRIMARY guest"})
```

**After:**
```python
# Reject any PRIMARY in party  
if primary_count > 0:
    return Response({"detail": "Do not include PRIMARY in party; primary guest is inferred from primary_* fields."})
```

### Part B: Precheckin Submit ([hotel/public_views.py](hotel/public_views.py))

**Changes Made:**
- ✅ **PRIMARY rejection**: Same error message as booking create
- ✅ **PRIMARY preservation**: Only delete `COMPANION` BookingGuests, preserve `PRIMARY`
- ✅ **Size validation**: `1 + len(party_data)` must match `adults + children`
- ✅ **Idempotency**: Multiple submissions replace companions cleanly

**Before:**
```python
# Deleted ALL party members including PRIMARY
BookingGuest.objects.filter(booking=booking).delete()

# Required exactly 1 PRIMARY in payload
if primary_count != 1:
    return Response({"message": "Exactly one PRIMARY guest is required"})
```

**After:**
```python
# Only delete COMPANION BookingGuests - preserve PRIMARY
BookingGuest.objects.filter(booking=booking, role='COMPANION').delete()

# Reject PRIMARY in payload
if primary_count > 0:
    return Response({"message": "Do not include PRIMARY in party; primary guest is inferred from primary_* fields."})
```

---

## 🧪 Comprehensive Test Coverage

Created extensive test suite ([test_companions_only_party_contract.py](test_companions_only_party_contract.py)) covering:

### Booking Create Tests
- ✅ **Companions-only success**: Party with only companions creates booking
- ❌ **PRIMARY rejection**: Returns 400 when PRIMARY in party 
- ✅ **Empty party success**: PRIMARY-only bookings work
- ❌ **Validation**: Missing `first_name`/`last_name` returns 400

### Precheckin Submit Tests  
- ✅ **PRIMARY preservation**: Existing PRIMARY BookingGuest unchanged
- ✅ **Companion replacement**: Old companions deleted, new ones created
- ❌ **PRIMARY rejection**: Returns 400 when PRIMARY in party
- ✅ **Empty party**: Can submit no companions (PRIMARY-only)
- ❌ **Size validation**: Party size must match `adults + children`
- ✅ **Idempotency**: Multiple submissions work correctly

### End-to-End Integration Tests
- ✅ **Complete workflow**: Booking create → precheckin submit
- ✅ **Constraint invariant**: Exactly 1 PRIMARY maintained throughout
- ✅ **State transitions**: Proper party updates across endpoints

---

## 🔧 Verification Script

Created quick verification script ([verify_companions_only_contract.py](verify_companions_only_contract.py)) that:

- ✅ Tests both endpoints without full Django test setup
- ✅ Validates PRIMARY rejection behavior
- ✅ Confirms PRIMARY preservation in precheckin
- ✅ Verifies companion replacement logic

**Run verification:**
```bash
cd /path/to/HotelMateBackend
python verify_companions_only_contract.py
```

---

## 🎯 Behavioral Guarantees

### 1. **Unified Contract**
- Both endpoints use identical party validation logic
- Same error messages for PRIMARY rejection
- Consistent companions-only processing

### 2. **PRIMARY Safety**
- PRIMARY never appears in party payloads
- PRIMARY BookingGuest always preserved during precheckin
- Exactly 1 PRIMARY constraint maintained (enforced by DB)

### 3. **Companion Flexibility**
- Empty companions allowed (PRIMARY-only bookings)
- Optional email/phone fields for companions
- Clean replacement during precheckin updates

### 4. **Data Integrity**
- Party size validation against booking capacity
- Atomic transactions prevent partial updates
- Idempotent precheckin submissions

---

## 🔄 Migration Path

### Current Status: ✅ READY
- **No database migrations required**
- **Backward compatible** for existing bookings
- **Forward compatible** for new API consumers

### For API Consumers:
1. **Remove PRIMARY from party payloads** in both endpoints
2. **Use primary_* fields** for primary guest data  
3. **Send companions-only** in party arrays
4. **Handle 400 errors** if PRIMARY accidentally included

---

## 📋 Validation Summary

| Scenario | Booking Create | Precheckin Submit | Result |
|----------|---------------|-------------------|---------|
| Empty party | ✅ SUCCESS | ✅ SUCCESS | PRIMARY-only |
| Companions-only | ✅ SUCCESS | ✅ SUCCESS | PRIMARY + companions |
| PRIMARY in party | ❌ 400 ERROR | ❌ 400 ERROR | Rejected |
| Missing first/last name | ❌ 400 ERROR | ❌ 400 ERROR | Rejected |
| Size mismatch | N/A | ❌ 400 ERROR | Rejected |

---

## 🚀 Next Steps

1. **Deploy implementation** to staging environment
2. **Update API documentation** with new contract
3. **Notify frontend teams** of party payload changes  
4. **Monitor error logs** for PRIMARY rejection patterns
5. **Consider deprecation warnings** for transition period

**Contract now enforced: PRIMARY never sent, companions only! 🎉**