# RBAC Frontend Usage Contract

> **Source of truth.** Derived strictly from backend code:
> - `staff/capability_catalog.py` — canonical capability slugs
> - `staff/module_policy.py` — `MODULE_POLICY`, `resolve_module_policy`
> - `staff/permissions.py` — `resolve_effective_access`, `HasNavPermission`, `HasCapability`, tier resolver
> - `staff/nav_catalog.py` — `CANONICAL_NAV_SLUGS` / `CANONICAL_NAV_ITEMS`
>
> No documentation, README, comments, or assumptions were used. Where this document and any other doc disagree, **this document is wrong and the code is right**.

---

## 1. Exact `user.rbac` payload shape

The auth payload is computed by `resolve_effective_access(user)` in [staff/permissions.py](staff/permissions.py). The `rbac` field is produced by `resolve_module_policy(allowed_capabilities)` in [staff/module_policy.py](staff/module_policy.py).

Top-level payload keys returned by `resolve_effective_access`:

```
is_staff: bool
is_superuser: bool
hotel_slug: string | null
access_level: string | null      # tier slug; CONTEXT ONLY — do not gate on this
tier: string | null              # CONTEXT ONLY
department_slug: string | null   # CONTEXT ONLY
role_slug: string | null         # CONTEXT ONLY
allowed_navs: string[]           # canonical nav slugs the user can see
navigation_items: object[]       # NavigationItem rows (visibility metadata only)
allowed_capabilities: string[]   # raw canonical capability slugs
rbac: { [moduleKey]: { visible: bool, read: bool, actions: { [actionKey]: bool } } }
```

Per-module shape (one entry per `MODULE_POLICY` key):

```
user.rbac.<module>.visible           # bool — module/page/nav visibility
user.rbac.<module>.read              # bool — read access to module data
user.rbac.<module>.actions.<action>  # bool — per-action authority
```

**Missing-key behavior (fail-closed):**

- `resolve_module_policy` always emits an entry for **every** module in `MODULE_POLICY`. A module key the frontend expects but does not find at runtime means the backend dropped it — frontend MUST treat as `false` (deny).
- An `actions[<action>]` key the frontend expects but does not find MUST be treated as `false` (deny).
- `actions[<action>] === false` is the canonical deny signal — the action button must be hidden/disabled.
- `visible === false` MUST hide the entire module/page/nav entry.
- A capability that is not in `CANONICAL_CAPABILITIES` is forced to `false` by `resolve_module_policy` (drift protection). Frontend never sees `true` for an unknown capability.

The backend remains the final authority: any successful frontend gate must still be confirmed by the endpoint, which returns `403` if the capability is missing.

---

## 2. All RBAC modules

Every module key present in `MODULE_POLICY` (the full enumeration that hydrates `user.rbac`).

| Module key             | Nav slug                | Visible path                            | Actions path                                       | Backend source                                                                                          |
| ---------------------- | ----------------------- | --------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `attendance`           | `attendance`            | `user.rbac.attendance.visible`          | `user.rbac.attendance.actions.<action>`            | `MODULE_POLICY['attendance']` in [staff/module_policy.py](staff/module_policy.py)                       |
| `bookings`             | `room_bookings`         | `user.rbac.bookings.visible`            | `user.rbac.bookings.actions.<action>`              | `MODULE_POLICY['bookings']` in [staff/module_policy.py](staff/module_policy.py)                         |
| `chat`                 | `chat`                  | `user.rbac.chat.visible`                | `user.rbac.chat.actions.<action>`                  | `MODULE_POLICY['chat']` in [staff/module_policy.py](staff/module_policy.py)                             |
| `guests`               | *(none)*                | `user.rbac.guests.visible`              | `user.rbac.guests.actions.<action>`                | `MODULE_POLICY['guests']` in [staff/module_policy.py](staff/module_policy.py)                           |
| `hotel_info`           | `hotel_info`            | `user.rbac.hotel_info.visible`          | `user.rbac.hotel_info.actions.<action>`            | `MODULE_POLICY['hotel_info']` in [staff/module_policy.py](staff/module_policy.py)                       |
| `housekeeping`         | `housekeeping`          | `user.rbac.housekeeping.visible`        | `user.rbac.housekeeping.actions.<action>`          | `MODULE_POLICY['housekeeping']` in [staff/module_policy.py](staff/module_policy.py)                     |
| `maintenance`          | `maintenance`           | `user.rbac.maintenance.visible`         | `user.rbac.maintenance.actions.<action>`           | `MODULE_POLICY['maintenance']` in [staff/module_policy.py](staff/module_policy.py)                      |
| `restaurant_bookings`  | `restaurant_bookings`   | `user.rbac.restaurant_bookings.visible` | `user.rbac.restaurant_bookings.actions.<action>`   | `MODULE_POLICY['restaurant_bookings']` in [staff/module_policy.py](staff/module_policy.py)              |
| `room_services`        | `room_services`         | `user.rbac.room_services.visible`       | `user.rbac.room_services.actions.<action>`         | `MODULE_POLICY['room_services']` in [staff/module_policy.py](staff/module_policy.py)                    |
| `rooms`                | `rooms`                 | `user.rbac.rooms.visible`               | `user.rbac.rooms.actions.<action>`                 | `MODULE_POLICY['rooms']` in [staff/module_policy.py](staff/module_policy.py)                            |
| `staff_chat`           | *(none)*                | `user.rbac.staff_chat.visible`          | `user.rbac.staff_chat.actions.<action>`            | `MODULE_POLICY['staff_chat']` in [staff/module_policy.py](staff/module_policy.py)                       |
| `staff_management`     | `staff_management`      | `user.rbac.staff_management.visible`    | `user.rbac.staff_management.actions.<action>`      | `MODULE_POLICY['staff_management']` in [staff/module_policy.py](staff/module_policy.py)                 |

**Notes on naming, derived strictly from code:**

- Module key for hotel-room bookings is `bookings`, but the nav slug is `room_bookings`. Frontend MUST read `user.rbac.bookings.*` for room-booking authority and use `room_bookings` only for the nav entry.
- `guests` and `staff_chat` exist as RBAC modules but are NOT in `CANONICAL_NAV_SLUGS`. They have no nav entry; gate their UI strictly on `user.rbac.guests.visible` / `user.rbac.staff_chat.visible`.
- `home` and `admin_settings` are nav slugs in `CANONICAL_NAV_SLUGS` but have NO entry in `MODULE_POLICY`. They are visibility-only via `allowed_navs`; there are no `user.rbac.home.*` / `user.rbac.admin_settings.*` keys.
- There is NO module key for "admin_settings" / "public page builder" / "provisioning" / "super_user" in the RBAC payload. Those surfaces are gated by tier (`IsDjangoSuperUser`, `IsAdminTier`, `IsSuperStaffAdminOrAbove`) at the endpoint level — the frontend cannot derive button-level authority for them from `user.rbac`.

---

## 3. All actions by module

Action keys are exactly as registered in `MODULE_POLICY[<module>]['actions']` in [staff/module_policy.py](staff/module_policy.py). No invented keys.

### attendance

Visible:
- `user.rbac.attendance.visible`

Read:
- `user.rbac.attendance.read`

