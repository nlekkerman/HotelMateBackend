# Frontend Pusher Integration - Stocktake Real-Time Updates

## Overview

All stocktake-related changes broadcast real-time events via **Pusher**. This means when one user makes changes, all other users viewing the same stocktake will see updates instantly without needing to refresh.

---

## Pusher Configuration

### 1. Install Pusher JS Library

```bash
npm install pusher-js
```

### 2. Initialize Pusher Client

```javascript
import Pusher from 'pusher-js';

const pusher = new Pusher(process.env.PUSHER_KEY, {
  cluster: process.env.PUSHER_CLUSTER,
  encrypted: true
});
```

---

## Channel Structure

### Channel Naming Convention

There are **two types of channels** for stocktakes:

#### 1. Hotel Stocktakes List Channel
For users viewing the stocktakes list page:

```javascript
const channel = pusher.subscribe(`${hotelIdentifier}-stocktakes`);
// Example: "hotel-killarney-stocktakes"
```

**Events on this channel:**
- `stocktake-created` - New stocktake was created
- `stocktake-deleted` - Stocktake was deleted
- `stocktake-status-changed` - Stocktake was approved/changed status

#### 2. Specific Stocktake Detail Channel
For users viewing a specific stocktake's details:

```javascript
const channel = pusher.subscribe(`${hotelIdentifier}-stocktake-${stocktakeId}`);
// Example: "hotel-killarney-stocktake-5"
```

**Events on this channel:**
- `stocktake-populated` - Stocktake was populated with items
- `stocktake-status-changed` - Stocktake was approved
- `line-counted-updated` - User updated counted quantities on a line
- `line-movement-added` - Purchase/waste movement was added to a line

---

## Event Handlers by View

### 📋 Stocktakes List Page

```javascript
// Subscribe to hotel stocktakes channel
const hotelChannel = pusher.subscribe(`${hotelIdentifier}-stocktakes`);

// 1. New stocktake created
hotelChannel.bind('stocktake-created', (data) => {
  console.log('New stocktake created:', data);
  
  // Add new stocktake to the list
  setStocktakes(prev => [data, ...prev]);
  
  // Show toast notification
  toast.success(`New stocktake created for ${data.period_start} - ${data.period_end}`);
});

// 2. Stocktake deleted
hotelChannel.bind('stocktake-deleted', (data) => {
  console.log('Stocktake deleted:', data.stocktake_id);
  
  // Remove from list
  setStocktakes(prev => 
    prev.filter(st => st.id !== data.stocktake_id)
  );
  
  toast.info('A stocktake was deleted');
});

// 3. Stocktake status changed (DRAFT → APPROVED)
hotelChannel.bind('stocktake-status-changed', (data) => {
  console.log('Stocktake status changed:', data);
  
  // Update the stocktake in the list
  setStocktakes(prev => 
    prev.map(st => 
      st.id === data.stocktake_id 
        ? { ...st, ...data.stocktake }
        : st
    )
  );
  
  if (data.status === 'APPROVED') {
    toast.success(`Stocktake approved with ${data.adjustments_created} adjustments`);
  }
});

// Cleanup when component unmounts
return () => {
  hotelChannel.unbind_all();
  pusher.unsubscribe(`${hotelIdentifier}-stocktakes`);
};
```

---

### 📊 Stocktake Detail Page

