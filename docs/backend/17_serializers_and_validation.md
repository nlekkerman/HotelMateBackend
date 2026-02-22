# Serializers & Validation

> Documents all serializer classes grouped by app, with their validation rules and notable behaviors.

---

## 1. Hotel App Serializers

**Source:** `hotel/serializers.py` (re-exports), `hotel/base_serializers.py`, `hotel/public_serializers.py`, `hotel/booking_serializers.py`, `hotel/canonical_serializers.py`, `hotel/staff_serializers.py`, `hotel/cancellation_policy_serializers.py`, `hotel/rate_plan_serializers.py`

### Base / Admin Serializers (`hotel/base_serializers.py`)

| Serializer | Model | Purpose |
|-----------|-------|---------|
| `PresetSerializer` | Preset | Full CRUD |
| `AccessConfigSerializer` | HotelAccessConfig | Minimal config |
| `HotelSerializer` | Hotel | Full admin serializer (superuser CRUD) |
| `HotelPublicPageSerializer` | HotelPublicPage | Public page config |

### Public Serializers (`hotel/public_serializers.py`)

| Serializer | Model | Purpose |
|-----------|-------|---------|
| `PublicHotelSerializer` | Hotel | Public hotel card (logo, portal flags, booking_options) |
| `PublicElementItemSerializer` | ElementItem | CMS items with Cloudinary URLs |
| `PublicSectionElementSerializer` | SectionElement | Elements with nested items |
| `PublicPageSectionSerializer` | PublicPageSection | Sections with elements |
| `PublicHeroSerializer` | HeroSection | Hero banner with absolute image URLs |
| `PublicGalleryImageSerializer` | GalleryImage | Gallery images |
| `PublicGallerySerializer` | Gallery | Gallery container with images |
| `PublicCardSerializer` | Card | Cards with preset |
| `PublicListContainerSerializer` | ListContainer | List containers with cards |
| `PublicContentBlockSerializer` | ContentBlock | Text/image blocks |
| `PublicNewsItemSerializer` | NewsItem | News items with content blocks |
| `PublicRoomTypeWithRatePlanSerializer` | RoomType | Room type + rate plan combo for public display |
| `PublicRoomTypeSerializer` | RoomType | Legacy simple room type display |
| `PublicRoomsSectionSerializer` | RoomsSection | Rooms section with live data query |
| `PublicFullSectionSerializer` | PublicPageSection | Full section with all nested content types |

### Booking Serializers (`hotel/booking_serializers.py`)

| Serializer | Model | Purpose | Validation |
|-----------|-------|---------|-----------|
| `BookingOptionsSerializer` | BookingOptions | CTA configuration | — |
| `BookingPartyMemberSerializer` | BookingPartyMember | Party members | — |
| `BookingRoomTypeSerializer` | RoomType | Marketing info for booking flow | — |
| `PricingQuoteSerializer` | PricingQuote | Quote with nightly breakdown | — |
| `BookingListSerializer` | RoomBooking | Minimal list view | — |
| `BookingDetailSerializer` | RoomBooking | Full detail view | — |
| `ExternalBookingDetailSerializer` | RoomBooking | External-facing detail | — |

### Canonical Serializers (`hotel/canonical_serializers.py`, 617 lines)

| Serializer | Purpose | Notable |
|-----------|---------|---------|
| `CanonicalPartyMemberSerializer` | Party member (canonical format) | — |
| `GroupedBookingPartySerializer` | Primary + companions grouped | — |
| `InHouseGuestSerializer` | Guest record from Guest model | — |
| `GroupedInHouseGuestsSerializer` | Grouped in-house guests | — |
| `StaffBookingListSerializer` | Staff booking list with time warnings | Computes `approval_risk_level`, `checkout_risk_level` using `booking_deadlines` and `stay_time_rules` |
| `StaffBookingDetailSerializer` | Full detail with flags | Includes `party`, `in_house_guests`, `overstay_incidents`, `extensions`, `available_rooms` |

### Staff CRUD Serializers (`hotel/staff_serializers.py`)

| Serializer | Purpose | Validation |
|-----------|---------|-----------|
| `StaffAccessConfigSerializer` | Access config with time controls | — |
| `StaffRoomTypeSerializer` | Room type CRUD | — |
| `StaffElementItemSerializer` | Element item CRUD | — |
| `StaffSectionElementSerializer` | Element CRUD | — |
| `StaffPublicPageSectionSerializer` | Section CRUD | — |
| `StaffGalleryImageSerializer` | Gallery image | — |
| `StaffGallerySerializer` | Gallery container | — |
| `BulkGalleryImageUploadSerializer` | Bulk image upload | Validates 1-20 images |
| `StaffRoomsSectionSerializer` | Rooms section | — |

