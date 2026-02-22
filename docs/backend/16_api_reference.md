# API Reference

> Complete endpoint inventory grouped by domain. Derived from URL files.
> 
> **Legend:** 🔓 AllowAny | 🔑 TokenAuth+IsAuthenticated | 🏨 IsStaffOfHotel | 👑 IsAdminUser | 🎫 GuestToken (custom)

---

## Public Zone — `/api/public/`

**Auth:** 🔓 AllowAny on all endpoints  
**Source:** `public_urls.py`, `hotel/public_urls.py`

### Hotel Discovery

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| GET | `/api/public/presets/` | `PublicPresetsView` | Style presets |
| GET | `/api/public/hotels/` | `HotelPublicListView` | Search: q, city, country, tags, hotel_type, sort |
| GET | `/api/public/hotels/filters/` | `HotelFilterOptionsView` | Available filter options |
| GET | `/api/public/hotel/{slug}/page/` | `HotelPublicPageView` | Full public page with sections |

### Booking Flow

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| GET | `/api/public/hotel/{slug}/availability/` | `HotelAvailabilityView` | Check room availability for dates |
| POST | `/api/public/hotel/{slug}/pricing/quote/` | `HotelPricingQuoteView` | Calculate pricing |
| POST | `/api/public/hotel/{slug}/bookings/` | `HotelBookingCreateView` | Create booking (→ PENDING_PAYMENT) |
| GET | `/api/public/hotel/{slug}/room-bookings/{id}/` | `PublicRoomBookingDetailView` | Booking details |

### Payments (Stripe)

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| POST | `/api/public/hotel/{slug}/room-bookings/{id}/payment/` | `CreatePaymentSessionView` | Create Stripe checkout session |
| POST | `/api/public/hotel/{slug}/room-bookings/{id}/payment/session/` | `CreatePaymentSessionView` | Alias |
| GET | `/api/public/hotel/{slug}/room-bookings/{id}/payment/verify/` | `VerifyPaymentView` | Verify payment status |
| POST | `/api/public/hotel/room-bookings/stripe-webhook/` | `StripeWebhookView` | Stripe webhook (signature verified) |

### Booking Management (Guest-Facing)

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| GET | `/api/public/hotels/{slug}/booking/status/{id}/` | `BookingStatusView` | Public booking status |
| POST | `/api/public/booking/validate-token/` | `ValidateBookingManagementTokenView` | Validate mgmt token |
| POST | `/api/public/booking/cancel/` | `CancelBookingView` | Guest-initiated cancel |
| GET | `/api/public/hotels/{slug}/cancellation-policy/` | `HotelCancellationPolicyView` | Policy details |
| POST | `/api/public/hotel/{slug}/room-bookings/{id}/cancel/` | `BookingStatusView` | Cancel via booking ID |

### Pre-Checkin

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| GET/POST | `/api/public/hotels/{slug}/precheckin/validate-token/` | `ValidatePrecheckinTokenView` | Token validation |
| POST | `/api/public/hotels/{slug}/precheckin/submit/` | `SubmitPrecheckinView` | Submit pre-checkin data |

### Survey

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| GET/POST | `/api/public/hotels/{slug}/survey/validate-token/` | `ValidateSurveyTokenView` | Token validation |
| POST | `/api/public/hotels/{slug}/survey/submit/` | `SubmitSurveyView` | Submit survey response |

---

## Guest Zone — `/api/guest/`

**Auth:** 🔓 AllowAny (🎫 GuestToken validated internally)  
**Source:** `guest_urls.py`

### Guest Portal

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| GET | `/api/guest/context/` | `GuestContextView` | 🎫 | Booking context via token |
| GET | `/api/guest/hotels/{slug}/room-service/` | `GuestRoomServiceView` | 🎫 | Room service context (in-house only) |

