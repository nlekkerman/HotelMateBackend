# Stock Tracker Documentation Index

## 📚 Quick Navigation

### For Frontend Developers

1. **[FRONTEND_UOM_QUICK_GUIDE.md](./FRONTEND_UOM_QUICK_GUIDE.md)** ⭐ **START HERE**
   - Simple, visual guide for displaying UOM and yields
   - Code examples and UI mockups
   - Focus on 30L and 50L kegs
   - **Read this first!**

2. **[UOM_CHEAT_SHEET.md](./UOM_CHEAT_SHEET.md)** 📋 **PRINT & KEEP**
   - Visual reference cards
   - Quick calculations
   - Color coding suggestions
   - Mobile display examples

3. **[STOCK_TRACKER_FRONTEND_GUIDE.md](./STOCK_TRACKER_FRONTEND_GUIDE.md)**
   - Complete frontend integration guide
   - API endpoints and responses
   - State management examples

### For Backend/Technical Details

4. **[UOM_SERVING_YIELD_GUIDE.md](./UOM_SERVING_YIELD_GUIDE.md)**
   - Comprehensive technical documentation
   - Formula explanations
   - All product types covered
   - Backend calculation details

5. **[STOCK_TRACKER_API_GUIDE.md](./STOCK_TRACKER_API_GUIDE.md)**
   - Full API documentation
   - Request/response examples
   - Authentication & permissions

6. **[STOCK_TRACKER_ENDPOINTS.md](./STOCK_TRACKER_ENDPOINTS.md)**
   - Endpoint reference
   - Query parameters
   - Error handling

---

## 🎯 Quick Reference

### Keg Sizes (All Three Supported)

| Size | Pints | Half-Pints | Your Stock |
|------|-------|------------|------------|
| **20L** | **35.2** | **70.4** | **1 brand** |
| **30L** | **52.8** | **105.6** | **11 brands** ⭐ |
| **50L** | **88.0** | **176.0** | **3 brands** |

**Note:** Each keg size = Separate SKU (e.g., Heineken 30L ≠ Heineken 50L)

### Spirit Bottles

| Size | 25ml Shot | 35ml Shot |
|------|-----------|-----------|
| **70cl** | **28 shots** | **20 shots** ⭐ |
| 1L | 40 shots | 28 shots |

### API Fields (Read-Only)

```typescript
{
  pints_per_keg: number;        // For Draught
  half_pints_per_keg: number;   // For Draught
  shots_per_bottle: number;     // For Spirits
  servings_per_unit: number;    // General
}
```

---

## 📖 Reading Order

### New to the Project?
1. **FRONTEND_UOM_QUICK_GUIDE.md** - Get up to speed fast
2. **UOM_CHEAT_SHEET.md** - Visual reference
3. **STOCK_TRACKER_FRONTEND_GUIDE.md** - Deep dive

### Implementing Stock Features?
1. **STOCK_TRACKER_FRONTEND_GUIDE.md** - Full integration
2. **STOCK_TRACKER_API_GUIDE.md** - API details
3. **UOM_SERVING_YIELD_GUIDE.md** - Technical specs

### Need Quick Answers?
1. **UOM_CHEAT_SHEET.md** - Visual lookup
2. **STOCK_TRACKER_ENDPOINTS.md** - API reference

---

## 🔍 Search by Topic

### Kegs (30L, 50L)
- **FRONTEND_UOM_QUICK_GUIDE.md** - Section: "Draught Beer"
- **UOM_CHEAT_SHEET.md** - Section: "Keg Size Reference"
- **UOM_SERVING_YIELD_GUIDE.md** - Section: "Draught Beer (Kegs)"

### Spirits (Shots)
- **FRONTEND_UOM_QUICK_GUIDE.md** - Section: "Spirits & Liqueurs"
- **UOM_CHEAT_SHEET.md** - Section: "Spirit Bottle Reference"
- **UOM_SERVING_YIELD_GUIDE.md** - Section: "Spirits & Liqueurs"

### Bottled Beer
- **FRONTEND_UOM_QUICK_GUIDE.md** - Section: "Bottled Beer"
- **UOM_CHEAT_SHEET.md** - Section: "Bottled Beer Reference"

### Stocktake Counting
- **FRONTEND_UOM_QUICK_GUIDE.md** - Section: "Stocktake Counting Guide"
- **UOM_CHEAT_SHEET.md** - Section: "Stocktake Display Examples"
- **STOCK_TRACKER_FRONTEND_GUIDE.md** - Section: "Stocktake"

### API Integration
- **STOCK_TRACKER_API_GUIDE.md** - Complete API docs
- **STOCK_TRACKER_ENDPOINTS.md** - Endpoint reference
- **STOCK_TRACKER_FRONTEND_GUIDE.md** - Frontend examples

---

## 💡 Common Questions

### "How do I display keg yields?"
→ See **FRONTEND_UOM_QUICK_GUIDE.md** - "Draught Beer" section

### "What's the difference between 30L and 50L kegs?"
→ See **UOM_CHEAT_SHEET.md** - "Keg Size Reference"
- 30L = 52.8 pints (most common)
- 50L = 88.0 pints (high volume)

### "How are shots calculated?"
→ See **UOM_SERVING_YIELD_GUIDE.md** - "Spirits & Liqueurs"
- 70cl bottle ÷ 25ml shot = 28 shots

### "Do I need to calculate yields manually?"
→ **NO!** All yields are auto-calculated by the backend
→ See **FRONTEND_UOM_QUICK_GUIDE.md** - "Important Notes"

### "What API fields are available?"
→ See **STOCK_TRACKER_ENDPOINTS.md** - StockItem fields

---

## 🚀 Implementation Checklist

### Frontend Developer Tasks

- [ ] Read **FRONTEND_UOM_QUICK_GUIDE.md**
- [ ] Print **UOM_CHEAT_SHEET.md** for reference
- [ ] Implement display logic for product types
- [ ] Add yield display to stock item cards/tables
- [ ] Test with 30L and 50L kegs
- [ ] Test with 70cl spirit bottles
- [ ] Implement stocktake counting UI
- [ ] Add helper text for different product types

### Backend Integration Tasks

- [ ] Review **STOCK_TRACKER_API_GUIDE.md**
- [ ] Understand **UOM_SERVING_YIELD_GUIDE.md** calculations
- [ ] Test API endpoints
- [ ] Verify yield calculations
- [ ] Check edge cases (null values, zero sizes)

---

## 📝 Notes

- **30L kegs** are the most common size
- **50L kegs** are used in high-volume venues
- All yields are **read-only** from the API
- Backend handles all calculations automatically
- Update `size` or `serving_size` to recalculate yields

---

## 🆘 Need Help?

1. Check the appropriate guide from the list above
2. Search for your topic using Ctrl+F in the guides
3. Review code examples in **FRONTEND_UOM_QUICK_GUIDE.md**
4. Contact backend team for technical issues

---

## 📂 File Organization

```
docs/
├── README.md (this file)
│
├── Quick Start (Frontend)
│   ├── FRONTEND_UOM_QUICK_GUIDE.md ⭐
│   └── UOM_CHEAT_SHEET.md 📋
│
├── Complete Guides
│   ├── STOCK_TRACKER_FRONTEND_GUIDE.md
│   ├── STOCK_TRACKER_API_GUIDE.md
│   └── UOM_SERVING_YIELD_GUIDE.md
│
└── API Reference
    └── STOCK_TRACKER_ENDPOINTS.md
```

---

**Last Updated:** November 6, 2025
**Maintained By:** HotelMate Backend Team
