# Phase R1 Implementation Plan: Multi-Hotel Integrity + Safe Uniqueness Constraints

## Overview
Implementing Phase R1 to enforce hotel-scoped uniqueness for restaurant and booking subcategory slugs, plus cross-hotel validation for booking references. Converting global slug constraints to per-hotel constraints through sequential migrations while safely handling existing data.

## Target Outcomes
- Convert global slug uniqueness into per-hotel slug uniqueness for `Restaurant.slug` and `BookingSubcategory.slug` using `(hotel, slug)` constraints
- Add model-level validation to enforce cross-hotel FK consistency in `Booking` model
- Add `BookingCategory` hotel consistency validation
- Ensure DRF serializers and admin forms trigger proper validation
- Create comprehensive tests for multi-hotel scenarios

## Implementation Steps

### Step 1: Migration A - Remove Global Unique Constraints
**File**: `bookings/migrations/000x_remove_global_slug_unique.py`

- Remove `unique=True` from `Restaurant.slug` field (line ~79)
- Remove `unique=True` from `BookingSubcategory.slug` field (line ~11)  
- Leave fields as regular `SlugField` without touching `Meta.constraints` yet
- **CRITICAL**: Do NOT add `UniqueConstraint` in models.py yet

### Step 2: Migration B - Data Migration Normalize Slugs
**File**: `bookings/migrations/000x_normalize_hotel_slugs.py`

**Deterministic slug normalization rules**:
- Generate slug using `slugify(name) or "item"` 
- Process ordered by `hotel_id` (outer loop), then by `id` within each hotel for deterministic results
- Handle per-hotel collisions by appending `-2, -3, etc.`
- Use `bulk_update(updates, ["slug"])` per hotel for performance
- **No row deletion** - only slug updates

**Implementation approach**:
```python
def normalize_slugs_forward(apps, schema_editor):
    from django.utils.text import slugify
    
    Restaurant = apps.get_model('bookings', 'Restaurant')
    BookingSubcategory = apps.get_model('bookings', 'BookingSubcategory')
    
    for model in [Restaurant, BookingSubcategory]:
        # Process by hotel to ensure per-hotel uniqueness
        for hotel_id in model.objects.values_list('hotel_id', flat=True).distinct():
            used_slugs = set()
            updates = []
            
            # Deterministic ordering
            objects = model.objects.filter(hotel_id=hotel_id).order_by('id')
            
            for obj in objects:
                base_slug = slugify(obj.name) or "item"
                final_slug = base_slug
                counter = 2
                
                # Handle collisions within hotel
                while final_slug in used_slugs:
                    final_slug = f"{base_slug}-{counter}"
                    counter += 1
                
                used_slugs.add(final_slug)
                
                if obj.slug != final_slug:
                    obj.slug = final_slug
                    updates.append(obj)
            
            # Bulk update per hotel
            if updates:
                model.objects.bulk_update(updates, ['slug'])
```

### Step 3: Migration C - Add Hotel-Scoped Constraints  
**File**: `bookings/migrations/000x_add_hotel_scoped_constraints.py`

**Model changes first**:
- Add `Meta.constraints` to `Restaurant` and `BookingSubcategory` models
- Generate migration to apply DB constraints

**New Meta constraints**:
```python
class Restaurant(models.Model):
    # ... existing fields ...
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hotel", "slug"], 
                name="uniq_restaurant_hotel_slug"
            )
        ]

class BookingSubcategory(models.Model):
    # ... existing fields ...
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["hotel", "slug"], 
                name="uniq_booking_subcategory_hotel_slug"
            )
        ]
```

### Step 4: Cross-Hotel Validation in Models
**File**: `bookings/models.py`

**Enhanced `Booking.clean()` method**:
```python
def clean(self):
    """Validate time constraints and cross-hotel FK consistency."""
    errors = {}
    
    # Existing time validation
    if self.start_time and self.end_time and self.end_time <= self.start_time:
        errors['end_time'] = "End time must be later than start time."
    
    # Cross-hotel FK validation
    if self.restaurant_id and self.restaurant.hotel_id != self.hotel_id:
        errors['restaurant'] = "Restaurant belongs to a different hotel."
    
    if self.category_id and self.category.hotel_id != self.hotel_id:
        errors['category'] = "Category belongs to a different hotel."
    
    if self.category_id and self.category.subcategory.hotel_id != self.hotel_id:
        errors['subcategory'] = "Subcategory belongs to a different hotel."
    
    if self.room_id and self.room.hotel_id != self.hotel_id:
        errors['room'] = "Room belongs to a different hotel."
    
    if errors:
        raise ValidationError(errors)
```