### Hotel Info (Guest-Facing)

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| GET | `/api/guest/hotels/{slug}/` | `guest_home()` | Hotel info with booking options |
| GET | `/api/guest/hotels/{slug}/rooms/` | `guest_rooms()` | Room types with photos |
| GET | `/api/guest/hotels/{slug}/amenities/` | `guest_amenities()` | Hotel amenities |
| GET | `/api/guest/hotels/{slug}/availability/` | `check_availability()` | Room availability |
| POST | `/api/guest/hotels/{slug}/bookings/` | `create_booking()` | Create booking |
| GET | `/api/guest/hotels/{slug}/cancellation-policy/` | `cancellation_policy_details()` | Policy info |
| POST | `/api/guest/hotels/{slug}/pricing/quote/` | `guest_pricing_quote()` | Pricing |

### Guest Chat (Canonical)

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| GET | `/api/guest/hotels/{slug}/chat/context/` | `CanonicalGuestChatContextView` | 🎫 Chat context |
| POST | `/api/guest/hotels/{slug}/chat/send/` | `CanonicalGuestChatSendMessageView` | 🎫 Send message |
| POST | `/api/guest/hotels/{slug}/chat/pusher-auth/` | `CanonicalGuestChatPusherAuthView` | 🎫 Pusher channel auth |

### Guest Room Service

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| GET | `/api/guest/hotels/{slug}/room/{number}/menu/` | `RoomServiceItemViewSet` | Menu items |
| GET/POST | `/api/guest/hotels/{slug}/room-services/orders/` | `OrderViewSet` | List/create orders |

---

## Staff Zone — `/api/staff/`

**Source:** `staff_urls.py` (⚠️ .pyc only), individual app `staff_urls.py` files

### Staff Authentication (No hotel_slug)

| Method | Path | Handler | Auth | Notes |
|--------|------|---------|------|-------|
| POST | `/api/staff/login/` | `StaffLoginView` | 🔓 | Returns token + permissions |
| POST | `/api/staff/{slug}/register/` | `StaffRegisterView` | 🔓 | Reg code + QR token |
| POST | `/api/staff/registration-package/` | `RegistrationPackageView` | 🔑 | Generate reg codes |
| POST | `/api/staff/save-fcm-token/` | `SaveFcmTokenView` | 🔑 | FCM push token |
| POST | `/api/staff/password-reset/` | `PasswordResetView` | 🔓 | Email-based reset |
| POST | `/api/staff/password-reset-confirm/` | `PasswordResetConfirmView` | 🔓 | Confirm reset |
| GET | `/api/staff/users/` | `UserListView` | 👑 | All Django users |
| GET | `/api/staff/users/by-hotel-codes/` | `UsersByHotelCodesView` | 🔑 | Users by reg codes |
| CRUD | `/api/staff/departments/` | `DepartmentViewSet` | 🔑 | Department CRUD |
| CRUD | `/api/staff/roles/` | `RoleViewSet` | 🔑 | Role CRUD |
| CRUD | `/api/staff/navigation-items/` | `NavigationItemViewSet` | 🔑/👑 | Nav items (CUD=superuser) |
| GET | `/api/staff/{id}/permissions/` | `StaffPermissionsView` | 🔑 | Staff nav perms |
| GET | `/api/staff/hotels/{slug}/metadata/` | `StaffMetadataView` | 🔑 | Depts/roles/access_levels |
| GET | `/api/staff/hotels/{slug}/pending-registrations/` | `PendingRegistrationsView` | 🔑 | Unlinked users |
| POST | `/api/staff/hotels/{slug}/create-staff/` | `CreateStaffFromUserView` | 🔑 | Create Staff profile |
| CRUD | `/api/staff/hotels/{slug}/staff/` | `StaffViewSet` | 👑 | Staff CRUD + custom actions |
| GET | `/api/staff/me/` | `StaffMeView` | 🔑 | Current staff profile |