```javascript
// Subscribe to specific stocktake channel
const stocktakeChannel = pusher.subscribe(
  `${hotelIdentifier}-stocktake-${stocktakeId}`
);

// 1. Stocktake populated with items
stocktakeChannel.bind('stocktake-populated', (data) => {
  console.log('Stocktake populated:', data);
  
  // Refresh the lines list
  fetchStocktakeLines(stocktakeId);
  
  toast.success(`${data.lines_created} items added to stocktake`);
});

// 2. Stocktake approved (locks editing)
stocktakeChannel.bind('stocktake-status-changed', (data) => {
  console.log('Stocktake approved:', data);
  
  // Update stocktake object
  setStocktake(prev => ({ ...prev, ...data.stocktake }));
  
  // Lock all inputs
  setIsEditable(false);
  
  toast.success('Stocktake has been approved and locked');
});

// 3. Line counted quantities updated
stocktakeChannel.bind('line-counted-updated', (data) => {
  console.log('Line counted updated:', data);
  
  // Update specific line in the list
  setLines(prev => 
    prev.map(line => 
      line.id === data.line_id 
        ? data.line  // Replace with updated line
        : line
    )
  );
  
  // Optional: Show who's editing
  showEditingIndicator(data.line.item_sku, data.user);
});

// 4. Movement (purchase/waste) added
stocktakeChannel.bind('line-movement-added', (data) => {
  console.log('Movement added:', data);
  
  // Update the line with new expected_qty and variance
  setLines(prev => 
    prev.map(line => 
      line.id === data.line_id 
        ? data.line  // Backend sends fully updated line
        : line
    )
  );
  
  // Show toast with movement details
  const movementType = data.movement.movement_type;
  const quantity = parseFloat(data.movement.quantity);
  toast.info(
    `${movementType}: ${quantity.toFixed(2)} added to ${data.item_sku}`
  );
});

// Cleanup when component unmounts or stocktake changes
return () => {
  stocktakeChannel.unbind_all();
  pusher.unsubscribe(`${hotelIdentifier}-stocktake-${stocktakeId}`);
};
```

---

## Complete React Hook Example

Here's a complete React hook for managing Pusher subscriptions:

```javascript
import { useEffect } from 'react';
import Pusher from 'pusher-js';
import { toast } from 'react-toastify';

export const useStocktakePusher = (
  hotelIdentifier,
  stocktakeId,
  onLineUpdated,
  onStocktakeUpdated
) => {
  useEffect(() => {
    // Initialize Pusher
    const pusher = new Pusher(process.env.REACT_APP_PUSHER_KEY, {
      cluster: process.env.REACT_APP_PUSHER_CLUSTER,
      encrypted: true
    });

    // Subscribe to stocktake channel
    const channelName = `${hotelIdentifier}-stocktake-${stocktakeId}`;
    const channel = pusher.subscribe(channelName);
    
    console.log(`📡 Subscribed to Pusher channel: ${channelName}`);

    // Bind event handlers
    channel.bind('line-counted-updated', (data) => {
      console.log('🔄 Line counted updated:', data);
      onLineUpdated(data.line);
      toast.info(`${data.item_sku} updated`);
    });

    channel.bind('line-movement-added', (data) => {
      console.log('📦 Movement added:', data);
      onLineUpdated(data.line);
      
      const type = data.movement.movement_type;
      const qty = parseFloat(data.movement.quantity).toFixed(2);
      toast.info(`${type}: ${qty} added to ${data.item_sku}`);
    });

    channel.bind('stocktake-status-changed', (data) => {
      console.log('✅ Stocktake approved:', data);
      onStocktakeUpdated(data.stocktake);
      
      if (data.status === 'APPROVED') {
        toast.success('Stocktake approved and locked');
      }
    });

    channel.bind('stocktake-populated', (data) => {
      console.log('📋 Stocktake populated:', data);
      toast.success(`${data.lines_created} items loaded`);
      // Trigger full refresh
      window.location.reload();
    });

    // Cleanup
    return () => {
      console.log(`📡 Unsubscribing from: ${channelName}`);
      channel.unbind_all();
      pusher.unsubscribe(channelName);
      pusher.disconnect();
    };
  }, [hotelIdentifier, stocktakeId, onLineUpdated, onStocktakeUpdated]);
};

// Usage in component:
function StocktakeDetailPage({ hotelIdentifier, stocktakeId }) {
  const [lines, setLines] = useState([]);
  const [stocktake, setStocktake] = useState(null);

  const handleLineUpdated = (updatedLine) => {
    setLines(prev => 
      prev.map(line => 
        line.id === updatedLine.id ? updatedLine : line
      )
    );
  };

  const handleStocktakeUpdated = (updatedStocktake) => {
    setStocktake(updatedStocktake);
  };

  useStocktakePusher(
    hotelIdentifier,
    stocktakeId,
    handleLineUpdated,
    handleStocktakeUpdated
  );

  // Rest of component...
}
```

