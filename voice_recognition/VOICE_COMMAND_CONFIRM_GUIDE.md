# Voice Command Confirmation Flow

## Overview

Voice recognition now uses a **two-step workflow**:
1. **Parse & Preview** - Voice command is transcribed and parsed (NO database changes)
2. **User Confirms** - Frontend shows preview, user confirms, then database is updated

## Why Two Steps?

- **User Control**: Review what was heard before applying changes
- **Error Prevention**: Catch transcription mistakes before they affect data
- **Transparency**: See exactly what will be updated

## Backend Endpoints

### 1. Parse Voice Command (Preview Only)

**POST** `/api/stock_tracker/{hotel}/stocktake-lines/voice-command/`

**Request:**
- `audio` (File): Audio blob (WebM/Opus, MP4, OGG)
- `stocktake_id` (string): Stocktake ID

**Response:**
```json
{
  "success": true,
  "command": {
    "action": "count",
    "item_identifier": "budweiser",
    "value": 7,
    "full_units": 7,
    "partial_units": 0,
    "transcription": "count budweiser 7 cases"
  },
  "stocktake_id": 123
}
```

**What it does:**
- ✅ Transcribes audio using OpenAI Whisper
- ✅ Parses command into structured data
- ❌ Does NOT update database
- ❌ Does NOT match stock items

---

### 2. Confirm Voice Command (Update Database)

**POST** `/api/stock_tracker/{hotel}/stocktake-lines/voice-command/confirm/`

**Request:**
```json
{
  "stocktake_id": 123,
  "command": {
    "action": "count",
    "item_identifier": "budweiser",
    "value": 7,
    "full_units": 7,
    "partial_units": 0
  }
}
```

**Response:**
```json
{
  "success": true,
  "line": {
    "id": 456,
    "item": {
      "id": 789,
      "sku": "BUD-001",
      "name": "Budweiser"
    },
    "counted_full_units": 7,
    "counted_partial_units": 0,
    "counted_qty": 7,
    "opening_qty": 5,
    "expected_qty": 8,
    "variance_qty": -1
  },
  "message": "Counted 7 units of Budweiser",
  "item_name": "Budweiser",
  "item_sku": "BUD-001"
}
```

**What it does:**
- ✅ Finds stock item using fuzzy matching
- ✅ Creates or updates StocktakeLine
- ✅ Updates counted_full_units/counted_partial_units
- ✅ Triggers Pusher broadcast to all clients
- ✅ Returns updated line data

---

## Item Matching Logic

The confirm endpoint searches for stock items in this order:

1. **Exact SKU match** (case-insensitive)
2. **Exact name match** (case-insensitive)
3. **SKU contains** (case-insensitive)
4. **Name contains** (case-insensitive)

**Examples:**
- "budweiser" → matches "Budweiser", "BUD-001", "Budweiser Bottle"
- "jack" → matches "Jack Daniels", "JACK-750ML"
- "guin" → matches "Guinness Draught", "GUIN-KEG"

**Only active items** (`is_active=True`) are matched.

---

## Action Types

### COUNT
Updates `counted_full_units` and `counted_partial_units`:

```json
{
  "action": "count",
  "value": 7,
  "full_units": 7,
  "partial_units": 0
}
```

Result: `line.counted_full_units = 7`, `line.counted_partial_units = 0`

---

### PURCHASE
Adds to `purchases` field:

```json
{
  "action": "purchase",
  "value": 2
}
```

Result: `line.purchases += 2`

---

### WASTE
Adds to `waste` field:

```json
{
  "action": "waste",
  "value": 1.5
}
```

Result: `line.waste += 1.5`

---

## Frontend Integration

### Complete Workflow