### Room Bookings Management — `/api/staff/hotel/{slug}/room-bookings/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | `/` | `StaffBookingListView` | 🏨 |
| GET | `/{id}/` | `StaffBookingDetailView` | 🏨 |
| POST | `/{id}/confirm/` | `ConfirmBookingView` | 🏨 |
| POST | `/{id}/cancel/` | `CancelBookingView` | 🏨 |
| POST | `/{id}/seen/` | `MarkBookingSeenView` | 🏨 |
| GET/PUT | `/{id}/party/` | `BookingPartyView` | 🏨 |
| PUT | `/{id}/assign-room/` | `SafeRoomAssignmentView` | 🏨 |
| GET | `/{id}/available-rooms/` | `AvailableRoomsView` | 🏨 |
| POST | `/{id}/unassign-room/` | `UnassignRoomView` | 🏨 |
| POST | `/{id}/move-room/` | `MoveRoomView` | 🏨 |
| POST | `/{id}/check-in/` | `StaffCheckInView` | 🏨 |
| POST | `/{id}/check-out/` | `StaffCheckOutView` | 🏨 |
| POST | `/{id}/send-precheckin-link/` | `SendPrecheckinLinkView` | 🏨 |
| POST | `/{id}/send-survey-link/` | `SendSurveyLinkView` | 🏨 |
| POST | `/{id}/accept/` | `AcceptBookingView` | 🏨 |
| POST | `/{id}/decline/` | `DeclineBookingView` | 🏨 |
| POST | `/{id}/overstay/acknowledge/` | `AcknowledgeOverstayView` | 🏨 |
| POST | `/{id}/overstay/extend/` | `ExtendOverstayView` | 🏨 |
| GET | `/{id}/overstay/status/` | `OverstayStatusView` | 🏨 |

### Hotel Settings — `/api/staff/hotel/{slug}/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET/PATCH | `settings/` | `HotelSettingsView` | 🏨 |
| GET/PUT | `access-config/` | `StaffAccessConfigView` | 🏨 |
| GET/POST | `precheckin-config/` | `HotelPrecheckinConfigView` | 🏨 |
| GET/POST | `survey-config/` | `HotelSurveyConfigView` | 🏨 |
| GET | `readiness/` | `HotelReadinessView` | 🏨 |

### Public Page Builder — `/api/staff/hotel/{slug}/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET/POST | `public-page-builder/` | `PublicPageBuilderView` | 🏨 |
| POST | `public-page-builder/bootstrap-default/` | `BootstrapDefaultSectionsView` | 🏨 |
| POST | `public-page-builder/create-section/` | `CreateSectionView` | 🏨 |
| CRUD | `public-page/` | `HotelPublicPageViewSet` | 🏨 |
| CRUD | `public-sections/` | `PublicPageSectionViewSet` | 🏨 |
| CRUD | `public-elements/` | `SectionElementViewSet` | 🏨 |
| CRUD | `public-element-items/` | `ElementItemViewSet` | 🏨 |
| CRUD | `hero-sections/` | `HeroSectionViewSet` | 🏨 |
| CRUD | `gallery-containers/` | `GalleryViewSet` | 🏨 |
| CRUD | `gallery-images/` | `GalleryImageViewSet` | 🏨 |
| CRUD | `list-containers/` | `ListContainerViewSet` | 🏨 |
| CRUD | `cards/` | `CardViewSet` | 🏨 |
| CRUD | `news-items/` | `NewsItemViewSet` | 🏨 |
| CRUD | `content-blocks/` | `ContentBlockViewSet` | 🏨 |
| CRUD | `rooms-sections/` | `RoomsSectionViewSet` | 🏨 |
| CRUD | `presets/` | `PresetViewSet` (ReadOnly) | 🏨 |

### Cancellation Policies & Rate Plans

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET/POST | `/api/staff/hotel/{slug}/cancellation-policies/` | `cancellation_policy_list` | 🏨 |
| GET/PUT/PATCH/DELETE | `/api/staff/hotel/{slug}/cancellation-policies/{id}/` | `cancellation_policy_detail` | 🏨 |
| GET | `/api/staff/hotel/{slug}/cancellation-policies/templates/` | `cancellation_policy_templates` | 🏨 |
| GET/POST | `/api/staff/hotel/{slug}/rate-plans/` | `rate_plan_list` | 🏨 |
| GET/PUT/PATCH | `/api/staff/hotel/{slug}/rate-plans/{id}/` | `rate_plan_detail` | 🏨 |
| DELETE | `/api/staff/hotel/{slug}/rate-plans/{id}/delete/` | `rate_plan_delete` | 🏨 |

