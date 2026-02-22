# Models & Relationships

> Complete model inventory with fields, relationships, and constraints.
> Source: direct reading of each app's `models.py`.

---

## hotel app — `hotel/models.py` (3042 lines)

### Hotel
| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(255) | |
| `slug` | SlugField | unique |
| `code` | CharField(10) | unique |
| `hero_image` | CloudinaryField | nullable |
| `description` | TextField | |
| `star_rating` | IntegerField | nullable |
| `total_rooms` | PositiveIntegerField | default=0 |
| `address`, `city`, `state`, `country`, `postal_code` | CharFields | |
| `latitude`, `longitude` | DecimalField | nullable |
| `phone`, `email`, `website` | CharFields | |
| `tags` | JSONField | default=list |
| `hotel_type` | CharField(20) | 20 choices (boutique, resort, hostel, etc.) |
| `preset` | FK → `Preset` | nullable |
| `is_published` | BooleanField | default=False |

**Relationships:** Has many `RoomBooking`, `PricingQuote`, `SurveyResponse`, `GuestBookingToken`. Has one `HotelAccessConfig`, `BookingOptions`, `HotelPublicPage`, `HotelSurveyConfig`, `HotelPrecheckinConfig`, `HotelAttendanceConfig`.

### RoomBooking ⭐ (~100 fields)
| Field Group | Key Fields |
|-------------|-----------|
| Identity | `booking_id` (auto, unique), `booking_reference` (auto, unique) |
| Core FKs | `hotel` → Hotel, `room_type` → rooms.RoomType |
| Dates | `check_in_date`, `check_out_date` |
| Booker | `booker_first_name`, `booker_last_name`, `booker_email`, `booker_phone` |
| Primary Guest | `guest_first_name`, `guest_last_name`, `guest_email`, `guest_phone` |
| Payment | `payment_status` (PENDING/PAID/REFUNDED/PARTIAL_REFUND), `stripe_payment_intent_id`, `stripe_session_id`, `total_amount`, `amount_paid` |
| Approval | `approval_status` (PENDING/APPROVED/DECLINED), `approved_by` → Staff, `approval_deadline`, `approved_at` |
| Assignment | `assigned_room` → rooms.Room, `room_assigned_at`, `room_assigned_by`, `assignment_version` |
| Status | `status` choices: PENDING_PAYMENT, PENDING_APPROVAL, CONFIRMED, IN_HOUSE, COMPLETED, DECLINED, CANCELLED, CANCELLED_DRAFT, EXPIRED, NO_SHOW |
| Overstay | `is_overstay`, `overstay_acknowledged_at` |
| Refund | `refund_amount`, `refund_reason` |
| Cancellation | `cancellation_policy` → CancellationPolicy, `cancelled_at`, `cancelled_by_type`, `cancellation_fee`, `cancellation_refund_amount` |
| Survey | `survey_sent_at`, `survey_completed_at`, `survey_send_scheduled_at` |
| Pre-checkin | `precheckin_data` (JSONField), `precheckin_completed_at` |
| Staff tracking | `seen_by_staff`, `checked_in_by` → Staff |

**Indexes:** 8 composite indexes including `(hotel, status)`, `(hotel, check_in_date, check_out_date)`, `(hotel, booking_id)`.

### GuestBookingToken
| Field | Type | Notes |
|-------|------|-------|
| `token_hash` | CharField(64) | SHA-256, unique |
| `booking` | FK → RoomBooking | CASCADE |
| `hotel` | FK → Hotel | CASCADE (denormalized) |
| `raw_token_preview` | CharField(8) | first 8 chars for debugging |
| `status` | CharField | ACTIVE / REVOKED |
| `scopes` | JSONField | `['STATUS_READ', 'CHAT', 'ROOM_SERVICE']` |
| `expires_at` | DateTimeField | checkout + 30 days |
| `last_used_at` | DateTimeField | nullable |

