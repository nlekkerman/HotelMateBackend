# HotelMate Backend API

Django REST Framework backend for comprehensive hotel management system.

## 🏨 Core Modules

### Staff Management
- User authentication & JWT tokens
- Registration with QR codes & codes
- Role-based permissions (Manager, Reception, Kitchen, Maintenance, Porter, etc.)
- Department management
- FCM push notifications
- Password reset functionality
- Staff profile management
- Pending registration approvals

### Attendance & Roster
- Clock in/out logging
- Roster period management (weekly/monthly)
- Staff shift scheduling
- Shift location tracking
- Daily planning & entries
- Roster analytics & reporting
- PDF export for rosters
- Department roster creation
- Copy roster functionality
- Bulk shift saving

### Room Management
- Room CRUD operations
- Room status tracking
- Guest assignments
- Checkout management
- Room search by hotel & number
- Checkout notifications

### Guest Management
- Guest profiles
- Guest room history
- Contact information
- Check-in/out dates

### Bookings & Restaurants
- Restaurant management
- Dining table management
- Booking categories & subcategories
- Table assignments
- Real-time seat availability
- Restaurant blueprints (floor plans)
- Blueprint objects (furniture, entrances, windows)
- Guest dinner bookings
- Booking notifications (Pusher)
- Mark bookings as seen
- Unseat guests from tables

### Room Service
- Room service menu items
- Breakfast menu items
- Order management
- Order status tracking
- Kitchen notifications
- Porter notifications
- Order history by room

### Stock Tracker (Comprehensive Inventory System)
- **Stock Items**: Full CRUD with categories (Drinks, Beer, Spirits, Wine, Minerals)
- **Locations**: Bar, Cellar, Storage tracking
- **Stock Periods**: Weekly, Monthly, Quarterly, Yearly
- **Stock Snapshots**: Historical stock levels
- **Stock Movements**: Purchases, Waste, Adjustments with audit trail
- **Stocktakes**: 
  - Create, populate, approve, reopen
  - Line-by-line counting
  - Category totals
  - PDF & Excel export
  - Combined PDF reports
- **Sales Tracking**: Record & analyze sales
- **Cocktail Management**:
  - Recipe creation with ingredients
  - Cocktail consumption tracking
  - Ingredient deduction from stock
  - Merge cocktail consumption into stocktakes
- **Analytics**:
  - Ingredient usage reports
  - Stock value reports
  - Sales reports with filters
  - KPI summaries
- **Comparison Tools**:
  - Category comparisons
  - Top movers (gainers/losers)
  - Cost analysis
  - Trend analysis
  - Variance heatmaps
  - Performance scorecards
- **Voice Commands**: Voice-based stock updates

### Chat System
- Hotel-specific chat channels
- Room-specific guest chat
- Message CRUD
- Attachment support (images, files)
- Message reactions/likes
- Real-time messaging (Pusher)
- Message deletion broadcasts
- Unread message tracking
- Attachment deletion

### Staff Chat
- Department-based channels
- Staff-to-staff messaging
- Message tracking & deletion
- Pusher events for real-time updates

### Entertainment (Quiz System - Guessticulator)
- **Quiz Categories**: History, Science, Music, Sports, Geography, etc.
- **Questions**: Multiple choice with difficulty levels
- **Random Category Selection** (slot machine feature)
- **Tournament System**:
  - Tournament creation & management
  - Player registration
  - Bracket generation
  - Match tracking
  - Tournament progression
  - Finals & winners
- **Leaderboards**: Top scorers tracking
- **Player Stats**: Performance analytics

### Maintenance
- Maintenance request creation
- Request status tracking (Pending, In Progress, Completed)
- Priority levels
- Photo attachments
- Comments on requests
- Staff assignment
- Request filtering by hotel

### Hotel Information
- Hotel profiles
- Info categories (Activities, Dining, Services, etc.)
- QR code generation for categories
- Good-to-know entries
- Hotel-specific information management
- Download all QR codes

### Posts & Social Feed
- Create/edit/delete posts
- Image attachments
- Comments & nested replies
- Like system
- Hotel-specific feeds
- Post visibility controls

### Notifications
- Push notifications (FCM)
- Kitchen staff alerts
- Porter notifications
- Room service alerts
- Booking notifications
- Maintenance alerts

### Common/Theme
- Hotel theme preferences (colors, branding)
- Get/create/update theme settings
- Auto-creation for new hotels

## 🔧 Technical Features

- **Multi-tenancy**: Hotel-based data isolation via slug/subdomain
- **Real-time**: Pusher integration for live updates
- **Authentication**: JWT token-based auth
- **Permissions**: Role-based access control
- **File Uploads**: Image & document handling
- **PDF Generation**: Reports & rosters
- **Excel Export**: Stocktake data
- **QR Codes**: Registration & information access
- **Voice Recognition**: Voice commands for stock
- **Analytics**: Comprehensive reporting across modules
- **Audit Trail**: Stock movement tracking
- **Filtering**: Advanced query filtering (django-filter)

## 📡 API Structure

All endpoints prefixed with `/api/`

### Key Endpoints
- `/api/staff/` - Staff management
- `/api/attendance/` - Clock logs & rosters
- `/api/rooms/` - Room operations
- `/api/bookings/` - Restaurant bookings
- `/api/stock-tracker/` - Inventory management
- `/api/chat/` - Guest messaging
- `/api/staff-chat/` - Staff messaging
- `/api/entertainment/` - Quiz & tournaments
- `/api/maintenance/` - Maintenance requests
- `/api/hotel-info/` - Hotel information
- `/api/room-service/` - Orders & menus
- `/api/home/` - Posts & social feed
- `/api/hotels/` - Hotel theme settings

## 🗃️ Database Models

### Main Models
- Hotel, Staff, User
- Room, Guest, Booking
- StockItem, Stocktake, Sale
- Post, Comment, Message
- MaintenanceRequest
- QuizCategory, Question, Tournament
- RosterPeriod, ClockLog
- Order, RoomServiceItem

## 🚀 Deployment

- **Platform**: Configured for Heroku (Procfile)
- **Database**: PostgreSQL
- **Storage**: Static files & media
- **Cache**: Redis support
- **Real-time**: Pusher channels

## 📦 Key Dependencies

- Django REST Framework
- Pusher (real-time)
- Pillow (images)
- ReportLab (PDFs)
- OpenPyXL (Excel)
- QR Code generation
- Firebase Admin (FCM)
- django-filter

## 🔐 Security

- Token authentication
- Permission classes per endpoint
- Hotel data isolation
- Role-based feature access
- Secure file uploads

## 📊 Reporting

- Stock value reports
- Sales analytics
- Staff roster PDFs
- Stocktake exports (PDF/Excel)
- Performance scorecards
- Tournament brackets

---

**Version**: Production-ready hotel management system
**Architecture**: Django + DRF + PostgreSQL + Pusher
**Frontend**: Separate React/mobile applications
