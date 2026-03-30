# HotelMateBackend — Complete Backend Discovery Report

**Date:** 2026-03-30  
**Scope:** Full codebase audit — models, endpoints, auth, realtime, services, dead code, inconsistencies

---

## TABLE OF CONTENTS

1. [Domain Areas](#1-domain-areas)
2. [Feature Inventory](#2-feature-inventory)
3. [All Models](#3-all-models-123-total)
4. [All Endpoints](#4-all-endpoints-350)
5. [Auth / Access Mechanisms](#5-auth--access-mechanisms)
6. [Background / Automated Logic](#6-background--automated-logic)
7. [Realtime / Event Emission](#7-realtime--event-emission)
8. [Duplicated / Overlapping Flows](#8-duplicated--overlapping-flows)
9. [Unused / Dead / Legacy Code](#9-unused--dead--legacy-code)
10. [Inconsistencies](#10-inconsistencies)
11. [Features Not Wired Into Complete Flows](#11-features-not-wired-into-complete-flows)
12. [Raw Feature Inventory](#12-raw-feature-inventory)
13. [Surprising or Hidden Capabilities](#13-surprising-or-hidden-capabilities)
14. [Dangerous Inconsistencies](#14-dangerous-inconsistencies)

---

## 1. DOMAIN AREAS

### 14 distinct domain areas identified:

| # | Domain | Primary Apps | Models | Endpoints |
|---|--------|-------------|--------|-----------|
| 1 | **Hotel/Property Management** | `hotel`, `rooms` | Hotel, HotelAccessConfig, HotelPrecheckinConfig, HotelSurveyConfig, BookingOptions, Room, RoomType, RatePlan, DailyRate, Promotion, RoomTypeInventory, RoomTypeRatePlan, Preset, HotelPublicPage, AttendanceSettings | ~30 |
| 2 | **Room Booking Lifecycle** | `hotel`, `room_bookings` | RoomBooking, BookingGuest, PricingQuote, GuestBookingToken, BookingPrecheckinToken, BookingManagementToken, BookingSurveyToken, BookingSurveyResponse, CancellationPolicy, CancellationPolicyTier, OverstayIncident, BookingExtension, StripeWebhookEvent | ~50 |
| 3 | **Guest Portal** | `hotel`, `guests`, `common` | Guest, ThemePreference | ~14 |
| 4 | **Guest–Staff Chat** | `chat`, `hotel` (canonical views) | Conversation, RoomMessage, GuestConversationParticipant, MessageAttachment | ~30 |
| 5 | **Staff-to-Staff Chat** | `staff_chat` | StaffConversation, StaffChatMessage, StaffChatAttachment, StaffMessageReaction | ~20 |
| 6 | **Staff Management** | `staff` | Staff, Department, Role, NavigationItem, RegistrationCode, UserProfile | ~20 |
| 7 | **Attendance / Rostering** | `attendance` | ClockLog, StaffFace, RosterPeriod, StaffRoster, StaffAvailability, ShiftTemplate, RosterRequirement, ShiftLocation, DailyPlan, DailyPlanEntry, RosterAuditLog, FaceAuditLog | ~60 |
| 8 | **Housekeeping** | `housekeeping` | RoomStatusEvent, HousekeepingTask | ~8 |
| 9 | **Room Service & Breakfast** | `room_services` | RoomServiceItem, Order, OrderItem, BreakfastItem, BreakfastOrder, BreakfastOrderItem | ~15 |
| 10 | **Restaurant/Dining Bookings** | `bookings` | Restaurant, RestaurantBlueprint, BlueprintArea, DiningTable, TableSeatSpot, Booking, Seats, BookingTable, BookingCategory, BookingSubcategory, BlueprintObjectType, BlueprintObject | ~30 |
| 11 | **Entertainment/Games** | `entertainment` | Game, GameHighScore, GameQRCode, MemoryGameCard, MemoryGameSession, MemoryGameStats, MemoryGameTournament, TournamentParticipation, MemoryGameAchievement, UserAchievement, QuizCategory, QuizQuestion, QuizSession, QuizAnswer, QuizLeaderboard, QuizTournament | ~30 |
| 12 | **Stock/Inventory Tracker** | `stock_tracker` | StockItem, StockCategory, StockPeriod, StockSnapshot, StockMovement, Stocktake, StocktakeLine, Sale, Location, PeriodReopenPermission, Ingredient, CocktailRecipe, RecipeIngredient, CocktailConsumption, CocktailIngredientConsumption | ~60 |
| 13 | **Maintenance** | `maintenance` | MaintenanceRequest, MaintenanceComment, MaintenancePhoto | ~5 |
| 14 | **Hotel Info / Content** | `hotel_info`, `home`, `hotel` (public page) | HotelInfo, HotelInfoCategory, CategoryQRCode, GoodToKnowEntry, Post, Like, Comment, CommentReply, PublicSection, PublicElement, PublicElementItem, HeroSection, GalleryContainer, GalleryImage, ListContainer, Card, NewsItem, ContentBlock, RoomsSection | ~20 |

**Cross-cutting concerns:**
- **Notifications** (`notifications`) — Central realtime hub + email + FCM. No models of its own.
- **Voice Recognition** (`voice_recognition`) — Wired through stock_tracker only. Uses OpenAI Whisper.
- **Booking Services** (`apps/booking/services`) — Deadline/stay-time business rules.
- **Check-in Policy** (`hotelmate/utils`) — Policy engine for check-in validation.

---

## 2. FEATURE INVENTORY

### A. ROOM BOOKING LIFECYCLE (fully implemented)
- Public booking creation from hotel landing page
- Stripe payment integration (checkout sessions, webhooks, payment verification)
- Booking status machine: PENDING_PAYMENT → PENDING_APPROVAL → CONFIRMED → CHECKED_IN → CHECKED_OUT (+ CANCELLED, EXPIRED, DECLINED, NO_SHOW)
- Staff approval/decline workflow with deadline auto-expiry
- Room type availability checking with inventory
- Pricing engine: rate plans, daily rates, promotions, tax/fee calculation
- Pricing quote generation with TTL
- Room assignment/unassignment/move with atomic operations + version tracking
- Check-in validation engine with hotel-configurable policies
- Check-out with full teardown (guest detach, room turnover trigger, survey send)
- Overstay detection, acknowledgment, and stay extension (with Stripe re-charge)
- Cancellation with configurable tiered cancellation policies + penalty calculation
- Booking management via tokenized email links
- Booking party management (primary guest + companions)
- Pre-check-in data collection via tokenized email links
- Post-checkout survey via tokenized email links
- Survey analytics
- Booking integrity self-healing engine

### B. GUEST PORTAL (fully implemented)
- Token-based guest authentication (GuestBookingToken + BookingManagementToken fallback)
- Guest context API (returns booking info, room, chat availability)
- Room service ordering from menu
- Breakfast ordering
- Restaurant dinner booking (guest-facing)
- Chat with hotel staff (real-time via Pusher)
- Pusher channel authorization for guests
- Theme customization per hotel

### C. GUEST–STAFF CHAT (fully implemented)
- Conversation creation from room number
- Real-time message delivery (Pusher)
- Staff assignment to conversations
- Message editing and soft-deletion
- File attachments (Cloudinary)
- Read receipts (staff and guest side)
- Unread count tracking
- FCM push notifications to staff
- Chat session grants (HMAC-signed, 4h TTL)

### D. STAFF-TO-STAFF CHAT (fully implemented)
- 1:1 and group conversations
- Real-time message delivery (Pusher)
- Message editing and soft-deletion
- Reactions (emoji)
- Reply-to (threading)
- Message forwarding across conversations
- File attachments (Cloudinary)
- Read receipts per participant
- Unread count tracking per staff member
- Mentions (@user)
- Conversation archival
- FCM push notifications

### E. STAFF MANAGEMENT (fully implemented)
- Registration via unique codes (QR-based)
- Token-based staff auth
- Password reset flow
- Staff profiles with department/role/access-level
- Navigation-based permissions (per-staff configurable)
- Staff metadata endpoint
- Staff profile image (Cloudinary)
- Duty status tracking (on_duty / off_duty)
- FCM token management

### F. ATTENDANCE & ROSTERING (fully implemented)
- Clock in/out with break tracking
- Face recognition clock-in (Cloudinary + encoding storage)
- Face registration with consent tracking
- Unrostered clock-in requests with approval
- Roster period management (create, finalize, unfinalize)
- Shift management: create, bulk-save, copy-day, copy-week, copy-period, duplicate
- Custom period creation
- Shift locations
- Daily plan generation from roster
- Roster analytics: staff summary, department summary, KPIs, daily/weekly breakdowns
- PDF export: roster period PDF, daily PDF, staff PDF, daily plan PDF
- Break/overtime/hard-limit alerts (Pusher realtime)
- Auto-clock-out for excessive sessions (management command)
- Face audit logging
- Roster audit logging

### G. HOUSEKEEPING (fully implemented)
- Room status state machine: VACANT_CLEAN → OCCUPIED → VACANT_DIRTY → CLEANING → VACANT_CLEAN → INSPECTED (+ OUT_OF_ORDER, MAINTENANCE branches)
- Status change authorization by role (housekeeper, supervisor, manager)
- Manager override for status transitions
- Task management: create, assign, start, complete (CHECKOUT_CLEAN, STAYOVER_CLEAN, DEEP_CLEAN, INSPECTION, TURNDOWN, LINEN_CHANGE)
- Priority-based ordering (URGENT, HIGH, NORMAL, LOW)
- SLA-based overdue detection
- Dashboard with room summary statistics
- Status history audit trail

### H. ROOM SERVICE & BREAKFAST (fully implemented)
- Menu items per hotel (with Cloudinary images)
- Room service order creation and status tracking
- Breakfast menu and ordering with delivery time
- Order summary and history
- Pending order count (with real-time updates)
- Staff menu item management (CRUD)
- Realtime order notifications to porters/kitchen via Pusher + FCM

### I. RESTAURANT/DINING SYSTEM (fully implemented)
- Restaurant management with capacity, hours, booking controls
- Restaurant blueprints (floor plans) with coordinate-based layouts
- Blueprint areas (zones within restaurant)
- Dining tables: shapes, sizes, positions, joinability, rotation
- Seat spots per table with angular offsets
- Table availability checking
- Guest-to-table assignment
- Table booking with capacity validation + overlap checking
- Blueprint decorative objects (non-table items)
- Guest dinner booking (from room number)
- Booking categories and subcategories
- QR code generation for restaurant access

### J. ENTERTAINMENT & GAMES (fully implemented)
- Generic game framework with high scores + QR codes
- **Memory Game**: Card decks, difficulty levels, timed sessions, score calculation, practice mode, leaderboards
- **Memory Game Tournaments**: Registration, scoring, QR codes, prizes, start/end lifecycle, participant ranking
- **Memory Game Achievements**: Configurable achievement types with unlock tracking
- **Quiz System**: Categories with difficulty, question bank, timed sessions, answer validation, scoring
- **Quiz Tournaments**: Same lifecycle as memory tournaments
- **Quiz Leaderboards**: Global + per-player rank tracking
- Dashboard with aggregated stats

### K. STOCK/INVENTORY TRACKER (fully implemented)
- Stock items with SKU, category, pricing (menu/bottle/promo), size/unit management
- Stock categories auto-mapped from SKU prefix
- Par level tracking + low stock detection
- Profitability analysis: cost per serving, gross profit %, pour cost %, markup %
- Stock periods (monthly/quarterly) with open/close/reopen lifecycle
- Snapshots: closing stock per item per period
- Stock movements: purchases, sales, waste, transfers, adjustments
- Stocktake workflow: populate → count → approve
- Stocktake lines with variance calculation (expected vs counted)
- Cocktail recipes with ingredient linking
- Cocktail consumption tracking with auto-cost calculation
- Cocktail ingredient consumption merge to stocktake
- Period comparison analytics
- PDF/Excel export for stocktakes and periods
- KPI summary dashboard
- Voice command interface (OpenAI Whisper → fuzzy match → stock operation)
- Sales recording and reporting

### L. MAINTENANCE (fully implemented)
- Maintenance request lifecycle (NEW → IN_PROGRESS → RESOLVED)
- Photo attachments (Cloudinary)
- Comments/notes per request
- Staff assignment (reported_by, accepted_by)

### M. HOTEL CONTENT MANAGEMENT (fully implemented)
- **Public Landing Page Builder**: Sections, elements, items — full CMS
- Hero sections with customizable imagery
- Gallery containers with images
- List containers with cards
- News items with content blocks (text + image)
- Rooms section linked to room types
- Style variants and layout presets
- Bootstrap-default page generation
- Hotel info categories with entries
- "Good to Know" entries per hotel
- QR code generation per category
- Social-style staff posts with likes, comments, and replies (home app)
- Theme preference per hotel (colors)
- Booking options (CTA labels, URLs, terms/policies links)

### N. NOTIFICATIONS / REALTIME (fully implemented)
- Pusher realtime events for 12+ domains (see Section 7)
- FCM push notifications (Firebase)
- Email service (Gmail SMTP): booking confirmation, cancellation, management links, pre-check-in, survey
- Central NotificationManager (~2400 lines, 40+ methods)

### O. PAYMENT (fully implemented)
- Stripe Checkout Sessions
- Stripe webhooks (checkout.session.completed, payment_intent.succeeded)
- Payment verification
- Idempotent operations via `payment_cache_table`
- Refund processing on cancellation
- Overstay extension re-charging

---

## 3. ALL MODELS (123 total)

### hotel app (30 models)
| Model | Purpose |
|-------|---------|
| `Hotel` | Core hotel entity with slug, subdomain, location, contact, branding |
| `HotelAccessConfig` | Guest/staff portal settings, PIN config, checkout timing |
| `HotelPrecheckinConfig` | Configurable pre-check-in fields (enabled/required) |
| `HotelSurveyConfig` | Post-checkout survey configuration |
| `BookingOptions` | CTA labels, URLs, policies links |
| `RoomBooking` | Room accommodation booking with full lifecycle state machine |
| `GuestBookingToken` | SHA-256 hashed guest access tokens with scopes |
| `BookingPrecheckinToken` | Tokenized pre-check-in link |
| `BookingManagementToken` | Tokenized booking management link |
| `BookingSurveyToken` | Tokenized survey link |
| `BookingSurveyResponse` | Survey response with rating and payload |
| `BookingGuest` | Booking party member (PRIMARY or COMPANION) |
| `PricingQuote` | Time-limited pricing quote for bookings |
| `CancellationPolicy` | Tiered cancellation policy with penalty types |
| `CancellationPolicyTier` | Time-based penalty tier |
| `OverstayIncident` | Overstay detection/acknowledgment/resolution tracking |
| `BookingExtension` | Stay extension with Stripe pricing snapshot |
| `StripeWebhookEvent` | Stripe event deduplication log |
| `Preset` | Reusable style/layout preset configs (JSON) |
| `HotelPublicPage` | Root of public page CMS |
| `PublicSection` | CMS section with position and style |
| `PublicElement` | CMS element within section |
| `PublicElementItem` | Items within CMS element |
| `HeroSection` | Hero banner configuration |
| `GalleryContainer` | Gallery grouping |
| `GalleryImage` | Individual gallery image |
| `ListContainer` | Card list grouping |
| `Card` | Individual card in list |
| `NewsItem` | News/update entry |
| `ContentBlock` | Text/image block within news item |
| `RoomsSection` | Room types display section |
| `AttendanceSettings` | Per-hotel attendance and face recognition config |

### stock_tracker app (16 models)
| Model | Purpose |
|-------|---------|
| `StockItem` | Individual stock item with SKU, pricing, quantity |
| `StockCategory` | Category auto-mapped from SKU prefix |
| `StockPeriod` | Time-bounded stock tracking period |
| `StockSnapshot` | Closing stock snapshot per item per period |
| `StockMovement` | Stock movement record (purchase/sale/waste/transfer/adjustment) |
| `Stocktake` | Full stock count session |
| `StocktakeLine` | Per-item stocktake data (opening, counted, variance) |
| `Sale` | Individual sale record |
| `Location` | Physical stock location |
| `PeriodReopenPermission` | Permission to reopen closed periods |
| `Ingredient` | Raw ingredient for cocktails |
| `CocktailRecipe` | Recipe with ingredients |
| `RecipeIngredient` | Recipe ↔ ingredient bridge |
| `CocktailConsumption` | Cocktail production record |
| `CocktailIngredientConsumption` | Per-ingredient consumption with cost |

### entertainment app (16 models)
| Model | Purpose |
|-------|---------|
| `Game` | Generic game entry |
| `GameHighScore` | High scores per game per user |
| `GameQRCode` | QR code per game per hotel |
| `MemoryGameCard` | Card asset for memory game |
| `MemoryGameSession` | Single game play session |
| `MemoryGameStats` | Aggregated stats per user |
| `MemoryGameTournament` | Tournament definition |
| `TournamentParticipation` | Player in tournament |
| `MemoryGameAchievement` | Achievement definition |
| `UserAchievement` | Unlocked achievement |
| `QuizCategory` | Quiz category |
| `QuizQuestion` | Quiz question with 4 options |
| `QuizSession` | Quiz play session |
| `QuizAnswer` | Individual answer record |
| `QuizLeaderboard` | Global leaderboard entry |
| `QuizTournament` | Quiz tournament definition |

### attendance app (12 models)
| Model | Purpose |
|-------|---------|
| `ClockLog` | Clock in/out record with break tracking |
| `StaffFace` | Face encoding for recognition |
| `RosterPeriod` | Roster time boundary with finalization |
| `StaffRoster` | Individual shift assignment |
| `StaffAvailability` | Staff availability declaration |
| `ShiftTemplate` | Reusable shift definition |
| `RosterRequirement` | Required staffing per dept/role/date |
| `ShiftLocation` | Named location for shifts |
| `DailyPlan` | Day-level staffing plan |
| `DailyPlanEntry` | Individual staff entry in daily plan |
| `RosterAuditLog` | Roster operation audit trail |
| `FaceAuditLog` | Face registration/revocation audit |

### bookings app (12 models)
| Model | Purpose |
|-------|---------|
| `Restaurant` | Restaurant entity with hours and capacity |
| `RestaurantBlueprint` | Floor plan layout |
| `BlueprintArea` | Named zone in blueprint |
| `DiningTable` | Table with shape, position, capacity |
| `TableSeatSpot` | Seat positions on table |
| `Booking` | Restaurant/dining reservation |
| `Seats` | Adult/child/infant counts |
| `BookingTable` | Booking ↔ table bridge |
| `BookingCategory` | Booking type category |
| `BookingSubcategory` | Booking subcategory |
| `BlueprintObjectType` | Decorative object type |
| `BlueprintObject` | Decorative object instance |

### rooms app (7 models)
| Model | Purpose |
|-------|---------|
| `Room` | Physical room with status and housekeeping state |
| `RoomType` | Room type definition with pricing |
| `RatePlan` | Named rate plan with refund policy |
| `RoomTypeRatePlan` | Room type ↔ rate plan bridge |
| `DailyRate` | Date-specific rate override |
| `Promotion` | Promotional discount |
| `RoomTypeInventory` | Per-date room availability + stop-sell |

### room_services app (6 models)
| Model | Purpose |
|-------|---------|
| `RoomServiceItem` | Menu item with category and stock status |
| `Order` | Room service order |
| `OrderItem` | Order ↔ item bridge |
| `BreakfastItem` | Breakfast menu item |
| `BreakfastOrder` | Breakfast order with delivery time |
| `BreakfastOrderItem` | Breakfast order ↔ item bridge |

### staff app (6 models)
| Model | Purpose |
|-------|---------|
| `Staff` | Staff profile with department/role/access level |
| `Department` | Organizational department |
| `Role` | Staff role within department |
| `NavigationItem` | Per-hotel navigation/permission item |
| `RegistrationCode` | Unique registration code with QR |
| `UserProfile` | Extended user → registration code link |

### chat app (4 models)
| Model | Purpose |
|-------|---------|
| `Conversation` | Guest–staff chat thread |
| `RoomMessage` | Individual message with sender tracking |
| `GuestConversationParticipant` | Staff member joined to conversation |
| `MessageAttachment` | File attached to message |

### staff_chat app (4 models)
| Model | Purpose |
|-------|---------|
| `StaffConversation` | Staff-to-staff thread (1:1 or group) |
| `StaffChatMessage` | Staff chat message with read/reaction tracking |
| `StaffChatAttachment` | File attached to staff message |
| `StaffMessageReaction` | Emoji reaction on message |

### hotel_info app (4 models)
| Model | Purpose |
|-------|---------|
| `HotelInfoCategory` | Category for hotel info entries |
| `HotelInfo` | Hotel info entry (events, services, etc.) |
| `CategoryQRCode` | QR code per category per hotel |
| `GoodToKnowEntry` | "Good to Know" content entries |

### home app (4 models)
| Model | Purpose |
|-------|---------|
| `Post` | Staff social post |
| `Like` | Like on post |
| `Comment` | Comment on post |
| `CommentReply` | Reply to comment |

### maintenance app (3 models)
| Model | Purpose |
|-------|---------|
| `MaintenanceRequest` | Maintenance ticket |
| `MaintenanceComment` | Comment on ticket |
| `MaintenancePhoto` | Photo evidence |

### housekeeping app (2 models)
| Model | Purpose |
|-------|---------|
| `RoomStatusEvent` | Status change audit trail |
| `HousekeepingTask` | Cleaning/inspection task with SLA |

### guests app (1 model)
| Model | Purpose |
|-------|---------|
| `Guest` | In-house guest record (linked to booking) |

### common app (1 model)
| Model | Purpose |
|-------|---------|
| `ThemePreference` | Hotel theme colors |

---

## 4. ALL ENDPOINTS (~350+)

### Public Zone — `api/public/` (~23 endpoints)
| Path | Purpose |
|------|---------|
| `presets/` | List reusable layout presets |
| `hotels/` | List active hotels |
| `hotels/filters/` | Hotel filter options |
| `hotel/<slug>/page/` | Full public page CMS render |
| `hotel/<slug>/availability/` | Room type availability check |
| `hotel/<slug>/pricing/quote/` | Generate pricing quote |
| `hotel/<slug>/bookings/` | Create new booking |
| `hotel/<slug>/room-bookings/<id>/` | Booking detail (public) |
| `hotel/<slug>/room-bookings/<id>/cancel/` | Cancel booking |
| `hotel/<slug>/room-bookings/<id>/payment/` | Create payment session |
| `hotel/<slug>/room-bookings/<id>/payment/session/` | Create payment session (alt) |
| `hotel/<slug>/room-bookings/<id>/payment/verify/` | Verify payment |
| `hotel/room-bookings/stripe-webhook/` | Stripe webhook receiver |
| `hotels/<slug>/booking/status/<id>/` | Booking status check |
| `booking/validate-token/` | Validate management token |
| `booking/cancel/` | Cancel via management token |
| `hotels/<slug>/cancellation-policy/` | View cancellation policy |
| `hotel/<slug>/cancellation-policy/` | View cancellation policy (dup path) |
| `hotel/<slug>/booking-management/` | Validate booking management token |
| `hotel/<slug>/booking-management/cancel/` | Cancel via management token |
| `hotel/<slug>/precheckin/` | Validate precheckin token |
| `hotel/<slug>/precheckin/submit/` | Submit precheckin data |
| `hotel/<slug>/survey/` | Validate survey token |
| `hotel/<slug>/survey/submit/` | Submit survey response |

### Guest Zone — `api/guest/` (~14 endpoints)
| Path | Purpose |
|------|---------|
| `context/` | Guest bootstrap context |
| `hotels/<slug>/` | Guest hotel detail |
| `hotels/<slug>/site/home/` | Guest home page data |
| `hotels/<slug>/site/rooms/` | Guest rooms listing |
| `hotels/<slug>/availability/` | Room availability |
| `hotels/<slug>/pricing/quote/` | Pricing quote |
| `hotels/<slug>/cancellation-policy/` | Cancellation policy |
| `hotels/<slug>/bookings/` | Create booking |
| `hotels/<slug>/room-services/orders/` | Room service ordering |
| `hotels/<slug>/room/<room>/menu/` | Room service menu |
| `hotel/<slug>/chat/context` | Chat bootstrap |
| `hotel/<slug>/chat/messages` | Send chat message |
| `hotel/<slug>/chat/pusher/auth` | Pusher auth for guest |
| `hotel/<slug>/chat/conversations/<id>/mark_read/` | Mark messages read |

### Staff Zone — `api/staff/` (~250+ endpoints)

#### Staff Auth & Profile (~20)
- `login/`, `register/`, `registration-package/`
- `password-reset/`, `password-reset-confirm/`
- `save-fcm-token/`, `users/`, `users/by-hotel-codes/`
- `departments/` (CRUD), `roles/` (CRUD), `navigation-items/` (CRUD)
- `<staff_id>/permissions/`
- `<slug>/metadata/`, `<slug>/pending-registrations/`, `<slug>/create-staff/`
- `<slug>/` (Staff CRUD)
- `hotel/<slug>/me/`

#### Room Bookings (~20)
- `room-bookings/` (list), `<id>/` (detail), `<id>/mark-seen/`
- `<id>/confirm/`, `<id>/cancel/`, `<id>/approve/`, `<id>/decline/`
- `<id>/party/`, `<id>/party/companions/`
- `<id>/available-rooms/`, `<id>/safe-assign-room/`, `<id>/unassign-room/`, `<id>/move-room/`
- `<id>/check-in/`, `<id>/check-out/`
- `<id>/send-precheckin-link/`, `<id>/send-survey-link/`
- `<id>/overstay/acknowledge/`, `<id>/overstay/extend/`, `<id>/overstay/status/`

#### Attendance & Rostering (~55)
- `roster-periods/` (CRUD + add-shift, create-department-roster, finalize/unfinalize, export-pdf, duplicate)
- `periods/` (alias for roster-periods — FULL DUPLICATE)
- `shifts/` (CRUD + bulk-save, daily-pdf, staff-pdf)
- `clock-logs/` (CRUD)
- `roster-analytics/` (staff-summary, department-summary, kpis, daily-totals, daily-by-department, daily-by-staff, weekly-*)
- `shift-locations/` (CRUD)
- `daily-plans/` (CRUD + prepare, download-pdf, by-department)
- `shift-copy/` (copy-roster-day-all, copy-roster-bulk, copy-week-staff, copy-entire-period)
- `face-management/` (register, revoke, list, face-clock-in, force-clock-in, confirm-clock-out, toggle-break, audit-logs, face-status)

#### Chat — Staff (Guest Chat Management) (~13)
- `active-rooms/`, `conversations/`, `conversations/from-room/<room>/`
- `conversations/<id>/messages/`, `conversations/<id>/messages/send/`
- `conversations/unread-count/`, `conversations/<id>/mark-read/`
- `conversations/<id>/assign-staff/`
- `messages/<id>/update/`, `messages/<id>/delete/`
- `conversations/<id>/upload-attachment/`, `attachments/<id>/delete/`
- `save-fcm-token/`

#### Staff-to-Staff Chat (~20)
- `staff-list/`, `conversations/` (CRUD + for-forwarding, unread-count, bulk-mark-as-read, conversations-with-unread-count)
- `conversations/<id>/send-message/`, `conversations/<id>/messages/`
- `messages/<id>/mark-as-read/`, `messages/<id>/edit/`, `messages/<id>/delete/`
- `messages/<id>/react/`, `messages/<id>/react/<emoji>/`, `messages/<id>/forward/`
- `conversations/<id>/upload/`, `attachments/<id>/delete/`, `attachments/<id>/url/`
- Legacy: `conversations/<id>/send_message/`, `conversations/<id>/mark_as_read/`

#### Housekeeping (~8)
- `dashboard/`, `tasks/` (CRUD + assign, start, complete)
- `rooms/<id>/status/`, `rooms/<id>/manager_override/`, `rooms/<id>/status-history/`

#### Room Turnover (~9)
- `rooms/checkout/`, `room-types/<id>/rooms/bulk-create/`
- `rooms/<room>/start-cleaning/`, `rooms/<room>/mark-cleaned/`
- `rooms/<room>/inspect/`, `rooms/<room>/mark-maintenance/`, `rooms/<room>/complete-maintenance/`
- `turnover/rooms/`, `turnover/stats/`

#### Room Service (~15)
- `<slug>/orders/` (CRUD + all-orders-summary, order-history, pending-count)
- `<slug>/room/<room>/menu/`, `<slug>/room/<room>/breakfast/`, `<slug>/room/<room>/save-fcm-token/`
- `<slug>/breakfast-orders/` (CRUD + pending-count)
- Staff CRUD for items: `room-service-items/`, `breakfast-items/`

#### Restaurant / Dining (~15)
- `bookings/` (CRUD), `categories/` (CRUD), `restaurants/` (CRUD)
- `blueprint/<slug>/` (CRUD), `tables/<slug>/` (CRUD)
- `blueprint/<slug>/<id>/objects/` (CRUD)
- `available-tables/<slug>/`, `mark-seen/`, `assign/<slug>/`, `unseat/<slug>/`, `delete/<slug>/<id>/`
- `blueprint-object-types/` (CRUD)

#### Entertainment (~30)
- `games/` (CRUD + highscores, qrcodes)
- `memory-cards/` (CRUD), `memory-sessions/` (CRUD + practice, my-stats, leaderboard)
- `tournaments/` (CRUD + active, summary, submit_score, generate_qr_code, leaderboard, participants, start, end)
- `achievements/` (CRUD + my-achievements), `dashboard/` (stats)
- `quiz-categories/` (CRUD + random_selection)
- `quiz-questions/` (CRUD), `quiz-sessions/` (CRUD + start_quiz, submit_answer, complete_session)
- `quiz-leaderboard/` (list + my_rank), `quiz-tournaments/` (CRUD + leaderboard, top_players)

#### Stock Tracker (~60)
- `items/` (CRUD + profitability, low-stock, history)
- `categories/` (CRUD + items), `locations/` (CRUD)
- `periods/` (CRUD + snapshots, populate-opening-stock, compare, reopen, approve-and-close, sales-analysis, download-pdf/excel, reopen-permissions, grant/revoke)
- `snapshots/` (CRUD), `movements/` (CRUD)
- `stocktakes/` (CRUD + populate, approve, reopen, category_totals, merge-all-cocktail-consumption, download-pdf/excel/combined-pdf)
- `stocktake-lines/` (CRUD + add-movement, movements, delete-movement, update-movement, merge-cocktail-consumption, voice-command)
- `sales/` (CRUD + summary, bulk-create)
- `ingredients/` (CRUD), `cocktails/` (CRUD)
- `consumptions/` (CRUD + sales-report), `ingredient-consumptions/` (list + available, by-stock-item)
- `analytics/ingredient-usage/`
- `reports/stock-value/`, `reports/sales/`
- `compare/` (categories, top-movers, cost-analysis, trend-analysis, variance-heatmap, performance-scorecard)
- `kpi-summary/`

#### Hotel Settings / Config (~15)
- `settings/`, `access-config/`, `status/`
- `public-page-builder/`, `public-page-builder/bootstrap-default/`
- `sections/create/`, `precheckin-config/`, `survey-config/`
- `cancellation-policies/` (CRUD + templates)
- `rate-plans/` (CRUD + delete)
- `presets/` (CRUD)
- `public-page/` (CRUD), `public-sections/`, `public-elements/`, `public-element-items/`
- `hero-sections/`, `gallery-containers/`, `gallery-images/`
- `list-containers/`, `cards/`, `news-items/`, `content-blocks/`
- `room-management/`, `room-types/`

#### Maintenance (~5)
- `requests/` (CRUD), `comments/` (CRUD), `photos/` (CRUD)

#### Hotel Info (~8)
- `hotelinfo/` (CRUD + create), `categories/` (CRUD)
- `category_qr/` (CRUD + download_all), `good_to_know/<slug>/` (CRUD)

#### Home/Posts (~8)
- `posts/` (CRUD), `posts/<id>/comments/` (CRUD)
- `posts/<id>/comments/<id>/replies/` (CRUD)

#### Common (~1)
- `theme/` (CRUD)

### Legacy Direct Zone (~40 endpoints)
| Prefix | Content |
|--------|---------|
| `api/chat/` | **Full duplicate** of staff chat endpoints (13 views) |
| `api/bookings/` | **Near-full duplicate** of staff restaurant booking endpoints + guest dinner booking |
| `api/room_services/` | Room service endpoints (orders, menus, breakfast) |
| `api/hotel/` | Hotel CRUD + staff router (public page management) |
| `api/notifications/` | `save-fcm-token/`, `pusher/auth/` |

### Global (~3)
| Path | Purpose |
|------|---------|
| `admin/` | Django admin |
| `/` | Root home view |
| `api/hotels/<slug>/face-config/` | Public face attendance config |

---

## 5. AUTH / ACCESS MECHANISMS

### 5 distinct authentication mechanisms:

| # | Mechanism | Transport | Used By | Implementation |
|---|-----------|-----------|---------|----------------|
| 1 | **DRF Token Auth** | `Authorization: Token <key>` | All staff endpoints | `rest_framework.authtoken` — auto-created on `User` post_save signal |
| 2 | **GuestBookingToken** | `?token=` or `Authorization: GuestToken <token>` | Guest portal (primary) | Custom: SHA-256 hash → DB lookup → scope validation → booking lifecycle check |
| 3 | **BookingManagementToken** | `?token=` or `Authorization: GuestToken <token>` | Email management links (fallback) | Same transport as GBT, tried second if GBT lookup fails |
| 4 | **Guest Chat Grant** | `X-Guest-Chat-Session` header | Post-bootstrap chat endpoints | HMAC-SHA256 signed via `django.core.signing` (4h TTL). Claims: booking_id, hotel_slug, room_id, scope |
| 5 | **HotelSubdomainBackend** | Username + password + subdomain | **DEFINED BUT NOT ACTIVE** | `hotel/auth_backends.py` — not in `AUTHENTICATION_BACKENDS` setting |

### Permission classes (10):

| Class | Location | Logic |
|-------|----------|-------|
| `IsAuthenticated` | DRF built-in | Global default |
| `AllowAny` | DRF built-in | Guest-facing reads |
| `IsAuthenticatedOrReadOnly` | DRF built-in | Blueprints, tables |
| `IsStaffMember` | `staff_chat/permissions.py` | Has `staff_profile` |
| `IsConversationParticipant` | `staff_chat/permissions.py` | Object-level: in `obj.participants` |
| `IsMessageSender` | `staff_chat/permissions.py` | Object-level: is `obj.sender` |
| `IsSameHotel` | `staff_chat/permissions.py` | Staff hotel matches URL hotel |
| `CanManageConversation` | `staff_chat/permissions.py` | Creator or manager/admin role |
| `CanDeleteMessage` | `staff_chat/permissions.py` | Own messages or manager/admin |
| `IsHotelStaff` | `hotel/permissions.py` | Staff hotel matches URL slug |
| `IsSuperStaffAdminForHotel` | `hotel/permissions.py` | Super staff admin only |
| `HasNavPermission(slug)` | `staff/permissions.py` | Checks navigation item access |

### Throttle classes (4):
| Class | Scope | Rate |
|-------|-------|------|
| `PublicBurstThrottle` | public_burst | 30/min |
| `PublicSustainedThrottle` | public_sustained | 200/hour |
| `GuestTokenBurstThrottle` | guest_burst | 60/min |
| `GuestTokenSustainedThrottle` | guest_sustained | 600/hour |

### Middleware:
- `CorsMiddleware` — CORS header injection
- `SecurityMiddleware` — Django security (HSTS, etc.)
- `WhiteNoiseMiddleware` — Static file serving
- `SessionMiddleware`, `CsrfViewMiddleware`, `AuthenticationMiddleware`, `MessageMiddleware`, `XFrameOptionsMiddleware`
- `HotelMiddleware` — **DEFINED but NOT in MIDDLEWARE list** (subdomain → hotel resolver)

---

## 6. BACKGROUND / AUTOMATED LOGIC

### Signals (12 handlers):

| Signal | Sender | Handler | Effect |
|--------|--------|---------|--------|
| `post_save` | `Hotel` | `create_hotel_access_config` | Auto-create HotelAccessConfig |
| `post_save` | `Hotel` | `save_hotel_access_config` | Backfill HotelAccessConfig |
| `post_save` | `Hotel` | `create_hotel_related_objects` | Auto-create 6 related config objects |
| `post_save` | `Hotel` | `create_default_navigation_items` | Create default nav items |
| `pre_save` | `GuestBookingToken` | `auto_populate_guest_token_hotel` | Set hotel from booking |
| `post_save` | `Department` | `add_department_to_face_attendance` | Add dept to all hotels' face settings |
| `post_save` | `User` | `create_auth_token` | Auto-create DRF Token |
| `post_save` | `User` | `create_staff_from_registration_code` | Auto-create Staff from reg code |
| `post_save` | `CategoryQRCode` | `generate_qr_on_create` | Auto-generate QR URL |
| `post_save` | `Order` | `send_porter_notification_on_room_service` | Realtime notification on order |
| `post_save` | `BreakfastOrder` | `send_porter_notification_on_breakfast_order` | Realtime notification on breakfast order |
| `post_save` | `StaffChatMessage` | `handle_staff_message_created` | Unread count updates |

### Management commands — Scheduled (9):
| Command | Schedule | Purpose |
|---------|----------|---------|
| `check_attendance_alerts` | Every 5-10 min | Break/overtime alerts |
| `auto_clock_out_excessive` | Every 30 min | Force clock-out past hard limit |
| `send_scheduled_surveys` | Every 15 min | Send survey emails at scheduled time |
| `flag_overstay_bookings` | Every 15-30 min | Detect overstay incidents |
| `auto_expire_overdue_bookings` | Every 5-15 min | Expire overdue PENDING_APPROVAL bookings |
| `cleanup_survey_tokens` | Daily | Clean expired survey tokens |
| `cleanup_orphaned_guests` | As needed | Fix ghost guest records |
| `heal_booking_integrity` | As needed | Self-heal booking data |
| `update_tournament_statuses` | Hourly | Update tournament lifecycle |

### Management commands — Seed/Data (22):
| Command | Purpose |
|---------|---------|
| `seed_hotels` | Seed sample hotels |
| `seed_killarney_public_page` | Seed Killarney public page |
| `seed_default_cancellation_policies` | Seed cancellation templates |
| `seed_navigation_items` | Seed nav items |
| `populate_killarney_pms` | Populate PMS data |
| `simulate_killarney_bookings` | Simulate booking flow |
| `upload_killarney_images` | Upload to Cloudinary |
| `check_killarney_rooms` | Check room data |
| `generate_restaurant_bookings` | Generate dining bookings |
| `seed_no_way_bookings` | Deterministic test data |
| `generate_analytics_data` | Generate stock analytics |
| `create_cocktails` | Create cocktail data |
| `create_missing_cocktails` | Backfill cocktails |
| `update_cocktail_prices` | Update prices |
| `create_stock_categories` | Create categories |
| `create_october_stocktake` | Create October stocktake |
| `create_october_2025` | Create October period |
| `check_october_period` | Check period status |
| `close_october_period` | Close period |
| `fetch_october_2025` | Fetch period data |
| `recreate_october_period` | Recreate period |

### Management commands — Maintenance (4):
| Command | Purpose |
|---------|---------|
| `fix_cloudinary_urls` | Fix backslash URLs |
| `delete_all_images` | Delete all Cloudinary images |
| `backfill_hotel_related_objects` | Backfill missing configs |
| `audit_legacy_routes` | Test URL resolution |

### Implicit automated workflows in save() overrides:
- `RoomBooking.save()` → auto-gen `booking_id` + `confirmation_number` + sync primary BookingGuest
- `ClockLog.save()` → auto-calculate `hours_worked`
- `RoomMessage.save()` → auto-populate `staff_display_name`, `staff_role_name`
- `StaffChatMessage.post_save` → fire unread count updates
- `StockItem.save()` → auto-set category from SKU prefix
- `CocktailConsumption.save()` → auto-calculate revenue/cost + create ingredient records
- `Sale.save()` → auto-calculate totals
- `DailyPlanEntry.save()` → auto-set department from staff
- `MessageAttachment.save()` / `StaffChatAttachment.save()` → auto-detect file type
- `BookingSurveyResponse.save()` → log low-rating alerts
- `Hotel.save()` → auto-generate slug
- `StockSnapshot.save()` → auto-convert units for Minerals category

---

## 7. REALTIME / EVENT EMISSION

### Architecture
- **Client**: Pusher (one global singleton in `chat/utils.py`)
- **Central hub**: `NotificationManager` in `notifications/notification_manager.py` (~2450 lines, 40+ methods)
- **FCM**: Firebase Cloud Messaging for mobile push
- **Bypass paths**: Some modules call Pusher directly, skipping NotificationManager

### Channel Map (14 channel types):

| Channel Pattern | Domain | Key Events |
|-----------------|--------|------------|
| `private-guest-booking.{booking_id}` | Guest Booking | payment_required, confirmed, cancelled, checked_in, checked_out, room_assigned |
| `{slug}.room-bookings` | Staff Bookings | created, updated, confirmed, cancelled, checked_in, checked_out, party_updated, integrity_healed |
| `{slug}.attendance` | Attendance | clock_status_updated |
| `{slug}-conversation-{id}-chat` | Staff Chat | message_created/edited/deleted, attachment_uploaded/deleted |
| `{slug}-staff-{id}-notifications` | Staff Notifications | unread_updated, guest_messages |
| `private-hotel-{slug}-guest-chat-booking-{bid}` | Guest Chat | chat.message.created/edited/deleted, unread_updated |
| `{slug}.room-service` | Room Service | order_created, order_updated |
| `{slug}.rooms` | Rooms | room_updated, room_occupancy_updated |
| `{slug}.staff-menu-management` | Menu Mgmt | menu_item_updated |
| `{slug}-stocktake-{id}` | Stocktake | stocktake/line events |
| `attendance-{slug}-staff-{id}` | Attendance Alerts | break/overtime/hard-limit warnings |
| `attendance-{slug}-managers` | Attendance Mgrs | staff warnings, unrostered requests |
| `{slug}` | Hotel-wide | booking_overstay_detected/acknowledged/extended/resolved |
| `private-conversation-{id}` | Guest Chat (alt) | chat.message.created |

### Event emission by domain:

| Domain | Through NM? | Direct Pusher? | Events |
|--------|-------------|----------------|--------|
| Booking lifecycle | ✅ | — | 12+ events |
| Guest chat | ✅ | — | 4 events |
| Staff chat | ✅ | — | 8+ events |
| Room service | ✅ | — | 3 events |
| Room updates | ✅ | — | 2 events |
| Booking integrity | ✅ | — | 3 events |
| Overstay | ✅ | — | 4 events |
| Attendance clock | ✅ | — | 1 event |
| Attendance alerts | — | ✅ BYPASS | 7+ direct calls |
| Attendance roster | — | ✅ BYPASS | 5+ direct calls |
| Stock tracker | — | ✅ BYPASS | All stocktake events |
| Hotel staff-views | — | ✅ BYPASS | 3 direct calls |
| Staff profile | — | ✅ BYPASS (1 call) | staff_profile_updated |

---

## 8. DUPLICATED / OVERLAPPING FLOWS

### 8.1 URL Duplication (CRITICAL)

| Duplicate Set | Scope | Impact |
|---------------|-------|--------|
| `chat/urls.py` vs `chat/staff_urls.py` | **100% identical** views | Same 13 views mounted at `/api/chat/<slug>/` AND `/api/staff/hotel/<slug>/chat/` |
| `bookings/urls.py` vs `bookings/staff_urls.py` | **~90% identical** views | Same restaurant booking views at `/api/bookings/<slug>/` AND `/api/staff/hotel/<slug>/service-bookings/` |
| `hotel/urls.py` `staff_router` vs `staff_urls.py` `staff_hotel_router` | **11 ViewSets** registered twice | Public page CMS endpoints at `/api/hotel/staff/` AND `/api/staff/hotel/<slug>/` |
| `roster-periods/` vs `periods/` | **100% alias** | Same ViewSet registered under 2 prefixes in attendance URLs |
| `api/public/hotels/<slug>/cancellation-policy/` vs `api/public/hotel/<slug>/cancellation-policy/` | Same view | Mounted at two path variants |
| `conversation-send-message-legacy` | Legacy alias | Old endpoint alongside new `send-message` |

### 8.2 Notification Path Duplication

| Path | What it does |
|------|-------------|
| `notifications/notification_manager.py` | Central hub — 40+ methods |
| `notifications/pusher_utils.py` | Building-block Pusher utilities (used BY NM) |
| `notifications/utils.py` | Orchestrates Pusher + FCM (standalone) |
| `staff/pusher_utils.py` | Partially delegates to NM, partially direct |
| `staff_chat/pusher_utils.py` | **DEPRECATED** — fully delegates to NM |
| `stock_tracker/pusher_utils.py` | **Bypasses NM entirely** — all direct Pusher |
| `attendance/utils.py` | **Bypasses NM** — 7 direct Pusher calls |
| `attendance/views.py` | **Bypasses NM** — 5 direct Pusher calls |

### 8.3 FCM Token Save Duplication

Three separate endpoints save FCM tokens:
1. `notifications/views.py` → `SaveFcmTokenView` at `/api/notifications/save-fcm-token/`
2. `staff/views.py` → `SaveFCMTokenView` at `/api/staff/save-fcm-token/`
3. `chat/views.py` → `save_fcm_token()` at `/api/chat/<slug>/save-fcm-token/` + `/api/staff/hotel/<slug>/chat/save-fcm-token/`

Each saves to a different field: `staff.fcm_token`, `room.guest_fcm_token`.

### 8.4 Guest Name Resolution Duplication

Guest name is resolved independently in 5+ places:
1. `booking.primary_guest_name` — property
2. `booking.guest_display_name` — property with fallback
3. `RoomMessageSerializer.get_guest_name()` — DB query
4. `ConversationSerializer.get_guest_name()` — DB query (duplicated logic)
5. `StaffRoomBookingDetailSerializer.get_guest_display_name()` — party query
6. Inline in email templates (`f"Dear {booking.primary_guest_name or 'Guest'}"`)

### 8.5 Unread Count Duplication

Two unread count views in chat:
1. `get_unread_count()` — newer version
2. `get_unread_conversation_count()` — older version with different query
Both mounted at different paths under `/api/chat/`.

### 8.6 Email Service Duplication

Two email sending paths:
1. `notifications/email_service.py` — booking confirmation, cancellation, management links
2. `hotel/email_utils.py` — **legacy** `send_booking_confirmation_email()` (appears to be old version)

---

## 9. UNUSED / DEAD / LEGACY CODE

### Dead Directories
| Path | Content | Status |
|------|---------|--------|
| `issues/` | 3 GitHub issue creation scripts + documentation | Dead project management tooling |
| `posts/` | Single `HIRO.jpg` image | Dead — not an app |
| `scripts/archive/` | 34 old stock_tracker debug scripts | Dead archive |
| `tools/` | 1 profitability check script | Dead utility |

### Dead Root-Level Scripts (13 files)
| File | Purpose |
|------|---------|
| `demo_time_controls.py` | Prints implementation summary |
| `manage_hotel_policies.py` | One-time policy setup |
| `room_validation.py` | Has AppConfig but NOT in INSTALLED_APPS |
| `seed_presets.py` | One-time seed |
| `validate_new_booking.py` | Import validation |
| `validate_precheckin.py` | Implementation validation |
| `validate_room_realtime.py` | Integration validation |
| `validate_staff_filtering.py` | Filter validation |
| `verify_api_fix.py` | Fix verification |
| `verify_canonical_room_status.py` | Status writer verification |
| `verify_companions_only_contract.py` | Party contract verification |
| `verify_payment_persistence.py` | Payment verification |
| `verify_token_match.py` | Token hash debugging |

### Dead/Inactive Code
| Item | Location | Status |
|------|----------|--------|
| `HotelSubdomainBackend` | `hotel/auth_backends.py` | Defined but NOT in `AUTHENTICATION_BACKENDS` |
| `HotelMiddleware` | `hotel/middleware.py` | Defined but NOT in `MIDDLEWARE` |
| `RoomValidationConfig` | `room_validation.py` | Has system check but NOT in `INSTALLED_APPS` |
| `staff_chat/pusher_utils.py` | All functions | Marked DEPRECATED — delegates to NM |
| `hotel/policy_management_urls.py` | URL patterns | Defined but `urlpatterns = []` (empty) — patterns in separate lists not used |
| `room_bookings/apps.py` | App config | Defined but NOT in `INSTALLED_APPS` |
| `stock_tracker/signals.py` | Signal file | **Empty** — imported but contains no handlers |

### Legacy Endpoints Still Mounted
| Endpoint | Where | Legacy Reason |
|----------|-------|---------------|
| `/api/chat/` | `HotelMateBackend/urls.py` | Entire chat module duplicated from before staff URL restructure |
| `/api/bookings/` | `HotelMateBackend/urls.py` | Restaurant bookings before staff URL restructure |
| `/api/room_services/` | `HotelMateBackend/urls.py` | Room services before staff URL restructure |
| `conversations/<id>/send_message/` | `staff_chat/urls.py` | Legacy underscore variant alongside hyphenated version |
| `conversations/<id>/mark_as_read/` | `staff_chat/urls.py` | Legacy underscore variant |

### Markdown Audit/Planning Files (not code, but clutter)
- `GUEST_CHAT_BACKEND_AUDIT.md`
- `GUEST_CHAT_CONTRACT_AUDIT.md`
- `GUEST_STAFF_CHAT_REALTIME_AUDIT.md`
- `STAFF_CHECKIN_VALIDATION_IMPLEMENTATION_PLAN.md`
- `pusher_debug_tool.html`

---

## 10. INCONSISTENCIES

### 10.1 URL Parameter Naming
| Pattern | Used By |
|---------|---------|
| `hotel_slug` (canonical) | chat, hotel, bookings, common, entertainment, staff_chat, housekeeping, notifications, home, hotel_info, maintenance |
| `hotel_identifier` (legacy) | rooms, voice_recognition, stock_tracker |

The `hotel/permissions.py` `IsHotelStaff` accepts **both** as a compatibility shim. This means some apps haven't migrated to canonical naming.

### 10.2 Payload Field Naming (Realtime vs API)
| Concept | API Serializer | Realtime Payload |
|---------|---------------|-----------------|
| Sender type | `sender_type` | `sender_role` |
| Conversation ID (numeric) | `conversation_id` | `room_conversation_id` |
| Conversation ID (string) | — | `conversation_id` (= booking_id string!) |
| Guest name | `guest_name` | `sender_name = "Guest"` (hardcoded) |
| Staff name | `staff_name` | `sender_name` |
| Staff info | `staff_info` (dict) | Not present |

### 10.3 Pusher Channel Naming Inconsistency
| Pattern | Examples |
|---------|---------|
| `{slug}.domain` (dot separator) | `{slug}.room-bookings`, `{slug}.rooms`, `{slug}.room-service`, `{slug}.attendance` |
| `{slug}-domain-{id}-chat` (dash separator) | `{slug}-conversation-{id}-chat`, `{slug}-stocktake-{id}` |
| `private-domain.{id}` (private prefix + dot) | `private-guest-booking.{id}` |
| `private-hotel-{slug}-domain-{id}` (compound) | `private-hotel-{slug}-guest-chat-booking-{bid}` |
| `attendance-{slug}-staff-{id}` (domain first) | Attendance alert channels |
| `{slug}` (bare slug) | Overstay events |

Six different naming patterns for Pusher channels. No consistent convention.

### 10.4 View Architecture Mix
| Style | Used By |
|-------|---------|
| `ModelViewSet` | Most CRUD operations |
| `ViewSet` with custom actions | Attendance, Staff Chat, Housekeeping |
| `APIView` subclass | Hotel booking views, payment, guest chat |
| `@api_view` function-based | Chat views, rate plans, cancellation policies, rooms turnover |
| Mixed in same app | chat (all FBV), staff_chat (ViewSet + FBV), hotel (all three) |

### 10.5 Serializer Import Inconsistency
The `staff_chat` app has 5 serializer files:
- `serializers.py` — original
- `serializers_staff.py` — staff-specific
- `serializers_messages.py` — message-specific
- `serializers_conversations.py` — conversation-specific
- `serializers_attachments.py` — attachment-specific

Some views import from the old `serializers.py`, others from the new split files. Potential for stale serializer usage.

### 10.6 DEBUG = True Hardcoded
`settings.py` line 32: `DEBUG = True` — not from environment variable. Risk in production.

---

## 11. FEATURES NOT WIRED INTO COMPLETE FLOWS

| Feature | Status | What's Missing |
|---------|--------|----------------|
| `HotelSubdomainBackend` | Code exists | Not in `AUTHENTICATION_BACKENDS` — never activated |
| `HotelMiddleware` | Code exists | Not in `MIDDLEWARE` — never runs |
| `room_validation.py` system check | Code exists | Not in `INSTALLED_APPS` — check never runs |
| `Django Channels` | In INSTALLED_APPS | No consumers, no routing — WebSocket support installed but unused (all realtime goes through Pusher) |
| `dal` / `dal_select2` | In INSTALLED_APPS | Autocomplete library — unclear what admin forms use it |
| `hotel/policy_management_urls.py` | URL patterns defined | `urlpatterns = []` — patterns defined in separate lists but never included |
| `room_bookings` app | Has apps.py, services, urls | NOT in INSTALLED_APPS — works as a code module but isn't a registered Django app |
| `stock_tracker/signals.py` | File exists, imported in `apps.py` | **Empty file** — no signal handlers defined |
| `RoomBooking.survey_send_at` field | Field on model | Used by `send_scheduled_surveys` command — requires Heroku Scheduler setup to actually trigger |
| `RoomTypeInventory` model | Full model with `stop_sell` | Queried in availability service but no admin/API endpoint to manage inventory |
| `StaffAvailability` model | Full model | No URL endpoint to manage availability declarations |
| `ShiftTemplate` model | Full model | No URL endpoint to manage shift templates |
| `RosterRequirement` model | Full model | No URL endpoint to manage staffing requirements |
| Attachment details in realtime | `has_attachments` bool only | Full attachment data available but only boolean sent in realtime events |
| `Guest.in_house` property | Property exists | Date-based check that may not account for timezone properly |

---

## 12. RAW FEATURE INVENTORY

### By implementation completeness:

**FULLY IMPLEMENTED & WIRED:**
1. Hotel CRUD + multi-tenant scoping
2. Room type + room management
3. Rate plans + daily rates + promotions
4. Availability checking + inventory
5. Pricing engine + quote generation
6. Booking creation (public + guest)
7. Stripe payment (sessions + webhooks + verify)
8. Booking approval/decline workflow
9. Auto-expiry of overdue bookings
10. Room assignment/unassign/move (atomic)
11. Check-in with policy validation
12. Check-out with full teardown
13. Overstay detection + acknowledgment + extension
14. Cancellation with tiered policies + penalties
15. Booking party management (primary + companions)
16. Pre-check-in via tokenized links
17. Post-checkout survey via tokenized links
18. Booking management via tokenized links
19. Booking integrity self-healing
20. Guest portal with token auth
21. Guest–staff chat (realtime)
22. Staff-to-staff chat (realtime, reactions, threads, forwards)
23. Staff auth (registration, login, password reset)
24. Staff profile management
25. Navigation-based permissions
26. Clock in/out with break tracking
27. Face recognition attendance
28. Roster management (periods, shifts, copy, finalize)
29. Daily plan generation
30. Roster analytics (6 dimensions)
31. PDF export (rosters, daily plans)
32. Attendance alerts (break, overtime, hard limit)
33. Auto-clock-out excessive sessions
34. Housekeeping status machine
35. Housekeeping tasks with SLA
36. Room service ordering + management
37. Breakfast ordering + management
38. Restaurant management with blueprints
39. Dining table management (shapes, positions, joins)
40. Restaurant table booking + assignment
41. Memory game (cards, sessions, scores, leaderboards)
42. Memory game tournaments
43. Memory game achievements
44. Quiz system (categories, questions, sessions)
45. Quiz tournaments
46. Quiz leaderboards
47. Stock item management with profitability
48. Stock periods with open/close lifecycle
49. Stocktake workflow (populate → count → approve)
50. Stock movements + variance analysis
51. Cocktail recipe management
52. Cocktail consumption tracking + cost
53. Stock comparison analytics (6 report types)
54. PDF/Excel stock reports
55. Voice command for stock operations
56. Maintenance request management
57. Hotel info content management
58. QR code generation (hotels, games, restaurants)
59. Public page CMS (sections, elements, galleries, cards, news)
60. Staff social feed (posts, likes, comments, replies)
61. Theme customization per hotel
62. Cancellation policy management
63. Email notifications (booking, survey, management)
64. FCM push notifications
65. Pusher realtime events (40+ event types)

**PARTIALLY IMPLEMENTED / NO ENDPOINTS:**
66. Room type inventory management (model exists, no CRUD endpoints)
67. Staff availability declarations (model exists, no CRUD endpoints)
68. Shift templates (model exists, no CRUD endpoints)
69. Roster requirements (model exists, no CRUD endpoints)
70. Good to Know entries (endpoints exist but tightly coupled to hotel_info)

**DEFINED BUT NOT ACTIVE:**
71. Hotel subdomain authentication backend
72. Hotel subdomain middleware
73. Room validation system check
74. Django Channels (WebSocket — installed, never used)
75. Policy management URL patterns (defined but empty urlpatterns)

---

## 13. SURPRISING OR HIDDEN CAPABILITIES

1. **Voice-to-stock pipeline** — Full OpenAI Whisper → command parsing → fuzzy matching → LLM reasoning → stock operation pipeline. Lets staff verbally update stock counts. Hidden inside `voice_recognition/` app, only accessible through stock_tracker URLs.

2. **Booking integrity self-healing engine** — `hotel/services/booking_integrity.py` can detect and auto-fix data inconsistencies across bookings, parties, guests, and room occupancy. Runs as management command or triggered by staff.

3. **Tiered cancellation policy engine** — Full penalty calculation with time-based tiers, no-show penalties, and Stripe refund integration. Supports percentage and fixed-amount penalties per tier.

4. **Restaurant blueprint/floor plan system** — Coordinate-based table layout with shapes (circle, rectangle, square, oval, L), rotations, joinable table groups, and angular seat positions. Essentially a restaurant floor plan editor.

5. **Full tournament infrastructure** — Both memory game and quiz tournaments with registration deadlines, participant management, scoring, prizes, QR code generation, and automatic status lifecycle management.

6. **Cocktail ingredient consumption merge** — Tracks ingredient usage from cocktail production and can automatically merge consumption records into stocktake lines for accurate variance calculations.

7. **Staff face recognition** — Cloudinary-stored face encodings with consent tracking, face audit logging, and face-based clock-in verification. Includes configurable minimum confidence thresholds per hotel.

8. **Overstay detection → extension flow** — Detects checkout deadline violations, notifies staff, allows acknowledgment, and can extend stays with Stripe re-charge — all in realtime.

9. **Booking phase auto-expiry** — PENDING_APPROVAL bookings automatically expire past their deadline with refund processing, triggered by a scheduled management command.

10. **Guest chat session grants** — HMAC-signed, time-limited tokens issued at chat bootstrap, validated on each subsequent message. Separate from the main booking token, scoped specifically to chat operations.

11. **6-dimension stock comparison analytics** — Category comparison, top movers, cost analysis, trend analysis, variance heatmap, and performance scorecard. More sophisticated than typical hotel stock systems.

12. **Dual booking system** — Room bookings and restaurant/dining bookings are completely separate domains with different models, different views, different serializers. The `bookings/` app is the restaurant side.

13. **Public page CMS** — Full section-based page builder with presets, style variants, hero sections, galleries, cards, news with content blocks. Hotels can customize their public landing pages.

14. **Navigation-based permissions** — Staff access is controlled by which navigation items they can see, rather than traditional role-based permissions. Each staff member has a configurable set of UI sections.

---

## 14. DANGEROUS INCONSISTENCIES

### CRITICAL

1. **`DEBUG = True` hardcoded** — `settings.py` line 32. Not from environment variable. If this reaches production, detailed error pages and stack traces are exposed to users.

2. **11 ViewSets registered in TWO routers** — `hotel/urls.py` and `staff_urls.py` both register the same CMS ViewSets. Requests can succeed via either path with potentially different authentication/permission contexts. The `hotel/urls.py` router doesn't require `hotel_slug` in the URL but the staff path does.

3. **Legacy chat endpoints mounted without hotel scoping** — `/api/chat/<slug>/` endpoints use the same views as `/api/staff/hotel/<slug>/chat/` but the legacy path has no wrapper enforcing the staff hotel match. A staff member could potentially interact with conversations from a different hotel.

4. **Guest chat realtime payload hardcodes `sender_name = "Guest"`** — As documented in your audit. The real name is in `current_booking.guest_display_name`, already loaded, just not used.

5. **Staff notification badges hardcode `sender_name = "Guest"`** — `_notify_front_office_staff_of_guest_message()` line 1470. Staff see "Guest" instead of the actual guest name in all notification badges.

6. **Pusher client singleton lives in `chat/utils.py`** — A project-wide infrastructure component living in a domain-specific app. 12+ files import it. If chat app is ever removed/refactored, the entire realtime system breaks.

### HIGH

7. **12 direct Pusher bypass paths** — Attendance (12 calls), stock_tracker (all calls), hotel/staff_views (3 calls) bypass NotificationManager entirely. No centralized logging, rate limiting, or error handling for these events.

8. **3 separate FCM token save endpoints** — Staff FCM tokens saved via `/api/staff/save-fcm-token/`, `/api/notifications/save-fcm-token/`, and `/api/chat/<slug>/save-fcm-token/`. Guest FCM tokens via `/room/<room>/save-fcm-token/`. No single source of truth for token management.

9. **`hotel_identifier` vs `hotel_slug` naming split** — rooms, voice_recognition, and stock_tracker still use `hotel_identifier`. The permission layer handles both, but this means URL consistency is broken and any future permission tightening could break these apps.

10. **Realtime payload shape incompatible with serializer** — `RoomMessageSerializer` returns 30 fields; realtime payload returns 13 with different field names. Frontend must maintain two separate data-handling paths for the same domain object.

11. **`room_bookings` not in INSTALLED_APPS** — Functions perfectly as a service layer but its `apps.py` is orphaned. Any `AppConfig.ready()` hooks or management commands defined in this app would silently not load.

### MEDIUM

12. **Dual unread count views** — `get_unread_count()` and `get_unread_conversation_count()` both mounted in chat URLs. Different query logic, same concept. Frontend may call wrong one.

13. **Email service duplication** — `notifications/email_service.py` and `hotel/email_utils.py` both have `send_booking_confirmation_email()`. The hotel version appears to be legacy.

14. **System messages get `sender_name = "Guest"`** — No branch for `sender_type == "system"` in notification_manager. System join messages tagged as "Guest".

15. **6 different Pusher channel naming conventions** — Dot separators, dash separators, private prefixes, bare slugs. No consistent pattern. Easy to get channel subscriptions wrong.

16. **`StaffAvailability`, `ShiftTemplate`, `RosterRequirement` models have no API endpoints** — Data can be created via admin or management commands but staff-facing UI has no way to manage these.