Actions:
- `user.rbac.attendance.actions.clock_in_out`
- `user.rbac.attendance.actions.break_toggle`
- `user.rbac.attendance.actions.log_read_self`
- `user.rbac.attendance.actions.log_read_all`
- `user.rbac.attendance.actions.log_create`
- `user.rbac.attendance.actions.log_update`
- `user.rbac.attendance.actions.log_delete`
- `user.rbac.attendance.actions.log_approve`
- `user.rbac.attendance.actions.log_reject`
- `user.rbac.attendance.actions.log_relink`
- `user.rbac.attendance.actions.analytics_read`
- `user.rbac.attendance.actions.period_read`
- `user.rbac.attendance.actions.period_create`
- `user.rbac.attendance.actions.period_update`
- `user.rbac.attendance.actions.period_delete`
- `user.rbac.attendance.actions.period_finalize`
- `user.rbac.attendance.actions.period_unfinalize`
- `user.rbac.attendance.actions.period_force_finalize`
- `user.rbac.attendance.actions.shift_read`
- `user.rbac.attendance.actions.shift_create`
- `user.rbac.attendance.actions.shift_update`
- `user.rbac.attendance.actions.shift_delete`
- `user.rbac.attendance.actions.shift_bulk_write`
- `user.rbac.attendance.actions.shift_copy`
- `user.rbac.attendance.actions.shift_export_pdf`
- `user.rbac.attendance.actions.shift_location_read`
- `user.rbac.attendance.actions.shift_location_manage`
- `user.rbac.attendance.actions.daily_plan_read`
- `user.rbac.attendance.actions.daily_plan_manage`
- `user.rbac.attendance.actions.daily_plan_entry_manage`
- `user.rbac.attendance.actions.face_read`
- `user.rbac.attendance.actions.face_register_self`
- `user.rbac.attendance.actions.face_register_other`
- `user.rbac.attendance.actions.face_revoke`
- `user.rbac.attendance.actions.face_audit_read`
- `user.rbac.attendance.actions.roster_read_self`

### bookings (room bookings)

Visible:
- `user.rbac.bookings.visible`

Read:
- `user.rbac.bookings.read`

Actions:
- `user.rbac.bookings.actions.update`
- `user.rbac.bookings.actions.cancel`
- `user.rbac.bookings.actions.assign_room`
- `user.rbac.bookings.actions.checkin`
- `user.rbac.bookings.actions.checkout`
- `user.rbac.bookings.actions.communicate`
- `user.rbac.bookings.actions.override_conflicts`
- `user.rbac.bookings.actions.force_checkin`
- `user.rbac.bookings.actions.force_checkout`
- `user.rbac.bookings.actions.resolve_overstay`
- `user.rbac.bookings.actions.modify_locked`
- `user.rbac.bookings.actions.extend`
- `user.rbac.bookings.actions.manage_rules`

### chat (guest chat)

Visible:
- `user.rbac.chat.visible`

Read:
- `user.rbac.chat.read`

Actions:
- `user.rbac.chat.actions.conversation_read`
- `user.rbac.chat.actions.message_send`
- `user.rbac.chat.actions.message_moderate`
- `user.rbac.chat.actions.attachment_upload`
- `user.rbac.chat.actions.attachment_delete`
- `user.rbac.chat.actions.conversation_assign`
- `user.rbac.chat.actions.guest_respond`

### guests

Visible:
- `user.rbac.guests.visible`

Read:
- `user.rbac.guests.read`

Actions:
- `user.rbac.guests.actions.update`

### hotel_info

Visible:
- `user.rbac.hotel_info.visible`

Read:
- `user.rbac.hotel_info.read`

Actions:
- `user.rbac.hotel_info.actions.entry_read`
- `user.rbac.hotel_info.actions.entry_create`
- `user.rbac.hotel_info.actions.entry_update`
- `user.rbac.hotel_info.actions.entry_delete`
- `user.rbac.hotel_info.actions.category_read`
- `user.rbac.hotel_info.actions.category_manage`
- `user.rbac.hotel_info.actions.qr_read`
- `user.rbac.hotel_info.actions.qr_generate`

### housekeeping

Visible:
- `user.rbac.housekeeping.visible`

Read:
- `user.rbac.housekeeping.read`

Actions:
- `user.rbac.housekeeping.actions.dashboard_read`
- `user.rbac.housekeeping.actions.task_create`
- `user.rbac.housekeeping.actions.task_update`
- `user.rbac.housekeeping.actions.task_delete`
- `user.rbac.housekeeping.actions.task_assign`
- `user.rbac.housekeeping.actions.task_execute`
- `user.rbac.housekeeping.actions.task_cancel`
- `user.rbac.housekeeping.actions.status_transition`
- `user.rbac.housekeeping.actions.status_front_desk`
- `user.rbac.housekeeping.actions.status_override`
- `user.rbac.housekeeping.actions.status_history_read`

### maintenance

Visible:
- `user.rbac.maintenance.visible`

Read:
- `user.rbac.maintenance.read`

Actions:
- `user.rbac.maintenance.actions.request_create`
- `user.rbac.maintenance.actions.request_accept`
- `user.rbac.maintenance.actions.request_resolve`
- `user.rbac.maintenance.actions.request_update`
- `user.rbac.maintenance.actions.request_reassign`
- `user.rbac.maintenance.actions.request_reopen`
- `user.rbac.maintenance.actions.request_close`
- `user.rbac.maintenance.actions.request_delete`
- `user.rbac.maintenance.actions.comment_create`
- `user.rbac.maintenance.actions.comment_moderate`
- `user.rbac.maintenance.actions.photo_upload`
- `user.rbac.maintenance.actions.photo_delete`

### restaurant_bookings

Visible:
- `user.rbac.restaurant_bookings.visible`

Read:
- `user.rbac.restaurant_bookings.read`

Actions:
- `user.rbac.restaurant_bookings.actions.restaurant_read`
- `user.rbac.restaurant_bookings.actions.restaurant_create`
- `user.rbac.restaurant_bookings.actions.restaurant_update`
- `user.rbac.restaurant_bookings.actions.restaurant_delete`
- `user.rbac.restaurant_bookings.actions.category_read`
- `user.rbac.restaurant_bookings.actions.category_manage`
- `user.rbac.restaurant_bookings.actions.record_read`
- `user.rbac.restaurant_bookings.actions.record_create`
- `user.rbac.restaurant_bookings.actions.record_update`
- `user.rbac.restaurant_bookings.actions.record_delete`
- `user.rbac.restaurant_bookings.actions.record_mark_seen`
- `user.rbac.restaurant_bookings.actions.table_read`
- `user.rbac.restaurant_bookings.actions.table_manage`
- `user.rbac.restaurant_bookings.actions.blueprint_read`
- `user.rbac.restaurant_bookings.actions.blueprint_manage`
- `user.rbac.restaurant_bookings.actions.assignment_assign`
- `user.rbac.restaurant_bookings.actions.assignment_unseat`

### room_services

Visible:
- `user.rbac.room_services.visible`

Read:
- `user.rbac.room_services.read`

Actions:
- `user.rbac.room_services.actions.menu_read`
- `user.rbac.room_services.actions.menu_item_create`
- `user.rbac.room_services.actions.menu_item_update`
- `user.rbac.room_services.actions.menu_item_delete`
- `user.rbac.room_services.actions.menu_item_image_manage`
- `user.rbac.room_services.actions.order_read`
- `user.rbac.room_services.actions.order_create`
- `user.rbac.room_services.actions.order_update`
- `user.rbac.room_services.actions.order_delete`
- `user.rbac.room_services.actions.order_accept`
- `user.rbac.room_services.actions.order_complete`
- `user.rbac.room_services.actions.breakfast_order_read`
- `user.rbac.room_services.actions.breakfast_order_create`
- `user.rbac.room_services.actions.breakfast_order_update`
- `user.rbac.room_services.actions.breakfast_order_delete`
- `user.rbac.room_services.actions.breakfast_order_accept`
- `user.rbac.room_services.actions.breakfast_order_complete`

