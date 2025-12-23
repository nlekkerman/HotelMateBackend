# Frontend Survey Data Access Guide

## 📊 Survey Data in Booking Endpoints

After guests submit surveys, the data is **automatically included** in all booking endpoints when survey responses exist.

## 🔹 Survey Data (Always Included When Available)

All booking list and detail endpoints automatically include survey data when it exists:

```json
{
  "survey_sent": true,
  "survey_completed": true, 
  "survey_rating": 5,
  "survey_sent_at": "2025-12-23T12:41:16.178130Z",
  "survey_response": {
    "submitted_at": "2025-12-23T12:41:20.123456Z",
    "overall_rating": 5,
    "payload": {
      "overall_rating": 5,
      "room_rating": 4,
      "staff_rating": 5,
      "cleanliness_rating": 5,
      "bed_comfort_rating": 5,
      "value_rating": 4,
      "comment": "Amazing stay! Room was perfect.",
      "contact_permission": true,
      "recommend_hotel": true
    }
  }
}
```

**If no survey was submitted:**
```json
{
  "survey_sent": false,
  "survey_completed": false,
  "survey_rating": null,
  "survey_sent_at": null,
  "survey_response": null
}
```

## 🚀 Frontend Implementation Examples

### Basic Survey Status Check
```javascript
// Standard booking fetch - survey data automatically included
const response = await fetch(`/api/staff/hotel/${hotelSlug}/room-bookings/${bookingId}/`);
const booking = await response.json();

// Check survey status
if (booking.survey_sent) {
  console.log('Survey was sent on:', booking.survey_sent_at);
}

if (booking.survey_completed && booking.survey_response) {
  console.log('Guest rated:', booking.survey_response.overall_rating + '/5');
  console.log('Comment:', booking.survey_response.payload.comment);
}
```

### Complete Survey Data Access
```javascript
const response = await fetch(`/api/staff/hotel/${hotelSlug}/room-bookings/${bookingId}/`);
const booking = await response.json();

// Access all survey data
if (booking.survey_response) {
  const survey = booking.survey_response;
  const payload = survey.payload;
  
  console.log('Survey submitted:', survey.submitted_at);
  console.log('Overall Rating:', payload.overall_rating + '/5');
  console.log('Room Rating:', payload.room_rating + '/5');
  console.log('Staff Rating:', payload.staff_rating + '/5');
  console.log('Comment:', payload.comment);
  console.log('Would recommend:', payload.recommend_hotel);
  console.log('Contact permission:', payload.contact_permission);
}
```

### Survey Dashboard/List View
```javascript
// Get all bookings - survey data included automatically
const response = await fetch(`/api/staff/hotel/${hotelSlug}/room-bookings/?status=COMPLETED`);
const bookings = await response.json();

// Filter and display completed surveys
const completedSurveys = bookings.results.filter(booking => 
  booking.survey_completed && booking.survey_response
);

completedSurveys.forEach(booking => {
  const survey = booking.survey_response;
  console.log(`${booking.booking_id}: ${survey.overall_rating}/5 - "${survey.payload.comment}"`);
});
```

### Survey Statistics
```javascript
// Calculate average ratings from bookings list
const response = await fetch(`/api/staff/hotel/${hotelSlug}/room-bookings/?status=COMPLETED`);
const bookings = await response.json();

const surveys = bookings.results
  .filter(b => b.survey_response)
  .map(b => b.survey_response.payload);

const avgOverall = surveys.reduce((sum, s) => sum + s.overall_rating, 0) / surveys.length;
const avgRoom = surveys.reduce((sum, s) => sum + s.room_rating, 0) / surveys.length;

console.log(`Average overall rating: ${avgOverall.toFixed(1)}/5`);
console.log(`Average room rating: ${avgRoom.toFixed(1)}/5`);
```

## 📋 Available Survey Fields

The survey payload may contain (depending on hotel configuration):

- `overall_rating` - Overall experience rating (1-5)
- `room_rating` - Room quality rating (1-5) 
- `staff_rating` - Staff service rating (1-5)
- `cleanliness_rating` - Cleanliness rating (1-5)
- `bed_comfort_rating` - Bed comfort rating (1-5)
- `value_rating` - Value for money rating (1-5)
- `location_rating` - Location rating (1-5)
- `comment` - Free text feedback
- `contact_permission` - Guest consent for follow-up contact
- `recommend_hotel` - Would recommend to others (boolean)

## ⚡ Performance Notes

- **Survey data is automatically included** when it exists - no query parameters needed
- **List view**: Survey summary (submitted_at, overall_rating) - no full payload for performance
- **Detail view**: Complete survey data including full payload with all fields
- **Zero additional requests** needed - everything comes with the booking data

## 🔗 Related Endpoints

- **Survey Configuration**: `GET /api/staff/hotel/{hotel_slug}/survey-config/`
- **Send Survey Link**: `POST /api/staff/hotel/{hotel_slug}/room-bookings/{booking_id}/send-survey-link/`
- **Guest Survey Submission**: `GET /api/public/hotel/{hotel_slug}/survey/?token={token}` (public)