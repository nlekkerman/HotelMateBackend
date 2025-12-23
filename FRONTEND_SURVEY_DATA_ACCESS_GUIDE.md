# Frontend Survey Data Access Guide

## 📊 Survey Data in Booking Endpoints

After guests submit surveys, the data is accessible through existing booking endpoints with optional enhanced details.

## 🔹 Basic Survey Info (Always Included)

All booking list and detail endpoints automatically include these survey flags:

```json
{
  "survey_sent": true,
  "survey_completed": true, 
  "survey_rating": 5,
  "survey_sent_at": "2025-12-23T12:41:16.178130Z",
  "survey_response": null
}
```

## 🔹 Enhanced Survey Data (Optional)

To get detailed survey responses, add query parameter: `?include_survey_response=true`

### List View (Performance Optimized)
**Endpoint:** `GET /api/staff/hotel/{hotel_slug}/room-bookings/?include_survey_response=true`

```json
{
  "survey_response": {
    "submitted_at": "2025-12-23T12:41:20.123456Z",
    "overall_rating": 5
    // Note: Full payload not included in list view for performance
  }
}
```

### Detail View (Complete Data)
**Endpoint:** `GET /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/?include_survey_response=true`

```json
{
  "survey_response": {
    "submitted_at": "2025-12-23T12:41:20.123456Z", 
    "overall_rating": 5,
    "payload": {
      "overall_rating": 5,
      "room_rating": 4,
      "staff_rating": 5,
      "comment": "Amazing stay! Room was perfect.",
      "contact_permission": true,
      "recommend_hotel": true,
      "cleanliness_rating": 5,
      "value_rating": 4
    }
  }
}
```

## 🚀 Frontend Implementation Examples

### Basic Survey Status Check
```javascript
// Standard booking fetch - includes basic survey flags
const response = await fetch(`/api/staff/hotel/${hotelSlug}/room-bookings/${bookingId}/`);
const booking = await response.json();

// Check survey status
if (booking.survey_sent) {
  console.log('Survey was sent on:', booking.survey_sent_at);
}

if (booking.survey_completed) {
  console.log('Guest rated:', booking.survey_rating + '/5');
}
```

### Detailed Survey Data
```javascript
// Fetch booking with full survey response
const response = await fetch(
  `/api/staff/hotel/${hotelSlug}/room-bookings/${bookingId}/?include_survey_response=true`
);
const booking = await response.json();

// Access detailed survey data
if (booking.survey_response) {
  const survey = booking.survey_response;
  console.log('Submitted:', survey.submitted_at);
  console.log('Overall Rating:', survey.overall_rating);
  console.log('Comment:', survey.payload.comment);
  console.log('Room Rating:', survey.payload.room_rating);
  // ... access all survey fields from payload
}
```

### Survey Dashboard/List View
```javascript
// Get bookings with survey summaries (lightweight)
const response = await fetch(
  `/api/staff/hotel/${hotelSlug}/room-bookings/?include_survey_response=true&status=COMPLETED`
);
const bookings = await response.json();

// Filter completed surveys
const completedSurveys = bookings.results.filter(booking => 
  booking.survey_completed && booking.survey_response
);

completedSurveys.forEach(booking => {
  console.log(`${booking.booking_id}: ${booking.survey_response.overall_rating}/5`);
});
```

## 📋 Available Survey Fields

The survey payload may contain (depending on hotel configuration):

- `overall_rating` - Overall experience rating (1-5)
- `room_rating` - Room quality rating (1-5) 
- `staff_rating` - Staff service rating (1-5)
- `cleanliness_rating` - Cleanliness rating (1-5)
- `value_rating` - Value for money rating (1-5)
- `location_rating` - Location rating (1-5)
- `comment` - Free text feedback
- `contact_permission` - Guest consent for follow-up contact
- `recommend_hotel` - Would recommend to others (boolean)

## ⚡ Performance Notes

- **Default behavior**: Only basic survey flags are included (fast)
- **With `?include_survey_response=true`**:
  - **List view**: Survey summary only (no full payload)
  - **Detail view**: Complete survey data including full payload
- Use the query parameter only when you need detailed survey data to avoid unnecessary overhead

## 🔗 Related Endpoints

- **Survey Configuration**: `GET /api/staff/hotel/{hotel_slug}/survey-config/`
- **Send Survey Link**: `POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/send-survey-link/`
- **Guest Survey Submission**: `GET /api/public/hotel/{hotel_slug}/survey/?token={token}` (public)