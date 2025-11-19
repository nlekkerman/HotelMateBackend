"""
HEROKU LOG PATTERNS TO WATCH FOR
=================================

When you click "Approve and Close" in frontend, look for these in Heroku logs:
"""

print("="*80)
print("PATTERNS TO SEARCH IN HEROKU LOGS")
print("="*80)

print("""
1. APPROVE-AND-CLOSE REQUEST:
   Look for: "POST /api/v1/hotel-killarney/periods/{id}/approve-and-close/"
   Example: method=POST path="/api/v1/hotel-killarney/periods/30/approve-and-close/"
   
2. STATUS CODES TO WATCH:
   ✅ 200 = Success (snapshots created)
   ❌ 400 = Bad request (period already closed, or stocktake missing)
   ❌ 404 = Not found (stocktake doesn't exist)
   ❌ 500 = Server error (check error message)

3. ERROR MESSAGES TO LOOK FOR:
   - "Period is already closed"
   - "No stocktake found for this period"
   - "Can only approve draft stocktakes"
   - "DoesNotExist: StockPeriod matching query does not exist"
   - Python tracebacks with approve_stocktake

4. SUCCESS INDICATORS:
   - Status 200
   - Response contains: "Stocktake approved and period closed successfully"
   - Response contains: "adjustments_created": <number>

5. TO DEBUG ZERO OPENING BALANCES:
   Look for GET requests to:
   - "/api/v1/hotel-killarney/stocktakes/{id}/"
   - "/api/v1/hotel-killarney/periods/{id}/stocktake/"
   
   In response, check if stocktake lines have:
   - "opening_full_units": 0.00
   - "opening_partial_units": 0.00
   
   If all zeros → Previous period has NO snapshots

6. CURRENT SITUATION:
   - February stocktake WAS approved BUT didn't create snapshots
   - This is why March opening stock = ZERO
   - Fix is deployed in views.py but Heroku needs to be updated
""")

print("\n" + "="*80)
print("STEPS TO TEST")
print("="*80)

print("""
1. Make sure Heroku has latest code:
   git add stock_tracker/views.py
   git commit -m "Fix approve-and-close to create snapshots"
   git push heroku main

2. From frontend, trigger approve-and-close for March period

3. Watch Heroku logs for:
   - POST approve-and-close request
   - Status code (should be 200)
   - Any error messages

4. After approval, check if March snapshots were created:
   - Query: StockSnapshot.objects.filter(period_id=30).count()
   - Should be 253 snapshots

5. Create April period and check if opening stock populates
""")

print("\n" + "="*80)
print("QUICK FIX FOR EXISTING DATA")
print("="*80)

print("""
Since February already approved without creating snapshots:

Option A - Re-approve February:
   python fix_february_snapshots.py
   (Changes Feb status to DRAFT, re-approves to create snapshots)
   
Option B - Manually create Feb snapshots:
   Use February stocktake lines to create snapshots
   
Option C - Wait for next approval:
   March approval will work correctly with new code
   But March opening will still be zero (Feb has no snapshots)
   April opening will be correct (March will have snapshots)

Recommendation: Option A - Re-approve February to fix historical data
""")
