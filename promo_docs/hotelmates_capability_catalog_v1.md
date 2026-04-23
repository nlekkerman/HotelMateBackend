# HotelMates Canonical Capability Catalog — Phase 2 v1

**Status:** Phase 2 — canonical capability catalog
**Depends on:** `promo_docs/hotelmates_auth_contract_v1.md` (v1.1)
**Scope:** The authoritative list of every named capability in the HotelMates backend, grouped by domain.

---

## How to read this catalog

Every capability is defined with seven fields:

| Field | Meaning |
|---|---|
| **Slug** | Canonical name in `domain.resource.action` form. This is the wire value used in `allowed_capabilities`. |
| **Description** | Plain-English statement of what the capability lets a user do. |
| **Domain** | The module/bounded context this capability lives in. |
| **Classification** | `operational` \| `management` \| `config` (see below). |
| **Min tier** | Minimum tier eligible to be *granted* this capability (`regular_staff` / `staff_admin` / `super_staff_admin` / `super_user`). Lower-tier accounts cannot hold this capability even by mistake. |
| **Suggested departments** | Which canonical departments typically get this capability by preset. `*` means all departments. |
| **Affects nav** | Whether possessing this capability should influence module visibility in `allowed_navs`. `yes` = a user who holds this capability should see the module; `no` = capability is action-only, nav is decided by other rules or by already-visible module. |

### Classification definitions

- **operational** — Day-to-day work. Creating orders, updating task status, taking payments at the desk. No minimum tier elevation beyond `regular_staff`.
- **management** — Supervision and oversight. Reassigning work, approving, refunding, viewing department-wide reports, managing staff shifts. Typically requires `staff_admin` or above.
- **config** — System/hotel configuration. Managing menus, room inventory, policies, integrations, hotel-wide settings. Typically requires `super_staff_admin` or above.

### Tier / classification invariants

- `operational` ⇒ min tier is usually `regular_staff`.
- `management` ⇒ min tier is usually `staff_admin`.
- `config` ⇒ min tier is usually `super_staff_admin`.
- Anything cross-hotel or platform-administrative ⇒ `super_user`.

These are invariants; individual capabilities may tighten them, never loosen them.

### Naming rules (from contract v1.1 §5)

Three segments, lowercase, `snake_case`, dots between: `domain.resource.action`. Actions are verbs.

---

## Domain index

