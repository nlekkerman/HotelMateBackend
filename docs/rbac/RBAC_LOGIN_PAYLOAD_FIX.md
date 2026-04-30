# `/api/staff/login/` Missing `rbac` — Diagnosis & Fix

**Status:** Bug confirmed and fixed in [staff/serializers.py](staff/serializers.py#L313).

---

## 1. Which view handles `/api/staff/login/`

`CustomAuthToken.post` in [staff/views.py](staff/views.py#L150-L264).

URL wiring: [staff/urls.py:56](staff/urls.py#L56) →
```
path('login/', CustomAuthToken.as_view(), name='login'),
```

The view DOES call `resolve_effective_access(user)` at line 202 and DOES merge the result into the dict it passes to the serializer at line 223. So the payload is computed correctly.

The bug is in the **output serializer**, not the view.

---

## 2. Why `rbac` was missing

Look at how the view returns the response:

```python
output_serializer = StaffLoginOutputSerializer(data=data, context={'request': request})
output_serializer.is_valid(raise_exception=True)
return Response(output_serializer.data)
```

This uses the serializer in **input mode** (`data=data`), then returns `output_serializer.data`. DRF's behavior here is:

1. `is_valid()` produces `validated_data`, which contains **only declared fields** on the serializer.
2. `output_serializer.data` calls `to_representation(validated_data)`.

The previous `StaffLoginOutputSerializer` declared:

```
staff_id, username, token, hotel_id, hotel_name, hotel,
is_staff, is_superuser, hotel_slug, access_level,
allowed_navs, navigation_items,
isAdmin, profile_image_url, role, department
```

It did NOT declare:

- `rbac`
- `tier`
- `role_slug`
- `department_slug`
- `allowed_capabilities`
- `user`  ← critical: the raw user object passed in for the safety-net rehydrate

So during validation, all six were stripped from `validated_data`. Then the override:

```python
def to_representation(self, instance):
    ...
    user = instance.get('user')  # ← always None now
    if user:
        permissions = resolve_effective_access(user)
        data.update(permissions)
    return data
```

…never entered the `if user` branch, because `user` had been silently dropped by validation. Result: the response contained the declared fields only — exactly what your network tab shows.

This also explains why your response is missing `tier`, `role_slug`, `department_slug`, and `allowed_capabilities` (same root cause).

---

## 3. The fix

Two changes in `StaffLoginOutputSerializer`:

1. Declare the missing canonical permissions fields so they survive validation:
   - `rbac = serializers.DictField(required=False)`
   - `tier`, `role_slug`, `department_slug` → `CharField(allow_null=True, required=False)`
   - `allowed_capabilities` → `ListField(child=CharField(), required=False)`

2. Harden `to_representation` to recover `user` from `initial_data` or `context['request'].user` if it was stripped, so the safety net always re-runs `resolve_effective_access` and merges `rbac` into the final response.

After the fix, calling the serializer end-to-end with a real `Staff` row produces:

```
TOP KEYS: ['access_level', 'allowed_capabilities', 'allowed_navs',
           'department', 'department_slug', 'hotel', 'hotel_id', 'hotel_name',
           'hotel_slug', 'isAdmin', 'is_staff', 'is_superuser',
           'navigation_items', 'profile_image_url',
           'rbac', 'role', 'role_slug',
           'staff_id', 'tier', 'token', 'username']

HAS rbac: True
rbac modules: ['attendance', 'bookings', 'chat', 'guests', 'hotel_info',
               'housekeeping', 'maintenance', 'restaurant_bookings',
               'room_services', 'rooms', 'staff_chat', 'staff_management']
```

All 12 `MODULE_POLICY` modules are present, every one with `{visible, read, actions:{...}}`. Action keys are exactly as listed in the previous answer doc and the contract.

---

## 4. Should you use `/staff/me/` instead?

You don't have to. After the fix, `/api/staff/login/` returns the full canonical payload including `rbac`.

But `/api/staff/hotel/<hotel_slug>/me/` is also a valid rehydrate endpoint and returns the **same** shape — see `StaffMeView.get` in [staff/me_views.py:30-44](staff/me_views.py#L30-L44). It calls `resolve_effective_access(request.user)` and merges the entire payload into the response. Use it whenever the frontend needs to refresh permissions without re-authenticating (e.g. after a role/department change).

Recommended client behavior:

1. On login → consume `data.rbac` directly from `/api/staff/login/`.
2. On app focus / periodic refresh / after any "your authority changed" signal → call `/api/staff/hotel/<hotel_slug>/me/` and replace the cached `rbac`.
3. Always keep `rbac: data.rbac || {}` as the fail-closed fallback (correct).

---

## 5. Action required

- Pull / deploy the change to [staff/serializers.py](staff/serializers.py#L313-L379).
- Re-test `/api/staff/login/` — `rbac` will now appear at the top level of the JSON body, alongside `tier`, `role_slug`, `department_slug`, and `allowed_capabilities`.
- No frontend changes required; your existing `data.rbac` consumer will start working immediately once the backend is redeployed.