**Constraint:** One active token per booking (unique on `booking` where `status=ACTIVE`).

### CancellationPolicy
| Field | Type | Notes |
|-------|------|-------|
| `hotel` | FK → Hotel | CASCADE |
| `name`, `description` | CharFields | |
| `template_type` | CharField | FLEXIBLE / MODERATE / NON_REFUNDABLE / CUSTOM |
| `free_cancellation_hours` | PositiveIntegerField | |
| `penalty_type` | CharField | FULL_STAY / FIRST_NIGHT / PERCENTAGE / FIXED / NONE |
| `penalty_value` | DecimalField | |
| `is_default` | BooleanField | |

**Constraint:** `unique_together('hotel', 'name')`.

### CancellationPolicyTier
| Field | Type | Notes |
|-------|------|-------|
| `policy` | FK → CancellationPolicy | CASCADE |
| `hours_before_checkin` | PositiveIntegerField | |
| `penalty_type`, `penalty_value` | CharField, Decimal | |

### BookingPartyMember
| Field | Type | Notes |
|-------|------|-------|
| `booking` | FK → RoomBooking | CASCADE |
| `role` | CharField | PRIMARY / COMPANION |
| `first_name`, `last_name`, `email`, `phone` | CharFields | |
| `precheckin_data` | JSONField | nullable |

**Constraint:** One PRIMARY per booking (unique constraint).

### PricingQuote
| Field | Type | Notes |
|-------|------|-------|
| `quote_id` | CharField | auto-generated |
| `hotel` | FK → Hotel | CASCADE |
| `room_type` | FK → rooms.RoomType | CASCADE |
| `nightly_breakdown`, `subtotal`, `vat_amount`, `vat_rate`, `total`, `currency` | Decimal/JSON | |
| `expires_at` | DateTimeField | |

### OverstayIncident
| Field | Type | Notes |
|-------|------|-------|
| `booking` | FK → RoomBooking | CASCADE |
| `hotel` | FK → Hotel | CASCADE |
| `status` | CharField | OPEN / ACKED / RESOLVED / DISMISSED |
| `acknowledged_by` / `resolved_by` / `dismissed_by` | FK → Staff | nullable |
| `extension_details` | JSONField | nullable |

### BookingExtension
| Field | Type | Notes |
|-------|------|-------|
| `booking` | FK → RoomBooking | CASCADE |
| `overstay_incident` | FK → OverstayIncident | nullable |
| `extended_by` | FK → User | CASCADE |
| `original_checkout` / `new_checkout` | DateField | |
| `extension_amount`, `total_new_amount`, `currency` | Decimal/CharField | |
| `stripe_payment_intent_id` | CharField | nullable |

### HotelAccessConfig (OneToOne → Hotel)
Portal toggles, PIN settings, session limits, time controls (`check_in_time`, `check_out_time`, `checkout_grace_minutes`, `approval_deadline_minutes`).

### HotelPublicPage, PublicPageSection, SectionElement, ElementItem, HeroSection
CMS system for public hotel pages — nested structure: Page → Sections → Elements → Items.

### Gallery, GalleryImage, ListContainer, Card, NewsItem, ContentBlock, RoomsSection
Additional CMS content types, each with FK to their parent section/element.

### PrecheckinToken, BookingManagementToken, SurveyToken, SurveyResponse
Token-based guest access for pre-checkin forms, booking management, and post-checkout surveys.

### StripeWebhookEvent
| Field | Type | Notes |
|-------|------|-------|
| `event_id` | CharField | unique (Stripe event ID) |
| `event_type`, `booking_id`, `payment_intent_id` | CharFields | |
| `processed_at` | DateTimeField | auto_now_add |

---

## rooms app — `rooms/models.py`