```typescript
// Step 1: Record audio
const audioBlob = await recordAudio();

// Step 2: Parse voice command (preview)
const parseResult = await fetch(
  `/api/stock_tracker/${hotelId}/stocktake-lines/voice-command/`,
  {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: createFormData(audioBlob, stocktakeId)
  }
).then(r => r.json());

if (!parseResult.success) {
  // Show error: "Could not understand command"
  toast.error(parseResult.error);
  return;
}

// Step 3: Show confirmation modal
showConfirmationModal({
  action: parseResult.command.action,
  item: parseResult.command.item_identifier,
  value: parseResult.command.value,
  transcription: parseResult.command.transcription,
  onConfirm: async () => {
    // Step 4: User confirmed - update database
    const confirmResult = await fetch(
      `/api/stock_tracker/${hotelId}/stocktake-lines/voice-command/confirm/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          stocktake_id: stocktakeId,
          command: parseResult.command
        })
      }
    ).then(r => r.json());
    
    if (confirmResult.success) {
      toast.success(confirmResult.message);
      // Line is updated, Pusher will broadcast to all clients
    } else {
      toast.error(confirmResult.error);
    }
  },
  onCancel: () => {
    // User cancelled - do nothing
    toast.info('Voice command cancelled');
  }
});
```

---

## Confirmation Modal Example

```tsx
<Modal open={showConfirm} onClose={onCancel}>
  <ModalContent>
    <h2>Confirm Voice Command</h2>
    
    <div>
      <strong>You said:</strong>
      <p>"{transcription}"</p>
    </div>
    
    <div>
      <strong>Parsed as:</strong>
      <p>
        <span className="action">{action.toUpperCase()}</span>
        <span className="item">{itemName}</span>
        <span className="value">{value} units</span>
      </p>
    </div>
    
    {fullUnits && partialUnits && (
      <div>
        <strong>Details:</strong>
        <p>{fullUnits} cases + {partialUnits} bottles</p>
      </div>
    )}
    
    <div className="actions">
      <Button variant="secondary" onClick={onCancel}>
        Cancel
      </Button>
      <Button variant="primary" onClick={onConfirm}>
        Confirm
      </Button>
    </div>
  </ModalContent>
</Modal>
```

---

## Error Handling

### Parse Endpoint Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "No action keyword found" | Missing count/purchase/waste | Say "count", "I have", or similar |
| "No numeric value found" | Missing quantity | Clearly state the number |
| "No item identifier found" | Missing product name | Say the product name |
| "Transcription failed" | Audio quality or API issue | Record again or check OpenAI API |

### Confirm Endpoint Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Stock item not found" | Item doesn't exist or is inactive | Check spelling or use SKU |
| "Stocktake is locked" | Stocktake is approved | Cannot edit approved stocktakes |
| "Missing stocktake_id or command" | Invalid request | Check request format |

---

## Voice Command Requirements

### ✅ Required Elements

1. **Action keyword**: count, purchase, waste, have, got, etc.
2. **Product identifier**: Name or SKU
3. **Quantity**: Number (whole or decimal)

### ✅ Correct Examples

- "Count Budweiser 7 cases 7 bottles"
- "I have 12 Guinness"
- "Purchase Jack Daniels 2 bottles"
- "Waste Corona 1.5"
- "There are 24 Heineken"

### ❌ Incorrect Examples

- "Budweiser 7 cases" (missing action)
- "Count Budweiser" (missing quantity)
- "7 cases" (missing item and action)

---

## Security & Validation

### Parse Endpoint
- ✅ Requires authentication
- ✅ Validates hotel access
- ✅ Validates stocktake exists and belongs to hotel
- ✅ Checks stocktake is not locked (APPROVED)
- ✅ Validates audio file size (max 10MB)

### Confirm Endpoint
- ✅ Requires authentication
- ✅ Validates hotel access
- ✅ Validates stocktake exists and belongs to hotel
- ✅ Checks stocktake is not locked (APPROVED)
- ✅ Validates item exists and is active
- ✅ Creates line if doesn't exist (with opening_qty and valuation_cost)

---

## Real-Time Updates

When a voice command is confirmed, Pusher automatically broadcasts the update:

**Channel**: `{hotel_identifier}-stocktake-{stocktake_id}`  
**Event**: `line-counted-updated`  
**Payload**:
```json
{
  "line_id": 456,
  "item_sku": "BUD-001",
  "line": {
    "id": 456,
    "counted_full_units": 7,
    "counted_partial_units": 0,
    ...
  }
}
```

All clients viewing the same stocktake receive the update in real-time.

---

## Testing

### Test Parse Endpoint

```bash
curl -X POST \
  http://localhost:8000/api/stock_tracker/killarney/stocktake-lines/voice-command/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio=@test_voice.webm" \
  -F "stocktake_id=123"
```

### Test Confirm Endpoint

```bash
curl -X POST \
  http://localhost:8000/api/stock_tracker/killarney/stocktake-lines/voice-command/confirm/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stocktake_id": 123,
    "command": {
      "action": "count",
      "item_identifier": "budweiser",
      "value": 7,
      "full_units": 7,
      "partial_units": 0
    }
  }'
```

---

## Summary

| Step | Endpoint | Database Update | User Action |
|------|----------|----------------|-------------|
| 1. Parse | `/voice-command/` | ❌ No | Speaks into mic |
| 2. Preview | - | ❌ No | Reviews parsed command |
| 3. Confirm | `/voice-command/confirm/` | ✅ Yes | Clicks "Confirm" button |
| 4. Broadcast | Pusher | ✅ Yes | Sees update in real-time |

This two-step approach ensures accuracy and gives users full control over voice-based stocktake updates.