### rooms

Visible:
- `user.rbac.rooms.visible`

Read:
- `user.rbac.rooms.read`

Actions:
- `user.rbac.rooms.actions.inventory_create`
- `user.rbac.rooms.actions.inventory_update`
- `user.rbac.rooms.actions.inventory_delete`
- `user.rbac.rooms.actions.type_manage`
- `user.rbac.rooms.actions.media_manage`
- `user.rbac.rooms.actions.out_of_order_set`
- `user.rbac.rooms.actions.checkout_destructive`
- `user.rbac.rooms.actions.status_transition`
- `user.rbac.rooms.actions.maintenance_flag`
- `user.rbac.rooms.actions.inspect`
- `user.rbac.rooms.actions.maintenance_clear`
- `user.rbac.rooms.actions.checkout_bulk`

### staff_chat

Visible:
- `user.rbac.staff_chat.visible`

Read:
- `user.rbac.staff_chat.read`

Actions:
- `user.rbac.staff_chat.actions.conversation_read`
- `user.rbac.staff_chat.actions.conversation_create`
- `user.rbac.staff_chat.actions.conversation_delete`
- `user.rbac.staff_chat.actions.message_send`
- `user.rbac.staff_chat.actions.message_moderate`
- `user.rbac.staff_chat.actions.attachment_upload`
- `user.rbac.staff_chat.actions.attachment_delete`
- `user.rbac.staff_chat.actions.reaction_manage`

### staff_management

Visible:
- `user.rbac.staff_management.visible`

Read:
- `user.rbac.staff_management.read`

Actions:
- `user.rbac.staff_management.actions.staff_read`
- `user.rbac.staff_management.actions.user_read`
- `user.rbac.staff_management.actions.pending_registration_read`
- `user.rbac.staff_management.actions.staff_create`
- `user.rbac.staff_management.actions.staff_update_profile`
- `user.rbac.staff_management.actions.staff_deactivate`
- `user.rbac.staff_management.actions.staff_delete`
- `user.rbac.staff_management.actions.authority_view`
- `user.rbac.staff_management.actions.authority_role_assign`
- `user.rbac.staff_management.actions.authority_department_assign`
- `user.rbac.staff_management.actions.authority_access_level_assign`
- `user.rbac.staff_management.actions.authority_nav_assign`
- `user.rbac.staff_management.actions.authority_supervise`
- `user.rbac.staff_management.actions.role_read`
- `user.rbac.staff_management.actions.role_manage`
- `user.rbac.staff_management.actions.department_read`
- `user.rbac.staff_management.actions.department_manage`
- `user.rbac.staff_management.actions.registration_package_read`
- `user.rbac.staff_management.actions.registration_package_create`
- `user.rbac.staff_management.actions.registration_package_email`
- `user.rbac.staff_management.actions.registration_package_print`

---

## 4. Backend capability → frontend RBAC path map

Every canonical capability that appears in `MODULE_POLICY` and the exact frontend `user.rbac.*` boolean it controls. Capabilities below come directly from `staff.capability_catalog.CANONICAL_CAPABILITIES`; mapping comes from `MODULE_POLICY` in [staff/module_policy.py](staff/module_policy.py).

The "Module" column refers to the `MODULE_POLICY` key, not the nav slug.

