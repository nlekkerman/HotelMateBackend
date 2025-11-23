# Hotel Killarney – Public Hotel API Example (Backend)

This file defines an example payload for:

`GET /api/hotels/hotel-killarney/public/`

Use it as:
- reference for serializer/response shape
- seed/example data for tests or fixtures

```json
{
  "slug": "hotel-killarney",
  "name": "Hotel Killarney",
  "tagline": "Your perfect family escape on Cork Road.",
  "hero_image_url": "https://example.com/images/hotel-killarney/hero.jpg",
  "logo_url": "https://example.com/images/hotel-killarney/logo.png",
  "short_description": "Hotel Killarney is a welcoming family hotel on Cork Road, just minutes from Killarney town centre, with spacious rooms, a leisure centre and plenty of activities for all ages.",
  "long_description": "<p>Experience comfort, space and friendly hospitality at <strong>Hotel Killarney</strong>, perfectly located on <strong>Cork Road</strong>, a short drive from Killarney National Park, the Lakes of Killarney and the town’s vibrant shopping and dining scene.</p><p>Designed with both <strong>families</strong> and <strong>leisure travellers</strong> in mind, the hotel features a modern leisure centre, large family rooms, on-site dining options and entertainment facilities. Whether you’re visiting for nature, relaxation or adventure, Hotel Killarney is the perfect starting point.</p>",

  "location": {
    "city": "Killarney",
    "country": "Ireland",
    "address_line_1": "Cork Road",
    "address_line_2": "",
    "postal_code": "V93",
    "latitude": 52.058,
    "longitude": -9.507
  },

  "contact": {
    "phone": "+353 64 662 6200",
    "email": "info@hotelkillarney.ie",
    "website_url": "https://www.hotelkillarney.ie",
    "booking_url": "https://bookings.hotelkillarney.ie"
  },

  "booking_options": {
    "primary_cta_label": "Book a Room",
    "primary_cta_url": "https://bookings.hotelkillarney.ie",
    "secondary_cta_label": "Call to Book",
    "secondary_cta_phone": "+353 64 662 6200",
    "terms_url": "https://www.hotelkillarney.ie/terms",
    "policies_url": "https://www.hotelkillarney.ie/policies"
  },

  "room_types": [
    {
      "code": "FAMILY_ROOM",
      "name": "Family Room",
      "short_description": "Spacious family room for 2 adults and 2 children, ideal for exploring Killarney and the Ring of Kerry.",
      "max_occupancy": 4,
      "bed_setup": "1 double bed + 2 single beds",
      "photo_url": "https://example.com/images/hotel-killarney/rooms/family-room.jpg",
      "starting_price_from": 140.0,
      "currency": "EUR",
      "booking_code": "FAM_STD",
      "booking_url": "https://bookings.hotelkillarney.ie/rooms/family",
      "availability_message": "Popular with families – limited availability during weekends."
    },
    {
      "code": "DOUBLE_TWIN",
      "name": "Double / Twin Room",
      "short_description": "Bright and comfortable room with a double bed or two singles, perfect for couples or friends.",
      "max_occupancy": 2,
      "bed_setup": "1 double bed or 2 single beds",
      "photo_url": "https://example.com/images/hotel-killarney/rooms/double-twin.jpg",
      "starting_price_from": 110.0,
      "currency": "EUR",
      "booking_code": "DBL_TWN",
      "booking_url": "https://bookings.hotelkillarney.ie/rooms/double-twin",
      "availability_message": "Great value option on Cork Road."
    },
    {
      "code": "SUPERIOR",
      "name": "Superior Room",
      "short_description": "Larger, upgraded room with extra comfort for longer stays or relaxing weekends.",
      "max_occupancy": 2,
      "bed_setup": "King bed or 1 double bed",
      "photo_url": "https://example.com/images/hotel-killarney/rooms/superior.jpg",
      "starting_price_from": 160.0,
      "currency": "EUR",
      "booking_code": "SUP_ROOM",
      "booking_url": "https://bookings.hotelkillarney.ie/rooms/superior",
      "availability_message": "Limited number of superior rooms available."
    }
  ],

  "offers": [
    {
      "title": "3 Nights for the Price of 2",
      "short_description": "Stay three nights and pay for only two, including complimentary leisure centre access and Wi-Fi.",
      "details_html": "<p>Enjoy an extended break in Killarney with our 3-for-2 offer. Includes access to the leisure centre and free Wi-Fi throughout your stay. Subject to availability and specific date restrictions.</p>",
      "valid_from": "2025-01-01",
      "valid_to": "2025-03-31",
      "tag": "Special Offer",
      "book_now_url": "https://bookings.hotelkillarney.ie/offers/3-for-2"
    },
    {
      "title": "Family Fun Package",
      "short_description": "Two nights’ accommodation, breakfast each morning and a kids’ activity pass for the leisure facilities.",
      "details_html": "<p>Our Family Fun Package includes two nights’ accommodation, breakfast for the whole family and a kids’ activity pass. Perfect for school holidays and weekend breaks.</p>",
      "valid_from": "2025-04-01",
      "valid_to": "2025-10-31",
      "tag": "Family Deal",
      "book_now_url": "https://bookings.hotelkillarney.ie/offers/family-fun"
    }
  ],

  "leisure_activities": [
    {
      "name": "Leisure Centre",
      "category": "Wellness",
      "short_description": "Indoor heated pool, sauna and steam room for guests to relax and unwind.",
      "icon": "pool",
      "image_url": "https://example.com/images/hotel-killarney/leisure/pool.jpg",
      "details_html": "<p>Enjoy our indoor heated pool, sauna and steam room, open daily for hotel guests. Towels are provided at the leisure centre.</p>"
    },
    {
      "name": "Kids Club",
      "category": "Family",
      "short_description": "Supervised activities for children during weekends and school holidays.",
      "icon": "kids",
      "image_url": "https://example.com/images/hotel-killarney/leisure/kids-club.jpg",
      "details_html": "<p>Our Kids Club offers fun, supervised activities to keep younger guests entertained, giving parents some well-deserved downtime.</p>"
    },
    {
      "name": "Fitness Room",
      "category": "Wellness",
      "short_description": "Compact fitness room with cardio and strength equipment for your daily workout.",
      "icon": "fitness",
      "image_url": "https://example.com/images/hotel-killarney/leisure/fitness-room.jpg",
      "details_html": "<p>Stay on track with your fitness routine using our gym facilities, available to all hotel guests.</p>"
    },
    {
      "name": "Nearby Nature & Attractions",
      "category": "Local Area",
      "short_description": "Minutes from Killarney National Park, Muckross House, Ross Castle and the Lakes of Killarney.",
      "icon": "nature",
      "image_url": "https://example.com/images/hotel-killarney/leisure/nature.jpg",
      "details_html": "<p>Hotel Killarney on Cork Road is a great base for exploring the Ring of Kerry, Killarney National Park and the Lakes of Killarney.</p>"
    }
  ],

  "meta": {
    "seo_title": "Hotel Killarney on Cork Road – Family Hotel in Killarney, Co. Kerry",
    "seo_description": "Book your stay at Hotel Killarney on Cork Road. Family-friendly hotel with spacious rooms, leisure centre, kids club and easy access to Killarney town and National Park."
  }
}
```