### Rooms — `/api/staff/hotel/{slug}/rooms/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| CRUD | `rooms/` | `RoomViewSet` | 🏨 |
| CRUD | `room-types/` | `RoomTypeViewSet` | 🏨 |
| POST | `rooms/bulk-create/` | `bulk_create_rooms` | 🏨 |
| POST | `rooms/{id}/checkout/` | `staff_room_checkout` | 🏨 |
| POST | `rooms/{id}/start-cleaning/` | `start_cleaning` | 🏨 |
| POST | `rooms/{id}/mark-cleaned/` | `mark_cleaned` | 🏨 |
| POST | `rooms/{id}/inspect/` | `inspect_room` | 🏨 |
| POST | `rooms/{id}/mark-maintenance/` | `mark_maintenance` | 🏨 |
| POST | `rooms/{id}/complete-maintenance/` | `complete_maintenance` | 🏨 |
| GET | `rooms/turnover/` | `turnover_rooms` | 🏨 |
| GET | `rooms/turnover/stats/` | `turnover_stats` | 🏨 |

### Housekeeping — `/api/staff/hotel/{slug}/housekeeping/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | `dashboard/` | `HousekeepingDashboardViewSet` | 🏨 |
| CRUD | `tasks/` | `HousekeepingTaskViewSet` | 🏨 |
| POST | `tasks/{id}/assign/` | TaskViewSet action | 🏨 |
| POST | `tasks/{id}/start/` | TaskViewSet action | 🏨 |
| POST | `tasks/{id}/complete/` | TaskViewSet action | 🏨 |
| POST | `room-status/{id}/change/` | `RoomStatusViewSet` | 🏨 |
| POST | `room-status/{id}/override/` | `RoomStatusViewSet` | 🏨 |
| GET | `room-status/{id}/history/` | `RoomStatusViewSet` | 🏨 |

### Guests — `/api/staff/hotel/{slug}/guests/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | `/` | `GuestViewSet.list` | 🏨 |
| GET/PUT | `/{id}/` | `GuestViewSet.retrieve/update` | 🏨 |

### Chat (Guest↔Staff) — `/api/staff/hotel/{slug}/chat/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | `conversations/` | `get_conversations` | 🏨 |
| GET/POST | `conversations/from-room/{number}/` | `get_or_create_conversation` | 🏨 |
| GET | `conversations/{id}/messages/` | `get_messages` | 🏨 |
| POST | `conversations/{id}/messages/send/` | `send_message` | 🏨 |
| POST | `conversations/{id}/mark-read/` | `mark_messages_as_read` | 🏨 |
| POST | `conversations/{id}/assign-staff/` | `assign_staff` | 🏨 |
| PUT | `messages/{id}/update/` | `update_message` | 🏨 |
| DELETE | `messages/{id}/delete/` | `delete_message` | 🏨 |
| POST | `conversations/{id}/upload-attachment/` | `upload_attachment` | 🏨 |
| DELETE | `attachments/{id}/delete/` | `delete_attachment` | 🏨 |

