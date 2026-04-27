# RBAC Wave 2B Audit — `staff_chat` (staff ↔ staff messenger)

> Code-derived only. No documentation, README, comment, or naming inference.
> No code changes were made; this is an audit pass.

---

## 1. Files inspected

Real source files read end-to-end (or at the relevant ranges) for this audit:

- [staff_chat/urls.py](staff_chat/urls.py)
- [staff_chat/views.py](staff_chat/views.py)
- [staff_chat/views_messages.py](staff_chat/views_messages.py)
- [staff_chat/views_attachments.py](staff_chat/views_attachments.py)
- [staff_chat/permissions.py](staff_chat/permissions.py)
- [staff_chat/serializers.py](staff_chat/serializers.py)
- [staff_chat/serializers_staff.py](staff_chat/serializers_staff.py)
- [staff_urls.py](staff_urls.py) (mount point + `STAFF_APPS` loop)
- [staff/permissions.py](staff/permissions.py) (`HasCapability`, `has_capability`, `CanViewStaffChatModule`, `CanReadStaffChatConversation`, `CanCreateStaffChatConversation`, `CanDeleteStaffChatConversation`, `CanSendStaffChatMessage`, `CanModerateStaffChatMessage`, `CanUploadStaffChatAttachment`, `CanDeleteStaffChatAttachment`, `CanManageStaffChatReaction`)
- [staff/capability_catalog.py](staff/capability_catalog.py) (`STAFF_CHAT_*` constants, `CANONICAL_CAPABILITIES`, `_STAFF_CHAT_BASE`, `_SUPERVISOR_AUTHORITY`)
- [staff/module_policy.py](staff/module_policy.py) (`MODULE_POLICY['staff_chat']`)

Files in scope but **not** inspected as authority sources (models / services /
serializer bodies were only consulted for ownership/participant fields):

- [staff_chat/models.py](staff_chat/models.py) — referenced by views (`StaffConversation.participants`, `StaffChatMessage.sender`, etc.)
- [staff_chat/serializers_messages.py](staff_chat/serializers_messages.py), [staff_chat/serializers_attachments.py](staff_chat/serializers_attachments.py) — payload validation only.

Excluded per request: `chat/`, `common/guest_chat_grant.py`, canonical guest
chat views, `stock_tracker`, all test files.

---

## 2. URL / endpoint inventory

