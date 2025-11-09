"""
Test Hotel-Wide Movement System
Only PURCHASE, SALE, WASTE (no transfers/adjustments)
"""

print("="*80)
print("HOTEL-WIDE STOCK SYSTEM - SIMPLIFIED")
print("="*80)

print("\n✅ ALLOWED MOVEMENT TYPES:")
print("   • PURCHASE - Stock coming into hotel")
print("   • SALE - Stock sold to guests")
print("   • WASTE - Breakage, spillage, spoilage")

print("\n❌ REMOVED (Not needed for hotel-wide):")
print("   • TRANSFER_IN - Only for multi-outlet (bar to bar)")
print("   • TRANSFER_OUT - Only for multi-outlet (bar to bar)")
print("   • ADJUSTMENT - Only for multi-outlet corrections")

print("\n" + "="*80)
print("EXAMPLE: Cronin's 0.0% Beer")
print("="*80)

# Starting stock
opening = 69
purchases = 24
sales = 12
waste = 5

print(f"\n📦 Opening Stock: {opening} bottles")
print(f"📥 Purchases: +{purchases} bottles (delivery received)")
print(f"💰 Sales: -{sales} bottles (sold to guests)")
print(f"💥 Waste: -{waste} bottles (broke during service)")

expected = opening + purchases - sales - waste
print(f"\n📊 Expected Stock:")
print(f"   = Opening + Purchases - Sales - Waste")
print(f"   = {opening} + {purchases} - {sales} - {waste}")
print(f"   = {expected} bottles")

# Counted stock
counted = 76
variance = counted - expected

print(f"\n🔍 Physical Count: {counted} bottles")
print(f"📈 Variance: {variance:+d} bottles")

if variance == 0:
    print("   ✅ Perfect match!")
elif variance > 0:
    print(f"   ⚠️  Surplus of {variance} bottles")
else:
    print(f"   ⚠️  Shortage of {abs(variance)} bottles")

print("\n" + "="*80)
print("API EXAMPLES")
print("="*80)

print("\n1️⃣  ADD PURCHASE:")
print("""
POST /api/hotels/{hotel}/stock-tracker/stocktake-lines/{line_id}/add-movement/
{
    "movement_type": "PURCHASE",
    "quantity": 24,
    "reference": "INV-2024-001",
    "notes": "Weekly delivery"
}
""")

print("\n2️⃣  ADD SALE:")
print("""
POST /api/hotels/{hotel}/stock-tracker/stocktake-lines/{line_id}/add-movement/
{
    "movement_type": "SALE",
    "quantity": 12,
    "notes": "POS integration sync"
}
""")

print("\n3️⃣  ADD WASTE:")
print("""
POST /api/hotels/{hotel}/stock-tracker/stocktake-lines/{line_id}/add-movement/
{
    "movement_type": "WASTE",
    "quantity": 5,
    "notes": "Dropped tray, 5 bottles broke"
}
""")

print("\n❌ INVALID (Will be rejected):")
print("""
POST /api/hotels/{hotel}/stock-tracker/stocktake-lines/{line_id}/add-movement/
{
    "movement_type": "TRANSFER_IN",  ← NOT ALLOWED!
    "quantity": 10
}

Response: 400 Bad Request
{
    "error": "Invalid movement_type. Must be one of: PURCHASE, SALE, WASTE"
}
""")

print("\n" + "="*80)
print("FORMULA (Simplified)")
print("="*80)

print("""
Expected Qty = Opening + Purchases - Sales - Waste

Variance = Counted - Expected

That's it! No transfers, no adjustments.
Everything is hotel-wide, not outlet-specific.
""")

print("="*80)
print("✅ SYSTEM READY FOR HOTEL-WIDE STOCK TRACKING")
print("="*80)
