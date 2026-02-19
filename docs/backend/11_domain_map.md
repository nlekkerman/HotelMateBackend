# 11. Domain Map and Application Structure

## Django Application Domains

The HotelMate backend is organized into domain-driven Django applications, each responsible for specific business areas.

### Core Business Domain Applications

#### 1. Hotel Management (`hotel/`)
**Domain:** Central hotel configuration and booking lifecycle management
**Responsibility:**
- Hotel entity management and multi-tenant configuration
- Room booking lifecycle (creation, payment, approval, completion)
- Payment processing integration with Stripe
- Cancellation policy engine
- Guest access token management
- Overstay detection and management
- Public page builder for hotel marketing sites

**Key Models:**
- `Hotel` - Multi-tenant hotel entities with configuration
- `RoomBooking` - Guest room reservations with state machine
- `GuestBookingToken` - Scoped access tokens for guests
- `CancellationPolicy` - Flexible cancellation rule engine
- `HotelAccessConfig` - Per-hotel operational settings
- `HotelPrecheckinConfig` - Configurable precheckin forms
- `HotelSurveyConfig` - Guest survey automation settings

**Evidence:** `hotel/models.py` extensive model definitions and `INSTALLED_APPS`

#### 2. Room & Inventory Management (`rooms/`)
**Domain:** Physical room inventory and status management
**Responsibility:**
- Room and room type definitions
- Room status state machine for housekeeping workflow
- Availability calculations for booking system
- Physical room to room type mapping for PMS integration

**Key Models:**
- `Room` - Physical room entities with status tracking
- `RoomType` - Bookable room categories with pricing

**State Machine:** 7-state turnover workflow from OCCUPIED to READY_FOR_GUEST
**Evidence:** `rooms/models.py` lines 36-115 for state machine implementation

#### 3. Guest Management (`guests/`)
**Domain:** Guest profiles and relationship management
**Responsibility:**
- Guest registration and profile management
- Guest service history and preferences
- Guest communication management

UNCLEAR IN CODE: Specific guest models need analysis of `guests/models.py`

#### 4. Staff Operations (`staff/`)
**Domain:** Staff authentication, roles, and operational tools
**Responsibility:**
- Staff authentication and profile management
- Role-based access control system
- Department organization structure
- Navigation and UI configuration
- Staff registration code system

**Key Models:**
- `Staff` - Staff member profiles with hotel association
- `Department` - Organizational structure
- `Role` - Permission-based role system
- `NavigationItem` - Configurable staff portal navigation
- `RegistrationCode` - Staff onboarding system
- `UserProfile` - Extended user profile data

**Evidence:** `staff/models.py` comprehensive staff management system

#### 5. Housekeeping Management (`housekeeping/`)
**Domain:** Room cleaning and maintenance workflow
**Responsibility:**
- Room turnover task management
- Housekeeping staff assignment and tracking
- Room status event logging
- Maintenance requirement flagging

**Key Models:**
- `HousekeepingTask` - Work assignments with priorities
- `RoomStatusEvent` - Status change audit trail

**Integration:** Connects with `rooms/` app for status updates
**Evidence:** `housekeeping/services.py` line 259 task creation function

### Service Domain Applications

#### 6. Room Services (`room_services/`)
**Domain:** In-room service ordering and fulfillment
**Responsibility:**
- Room service menu management
- Order processing and tracking
- Breakfast service management
- Guest ordering interface

**Key Models:**
- `RoomServiceItem` - Menu items with hotel-specific pricing
- `Order` / `OrderItem` - Order processing system
- `BreakfastItem` / `BreakfastOrder` - Breakfast-specific services

**API Integration:** Real-time order notifications via Pusher
**Evidence:** `room_services/models.py` comprehensive service system

#### 7. Inventory & Stock Management (`stock_tracker/`)
**Domain:** Bar inventory, cocktail recipes, and stock control
**Responsibility:**
- Ingredient and recipe management
- Cocktail consumption tracking
- Stock movement logging
- Period-based inventory control
- Stocktake management
- Voice recognition integration for inventory updates

**Key Models:**
- `Ingredient` - Base inventory items
- `CocktailRecipe` - Recipe definitions with ingredient mapping
- `CocktailConsumption` - Sale tracking with automatic ingredient deduction
- `StockItem` - Inventory items with location tracking
- `StockPeriod` - Time-based inventory accounting
- `StockMovement` - All stock transactions and adjustments
- `Stocktake` - Physical inventory counting

**Complex Features:** Recipe-based automatic ingredient consumption calculation
**Evidence:** `stock_tracker/models.py` extensive inventory system (2000+ lines)

#### 8. Maintenance Management (`maintenance/`)
**Domain:** Property maintenance and repair tracking
**Responsibility:**
- Maintenance request management
- Work order tracking
- Asset management

UNCLEAR IN CODE: Specific maintenance models need analysis

### Communication Domain Applications

