# RBAC Wave 2 Audit — chat + staff_chat

Audit of the current RBAC / security state of the `chat` (guest ↔ staff) and `staff_chat` (staff ↔ staff) apps prior to canonical capability migration. Code-only; no docs / comments / assumptions.

Reference files:
- [chat/urls.py](chat/urls.py)
- [chat/staff_urls.py](chat/staff_urls.py)
- [chat/views.py](chat/views.py)
- [staff_chat/urls.py](staff_chat/urls.py)
- [staff_chat/views.py](staff_chat/views.py)
- [staff_chat/views_messages.py](staff_chat/views_messages.py)
- [staff_chat/views_attachments.py](staff_chat/views_attachments.py)
- [staff_chat/permissions.py](staff_chat/permissions.py)
- [staff/permissions.py](staff/permissions.py)
- [staff/capability_catalog.py](staff/capability_catalog.py)
- [staff/module_policy.py](staff/module_policy.py)
- [hotel/canonical_guest_chat_views.py](hotel/canonical_guest_chat_views.py)
- [common/guest_chat_grant.py](common/guest_chat_grant.py)
- [notifications/views.py](notifications/views.py)
- [guest_urls.py](guest_urls.py)
- [staff_urls.py](staff_urls.py)

---

## 1. Endpoint Inventory

### 1.1 `chat` (guest-room chat) — staff endpoints

