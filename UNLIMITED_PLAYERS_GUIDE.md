# Unlimited Players Leaderboard API Guide

## 🚀 **UNLIMITED PLAYERS SUPPORTED!**

Perfect for hotel tournaments where hundreds of kids can participate!

## 🎯 **Leaderboard API Endpoints**

### **1. General Memory Game Leaderboard**
```
GET /api/entertainment/memory-sessions/leaderboard/
```

**Default Limit:** `10` entries  
**Maximum Limit:** `UNLIMITED` ✅ (Can handle hundreds of players!)  

### **2. Tournament Leaderboard**
```
GET /api/entertainment/tournaments/{id}/leaderboard/
```

**Default Limit:** `20` entries  
**Maximum Limit:** `UNLIMITED` ✅ (Perfect for large hotel tournaments!)

## 📊 **API Parameters**

Both endpoints support:
- `limit` (optional): Number of entries to return
  - Default: 10 (general) / 20 (tournament)  
  - **Maximum: UNLIMITED** - Request as many as needed!

**Example Requests:**
```javascript
// Show ALL tournament players (no limit)
GET /api/entertainment/tournaments/23/leaderboard/?limit=999999

// Show top 500 hotel-wide players
GET /api/entertainment/memory-sessions/leaderboard/?limit=500&hotel=hotel-killarney

// Show ALL players from specific hotel
GET /api/entertainment/memory-sessions/leaderboard/?limit=10000&hotel=hotel-killarney
```

## 🏨 **Hotel Tournament Scenarios**

### **Large Kids Tournament (200+ players):**
```javascript
// Get complete tournament results - ALL players
const allPlayers = await fetch(
    `/api/entertainment/tournaments/23/leaderboard/?limit=1000`
);

// Show everyone who participated
const results = await allPlayers.json();
console.log(`Total participants: ${results.length}`); // Could be 300+!
```

### **Hotel-Wide Leaderboard (500+ games):**
```javascript
// Get all scores from this hotel
const hotelLeaderboard = await fetch(
    `/api/entertainment/memory-sessions/leaderboard/?limit=2000&hotel=resort-paradise`
);
```

## 📱 **Frontend Strategies for Large Lists**

### **1. Pagination (Recommended)**
```javascript
class PaginatedLeaderboard {
    constructor() {
        this.pageSize = 50;  // Show 50 at a time
        this.currentPage = 1;
    }
    
    async loadPage(page) {
        const startIndex = (page - 1) * this.pageSize;
        const limit = page * this.pageSize;
        
        const response = await fetch(
            `/api/entertainment/tournaments/23/leaderboard/?limit=${limit}`
        );
        const allData = await response.json();
        
        // Return only the current page
        return allData.slice(startIndex, startIndex + this.pageSize);
    }
}
```

### **2. Virtual Scrolling (For 100+ players)**
```javascript
class VirtualScrollLeaderboard {
    async loadAllPlayers() {
        // Load ALL players at once - no artificial limits!
        const response = await fetch(
            `/api/entertainment/tournaments/23/leaderboard/?limit=5000`
        );
        const allPlayers = await response.json();
        
        // Use virtual scrolling to render efficiently
        this.setupVirtualScroll(allPlayers);
    }
}
```

### **3. Progressive Loading**
```javascript
class ProgressiveLeaderboard {
    constructor() {
        this.batchSize = 25;
        this.currentIndex = 0;
        this.allData = [];
    }
    
    async loadMore() {
        this.currentIndex += this.batchSize;
        
        // Request more data (still no backend limit!)
        const response = await fetch(
            `/api/entertainment/tournaments/23/leaderboard/?limit=${this.currentIndex + this.batchSize}`
        );
        const data = await response.json();
        
        // Extract new entries
        const newEntries = data.slice(this.currentIndex);
        this.allData.push(...newEntries);
        
        return newEntries;
    }
}
```

## 🎯 **Recommended Frontend Limits by Context**

| Context | Recommended Frontend Limit | Reason |
|---------|---------------------------|---------|
| **Mobile View** | 10-20 | Screen space limited |
| **Tablet View** | 25-50 | Better screen real estate |
| **Desktop View** | 50-100 | Can show more data |
| **Tournament Results** | ALL players | Show complete results |
| **Admin/Analytics** | ALL data | Need complete picture |
| **Prize Winner Display** | 3-10 | Focus on winners |

## 💪 **Backend Performance**

The backend can handle large requests efficiently:
- ✅ **Database optimized** for large result sets
- ✅ **No artificial caps** - request what you need
- ✅ **Clean player names** extracted from tokens
- ✅ **Proper sorting** by score and time
- ✅ **Hotel filtering** to reduce result sets when needed

## 🚀 **Use Cases Now Supported:**

### ✅ **Large Hotel Tournaments**
- 200+ kids in tournament
- Show ALL participants and rankings
- No missing players due to arbitrary limits

### ✅ **Hotel-Wide Statistics**
- Track all games across entire hotel
- Analyze patterns across hundreds of sessions
- Complete leaderboards for hotel dashboards

### ✅ **Analytics & Reporting**
- Export complete tournament data
- Generate comprehensive reports
- No data truncation

## 🎉 **Perfect for Hotels!**

With unlimited players support, your tournament system can now handle:
- **Large resort tournaments** (300+ kids)
- **Multi-day events** (accumulating hundreds of scores)  
- **Hotel chain competitions** (unlimited participants)
- **Complete historical data** (all scores ever recorded)

The frontend controls the display limits based on UI needs, while the backend provides complete, unlimited data access!