---

## Event Data Structures

### Event: `stocktake-created`
```json
{
  "id": 6,
  "period_start": "2025-12-01",
  "period_end": "2025-12-31",
  "status": "DRAFT",
  "hotel": 1,
  "line_count": 0
}
```

### Event: `stocktake-deleted`
```json
{
  "stocktake_id": 6
}
```

### Event: `stocktake-status-changed`
```json
{
  "stocktake_id": 5,
  "status": "APPROVED",
  "adjustments_created": 187,
  "stocktake": {
    "id": 5,
    "period_start": "2025-10-01",
    "period_end": "2025-10-31",
    "status": "APPROVED",
    "is_locked": true,
    "line_count": 254
  }
}
```

### Event: `stocktake-populated`
```json
{
  "stocktake_id": 6,
  "lines_created": 254,
  "message": "Created 254 stocktake lines"
}
```

### Event: `line-counted-updated`
```json
{
  "line_id": 1709,
  "item_sku": "D0030",
  "line": {
    "id": 1709,
    "item_sku": "D0030",
    "item_name": "Guinness Keg",
    "counted_full_units": "2.00",
    "counted_partial_units": "45.50",
    "counted_qty": "221.5000",
    "expected_qty": "259.0000",
    "variance_qty": "-37.5000",
    "variance_value": "-93.75"
  }
}
```

### Event: `line-movement-added`
```json
{
  "line_id": 1709,
  "item_sku": "D0030",
  "movement": {
    "id": 5678,
    "movement_type": "PURCHASE",
    "quantity": "88.0000",
    "timestamp": "2025-11-09T14:30:00Z"
  },
  "line": {
    "id": 1709,
    "item_sku": "D0030",
    "purchases": "264.0000",
    "expected_qty": "347.0000",
    "variance_qty": "-125.5000"
  }
}
```

---

## Best Practices

### 1. **Always Unsubscribe on Cleanup**
```javascript
useEffect(() => {
  const channel = pusher.subscribe(`${hotelIdentifier}-stocktake-${stocktakeId}`);
  
  // ... bind events
  
  return () => {
    channel.unbind_all();
    pusher.unsubscribe(`${hotelIdentifier}-stocktake-${stocktakeId}`);
  };
}, [stocktakeId]);
```

### 2. **Optimistic Updates + Pusher Sync**
```javascript
const updateCountedQty = async (lineId, fullUnits, partialUnits) => {
  // 1. Optimistic update (immediate UI feedback)
  setLines(prev => 
    prev.map(line => 
      line.id === lineId 
        ? { ...line, counted_full_units: fullUnits, counted_partial_units: partialUnits }
        : line
    )
  );
  
  // 2. Send to backend
  const response = await patchStocktakeLine(lineId, { 
    counted_full_units: fullUnits,
    counted_partial_units: partialUnits
  });
  
  // 3. Replace with backend's authoritative data (from HTTP response)
  setLines(prev => 
    prev.map(line => line.id === lineId ? response.data : line)
  );
  
  // 4. Pusher will broadcast to OTHER users (not you)
  // Your update comes from HTTP response, others get Pusher event
};
```

### 3. **Debounce Rapid Updates**
```javascript
import { debounce } from 'lodash';

const debouncedUpdate = debounce(async (lineId, value) => {
  await updateCountedQty(lineId, value);
}, 500); // Wait 500ms after user stops typing

<input 
  value={partialUnits}
  onChange={(e) => {
    setPartialUnits(e.target.value); // Immediate local update
    debouncedUpdate(lineId, e.target.value); // Debounced API call
  }}
/>
```

