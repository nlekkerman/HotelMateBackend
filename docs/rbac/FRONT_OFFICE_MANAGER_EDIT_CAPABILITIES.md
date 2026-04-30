# Front Office Manager — Edit Capabilities

> **Source of truth:** `ROLE_PRESET_CAPABILITIES['front_office_manager']` in
> [staff/capability_catalog.py](../../staff/capability_catalog.py) and
> `MODULE_POLICY` in [staff/module_policy.py](../../staff/module_policy.py).
>
> Role bundle (line 1468):
> `_BOOKING_MANAGE | _ROOM_SUPERVISE | _HOUSEKEEPING_SUPERVISE | _MAINTENANCE_REPORTER | _GUESTS_OPERATE | _HOTEL_INFO_READ`

This document lists **only edit / mutation authority** (writes, deletes,
status changes, assignments). Pure reads are excluded.

---

## 1. Bookings (room bookings) — `_BOOKING_MANAGE`

Module: `bookings` — full manage bundle.

| Frontend gate | What they can do |
| --- | --- |
| `user.rbac.bookings.actions.update` | Edit booking record (mark seen, confirm, modify fields) |
| `user.rbac.bookings.actions.cancel` | Cancel a booking |
| `user.rbac.bookings.actions.assign_room` | Assign / move room on a booking |
| `user.rbac.bookings.actions.checkin` | Check guest in |
| `user.rbac.bookings.actions.checkout` | Check guest out |
| `user.rbac.bookings.actions.communicate` | Send precheckin / survey guest comms |
| `user.rbac.bookings.actions.override_conflicts` | Override booking conflicts (supervise) |
| `user.rbac.bookings.actions.force_checkin` | Force checkin (supervise) |
| `user.rbac.bookings.actions.force_checkout` | Force checkout (supervise) |
| `user.rbac.bookings.actions.resolve_overstay` | Resolve overstay (supervise) |
| `user.rbac.bookings.actions.modify_locked` | Modify a locked booking (supervise) |
| `user.rbac.bookings.actions.extend` | Extend stay (supervise) |
| `user.rbac.bookings.actions.manage_rules` | Manage booking rules / config |

---

## 2. Rooms — `_ROOM_SUPERVISE`

Module: `rooms` — supervise bundle (no inventory CRUD, no destructive checkout, no out-of-order toggle).

| Frontend gate | What they can do |
| --- | --- |
| `user.rbac.rooms.actions.status_transition` | Standard turnover transitions (start cleaning, mark cleaned) |
| `user.rbac.rooms.actions.maintenance_flag` | Flag a room for maintenance |
| `user.rbac.rooms.actions.maintenance_clear` | Clear a maintenance flag |
| `user.rbac.rooms.actions.inspect` | Pass / fail inspection |
| `user.rbac.rooms.actions.checkout_bulk` | Bulk (non-destructive) checkout |

**Cannot edit:** `inventory_create`, `inventory_update`, `inventory_delete`,
`type_manage`, `media_manage`, `out_of_order_set`, `checkout_destructive`.

---

## 3. Housekeeping — `_HOUSEKEEPING_SUPERVISE`

Module: `housekeeping` — supervise bundle (no `task_delete`).

| Frontend gate | What they can do |
| --- | --- |
| `user.rbac.housekeeping.actions.task_create` | Create housekeeping task |
| `user.rbac.housekeeping.actions.task_update` | Edit housekeeping task |
| `user.rbac.housekeeping.actions.task_assign` | Assign housekeeping task to staff |
| `user.rbac.housekeeping.actions.task_cancel` | Cancel a housekeeping task |
| `user.rbac.housekeeping.actions.task_execute` | Start / complete an own task |
| `user.rbac.housekeeping.actions.status_transition` | Standard room status transition |
| `user.rbac.housekeeping.actions.status_override` | Manager-level room status override |

**Cannot edit:** `task_delete`, `status_front_desk` (the front-desk-only
status surface is granted by the `front_office` **department** preset, not
by this role — see §7).

---

## 4. Maintenance — `_MAINTENANCE_REPORTER`

Module: `maintenance` — reporter only.

| Frontend gate | What they can do |
| --- | --- |
| `user.rbac.maintenance.actions.request_create` | File a new maintenance request |

**Cannot edit:** accept, resolve, update, reassign, reopen, close, delete,
comment moderate, photo upload/delete (those need maintenance roles).

---

## 5. Guests — `_GUESTS_OPERATE`

Module: `guests`.

| Frontend gate | What they can do |
| --- | --- |
| `user.rbac.guests.actions.update` | Edit in-house guest record |

---

## 6. Hotel Info — `_HOTEL_INFO_READ`

**No edit authority.** Read-only on hotel info entries, categories, and QR.

---

## 7. Add-ons typically present (NOT from the `front_office_manager` role itself)

A real front office manager usually also carries `department = front_office`
and `tier = super_staff_admin`. Those add the following **edit** capabilities
on top of the role preset above:

### From `DEPARTMENT_PRESET_CAPABILITIES['front_office']`

| Frontend gate | What they can do |
| --- | --- |
| `user.rbac.housekeeping.actions.status_front_desk` | Front-desk-driven room status changes |
| `user.rbac.chat.actions.conversation_assign` | Assign / hand off guest chat conversations |
| `user.rbac.chat.actions.guest_respond` | Eligible to receive guest-chat routing |

### From `super_staff_admin` tier baseline (`_SUPERVISOR_AUTHORITY`)

| Frontend gate | What they can do |
| --- | --- |
| `user.rbac.chat.actions.message_moderate` | Moderate (hard-delete) others' guest chat messages |
| `user.rbac.chat.actions.conversation_assign` | (already granted by dept) |
| `user.rbac.staff_chat.actions.message_moderate` | Moderate staff-chat messages |
| `user.rbac.staff_chat.actions.conversation_delete` | Delete staff-chat conversations |

### From the cross-tier chat / staff-chat base bundles

| Frontend gate | What they can do |
| --- | --- |
| `user.rbac.chat.actions.message_send` | Send guest chat message |
| `user.rbac.chat.actions.attachment_upload` | Upload guest chat attachment |
| `user.rbac.chat.actions.attachment_delete` | Delete own guest chat attachment |
| `user.rbac.staff_chat.actions.conversation_create` | Create staff chat conversation |
| `user.rbac.staff_chat.actions.message_send` | Send staff chat message |
| `user.rbac.staff_chat.actions.attachment_upload` | Upload staff chat attachment |
| `user.rbac.staff_chat.actions.attachment_delete` | Delete own staff chat attachment |
| `user.rbac.staff_chat.actions.reaction_manage` | Add / remove reactions |

---

## 8. Things they explicitly CANNOT edit

- Room inventory CRUD, room types, media, out-of-order, destructive checkout.
- Housekeeping task **delete**.
- Maintenance lifecycle beyond filing a ticket (no accept / resolve / close / delete / reassign / update / reopen / comment moderate / photo upload-delete).
- Hotel info entries (read-only).
- Restaurant bookings (no caps in any of their bundles).
- Room services menu / orders / breakfast (no caps in any of their bundles).
- Attendance management (no caps in any of their bundles — beyond what the tier might grant for self clock-in/out, which is not in the role preset).
- Staff management (creating / updating / deactivating staff, role/department/access_level/nav assignment, supervise) — those require the `staff_admin`, `super_staff_admin`, or `hotel_manager` **role** presets, NOT `front_office_manager`.

---

**End.** Frontend MUST gate every edit button on the exact `user.rbac.<module>.actions.<action>` boolean shown above. Backend `403` is the final authority.