### Room
| Field | Type | Notes |
|-------|------|-------|
| `hotel` | FK → Hotel | CASCADE |
| `number` | IntegerField | unique_together with hotel |
| `is_occupied` | BooleanField | default=False |
| `device_token` | CharField(255) | nullable, FCM token |
| `room_type` | FK → RoomType | PROTECT, nullable |
| `is_active`, `is_bookable` | BooleanField | |
| `status` | CharField(20) | 7 choices (see State Machines doc) |
| `cleaned_at` | DateTimeField | nullable |
| `cleaned_by` | FK → Staff | nullable |
| `inspected_at` | DateTimeField | nullable |
| `inspected_by` | FK → Staff | nullable |
| `maintenance_notes` | TextField | |
| `has_maintenance_issue`, `maintenance_priority` | Bool/CharField | |

### RoomType
| Field | Type | Notes |
|-------|------|-------|
| `hotel` | FK → Hotel | CASCADE |
| `name`, `code` | CharField | |
| `max_occupancy` | IntegerField | |
| `starting_price_from` | DecimalField | |
| `photo` | CloudinaryField | nullable |
| `currency` | CharField | default='EUR' |
| `is_active` | BooleanField | |

### RatePlan
| Field | Type | Notes |
|-------|------|-------|
| `hotel` | FK → Hotel | CASCADE |
| `name`, `code` | CharField | unique on (hotel, code) |
| `cancellation_policy` | FK → CancellationPolicy | nullable |

### RoomTypeRatePlan
Junction: `room_type` → RoomType + `rate_plan` → RatePlan + `base_price` override. Unique on (room_type, rate_plan).

### DailyRate
| Field | Type | Notes |
|-------|------|-------|
| `room_type_rate_plan` | FK → RoomTypeRatePlan | CASCADE |
| `hotel` | FK → Hotel | CASCADE |
| `date` | DateField | |
| `price` | DecimalField | |

**Unique on** `(room_type_rate_plan, date)`.

### Promotion
| Field | Type | Notes |
|-------|------|-------|
| `hotel` | FK → Hotel | CASCADE |
| `promo_code` | CharField | unique |
| `discount_type` | CharField | PERCENTAGE / FIXED |
| `applicable_room_types` | M2M → RoomType | |
| `applicable_rate_plans` | M2M → RatePlan | |
| `valid_from`, `valid_to` | DateField | |
| `is_active`, `is_stackable` | BooleanField | |

### RoomTypeInventory
Daily inventory override: `room_type` + `date` + `available_units`. Unique on (room_type, date).

---

## guests app — `guests/models.py`

### Guest
| Field | Type | Notes |
|-------|------|-------|
| `hotel` | FK → Hotel | CASCADE, nullable |
| `first_name`, `last_name` | CharField(100) | |
| `room` | FK → Room | SET_NULL, nullable |
| `number_of_guests` | PositiveIntegerField | default=1 |
| `check_in_date`, `check_out_date` | DateField | nullable |
| `pin` | CharField(4) | unique, nullable |
| `booking` | FK → rooms.Room | SET_NULL, nullable (legacy) |
| `guest_type` | CharField | PRIMARY / COMPANION / WALKIN |
| `primary_guest` | FK → self | SET_NULL, nullable |
| `source_booking` | FK → RoomBooking | SET_NULL, nullable |

---

## staff app — `staff/models.py`

### Staff
| Field | Type | Notes |
|-------|------|-------|
| `user` | OneToOne → User | nullable |
| `hotel` | FK → Hotel | CASCADE |
| `department` | FK → Department | SET_NULL, nullable |
| `role` | FK → Role | SET_NULL, nullable |
| `access_level` | CharField(20) | staff_admin / super_staff_admin / regular_staff |
| `first_name`, `last_name` | CharField(100) | |
| `email` | EmailField | unique, nullable |
| `duty_status` | CharField(20) | off_duty / on_duty / on_break |
| `device_token` | CharField(255) | FCM token, nullable |
| `profile_image` | CloudinaryField | |
| `nav_permissions` | M2M → NavigationItem | |

### Department
`name` (unique), `slug` (unique), `description`.