| Backend capability                                  | Module                | Frontend RBAC path                                                    |
| --------------------------------------------------- | --------------------- | --------------------------------------------------------------------- |
| `attendance.module.view`                            | `attendance`          | `user.rbac.attendance.visible`                                        |
| `attendance.log.read_self`                          | `attendance`          | `user.rbac.attendance.read` and `user.rbac.attendance.actions.log_read_self` |
| `attendance.clock.in_out`                           | `attendance`          | `user.rbac.attendance.actions.clock_in_out`                           |
| `attendance.break.toggle`                           | `attendance`          | `user.rbac.attendance.actions.break_toggle`                           |
| `attendance.log.read_all`                           | `attendance`          | `user.rbac.attendance.actions.log_read_all`                           |
| `attendance.log.create`                             | `attendance`          | `user.rbac.attendance.actions.log_create`                             |
| `attendance.log.update`                             | `attendance`          | `user.rbac.attendance.actions.log_update`                             |
| `attendance.log.delete`                             | `attendance`          | `user.rbac.attendance.actions.log_delete`                             |
| `attendance.log.approve`                            | `attendance`          | `user.rbac.attendance.actions.log_approve`                            |
| `attendance.log.reject`                             | `attendance`          | `user.rbac.attendance.actions.log_reject`                             |
| `attendance.log.relink`                             | `attendance`          | `user.rbac.attendance.actions.log_relink`                             |
| `attendance.analytics.read`                         | `attendance`          | `user.rbac.attendance.actions.analytics_read`                         |
| `attendance.period.read`                            | `attendance`          | `user.rbac.attendance.actions.period_read`                            |
| `attendance.period.create`                          | `attendance`          | `user.rbac.attendance.actions.period_create`                          |
| `attendance.period.update`                          | `attendance`          | `user.rbac.attendance.actions.period_update`                          |
| `attendance.period.delete`                          | `attendance`          | `user.rbac.attendance.actions.period_delete`                          |
| `attendance.period.finalize`                        | `attendance`          | `user.rbac.attendance.actions.period_finalize`                        |
| `attendance.period.unfinalize`                      | `attendance`          | `user.rbac.attendance.actions.period_unfinalize`                      |
| `attendance.period.force_finalize`                  | `attendance`          | `user.rbac.attendance.actions.period_force_finalize`                  |
| `attendance.shift.read`                             | `attendance`          | `user.rbac.attendance.actions.shift_read`                             |
| `attendance.shift.create`                           | `attendance`          | `user.rbac.attendance.actions.shift_create`                           |
| `attendance.shift.update`                           | `attendance`          | `user.rbac.attendance.actions.shift_update`                           |
| `attendance.shift.delete`                           | `attendance`          | `user.rbac.attendance.actions.shift_delete`                           |
| `attendance.shift.bulk_write`                       | `attendance`          | `user.rbac.attendance.actions.shift_bulk_write`                       |
| `attendance.shift.copy`                             | `attendance`          | `user.rbac.attendance.actions.shift_copy`                             |
| `attendance.shift.export_pdf`                       | `attendance`          | `user.rbac.attendance.actions.shift_export_pdf`                       |
| `attendance.shift_location.read`                    | `attendance`          | `user.rbac.attendance.actions.shift_location_read`                    |
| `attendance.shift_location.manage`                  | `attendance`          | `user.rbac.attendance.actions.shift_location_manage`                  |
| `attendance.daily_plan.read`                        | `attendance`          | `user.rbac.attendance.actions.daily_plan_read`                        |
| `attendance.daily_plan.manage`                      | `attendance`          | `user.rbac.attendance.actions.daily_plan_manage`                      |
| `attendance.daily_plan.entry_manage`                | `attendance`          | `user.rbac.attendance.actions.daily_plan_entry_manage`                |
| `attendance.face.read`                              | `attendance`          | `user.rbac.attendance.actions.face_read`                              |
| `attendance.face.register_self`                     | `attendance`          | `user.rbac.attendance.actions.face_register_self`                     |
| `attendance.face.register_other`                    | `attendance`          | `user.rbac.attendance.actions.face_register_other`                    |
| `attendance.face.revoke`                            | `attendance`          | `user.rbac.attendance.actions.face_revoke`                            |
| `attendance.face.audit_read`                        | `attendance`          | `user.rbac.attendance.actions.face_audit_read`                        |
| `attendance.roster.read_self`                       | `attendance`          | `user.rbac.attendance.actions.roster_read_self`                       |
| `booking.module.view`                               | `bookings`            | `user.rbac.bookings.visible`                                          |
| `booking.record.read`                               | `bookings`            | `user.rbac.bookings.read`                                             |
| `booking.record.update`                             | `bookings`            | `user.rbac.bookings.actions.update`                                   |
| `booking.record.cancel`                             | `bookings`            | `user.rbac.bookings.actions.cancel`                                   |
| `booking.room.assign`                               | `bookings`            | `user.rbac.bookings.actions.assign_room`                              |
| `booking.stay.checkin`                              | `bookings`            | `user.rbac.bookings.actions.checkin`                                  |
| `booking.stay.checkout`                             | `bookings`            | `user.rbac.bookings.actions.checkout`                                 |
| `booking.guest.communicate`                         | `bookings`            | `user.rbac.bookings.actions.communicate`                              |
| `booking.override.supervise`                        | `bookings`            | `user.rbac.bookings.actions.override_conflicts`, `user.rbac.bookings.actions.force_checkin`, `user.rbac.bookings.actions.force_checkout`, `user.rbac.bookings.actions.resolve_overstay`, `user.rbac.bookings.actions.modify_locked`, `user.rbac.bookings.actions.extend` |
| `booking.config.manage`                             | `bookings`            | `user.rbac.bookings.actions.manage_rules`                             |
| `chat.module.view`                                  | `chat`                | `user.rbac.chat.visible`                                              |
| `chat.conversation.read`                            | `chat`                | `user.rbac.chat.read` and `user.rbac.chat.actions.conversation_read`  |
| `chat.message.send`                                 | `chat`                | `user.rbac.chat.actions.message_send`                                 |
| `chat.message.moderate`                             | `chat`                | `user.rbac.chat.actions.message_moderate`                             |
| `chat.attachment.upload`                            | `chat`                | `user.rbac.chat.actions.attachment_upload`                            |
| `chat.attachment.delete`                            | `chat`                | `user.rbac.chat.actions.attachment_delete`                            |
| `chat.conversation.assign`                          | `chat`                | `user.rbac.chat.actions.conversation_assign`                          |
| `chat.guest.respond`                                | `chat`                | `user.rbac.chat.actions.guest_respond`                                |
| `guest.record.read`                                 | `guests`              | `user.rbac.guests.visible` and `user.rbac.guests.read`                |
| `guest.record.update`                               | `guests`              | `user.rbac.guests.actions.update`                                     |
| `hotel_info.module.view`                            | `hotel_info`          | `user.rbac.hotel_info.visible`                                        |
| `hotel_info.entry.read`                             | `hotel_info`          | `user.rbac.hotel_info.read` and `user.rbac.hotel_info.actions.entry_read` |
| `hotel_info.entry.create`                           | `hotel_info`          | `user.rbac.hotel_info.actions.entry_create`                           |
| `hotel_info.entry.update`                           | `hotel_info`          | `user.rbac.hotel_info.actions.entry_update`                           |
| `hotel_info.entry.delete`                           | `hotel_info`          | `user.rbac.hotel_info.actions.entry_delete`                           |
| `hotel_info.category.read`                          | `hotel_info`          | `user.rbac.hotel_info.actions.category_read`                          |
| `hotel_info.category.manage`                        | `hotel_info`          | `user.rbac.hotel_info.actions.category_manage`                        |
| `hotel_info.qr.read`                                | `hotel_info`          | `user.rbac.hotel_info.actions.qr_read`                                |
| `hotel_info.qr.generate`                            | `hotel_info`          | `user.rbac.hotel_info.actions.qr_generate`                            |
| `housekeeping.module.view`                          | `housekeeping`        | `user.rbac.housekeeping.visible`                                      |
| `housekeeping.task.read`                            | `housekeeping`        | `user.rbac.housekeeping.read`                                         |
| `housekeeping.dashboard.read`                       | `housekeeping`        | `user.rbac.housekeeping.actions.dashboard_read`                       |
| `housekeeping.task.create`                          | `housekeeping`        | `user.rbac.housekeeping.actions.task_create`                          |
| `housekeeping.task.update`                          | `housekeeping`        | `user.rbac.housekeeping.actions.task_update`                          |
| `housekeeping.task.delete`                          | `housekeeping`        | `user.rbac.housekeeping.actions.task_delete`                          |
| `housekeeping.task.assign`                          | `housekeeping`        | `user.rbac.housekeeping.actions.task_assign`                          |
| `housekeeping.task.execute`                         | `housekeeping`        | `user.rbac.housekeeping.actions.task_execute`                         |
| `housekeeping.task.cancel`                          | `housekeeping`        | `user.rbac.housekeeping.actions.task_cancel`                          |
| `housekeeping.room_status.transition`               | `housekeeping`        | `user.rbac.housekeeping.actions.status_transition`                    |
| `housekeeping.room_status.front_desk`               | `housekeeping`        | `user.rbac.housekeeping.actions.status_front_desk`                    |
| `housekeeping.room_status.override`                 | `housekeeping`        | `user.rbac.housekeeping.actions.status_override`                      |
| `housekeeping.room_status.history.read`             | `housekeeping`        | `user.rbac.housekeeping.actions.status_history_read`                  |
| `maintenance.module.view`                           | `maintenance`         | `user.rbac.maintenance.visible`                                       |
| `maintenance.request.read`                          | `maintenance`         | `user.rbac.maintenance.read`                                          |
| `maintenance.request.create`                        | `maintenance`         | `user.rbac.maintenance.actions.request_create`                        |
| `maintenance.request.accept`                        | `maintenance`         | `user.rbac.maintenance.actions.request_accept`                        |
| `maintenance.request.resolve`                       | `maintenance`         | `user.rbac.maintenance.actions.request_resolve`                       |
| `maintenance.request.update`                        | `maintenance`         | `user.rbac.maintenance.actions.request_update`                        |
| `maintenance.request.reassign`                      | `maintenance`         | `user.rbac.maintenance.actions.request_reassign`                      |
| `maintenance.request.reopen`                        | `maintenance`         | `user.rbac.maintenance.actions.request_reopen`                        |
| `maintenance.request.close`                         | `maintenance`         | `user.rbac.maintenance.actions.request_close`                         |
| `maintenance.request.delete`                        | `maintenance`         | `user.rbac.maintenance.actions.request_delete`                        |
| `maintenance.comment.create`                        | `maintenance`         | `user.rbac.maintenance.actions.comment_create`                        |
| `maintenance.comment.moderate`                      | `maintenance`         | `user.rbac.maintenance.actions.comment_moderate`                      |
| `maintenance.photo.upload`                          | `maintenance`         | `user.rbac.maintenance.actions.photo_upload`                          |
| `maintenance.photo.delete`                          | `maintenance`         | `user.rbac.maintenance.actions.photo_delete`                          |
| `restaurant_booking.module.view`                    | `restaurant_bookings` | `user.rbac.restaurant_bookings.visible`                               |
| `restaurant_booking.record.read`                    | `restaurant_bookings` | `user.rbac.restaurant_bookings.read` and `user.rbac.restaurant_bookings.actions.record_read` |
| `restaurant_booking.restaurant.read`                | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.restaurant_read`               |
| `restaurant_booking.restaurant.create`              | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.restaurant_create`             |
| `restaurant_booking.restaurant.update`              | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.restaurant_update`             |
| `restaurant_booking.restaurant.delete`              | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.restaurant_delete`             |
| `restaurant_booking.category.read`                  | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.category_read`                 |
| `restaurant_booking.category.manage`                | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.category_manage`               |
| `restaurant_booking.record.create`                  | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.record_create`                 |
| `restaurant_booking.record.update`                  | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.record_update`                 |
| `restaurant_booking.record.delete`                  | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.record_delete`                 |
| `restaurant_booking.record.mark_seen`               | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.record_mark_seen`              |
| `restaurant_booking.table.read`                     | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.table_read`                    |
| `restaurant_booking.table.manage`                   | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.table_manage`                  |
| `restaurant_booking.blueprint.read`                 | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.blueprint_read`                |
| `restaurant_booking.blueprint.manage`               | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.blueprint_manage`              |
| `restaurant_booking.assignment.assign`              | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.assignment_assign`             |
| `restaurant_booking.assignment.unseat`              | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.assignment_unseat`             |
| `room_service.module.view`                          | `room_services`       | `user.rbac.room_services.visible`                                     |
| `room_service.order.read`                           | `room_services`       | `user.rbac.room_services.read` and `user.rbac.room_services.actions.order_read` |
| `room_service.menu.read`                            | `room_services`       | `user.rbac.room_services.actions.menu_read`                           |
| `room_service.menu.item.create`                     | `room_services`       | `user.rbac.room_services.actions.menu_item_create`                    |
| `room_service.menu.item.update`                     | `room_services`       | `user.rbac.room_services.actions.menu_item_update`                    |
| `room_service.menu.item.delete`                     | `room_services`       | `user.rbac.room_services.actions.menu_item_delete`                    |
| `room_service.menu.item.image_manage`               | `room_services`       | `user.rbac.room_services.actions.menu_item_image_manage`              |
| `room_service.order.create`                         | `room_services`       | `user.rbac.room_services.actions.order_create`                        |
| `room_service.order.update`                         | `room_services`       | `user.rbac.room_services.actions.order_update`                        |
| `room_service.order.delete`                         | `room_services`       | `user.rbac.room_services.actions.order_delete`                        |
| `room_service.order.accept`                         | `room_services`       | `user.rbac.room_services.actions.order_accept`                        |
| `room_service.order.complete`                       | `room_services`       | `user.rbac.room_services.actions.order_complete`                      |
| `room_service.breakfast_order.read`                 | `room_services`       | `user.rbac.room_services.actions.breakfast_order_read`                |
| `room_service.breakfast_order.create`               | `room_services`       | `user.rbac.room_services.actions.breakfast_order_create`              |
| `room_service.breakfast_order.update`               | `room_services`       | `user.rbac.room_services.actions.breakfast_order_update`              |
| `room_service.breakfast_order.delete`               | `room_services`       | `user.rbac.room_services.actions.breakfast_order_delete`              |
| `room_service.breakfast_order.accept`               | `room_services`       | `user.rbac.room_services.actions.breakfast_order_accept`              |
| `room_service.breakfast_order.complete`             | `room_services`       | `user.rbac.room_services.actions.breakfast_order_complete`            |
| `room.module.view`                                  | `rooms`               | `user.rbac.rooms.visible`                                             |
| `room.inventory.read`                               | `rooms`               | `user.rbac.rooms.read`                                                |
| `room.inventory.create`                             | `rooms`               | `user.rbac.rooms.actions.inventory_create`                            |
| `room.inventory.update`                             | `rooms`               | `user.rbac.rooms.actions.inventory_update`                            |
| `room.inventory.delete`                             | `rooms`               | `user.rbac.rooms.actions.inventory_delete`                            |
| `room.type.manage`                                  | `rooms`               | `user.rbac.rooms.actions.type_manage`                                 |
| `room.media.manage`                                 | `rooms`               | `user.rbac.rooms.actions.media_manage`                                |
| `room.out_of_order.set`                             | `rooms`               | `user.rbac.rooms.actions.out_of_order_set`                            |
| `room.checkout.destructive`                         | `rooms`               | `user.rbac.rooms.actions.checkout_destructive`                        |
| `room.status.transition`                            | `rooms`               | `user.rbac.rooms.actions.status_transition`                           |
| `room.maintenance.flag`                             | `rooms`               | `user.rbac.rooms.actions.maintenance_flag`                            |
| `room.inspection.perform`                           | `rooms`               | `user.rbac.rooms.actions.inspect`                                     |
| `room.maintenance.clear`                            | `rooms`               | `user.rbac.rooms.actions.maintenance_clear`                           |
| `room.checkout.bulk`                                | `rooms`               | `user.rbac.rooms.actions.checkout_bulk`                               |
| `staff_chat.module.view`                            | `staff_chat`          | `user.rbac.staff_chat.visible`                                        |
| `staff_chat.conversation.read`                      | `staff_chat`          | `user.rbac.staff_chat.read` and `user.rbac.staff_chat.actions.conversation_read` |
| `staff_chat.conversation.create`                    | `staff_chat`          | `user.rbac.staff_chat.actions.conversation_create`                    |
| `staff_chat.conversation.delete`                    | `staff_chat`          | `user.rbac.staff_chat.actions.conversation_delete`                    |
| `staff_chat.message.send`                           | `staff_chat`          | `user.rbac.staff_chat.actions.message_send`                           |
| `staff_chat.conversation.moderate`                  | `staff_chat`          | `user.rbac.staff_chat.actions.message_moderate`                       |
| `staff_chat.attachment.upload`                      | `staff_chat`          | `user.rbac.staff_chat.actions.attachment_upload`                      |
| `staff_chat.attachment.delete`                      | `staff_chat`          | `user.rbac.staff_chat.actions.attachment_delete`                      |
| `staff_chat.reaction.manage`                        | `staff_chat`          | `user.rbac.staff_chat.actions.reaction_manage`                        |
| `staff_management.module.view`                      | `staff_management`    | `user.rbac.staff_management.visible`                                  |
| `staff_management.staff.read`                       | `staff_management`    | `user.rbac.staff_management.read` and `user.rbac.staff_management.actions.staff_read` |
| `staff_management.user.read`                        | `staff_management`    | `user.rbac.staff_management.actions.user_read`                        |
| `staff_management.pending_registration.read`        | `staff_management`    | `user.rbac.staff_management.actions.pending_registration_read`        |
| `staff_management.staff.create`                     | `staff_management`    | `user.rbac.staff_management.actions.staff_create`                     |
| `staff_management.staff.update_profile`             | `staff_management`    | `user.rbac.staff_management.actions.staff_update_profile`             |
| `staff_management.staff.deactivate`                 | `staff_management`    | `user.rbac.staff_management.actions.staff_deactivate`                 |
| `staff_management.staff.delete`                     | `staff_management`    | `user.rbac.staff_management.actions.staff_delete`                     |
| `staff_management.authority.view`                   | `staff_management`    | `user.rbac.staff_management.actions.authority_view`                   |
| `staff_management.authority.role.assign`            | `staff_management`    | `user.rbac.staff_management.actions.authority_role_assign`            |
| `staff_management.authority.department.assign`      | `staff_management`    | `user.rbac.staff_management.actions.authority_department_assign`      |
| `staff_management.authority.access_level.assign`    | `staff_management`    | `user.rbac.staff_management.actions.authority_access_level_assign`    |
| `staff_management.authority.nav.assign`             | `staff_management`    | `user.rbac.staff_management.actions.authority_nav_assign`             |
| `staff_management.authority.supervise`              | `staff_management`    | `user.rbac.staff_management.actions.authority_supervise`              |
| `staff_management.role.read`                        | `staff_management`    | `user.rbac.staff_management.actions.role_read`                        |
| `staff_management.role.manage`                      | `staff_management`    | `user.rbac.staff_management.actions.role_manage`                      |
| `staff_management.department.read`                  | `staff_management`    | `user.rbac.staff_management.actions.department_read`                  |
| `staff_management.department.manage`                | `staff_management`    | `user.rbac.staff_management.actions.department_manage`                |
| `staff_management.registration_package.read`        | `staff_management`    | `user.rbac.staff_management.actions.registration_package_read`        |
| `staff_management.registration_package.create`      | `staff_management`    | `user.rbac.staff_management.actions.registration_package_create`      |
| `staff_management.registration_package.email`       | `staff_management`    | `user.rbac.staff_management.actions.registration_package_email`       |
| `staff_management.registration_package.print`       | `staff_management`    | `user.rbac.staff_management.actions.registration_package_print`       |