### Policy Serializers

| Serializer | Purpose |
|-----------|---------|
| `CancellationPolicySerializer` | Full policy with nested tiers |
| `CancellationPolicyListSerializer` | Simplified policy list |
| `CancellationPolicyTierSerializer` | Individual tier |
| `RatePlanSerializer` | Rate plan with cancellation policy |
| `RatePlanListSerializer` | Simplified rate plan list |

---

## 2. Rooms App Serializers (`rooms/serializers.py`)

| Serializer | Model | Notable |
|-----------|-------|---------|
| `RoomSerializer` | Room | Includes computed: `guest_name`, `guest_count`, `current_guests` (grouped), `active_booking_id`, `checkout_risk`, `booking_checkout_date`, `check_out_time` |
| `RoomInventorySerializer` | Room | Inventory management subset |
| `RoomTypeSerializer` | RoomType | Basic: id, name, code, max_occupancy, starting_price_from, currency, is_active |

---

## 3. Guests App Serializer (`guests/serializers.py`)

| Serializer | Model | Notable |
|-----------|-------|---------|
| `GuestSerializer` | Guest | Computed: `is_current_guest` (date-based), `room_number`. Includes first/last name, email, phone, pin, guest_type, primary_guest |

---

## 4. Staff App Serializers (`staff/serializers.py`, 533 lines)

| Serializer | Model | Purpose |
|-----------|-------|---------|
| `NavigationItemSerializer` | NavigationItem | Full CRUD |
| `DepartmentSerializer` | Department | id, name, slug, description |
| `RoleSerializer` | Role | id, name, slug, description, department |
| `StaffListSerializer` | Staff | Compact with nested hotel/dept/role |
| `UserSerializer` | User | User CRUD with reg code handling |
| `StaffSerializer` | Staff | Full with user data, nav permissions, `current_status` |
| `LoginSerializer` | — | username + password validation |
| `LoginResponseSerializer` | — | Token + canonical permissions payload |
| `StaffWithAttendanceSerializer` | Staff | Extends StaffSerializer with attendance aggregations |
| `CreateStaffSerializer` | Staff | Create from `user_id` |
| `RegistrationCodeSerializer` | RegistrationCode | Code + QR info |

**⚠️ Issue:** `StaffWithAttendanceSerializer` redefines parent FK-based fields (department, role, hotel) with `CharField`/`SerializerMethodField` — can cause serialization inconsistencies.

---

## 5. Bookings App Serializers (`bookings/serializers.py`)

| Serializer | Model | Validation |
|-----------|-------|-----------|
| `CategorySerializer` | BookingCategory | Read: id, name, slug |
| `BookingSerializer` | Booking | Nests `CategorySerializer`; calls `category.clean()` on create/update |
| `RestaurantSerializer` | Restaurant | Read-only: image, slug, hotel, hotel_slug |
| `SeatsSerializer` | Seats | total, adults, children, infants |
| `DiningTableSerializer` | DiningTable | Validates shape/dimension consistency |
| `BlueprintSerializer` | Blueprint | Nests `DiningTableSerializer` read; accepts `dining_tables` write |
| `DinnerBookingSerializer` | DinnerBooking | Read: category_detail, restaurant, seats, room, guest, booking_tables |
| `DinnerBookingCreateSerializer` | DinnerBooking | Write: adults/children/infants → creates `Seats`; calls `Seats.clean()` |
| `BookingTableSerializer` | BookingTable | Nests tables |
| `FullBlueprintSerializer` | Blueprint | Nests areas; includes background_image, restaurant_slug |
| `BlueprintObjectTypeSerializer` | BlueprintObjectType | Simple CRUD |
| `BlueprintObjectSerializer` | BlueprintObject | Nests type read; accepts type_id + blueprint_id write |

---

## 6. Chat App Serializers (`chat/serializers.py`)

| Serializer | Model | Notable |
|-----------|-------|---------|
| `ConversationSerializer` | Conversation | Includes participants, message count |
| `RoomMessageSerializer` | RoomMessage | Includes sender info, attachments, reply chain |
| `MessageAttachmentSerializer` | MessageAttachment | File metadata (50MB max) |

---

## 7. Staff Chat Serializers (`staff_chat/serializers*.py`)

| Serializer | Model | Purpose |
|-----------|-------|---------|
| `StaffConversationListSerializer` | StaffConversation | List with last message, unread count |
| `StaffConversationDetailSerializer` | StaffConversation | Full with participants |
| `StaffConversationCreateSerializer` | StaffConversation | Create 1:1 or group |
| `StaffMessageSerializer` | StaffMessage | Full message with reactions, read_by |
| `StaffMessageCreateSerializer` | StaffMessage | Create with optional reply_to, mentions |
| `StaffMessageAttachmentSerializer` | StaffMessageAttachment | File metadata |
| `MessageReactionSerializer` | MessageReaction | Emoji reaction |
| `StaffChatStaffSerializer` | Staff | Minimal staff info for chat UI |