### Role
`department` FK (nullable), `name` (unique), `slug` (unique), `description`.

### NavigationItem
`hotel` FK, `label`, `slug`, `icon`, `path`, `category`, `position`, `is_active`, `requires_role`. Unique on (hotel, slug).

### RegistrationCode
`code` (unique), `hotel` FK, `user` OneToOne (nullable), `department`, `role`, `qr_token` (unique, nullable), `used`.

### UserProfile
`user` OneToOne, `registration_code` OneToOne (nullable).

---

## bookings app — `bookings/models.py`

### Restaurant
`hotel` FK, `name`, `slug`. UniqueConstraint on (hotel, slug).

### DinnerBooking
`date`, `start_time`, `end_time`, `special_requests`, `status`, `is_seen`. FKs: `hotel`, `restaurant`, `room` (nullable), `guest` (nullable), `booking` (nullable, → RoomBooking).

### Blueprint
`restaurant` FK, `name`, `width`, `height`, `background_image` (CloudinaryField). UniqueConstraint on (restaurant, name).

### DiningTable
`restaurant` FK, `blueprint` FK (nullable), `name`, `shape` (RECT/CIRCLE/OVAL), dimensions, position, capacity.

### BookingTable
Junction: `booking` → DinnerBooking + `table` → DiningTable. Validates seat capacity and time overlap.

---

## chat app — `chat/models.py`

### Conversation
`hotel` FK, `has_unread` Bool, `participants_staff` M2M → Staff.

### RoomMessage
`conversation` FK, `room` FK, `sender_staff` FK (nullable), `sender_type` (guest/staff/system), `message`, `status` (pending/delivered/read), `read_by_staff`, `read_by_guest`, `is_deleted`, `reply_to` self-FK.

### MessageAttachment
`message` FK, `file` CloudinaryField, `file_type`, `file_size` (50MB max), `mime_type`.

---

## staff_chat app — `staff_chat/models.py`

### StaffConversation
`hotel` FK, `title`, `is_group`, `is_archived`, `has_unread`, `group_avatar` CloudinaryField, `created_by` FK → Staff, `participants` M2M → Staff.

### StaffMessage
`conversation` FK, `sender` FK → Staff, `message`, `status`, `is_edited`, `is_deleted`, `reply_to` self-FK, `read_by` M2M → Staff, `mentions` M2M → Staff.

### StaffMessageAttachment
`message` FK, `file` CloudinaryField, `file_name`, `file_type`, `file_size`, `mime_type`.

### MessageReaction
`message` FK, `staff` FK, `emoji` (10 choices). UniqueConstraint on (message, staff, emoji).

---

## attendance app — `attendance/models.py`

### FaceDescriptor
`staff` OneToOne, `hotel` FK, `image` CloudinaryField, `encoding` JSONField (128-dim), `consent_given` Bool, `registered_by` FK → Staff.

### ClockLog
`staff` FK, `hotel` FK, `time_in`/`time_out` DateTimeField, `verified_by_face` Bool, `auto_clock_out` Bool, `hours_worked` Decimal, `is_unrostered` Bool, `is_approved`/`is_rejected` Bool, break tracking, overtime/hard-limit flags, `roster_shift` FK → StaffRoster.

### RosterPeriod
`hotel` FK, `title`, `start_date`/`end_date`, `published` Bool, `is_finalized` Bool, `finalized_by` FK → Staff.

### StaffRoster
`roster_period` FK, `staff` FK, `department` FK, `shift_date`, `shift_start`/`shift_end`, `break_start`/`break_end`, `shift_type`, `expected_hours`, `shift_location` FK. Unique on (roster_period, staff, shift_date).

### ShiftLocation, StaffingRequirement, ShiftLabel, DailyPlan, DailyPlanEntry, RosterBulkOperation, FaceAuditLog
Additional models for shift management, daily planning, bulk operations, and face recognition audit trail.

---