**Capabilities present in `CANONICAL_CAPABILITIES` but NOT mapped into any `user.rbac.*` action key** (these are routing / eligibility / non-policy capabilities — not consumable by frontend `user.rbac`):

- `chat.guest.respond` — IS mapped to `user.rbac.chat.actions.guest_respond` (notification routing eligibility, surfaced).
- `room_service.order.fulfill_porter` — NOT in `MODULE_POLICY`. Notification routing only. Frontend MUST NOT gate on this.
- `room_service.order.fulfill_kitchen` — NOT in `MODULE_POLICY`. Notification routing only. Frontend MUST NOT gate on this.
- `room.type.read`, `room.media.read`, `room.status.read` — present in `CANONICAL_CAPABILITIES` and in role/tier presets, but NOT mapped to any `user.rbac.rooms.actions.*` key. Frontend MUST treat the rooms read surface as gated by `user.rbac.rooms.read` (which is `room.inventory.read`); no separate boolean is exposed.

---

## 5. Nav slugs

`CANONICAL_NAV_SLUGS` from [staff/nav_catalog.py](staff/nav_catalog.py). The runtime list seen by the frontend lives at `user.allowed_navs` (computed by `resolve_effective_access`).

| Nav slug              | Module key (in `user.rbac`) | Frontend use                                                                |
| --------------------- | --------------------------- | --------------------------------------------------------------------------- |
| `home`                | *(no module)*               | Show the Home nav entry only. No `user.rbac.home`.                          |
| `chat`                | `chat`                      | Show the guest-chat nav entry. Page/action authority lives in `user.rbac.chat`. |
| `rooms`               | `rooms`                     | Show the rooms nav entry.                                                   |
| `room_bookings`       | `bookings`                  | Show the room-bookings nav entry. Authority is under `user.rbac.bookings`.  |
| `restaurant_bookings` | `restaurant_bookings`       | Show the restaurant-bookings nav entry.                                     |
| `housekeeping`        | `housekeeping`              | Show the housekeeping nav entry.                                            |
| `maintenance`         | `maintenance`               | Show the maintenance nav entry.                                             |
| `attendance`          | `attendance`                | Show the attendance nav entry.                                              |
| `staff_management`    | `staff_management`          | Show the staff management nav entry.                                        |
| `room_services`       | `room_services`             | Show the room services nav entry.                                           |
| `hotel_info`          | `hotel_info`                | Show the hotel info nav entry.                                              |
| `admin_settings`      | *(no module)*               | Show the admin settings nav entry. No `user.rbac.admin_settings`. Action authority on this surface is tier-gated server-side; frontend MUST rely on backend `403` for any action there. |

