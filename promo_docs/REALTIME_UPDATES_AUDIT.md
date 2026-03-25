# HotelMate — Realtime Updates Audit

**Date:** 2026-03-25  
**Scope:** Full audit of every Pusher-based realtime event fired across the hotel-booking ecosystem  
**Transport:** Pusher (all environments). Private channels (`private-*`) require token auth.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Booking Lifecycle — Guest-Facing Events](#2-booking-lifecycle--guest-facing-events)
3. [Booking Lifecycle — Staff-Facing Events](#3-booking-lifecycle--staff-facing-events)
4. [Overstay & Extension Events](#4-overstay--extension-events)
5. [Room Occupancy & Status Events](#5-room-occupancy--status-events)
6. [Room Move Events](#6-room-move-events)
7. [Guest Chat Events](#7-guest-chat-events)
8. [Staff Chat Events](#8-staff-chat-events)
9. [Room Service & Menu Events](#9-room-service--menu-events)
10. [Attendance & Shift Events](#10-attendance--shift-events)
11. [Staff Management Events](#11-staff-management-events)
12. [Stock / Inventory Events](#12-stock--inventory-events)
13. [Self-Healing / Integrity Events](#13-self-healing--integrity-events)
14. [Channel Naming Convention Summary](#14-channel-naming-convention-summary)
15. [Audit Statistics](#15-audit-statistics)

---

## 1. Architecture Overview

| Component | Role |
|-----------|------|
| **Pusher client** | Initialised in `chat/utils.py` via `pusher.Pusher(...)` using Django settings |
| **NotificationManager** | Centralised facade in `notifications/notification_manager.py` — 32+ realtime methods |
| **Django Signals** | `post_save` / `post_delete` in `room_services/signals.py` auto-fire order events |
| **Direct triggers** | Some views still call `pusher_client.trigger()` directly (attendance, stock, older chat code) |
| **Pusher utility modules** | `notifications/pusher_utils.py`, `staff/pusher_utils.py`, `staff_chat/pusher_utils.py`, `stock_tracker/pusher_utils.py` |

---

## 2. Booking Lifecycle — Guest-Facing Events

Channel pattern: **`private-guest-booking.{booking_id}`**

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `booking_payment_required` | Payment required flagged | `booking_id`, `status`, `payment_required`, `reason`, `hotel_name`, `hotel_phone` |
| `booking_confirmed` | Booking confirmed by staff | `booking_id`, `status`, `confirmation_details` |
| `booking_cancelled` | Booking cancelled | `booking_id`, `status`, `cancellation_reason`, `cancelled_at` |
| `booking_checked_in` | Guest checked in | `booking_id`, `room_number`, `check_in_time` |
| `booking_checked_out` | Guest checked out | `booking_id`, `room_number`, `check_out_time` |
| `room_assigned` | Room assigned to booking | `booking_id`, `room_number`, `assignment_time` |

**Source files:** `bookings/views.py`, `notifications/notification_manager.py`

---

## 3. Booking Lifecycle — Staff-Facing Events

Channel pattern: **`{hotel_slug}.room-bookings`**

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `booking_created` | New booking created | `booking_id`, `guest_name`, `check_in`, `check_out` |
| `booking_updated` | Booking details changed | `booking_id`, `changes`, `updated_fields` |
| `booking_confirmed` | Booking confirmed | `booking_id`, `confirmation_details` |
| `booking_party_updated` | Party/companion guests changed | `booking_id`, `party_members`, `updated_guest_info` |
| `booking_cancelled` | Booking cancelled | `booking_id`, `cancellation_reason` |
| `booking_checked_in` | Guest checked in | `booking_id`, `room_number`, `guests` |
| `booking_checked_out` | Guest checked out | `booking_id`, `room_number` |

**Source files:** `bookings/views.py`, `hotel/staff_views.py`, `notifications/notification_manager.py`

---

## 4. Overstay & Extension Events

Channel pattern: **`{hotel_slug}-staff-overstays`** and **`{hotel_slug}-staff-bookings`**

| Event Name | Channel | Trigger Context | Data Payload |
|------------|---------|-----------------|--------------|
| `booking_overstay_flagged` | `{slug}-staff-overstays` | Guest exceeds checkout time | `booking_id`, `overstay_details`, `incident_id` |
| `booking_overstay_acknowledged` | `{slug}-staff-overstays` | Manager acknowledges the overstay | `booking_id`, `acknowledged_by`, `note` |
| `booking_overstay_extended` | `{slug}-staff-overstays` | Booking extended past original checkout | `booking_id`, `old_checkout`, `new_checkout`, `added_nights` |
| `booking_updated` | `{slug}-staff-bookings` | Generic update after extension | `booking_id`, `changes`, `new_checkout_date` |

**Source file:** `room_bookings/services/overstay.py`

---

## 5. Room Occupancy & Status Events

Channel pattern: **`{hotel_slug}.rooms`**

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `room_occupancy_updated` | Check-in, check-out, room move | `room_id`, `room_number`, `occupancy_status`, `booking_id` |
| `room_updated` | Any room property/status change | `room_id`, `room_number`, `status`, `changed_fields` |

**Source file:** `notifications/notification_manager.py`

---

## 6. Room Move Events

When a room move occurs, the following are triggered via `room_bookings/services/room_move.py`:

1. `realtime_booking_updated()` — booking record reflects new room
2. `realtime_room_occupancy_updated()` — **source** room marked vacant
3. `realtime_room_occupancy_updated()` — **destination** room marked occupied

---

## 7. Guest Chat Events

Channel pattern: **`private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}`**

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `realtime_event` | System message (staff joins chat) | `join_system_message`, `timestamp` |
| `realtime_event` | Guest sends a message | `message_id`, `content`, `sender` |
| `realtime_event` | Staff sends a message | `staff_message_data` |
| `realtime_event` | Message with file attachment | `message_with_attachment` |
| `chat_unread_updated` | Unread count changes | `unread_count` |
| `chat_unread_updated` | Unread cleared (= 0) | `unread_count` = 0 |
| `message_edited` | Message content edited | `message_id`, `edited_content`, `edited_at` |
| `message_deleted` | Message deleted (staff or guest) | `message_id`, `deleted_at`, `deleted_by` |
| `attachment_deleted` | File attachment removed | `attachment_id`, `message_id` |

Additional staff-side channel: **`{hotel_slug}-conversation-{conversation_id}-chat`**

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `messages-read-by-staff` | Staff marks messages read | `message_ids`, `read_at`, `staff_name` |
| `attachment_deleted` | Attachment removed (conv. channel) | `attachment_id`, `message_id` |

**Source file:** `chat/views.py`

---

## 8. Staff Chat Events

### 8a. Conversation Channel — `{hotel_slug}-conversation-{conversation_id}-chat`

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `message_created` | New staff message | `message_data` |
| `message_created` | File attachment posted | `attachment_message_data` |
| `message_edited` | Message content edited | `message_id`, `edited_content` |
| `message_deleted` | Soft-delete message | `message_id`, `deleted_by_staff` |
| `message_deleted` | Hard-delete message | `message_id`, `permanently_deleted` |
| `read_receipt` | Staff reads messages | `message_ids`, `staff_name` / `staff_id` |
| `attachment_uploaded` | Attachment metadata updated | `attachment_data`, `message_id` |
| `attachment_deleted` | Attachment removed | `attachment_id`, `message_id` |

### 8b. Staff Notification Channel — `{hotel_slug}-staff-{staff_id}-notifications`

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `unread_conversations_updated` | Unread count changed | `unread_count` |

**Source files:** `staff_chat/views_messages.py`, `staff_chat/views_attachments.py`, `notifications/notification_manager.py`

---

## 9. Room Service & Menu Events

### 9a. Order Events — `{hotel_slug}.room-service`

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `order_created` | Guest places room service order | `order_id`, `room_number`, `items`, `guest_name` |
| `order_updated` | Order status/details change | `order_id`, `status`, `updated_fields` |

Fired from: **NotificationManager** + **Django `post_save`/`post_delete` signals** in `room_services/signals.py`

### 9b. Menu Management — `{hotel_slug}.staff-menu-management`

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `menu_item_updated` | Menu item add/edit/remove | `menu_type`, `item_data`, `action` |
| `menu_updated` | Bulk menu management changes | `menu_data` |

**Source files:** `room_services/staff_views.py`, `notifications/notification_manager.py`

---

## 10. Attendance & Shift Events

### 10a. Staff Attendance — various channels

| Channel | Event Name | Trigger Context | Data Payload |
|---------|------------|-----------------|--------------|
| `{slug}.attendance` | `staff_clock_status_changed` | Clock in / clock out | `staff_id`, `action`, `time` |
| `attendance-{slug}-staff-{id}` | `clocklog-approved` | Manager approves unrostered clock | `clock_log_id`, `message` |
| `attendance-{slug}-staff-{id}` | `clocklog-rejected` | Manager rejects unrostered clock | `clock_log_id`, `message` |
| `attendance-{slug}-staff-{id}` | `clocklog-extension-granted` | Manager extends session | `clock_log_id`, `message` |
| `attendance-{slug}-managers` | `staff-long-session-acknowledged` | Staff acknowledges long session | `clock_log_id`, `staff_id`, `staff_name`, `action` |
| `attendance-{slug}-managers` | `staff-hard-limit-exceeded` | Staff hits hard time limit | `clock_log_id`, `staff_id`, `staff_name` |

### 10b. Duty & Scheduling — various channels

| Channel | Event Name | Trigger Context | Data Payload |
|---------|------------|-----------------|--------------|
| `{slug}-staff-{id}-duty` | `duty_status_updated` | Staff goes on/off duty | `staff_id`, `new_status` |
| `{slug}-attendance-{period_id}` | `attendance_period_sync` | Period data sync | `sync_data` |
| `{slug}-shift-{shift_id}` | `shift_updated` | Shift definition changed | `shift_data` |
| `{slug}-staff-{id}-schedule` | `schedule_updated` | Staff schedule changed | `schedule_data` |
| `{slug}-staff-{id}-roster` | `roster_updated` | Roster assignment changed | `roster_data` |
| `{slug}-rostering-{date}` | `rostering_updated` | Batch rostering update | `rostering_batch_data` |
| `{slug}-staff-{id}-shifts` | `next_shifts_updated` | Upcoming shifts refreshed | `upcoming_shifts` |

**Source files:** `attendance/views.py`, `attendance/utils.py`, `staff/pusher_utils.py`

---

## 11. Staff Management Events

Channel: **`hotel-{hotel_slug}`** / **`{hotel_slug}-staff-{staff_id}`**

| Channel | Event Name | Trigger Context | Data Payload |
|---------|------------|-----------------|--------------|
| `hotel-{slug}` | `room-type-image-updated` | Room type photo uploaded | `room_type_id`, `photo_url`, `timestamp` |
| `{slug}-staff-{id}` | `access-config-updated` | Staff permissions changed | `access_config_data` |

**Source file:** `hotel/staff_views.py`

---

## 12. Stock / Inventory Events

### 12a. Stocktake List — `{hotel_slug}.stock-stocktakes`

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `stocktake_created` | New stocktake initiated | `stocktake_id`, `created_data` |
| `stocktake_status_changed` | Approved / rejected / reopened | `stocktake_id`, `status`, `approved_by` |
| `stocktake_status_changed` | Bulk cocktail merge completed | `stocktake_id`, `bulk_merge_data` |

### 12b. Single Stocktake — `{hotel_slug}.stock-stocktakes-{stocktake_id}`

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `stocktake_populated` | Lines populated | `line_count`, `timestamp` |
| `line_counted_updated` | Line item counted / recounted | `line_id`, `counted_qty`, `variance` |
| `line_movement_added` | Inventory movement recorded | `movement_id`, `movement_type` |
| `line_movement_updated` | Movement edited | `movement_id`, `updated_data` |
| `line_movement_deleted` | Movement deleted | `movement_id` |

**Source files:** `stock_tracker/views.py`, `stock_tracker/pusher_utils.py`

---

## 13. Self-Healing / Integrity Events

Channel: **`{hotel_slug}.room-bookings`**

| Event Name | Trigger Context | Data Payload |
|------------|-----------------|--------------|
| `booking_integrity_healed` | Auto-heal detected & fixed inconsistency | Audit healing report |
| `booking_party_healed` | Party membership auto-repaired | Party healing details |
| `booking_guests_healed` | Guest record auto-repaired | Guest healing details |

**Source file:** `notifications/notification_manager.py`

---

## 14. Channel Naming Convention Summary

| Pattern | Scope | Auth | Example |
|---------|-------|------|---------|
| `private-guest-booking.{booking_id}` | Single guest booking | Private (token) | `private-guest-booking.42` |
| `private-hotel-{slug}-guest-chat-booking-{id}` | Guest ↔ Staff chat | Private (token) | `private-hotel-sunrise-guest-chat-booking-42` |
| `{slug}.room-bookings` | All staff — bookings | Public* | `sunrise.room-bookings` |
| `{slug}.rooms` | All staff — rooms | Public* | `sunrise.rooms` |
| `{slug}.room-service` | All staff — orders | Public* | `sunrise.room-service` |
| `{slug}.staff-menu-management` | Menu managers | Public* | `sunrise.staff-menu-management` |
| `{slug}.attendance` | All staff — clocking | Public* | `sunrise.attendance` |
| `{slug}-staff-overstays` | Staff — overstay alerts | Public* | `sunrise-staff-overstays` |
| `{slug}-staff-bookings` | Staff — booking updates | Public* | `sunrise-staff-bookings` |
| `{slug}-conversation-{id}-chat` | Staff chat conversation | Public* | `sunrise-conversation-7-chat` |
| `{slug}-staff-{id}-notifications` | Individual staff alerts | Public* | `sunrise-staff-5-notifications` |
| `{slug}-staff-{id}-duty` | Individual duty status | Public* | `sunrise-staff-5-duty` |
| `attendance-{slug}-staff-{id}` | Individual clock actions | Public* | `attendance-sunrise-staff-5` |
| `attendance-{slug}-managers` | Manager alerts | Public* | `attendance-sunrise-managers` |
| `{slug}-shift-{id}` | Shift updates | Public* | `sunrise-shift-3` |
| `{slug}-staff-{id}-schedule` | Staff schedule | Public* | `sunrise-staff-5-schedule` |
| `{slug}-staff-{id}-roster` | Staff roster | Public* | `sunrise-staff-5-roster` |
| `{slug}-rostering-{date}` | Daily rostering batch | Public* | `sunrise-rostering-2026-03-25` |
| `{slug}-staff-{id}-shifts` | Upcoming shifts | Public* | `sunrise-staff-5-shifts` |
| `hotel-{slug}` | Hotel-wide admin | Public* | `hotel-sunrise` |
| `{slug}-staff-{id}` | Individual staff config | Public* | `sunrise-staff-5` |
| `{slug}.stock-stocktakes` | Stock list | Public* | `sunrise.stock-stocktakes` |
| `{slug}.stock-stocktakes-{id}` | Single stocktake | Public* | `sunrise.stock-stocktakes-12` |
| `{slug}-attendance-{period_id}` | Attendance period | Public* | `sunrise-attendance-9` |

> \* "Public" channels are scoped by `hotel_slug` — not globally public. Only clients that know the slug can subscribe.

---

## 15. Audit Statistics

| Metric | Count |
|--------|-------|
| **NotificationManager realtime methods** | 32 |
| **Direct `pusher_client.trigger()` call sites** | 25+ |
| **Unique channel patterns** | 23 |
| **Unique event names** | 40+ |
| **Apps with realtime integration** | 10 (bookings, chat, staff_chat, attendance, rooms, room_services, room_bookings, hotel, stock_tracker, notifications) |
| **Guest-facing event types** | 6 |
| **Staff-facing event types** | 34+ |
| **Django signal-driven events** | 2 (room service `post_save` / `post_delete`) |
| **Self-healing events** | 3 |

---

*Generated from codebase audit — 2026-03-25*
