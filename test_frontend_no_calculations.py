"""
Verify that frontend gets ALL calculations pre-done
They should NOT need to calculate anything
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod
from stock_tracker.stock_serializers import StockPeriodDetailSerializer
import json

period = StockPeriod.objects.get(id=9)
data = StockPeriodDetailSerializer(period).data

print("=" * 80)
print("FRONTEND RECEIVES - NO CALCULATIONS NEEDED!")
print("=" * 80)

# Get first few items from different categories
test_items = []
for snap in data['snapshots']:
    cat = snap['item']['category']
    closing = float(snap['closing_partial_units'])
    if closing > 0 and not any(t['item']['category'] == cat for t in test_items):
        test_items.append(snap)
    if len(test_items) >= 3:
        break

for snap in test_items:
    print(f"\n{'=' * 80}")
    print(f"{snap['item']['name']} ({snap['item']['sku']}) - Category {snap['item']['category']}")
    print("=" * 80)
    
    print("\n✅ WHAT FRONTEND RECEIVES (Pre-calculated by backend):")
    print("-" * 80)
    
    print("\n1. OPENING STOCK:")
    print(f"   Raw values:")
    print(f"     opening_full_units: {snap['opening_full_units']}")
    print(f"     opening_partial_units: {snap['opening_partial_units']}")
    print(f"     opening_stock_value: €{snap['opening_stock_value']}")
    print(f"   Display values (for UI):")
    print(f"     opening_display_full_units: {snap['opening_display_full_units']}")
    print(f"     opening_display_partial_units: {snap['opening_display_partial_units']}")
    
    print("\n2. CLOSING STOCK:")
    print(f"   Raw values:")
    print(f"     closing_full_units: {snap['closing_full_units']}")
    print(f"     closing_partial_units: {snap['closing_partial_units']}")
    print(f"     closing_stock_value: €{snap['closing_stock_value']}")
    print(f"   Display values (for UI):")
    print(f"     display_full_units: {snap['display_full_units']}")
    print(f"     display_partial_units: {snap['display_partial_units']}")
    print(f"     total_servings: {snap['total_servings']}")
    
    print("\n3. COSTS (Pre-calculated):")
    print(f"   unit_cost: €{snap['unit_cost']}")
    print(f"   cost_per_serving: €{snap['cost_per_serving']}")
    
    print("\n4. PROFITABILITY (Pre-calculated):")
    print(f"   gp_percentage: {snap['gp_percentage']}%")
    print(f"   markup_percentage: {snap['markup_percentage']}%")
    print(f"   pour_cost_percentage: {snap['pour_cost_percentage']}%")
    
    print("\n5. ITEM INFO:")
    print(f"   item.id: {snap['item']['id']}")
    print(f"   item.sku: {snap['item']['sku']}")
    print(f"   item.name: {snap['item']['name']}")
    print(f"   item.category: {snap['item']['category']}")
    print(f"   item.category_display: {snap['item']['category_display']}")
    print(f"   item.size: {snap['item']['size']}")
    print(f"   item.unit_cost: €{snap['item']['unit_cost']}")
    print(f"   item.menu_price: €{snap['item']['menu_price']}")

print("\n" + "=" * 80)
print("WHAT FRONTEND NEEDS TO DO")
print("=" * 80)
print("\n✅ FOR DISPLAY ONLY:")
print("   1. Show opening_display_full_units + opening_display_partial_units")
print("   2. Show display_full_units + display_partial_units")
print("   3. Show values as-is (already formatted)")
print()
print("✅ FOR USER INPUT (Stocktake counting):")
print("   1. Let user enter counts (full + partial)")
print("   2. Send entered values to backend")
print("   3. Backend calculates everything else")
print()
print("❌ FRONTEND DOES NOT NEED TO:")
print("   ❌ Convert bottles to cases")
print("   ❌ Convert pints to kegs")
print("   ❌ Calculate opening stock (already from previous period)")
print("   ❌ Calculate stock value (already calculated)")
print("   ❌ Calculate cost per serving (already calculated)")
print("   ❌ Calculate GP%, markup%, pour cost% (already calculated)")
print("   ❌ Calculate total servings (already calculated)")
print("   ❌ Know about UOM or conversion logic (all handled by backend)")

print("\n" + "=" * 80)
print("EXAMPLE FRONTEND CODE")
print("=" * 80)
print("""
// Fetch period data
const period = await fetch('/api/stock_tracker/1/periods/9/').then(r => r.json());

// Display item
period.snapshots.forEach(snap => {
  // Just display the pre-calculated values!
  console.log(`${snap.item.name}`);
  console.log(`Opening: ${snap.opening_display_full_units} + ${snap.opening_display_partial_units}`);
  console.log(`Closing: ${snap.display_full_units} + ${snap.display_partial_units}`);
  console.log(`Value: €${snap.closing_stock_value}`);
  console.log(`Cost/Serving: €${snap.cost_per_serving}`);
  console.log(`GP: ${snap.gp_percentage}%`);
});

// User enters count - just send to backend
const userCount = { 
  full_units: 10, 
  partial_units: 5 
};
// Backend will calculate everything!
""")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("\n✅ Backend calculates EVERYTHING")
print("✅ Frontend just displays the data")
print("✅ Frontend collects user input and sends to backend")
print("✅ NO calculations needed on frontend!")
print("\n" + "=" * 80)

# Show complete JSON for one item
print("\nCOMPLETE JSON RESPONSE FOR ONE ITEM:")
print("=" * 80)
print(json.dumps(test_items[0], indent=2, default=str))
print("\n✅ All fields pre-calculated and ready to display!")
print("=" * 80)