### Staff Chat — `/api/staff/hotel/{slug}/staff_chat/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET | `staff-list/` | `StaffListView` | 🏨 |
| GET/POST | `conversations/` | ConversationView list/create | 🏨 |
| GET | `conversations/for-forwarding/` | `ForForwardingView` | 🏨 |
| CRUD | `conversations/{pk}/` | ConversationView detail | 🏨 |
| POST | `conversations/{id}/send-message/` | `SendMessageView` | 🏨 |
| GET | `conversations/{id}/messages/` | `MessageListView` | 🏨 |
| POST | `conversations/bulk-mark-as-read/` | `BulkMarkReadView` | 🏨 |
| POST | `messages/{id}/mark-as-read/` | `MarkAsReadView` | 🏨 |
| PUT | `messages/{id}/edit/` | `EditMessageView` | 🏨 |
| DELETE | `messages/{id}/delete/` | `DeleteMessageView` | 🏨 |
| POST | `messages/{id}/react/` | `AddReactionView` | 🏨 |
| DELETE | `messages/{id}/react/{emoji}/` | `RemoveReactionView` | 🏨 |
| POST | `messages/{id}/forward/` | `ForwardMessageView` | 🏨 |
| POST | `conversations/{id}/upload/` | `UploadAttachmentView` | 🏨 |
| DELETE | `attachments/{id}/delete/` | `DeleteAttachmentView` | 🏨 |

### Attendance — `/api/staff/hotel/{slug}/attendance/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| CRUD | `clock-logs/` | `ClockLogViewSet` | 🏨 |
| CRUD | `roster-periods/` | `RosterPeriodViewSet` | 🏨 |
| POST | `roster-periods/{pk}/add-shift/` | action | 🏨 |
| POST | `roster-periods/{pk}/finalize/` | action | 🏨 |
| GET | `roster-periods/{pk}/export-pdf/` | action | 🏨 |
| CRUD | `shifts/` | `StaffRosterViewSet` | 🏨 |
| POST | `shifts/bulk-save/` | action | 🏨 |
| GET | `shifts/daily-pdf/` | action | 🏨 |
| CRUD | `shift-locations/` | `ShiftLocationViewSet` | 🏨 |
| CRUD | `daily-plans/` | `DailyPlanViewSet` | 🏨 |
| POST | `face-management/register-face/` | `FaceRecognitionViewSet` | 🏨 |
| POST | `face-management/face-clock-in/` | action | 🏨 |
| POST | `face-management/toggle-break/` | action | 🏨 |
| GET | `face-management/audit-logs/` | action | 🏨 |
| GET | `roster-analytics/staff-summary/` | `AttendanceAnalyticsViewSet` | 🏨 |
| POST | `shift-copy/copy-roster-day-all/` | `ShiftCopyViewSet` | 🏨 |

### Entertainment — `/api/staff/hotel/{slug}/entertainment/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| CRUD | `games/` | `GameViewSet` (ReadOnly) | 🔓 |
| CRUD | `memory-cards/` | `MemoryCardViewSet` (ReadOnly) | 🔓 |
| CRUD | `memory-sessions/` | `MemorySessionViewSet` | 🔓 |
| CRUD | `tournaments/` | `MemoryTournamentViewSet` | 🔓 |
| CRUD | `quiz-categories/` | `QuizCategoryViewSet` (ReadOnly) | 🔓 |
| CRUD | `quiz-sessions/` | `QuizSessionViewSet` | 🔓 |
| CRUD | `quiz-tournaments/` | `QuizTournamentViewSet` (ReadOnly) | 🔓 |

### Room Services — `/api/staff/hotel/{slug}/room-services/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| CRUD | `room-service-items/` | `StaffRoomServiceItemViewSet` | 🏨 |
| CRUD | `breakfast-items/` | `StaffBreakfastItemViewSet` | 🏨 |
| CRUD | `orders/` | `OrderViewSet` | 🏨 |

### Restaurant Bookings — `/api/staff/hotel/{slug}/service-bookings/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| CRUD | `restaurants/` | `RestaurantViewSet` | 🏨 |
| CRUD | `bookings/` | `BookingViewSet` | 🏨 |
| CRUD | `categories/` | `CategoryViewSet` | 🏨 |
| GET/POST | `dinner-bookings/` | `DinnerBookingListCreateView` | 🏨 |
| CRUD | `blueprint/` | `BlueprintViewSet` | 🏨 |
| CRUD | `dining-table/` | `DiningTableViewSet` | 🏨 |
| GET | `available-tables/{slug}/` | `available_tables` | 🏨 |
| POST | `assign/{slug}/` | `assign_guest_to_table` | 🔓 |
| POST | `mark-seen/` | `mark_bookings_seen` | 🏨 |