## room_services app — `room_services/models.py`

### RoomServiceItem
`hotel` FK, `name`, `price`, `image` CloudinaryField, `category` (Starters/Mains/Desserts/Drinks/Others), `is_on_stock` Bool.

### Order
`hotel` FK, `room_number` CharField, `status` (pending/accepted/completed), `items` M2M → RoomServiceItem (through OrderItem). **Property:** `total_price`.

### BreakfastItem, BreakfastOrder, BreakfastOrderItem
Parallel structure for breakfast orders with `delivery_time` time slots.

---

## stock_tracker app — `stock_tracker/models.py` (2633 lines)

### Core: StockCategory → StockItem → StockMovement
- **StockCategory**: `code` PK (D/B/S/W/M), `name`.
- **StockItem**: `hotel` FK, `sku`, `name`, `category` FK, `subcategory`, `size`/`unit`/`uom`, `unit_cost`, `current_full_units`/`current_partial_units`, `par_level`, multiple price fields. Computed: `cost_per_serving`, `total_stock_in_servings`, `gross_profit_percentage`, `markup_percentage`, `pour_cost_percentage`.
- **StockMovement**: `hotel` FK, `stock_item` FK, `period` FK, `movement_type` (PURCHASE/SALE/WASTE/TRANSFER/ADJUSTMENT/COCKTAIL_CONSUMPTION), `quantity`, `unit_cost`.

### Period System: StockPeriod → StockSnapshot → Stocktake → StocktakeLine
- **StockPeriod**: `hotel` FK, `period_type`, dates, `is_closed`, `manual_sales`/`manual_purchases`.
- **Stocktake**: `hotel` FK, `period` FK, `status` (DRAFT/APPROVED), `approved_by` FK.
- **StocktakeLine**: Full inventory snapshot per item with opening, purchases, waste, adjustments, counted units, manual overrides, valuation cost.

### Cocktail System: Cocktail → CocktailIngredient, CocktailConsumption
Junction tables linking cocktails to stock items with consumption tracking.

### Sale
Per-item sales records with `quantity`, `unit_cost`, `unit_price`, `total_revenue`, gross profit calculations.

---

## Other Apps (Smaller Models)

### maintenance — `maintenance/models.py`
- **MaintenanceRequest**: `hotel` FK, `room` FK (nullable), `status` (open/in_progress/resolved/closed), `reported_by`/`accepted_by` FK → Staff.
- **MaintenanceComment**: `request` FK, `author` FK → Staff.
- **MaintenancePhoto**: `request` FK, `image` CloudinaryField.

### entertainment — `entertainment/models.py` (1499 lines)
- **Game**, **HighScore**, **GameQRCode** — basic game + leaderboard.
- **MemoryCard**, **MemorySession**, **MemoryPlayerStats** — memory match game.
- **MemoryTournament**, **TournamentParticipant**, **Achievement**, **PlayerAchievement** — tournament system.
- **QuizCategory**, **QuizQuestion**, **QuizSession**, **QuizAnswer**, **QuizLeaderboard**, **QuizTournament** — quiz (Guessticulator).

### hotel_info — `hotel_info/models.py`
- **HotelInfoCategory**, **HotelInfoCategoryQR**, **HotelInfoEvent**, **GoodToKnow**.

### home — `home/models.py`
- **Post**, **Like**, **Comment**, **Reply** — staff noticeboard.

### housekeeping — `housekeeping/models.py`
- **RoomStatusLog**: Immutable audit trail (hotel, room, from_status, to_status, changed_by, trigger, notes).
- **HousekeepingTask**: Workflow (hotel, room, booking FK, task_type, status, priority, assigned_to, created_by, SLA tracking).

### common — `common/models.py`
- **ThemeSettings**: OneToOne → Hotel, color fields (main, secondary, background, text, border, button, link).

### notifications — `notifications/models.py`
- ⚠️ No models — file contains a misplaced `SaveFcmTokenView` class.
