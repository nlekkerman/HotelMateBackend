# JUICE Input Flexibility - Both Formats Supported

## The Problem
Staff might enter juice counts in DIFFERENT ways:
- **Option A**: `3 cases + 3.5 bottles` (counting by cases)
- **Option B**: `39.5 bottles` (counting total bottles)

Both should work!

## How It Works

### Option A: User Enters Cases + Bottles
```
Input from frontend:
{
  "counted_cases": 3,
  "counted_bottles": 3.5,
  "counted_ml": 0
}

Backend converts to storage:
counted_full_units = (3 × 12) + 3.5 = 39.5 bottles
counted_partial_units = 0 ml
```

### Option B: User Enters Total Bottles Only
```
Input from frontend:
{
  "counted_bottles": 39.5  // or counted_full_units
}

Backend keeps as is:
counted_full_units = 39.5 bottles
counted_partial_units = 0 ml
```

### Display: Always Show Cases + Bottles
```
Storage: 39.5 bottles

Display conversion using helper:
39.5 bottles → 3 cases + 3.5 bottles

Frontend shows:
"3 cases, 3.5 bottles"
```

## Implementation in Serializer

```python
class StocktakeLineSerializer(serializers.ModelSerializer):
    # Accept optional 3-level input
    counted_cases = serializers.DecimalField(
        required=False, 
        allow_null=True,
        write_only=True
    )
    counted_bottles = serializers.DecimalField(
        required=False,
        allow_null=True, 
        write_only=True
    )
    counted_ml = serializers.DecimalField(
        required=False,
        allow_null=True,
        write_only=True
    )
    
    def update(self, instance, validated_data):
        # Check if 3-level input provided
        if 'counted_cases' in validated_data or 'counted_bottles' in validated_data:
            from stock_tracker.juice_helpers import cases_bottles_ml_to_bottles
            
            cases = validated_data.pop('counted_cases', 0) or 0
            bottles = validated_data.pop('counted_bottles', 0) or 0
            ml = validated_data.pop('counted_ml', 0) or 0
            
            # Convert to total bottles for storage
            if cases > 0 or bottles > 0:
                total_bottles = cases_bottles_ml_to_bottles(
                    cases, bottles, ml,
                    bottle_size_ml=instance.item.uom,
                    bottles_per_case=12
                )
                instance.counted_full_units = total_bottles
                instance.counted_partial_units = 0  # ml already in bottles
            
        # Normal update for other fields
        return super().update(instance, validated_data)
```

## Frontend Flexibility

### Scenario 1: Simple Input (Total Bottles)
```javascript
<Input 
  label="Total Bottles" 
  name="counted_full_units" 
  value="39.5"
/>
```

### Scenario 2: Detailed Input (Cases + Bottles + ml)
```javascript
<Input label="Cases" name="counted_cases" value="3" />
<Input label="Bottles" name="counted_bottles" value="3.5" />
<Input label="ml" name="counted_ml" value="0" />
```

Both work! Backend handles conversion automatically.

## Examples

### Example 1: Staff counts 3 cases + 3.5 bottles
```
POST /stocktake-lines/123/
{
  "counted_cases": 3,
  "counted_bottles": 3.5
}

Backend stores:
counted_full_units = 39.5

Frontend displays:
"3 cases, 3.5 bottles"
```

### Example 2: Staff counts 150.5 bottles total
```
POST /stocktake-lines/123/
{
  "counted_full_units": 150.5
}

Backend stores:
counted_full_units = 150.5

Frontend displays using helper:
"12 cases, 6.5 bottles"
```

### Example 3: Opening stock is 716 bottles
```
Current storage:
opening_qty = 716 (servings in bottles)

Display conversion:
716 bottles → 59 cases + 8 bottles

Frontend shows:
"59 cases, 8 bottles"
```

## Key Point

**Storage is always in total bottles** (counted_full_units), but:
- **Input** can be cases+bottles OR total bottles
- **Display** is always converted to cases+bottles for clarity

The helper function `bottles_to_cases_bottles_ml()` makes this seamless!
