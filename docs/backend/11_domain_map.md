# Domain Map

> Maps each Django app / module to its business domain and responsibilities.

## Domain → App Mapping

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HOTEL PLATFORM                               │
├──────────────┬──────────────┬──────────────┬────────────────────────┤
│  BOOKING &   │  OPERATIONS  │ COMMUNICATION│   ENGAGEMENT &         │
│  REVENUE     │              │              │   ANALYTICS            │
├──────────────┼──────────────┼──────────────┼────────────────────────┤
│ hotel        │ rooms        │ chat         │ entertainment          │
│ room_bookings│ housekeeping │ staff_chat   │ attendance             │
│ bookings     │ maintenance  │ notifications│ stock_tracker          │
│ guests       │ room_services│              │ voice_recognition      │
│              │ hotel_info   │              │ home (noticeboard)     │
│              │ staff        │              │                        │
│              │ common       │              │                        │
└──────────────┴──────────────┴──────────────┴────────────────────────┘
```

## Detailed App Responsibilities

### Booking & Revenue Domain

| App | Responsibility | Key Models | Files |
|-----|---------------|------------|-------|
| **hotel** | Core hotel entity; room booking lifecycle; payment processing; public page CMS; cancellation policies; rate plans; guest tokens; pre-checkin; surveys; overstay management | `Hotel`, `RoomBooking`, `GuestBookingToken`, `CancellationPolicy`, `PricingQuote`, `HotelPublicPage`, `SurveyResponse`, `OverstayIncident`, `BookingExtension` (+ 20 more) | `hotel/models.py` (3042 lines) |
| **room_bookings** | Orchestration layer for room booking lifecycle — no own models. Services for room assignment, checkout, overstay detection, room moves | *(uses hotel.models)* | `room_bookings/services/` |
| **bookings** | Restaurant/dining reservation system with floor plans and table management | `Restaurant`, `DinnerBooking`, `Blueprint`, `DiningTable`, `BookingTable` | `bookings/models.py` |
| **guests** | Guest profile records (walk-in or booking-linked) | `Guest` | `guests/models.py` |
| **apps/booking/services** | Pure business rules for booking deadlines and stay-time calculations | *(no models)* | `apps/booking/services/booking_deadlines.py`, `stay_time_rules.py` |

### Operations Domain

| App | Responsibility | Key Models | Files |
|-----|---------------|------------|-------|
| **rooms** | Physical room inventory, room types, rate plans, promotions, daily pricing, inventory overrides | `Room`, `RoomType`, `RatePlan`, `RoomTypeRatePlan`, `DailyRate`, `Promotion`, `RoomTypeInventory` | `rooms/models.py` |
| **housekeeping** | Room status state machine (canonical), task management, audit trail, RBAC policies | `RoomStatusLog`, `HousekeepingTask` | `housekeeping/models.py`, `housekeeping/services.py` |
| **room_services** | In-room dining: menu items + guest orders (room service & breakfast) | `RoomServiceItem`, `Order`, `OrderItem`, `BreakfastItem`, `BreakfastOrder`, `BreakfastOrderItem` | `room_services/models.py` |
| **maintenance** | Maintenance request tracking with comments and photos | `MaintenanceRequest`, `MaintenanceComment`, `MaintenancePhoto` | `maintenance/models.py` |
| **hotel_info** | Hotel information pages, categories, events, good-to-know items, QR codes | `HotelInfoCategory`, `HotelInfoCategoryQR`, `HotelInfoEvent`, `GoodToKnow` | `hotel_info/models.py` |
| **staff** | Staff profiles, auth tokens, registration codes, departments, roles, navigation permissions | `Staff`, `RegistrationCode`, `UserProfile`, `Department`, `Role`, `NavigationItem` | `staff/models.py` |
| **common** | Shared theme/color config, hotel-scoped mixins, Cloudinary upload utilities | `ThemeSettings` | `common/models.py`, `common/mixins.py` |

### Communication Domain

| App | Responsibility | Key Models | Files |
|-----|---------------|------------|-------|
| **chat** | Guest ↔ staff conversations (room-scoped), message lifecycle, file attachments | `Conversation`, `RoomMessage`, `RoomMessageReadReceipt`, `MessageAttachment` | `chat/models.py` |
| **staff_chat** | Staff ↔ staff messaging — 1:1 and group, reactions, forwarding, mentions | `StaffConversation`, `StaffMessage`, `StaffMessageAttachment`, `MessageReaction` | `staff_chat/models.py` |
| **notifications** | Unified notification hub — delegates to Pusher (realtime), FCM (push), SMTP (email) | *(no models — misplaced `SaveFcmTokenView` in models.py)* | `notifications/notification_manager.py` (2417 lines) |

### Engagement & Analytics Domain

| App | Responsibility | Key Models | Files |
|-----|---------------|------------|-------|
| **entertainment** | Guest games — memory match, quiz (Guessticulator), tournaments, achievements, leaderboards | `Game`, `MemoryCard`, `MemorySession`, `Tournament`, `QuizCategory`, `QuizQuestion`, `QuizSession` (+ 10 more) | `entertainment/models.py` (1499 lines) |
| **attendance** | Staff clock-in/out, roster periods, shift planning, face recognition, analytics, daily plans | `FaceDescriptor`, `ClockLog`, `RosterPeriod`, `StaffRoster`, `ShiftLocation`, `DailyPlan`, `DailyPlanEntry`, `RosterBulkOperation` (+ 4 more) | `attendance/models.py` (578 lines) |
| **stock_tracker** | Bar/restaurant inventory — categories, items, periods, stocktakes, movements, sales, cocktails, comparisons | `StockCategory`, `StockItem`, `StockPeriod`, `Stocktake`, `StocktakeLine`, `StockMovement`, `Sale`, `Cocktail`, `CocktailIngredient` (+ 8 more) | `stock_tracker/models.py` (2633 lines) |
| **voice_recognition** | Audio → text → parsed stock commands pipeline (no models, no URLs) | *(no models)* | `voice_recognition/voice_command_service.py`, `command_parser.py`, `fuzzy_matcher.py` |
| **home** | Staff social noticeboard — posts, comments, replies, likes | `Post`, `Like`, `Comment`, `Reply` | `home/models.py` |

## Non-Django Modules

| Directory | Purpose |
|-----------|---------|
| `scripts/` | One-time migration and debug scripts (34 stock-related scripts in `archive/`) |
| `tools/` | Debug utilities (`check_profitability.py`) |
| `issues/` | GitHub issue creation scripts + markdown specs |
| `templates/` | Django templates (admin overrides, email HTML) |
| `docs/` | Documentation |

## Cross-Domain Dependencies

```
hotel ──────────► rooms (RoomType, Room FKs)
  │               │
  │               ▼
  │           housekeeping (set_room_status — canonical)
  │               ▲
  │               │
  ├──► room_bookings (orchestration — calls housekeeping, chat, room_services)
  │
  ├──► guests (Guest creation during check-in)
  │
  ├──► notifications (all realtime/push/email through NotificationManager)
  │
  ├──► bookings (restaurant bookings reference Hotel, Room, Guest)
  │
  └──► staff (Staff FK for approval, assignment audit)

room_bookings ──► housekeeping.services.set_room_status()
              ──► chat (cleanup on checkout)
              ──► room_services (cleanup on checkout)
              ──► notifications (realtime events)
              ──► hotel.services.cancellation_service (refund calc)

attendance ────► staff (Staff FK, Department, Role)
               ► notifications (Pusher clock status events)

stock_tracker ─► voice_recognition (voice command pipeline)
               ► notifications (Pusher stocktake status)

staff_chat ────► staff (Staff FK, Department for RBAC)
               ► notifications (FCM push, Pusher realtime)

chat ──────────► rooms (Room FK), guests (Guest FK)
               ► staff (Staff participants)
               ► notifications (Pusher + FCM)
```