---

## 8. Attendance App Serializers (`attendance/serializers.py`, `attendance/serializers_analytics.py`)

| Serializer | Purpose |
|-----------|---------|
| `ClockLogSerializer` | Clock in/out records with computed hours, break time |
| `RosterPeriodSerializer` | Period CRUD with shift counts |
| `StaffRosterSerializer` | Individual shift assignment |
| `ShiftLocationSerializer` | Location CRUD |
| `DailyPlanSerializer` | Daily plan with entries |
| `DailyPlanEntrySerializer` | Plan entry with staff/shift info |
| `FaceDescriptorSerializer` | Face registration data |
| `AttendanceAnalyticsSerializer` | Staff summary, department summary KPIs |

---

## 9. Housekeeping Serializers (`housekeeping/serializers.py`)

| Serializer | Purpose | Validation |
|-----------|---------|-----------|
| `RoomStatusLogSerializer` | Read-only audit events with `changed_by_name`, `trigger_display` | — |
| `HousekeepingTaskSerializer` | Full CRUD with computed `is_overdue`, `sla_hours`, display fields | Validates hotel scoping on all FK fields |
| `TaskAssignSerializer` | Assign staff to task | Validates `assigned_to` belongs to same hotel; checks `can_assign_tasks` policy |
| `RoomStatusChangeSerializer` | Status transition request | Validates `new_status` against `VALID_TRANSITIONS`; validates `trigger` against allowed triggers; checks `can_transition` RBAC; requires note for manager overrides |
| `DashboardRoomSerializer` | Room summary for dashboard | — |
| `DashboardSerializer` | Wraps counts + rooms_by_status + tasks | — |

---

## 10. Room Services Serializers (`room_services/serializers.py`)

| Serializer | Model | Notable |
|-----------|-------|---------|
| `RoomServiceItemSerializer` | RoomServiceItem | Menu item with image |
| `OrderItemSerializer` | OrderItem | Quantity, notes |
| `OrderSerializer` | Order | Nested items, total_price computed |
| `BreakfastItemSerializer` | BreakfastItem | Menu item |
| `BreakfastOrderSerializer` | BreakfastOrder | With delivery_time |

---

## 11. Stock Tracker Serializers (multiple files)

| File | Key Serializers |
|------|----------------|
| `stock_serializers.py` | `StockCategorySerializer`, `StockItemSerializer`, `StockPeriodSerializer`, `StocktakeSerializer`, `StocktakeLineSerializer`, `StockMovementSerializer`, `StockSnapshotSerializer`, `SaleSerializer` |
| `cocktail_serializers.py` | `CocktailSerializer`, `CocktailIngredientSerializer`, `CocktailConsumptionSerializer` |
| `comparison_serializers.py` | `ComparisonCategorySerializer`, `TopMoverSerializer`, `CostAnalysisSerializer`, `TrendAnalysisSerializer` |

---

## 12. Key Validation Patterns

### Cross-Hotel FK Validation
Multiple serializers validate that related objects belong to the same hotel:
- `HousekeepingTaskSerializer.validate()` — room, booking, assigned_to, created_by
- `DinnerBookingCreateSerializer` — restaurant.hotel matches booking.hotel
- `RoomStatusChangeSerializer` — trigger source matches staff's hotel

### Idempotency Validation
- Payment views use `Idempotency-Key` header with DB cache (`hotel/utils.py`)
- Stripe webhooks use `StripeWebhookEvent.event_id` uniqueness
- Overstay flagging uses `get_or_create` on (booking, status=OPEN)
- Room assignment supports idempotent re-assignment (same room = no-op)

### File Upload Validation
- Cloudinary uploads: 10MB max per image, JPEG/PNG/WebP only (`common/cloudinary_utils.py`)
- Bulk gallery upload: 1-20 images (`hotel/staff_serializers.py`)
- Chat attachments: 50MB max (`chat/models.py`)
- Staff chat attachments: 50MB max (`staff_chat/models.py`)

### Business Rule Validation in Serializers
- `DinnerBookingCreateSerializer`: capacity check, max bookings/hour, group size limit, duplicate room/date
- `StaffRosterSerializer`: unique_together (roster_period, staff, shift_date) enforced at DB level
- `BookingPartyMemberSerializer`: one PRIMARY per booking (DB constraint)
- `RoomStatusChangeSerializer`: full state machine transition validation