**Nav contract:**

- Nav is **visibility only**. A slug in `user.allowed_navs` permits the entry to appear in the menu and the route to render.
- Nav is **NEVER action authority**. Buttons, mutations, and writes within a page MUST be gated on `user.rbac.<module>.actions.<action>`.
- For modules without a nav slug (`guests`, `staff_chat`), use `user.rbac.<module>.visible` to decide whether to render their UI surface.

---

## 6. Roles / tiers / departments (CONTEXT ONLY)

Values present in backend code:

**Tiers** (`TIER_HIERARCHY` and `TIER_DEFAULT_NAVS` in [staff/permissions.py](staff/permissions.py), high → low):

- `super_user` (Django superuser)
- `super_staff_admin`
- `staff_admin`
- `regular_staff`

These appear on the auth payload as `tier` and `access_level` (and `is_superuser`).

**Roles** — the backend exposes `role_slug` on the auth payload; concrete role slugs are stored as `Role` rows per hotel and used as keys in `ROLE_PRESET_CAPABILITIES`. The set is data-driven; the frontend MUST NOT enumerate them.

**Departments** — same shape: `department_slug` on the auth payload; data-driven keys in `DEPARTMENT_PRESET_CAPABILITIES`.

> **Frontend MUST NOT gate any UI on `role`, `role_slug`, `access_level`, `tier`, or `department` for action buttons, mutations, deletes, status changes, exports, admin tabs, or privileged reads. They are backend context / preset-source fields only.**

The only frontend-visible derivative that survives the contract is the booleans inside `user.rbac.*` (which the backend already computed from those preset sources).

---

## 7. Frontend usage rules

1. Use `user.rbac.<module>.visible` for navigation entries, page rendering, and module-level visibility.
2. Use `user.rbac.<module>.read` to gate read surfaces (lists, detail views, dashboards) when present.
3. Use `user.rbac.<module>.actions.<action>` for **every** button, mutation, delete, status change, export, admin tab, and privileged read.
4. For nav slugs without a module (`home`, `admin_settings`), use `user.allowed_navs.includes('<slug>')` for the nav entry only. The backend remains the final authority for any action on those surfaces (`403` from the endpoint is the deny signal).
5. Missing module → deny.
6. Missing action → deny.
7. `false` from the backend → deny. Never relax this client-side.
8. Backend `403` is final authority. Even if `user.rbac.<module>.actions.<action> === true`, a `403` MUST disable the action.

**Frontend MUST NOT use:**

- `role`
- `role_slug`
- `access_level`
- `tier`
- `department`
- `isAdmin`
- `isStaffAdmin`
- `isSuperStaffAdmin`
- `canAccess([...roles])`
- `hasNavAccess(...)` for actions (nav is visibility-only)

These checks are explicitly forbidden by the backend contract (`HasNavPermission` is documented in [staff/permissions.py](staff/permissions.py) as "module VISIBILITY only — does NOT grant mutation authority"; capability classes are the only valid action gate). The frontend mirror of that rule is: only `user.rbac.<module>.actions.<action>` decides action visibility.

---

## 8. Frontend warning map

Comparison of common frontend areas against the canonical backend RBAC keys. "Frontend should use" is the **only** acceptable gate for that surface.