### 4. **Show "Who's Editing" Indicators**
```javascript
stocktakeChannel.bind('line-counted-updated', (data) => {
  // Update the line data
  updateLine(data.line);
  
  // Show editing indicator (optional)
  if (data.user && data.user.id !== currentUserId) {
    showEditingIndicator(data.line_id, data.user.name);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
      hideEditingIndicator(data.line_id);
    }, 3000);
  }
});
```

### 5. **Handle Connection State**
```javascript
pusher.connection.bind('connected', () => {
  console.log('✅ Pusher connected');
  setConnectionStatus('connected');
});

pusher.connection.bind('disconnected', () => {
  console.log('❌ Pusher disconnected');
  setConnectionStatus('disconnected');
  toast.error('Real-time updates disconnected');
});

pusher.connection.bind('error', (err) => {
  console.error('❌ Pusher error:', err);
  toast.error('Real-time connection error');
});
```

---

## Testing Pusher Events

### Test in Browser Console

```javascript
// Subscribe to channel
const channel = pusher.subscribe('hotel-killarney-stocktake-5');

// Listen to all events
channel.bind_global((event, data) => {
  console.log(`Event: ${event}`, data);
});

// Test specific event
channel.bind('line-counted-updated', (data) => {
  console.log('Line updated:', data);
});
```

### Test with Backend API Call

```bash
# Update a line (should trigger Pusher event)
curl -X PATCH \
  https://hotel-porter-d25ad83b12cf.herokuapp.com/api/stock_tracker/hotel-killarney/stocktake-lines/1709/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "counted_full_units": 2,
    "counted_partial_units": 50.0
  }'
```

---

## Troubleshooting

### Issue: Not receiving events

**Check:**
1. Correct channel name format: `${hotelIdentifier}-stocktake-${stocktakeId}`
2. Pusher credentials are correct in `.env`
3. Channel is subscribed before events are triggered
4. Backend is successfully broadcasting (check server logs)

```javascript
// Debug channel subscription
const channel = pusher.subscribe('hotel-killarney-stocktake-5');
channel.bind('pusher:subscription_succeeded', () => {
  console.log('✅ Successfully subscribed to channel');
});
```

### Issue: Duplicate updates

**Solution:** Don't update from both HTTP response AND Pusher event for the same user action.

```javascript
// ❌ WRONG - double update
const updateLine = async (lineId, data) => {
  const response = await api.patch(`/lines/${lineId}/`, data);
  setLine(response.data); // Update 1
  
  // Pusher event also triggers setLine() - Update 2 (duplicate!)
};

// ✅ CORRECT - only use HTTP response for your own actions
const updateLine = async (lineId, data) => {
  const response = await api.patch(`/lines/${lineId}/`, data);
  setLine(response.data); // Your update comes from HTTP
  
  // Pusher events only update OTHER users' UIs
};
```

---

## Summary Checklist

✅ Install `pusher-js` package  
✅ Subscribe to correct channel names  
✅ Bind event handlers for all relevant events  
✅ Update state when events received  
✅ Show toast notifications for user feedback  
✅ Unsubscribe on component unmount  
✅ Handle optimistic updates correctly  
✅ Debounce rapid input changes  
✅ Test connection status  
✅ Handle errors gracefully  

---

## Next Steps

1. **Implement in Stocktakes List Page** - Handle stocktake creation/deletion/status changes
2. **Implement in Stocktake Detail Page** - Handle line updates and movements
3. **Add Toast Notifications** - User feedback for all events
4. **Test Multi-User Scenarios** - Open in two browsers, verify sync works
5. **Add Connection Status Indicator** - Show users if real-time is working

Need help? Check:
- Backend Pusher utils: `stock_tracker/pusher_utils.py`
- Backend views: `stock_tracker/views.py` (StocktakeViewSet, StocktakeLineViewSet)
- Pusher docs: https://pusher.com/docs/channels/getting_started/javascript/