### Maintenance — `/api/staff/hotel/{slug}/maintenance/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| CRUD | `requests/` | `MaintenanceRequestViewSet` | 🔑 |
| CRUD | `comments/` | `MaintenanceCommentViewSet` | 🔓 |
| CRUD | `photos/` | `MaintenancePhotoViewSet` | 🔑 |

### Stock Tracker — `/api/staff/hotel/{slug}/stock_tracker/`

*Extensive — 60+ endpoints. Key groups:*

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| CRUD | `items/` | `StockItemViewSet` | 🏨 |
| GET | `items/profitability/` | action | 🏨 |
| GET | `items/low-stock/` | action | 🏨 |
| CRUD | `categories/` | `StockCategoryViewSet` | 🏨 |
| CRUD | `periods/` | `StockPeriodViewSet` | 🏨 |
| POST | `periods/{pk}/approve-and-close/` | action | 🏨 |
| POST | `periods/{pk}/reopen/` | action | 🏨 |
| CRUD | `stocktakes/` | `StocktakeViewSet` | 🏨 |
| POST | `stocktakes/{pk}/populate/` | action | 🏨 |
| POST | `stocktakes/{pk}/approve/` | action | 🏨 |
| GET | `stocktakes/{pk}/download-pdf/` | action | 🏨 |
| GET | `stocktakes/{pk}/download-excel/` | action | 🏨 |
| CRUD | `stocktake-lines/` | `StocktakeLineViewSet` | 🏨 |
| POST | `stocktake-lines/voice-command/` | `VoiceCommandView` | 🔑 |
| POST | `stocktake-lines/voice-command/confirm/` | `VoiceCommandConfirmView` | 🔑 |
| CRUD | `cocktails/` | `CocktailViewSet` | 🏨 |
| CRUD | `sales/` | `SaleViewSet` | 🏨 |
| CRUD | `movements/` | `StockMovementViewSet` | 🏨 |
| GET | `compare/categories/` | `ComparisonCategoriesView` | 🏨 |
| GET | `kpi-summary/` | `KPISummaryView` | 🏨 |

### Hotel Info — `/api/staff/hotel/{slug}/hotel_info/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| CRUD | `hotelinfo/` | `HotelInfoCategoryViewSet` | 🔑/🔓 |
| CRUD | `categories/` | `HotelInfoCategoryViewSet` | 🔑/🔓 |
| GET/POST | `good-to-know/` | `GoodToKnowView` | 🔑 |

### Home (Noticeboard) — `/api/staff/hotel/{slug}/home/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| CRUD | `posts/` | `PostViewSet` | 🔑 |
| CRUD | `posts/{pk}/comments/` | `CommentViewSet` | 🔑 |
| CRUD | `posts/{pk}/comments/{pk}/replies/` | `ReplyViewSet` | 🔑 |

### Common — `/api/staff/hotel/{slug}/common/`

| Method | Path | Handler | Auth |
|--------|------|---------|------|
| GET/POST/PUT/PATCH | `theme/` | `ThemeSettingsView` | 🔑 |

---

## Direct-Mount Endpoints (Legacy)

| Mount | Target | Notes |
|-------|--------|-------|
| `/api/hotel/` | `hotel.urls` | Admin hotel CRUD (👑 superuser) |
| `/api/chat/` | `chat.urls` | Legacy chat access |
| `/api/room_services/` | `room_services.urls` | Legacy room service |
| `/api/bookings/` | `bookings.urls` | Legacy restaurant bookings |
| `/api/notifications/pusher/auth/` | `PusherAuthView` | Dual-mode Pusher auth |
| `/api/notifications/save-fcm-token/` | `SaveFcmTokenView` | FCM token save |
| `/api/hotels/{slug}/face-config/` | `HotelFaceConfigView` | 🔓 Face recognition config |