| Frontend area                                          | Backend module        | Frontend should use                                                                                                                                                               |
| ------------------------------------------------------ | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Room bookings nav entry                                | `bookings`            | `user.allowed_navs.includes('room_bookings')` AND `user.rbac.bookings.visible`                                                                                                    |
| Room bookings list / detail page                       | `bookings`            | `user.rbac.bookings.read`                                                                                                                                                         |
| Room booking edit / mark-seen / confirm form           | `bookings`            | `user.rbac.bookings.actions.update`                                                                                                                                               |
| Room booking cancel button                             | `bookings`            | `user.rbac.bookings.actions.cancel`                                                                                                                                               |
| Room booking assign-room / move-room                   | `bookings`            | `user.rbac.bookings.actions.assign_room`                                                                                                                                          |
| Room booking check-in / check-out                      | `bookings`            | `user.rbac.bookings.actions.checkin` / `user.rbac.bookings.actions.checkout`                                                                                                      |
| Booking guest-comms (precheckin link, survey link)     | `bookings`            | `user.rbac.bookings.actions.communicate`                                                                                                                                          |
| Force checkin / checkout / overstay / locked / extend  | `bookings`            | `user.rbac.bookings.actions.force_checkin` / `force_checkout` / `resolve_overstay` / `modify_locked` / `extend` / `override_conflicts` (all backed by `booking.override.supervise`) |
| Booking rules / config admin                           | `bookings`            | `user.rbac.bookings.actions.manage_rules`                                                                                                                                         |
| Restaurant bookings nav                                | `restaurant_bookings` | `user.allowed_navs.includes('restaurant_bookings')` AND `user.rbac.restaurant_bookings.visible`                                                                                   |
| Restaurant bookings list / detail                      | `restaurant_bookings` | `user.rbac.restaurant_bookings.read`                                                                                                                                              |
| Restaurant booking create / edit / delete / mark-seen  | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.record_create` / `record_update` / `record_delete` / `record_mark_seen`                                                                    |
| Restaurant CRUD (catalog management)                   | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.restaurant_create` / `restaurant_update` / `restaurant_delete`                                                                             |
| Booking categories management                          | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.category_manage`                                                                                                                           |
| Dining table management                                | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.table_manage`                                                                                                                              |
| Restaurant blueprint editor                            | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.blueprint_manage`                                                                                                                          |
| Seat / unseat booking on table                         | `restaurant_bookings` | `user.rbac.restaurant_bookings.actions.assignment_assign` / `assignment_unseat`                                                                                                   |
| Room services nav                                      | `room_services`       | `user.allowed_navs.includes('room_services')` AND `user.rbac.room_services.visible`                                                                                               |
| Room service orders list                               | `room_services`       | `user.rbac.room_services.read`                                                                                                                                                    |
| Accept / complete room service order                   | `room_services`       | `user.rbac.room_services.actions.order_accept` / `order_complete`                                                                                                                 |
| Create / edit / delete room service order              | `room_services`       | `user.rbac.room_services.actions.order_create` / `order_update` / `order_delete`                                                                                                  |
| Breakfast order accept / complete / CRUD               | `room_services`       | `user.rbac.room_services.actions.breakfast_order_accept` / `breakfast_order_complete` / `breakfast_order_create` / `breakfast_order_update` / `breakfast_order_delete`            |
| Menu item CRUD / image manage                          | `room_services`       | `user.rbac.room_services.actions.menu_item_create` / `menu_item_update` / `menu_item_delete` / `menu_item_image_manage`                                                           |
| Rooms nav                                              | `rooms`               | `user.allowed_navs.includes('rooms')` AND `user.rbac.rooms.visible`                                                                                                               |
| Room inventory list                                    | `rooms`               | `user.rbac.rooms.read`                                                                                                                                                            |
| Room create / edit / delete                            | `rooms`               | `user.rbac.rooms.actions.inventory_create` / `inventory_update` / `inventory_delete`                                                                                              |
| Room type management                                   | `rooms`               | `user.rbac.rooms.actions.type_manage`                                                                                                                                             |
| Room media (gallery) management                        | `rooms`               | `user.rbac.rooms.actions.media_manage`                                                                                                                                            |
| Out-of-order toggle                                    | `rooms`               | `user.rbac.rooms.actions.out_of_order_set`                                                                                                                                        |
| Bulk checkout (non-destructive)                        | `rooms`               | `user.rbac.rooms.actions.checkout_bulk`                                                                                                                                           |
| Bulk destructive checkout                              | `rooms`               | `user.rbac.rooms.actions.checkout_destructive`                                                                                                                                    |
| Turnover: start cleaning / mark cleaned                | `rooms`               | `user.rbac.rooms.actions.status_transition`                                                                                                                                       |
| Inspection pass / fail                                 | `rooms`               | `user.rbac.rooms.actions.inspect`                                                                                                                                                 |
| Flag / clear maintenance on a room                     | `rooms`               | `user.rbac.rooms.actions.maintenance_flag` / `maintenance_clear`                                                                                                                  |
| Housekeeping nav                                       | `housekeeping`        | `user.allowed_navs.includes('housekeeping')` AND `user.rbac.housekeeping.visible`                                                                                                 |
| Housekeeping dashboard                                 | `housekeeping`        | `user.rbac.housekeeping.actions.dashboard_read`                                                                                                                                   |
| Housekeeping task list                                 | `housekeeping`        | `user.rbac.housekeeping.read`                                                                                                                                                     |
| Create / edit / delete / cancel housekeeping task      | `housekeeping`        | `user.rbac.housekeeping.actions.task_create` / `task_update` / `task_delete` / `task_cancel`                                                                                      |
| Assign housekeeping task                               | `housekeeping`        | `user.rbac.housekeeping.actions.task_assign`                                                                                                                                      |
| Start / complete own task                              | `housekeeping`        | `user.rbac.housekeeping.actions.task_execute` (self-ownership enforced server-side)                                                                                               |
| Standard room status transition                        | `housekeeping`        | `user.rbac.housekeeping.actions.status_transition`                                                                                                                                |
| Front-desk room status changes                         | `housekeeping`        | `user.rbac.housekeeping.actions.status_front_desk`                                                                                                                                |
| Manager room status override                           | `housekeeping`        | `user.rbac.housekeeping.actions.status_override`                                                                                                                                  |
| Room status history view                               | `housekeeping`        | `user.rbac.housekeeping.actions.status_history_read`                                                                                                                              |
| Maintenance nav                                        | `maintenance`         | `user.allowed_navs.includes('maintenance')` AND `user.rbac.maintenance.visible`                                                                                                   |
| Maintenance request list / detail                      | `maintenance`         | `user.rbac.maintenance.read`                                                                                                                                                      |
| File new maintenance request                           | `maintenance`         | `user.rbac.maintenance.actions.request_create`                                                                                                                                    |
| Accept / resolve / reopen / close / delete request     | `maintenance`         | `user.rbac.maintenance.actions.request_accept` / `request_resolve` / `request_reopen` / `request_close` / `request_delete`                                                        |
| Edit / reassign request                                | `maintenance`         | `user.rbac.maintenance.actions.request_update` / `request_reassign`                                                                                                               |
| Comment create / moderate                              | `maintenance`         | `user.rbac.maintenance.actions.comment_create` / `comment_moderate`                                                                                                               |
| Photo upload / delete                                  | `maintenance`         | `user.rbac.maintenance.actions.photo_upload` / `photo_delete`                                                                                                                     |
| Staff management nav                                   | `staff_management`    | `user.allowed_navs.includes('staff_management')` AND `user.rbac.staff_management.visible`                                                                                         |
| Staff list                                             | `staff_management`    | `user.rbac.staff_management.read`                                                                                                                                                 |
| User list (cross-hotel registrations)                  | `staff_management`    | `user.rbac.staff_management.actions.user_read`                                                                                                                                    |
| Pending staff registrations                            | `staff_management`    | `user.rbac.staff_management.actions.pending_registration_read`                                                                                                                    |
| Create staff / update profile / deactivate / delete    | `staff_management`    | `user.rbac.staff_management.actions.staff_create` / `staff_update_profile` / `staff_deactivate` / `staff_delete`                                                                  |
| View canonical authority for a staff                   | `staff_management`    | `user.rbac.staff_management.actions.authority_view`                                                                                                                               |
| Assign role / department / access_level / nav          | `staff_management`    | `user.rbac.staff_management.actions.authority_role_assign` / `authority_department_assign` / `authority_access_level_assign` / `authority_nav_assign`                             |
| Lift anti-escalation ceilings (manager surface)        | `staff_management`    | `user.rbac.staff_management.actions.authority_supervise`                                                                                                                          |
| Role list / manage                                     | `staff_management`    | `user.rbac.staff_management.actions.role_read` / `role_manage`                                                                                                                    |
| Department list / manage                               | `staff_management`    | `user.rbac.staff_management.actions.department_read` / `department_manage`                                                                                                        |
| Registration package list / mint / email / print       | `staff_management`    | `user.rbac.staff_management.actions.registration_package_read` / `registration_package_create` / `registration_package_email` / `registration_package_print`                      |
| Attendance nav                                         | `attendance`          | `user.allowed_navs.includes('attendance')` AND `user.rbac.attendance.visible`                                                                                                     |
| Self clock in / out                                    | `attendance`          | `user.rbac.attendance.actions.clock_in_out`                                                                                                                                       |
| Self break start / end                                 | `attendance`          | `user.rbac.attendance.actions.break_toggle`                                                                                                                                       |
| Self log / roster / face-register-self                 | `attendance`          | `user.rbac.attendance.actions.log_read_self` / `roster_read_self` / `face_register_self`                                                                                          |
| Hotel-wide log read / create / update / delete         | `attendance`          | `user.rbac.attendance.actions.log_read_all` / `log_create` / `log_update` / `log_delete`                                                                                          |
| Approve / reject / relink unrostered logs              | `attendance`          | `user.rbac.attendance.actions.log_approve` / `log_reject` / `log_relink`                                                                                                          |
| Analytics dashboards                                   | `attendance`          | `user.rbac.attendance.actions.analytics_read`                                                                                                                                     |
| Period CRUD / finalize / unfinalize / force            | `attendance`          | `user.rbac.attendance.actions.period_read` / `period_create` / `period_update` / `period_delete` / `period_finalize` / `period_unfinalize` / `period_force_finalize`              |
| Shift CRUD / bulk / copy / export PDF                  | `attendance`          | `user.rbac.attendance.actions.shift_read` / `shift_create` / `shift_update` / `shift_delete` / `shift_bulk_write` / `shift_copy` / `shift_export_pdf`                             |
| Shift location read / manage                           | `attendance`          | `user.rbac.attendance.actions.shift_location_read` / `shift_location_manage`                                                                                                      |
| Daily plan read / manage / entry manage                | `attendance`          | `user.rbac.attendance.actions.daily_plan_read` / `daily_plan_manage` / `daily_plan_entry_manage`                                                                                  |
| Face other / revoke / audit                            | `attendance`          | `user.rbac.attendance.actions.face_read` / `face_register_other` / `face_revoke` / `face_audit_read`                                                                              |
| Guests page (in-house)                                 | `guests`              | `user.rbac.guests.visible` AND `user.rbac.guests.read` (no nav slug)                                                                                                              |
| Edit guest record                                      | `guests`              | `user.rbac.guests.actions.update`                                                                                                                                                 |
| Hotel Info nav                                         | `hotel_info`          | `user.allowed_navs.includes('hotel_info')` AND `user.rbac.hotel_info.visible`                                                                                                     |
| Hotel info entry CRUD                                  | `hotel_info`          | `user.rbac.hotel_info.actions.entry_read` / `entry_create` / `entry_update` / `entry_delete`                                                                                      |
| Category read / manage (platform-only)                 | `hotel_info`          | `user.rbac.hotel_info.actions.category_read` / `category_manage` (`category_manage` is normally only `true` for Django superuser)                                                 |
| QR read / generate                                     | `hotel_info`          | `user.rbac.hotel_info.actions.qr_read` / `qr_generate`                                                                                                                            |
| Guest chat nav                                         | `chat`                | `user.allowed_navs.includes('chat')` AND `user.rbac.chat.visible`                                                                                                                 |
| Guest chat conversation list / detail                  | `chat`                | `user.rbac.chat.read` (== `user.rbac.chat.actions.conversation_read`)                                                                                                             |
| Send guest chat message                                | `chat`                | `user.rbac.chat.actions.message_send`                                                                                                                                             |
| Moderate (hard-delete others') guest chat              | `chat`                | `user.rbac.chat.actions.message_moderate`                                                                                                                                         |
| Upload / delete (own) guest chat attachment            | `chat`                | `user.rbac.chat.actions.attachment_upload` / `attachment_delete`                                                                                                                  |
| Assign / hand off guest chat conversation              | `chat`                | `user.rbac.chat.actions.conversation_assign`                                                                                                                                      |
| "Eligible for guest-chat routing" indicator            | `chat`                | `user.rbac.chat.actions.guest_respond`                                                                                                                                            |
| Staff chat surface (no nav)                            | `staff_chat`          | `user.rbac.staff_chat.visible` AND `user.rbac.staff_chat.read`                                                                                                                    |
| Create / delete staff chat conversation                | `staff_chat`          | `user.rbac.staff_chat.actions.conversation_create` / `conversation_delete`                                                                                                        |
| Send staff chat message                                | `staff_chat`          | `user.rbac.staff_chat.actions.message_send`                                                                                                                                       |
| Moderate staff chat (delete others' messages/attachments) | `staff_chat`        | `user.rbac.staff_chat.actions.message_moderate`                                                                                                                                   |
| Staff chat attachment upload / delete (own)            | `staff_chat`          | `user.rbac.staff_chat.actions.attachment_upload` / `attachment_delete`                                                                                                            |
| React to staff chat message                            | `staff_chat`          | `user.rbac.staff_chat.actions.reaction_manage`                                                                                                                                    |
| Admin Settings nav (no module in `user.rbac`)          | *(no module)*         | `user.allowed_navs.includes('admin_settings')` for visibility ONLY. Action authority on this surface is tier-gated server-side; frontend MUST defer to backend `403`.             |
| Public page builder / hotel config CUD                 | *(no module)*         | No `user.rbac.*` key exists. Render the surface only if `user.allowed_navs.includes('admin_settings')` and rely on backend `403` for action denial.                               |
| Provisioning / hotel CRUD / cross-hotel super surfaces | *(no module)*         | No `user.rbac.*` key exists. Backend gates with `IsDjangoSuperUser` / `IsAdminTier` / `IsSuperStaffAdminOrAbove`. Frontend MUST defer to backend; `user.is_superuser` may be used purely for "show super-only nav entries" but never for action authority. |
| Home dashboard                                         | *(no module)*         | `user.allowed_navs.includes('home')`. No `user.rbac.home`.                                                                                                                        |

---

**End of contract.** Any UI gate that does not derive from `user.rbac.<module>.visible`, `user.rbac.<module>.read`, `user.rbac.<module>.actions.<action>`, or `user.allowed_navs.includes('<slug>')` (visibility only) is non-conformant.
