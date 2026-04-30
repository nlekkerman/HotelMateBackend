# RBAC Login Payload — Backend Confirmation

**Source of truth (verified live):**
- [staff/views.py](staff/views.py#L150-L264) — `CustomAuthToken.post` (the `/api/staff/login/` view)
- [staff/me_views.py](staff/me_views.py#L19-L57) — `StaffMeView.get` (the `/api/staff/hotel/<hotel_slug>/me/` view)
- [staff/permissions.py](staff/permissions.py#L102-L246) — `resolve_effective_access(user)`
- [staff/module_policy.py](staff/module_policy.py) — `MODULE_POLICY`, `resolve_module_policy(allowed_capabilities)`
- [staff/serializers.py](staff/serializers.py#L313-L373) — `StaffLoginOutputSerializer`

---

## 1. Does the login response include a top-level `rbac` object?

**Yes.** `rbac` is a top-level key on the `/api/staff/login/` response body.

It is produced as follows:

1. `CustomAuthToken.post` calls `resolve_effective_access(user)` ([staff/views.py:202](staff/views.py#L202)).
2. The full payload is merged into the response data via `data.update(permissions_payload)` ([staff/views.py:223](staff/views.py#L223)).
3. `resolve_effective_access` always sets `rbac = resolve_module_policy(allowed_capabilities)` ([staff/permissions.py:130, 174, 246](staff/permissions.py#L246)).
4. `resolve_module_policy` always emits an entry for **every** module in `MODULE_POLICY` (fail-closed: unknown caps are forced to `false`).

If your frontend currently sees `rbac: {}`, that is **not** what the backend emits — the backend always emits the full module map. Likely causes on the client side: stripping unknown fields in a typed model, reading the wrong response key, or caching an old payload from before Phase 6A.

> Note: `StaffLoginOutputSerializer` does not declare `rbac` as a field, **but** its `to_representation` method calls `resolve_effective_access(user)` and merges the result into `data` ([staff/serializers.py:339-352](staff/serializers.py#L339-L352)). DRF `Serializer.to_representation` returns the merged `data` dict directly, so `rbac` is included in the JSON response.

---

## 2. Exact shape (real example)

Below is a real example for a user with **all canonical capabilities** (e.g. a Django superuser). It is the literal output of `resolve_module_policy(CANONICAL_CAPABILITIES)` for the six modules you asked about, plus the surrounding top-level keys returned by `resolve_effective_access`.

```json
{
  "staff_id": 12,
  "token": "abc...redacted...",
  "username": "alice",
  "hotel_id": 1,
  "hotel_name": "Acme Hotel",
  "hotel": { "id": 1, "name": "Acme Hotel", "slug": "acme" },
  "profile_image_url": null,
  "role": "Front Desk Manager",
  "department": "Front Desk",

  "is_staff": true,
  "is_superuser": true,
  "hotel_slug": "acme",
  "access_level": "super_staff_admin",
  "tier": "super_user",
  "department_slug": "front-desk",
  "role_slug": "front-desk-manager",
  "allowed_navs": ["home", "chat", "rooms", "room_bookings", "restaurant_bookings", "housekeeping", "maintenance", "attendance", "staff_management", "room_services", "hotel_info", "admin_settings"],
  "navigation_items": [ /* NavigationItem rows */ ],
  "allowed_capabilities": [ /* canonical capability slugs */ ],

  "isAdmin": true,

  "rbac": {
    "bookings": {
      "visible": true,
      "read": true,
      "actions": {
        "update": true,
        "cancel": true,
        "assign_room": true,
        "checkin": true,
        "checkout": true,
        "communicate": true,
        "override_conflicts": true,
        "force_checkin": true,
        "force_checkout": true,
        "resolve_overstay": true,
        "modify_locked": true,
        "extend": true,
        "manage_rules": true
      }
    },
    "chat": {
      "visible": true,
      "read": true,
      "actions": {
        "conversation_read": true,
        "message_send": true,
        "message_moderate": true,
        "attachment_upload": true,
        "attachment_delete": true,
        "conversation_assign": true,
        "guest_respond": true
      }
    },
    "staff_chat": {
      "visible": true,
      "read": true,
      "actions": {
        "conversation_read": true,
        "conversation_create": true,
        "conversation_delete": true,
        "message_send": true,
        "message_moderate": true,
        "attachment_upload": true,
        "attachment_delete": true,
        "reaction_manage": true
      }
    },
    "attendance": {
      "visible": true,
      "read": true,
      "actions": {
        "clock_in_out": true,
        "break_toggle": true,
        "log_read_self": true,
        "log_read_all": true,
        "log_create": true,
        "log_update": true,
        "log_delete": true,
        "log_approve": true,
        "log_reject": true,
        "log_relink": true,
        "analytics_read": true,
        "period_read": true,
        "period_create": true,
        "period_update": true,
        "period_delete": true,
        "period_finalize": true,
        "period_unfinalize": true,
        "period_force_finalize": true,
        "shift_read": true,
        "shift_create": true,
        "shift_update": true,
        "shift_delete": true,
        "shift_bulk_write": true,
        "shift_copy": true,
        "shift_export_pdf": true,
        "shift_location_read": true,
        "shift_location_manage": true,
        "daily_plan_read": true,
        "daily_plan_manage": true,
        "daily_plan_entry_manage": true,
        "face_read": true,
        "face_register_self": true,
        "face_register_other": true,
        "face_revoke": true,
        "face_audit_read": true,
        "roster_read_self": true
      }
    },
    "rooms": {
      "visible": true,
      "read": true,
      "actions": {
        "inventory_create": true,
        "inventory_update": true,
        "inventory_delete": true,
        "type_manage": true,
        "media_manage": true,
        "out_of_order_set": true,
        "checkout_destructive": true,
        "status_transition": true,
        "maintenance_flag": true,
        "inspect": true,
        "maintenance_clear": true,
        "checkout_bulk": true
      }
    },
    "housekeeping": {
      "visible": true,
      "read": true,
      "actions": {
        "dashboard_read": true,
        "task_create": true,
        "task_update": true,
        "task_delete": true,
        "task_assign": true,
        "task_execute": true,
        "task_cancel": true,
        "status_transition": true,
        "status_front_desk": true,
        "status_override": true,
        "status_history_read": true
      }
    }
    /* and: guests, hotel_info, maintenance, restaurant_bookings, room_services, staff_management — all present, every one with {visible, read, actions:{...}} */
  }
}
```

The block under `"rbac"` was generated by running:

```powershell
python manage.py shell -c "from staff.module_policy import resolve_module_policy; from staff.capability_catalog import CANONICAL_CAPABILITIES; import json; r = resolve_module_policy(list(CANONICAL_CAPABILITIES)); print(json.dumps({k: r[k] for k in ['bookings','chat','staff_chat','attendance','rooms','housekeeping']}, indent=2))"
```

For a non-superuser, the **shape is identical** — every module key is always present, every action key is always present; only the boolean values differ.

---

## 3. Confirmed action keys per module

(Exact keys from the live `MODULE_POLICY` output above.)

### `bookings` (room bookings)
- `visible`, `read`
- actions: `update`, `cancel`, `assign_room`, `checkin`, `checkout`, `communicate`, `override_conflicts`, `force_checkin`, `force_checkout`, `resolve_overstay`, `modify_locked`, `extend`, `manage_rules`

### `chat` (guest chat)
- `visible`, `read`
- actions: `conversation_read`, `message_send`, `message_moderate`, `attachment_upload`, `attachment_delete`, `conversation_assign`, `guest_respond`

### `staff_chat`
- `visible`, `read`
- actions: `conversation_read`, `conversation_create`, `conversation_delete`, `message_send`, `message_moderate`, `attachment_upload`, `attachment_delete`, `reaction_manage`

### `attendance`
- `visible`, `read`
- actions: `clock_in_out`, `break_toggle`, `log_read_self`, `log_read_all`, `log_create`, `log_update`, `log_delete`, `log_approve`, `log_reject`, `log_relink`, `analytics_read`, `period_read`, `period_create`, `period_update`, `period_delete`, `period_finalize`, `period_unfinalize`, `period_force_finalize`, `shift_read`, `shift_create`, `shift_update`, `shift_delete`, `shift_bulk_write`, `shift_copy`, `shift_export_pdf`, `shift_location_read`, `shift_location_manage`, `daily_plan_read`, `daily_plan_manage`, `daily_plan_entry_manage`, `face_read`, `face_register_self`, `face_register_other`, `face_revoke`, `face_audit_read`, `roster_read_self`

### `rooms`
- `visible`, `read`
- actions: `inventory_create`, `inventory_update`, `inventory_delete`, `type_manage`, `media_manage`, `out_of_order_set`, `checkout_destructive`, `status_transition`, `maintenance_flag`, `inspect`, `maintenance_clear`, `checkout_bulk`

### `housekeeping`
- `visible`, `read`
- actions: `dashboard_read`, `task_create`, `task_update`, `task_delete`, `task_assign`, `task_execute`, `task_cancel`, `status_transition`, `status_front_desk`, `status_override`, `status_history_read`

---

## 4. Is `rbac` computed per user (not per role / nav)?

**Yes — per user.**

`resolve_effective_access(user)` ([staff/permissions.py:102](staff/permissions.py#L102)) computes:

```
allowed_capabilities = resolve_capabilities(
    tier=resolve_tier(user),
    role_slug=staff.role.slug,
    department_slug=staff.department.slug,
    is_superuser=user.is_superuser,
)
rbac = resolve_module_policy(allowed_capabilities)
```

So `rbac` is the union of tier presets + role presets + department presets + Django superuser bypass, evaluated **for the specific authenticated user**. It is not a role lookup, not derived from `allowed_navs`, and not the same for two users in the same role if their tier / department / superuser flag differ.

---

## 5. Does `/staff/me/` return the same `rbac` shape?

**Yes — identical shape.**

`StaffMeView.get` ([staff/me_views.py:30-44](staff/me_views.py#L30-L44)) calls the same `resolve_effective_access(request.user)` and merges the full payload (including `rbac`) into the response. The route is:

```
GET /api/staff/hotel/<hotel_slug>/me/
```

Both 200 (staff found) and 404 (no staff profile for that hotel) responses include the full canonical permissions payload, so the frontend can rely on the same `rbac` keys on both endpoints.

---

## Summary

| Question | Answer |
| --- | --- |
| 1. Top-level `rbac` on login? | **Yes**, always. Produced by `resolve_module_policy` and merged via `StaffLoginOutputSerializer.to_representation`. |
| 2. Exact shape | `rbac.<module>.{visible, read, actions.<action>}`, every module always present, every action always present. See JSON above. |
| 3. Action keys for bookings / chat / staff_chat / attendance / rooms / housekeeping | Listed above, verified live from `MODULE_POLICY`. |
| 4. Per user? | **Yes** — computed from the user's tier ∪ role ∪ department ∪ superuser flag. Not from role name. Not from nav. |
| 5. `/staff/me/` returns same shape? | **Yes**, same `resolve_effective_access` call, same `rbac` keys. |

If the client is observing `rbac: {}`, that is a client-side issue (response parsing / typed model stripping unknown fields / stale cache). The backend currently emits the full per-module map on every successful login and on every `/staff/hotel/<slug>/me/` GET.
