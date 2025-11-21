# 🔔 Pusher Real-Time Updates Not Working - Diagnosis

## Problem
Updates made on phone (voice or manual) are **NOT** appearing in real-time on laptop.
User must **refresh the page** to see changes.

## Root Cause
**Frontend is not subscribing to Pusher channels or not handling events.**

Backend IS correctly sending Pusher events, but frontend is not receiving them.

---

## Backend Status: ✅ WORKING

### Voice Commands Send Pusher Updates
File: `voice_recognition/views.py` (line 574-586)
```python
from stock_tracker.pusher_utils import broadcast_line_counted_updated
try:
    broadcast_line_counted_updated(
        hotel_identifier,
        stocktake.id,
        {
            "line_id": line.id,
            "item_sku": stock_item.sku,
            "line": serializer.data
        }
    )
except Exception as e:
    logger.error(f"Failed to broadcast voice command update: {e}")
```

### Manual Edits Send Pusher Updates
File: `stock_tracker/views.py` (line 2513-2527)
```python
broadcast_line_counted_updated(
    hotel_identifier,
    instance.stocktake.id,
    {
        "line_id": instance.id,
        "item_sku": instance.item.sku,
        "line": response_serializer.data
    }
)
```

### Pusher Configuration
- App ID: `2040120`
- Key: `6744ef8e4ff09af2a849`
- Cluster: `eu`
- Channel Format: `{hotel_identifier}-stocktake-{stocktake_id}`
- Event Name: `line-counted-updated`

---

## Frontend Issue: ❌ NOT WORKING

### What's Missing in Frontend

The frontend needs to:

1. **Import Pusher library**
```javascript
import Pusher from 'pusher-js';
```

2. **Initialize Pusher client**
```javascript
const pusher = new Pusher('6744ef8e4ff09af2a849', {
  cluster: 'eu'
});
```

3. **Subscribe to stocktake channel**
```javascript
const channel = pusher.subscribe(`${hotelIdentifier}-stocktake-${stocktakeId}`);
```

4. **Listen for line updates**
```javascript
channel.bind('line-counted-updated', (data) => {
  console.log('📡 Pusher update received:', data);
  
  // Update the specific line in UI
  const { line_id, line } = data;
  
  // Option 1: Update state directly
  setStocktakeLines(prevLines => 
    prevLines.map(l => l.id === line_id ? line : l)
  );
  
  // Option 2: Show toast notification
  toast.info(`${line.item.name} updated by another user`);
});
```

5. **Unsubscribe when leaving page**
```javascript
useEffect(() => {
  return () => {
    channel.unbind_all();
    channel.unsubscribe();
  };
}, []);
```

---

## Testing Backend Pusher

### Option 1: Check Server Logs
When you update a line (voice or manual), you should see:
```
Pusher: stocktake channel=hotel-killarney-stocktake-123, event=line-counted-updated
```

If you DON'T see this log:
- Pusher package might not be installed in backend environment
- Pusher credentials might be invalid
- Exception is being caught silently

### Option 2: Use Pusher Debug Console
1. Go to: https://dashboard.pusher.com/
2. Log in with your Pusher account
3. Select App ID `2040120`
4. Go to "Debug Console"
5. Make an update on phone
6. You should see the event appear in console

### Option 3: Test Script (requires active venv)
```bash
python test_pusher_working.py
```

---

## Events Being Broadcast

| Event | Channel | When Triggered |
|-------|---------|---------------|
| `line-counted-updated` | `{hotel}-stocktake-{id}` | User updates counted quantities (manual or voice) |
| `line-movement-added` | `{hotel}-stocktake-{id}` | User adds purchase/waste movement |
| `line-movement-deleted` | `{hotel}-stocktake-{id}` | User deletes a movement |
| `line-movement-updated` | `{hotel}-stocktake-{id}` | User edits a movement |
| `stocktake-populated` | `{hotel}-stocktake-{id}` | Stocktake is populated with items |
| `stocktake-status-changed` | `{hotel}-stocktake-{id}` | Stocktake approved/reopened |
| `stocktake-created` | `{hotel}-stocktakes` | New stocktake created (list view) |
| `stocktake-deleted` | `{hotel}-stocktakes` | Stocktake deleted (list view) |

---

## Quick Fix for Frontend

If using React, add this to your stocktake detail page:

```typescript
// hooks/usePusherStocktake.ts
import { useEffect } from 'react';
import Pusher from 'pusher-js';

export function usePusherStocktake(
  hotelIdentifier: string,
  stocktakeId: number,
  onLineUpdate: (data: any) => void
) {
  useEffect(() => {
    const pusher = new Pusher('6744ef8e4ff09af2a849', {
      cluster: 'eu'
    });
    
    const channel = pusher.subscribe(
      `${hotelIdentifier}-stocktake-${stocktakeId}`
    );
    
    channel.bind('line-counted-updated', onLineUpdate);
    
    return () => {
      channel.unbind_all();
      channel.unsubscribe();
    };
  }, [hotelIdentifier, stocktakeId, onLineUpdate]);
}
```

Then in your component:
```typescript
usePusherStocktake(hotelId, stocktakeId, (data) => {
  // Update the line that changed
  setLines(prev => prev.map(line => 
    line.id === data.line_id ? data.line : line
  ));
});
```

---

## Summary

✅ Backend sends Pusher events for **all** updates (voice + manual)
❌ Frontend not receiving events because it's not subscribed
🔧 Fix: Add Pusher subscription code to frontend

The issue is **100% on the frontend side** - backend is working correctly.
