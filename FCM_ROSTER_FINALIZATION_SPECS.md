# FCM Notifications for Finalized Rosters

## Overview
FCM (Firebase Cloud Messaging) push notifications for roster finalization events. These notifications are sent when roster periods are finalized, unfinalized, or when staff need to be alerted about finalized status changes.

## FCM Token Storage
- **Staff FCM Token**: `staff.fcm_token` field (CharField, max_length=255)
- **Token Management**: Stored via `/api/staff/save-fcm-token/` endpoint
- **Validation**: Token checked before sending notifications

## Notification Types

### 1. Roster Period Finalized
**Triggered by**: Manager finalizes a roster period

#### 1.1 Manager Notification (Self-Confirmation)
- **Title**: `✅ Roster Finalized`
- **Body**: `You have finalized roster '{period_title}' for {hotel_name}`
- **Recipients**: Manager who performed finalization
- **Data**:
  ```json
  {
    "type": "roster_period_finalized",
    "period_id": "123",
    "period_title": "Week of Dec 2-8",
    "finalized_by_id": "456",
    "finalized_by_name": "Manager Smith",
    "finalized_at": "2025-12-04T15:30:00Z",
    "hotel_slug": "hotel-killarney",
    "click_action": "FLUTTER_NOTIFICATION_CLICK",
    "route": "/attendance/roster-periods/123"
  }
  ```

#### 1.2 Staff Notification (Affected Staff)
- **Title**: `🔒 Roster Locked`
- **Body**: `Your roster for '{period_title}' has been finalized and locked`
- **Recipients**: All staff with shifts in the finalized period
- **Data**:
  ```json
  {
    "type": "roster_period_staff_locked",
    "period_id": "123",
    "period_title": "Week of Dec 2-8",
    "finalized_by_name": "Manager Smith",
    "finalized_at": "2025-12-04T15:30:00Z",
    "staff_shift_count": "5",
    "hotel_slug": "hotel-killarney",
    "click_action": "FLUTTER_NOTIFICATION_CLICK",
    "route": "/attendance/my-shifts"
  }
  ```

#### 1.3 Admin/Manager Alert
- **Title**: `📋 Period Finalized`
- **Body**: `{finalized_by_name} finalized roster '{period_title}'`
- **Recipients**: Hotel admins and senior managers
- **Data**:
  ```json
  {
    "type": "roster_period_admin_alert",
    "period_id": "123",
    "period_title": "Week of Dec 2-8",
    "finalized_by_id": "456",
    "finalized_by_name": "Manager Smith",
    "finalized_at": "2025-12-04T15:30:00Z",
    "total_shifts": "85",
    "total_staff": "23",
    "hotel_slug": "hotel-killarney",
    "click_action": "FLUTTER_NOTIFICATION_CLICK",
    "route": "/attendance/roster-periods"
  }
  ```

### 2. Roster Period Unfinalized
**Triggered by**: Admin unfinalizes a roster period

#### 2.1 Admin Notification (Self-Confirmation)
- **Title**: `🔓 Roster Unlocked`
- **Body**: `You have unfinalized roster '{period_title}' - editing is now allowed`
- **Recipients**: Admin who performed unfinalization
- **Data**:
  ```json
  {
    "type": "roster_period_unfinalized",
    "period_id": "123",
    "period_title": "Week of Dec 2-8",
    "unfinalized_by_id": "789",
    "unfinalized_by_name": "Admin Johnson",
    "unfinalized_at": "2025-12-04T16:45:00Z",
    "hotel_slug": "hotel-killarney",
    "click_action": "FLUTTER_NOTIFICATION_CLICK",
    "route": "/attendance/roster-periods/123"
  }
  ```

#### 2.2 Manager Alert (Editing Resumed)
- **Title**: `⚠️ Roster Reopened`
- **Body**: `Roster '{period_title}' has been unlocked for editing by admin`
- **Recipients**: All managers with roster editing permissions
- **Data**:
  ```json
  {
    "type": "roster_period_reopened",
    "period_id": "123",
    "period_title": "Week of Dec 2-8",
    "unfinalized_by_name": "Admin Johnson",
    "unfinalized_at": "2025-12-04T16:45:00Z",
    "hotel_slug": "hotel-killarney",
    "click_action": "FLUTTER_NOTIFICATION_CLICK",
    "route": "/attendance/roster-periods/123"
  }
  ```

### 3. Finalization Validation Errors
**Triggered by**: Attempted finalization fails validation

#### 3.1 Manager Error Notification
- **Title**: `❌ Roster Finalization Failed`
- **Body**: `Cannot finalize '{period_title}' - {error_count} unresolved issues`
- **Recipients**: Manager who attempted finalization
- **Data**:
  ```json
  {
    "type": "roster_finalization_failed",
    "period_id": "123",
    "period_title": "Week of Dec 2-8",
    "error_count": "3",
    "error_summary": "Unresolved unrostered clock-ins",
    "validation_errors": [
      "John Doe has unresolved clock-in",
      "Jane Smith has unresolved clock-in"
    ],
    "hotel_slug": "hotel-killarney",
    "click_action": "FLUTTER_NOTIFICATION_CLICK",
    "route": "/attendance/roster-periods/123/issues"
  }
  ```

## Implementation Structure

### FCM Service Function
```python
# Add to notifications/fcm_service.py

def send_roster_finalization_notification(staff, period, notification_type, **kwargs):
    """
    Send roster finalization FCM notification
    
    Args:
        staff: Staff instance (recipient)
        period: RosterPeriod instance
        notification_type: str ('finalized', 'unfinalized', 'failed', 'staff_locked')
        **kwargs: Additional data (finalized_by, error_count, etc.)
    
    Returns:
        bool: True if notification sent successfully
    """
```

### Notification Recipients

#### For Finalization:
- **Manager who finalized**: Self-confirmation
- **All staff with shifts**: Period locked notification
- **Hotel admins**: Administrative alert

#### For Unfinalization:
- **Admin who unfinalized**: Self-confirmation  
- **All managers**: Editing resumed alert

#### For Validation Errors:
- **Manager who attempted**: Error details and resolution steps

## Data Structure Standards

### Common Fields:
- `type`: Notification category
- `period_id`: RosterPeriod ID
- `period_title`: Human-readable period name
- `hotel_slug`: Hotel identifier
- `click_action`: Mobile app action
- `route`: Navigation route

### Action-Specific Fields:
- `finalized_by_id/name`: Who performed finalization
- `finalized_at`: When finalized (ISO format)
- `staff_shift_count`: Number of shifts for staff member
- `total_shifts/staff`: Period statistics
- `error_count/summary`: Validation failure details

## Mobile App Integration

### Click Actions:
- **FLUTTER_NOTIFICATION_CLICK**: Standard mobile app handler
- **Route Navigation**: Deep links to specific screens
- **Fallback URLs**: Web app equivalent for cross-platform

### Notification Channels:
- **Roster Management**: High priority for managers
- **Staff Updates**: Standard priority for staff notifications
- **Admin Alerts**: High priority for administrative notifications

## Testing Considerations

### Mock Data:
```python
# Test FCM notification data
test_period = {
    "id": 123,
    "title": "Week of Dec 2-8",
    "hotel_slug": "hotel-killarney"
}

test_staff = {
    "id": 456,
    "fcm_token": "test_token_123",
    "name": "John Doe"
}
```

### Validation:
- FCM token exists and is valid
- Staff has appropriate permissions
- Period data is complete
- Error handling for failed deliveries
- Token cleanup for invalid/expired tokens