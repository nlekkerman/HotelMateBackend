# Room Pricing System Implementation

## Overview
Enhanced room pricing system that displays multiple pricing variants per room type based on different rate plans. The system intelligently groups room types and shows all available pricing options when they differ.

## Backend Implementation

### Models Structure
- **RoomType**: Base room information (name, description, starting_price_from)
- **RatePlan**: Pricing plans (Standard, Early Bird, Non-Refundable, etc.)
- **RoomTypeRatePlan**: Links room types to rate plans with specific pricing
- **Promotion**: Discount codes with percentage/fixed amounts

### API Endpoint
```
GET /api/public/hotel/{hotel-slug}/page/
```

### Enhanced Serializer Logic

#### RoomTypeRatePlanVariantSerializer
Returns detailed pricing information for each room type + rate plan combination:

```json
{
  "room_type_name": "Deluxe Double Room",
  "rate_plan_name": "Early Bird 30",
  "rate_plan_code": "EB30",
  "current_price": 96.0,
  "original_price": 129.0,
  "price_display": "€96",
  "discount_percent": 20.0,
  "has_discount": true,
  "is_refundable": true,
  "booking_cta_url": "/public/booking/hotel-killarney?room_type_code=Deluxe Double Room&rate_plan_code=EB30"
}
```

#### Smart Grouping Algorithm
```python
# Group by room type
room_type_groups = {}
for rtrp in room_type_rate_plans:
    room_type_id = rtrp.room_type.id
    if room_type_id not in room_type_groups:
        room_type_groups[room_type_id] = []
    room_type_groups[room_type_id].append(rtrp)

# Show all variants if different prices, single if same
for room_type_id, variants in room_type_groups.items():
    unique_prices = set()
    for variant in variants:
        price = variant.base_price if variant.base_price else variant.room_type.starting_price_from
        unique_prices.add(price)
    
    if len(unique_prices) > 1:
        # Multiple different prices - show all variants
        for variant in variants:
            result.append(RoomTypeRatePlanVariantSerializer(variant).data)
    else:
        # Same price - show only best (most discounted) variant
        best_variant = min(variants, key=lambda x: x.rate_plan.default_discount_percent, reverse=True)
        result.append(RoomTypeRatePlanVariantSerializer(best_variant).data)
```

## Current Data Structure (Hotel Killarney)

### Rate Plans Available
- **Standard Rate (STANDARD)**: 0% discount, refundable
- **Standard Rate (STD)**: 0% discount, refundable  
- **Non-Refundable Rate (NRF)**: 15% discount, non-refundable
- **Early Bird 30 (EB30)**: 20% discount, refundable

### Sample Room Type Variants
```
1. Deluxe Double Room - Standard Rate (STANDARD): €129
2. Deluxe Double Room - Standard Rate (STD): €120
3. Deluxe Double Room - Non-Refundable Rate (NRF): €102 (15% OFF)
4. Deluxe Double Room - Early Bird 30 (EB30): €96 (20% OFF)

5. Standard Room - Standard Rate (STANDARD): €89
6. Standard Room - Standard Rate (STD): €120
7. Standard Room - Non-Refundable Rate (NRF): €102 (15% OFF)
8. Standard Room - Early Bird 30 (EB30): €96 (20% OFF)
```

## Frontend Implementation

### Booking Page URL Structure
```
http://localhost:5173/public/booking/hotel-killarney?room_type_code=STD&rate_plan_code=EB30
```

### Room Card Display Components

#### Basic Room Card
```jsx
<div className="room-card">
  <h3>{room.room_type_name}</h3>
  <p>Up to {room.max_occupancy} guests</p>
  
  {/* Rate Plan Badge */}
  <div className="rate-plan-badge">
    {room.rate_plan_name}
  </div>
  
  {/* Discount Badge */}
  {room.has_discount && (
    <div className="discount-badge">
      {room.discount_percent}% OFF
    </div>
  )}
  
  {/* Pricing Display */}
  <div className="pricing">
    <span className="current-price">{room.price_display}</span>
    {room.has_discount && (
      <span className="original-price">€{room.original_price}</span>
    )}
  </div>
  
  {/* Refund Policy */}
  <div className="policy">
    {room.is_refundable ? '✅ Refundable' : '❌ Non-Refundable'}
  </div>
  
  <button onClick={() => selectRoom(room)}>
    SELECT THIS ROOM
  </button>
</div>
```

### Data Fetching
```javascript
// Fetch room data from API
const response = await fetch('/api/public/hotel/hotel-killarney/page/');
const data = await response.json();

// Extract room types from rooms section
const roomsSection = data.sections.find(s => s.section_type === 'rooms');
const roomVariants = roomsSection.rooms_data.room_types;

// Group by room type name for display
const groupedRooms = roomVariants.reduce((acc, room) => {
  const key = room.room_type_name;
  if (!acc[key]) acc[key] = [];
  acc[key].push(room);
  return acc;
}, {});
```

### Room Selection Logic
```javascript
// Handle room selection with rate plan
const selectRoom = (roomVariant) => {
  const bookingUrl = roomVariant.booking_cta_url;
  // Navigate to booking flow with specific room and rate plan
  router.push(bookingUrl);
};

// Pre-select room from URL params
const urlParams = new URLSearchParams(window.location.search);
const preselectedRoomCode = urlParams.get('room_type_code');
const preselectedRatePlan = urlParams.get('rate_plan_code');

// Highlight matching room variant
const isPreselected = (room) => {
  return room.room_type_code === preselectedRoomCode && 
         (room.rate_plan_code === preselectedRatePlan || !preselectedRatePlan);
};
```

## Benefits

### For Hotels
1. **Multiple Pricing Strategies**: Different rate plans for different customer segments
2. **Revenue Optimization**: Early bird discounts, non-refundable rates
3. **Inventory Management**: Flexible pricing based on demand

### For Customers
1. **Price Transparency**: Clear display of all available rates
2. **Choice Flexibility**: Select based on refund policy preferences
3. **Savings Visibility**: Clear discount percentages and original prices

### For Developers
1. **Smart Grouping**: Automatically shows relevant variants
2. **Backward Compatibility**: Legacy single-price display still supported
3. **Extensible**: Easy to add new rate plan types and promotions

## Testing

Run the test script to see current pricing variants:
```bash
python test_room_pricing_variants.py
```

Current output shows 24 room variants across 6 room types with 4 different rate plans each.

## Future Enhancements

1. **Dynamic Pricing**: Date-based pricing with DailyRate model
2. **Promotion Codes**: Integration with Promotion model for additional discounts
3. **Availability Integration**: Real-time inventory checking
4. **A/B Testing**: Different pricing displays for optimization