URL mount: [staff_urls.py](staff_urls.py#L260-L268) loops over `STAFF_APPS`
(includes `'staff_chat'`, [staff_urls.py](staff_urls.py#L48-L62)) and mounts:

```
path('hotel/<str:hotel_slug>/staff_chat/', include('staff_chat.urls'))
```

So every endpoint below is live at
`/api/staff/hotel/<hotel_slug>/staff_chat/...`.

Routes are declared in [staff_chat/urls.py](staff_chat/urls.py).

| # | Method | Path (relative to mount) | View | Action / function | `permission_classes` | Serializer | Model / service touched |
|---|--------|--------------------------|------|-------------------|----------------------|------------|--------------------------|
| 1 | GET | `staff-list/` | `StaffListViewSet` | `list` | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanReadStaffChatConversation` | `StaffListSerializer` | `staff.Staff` |
| 2 | GET | `conversations/` | `StaffConversationViewSet` | `list` (via `get_permissions` "list" branch) | base + `CanReadStaffChatConversation` | `StaffConversationSerializer` | `StaffConversation` |
| 3 | POST | `conversations/` | `StaffConversationViewSet` | `create` | base + `CanCreateStaffChatConversation` | `StaffConversationSerializer` | `StaffConversation.get_or_create_conversation` |
| 4 | GET | `conversations/for-forwarding/` | `StaffConversationViewSet` | `for_forwarding` | base + `CanReadStaffChatConversation` | inline JSON | `StaffConversation`, `StaffChatMessage` |
| 5 | GET | `conversations/unread-count/` | `StaffConversationViewSet` | `unread_count` | base + `CanReadStaffChatConversation` | inline JSON | `StaffConversation.get_unread_count_for_staff` |
| 6 | GET | `conversations/conversations-with-unread-count/` | `StaffConversationViewSet` | `conversations_with_unread_count` | base + `CanReadStaffChatConversation` | inline JSON | `StaffConversation` |
| 7 | POST | `conversations/bulk-mark-as-read/` | `StaffConversationViewSet` | `bulk_mark_as_read` | base + `CanReadStaffChatConversation` | inline | `StaffChatMessage.read_by`, `notification_manager.realtime_staff_chat_conversations_with_unread` |
| 8 | GET | `conversations/<pk>/` | `StaffConversationViewSet` | `retrieve` | base + `CanReadStaffChatConversation`, `IsConversationParticipant` | `StaffConversationDetailSerializer` | `StaffConversation` |
| 9 | PUT | `conversations/<pk>/` | `StaffConversationViewSet` | `update` | base + `_DenyAll` | n/a | hard-denied |
| 10 | PATCH | `conversations/<pk>/` | `StaffConversationViewSet` | `partial_update` | base + `_DenyAll` | n/a | hard-denied |
| 11 | DELETE | `conversations/<pk>/` | `StaffConversationViewSet` | `destroy` | base + `CanReadStaffChatConversation`, `IsConversationParticipant`, `CanDeleteStaffChatConversation` | n/a | `StaffConversation` |
| 12 | POST | `conversations/<conversation_id>/send-message/` | `views_messages.send_message` (FBV) | — | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanReadStaffChatConversation`, `CanSendStaffChatMessage` | `MessageCreateSerializer`, `StaffChatMessageSerializer` | `StaffChatMessage`, `notification_manager.realtime_staff_chat_message_created`, `notify_conversation_participants` (FCM) |
| 13 | GET | `conversations/<conversation_id>/messages/` | `views_messages.get_conversation_messages` | — | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanReadStaffChatConversation` | `StaffChatMessageSerializer` | `StaffChatMessage` |
| 14 | POST | `messages/<message_id>/mark-as-read/` | `views_messages.mark_message_as_read` | — | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanReadStaffChatConversation` | `StaffChatMessageSerializer` | `StaffChatMessage.mark_as_read_by`, `broadcast_read_receipt` |
| 15 | PATCH | `messages/<message_id>/edit/` | `views_messages.edit_message` | — | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanSendStaffChatMessage` | `MessageUpdateSerializer`, `StaffChatMessageSerializer` | `StaffChatMessage` |
| 16 | DELETE | `messages/<message_id>/delete/` | `views_messages.delete_message` | — | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanReadStaffChatConversation` (+ inline `has_capability('staff_chat.conversation.moderate')` for non-owner / hard delete) | `StaffChatMessageSerializer` | `StaffChatMessage`, `notification_manager.realtime_staff_chat_message_deleted` |
| 17 | POST | `messages/<message_id>/react/` | `views_messages.add_reaction` | — | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanReadStaffChatConversation`, `CanManageStaffChatReaction` | `MessageReactionCreateSerializer`, `MessageReactionSerializer` | `StaffMessageReaction` |
| 18 | DELETE | `messages/<message_id>/react/<emoji>/` | `views_messages.remove_reaction` | — | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanReadStaffChatConversation`, `CanManageStaffChatReaction` | inline | `StaffMessageReaction` |
| 19 | POST | `messages/<message_id>/forward/` | `views_messages.forward_message` | — | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanReadStaffChatConversation`, `CanSendStaffChatMessage` | `ForwardMessageSerializer`, `StaffChatMessageSerializer` | `StaffChatMessage`, `StaffConversation.get_or_create_conversation`, `notification_manager.realtime_staff_chat_message_created` |
| 20 | POST | `conversations/<conversation_id>/upload/` | `views_attachments.upload_attachments` | — | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanReadStaffChatConversation`, `CanUploadStaffChatAttachment` | `AttachmentUploadSerializer`, `StaffChatAttachmentSerializer`, `StaffChatMessageSerializer` | `StaffChatAttachment`, `StaffChatMessage`, `notification_manager.realtime_staff_chat_*` |
| 21 | DELETE | `attachments/<attachment_id>/delete/` | `views_attachments.delete_attachment` | — | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanReadStaffChatConversation` (+ inline `has_capability('staff_chat.attachment.delete')` for own; `staff_chat.conversation.moderate` for others) | n/a | `StaffChatAttachment`, `notification_manager.realtime_staff_chat_attachment_deleted` |
| 22 | GET | `attachments/<attachment_id>/url/` | `views_attachments.get_attachment_url` | — | `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`, `CanViewStaffChatModule`, `CanReadStaffChatConversation` | inline JSON | `StaffChatAttachment` |
| 23 | POST | `conversations/<pk>/send_message/` (legacy) | `StaffConversationViewSet` | `send_message` | base + `CanReadStaffChatConversation`, `IsConversationParticipant`, `CanSendStaffChatMessage` | `StaffChatMessageSerializer` | `StaffChatMessage` |
| 24 | POST | `conversations/<pk>/mark_as_read/` (legacy) | `StaffConversationViewSet` | `mark_as_read` | base + `CanReadStaffChatConversation`, `IsConversationParticipant` | inline | `StaffChatMessage`, `broadcast_read_receipt`, `notification_manager.realtime_staff_chat_conversations_with_unread` |

Where "base" = `IsAuthenticated`, `IsStaffMember`, `IsSameHotel`,
`CanViewStaffChatModule`, as assembled in
[staff_chat/views.py](staff_chat/views.py#L116-L171) (`get_permissions`).

The viewset also exposes `messages` (`@action(detail=True, methods=['get'])`,
[staff_chat/views.py](staff_chat/views.py#L617-L636)) and
`sync_unread_counts` (`@action(detail=False, methods=['post'])`,
[staff_chat/views.py](staff_chat/views.py#L527-L568)) — both reachable through
DRF's automatic action routing if the router is wired, but they are **not**
explicit `path(...)` entries in [staff_chat/urls.py](staff_chat/urls.py), so
their live availability depends on DRF default routing through
`StaffConversationViewSet.as_view()`. Treated as ambient surfaces gated by the
viewset's `get_permissions` (`messages` and `sync_unread_counts` fall through
to the default `list / messages / unread_count / for_forwarding /
bulk_mark_as_read / sync_unread_counts / conversations_with_unread_count`
branch → base + `CanReadStaffChatConversation`).

---

## 3. Current authority checks

For every endpoint, derived from
[staff_chat/permissions.py](staff_chat/permissions.py) and the
`permission_classes` chains above:

- **Authentication** (`IsAuthenticated`): every endpoint.
- **Staff profile presence** (`IsStaffMember`,
  [staff_chat/permissions.py](staff_chat/permissions.py#L8-L20)): every
  endpoint.
- **Same-hotel check** (`IsSameHotel`,
  [staff_chat/permissions.py](staff_chat/permissions.py#L54-L86) — derives
  `staff.hotel.slug == view.kwargs['hotel_slug']` and at object level
  `obj.hotel.id == staff.hotel.id` / `obj.conversation.hotel.id`): every
  endpoint.
- **Module visibility** (`CanViewStaffChatModule` →
  capability `staff_chat.module.view`,
  [staff/permissions.py](staff/permissions.py#L1579-L1583)): every endpoint.
- **Capability gates** (subclasses of `HasCapability` in
  [staff/permissions.py](staff/permissions.py#L1579-L1626)): per row in
  section 2.
- **Participant scoping**:
  - DRF object-permission via `IsConversationParticipant`
    ([staff_chat/permissions.py](staff_chat/permissions.py#L23-L34)) on
    viewset detail actions: `retrieve`, `destroy`, `send_message` (legacy),
    `mark_as_read` (legacy) — applied through
    [staff_chat/views.py](staff_chat/views.py#L131-L171).
  - **Inline** `conversation.participants.filter(id=staff.id).exists()` checks
    in every FBV that references a conversation:
    `send_message` ([views_messages.py](staff_chat/views_messages.py#L150-L156)),
    `get_conversation_messages` (~L300),
    `mark_message_as_read` (~L80),
    `edit_message` ([views_messages.py](staff_chat/views_messages.py#L391-L398)),
    `delete_message` ([views_messages.py](staff_chat/views_messages.py#L450-L460)),
    `add_reaction`, `remove_reaction`, `forward_message`
    ([views_messages.py](staff_chat/views_messages.py#L862-L878),
    L1056-L1062, L1118-L1129),
    `upload_attachments`, `delete_attachment`, `get_attachment_url`
    ([views_attachments.py](staff_chat/views_attachments.py#L75-L82),
    L260-L267, L385-L392).
- **Ownership / message-sender check**:
  - `IsMessageSender` ([staff_chat/permissions.py](staff_chat/permissions.py#L37-L51))
    — class exists but is **not** wired into any `permission_classes` chain
    in `urls.py` / views.
  - `CanDeleteMessage` ([staff_chat/permissions.py](staff_chat/permissions.py#L114-L142))
    — also not chained; instead `delete_message` performs the equivalent
    logic inline using `has_capability('staff_chat.conversation.moderate')`.
  - `edit_message` enforces sender-only inline at
    [views_messages.py](staff_chat/views_messages.py#L385-L389).
  - `upload_attachments` enforces sender-only when attaching to an existing
    message inline at
    [views_attachments.py](staff_chat/views_attachments.py#L130-L137).
  - `delete_attachment` enforces sender-only inline plus
    `has_capability('staff_chat.conversation.moderate')` override and the
    own-attachment `has_capability('staff_chat.attachment.delete')` check
    ([views_attachments.py](staff_chat/views_attachments.py#L268-L283)).
- **`CanManageConversation`** ([staff_chat/permissions.py](staff_chat/permissions.py#L89-L111))
  — class exists but is **not** chained anywhere; it references
  `staff_chat.conversation.moderate`. Functionally dead.
- **No** role-string, tier, `access_level`, nav-slug, `IsAdminTier`,
  `IsSuper`, or `department.slug` gate appears anywhere in
  `staff_chat/views*.py` or `staff_chat/permissions.py`. The four hits for
  `role.slug` / `department.slug` in
  [staff_chat/serializers.py](staff_chat/serializers.py#L71-L80) and
  [staff_chat/serializers_staff.py](staff_chat/serializers_staff.py#L107-L113)
  are **serializer output fields**, not gating logic.
- The [staff_chat/views.py](staff_chat/views.py#L27-L34) `_DenyAll` class is
  used to hard-deny `update` / `partial_update` on `StaffConversation`.

All authority is therefore: authentication + staff profile + same-hotel +
module visibility capability + per-action capability + participant scope
(class on viewset detail actions, inline elsewhere) + sender-or-moderator
ownership for edits/deletes (inline).

---

## 4. Participant-scope audit

Derived only from code paths above.

| Operation | Who can perform it (per code) | Enforcement |
|-----------|-------------------------------|-------------|
| Read conversation list | Same-hotel staff with `staff_chat.conversation.read`; queryset is filtered to `participants=staff` ([views.py](staff_chat/views.py#L173-L196)) | Capability + queryset filter (no object lookup) |
| Read a specific conversation (`retrieve`) | Same-hotel staff with `staff_chat.conversation.read` **and** is a participant | `CanReadStaffChatConversation` + `IsConversationParticipant` |
| Create conversation | Same-hotel staff with `staff_chat.conversation.create`; participant validation enforces all participant_ids belong to same hotel and are active ([views.py](staff_chat/views.py#L221-L238)) | Capability + same-hotel filter on participants |
| Update conversation (PUT/PATCH) | **Nobody** — `_DenyAll` returns 403 unconditionally | `_DenyAll` |
| Delete conversation (`destroy`) | Same-hotel participant with `staff_chat.conversation.delete` | `CanReadStaffChatConversation` + `IsConversationParticipant` + `CanDeleteStaffChatConversation` |
| Read messages | Same-hotel staff with `staff_chat.conversation.read`; inline check requires participant of the conversation | Capability + inline `participants.filter(id=staff.id).exists()` |
| Send message | Same-hotel staff with `staff_chat.message.send`; inline participant check | Capability + inline participant check |
| Edit message | Sender only — must be a participant and `staff.id == message.sender.id`; capability `staff_chat.message.send` | `CanSendStaffChatMessage` + inline sender check + inline participant check |
| Soft-delete own message | Same-hotel staff with `staff_chat.conversation.read`; inline participant check; sender-only branch | `CanReadStaffChatConversation` + inline participant + inline sender check |
| Soft-delete other's message | Same-hotel participant **with** `staff_chat.conversation.moderate` | inline `has_capability('staff_chat.conversation.moderate')` |
| Hard-delete own message | Sender + `?hard_delete=true` (no extra cap required for own) — see [views_messages.py](staff_chat/views_messages.py#L478-L490) | inline sender check |
| Hard-delete other's message | Participant with `staff_chat.conversation.moderate` | inline cap check |
| Upload attachment (new message) | Same-hotel participant with `staff_chat.attachment.upload` | `CanUploadStaffChatAttachment` + inline participant |
| Upload attachment to existing message | Same-hotel participant with `staff_chat.attachment.upload` AND `message.sender.id == staff.id` | capability + inline participant + inline sender-only |
| Delete own attachment | Same-hotel participant + `staff_chat.attachment.delete` cap | inline participant + inline cap |
| Delete other's attachment | Same-hotel participant + `staff_chat.conversation.moderate` cap | inline participant + inline cap |
| Get attachment URL | Same-hotel participant with `staff_chat.conversation.read` | `CanReadStaffChatConversation` + inline participant |
| Add / remove reaction | Same-hotel participant with `staff_chat.reaction.manage` | `CanManageStaffChatReaction` + inline participant |
| Forward message | Same-hotel staff with `staff_chat.message.send`, must be participant of source conversation; per target conversation, must be participant of that conversation too ([views_messages.py](staff_chat/views_messages.py#L1191-L1199)) | Capability + inline source-participant + inline per-target-participant |
| Mark message as read / mark conversation as read / bulk mark | Same-hotel staff with `staff_chat.conversation.read`; queryset / inline restricts to conversations where `staff` is a participant | Capability + queryset / inline participant |

**Are non-participants blocked?** Yes for every conversation-bound operation,
either via `IsConversationParticipant` (viewset detail actions) or via inline
`participants.filter(id=staff.id).exists()` checks in the FBVs. For list-style
actions, the queryset itself is filtered to `participants=staff`, so a
non-participant cannot enumerate or read.

---

## 5. RBAC gap table

Target capability set used for the audit:

```
staff_chat.module.view
staff_chat.conversation.read
staff_chat.conversation.create
staff_chat.conversation.delete
staff_chat.message.send
staff_chat.conversation.moderate
staff_chat.attachment.upload
staff_chat.attachment.delete
staff_chat.reaction.manage
```

| Endpoint | Current gate | Missing gate | Required capability | Risk |
|----------|--------------|--------------|---------------------|------|
| GET `staff-list/` | base + `CanReadStaffChatConversation` | none | `staff_chat.module.view` + `staff_chat.conversation.read` | low |
| GET `conversations/` | base + `CanReadStaffChatConversation`, queryset filtered to participants | none | `staff_chat.conversation.read` | low |
| POST `conversations/` | base + `CanCreateStaffChatConversation`; same-hotel participant validation | none | `staff_chat.conversation.create` | low |
| GET `conversations/for-forwarding/` | base + `CanReadStaffChatConversation`; queryset filtered to participants | none | `staff_chat.conversation.read` | low |
| GET `conversations/unread-count/` | base + `CanReadStaffChatConversation`; queryset filtered to participants | none | `staff_chat.conversation.read` | low |
| GET `conversations/conversations-with-unread-count/` | same as above | none | `staff_chat.conversation.read` | low |
| POST `conversations/bulk-mark-as-read/` | base + `CanReadStaffChatConversation`; per-conversation queryset enforces `participants=staff` | none | `staff_chat.conversation.read` | low |
| POST `conversations/sync-unread-counts/` (action) | base + `CanReadStaffChatConversation`; queryset enforces `participants=staff` | none | `staff_chat.conversation.read` | low |
| GET `conversations/<pk>/` | base + `CanReadStaffChatConversation` + `IsConversationParticipant` | none | `staff_chat.conversation.read` | low |
| PUT/PATCH `conversations/<pk>/` | base + `_DenyAll` | none — fully denied. No `staff_chat.conversation.update` capability is defined; the surface is parked. | n/a (denied) | low |
| DELETE `conversations/<pk>/` | base + `CanReadStaffChatConversation` + `IsConversationParticipant` + `CanDeleteStaffChatConversation` | none | `staff_chat.conversation.delete` | low |
| POST `conversations/<id>/send-message/` | full chain incl. `CanSendStaffChatMessage`; inline participant | none | `staff_chat.message.send` | low |
| GET `conversations/<id>/messages/` | base + `CanReadStaffChatConversation`; inline participant | none | `staff_chat.conversation.read` | low |
| POST `messages/<id>/mark-as-read/` | base + `CanReadStaffChatConversation`; inline participant | none | `staff_chat.conversation.read` | low |
| PATCH `messages/<id>/edit/` | base + `CanSendStaffChatMessage`; inline sender check; inline participant check | **`CanReadStaffChatConversation` is not chained** on `edit_message`; participant scoping is enforced inline only. | `staff_chat.message.send` | low (caps still enforced) — minor consistency nit |
| DELETE `messages/<id>/delete/` | base + `CanReadStaffChatConversation`; inline participant; inline sender-or-`staff_chat.conversation.moderate` | Moderate / hard-delete authority is enforced via `has_capability(...)` rather than chaining `CanModerateStaffChatMessage`. Class `CanModerateStaffChatMessage` exists but is unused. | `staff_chat.conversation.moderate` (for non-owner / hard delete) | low |
| POST `messages/<id>/react/` | base + `CanReadStaffChatConversation` + `CanManageStaffChatReaction`; inline participant | none | `staff_chat.reaction.manage` | low |
| DELETE `messages/<id>/react/<emoji>/` | base + `CanReadStaffChatConversation` + `CanManageStaffChatReaction`; inline participant | none | `staff_chat.reaction.manage` | low |
| POST `messages/<id>/forward/` | base + `CanReadStaffChatConversation` + `CanSendStaffChatMessage`; inline source-participant + per-target-participant | none | `staff_chat.message.send` | low |
| POST `conversations/<id>/upload/` | base + `CanReadStaffChatConversation` + `CanUploadStaffChatAttachment`; inline participant; inline sender-only when attaching to existing | none | `staff_chat.attachment.upload` | low |
| DELETE `attachments/<id>/delete/` | base + `CanReadStaffChatConversation`; inline participant; inline sender → `staff_chat.attachment.delete`; non-sender → `staff_chat.conversation.moderate` | `CanDeleteStaffChatAttachment` class exists but is **not** chained — the cap is enforced imperatively. | `staff_chat.attachment.delete` / `staff_chat.conversation.moderate` | low |
| GET `attachments/<id>/url/` | base + `CanReadStaffChatConversation`; inline participant | none | `staff_chat.conversation.read` | low |
| POST `conversations/<pk>/send_message/` (legacy) | base + `CanReadStaffChatConversation` + `IsConversationParticipant` + `CanSendStaffChatMessage` | none | `staff_chat.message.send` | low |
| POST `conversations/<pk>/mark_as_read/` (legacy) | base + `CanReadStaffChatConversation` + `IsConversationParticipant` | none | `staff_chat.conversation.read` | low |

**Net result.** No endpoint is unprotected. No legacy authority pattern
(role/tier/nav/access_level/department slug) is in use. Remaining items are
**stylistic / consistency**, not security gaps:

- `IsMessageSender`, `CanDeleteMessage`, `CanManageConversation`,
  `CanModerateStaffChatMessage`, `CanDeleteStaffChatAttachment` are defined
  but not chained anywhere; ownership/moderation is enforced inline. Either
  remove the unused classes or wire them in for consistency with the rest of
  the chain.
- `edit_message` chain omits `CanReadStaffChatConversation` (it goes module
  → `CanSendStaffChatMessage`). Functionally fine because `message.send` is
  granted only with `conversation.read` in the preset, but inconsistent with
  every other message endpoint.

---

## 6. Capability / registry status

Verified directly from registry source:

- **Capability catalog** ([staff/capability_catalog.py](staff/capability_catalog.py#L86-L111)):
  the nine staff_chat caps are declared as module-level constants and
  every one of them appears in `CANONICAL_CAPABILITIES`
  ([staff/capability_catalog.py](staff/capability_catalog.py#L506-L514)).
- **Module policy** ([staff/module_policy.py](staff/module_policy.py#L223-L235)):
  `MODULE_POLICY['staff_chat']` registers `view_capability`,
  `read_capability`, and 8 actions
  (`conversation_read`, `conversation_create`, `conversation_delete`,
  `message_send`, `message_moderate`, `attachment_upload`,
  `attachment_delete`, `reaction_manage`). All keys map to `STAFF_CHAT_*`
  constants.
- **Preset / role-capability bundles**:
  - `_STAFF_CHAT_BASE` ([staff/capability_catalog.py](staff/capability_catalog.py#L725-L742)):
    `{module.view, conversation.read, conversation.create, message.send,
    attachment.upload, attachment.delete, reaction.manage}`. Granted broadly
    (every tier picks it up per the bundle structure for staff chat).
  - `_SUPERVISOR_AUTHORITY` ([staff/capability_catalog.py](staff/capability_catalog.py#L696-L703)):
    adds `STAFF_CHAT_CONVERSATION_MODERATE` and
    `STAFF_CHAT_CONVERSATION_DELETE`.
- **Permission classes** ([staff/permissions.py](staff/permissions.py#L1579-L1626)):
  9 `HasCapability` subclasses, one per cap; visibility / read classes set
  `safe_methods_bypass = False`. All 9 are imported & used (except
  `CanModerateStaffChatMessage` and `CanDeleteStaffChatAttachment`, see §5).
- **Validation helpers**: `validate_module_policy` / `validate_preset_maps`
  exist in the staff module (called from
  [staff/permissions.py](staff/permissions.py) ecosystem). The staff_chat
  policy block is structured identically to the bookings / housekeeping /
  rooms / chat blocks already validated by Wave 2A and Phase 6, so it is
  consumed by the same registry checks.

**Conclusion: staff_chat is already fully registered in the canonical RBAC
registry — caps, module policy, presets and permission classes all present
and consistent with one another.**

---

## 7. Implementation recommendation

Wave 2B's stated objective (introduce canonical RBAC for staff_chat) is
already satisfied in code. There is **no security-gap implementation work
required** in this pass.

The only optional follow-ups are **non-blocking cleanup**:

1. **Decide on the unused permission classes.** Either:
   - delete `IsMessageSender`, `CanDeleteMessage`, `CanManageConversation`
     from [staff_chat/permissions.py](staff_chat/permissions.py) (they are
     superseded by inline checks against `has_capability(...)` and
     `message.sender.id`), and / or
   - delete `CanModerateStaffChatMessage` and `CanDeleteStaffChatAttachment`
     from [staff/permissions.py](staff/permissions.py#L1608-L1621) if you
     keep the imperative pattern; **or** wire them into the `delete_message`
     and `delete_attachment` chains and remove the redundant inline
     `has_capability()` calls.

2. **Optional consistency fix on `edit_message`.** Add
   `CanReadStaffChatConversation` to the `permission_classes` of
   [staff_chat/views_messages.py](staff_chat/views_messages.py#L355-L360) so
   every conversation-bound surface chains read before mutate. Functional
   parity with current behaviour is preserved by the preset bundles.

3. **Optional: convert inline participant checks to a single
   `IsConversationParticipant` object permission** by giving the FBVs an
   object via `get_object_or_404` + `self.check_object_permissions(...)`.
   Pure refactor — no authority change. Files affected:
   `views_messages.py`, `views_attachments.py`. No URL changes, no preset
   changes.

If any of the cleanup items are chosen, the change set would be:

- Files to modify: `staff_chat/permissions.py`, `staff_chat/views_messages.py`,
  `staff_chat/views_attachments.py`, possibly `staff/permissions.py`.
- Permission classes to update: none new; either delete unused classes or
  chain `CanModerateStaffChatMessage` / `CanDeleteStaffChatAttachment`.
- Endpoints to change: `messages/<id>/edit/`, `messages/<id>/delete/`,
  `attachments/<id>/delete/` (chain consistency only).
- Ownership rules: unchanged — sender-only for edits and own-soft-delete;
  `staff_chat.conversation.moderate` for cross-sender / hard delete.
- Participant rules: unchanged — `IsConversationParticipant` (object) on
  viewset detail actions; inline filter on FBVs (or refactor to object
  permission, see item 3).
- No model, migration, serializer, registry, preset, or
  `module_policy.py` changes are required.

---

## 8. Validation commands to run later

If any of §7's optional cleanups are applied, re-run:

```powershell
# Static / import / URL sanity
python manage.py check

# Registry contract checks (these are the canonical Wave 2 acceptance gates)
python manage.py shell -c "from staff.module_policy import validate_module_policy; print(validate_module_policy())"
python manage.py shell -c "from staff.capability_catalog import validate_preset_maps; print(validate_preset_maps())"

# Legacy-pattern scan (must remain 0 hits inside staff_chat/)
# Run from repo root:
#   PowerShell: Get-ChildItem -Recurse staff_chat -Include *.py | Select-String -Pattern 'role\.slug|tier|HasNavPermission|IsAdminTier|IsSuper|department\.slug'
# Currently 4 hits, all serializer output fields (serializers.py / serializers_staff.py) — no gating.
```

Both `validate_module_policy()` and `validate_preset_maps()` are expected to
return `[]` (empty list = clean) given the current state of
[staff/module_policy.py](staff/module_policy.py#L223-L235) and
[staff/capability_catalog.py](staff/capability_catalog.py#L725-L742).