**New `BookingCategory.clean()` method**:
```python
def clean(self):
    """Validate hotel consistency between category and subcategory."""
    if self.subcategory_id and self.hotel_id != self.subcategory.hotel_id:
        raise ValidationError({
            'hotel': "Category hotel must match subcategory hotel."
        })
```

**Note**: Ensure `BookingCategory.clean()` is actually called by adding `full_clean()` to BookingCategory serializers and admin forms (same pattern as Booking).

### Step 5: DRF Serializer Validation
**Files**: `bookings/serializers.py`

**Ensure serializers trigger model validation**:
- Add `full_clean()` calls in `create()` and `update()` methods
- OR duplicate validation logic in `validate()` methods
- Ensure field-specific errors are properly returned to frontend

**Implementation options**:
```python
class BookingSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = Booking(**validated_data)
        instance.full_clean()  # Triggers model.clean()
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean()  # Triggers model.clean()
        instance.save()
        return instance
```

### Step 6: Admin Form Validation
**File**: `bookings/admin.py`

**Ensure admin forms prevent cross-hotel assignments**:
- Override admin form classes to call `full_clean()`
- Add custom form validation if needed
- Use hotel-filtered querysets for FK fields

### Step 7: Comprehensive Testing
**File**: `bookings/tests.py`

**Test cases to implement**:

1. **Same slug different hotels** (should succeed):
   ```python
   def test_same_slug_different_hotels_allowed(self):
       # Create two hotels with restaurants having same slug
       # Should succeed after constraints are per-hotel
   ```

2. **Cross-hotel FK validation** (should fail):
   ```python
   def test_booking_restaurant_different_hotel_fails(self):
       # Try to create booking with restaurant from different hotel
       # Should raise ValidationError with field-specific message
   
   def test_booking_room_different_hotel_fails(self):
       # Try to create booking with room from different hotel
   
   def test_booking_category_different_hotel_fails(self):
       # Try to create booking with category from different hotel
   ```

3. **BookingCategory consistency** (should fail):
   ```python
   def test_category_subcategory_hotel_mismatch_fails(self):
       # Try to create category with subcategory from different hotel
   ```

4. **Slug collision resolution**:
   ```python
   def test_slug_collision_resolution_deterministic(self):
       # Test that migration creates breakfast, breakfast-2, breakfast-3
   ```

5. **DRF serializer validation**:
   ```python
   def test_serializer_triggers_cross_hotel_validation(self):
       # Test that DRF API calls trigger model validation
   ```

## Migration Sequence Summary

1. **Migration A**: Remove `unique=True` from slug fields
2. **Migration B**: Data migration to normalize slugs per hotel  
3. **Migration C**: Add `UniqueConstraint(fields=["hotel", "slug"])` 

## Key Safety Measures

- **Deterministic processing**: Order by `(hotel_id, id)` for consistent results
- **No data loss**: Only update slugs, never delete rows
- **Performance**: Use `bulk_update()` per hotel batch
- **Field-specific errors**: Use dict format for `ValidationError`
- **Comprehensive testing**: Cover all cross-hotel scenarios

## Validation Layers

1. **Model level**: `clean()` methods with field-specific errors
2. **Serializer level**: `full_clean()` calls or duplicate validation
3. **Admin level**: Form validation to prevent manual mistakes
4. **Database level**: `UniqueConstraint` for slug uniqueness

## Files to Modify

- `bookings/models.py` - Model constraints and validation methods
- `bookings/serializers.py` - Serializer validation integration  
- `bookings/admin.py` - Admin form validation
- `bookings/tests.py` - Comprehensive test coverage
- `bookings/migrations/` - Three sequential migrations

## Success Criteria

✅ Restaurant and BookingSubcategory slugs are unique per hotel, not globally  
✅ Booking creation fails with clear errors when FKs reference different hotels  
✅ BookingCategory creation fails when hotel != subcategory.hotel  
✅ DRF API enforces validation through serializers  
✅ Django admin prevents cross-hotel assignments  
✅ All existing data preserved with deterministic slug resolution  
✅ Comprehensive test coverage for multi-hotel scenarios