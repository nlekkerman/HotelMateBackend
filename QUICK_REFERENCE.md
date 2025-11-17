# Quick Reference Card - Stock Tracker Changes

## 🚨 Emergency Fix (If You're Seeing 500 Errors)

### Error Message:
```
IntegrityError: duplicate key value violates unique constraint
"stock_tracker_stocktake_hotel_id_period_start_pe_7d16c4a2_uniq"
```

### Quick Fix (Copy-Paste This):
```javascript
// Before creating stocktake, check if it exists:
async function createStocktake(periodStart, periodEnd) {
  // 1. Check for existing
  const existing = await fetch(
    `/api/stock_tracker/hotel-killarney/stocktakes/` +
    `?period_start=${periodStart}&period_end=${periodEnd}`
  ).then(r => r.json());
  
  if (existing.results?.length > 0) {
    // Navigate to existing instead
    navigate(`/stocktakes/${existing.results[0].id}`);
    return existing.results[0];
  }
  
  // 2. Create new if doesn't exist
  const response = await fetch(
    '/api/stock_tracker/hotel-killarney/stocktakes/',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ period_start: periodStart, period_end: periodEnd })
    }
  );
  
  return await response.json();
}
```

---

## 📋 What Changed (30-Second Version)

### Three Bugs Fixed ✅
1. Opening stock was missing kegs/cases (only showing pints/bottles)
2. Categories without closing stock showed fake opening values
3. Stock movements were auto-updating deprecated fields

### Impact on Your Code
**Breaking Changes:** NONE
**Action Required:** Prevent duplicate stocktake creation (see above)
**Deprecations:** `current_full_units` and `current_partial_units` no longer auto-update

---

## 🎯 One-Minute Quick Start

### For Frontend Devs:
1. Read: [FRONTEND_DUPLICATE_STOCKTAKE_FIX.md](./FRONTEND_DUPLICATE_STOCKTAKE_FIX.md)
2. Implement duplicate check (5 minutes)
3. Test with February 2025
4. Done! ✅

### For Backend Devs:
1. Read: [BACKEND_CHANGES_NOVEMBER_2025.md](./BACKEND_CHANGES_NOVEMBER_2025.md)
2. Review changes in:
   - `stocktake_service.py` (lines 94-103)
   - `models.py` (StockMovement.save)
   - `stock_serializers.py` (deprecation comments)
3. Done! ✅

### For Everyone Else:
1. Read: [SUMMARY.md](./SUMMARY.md)
2. Ask questions if needed
3. Done! ✅

---

## 📚 Full Documentation

| Document | When to Use It | Time |
|----------|---------------|------|
| [DOCS_INDEX.md](./DOCS_INDEX.md) | Always start here | 2 min |
| [FRONTEND_DUPLICATE_STOCKTAKE_FIX.md](./FRONTEND_DUPLICATE_STOCKTAKE_FIX.md) | Fixing 500 error | 5 min |
| [SUMMARY.md](./SUMMARY.md) | Team sync / overview | 10 min |
| [BACKEND_CHANGES_NOVEMBER_2025.md](./BACKEND_CHANGES_NOVEMBER_2025.md) | Deep technical dive | 20 min |
| [FILE_MANIFEST.md](./FILE_MANIFEST.md) | Maintaining docs | 5 min |

---

## ⚡ Key Facts

- **Date Fixed:** November 17, 2025
- **Bugs Fixed:** 3 critical bugs
- **Backend Changes:** 3 files modified
- **Frontend Changes:** 0 breaking, 1 action required
- **API Changes:** None (backward compatible)
- **Database Changes:** None
- **Deployment Risk:** Low
- **Testing Status:** Backend ✅ | Frontend ⏳

---

## 🔗 Common Scenarios

### "Help! Users can't create stocktakes!"
→ Implement duplicate check from [FRONTEND_DUPLICATE_STOCKTAKE_FIX.md](./FRONTEND_DUPLICATE_STOCKTAKE_FIX.md)

### "Why is current stock showing old data?"
→ Use snapshots instead of `current_*` fields (see [BACKEND_CHANGES_NOVEMBER_2025.md](./BACKEND_CHANGES_NOVEMBER_2025.md))

### "Where does opening stock come from?"
→ Previous period's closing snapshot `total_servings` property

### "I need to explain this to my manager"
→ Share [SUMMARY.md](./SUMMARY.md)

### "I'm new and confused"
→ Start with [DOCS_INDEX.md](./DOCS_INDEX.md)

---

## 🎓 Cheat Sheet

### Data Flow (One Line)
```
Previous Closing Snapshot → total_servings → Next Opening Stock
```

### Key Property
```python
snapshot.total_servings = (full_units × uom) + partial_units
```

### Deprecated Fields (Still Exist, Not Auto-Updated)
```javascript
// ❌ OLD (may be stale):
item.current_full_units
item.current_partial_units

// ✅ NEW (always accurate):
snapshot.closing_full_units
snapshot.closing_partial_units
snapshot.total_servings
```

### Duplicate Prevention Pattern
```javascript
const existing = await checkExisting(period_start, period_end);
if (existing) navigate(`/stocktakes/${existing.id}`);
else create();
```

---

## ✅ Quick Checklist

Frontend Team:
- [ ] Read duplicate fix guide (5 min)
- [ ] Implement duplicate check (30 min)
- [ ] Test with existing period (5 min)
- [ ] Deploy fix

Backend Team:
- [x] Fix Bug #1 (opening stock full units)
- [x] Fix Bug #2 (ghost categories)
- [x] Fix Bug #3 (auto-update conflict)
- [x] Add deprecation comments
- [x] Create documentation
- [x] Test with 5 periods

---

## 📞 Get Help

**Quick Questions:** Check FAQ in [SUMMARY.md](./SUMMARY.md)

**Technical Details:** See [BACKEND_CHANGES_NOVEMBER_2025.md](./BACKEND_CHANGES_NOVEMBER_2025.md)

**Implementation Help:** See [FRONTEND_DUPLICATE_STOCKTAKE_FIX.md](./FRONTEND_DUPLICATE_STOCKTAKE_FIX.md)

**Still Stuck?** Contact backend team

---

**Print this card and keep it handy! 📌**

Last Updated: November 17, 2025