Mounted both at `/api/chat/<hotel_slug>/...` (via [chat/urls.py](chat/urls.py)) and at `/api/staff/hotel/<hotel_slug>/chat/...` (via [chat/staff_urls.py](chat/staff_urls.py) wrapped by [staff_urls.py](staff_urls.py#L263)).

| Endpoint | Method | View | Current permissions | Access type | Risk | Source |
|---|---|---|---|---|---|---|
| `active-rooms/` | GET | `get_active_rooms` | `IsAuthenticated` + inline `HasNavPermission('chat')` + inline hotel slug check | Staff | Low | [chat/views.py](chat/views.py#L391-L405) |
| `conversations/from-room/<room_number>/` | POST | `get_or_create_conversation_from_room` | `IsAuthenticated` + inline `HasNavPermission('chat')` + inline hotel slug check | Staff | Low | [chat/views.py](chat/views.py#L355-L379) |
| `conversations/` | GET | `get_active_conversations` | `IsAuthenticated` + inline `HasNavPermission('chat')` + inline hotel slug check | Staff | Low | [chat/views.py](chat/views.py#L54-L72) |
| `conversations/<id>/messages/` | GET | `get_conversation_messages` | `IsAuthenticated` + inline `HasNavPermission('chat')` + inline hotel slug + cross-hotel object check | Staff | Low | [chat/views.py](chat/views.py#L75-L102) |
| `conversations/<id>/messages/send/` | POST | `send_conversation_message` | `IsAuthenticated` + inline `HasNavPermission('chat')` + inline hotel slug check | Staff (writes guest-or-staff message) | Medium — sender_type derived only from `request.user.staff_profile`; conversation hotel not re-checked beyond URL | [chat/views.py](chat/views.py#L106-L353) |
| `hotels/<hotel_slug>/conversations/unread-count/` | GET | `get_unread_conversation_count` | `IsAuthenticated` + inline `HasNavPermission('chat')` | Staff | Low | [chat/views.py](chat/views.py#L514-L562) |
| `<hotel_slug>/conversations/unread-count/` | GET | `get_unread_count` | `IsAuthenticated` + inline `HasNavPermission('chat')` + inline hotel slug check | Staff | Low | [chat/views.py](chat/views.py#L407-L432) |
| `conversations/<id>/mark-read/` | POST | `mark_conversation_read` | **`AllowAny`** (branches on staff vs guest by `request.user.staff_profile`) | Mixed staff/guest | **High** — no auth check at all; any unauthenticated request mutates message read flags & emits Pusher events | [chat/views.py](chat/views.py#L433-L513) |
| `conversations/<id>/assign-staff/` | POST | `assign_staff_to_conversation` | `IsAuthenticated` + inline `HasNavPermission('chat')` + inline `staff_profile` + hotel object check | Staff | Low | [chat/views.py](chat/views.py#L582-L702) |
| `messages/<id>/update/` | PATCH | `update_message` | **`AllowAny`** + inline ownership check (sender‑only) | Mixed | **High** — no auth required; no hotel scoping; guest branch is fully permissive | [chat/views.py](chat/views.py#L707-L808) |
| `messages/<id>/delete/` | DELETE | `delete_message` | **`AllowAny`** + inline ownership/`has_capability('chat.message.moderate')` | Mixed | **High** — no auth required; no hotel scoping on lookup | [chat/views.py](chat/views.py#L811-L1014) |
| `<hotel_slug>/conversations/<id>/upload-attachment/` | POST | `upload_message_attachment` | **`AllowAny`** + inline hotel-conversation match | Mixed | **High** — guest path can upload for any conversation in the slug; no token / session check on `chat/...` mount; staff side relies only on `request.user.staff_profile` presence | [chat/views.py](chat/views.py#L1019-L1180) |
| `attachments/<id>/delete/` | DELETE | `delete_attachment` | **`AllowAny`** + inline ownership branch | Mixed | **High** — no auth required, no hotel scoping on lookup | [chat/views.py](chat/views.py#L1183-L1289) |
| `<hotel_slug>/save-fcm-token/` | POST | `save_fcm_token` | **`AllowAny`** | Public/guest | **High** — anyone can overwrite any room's `guest_fcm_token` for any hotel slug | [chat/views.py](chat/views.py#L1295-L1349) |

### 1.2 `chat` (canonical guest chat) — guest endpoints

Mounted under `/api/guest/...` via [guest_urls.py](guest_urls.py#L575-L592).

| Endpoint | Method | View | Current permissions | Access type | Risk | Source |
|---|---|---|---|---|---|---|
| `hotel/<slug>/chat/context` | GET | `GuestChatContextView` | `AllowAny` + raw guest token validation via `resolve_guest_access` (scope `CHAT`) + `GuestTokenBurstThrottle`/`GuestTokenSustainedThrottle` | Guest token | Low | [hotel/canonical_guest_chat_views.py](hotel/canonical_guest_chat_views.py#L98-L166) |
| `hotel/<slug>/chat/messages` | GET, POST | `GuestChatSendMessageView` | `AllowAny` + `X-Guest-Chat-Session` validation (`validate_guest_chat_grant`) | Guest session | Low | [hotel/canonical_guest_chat_views.py](hotel/canonical_guest_chat_views.py#L168-L320) |
| `hotel/<slug>/chat/pusher/auth` | POST | `GuestChatPusherAuthView` | `AllowAny` + session validation + per-booking channel match | Guest session | Low | [hotel/canonical_guest_chat_views.py](hotel/canonical_guest_chat_views.py#L416-L520) |
| `hotel/<slug>/chat/conversations/<id>/mark_read/` | POST | `GuestChatMarkReadView` | `AllowAny` + session validation + conversation/booking match | Guest session | Low | [hotel/canonical_guest_chat_views.py](hotel/canonical_guest_chat_views.py#L322-L414) |

### 1.3 `staff_chat`

Mounted at `/api/staff/hotel/<hotel_slug>/staff_chat/...` via [staff_urls.py](staff_urls.py#L263).

| Endpoint | Method | View | Current permissions | Access type | Risk | Source |
|---|---|---|---|---|---|---|
| `staff-list/` | GET | `StaffListViewSet.list` | `IsAuthenticated` + `HasChatNav` + `IsStaffMember` + `IsSameHotel` | Staff | Low | [staff_chat/views.py](staff_chat/views.py#L31-L77) |
| `conversations/` | GET | `StaffConversationViewSet.list` | `IsAuthenticated` + `HasChatNav` + `IsStaffMember` + `IsSameHotel`; queryset scoped to `participants=staff` | Staff | Low | [staff_chat/views.py](staff_chat/views.py#L80-L124) |
| `conversations/` | POST | `StaffConversationViewSet.create` | same class set; inline `current_staff.hotel != hotel` + same-hotel participant validation | Staff | Low | [staff_chat/views.py](staff_chat/views.py#L126-L184) |
| `conversations/for-forwarding/` | GET | `StaffConversationViewSet.for_forwarding` | same class set; inline staff-hotel check | Staff | Low | [staff_chat/views.py](staff_chat/views.py#L633-L737) |
| `conversations/unread-count/` | GET | `StaffConversationViewSet.unread_count` | same class set | Staff | Low | [staff_chat/views.py](staff_chat/views.py#L500-L568) |
| `conversations/conversations-with-unread-count/` | GET | `StaffConversationViewSet.conversations_with_unread_count` | same class set | Staff | Low | [staff_chat/views.py](staff_chat/views.py#L569-L601) |
| `conversations/bulk-mark-as-read/` | POST | `StaffConversationViewSet.bulk_mark_as_read` | same class set | Staff | Low | [staff_chat/views.py](staff_chat/views.py#L373-L466) |
| `conversations/<pk>/` | GET, PUT, PATCH, DELETE | `StaffConversationViewSet.retrieve/update/partial_update/destroy` | only class set + queryset scoping. **No object-level `IsConversationParticipant` / `CanManageConversation`** | Staff | **High** — DELETE/PUT/PATCH on a conversation has no creator/moderation gate; queryset already filters to participants but any participant can update or destroy the conversation | [staff_chat/views.py](staff_chat/views.py#L80-L124) (queryset only) |
| `conversations/<conversation_id>/send-message/` | POST | `views_messages.send_message` | `IsAuthenticated` + `HasChatNav` + `IsStaffMember` + `IsSameHotel`; inline participants check | Staff | Low | [staff_chat/views_messages.py](staff_chat/views_messages.py#L116-L264) |
| `conversations/<conversation_id>/messages/` | GET | `views_messages.get_conversation_messages` | same class set; inline participants check | Staff | Low | [staff_chat/views_messages.py](staff_chat/views_messages.py#L266-L319) |
| `messages/<message_id>/mark-as-read/` | POST | `views_messages.mark_message_as_read` | same class set; inline participants check | Staff | Low | [staff_chat/views_messages.py](staff_chat/views_messages.py#L43-L113) |
| `messages/<message_id>/edit/` | PATCH | `views_messages.edit_message` | same class set; inline `message.sender.id == staff.id` | Staff | Low (own-only) | [staff_chat/views_messages.py](staff_chat/views_messages.py#L322-L401) |
| `messages/<message_id>/delete/` | DELETE | `views_messages.delete_message` | same class set; inline owner + `has_capability('staff_chat.conversation.moderate')` for non-owner / hard-delete | Staff | Low | [staff_chat/views_messages.py](staff_chat/views_messages.py#L404-L555) |
| `messages/<message_id>/react/` | POST | `views_messages.add_reaction` | same class set; inline participants check | Staff | Low | [staff_chat/views_messages.py](staff_chat/views_messages.py#L601-L716) |
| `messages/<message_id>/react/<emoji>/` | DELETE | `views_messages.remove_reaction` | same class set; inline `staff_profile` only — **no participants check before deleting reaction** | Staff | Low (delete only own emoji rows) | [staff_chat/views_messages.py](staff_chat/views_messages.py#L719-L795) |
| `messages/<message_id>/forward/` | POST | `views_messages.forward_message` | same class set; inline source-conversation participants check; inline target-conversation participants check per target | Staff | Low | [staff_chat/views_messages.py](staff_chat/views_messages.py#L798-L1021) |
| `conversations/<conversation_id>/upload/` | POST | `views_attachments.upload_attachments` | `IsAuthenticated` + `HasChatNav` + `IsStaffMember` + `IsSameHotel`; inline participants + sender check | Staff | Low | [staff_chat/views_attachments.py](staff_chat/views_attachments.py#L31-L213) |
| `attachments/<attachment_id>/delete/` | DELETE | `views_attachments.delete_attachment` | same class set; inline cross-hotel match + sender owner OR `has_capability('staff_chat.conversation.moderate')` | Staff | Low | [staff_chat/views_attachments.py](staff_chat/views_attachments.py#L216-L319) |
| `attachments/<attachment_id>/url/` | GET | `views_attachments.get_attachment_url` | same class set; inline participants check | Staff | Low | [staff_chat/views_attachments.py](staff_chat/views_attachments.py#L321-L376) |
| `conversations/<pk>/send_message/` (legacy) | POST | `StaffConversationViewSet.send_message` | only class set + inline participants check via `staff not in conversation.participants.all()` | Staff | Low | [staff_chat/views.py](staff_chat/views.py#L186-L249) |
| `conversations/<pk>/mark_as_read/` (legacy) | POST | `StaffConversationViewSet.mark_as_read` | same | Staff | Low | [staff_chat/views.py](staff_chat/views.py#L251-L329) |
| `conversations/sync-unread-counts/` | POST | `StaffConversationViewSet.sync_unread_counts` (registered only via `@action`, **not exposed in [staff_chat/urls.py](staff_chat/urls.py)**) | only class set | Staff | Info — likely dead path | [staff_chat/views.py](staff_chat/views.py#L468-L498) |

### 1.4 Cross-cutting

| Endpoint | Method | View | Current permissions | Access type | Risk | Source |
|---|---|---|---|---|---|---|
| `/api/notifications/pusher/auth/` | POST | `PusherAuthView` (staff branch) | `AllowAny`; staff branch requires `request.user.is_authenticated` + `Staff.objects.get(user=request.user)` and matches channel against `staff.hotel.slug` patterns including `private-hotel-{hotel_slug}-guest-chat-booking-` | Staff | Medium — staff with any hotel can authenticate to *their own* hotel's guest-chat booking channels regardless of `chat.guest.respond` capability | [notifications/views.py](notifications/views.py#L22-L126) |
| `/api/notifications/pusher/auth/` (guest branch) | POST | `PusherAuthView._handle_guest_auth` | Hard-rejects with HTTP 403 | Disabled | Low | [notifications/views.py](notifications/views.py#L108-L126) |

---

## 2. Current Protection (per endpoint highlights)

Only endpoints with non-trivial behaviour or gaps are detailed. The full matrix is in §1.

### `chat.send_conversation_message` — [chat/views.py](chat/views.py#L106-L353)
- Permission classes: `IsAuthenticated`
- Inline checks: `HasNavPermission('chat').has_permission(...)`; `staff_profile.hotel.slug == hotel_slug`
- Hotel scoping: by `staff.hotel.slug == hotel_slug` only; `conversation.room.hotel` is loaded but **not** compared against the URL slug.
- Conversation ownership: none — any authenticated staff in the hotel can post to any conversation belonging to that hotel.
- Source: lines 117-123

### `chat.mark_conversation_read` — [chat/views.py](chat/views.py#L433-L513)
- Permission classes: `AllowAny`
- Inline checks: branches on `request.user.staff_profile`; no auth, no hotel-slug match against conversation, no token validation.
- Hotel scoping: none.
- Conversation/message ownership: none.
- Source: lines 434-436

### `chat.update_message` — [chat/views.py](chat/views.py#L707-L808)
- Permission classes: `AllowAny`
- Inline checks: `is_staff and message.sender_type=='staff'` → must equal `message.staff`; guest branch (`not is_staff and message.sender_type=='guest'`) is unconditionally allowed; otherwise denied.
- Hotel scoping: none — message looked up by id only.
- Source: lines 712-744

### `chat.delete_message` — [chat/views.py](chat/views.py#L811-L1014)
- Permission classes: `AllowAny`
- Inline checks: staff → own message OR (hard delete on others requires `has_capability(request.user, 'chat.message.moderate')`); staff may delete any guest message; guest may delete only guest messages, no further verification of room association ("since they're anonymous").
- Hotel scoping: none on lookup.
- Source: lines 819-879

### `chat.upload_message_attachment` — [chat/views.py](chat/views.py#L1019-L1180)
- Permission classes: `AllowAny`
- Inline checks: `conversation.room.hotel != hotel` (URL slug match).
- Sender determined from `request.user.staff_profile` — **no guest token / session check**, so any external POST with the right URL becomes a "guest" upload.
- Source: lines 1031-1057

### `chat.delete_attachment` — [chat/views.py](chat/views.py#L1183-L1289)
- Permission classes: `AllowAny`
- Inline checks: staff branch requires `message.staff == staff`; guest branch (`not is_staff and message.sender_type=='guest'`) unconditionally allowed.
- Hotel scoping: none on lookup.

### `chat.save_fcm_token` — [chat/views.py](chat/views.py#L1295-L1349)
- Permission classes: `AllowAny`
- Inline checks: hotel + room exist.
- No proof of room occupancy / token / session — any caller can poison `Room.guest_fcm_token`.

### Canonical guest chat — [hotel/canonical_guest_chat_views.py](hotel/canonical_guest_chat_views.py)
- Permission classes: `AllowAny`
- Inline checks: `validate_guest_chat_grant(session, hotel_slug)` (HMAC-signed grant from `common.guest_chat_grant`, scope `guest_chat`, max age `GUEST_CHAT_GRANT_MAX_AGE_SECONDS` default 4h, hotel-slug cross-validated). Per-booking channel match in Pusher auth (`channel_name != guest_chat_channel(hotel_slug, booking.booking_id)` → 403).
- Hotel scoping: enforced by grant claim.
- Conversation/message ownership: enforced by `Conversation.booking == grant.booking`.

### `staff_chat.StaffConversationViewSet` — [staff_chat/views.py](staff_chat/views.py#L80-L124)
- Permission classes: `IsAuthenticated`, `HasChatNav`, `IsStaffMember`, `IsSameHotel`.
- Object-level enforcement: queryset scoped to `participants=staff`. **No** `has_object_permission` (`IsConversationParticipant` / `CanManageConversation` defined in [staff_chat/permissions.py](staff_chat/permissions.py) but unused). DELETE/PUT/PATCH inherit only the queryset filter — any participant can mutate or destroy the conversation row.

### `staff_chat.views_messages.delete_message` — [staff_chat/views_messages.py](staff_chat/views_messages.py#L404-L555)
- Permission classes: `IsAuthenticated, HasChatNav, IsStaffMember, IsSameHotel`.
- Inline checks: own-message → soft delete allowed; non-owner → `has_capability(request.user, 'staff_chat.conversation.moderate')`; hard-delete on others additionally requires same capability.

### `staff_chat.views_attachments.delete_attachment` — [staff_chat/views_attachments.py](staff_chat/views_attachments.py#L216-L319)
- Permission classes: same as above.
- Inline checks: cross-hotel match (`conversation.hotel.slug != hotel_slug`); owner OR `has_capability(... 'staff_chat.conversation.moderate')`.

### `notifications.views.PusherAuthView` (staff branch) — [notifications/views.py](notifications/views.py#L65-L106)
- `staff.hotel.slug` is used to compute `allowed_patterns`, so a staff member can only auth to channels of their *own* hotel (incl. `private-hotel-{hotel_slug}-guest-chat-booking-*`). No capability check — any staff member of the hotel can subscribe to any guest-chat booking channel of that hotel.

---

## 3. Existing Canonical Capabilities

| Capability | Used where | Module policy exposed? | Source |
|---|---|---|---|
| `chat.message.moderate` | Imperative gate for hard-deleting other staff's messages in guest chat | No — `chat` not in `MODULE_POLICY` | defined: [staff/capability_catalog.py](staff/capability_catalog.py#L55), used: [chat/views.py](chat/views.py#L853-L856), example reference: [staff/permissions.py](staff/permissions.py#L536-L541) |
| `chat.guest.respond` | `staff_with_capability(hotel, 'chat.guest.respond')` notification routing for inbound guest messages | No | defined: [staff/capability_catalog.py](staff/capability_catalog.py#L58), used: [chat/views.py](chat/views.py#L276-L283); preset: [staff/capability_catalog.py](staff/capability_catalog.py#L927) (department `front_office`) |
| `staff_chat.conversation.moderate` | Imperative gate: non-owner delete in `staff_chat`; non-owner attachment delete; legacy `CanManageConversation`, `CanDeleteMessage` permission classes (defined but **not wired into views**) | No — `staff_chat` not in `MODULE_POLICY` | defined: [staff/capability_catalog.py](staff/capability_catalog.py#L67), used: [staff_chat/views_messages.py](staff_chat/views_messages.py#L425-L443), [staff_chat/views_attachments.py](staff_chat/views_attachments.py#L256-L259), [staff_chat/permissions.py](staff_chat/permissions.py#L100-L141) |

Tier baseline `_SUPERVISOR_AUTHORITY` includes `CHAT_MESSAGE_MODERATE` and `STAFF_CHAT_CONVERSATION_MODERATE`, granted to `super_staff_admin` + `staff_admin` tiers ([staff/capability_catalog.py](staff/capability_catalog.py#L460-L464) and [staff/capability_catalog.py](staff/capability_catalog.py#L833-L840)).

[staff/module_policy.py](staff/module_policy.py) does **not** declare `chat` or `staff_chat` modules — neither `view_capability` nor any actions are exposed via the canonical `rbac` payload.

---

## 4. Security Gaps

| File | Function/Class | Issue | Risk |
|---|---|---|---|
| [chat/views.py](chat/views.py#L433-L513) | `mark_conversation_read` | `permission_classes=[AllowAny]`. No auth, no hotel scoping, no guest token / session check. Any anonymous request can flip read state and trigger Pusher events on `{hotel.slug}-conversation-{id}-chat`. | High |
| [chat/views.py](chat/views.py#L707-L808) | `update_message` | `AllowAny`; guest branch (`not is_staff and message.sender_type=='guest'`) edits any guest message in any hotel by ID. No hotel/session scoping. | High |
| [chat/views.py](chat/views.py#L811-L1014) | `delete_message` | `AllowAny`; same gap on the guest branch. Hard-delete moderation is gated on `chat.message.moderate` only when authenticated as staff; anonymous callers can soft-delete arbitrary guest messages by ID. | High |
| [chat/views.py](chat/views.py#L1019-L1180) | `upload_message_attachment` | `AllowAny`. Guest branch uploads to any conversation in the slug with no token/session. Sender type forged by absence of `staff_profile`. | High |
| [chat/views.py](chat/views.py#L1183-L1289) | `delete_attachment` | `AllowAny`; guest branch deletes any guest-message attachment by id. No hotel/session check. | High |
| [chat/views.py](chat/views.py#L1295-L1349) | `save_fcm_token` | `AllowAny`. Anyone can overwrite `Room.guest_fcm_token` for any hotel/room — silent push-notification hijack vector. | High |
| [chat/views.py](chat/views.py#L106-L353) | `send_conversation_message` | Hotel scoping is via `staff.hotel.slug == hotel_slug`, but `Conversation` is fetched by id only (`get_object_or_404(Conversation, id=...)`), then `room.hotel` is read without comparing against URL slug. Can accept `conversation_id` from another hotel if URL slug matches the staff's hotel — partially mitigated because conversation messages reference `conversation.room.hotel` for fan-out. | Medium |
| [chat/views.py](chat/views.py#L260-L301) | `send_conversation_message` (sender derivation) | `sender_type` is derived purely from `request.user.staff_profile`. With `IsAuthenticated`, this works for staff path, but the same endpoint historically allowed guest path. The legacy `_require_staff_or_guest` helper exists at [chat/views.py](chat/views.py#L25-L48) but is never called by any of the staff endpoints — orphan code. | Low |
| [chat/views.py](chat/views.py) (all staff endpoints) | All use inline `HasNavPermission('chat')` calls instead of `permission_classes=[IsAuthenticated, HasChatNav]`. There is no action-level capability gate (e.g. for `chat.guest.respond`) — any staff with `chat` nav can post, assign, or hard-delete via the moderation branch. | `chat` module visibility = nav-only; no canonical action capabilities. | Medium |
| [staff_chat/views.py](staff_chat/views.py#L80-L124) | `StaffConversationViewSet` (DELETE/PUT/PATCH) | No object-level permission. `IsConversationParticipant` and `CanManageConversation` are defined in [staff_chat/permissions.py](staff_chat/permissions.py) but never used. Any participant can `DELETE /conversations/<pk>/`. | High |
| [staff_chat/views_messages.py](staff_chat/views_messages.py#L719-L795) | `remove_reaction` | Skips the `conversation.participants.filter(id=staff.id).exists()` participant check used elsewhere; only filters reaction by `(message, staff, emoji)`. Effectively safe (deletes only own row) but inconsistent with other handlers. | Low |
| [notifications/views.py](notifications/views.py#L65-L106) | `PusherAuthView._handle_staff_auth` | Allows any same-hotel staff to authenticate to `private-hotel-{hotel_slug}-guest-chat-booking-*`. There is no `chat.guest.respond` capability check here, so staff outside front office can subscribe to guest chat realtime traffic. | Medium |
| [chat/staff_urls.py](chat/staff_urls.py) + [chat/urls.py](chat/urls.py) | URL duplication | The same staff-only views are mounted under both `/api/chat/<slug>/...` (legacy, [chat/urls.py](chat/urls.py)) and `/api/staff/hotel/<slug>/chat/...` ([chat/staff_urls.py](chat/staff_urls.py)). Same auth, but doubles audit surface and any future capability migration must update both mounts. | Low |
| [staff_chat/permissions.py](staff_chat/permissions.py#L25-L57) | `IsConversationParticipant`, `IsMessageSender` | Defined but unused — DRF object permissions never run because no view declares these. Dead code that masks the missing object-level enforcement. | Low |
| [chat/views.py](chat/views.py#L25-L48) | `_require_staff_or_guest` | Helper claims to be a "SECURITY GATE" but always returns `(_, None)` for any request (including unauthenticated). Misleading and unused. | Low |

No `IsAuthenticated`-only staff endpoint is missing `IsStaffMember` in `staff_chat`; in `chat` (both mounts) every staff endpoint is `IsAuthenticated` plus an inline `HasNavPermission('chat')` and an inline `staff_profile.hotel.slug == hotel_slug` check, so `IsStaffMember` / `IsSameHotel` exist only as inline duplicates.

No staff can access another hotel's conversation in either app: queryset / inline slug checks block cross-hotel access.

---

## 5. Zone Separation

| Area | Staff zone | Guest zone | Public? | Notes |
|---|---|---|---|---|
| `chat` (guest↔staff conversations) | `/api/chat/<slug>/...` and `/api/staff/hotel/<slug>/chat/...` — staff endpoints rely on `IsAuthenticated` + inline `HasNavPermission('chat')` + inline hotel-slug match. | Canonical guest endpoints under `/api/guest/hotel/<slug>/chat/...` use signed `X-Guest-Chat-Session` grant ([common/guest_chat_grant.py](common/guest_chat_grant.py)) issued from a raw guest token (`resolve_guest_access`). | Yes (effectively): `mark_conversation_read`, `update_message`, `delete_message`, `upload_message_attachment`, `delete_attachment`, `save_fcm_token` are `AllowAny` with no token/session check on the legacy `/api/chat/...` mount. | Guest realtime channel = `guest_chat_channel(slug, booking_id)` — `private-hotel-{slug}-guest-chat-booking-{booking_id}` ([common/guest_chat_config.py](common/guest_chat_config.py), used at [hotel/canonical_guest_chat_views.py](hotel/canonical_guest_chat_views.py#L420-L455)). |
| `staff_chat` (staff↔staff conversations) | `/api/staff/hotel/<slug>/staff_chat/...` — every endpoint uses `IsAuthenticated, HasChatNav, IsStaffMember, IsSameHotel` plus inline `participants` checks. | None | None | Pusher fan-out via `notification_manager.realtime_staff_chat_*`; channel auth via `notifications.views.PusherAuthView` staff branch. |
| Pusher auth | `/api/notifications/pusher/auth/` — staff JWT/session, channel patterns scoped to `staff.hotel.slug`. | `/api/guest/hotel/<slug>/chat/pusher/auth` — guest session, channel must equal `guest_chat_channel(slug, booking_id)`. | Legacy guest token submitted to `/api/notifications/pusher/auth/` is hard-rejected ([notifications/views.py](notifications/views.py#L108-L126)). | Guest chat remains token + session-based, separate from staff RBAC. |

Confirmed: guest chat continues to authenticate via raw token bootstrap → signed session grant → per-booking channel auth, fully decoupled from staff capability resolution.

---

## 6. Proposed Canonical RBAC Modules/Actions — `PROPOSED`

Derived strictly from current endpoint code. All slugs below are `PROPOSED`; only `chat.message.moderate`, `chat.guest.respond`, `staff_chat.conversation.moderate` exist today.

### `chat` module (guest↔staff)

```
chat:
  view_capability:  chat.module.view              (PROPOSED — replaces nav-only HasChatNav read gate)
  read_capability:  chat.conversation.read        (PROPOSED)
  actions:
    conversation_read:    chat.conversation.read           (PROPOSED) — list rooms / conversations / messages / unread-count
    message_send:         chat.message.send                (PROPOSED) — send_conversation_message
    message_moderate:     chat.message.moderate            (EXISTS)   — hard-delete other staff messages, soft/hard-delete guest messages on staff branch
    attachment_upload:    chat.attachment.upload           (PROPOSED) — upload_message_attachment (staff branch)
    attachment_delete:    chat.attachment.delete           (PROPOSED) — delete_attachment (staff branch)
    conversation_assign:  chat.conversation.assign         (PROPOSED) — assign_staff_to_conversation
    guest_respond:        chat.guest.respond               (EXISTS)   — routing eligibility (already used)
    pusher_subscribe:     chat.realtime.subscribe          (PROPOSED) — used by PusherAuthView when channel starts with private-hotel-{slug}-guest-chat-booking-
```

Notes from code:
- `update_message` for staff messages is gated only on `message.staff == staff` (own-only). Capability-style `message_edit_own` is implied; modeling as inline ownership rule on top of `chat.message.send` is sufficient — no separate slug needed unless cross-staff edit is wanted.
- Guest message edits/deletes/attachments must remain **session-only** (canonical guest endpoints). No staff capability is involved on the guest side.

### `staff_chat` module (staff↔staff)

```
staff_chat:
  view_capability:  staff_chat.module.view                  (PROPOSED)
  read_capability:  staff_chat.conversation.read            (PROPOSED)
  actions:
    conversation_read:     staff_chat.conversation.read     (PROPOSED) — list / retrieve / messages / unread-count / for-forwarding
    conversation_create:   staff_chat.conversation.create   (PROPOSED) — POST /conversations/
    conversation_delete:   staff_chat.conversation.delete   (PROPOSED) — currently UNGATED at view level
    message_send:          staff_chat.message.send          (PROPOSED) — send-message + legacy send_message + forward
    message_edit_own:      modelled as inline ownership only — code gate is `message.sender.id == staff.id`
    message_delete_own:    modelled as inline ownership only — code gate is `message.sender.id == staff.id`
    message_moderate:      staff_chat.conversation.moderate (EXISTS)   — non-owner soft delete + hard delete + non-owner attachment delete
    attachment_upload:     staff_chat.attachment.upload     (PROPOSED) — upload_attachments
    attachment_delete:     staff_chat.attachment.delete     (PROPOSED) — own-delete via inline ownership; non-owner via staff_chat.conversation.moderate
    reaction_manage:       staff_chat.reaction.manage       (PROPOSED) — add_reaction / remove_reaction
    pusher_subscribe:      staff_chat.realtime.subscribe    (PROPOSED) — implicit; PusherAuthView gates by hotel only today
```

Code suggests `message_edit_own` / `message_delete_own` are NOT separate capability slugs — every code path is "you are the sender". Only `message_moderate` (non-owner) is capability-gated. Therefore the proposed final shape diverges from the prompt's template by collapsing `message_edit_own` and `message_delete_own` into inline ownership rules anchored to `staff_chat.message.send`.

---

## 7. Implementation Plan

If implementation follows, the changes required are:

### `staff/capability_catalog.py`
Add to `CANONICAL_CAPABILITIES` (and define module-level constants):
- `CHAT_MODULE_VIEW = 'chat.module.view'`
- `CHAT_CONVERSATION_READ = 'chat.conversation.read'`
- `CHAT_MESSAGE_SEND = 'chat.message.send'`
- `CHAT_ATTACHMENT_UPLOAD = 'chat.attachment.upload'`
- `CHAT_ATTACHMENT_DELETE = 'chat.attachment.delete'`
- `CHAT_CONVERSATION_ASSIGN = 'chat.conversation.assign'`
- `CHAT_REALTIME_SUBSCRIBE = 'chat.realtime.subscribe'`
- `STAFF_CHAT_MODULE_VIEW = 'staff_chat.module.view'`
- `STAFF_CHAT_CONVERSATION_READ = 'staff_chat.conversation.read'`
- `STAFF_CHAT_CONVERSATION_CREATE = 'staff_chat.conversation.create'`
- `STAFF_CHAT_CONVERSATION_DELETE = 'staff_chat.conversation.delete'`
- `STAFF_CHAT_MESSAGE_SEND = 'staff_chat.message.send'`
- `STAFF_CHAT_ATTACHMENT_UPLOAD = 'staff_chat.attachment.upload'`
- `STAFF_CHAT_ATTACHMENT_DELETE = 'staff_chat.attachment.delete'`
- `STAFF_CHAT_REACTION_MANAGE = 'staff_chat.reaction.manage'`
- `STAFF_CHAT_REALTIME_SUBSCRIBE = 'staff_chat.realtime.subscribe'`

Wire into preset bundles:
- All staff (incl. `regular_staff`) need `staff_chat.module.view` + `staff_chat.conversation.read` + `staff_chat.message.send` + `staff_chat.conversation.create` + `staff_chat.attachment.*` + `staff_chat.reaction.manage` + `staff_chat.realtime.subscribe` because today every authenticated staff with chat nav can do these. → tier baseline `regular_staff`/`staff_admin`/`super_staff_admin`.
- `chat.module.view` + `chat.conversation.read` + `chat.message.send` + `chat.attachment.upload` + `chat.attachment.delete` + `chat.conversation.assign` + `chat.realtime.subscribe` should match the current `HasNavPermission('chat')` audience — tier defaults `regular_staff` already has `chat` in `TIER_DEFAULT_NAVS`, so add to a baseline bundle gated on tier+nav, or to the `front_office` department + chat-eligible roles. The narrowest faithful mapping: extend `front_office` department preset with the full `chat.*` operate bundle (it already carries `CHAT_GUEST_RESPOND`).
- `chat.realtime.subscribe` should additionally be required of `PusherAuthView` for the `private-hotel-{slug}-guest-chat-booking-*` pattern.

### `staff/module_policy.py`
Add two new entries to `MODULE_POLICY`:

```python
'chat': {
    'view_capability': CHAT_MODULE_VIEW,
    'read_capability': CHAT_CONVERSATION_READ,
    'actions': {
        'message_send':       CHAT_MESSAGE_SEND,
        'message_moderate':   CHAT_MESSAGE_MODERATE,
        'attachment_upload':  CHAT_ATTACHMENT_UPLOAD,
        'attachment_delete':  CHAT_ATTACHMENT_DELETE,
        'conversation_assign': CHAT_CONVERSATION_ASSIGN,
        'guest_respond':      CHAT_GUEST_RESPOND,
    },
},
'staff_chat': {
    'view_capability': STAFF_CHAT_MODULE_VIEW,
    'read_capability': STAFF_CHAT_CONVERSATION_READ,
    'actions': {
        'conversation_create': STAFF_CHAT_CONVERSATION_CREATE,
        'conversation_delete': STAFF_CHAT_CONVERSATION_DELETE,
        'message_send':        STAFF_CHAT_MESSAGE_SEND,
        'message_moderate':    STAFF_CHAT_CONVERSATION_MODERATE,
        'attachment_upload':   STAFF_CHAT_ATTACHMENT_UPLOAD,
        'attachment_delete':   STAFF_CHAT_ATTACHMENT_DELETE,
        'reaction_manage':     STAFF_CHAT_REACTION_MANAGE,
    },
},
```

### Permission classes (in `chat/permissions.py` new file + extend `staff_chat/permissions.py`)

Add zero-arg `HasCapability` subclasses for each new slug, mirroring the bookings pattern in [staff/permissions.py](staff/permissions.py#L678-L700):
- `CanViewChat`, `CanReadChat`, `CanSendChatMessage`, `CanModerateChat`, `CanUploadChatAttachment`, `CanDeleteChatAttachment`, `CanAssignChatConversation`.
- `CanViewStaffChat`, `CanReadStaffChat`, `CanCreateStaffChatConversation`, `CanDeleteStaffChatConversation`, `CanSendStaffChatMessage`, `CanModerateStaffChat`, `CanUploadStaffChatAttachment`, `CanDeleteStaffChatAttachment`, `CanManageStaffChatReaction`.

Wire `IsConversationParticipant` (already in [staff_chat/permissions.py](staff_chat/permissions.py#L25-L34)) into:
- `StaffConversationViewSet` — add `def get_permissions(self):` that augments the class list with `IsConversationParticipant` for `retrieve/update/partial_update/destroy/send_message/mark_as_read`, plus `CanDeleteStaffChatConversation` for `destroy`.

### View `permission_classes`

`chat` (both [chat/urls.py](chat/urls.py) and [chat/staff_urls.py](chat/staff_urls.py) mounts):
- Staff endpoints: replace `[IsAuthenticated]` + inline `HasNavPermission` with `[IsAuthenticated, IsStaffMember, IsSameHotel, CanReadChat]` (or more specific for writes), and remove inline `HasNavPermission('chat')` calls.
- `mark_conversation_read`, `update_message`, `delete_message`, `upload_message_attachment`, `delete_attachment`, `save_fcm_token`: split into two endpoints:
  - Staff path (mount under `/api/staff/hotel/<slug>/chat/...`) with explicit capability classes.
  - Guest path (mount under `/api/guest/hotel/<slug>/chat/...`) with `ChatSessionAuthenticationMixin` and grant validation, mirroring `GuestChatSendMessageView`. Today these legacy `AllowAny` endpoints have no caller in the canonical guest flow.
- `save_fcm_token`: must require either staff capability or a valid guest session (currently neither).

`staff_chat`:
- Replace `HasChatNav` with `CanViewStaffChat` (capability-driven module visibility).
- `StaffConversationViewSet`: add object-level permission `IsConversationParticipant` and (for `destroy`) `CanDeleteStaffChatConversation`.
- `views_messages.delete_message` / `views_attachments.delete_attachment`: keep imperative `has_capability(...)` for moderation OR replace with `CanModerateStaffChat` permission class on a moderation-specific subroute; not strictly required.

### Inline ownership/membership checks

Keep as-is:
- Staff-message edit / soft-delete: `message.sender.id == staff.id`.
- Guest-chat staff edit / soft-delete: `message.staff == staff`.
- Staff_chat participant gating: `conversation.participants.filter(id=staff.id).exists()`.

Add:
- `chat/views.py` — every endpoint that fetches by `conversation_id` or `message_id` must re-validate `conversation.room.hotel.slug == hotel_slug` (currently only `get_conversation_messages` and `assign_staff_to_conversation` do this).

### Serializer / queryset scoping

No changes required for read serializers in either app — querysets are already scoped by `hotel__slug` and (for `staff_chat`) `participants=staff`.

### Realtime / Pusher auth changes

[notifications/views.py](notifications/views.py#L65-L106) `_handle_staff_auth`:
- Add capability check: when `channel_name.startswith('private-hotel-{hotel_slug}-guest-chat-booking-')`, require `has_capability(request.user, CHAT_GUEST_RESPOND)` (or `CHAT_REALTIME_SUBSCRIBE` if introduced).
- When `channel_name.startswith('{hotel_slug}-staff-')` for staff_chat fan-out, require `has_capability(request.user, STAFF_CHAT_REALTIME_SUBSCRIBE)` (effectively all staff today).

No change required for guest path: [hotel/canonical_guest_chat_views.py](hotel/canonical_guest_chat_views.py#L416-L520) already enforces the per-booking channel match.

---

## 8. Minimal Tests Needed

Keep tests minimal; one assertion per scenario.

1. **Unauthenticated denied — staff endpoints**
   - `GET /api/staff/hotel/<slug>/chat/conversations/` without auth → 401/403.
   - `GET /api/staff/hotel/<slug>/staff_chat/conversations/` without auth → 401/403.
2. **Unauthenticated denied — currently-AllowAny chat endpoints (regression after lockdown)**
   - `POST /api/chat/<slug>/conversations/<id>/mark-read/` without auth/session → 401/403.
   - `PATCH /api/chat/messages/<id>/update/` without auth/session → 401/403.
   - `DELETE /api/chat/messages/<id>/delete/` → 401/403.
   - `POST /api/chat/<slug>/conversations/<id>/upload-attachment/` → 401/403.
   - `DELETE /api/chat/attachments/<id>/delete/` → 401/403.
   - `POST /api/chat/<slug>/save-fcm-token/` → 401/403.
3. **Wrong hotel denied**
   - Staff in hotel A calling `GET /api/staff/hotel/<slug-B>/chat/conversations/` → 403.
   - Same for `staff_chat`.
4. **Staff without capability denied**
   - Staff lacking `chat.module.view` calling `GET /api/staff/hotel/<slug>/chat/conversations/` → 403.
   - Staff lacking `staff_chat.conversation.moderate` deleting another staff's `staff_chat` message → 403.
   - Staff lacking `chat.message.moderate` hard-deleting another staff's guest-chat message → 403.
5. **Staff with capability allowed**
   - Front office staff (carries `chat.guest.respond` via department preset) `POST /chat/.../send/` → 201.
   - `staff_admin` tier staff (carries `staff_chat.conversation.moderate`) hard-deleting another staff's message → 200.
6. **Owner can edit/delete own message**
   - Sender PATCH `/staff_chat/messages/<id>/edit/` → 200.
   - Sender DELETE `/staff_chat/messages/<id>/delete/` → 200.
7. **Non-owner denied unless moderator**
   - Non-sender DELETE `/staff_chat/messages/<id>/delete/` without `staff_chat.conversation.moderate` → 403.
   - Non-sender DELETE with capability → 200.
8. **Conversation destroy gated**
   - Participant DELETE `/staff_chat/conversations/<pk>/` without `staff_chat.conversation.delete` → 403 (currently 204 — regression test).
9. **Guest token/session still works**
   - `GET /api/guest/hotel/<slug>/chat/context?token=<raw>` → 200 with `chat_session`.
   - `POST /api/guest/hotel/<slug>/chat/messages` with `X-Guest-Chat-Session: <session>` → 201.
   - Same `POST` without header → 401 `SESSION_REQUIRED`.
   - Same `POST` with grant for hotel B against hotel A → 403 `GRANT_HOTEL_MISMATCH`.
10. **Pusher auth scoped correctly**
    - Staff in hotel A POST `/api/notifications/pusher/auth/` with `channel_name = private-hotel-<slug-B>-guest-chat-booking-<id>` → 403.
    - Staff in hotel A without `chat.guest.respond` (after lockdown) on `private-hotel-<slug-A>-guest-chat-booking-<id>` → 403.
    - Guest with valid session POST `/api/guest/hotel/<slug>/chat/pusher/auth` for matching booking channel → 200.
    - Same guest with mismatching `channel_name` → 403 `CHANNEL_MISMATCH`.
    - Legacy `_handle_guest_auth` on `/api/notifications/pusher/auth/` with any guest token → 403 `ENDPOINT_MOVED`.