#### 9. Guest-Staff Chat (`chat/`)
**Domain:** Real-time messaging between guests and staff
**Responsibility:**
- Guest-initiated support conversations
- Real-time message delivery via Pusher
- File attachment support
- Message history and context management

UNCLEAR IN CODE: Specific chat models need analysis of `chat/models.py`

#### 10. Staff Communications (`staff_chat/`)
**Domain:** Internal staff messaging and collaboration
**Responsibility:**
- Staff-to-staff conversations
- Group messaging by department/role
- Message reactions and threading
- File sharing within staff teams

**Key Models:**
- `StaffConversation` - Conversation management
- `StaffChatMessage` - Individual messages with rich content
- `StaffChatAttachment` - File attachment handling
- `StaffMessageReaction` - Message reactions system

**Evidence:** `staff_chat/models.py` comprehensive internal messaging

#### 11. Notification System (`notifications/`)
**Domain:** Push notifications and real-time events
**Responsibility:**
- Pusher integration and authentication
- Push notification delivery
- Real-time event broadcasting
- Notification preference management

**Integration Point:** Global Pusher auth endpoint for all apps
**Evidence:** `HotelMateBackend/urls.py` line 69 notification routing

### Utility Domain Applications

#### 12. Common Utilities (`common/`)
**Domain:** Shared utilities and base functionality
**Responsibility:**
- Shared serializers and base classes
- Common validation logic
- Utility functions
- Custom 404 error handling

**Integration:** Used by all other applications for shared functionality
**Evidence:** Custom 404 handler reference in `HotelMateBackend/urls.py`

#### 13. Hotel Information (`hotel_info/`)
**Domain:** Hotel marketing and informational content
**Responsibility:**
- Hotel description and amenity management
- Location and contact information
- Marketing content management

**Config:** Uses custom app config `hotel_info.apps.HotelInfoConfig`
**Evidence:** `INSTALLED_APPS` configuration

### Extended Domain Applications

#### 14. Entertainment (`entertainment/`)
**Domain:** Guest entertainment and activity management
**Responsibility:** Guest activity booking and entertainment scheduling

#### 15. Voice Recognition (`voice_recognition/`)
**Domain:** Voice-controlled inventory management
**Responsibility:**
- Voice command processing for stock updates
- Brand name synonym matching
- Voice-to-data conversion for inventory operations

**Evidence:** `voice_recognition/brand_synonyms.py` with brand matching logic

#### 16. Attendance Tracking (`attendance/`)
**Domain:** Staff time and attendance management
**Responsibility:**
- Staff clock-in/clock-out tracking
- Attendance reporting
- Auto clock-out for excessive hours

**Automation:** Heroku Scheduler job every 30 minutes
**Evidence:** `setup_heroku_scheduler.sh` auto clock-out configuration

#### 17. Restaurant Bookings (`bookings/`)
**Domain:** Restaurant reservation management (separate from room bookings)
**Responsibility:**
- Restaurant table booking system
- Dining reservation management
- Restaurant-specific availability

**Note:** Distinct from room bookings in `hotel/` app
**Evidence:** Separate URL routing in main urls.py

#### 18. Home Dashboard (`home/`)
**Domain:** Dashboard and landing page functionality
**Responsibility:** Staff and guest dashboard content

## Application Interdependencies

### Core Dependencies
```
hotel/ → rooms/ (room availability for bookings)
rooms/ → housekeeping/ (status updates and tasks)
staff/ → all apps (authentication and permissions)
common/ ← all apps (shared utilities)
notifications/ ← all apps (real-time events)
```

### Business Logic Dependencies
```
hotel/RoomBooking → rooms/Room (availability checking)
housekeeping/HousekeepingTask → rooms/Room (status management)
stock_tracker/CocktailConsumption → stock_tracker/Ingredient (recipe calculations)
room_services/Order → hotel/RoomBooking (guest context)
```

### Communication Dependencies
```
chat/ → hotel/GuestBookingToken (guest authentication)
staff_chat/ → staff/Staff (staff identification)
notifications/ → pusher (real-time delivery)
```

## Directory Structure Analysis

**Evidence:** Directory inspection shows each app follows standard Django structure:
- `models.py` - Data models and business logic
- `views.py` - API endpoints and request handling
- `serializers.py` - Data serialization for API responses
- `urls.py` - URL routing configuration
- `admin.py` - Django admin interface configuration
- `migrations/` - Database schema evolution
- `management/commands/` - Custom Django commands

## Domain Boundaries

### Well-Defined Boundaries
- **Hotel vs Room Bookings:** Clear separation between hotel room reservations and restaurant bookings
- **Guest vs Staff Features:** Distinct authentication and feature sets
- **Real-time vs Batch Processing:** Clear separation between live messaging and scheduled tasks

### Potential Coupling Areas
- **Booking-Room Integration:** Tight coupling between booking creation and room availability
- **Authentication Across Apps:** Staff authentication used throughout multiple apps
- **Notification Integration:** Multiple apps depend on notification system

This domain structure provides clear separation of concerns while maintaining necessary integrations for business functionality.