1. [`rooms`](#1-rooms) — room inventory & status
2. [`bookings`](#2-bookings) — reservations and stay lifecycle
3. [`room_services`](#3-room_services) — in-room dining orders & menu
4. [`housekeeping`](#4-housekeeping) — cleaning tasks & room readiness
5. [`maintenance`](#5-maintenance) — maintenance work orders
6. [`issues`](#6-issues) — guest/staff issue tracking
7. [`guests`](#7-guests) — guest profiles & stay records
8. [`guest_chat`](#8-guest_chat) — guest ↔ staff messaging
9. [`staff_chat`](#9-staff_chat) — staff ↔ staff messaging
10. [`staff`](#10-staff) — staff accounts, roles, capabilities
11. [`attendance`](#11-attendance) — clock-in/out, shifts, rosters
12. [`stock_tracker`](#12-stock_tracker) — inventory & stock
13. [`entertainment`](#13-entertainment) — activities & programming
14. [`posts`](#14-posts) — announcements & hotel feed
15. [`notifications`](#15-notifications) — push/email notification wiring
16. [`hotel_info`](#16-hotel_info) — public-facing hotel content
17. [`hotel`](#17-hotel) — hotel-level configuration & policies
18. [`reports`](#18-reports) — cross-module reporting
19. [`platform`](#19-platform) — cross-hotel / super_user surface

---

## 1. `rooms`

Room inventory, statuses, and room-level metadata.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `rooms.room.read` | View room list and individual room details. | operational | regular_staff | front_office, housekeeping, maintenance, management | yes |
| `rooms.room.update_status` | Change a room's operational status (dirty, clean, inspected, out-of-order). | operational | regular_staff | front_office, housekeeping | no |
| `rooms.room.assign_guest` | Assign a guest/booking to a specific room. | operational | regular_staff | front_office | no |
| `rooms.room.release` | Release a room from its current assignment. | operational | regular_staff | front_office | no |
| `rooms.room.mark_out_of_order` | Take a room out of inventory for a period. | management | staff_admin | front_office, maintenance, management | no |
| `rooms.room.create` | Add a new room to the inventory. | config | super_staff_admin | administration, management | no |
| `rooms.room.update` | Edit room metadata (number, type, floor, features). | config | super_staff_admin | administration, management | no |
| `rooms.room.delete` | Remove a room from inventory. | config | super_staff_admin | administration, management | no |
| `rooms.room_type.manage` | Create/edit/delete room type definitions. | config | super_staff_admin | administration, management | no |

## 2. `bookings`

Reservations, check-in/out, stay lifecycle. Includes `bookings/` and `room_bookings/`.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `bookings.booking.read` | View bookings and reservation details. | operational | regular_staff | front_office, guest_relations, management | yes |
| `bookings.booking.create` | Create a new booking / reservation. | operational | regular_staff | front_office | no |
| `bookings.booking.update` | Edit booking details (dates, room, guest info). | operational | regular_staff | front_office | no |
| `bookings.booking.cancel` | Cancel a booking. | operational | regular_staff | front_office | no |
| `bookings.booking.check_in` | Perform guest check-in. | operational | regular_staff | front_office | no |
| `bookings.booking.check_out` | Perform guest check-out. | operational | regular_staff | front_office | no |
| `bookings.booking.override_dates` | Override booking dates outside standard rules. | management | staff_admin | front_office, management | no |
| `bookings.booking.waive_fees` | Waive cancellation/no-show fees. | management | staff_admin | front_office, management | no |
| `bookings.payment.read` | View booking payment history. | operational | regular_staff | front_office, administration, management | no |
| `bookings.payment.capture` | Capture a payment against a booking. | operational | regular_staff | front_office, administration | no |
| `bookings.payment.refund` | Issue a refund. | management | staff_admin | front_office, administration, management | no |
| `bookings.rate.manage` | Manage rate plans and pricing tables. | config | super_staff_admin | management, administration | no |
| `bookings.policy.manage` | Manage booking/cancellation policies. | config | super_staff_admin | management, administration | no |

## 3. `room_services`

In-room dining orders and menu management.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `room_services.order.read` | View room service orders. | operational | regular_staff | food_beverage, kitchen, front_office, management | yes |
| `room_services.order.create` | Take a new room service order. | operational | regular_staff | food_beverage, front_office | no |
| `room_services.order.update_status` | Advance order status (accepted, preparing, ready, delivered). | operational | regular_staff | food_beverage, kitchen | no |
| `room_services.order.cancel` | Cancel an in-flight order. | operational | regular_staff | food_beverage, kitchen | no |
| `room_services.order.reassign` | Reassign an order to another staff member. | management | staff_admin | food_beverage, kitchen, management | no |
| `room_services.order.comp` | Comp (no-charge) an order. | management | staff_admin | food_beverage, management | no |
| `room_services.menu.read` | View menus and availability. | operational | regular_staff | food_beverage, kitchen, front_office | no |
| `room_services.menu.create` | Add menu items. | config | super_staff_admin | food_beverage, management | no |
| `room_services.menu.update` | Edit menu items. | config | super_staff_admin | food_beverage, management | no |
| `room_services.menu.update_price` | Change menu item pricing. | config | super_staff_admin | food_beverage, management, administration | no |
| `room_services.menu.toggle_availability` | Mark items available/unavailable (e.g. 86'd). | management | staff_admin | food_beverage, kitchen | no |
| `room_services.menu.delete` | Delete menu items. | config | super_staff_admin | food_beverage, management | no |
| `room_services.settings.manage` | Manage room service hours, fees, delivery rules. | config | super_staff_admin | management, food_beverage | no |

## 4. `housekeeping`

Cleaning tasks, room readiness, housekeeping assignments.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `housekeeping.task.read` | View housekeeping tasks. | operational | regular_staff | housekeeping, front_office, management | yes |
| `housekeeping.task.create` | Create an ad-hoc housekeeping task. | operational | regular_staff | housekeeping, front_office | no |
| `housekeeping.task.update_status` | Update task status (started, in-progress, done). | operational | regular_staff | housekeeping | no |
| `housekeeping.task.assign` | Assign a task to a specific housekeeper. | management | staff_admin | housekeeping, management | no |
| `housekeeping.task.reassign` | Move a task from one staff member to another. | management | staff_admin | housekeeping, management | no |
| `housekeeping.task.delete` | Delete a housekeeping task. | management | staff_admin | housekeeping, management | no |
| `housekeeping.schedule.manage` | Manage housekeeping schedules and shift plans. | management | staff_admin | housekeeping, management | no |
| `housekeeping.checklist.manage` | Configure cleaning checklists/templates. | config | super_staff_admin | housekeeping, management | no |
| `housekeeping.settings.manage` | Configure housekeeping rules (turnover timing, priorities). | config | super_staff_admin | housekeeping, management | no |

## 5. `maintenance`

Maintenance work orders and preventive maintenance.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `maintenance.ticket.read` | View maintenance tickets. | operational | regular_staff | maintenance, housekeeping, front_office, management | yes |
| `maintenance.ticket.create` | Create a maintenance ticket. | operational | regular_staff | * | no |
| `maintenance.ticket.update_status` | Update ticket status (acknowledged, in-progress, resolved). | operational | regular_staff | maintenance | no |
| `maintenance.ticket.assign` | Assign a ticket to a maintenance staff member. | management | staff_admin | maintenance, management | no |
| `maintenance.ticket.reassign` | Reassign a ticket. | management | staff_admin | maintenance, management | no |
| `maintenance.ticket.close` | Close/resolve a ticket with resolution notes. | operational | regular_staff | maintenance | no |
| `maintenance.ticket.reopen` | Reopen a closed ticket. | management | staff_admin | maintenance, management | no |
| `maintenance.ticket.delete` | Delete a maintenance ticket. | management | staff_admin | maintenance, management | no |
| `maintenance.schedule.manage` | Manage preventive maintenance schedules. | management | staff_admin | maintenance, management | no |
| `maintenance.category.manage` | Manage ticket categories and priorities. | config | super_staff_admin | maintenance, management | no |

## 6. `issues`

Guest/staff issue reports (distinct from maintenance; used for complaints, incidents, general issues).

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `issues.issue.read` | View reported issues. | operational | regular_staff | guest_relations, front_office, management | yes |
| `issues.issue.create` | File a new issue on behalf of a guest or staff. | operational | regular_staff | * | no |
| `issues.issue.update` | Edit issue details. | operational | regular_staff | guest_relations, front_office | no |
| `issues.issue.assign` | Assign an issue to a handler. | management | staff_admin | guest_relations, management | no |
| `issues.issue.resolve` | Mark an issue resolved with resolution notes. | operational | regular_staff | guest_relations, front_office | no |
| `issues.issue.reopen` | Reopen a resolved issue. | management | staff_admin | guest_relations, management | no |
| `issues.issue.delete` | Delete an issue record. | management | staff_admin | guest_relations, management | no |
| `issues.category.manage` | Manage issue categories. | config | super_staff_admin | guest_relations, management | no |

## 7. `guests`

Guest profiles, stay history, loyalty.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `guests.guest.read` | View guest profiles. | operational | regular_staff | front_office, guest_relations, management | yes |
| `guests.guest.create` | Create a guest profile (walk-in / manual). | operational | regular_staff | front_office, guest_relations | no |
| `guests.guest.update` | Edit guest profile details. | operational | regular_staff | front_office, guest_relations | no |
| `guests.guest.merge` | Merge duplicate guest profiles. | management | staff_admin | front_office, guest_relations, management | no |
| `guests.guest.delete` | Delete a guest profile (GDPR / erasure request). | management | super_staff_admin | management, administration | no |
| `guests.note.read` | Read internal notes on a guest. | operational | regular_staff | front_office, guest_relations, management | no |
| `guests.note.create` | Add an internal note to a guest profile. | operational | regular_staff | front_office, guest_relations, management | no |
| `guests.note.delete` | Delete an internal note. | management | staff_admin | front_office, guest_relations, management | no |
| `guests.vip.manage` | Flag/unflag VIP status and manage VIP lists. | management | staff_admin | front_office, guest_relations, management | no |
| `guests.blacklist.manage` | Manage guest blacklist entries. | management | super_staff_admin | management, front_office | no |

## 8. `guest_chat`

Guest ↔ staff messaging threads.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `guest_chat.thread.read` | View guest chat threads. | operational | regular_staff | front_office, guest_relations, management | yes |
| `guest_chat.message.send` | Send a reply to a guest. | operational | regular_staff | front_office, guest_relations | no |
| `guest_chat.thread.assign` | Assign a thread to a specific staff member. | management | staff_admin | guest_relations, front_office, management | no |
| `guest_chat.thread.close` | Close / archive a guest chat thread. | operational | regular_staff | front_office, guest_relations | no |
| `guest_chat.message.delete` | Delete a message (moderation). | management | staff_admin | guest_relations, management | no |
| `guest_chat.settings.manage` | Configure chat greetings, routing, business hours. | config | super_staff_admin | management, guest_relations | no |

## 9. `staff_chat`

Internal staff-to-staff messaging.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `staff_chat.channel.read` | View staff channels/DMs available to this user. | operational | regular_staff | * | yes |
| `staff_chat.message.send` | Send staff chat messages. | operational | regular_staff | * | no |
| `staff_chat.channel.create` | Create a new staff channel. | management | staff_admin | * | no |
| `staff_chat.channel.manage_members` | Add/remove members from a channel. | management | staff_admin | * | no |
| `staff_chat.message.delete` | Delete staff chat messages (moderation). | management | staff_admin | management | no |
| `staff_chat.channel.delete` | Delete a staff channel. | management | super_staff_admin | management | no |

## 10. `staff`

Staff accounts, roles, tiers, capabilities, and the RBAC surface itself.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `staff.account.read` | View staff accounts within the same hotel. | operational | regular_staff | * | yes |
| `staff.account.read_sensitive` | View sensitive staff info (contact, documents, pay-related). | management | staff_admin | management, administration | no |
| `staff.account.create` | Create a new staff account. | management | super_staff_admin | management, administration | no |
| `staff.account.update` | Edit a staff account. | management | staff_admin | management, administration | no |
| `staff.account.deactivate` | Deactivate/suspend a staff account. | management | super_staff_admin | management, administration | no |
| `staff.account.delete` | Permanently delete a staff account. | config | super_staff_admin | management, administration | no |
| `staff.role.assign` | Assign a role to a staff member. | management | staff_admin | management, administration | no |
| `staff.role.manage` | Create/edit/delete role presets. | config | super_staff_admin | management, administration | no |
| `staff.capability.grant` | Grant a specific capability to a staff member. | config | super_staff_admin | management, administration | no |
| `staff.capability.revoke` | Revoke a specific capability from a staff member. | config | super_staff_admin | management, administration | no |
| `staff.tier.assign` | Change a staff member's tier. | config | super_staff_admin | management, administration | no |
| `staff.department.assign` | Change a staff member's department. | management | super_staff_admin | management, administration | no |
| `staff.invite.send` | Send an onboarding invitation. | management | staff_admin | management, administration | no |
| `staff.password.reset` | Trigger a password reset for a staff member. | management | staff_admin | management, administration | no |

## 11. `attendance`

Clock-in/out, shifts, rosters, analytics.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `attendance.self.clock` | Clock self in/out. | operational | regular_staff | * | yes |
| `attendance.self.read` | View own attendance history. | operational | regular_staff | * | no |
| `attendance.team.read` | View attendance records for own department. | operational | staff_admin | * | no |
| `attendance.hotel.read` | View attendance records across the hotel. | management | super_staff_admin | management, administration | no |
| `attendance.record.edit` | Edit / correct attendance records. | management | staff_admin | management, administration | no |
| `attendance.record.delete` | Delete attendance records. | management | super_staff_admin | management, administration | no |
| `attendance.shift.read` | View shift schedules. | operational | regular_staff | * | no |
| `attendance.shift.create` | Create shifts. | management | staff_admin | management, administration | no |
| `attendance.shift.update` | Edit shifts. | management | staff_admin | management, administration | no |
| `attendance.shift.delete` | Delete shifts. | management | staff_admin | management, administration | no |
| `attendance.roster.manage` | Manage rosters and shift patterns. | management | staff_admin | management, administration | no |
| `attendance.analytics.read` | View attendance analytics reports. | management | staff_admin | management, administration | no |
| `attendance.face.enroll` | Enroll a staff member for face-recognition clock-in. | config | super_staff_admin | management, administration | no |
| `attendance.settings.manage` | Configure attendance rules, grace periods, policies. | config | super_staff_admin | management, administration | no |

## 12. `stock_tracker`

Inventory, stock movements, stock take.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `stock_tracker.item.read` | View stock items and levels. | operational | regular_staff | food_beverage, kitchen, housekeeping, maintenance, administration, management | yes |
| `stock_tracker.movement.create` | Log stock consumption / receipt. | operational | regular_staff | food_beverage, kitchen, housekeeping, maintenance | no |
| `stock_tracker.movement.adjust` | Manually adjust stock counts (variance). | management | staff_admin | management, administration | no |
| `stock_tracker.item.create` | Add a new stock item. | config | super_staff_admin | management, administration | no |
| `stock_tracker.item.update` | Edit stock item metadata. | config | super_staff_admin | management, administration | no |
| `stock_tracker.item.delete` | Delete a stock item. | config | super_staff_admin | management, administration | no |
| `stock_tracker.supplier.manage` | Manage suppliers and purchase orders. | config | super_staff_admin | management, administration | no |
| `stock_tracker.stock_take.run` | Conduct a stock take / inventory count. | management | staff_admin | management, administration, food_beverage, kitchen | no |
| `stock_tracker.settings.manage` | Configure stock categories, units, thresholds. | config | super_staff_admin | management, administration | no |

## 13. `entertainment`

Activities, events, and programming schedules.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `entertainment.activity.read` | View scheduled activities/events. | operational | regular_staff | guest_relations, front_office, management | yes |
| `entertainment.booking.read` | View guest registrations for activities. | operational | regular_staff | guest_relations, front_office | no |
| `entertainment.booking.create` | Register a guest for an activity. | operational | regular_staff | guest_relations, front_office | no |
| `entertainment.booking.cancel` | Cancel a guest's activity registration. | operational | regular_staff | guest_relations, front_office | no |
| `entertainment.activity.create` | Schedule a new activity. | management | staff_admin | guest_relations, management | no |
| `entertainment.activity.update` | Edit a scheduled activity. | management | staff_admin | guest_relations, management | no |
| `entertainment.activity.delete` | Delete a scheduled activity. | management | staff_admin | guest_relations, management | no |
| `entertainment.program.manage` | Manage entertainment program templates/series. | config | super_staff_admin | management, guest_relations | no |

## 14. `posts`

Announcements / hotel feed.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `posts.post.read` | View published posts. | operational | regular_staff | * | yes |
| `posts.post.create` | Create a new post/announcement. | management | staff_admin | management, guest_relations, administration | no |
| `posts.post.update` | Edit an existing post. | management | staff_admin | management, guest_relations, administration | no |
| `posts.post.publish` | Publish/unpublish a post. | management | staff_admin | management, guest_relations | no |
| `posts.post.delete` | Delete a post. | management | super_staff_admin | management | no |
| `posts.category.manage` | Manage post categories. | config | super_staff_admin | management | no |

## 15. `notifications`

Notification rules, templates, delivery wiring.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `notifications.self.read` | Read notifications delivered to self. | operational | regular_staff | * | yes |
| `notifications.self.update_preferences` | Update own notification preferences. | operational | regular_staff | * | no |
| `notifications.broadcast.send` | Send a broadcast notification to staff or guests. | management | staff_admin | management, guest_relations | no |
| `notifications.template.manage` | Manage notification templates. | config | super_staff_admin | management, administration | no |
| `notifications.rule.manage` | Manage notification trigger rules. | config | super_staff_admin | management, administration | no |
| `notifications.channel.manage` | Configure delivery channels (push, email, SMS, providers). | config | super_staff_admin | administration, management | no |

## 16. `hotel_info`

Public-facing hotel content (directory, amenities, maps, guest-visible info).

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `hotel_info.content.read` | View hotel info content (staff view). | operational | regular_staff | * | yes |
| `hotel_info.content.update` | Edit hotel info content (amenity descriptions, directory entries). | management | staff_admin | management, guest_relations, administration | no |
| `hotel_info.content.publish` | Publish/unpublish hotel info content. | management | staff_admin | management, guest_relations | no |
| `hotel_info.content.delete` | Delete hotel info entries. | config | super_staff_admin | management, administration | no |
| `hotel_info.media.manage` | Upload and manage media assets (images, PDFs). | management | staff_admin | management, guest_relations, administration | no |

## 17. `hotel`

Hotel-level configuration, policies, branding.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `hotel.profile.read` | View hotel profile/branding/contact info. | operational | regular_staff | * | yes |
| `hotel.profile.update` | Edit hotel profile / branding. | config | super_staff_admin | management, administration | no |
| `hotel.policy.manage` | Manage hotel-level policies (cancellation, check-in rules, house rules). | config | super_staff_admin | management, administration | no |
| `hotel.hours.manage` | Manage operational hours per service. | config | super_staff_admin | management, administration | no |
| `hotel.integration.manage` | Manage third-party integrations (PMS, payment, channel manager). | config | super_staff_admin | administration, management | no |
| `hotel.billing.read` | View hotel subscription / billing info. | management | super_staff_admin | management, administration | no |
| `hotel.billing.manage` | Manage subscription / billing details. | config | super_staff_admin | management, administration | no |
| `hotel.audit_log.read` | View hotel-level audit log. | management | super_staff_admin | management, administration | no |

## 18. `reports`

Cross-module reporting & dashboards.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `reports.dashboard.read` | View the staff dashboard for own scope. | operational | regular_staff | * | yes |
| `reports.department.read` | View department-level reports. | management | staff_admin | * | no |
| `reports.hotel.read` | View hotel-wide reports. | management | super_staff_admin | management, administration | no |
| `reports.financial.read` | View financial reports (revenue, payments, refunds). | management | super_staff_admin | management, administration | no |
| `reports.export` | Export reports to CSV/PDF. | management | staff_admin | management, administration | no |

## 19. `platform`

Cross-hotel and platform-administrative capabilities. `super_user` only.

| Slug | Description | Class | Min tier | Departments | Nav |
|---|---|---|---|---|---|
| `platform.hotel.read` | View all hotels on the platform. | management | super_user | — | yes |
| `platform.hotel.create` | Provision a new hotel tenant. | config | super_user | — | no |
| `platform.hotel.update` | Edit a hotel tenant at platform level. | config | super_user | — | no |
| `platform.hotel.delete` | Delete/deprovision a hotel tenant. | config | super_user | — | no |
| `platform.staff.impersonate` | Impersonate a staff account for support purposes. | config | super_user | — | no |
| `platform.capability.catalog.manage` | Manage the canonical capability catalog itself. | config | super_user | — | no |
| `platform.audit_log.read` | View platform-wide audit logs across all hotels. | management | super_user | — | no |
| `platform.feature_flag.manage` | Manage feature flags per hotel or globally. | config | super_user | — | no |
| `platform.system.health.read` | View system health/metrics. | management | super_user | — | yes |

---

## Cross-cutting rules

1. **One primary capability per non-safe endpoint.** Every mutating endpoint picks exactly one slug from this catalog as its canonical primary capability. Additional tier/scope checks may layer on, but the slug in the catalog is the wire truth. (Contract v1.1 §5.)
2. **Nav visibility is a separate resolved surface.** The `Affects nav` column is an **input signal** to the nav resolver, not a direct mapping. The resolver combines tier, department, role, and capability signals to produce `allowed_navs`. (Contract v1.1 §9.)
3. **Hotel scope is implicit.** Every slug here implicitly means "within the user's hotel" unless it lives in the `platform` domain.
4. **Min tier is a grant-time invariant.** A capability cannot be granted to an account below its `Min tier`. Runtime checks still look at the resolved `allowed_capabilities` list — min tier is enforced at assignment and on preset resolution.
5. **Suggested departments are presets, not locks.** The department list drives default role presets; it does not prevent a management-tier user in another department from being granted the capability where sensible.
6. **Classification drives UX grouping.** `operational` capabilities cluster in day-to-day panels; `management` capabilities cluster in supervisory panels; `config` capabilities cluster in settings screens.
7. **Delete/grant/revoke capabilities require elevated tier.** No `*.delete` on shared data, no `staff.capability.grant`, and no `staff.capability.revoke` is ever operational-tier.
8. **New capabilities must be added to this catalog before being used in code.** Free-form capability strings in views are prohibited.

---

## Nav-input index (capabilities that feed `allowed_navs`)

These are the slugs marked `Affects nav: yes`. They are the signal set for the nav resolver — they do not individually guarantee nav visibility; the resolver combines them with tier/department rules.

| Module | Capability signal |
|---|---|
| Rooms | `rooms.room.read` |
| Bookings | `bookings.booking.read` |
| Room Service | `room_services.order.read` |
| Housekeeping | `housekeeping.task.read` |
| Maintenance | `maintenance.ticket.read` |
| Issues | `issues.issue.read` |
| Guests | `guests.guest.read` |
| Guest Chat | `guest_chat.thread.read` |
| Staff Chat | `staff_chat.channel.read` |
| Staff directory | `staff.account.read` |
| Attendance | `attendance.self.clock` |
| Stock | `stock_tracker.item.read` |
| Entertainment | `entertainment.activity.read` |
| Posts | `posts.post.read` |
| Notifications | `notifications.self.read` |
| Hotel Info | `hotel_info.content.read` |
| Hotel Settings | `hotel.profile.read` |
| Reports | `reports.dashboard.read` |
| Platform | `platform.hotel.read` / `platform.system.health.read` |

---

## Follow-up after this catalog

1. Encode this catalog as data (seed file / migration) keyed by slug.
2. Produce the **role preset bundles per department** (Phase 3): for each canonical department, list the default roles and which capabilities each role grants by default.
3. Produce the **tier baseline bundles**: the default capability set granted purely by tier (before role is applied).
4. Produce the **endpoint → primary capability map** so every backend view declares its primary slug.
5. Wire the effective-access resolver to emit `allowed_capabilities` and `allowed_navs` per the contract payload (v1.1 §10).

---

## Summary

This catalog is the single source of truth for every named capability in HotelMates. Every backend endpoint, every frontend guard, and every role preset derives from these slugs. Additions, renames, and deletions go through a catalog change, never through ad-hoc code.
