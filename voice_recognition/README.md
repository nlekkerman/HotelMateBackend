# Voice Recognition for Stocktake - Phase One

## Overview

Voice recognition system for hands-free stocktake counting using OpenAI Whisper for speech-to-text and regex-based command parsing. Two-step workflow: preview command first, then confirm to update database.

## Architecture

```
voice_recognition/
├── __init__.py           # Module initialization
├── apps.py               # Django app configuration
├── transcription.py      # OpenAI Whisper API integration
├── command_parser.py     # Regex-based command parsing
└── views.py              # VoiceCommandView + VoiceCommandConfirmView
```

## Workflow

1. **Record & Parse** → Voice command is transcribed and parsed (preview only)
2. **User Confirms** → Frontend shows preview, user reviews and confirms
3. **Update Database** → Confirmed command updates the stocktake line

## Endpoints

### 1. Parse Voice Command (Preview)

**POST** `/api/stock_tracker/<hotel_identifier>/stocktake-lines/voice-command/`

### Request

- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `audio` (File): Audio blob (WebM/Opus, MP4, or OGG) - max 10MB
  - `stocktake_id` (string): Stocktake context for validation

### Response (Success)

```json
{
  "success": true,
  "command": {
    "action": "count",
    "item_identifier": "guinness",
    "value": 5.5,
    "full_units": 3,
    "partial_units": 2.5,
    "transcription": "count guinness three kegs two point five pints"
  },
  "stocktake_id": 123
}
```

### Response (Error)

```json
{
  "success": false,
  "error": "No action keyword found in 'something five'",
  "transcription": "something five"
}
```

---

### 2. Confirm Voice Command (Update Database)

**POST** `/api/stock_tracker/<hotel_identifier>/stocktake-lines/voice-command/confirm/`

After user reviews and confirms the preview, this endpoint applies the command to the database.

#### Request

```json
{
  "stocktake_id": 123,
  "command": {
    "action": "count",
    "item_identifier": "guinness",
    "value": 5.5,
    "full_units": 3,
    "partial_units": 2.5
  }
}
```

#### Response (Success)

```json
{
  "success": true,
  "line": {
    "id": 456,
    "item": {...},
    "counted_full_units": 3,
    "counted_partial_units": 2.5,
    "counted_qty": 5.5,
    ...
  },
  "message": "Counted 5.5 units of Guinness",
  "item_name": "Guinness",
  "item_sku": "GUIN-KEG"
}
```

#### Response (Error)

```json
{
  "success": false,
  "error": "Stock item not found: unknown product"
}
```

#### Item Matching

The endpoint searches for stock items using fuzzy matching:
- Exact match on SKU (case-insensitive)
- Exact match on name (case-insensitive)
- Contains match on SKU
- Contains match on name

Example: "budweiser" matches "Budweiser Bottle", "BUD-001", "budweiser draught", etc.

#### Actions

| Action | Database Update |
|--------|-----------------|
| `count` | Sets `counted_full_units` and `counted_partial_units` |
| `purchase` | Adds to `purchases` field |
| `waste` | Adds to `waste` field |

## Voice Commands

### Supported Actions

- **Count**: count, counted, counting, total, have, got, stock, there are, there is, we have, i see
- **Purchase**: purchase, purchased, buy, bought, received, delivery, delivered, add, incoming
- **Waste**: waste, wasted, broken, spoiled, spilled, breakage, damaged, minus, subtract

### Examples

| Voice Command | Parsed Result |
|--------------|---------------|
| "count guinness 5.5" | `{action: 'count', item_identifier: 'guinness', value: 5.5}` |
| "count budweiser 7 cases 7 bottles" | `{action: 'count', item_identifier: 'budweiser', full_units: 7, partial_units: 7}` |
| "I have coca cola 12" | `{action: 'count', item_identifier: 'coca cola', value: 12}` |
| "purchase jack daniels 2 bottles" | `{action: 'purchase', item_identifier: 'jack daniels', value: 2}` |
| "count heineken 3 cases 6 bottles" | `{action: 'count', item_identifier: 'heineken', full_units: 3, partial_units: 6}` |
| "waste budweiser one point five" | `{action: 'waste', item_identifier: 'budweiser', value: 1.5}` |

### Important Notes

✅ **Action keyword is REQUIRED** - You must say "count", "purchase", "waste", etc.  
✅ **Natural language works** - "I have Budweiser 7" or "There are 7 Budweiser"  
✅ **Units are optional** - "7 cases 7 bottles" or just "7"  
❌ **Don't start with product name** - "Budweiser 7 cases" won't work without action word

### Number Word Conversion

The parser automatically converts number words to digits:

- "five point five" → 5.5
- "twenty three" → 23
- "three cases" → "3 cases"

## Setup

### 1. Install Dependencies

```bash
pip install openai>=1.0.0
```

### 2. Environment Variables

Add to `.env`:

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Django Settings

Add to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps
    'voice_recognition',
]
```

### 4. URL Configuration

Voice endpoint is already registered in `stock_tracker/urls.py`:

```python
path(
    '<str:hotel_identifier>/stocktake-lines/voice-command/',
    VoiceCommandView.as_view(),
    name='voice-command'
)
```

## Real-Time Updates (Pusher)

When frontend applies voice command updates to stocktake lines, Pusher broadcasting happens automatically through existing `StocktakeLineViewSet.update()` method:

```python
# In StocktakeLineViewSet.update()
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

**Channel**: `{hotel_identifier}-stocktake-{stocktake_id}`  
**Event**: `line-counted-updated`

All connected clients viewing the stocktake receive real-time updates.

## Security & Validation

### Audio File Validation

- **Max size**: 10MB
- **Formats**: WebM/Opus, MP4, OGG
- **Validation**: File size checked before processing

### Access Control

- **Authentication**: `IsAuthenticated` required
- **Hotel access**: Verified via slug or subdomain
- **Stocktake access**: Must exist and belong to hotel
- **Lock check**: Cannot process voice commands on approved stocktakes

## Error Handling

### Common Errors

| Error | HTTP Status | Cause |
|-------|-------------|-------|
| No audio file provided | 400 | Missing `audio` field |
| No stocktake_id provided | 400 | Missing `stocktake_id` field |
| Audio file too large | 400 | File exceeds 10MB limit |
| Stocktake is locked | 400 | Stocktake status is APPROVED |
| Transcription failed | 500 | OpenAI API error or network issue |
| No action keyword found | 400 | Unclear voice command (no count/purchase/waste) |
| No numeric value found | 400 | Missing quantity in command |
| No item identifier found | 400 | Missing product name/SKU |

## Testing

### Manual Test with cURL

```bash
curl -X POST \
  http://localhost:8000/api/stock_tracker/hotel-killarney/stocktake-lines/voice-command/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio=@test_voice.webm" \
  -F "stocktake_id=123"
```

### Expected Response

```json
{
  "success": true,
  "command": {
    "action": "count",
    "item_identifier": "guinness",
    "value": 5.5,
    "transcription": "count guinness five point five"
  },
  "stocktake_id": 123
}
```

## Frontend Integration

### Complete Workflow

```
1. User speaks into microphone
   ↓
2. Frontend sends audio → /voice-command/
   ↓
3. Backend returns parsed preview
   ↓
4. Frontend shows confirmation modal:
   "Count Budweiser: 7 cases, 7 bottles?"
   [Cancel] [Confirm]
   ↓
5. User clicks Confirm
   ↓
6. Frontend sends command → /voice-command/confirm/
   ↓
7. Backend updates stocktake line
   ↓
8. Pusher broadcasts update to all clients
```

### Frontend Code Example

```typescript
// Step 1: Record and parse
const parseVoiceCommand = async (audioBlob: Blob, stocktakeId: number) => {
  const formData = new FormData();
  formData.append('audio', audioBlob);
  formData.append('stocktake_id', stocktakeId.toString());
  
  const response = await fetch(
    `/api/stock_tracker/${hotelId}/stocktake-lines/voice-command/`,
    {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    }
  );
  
  return await response.json();
};

// Step 2: Show confirmation modal
const showConfirmation = (command: VoiceCommand) => {
  // Display: "Count Budweiser: 7 units"
  // User clicks Confirm → call confirmVoiceCommand()
};

// Step 3: Confirm and update database
const confirmVoiceCommand = async (stocktakeId: number, command: VoiceCommand) => {
  const response = await fetch(
    `/api/stock_tracker/${hotelId}/stocktake-lines/voice-command/confirm/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        stocktake_id: stocktakeId,
        command: command
      })
    }
  );
  
  const result = await response.json();
  
  if (result.success) {
    // Show success message
    toast.success(result.message);
    // Line is updated, Pusher will broadcast to all clients
  } else {
    // Show error
    toast.error(result.error);
  }
};
```

### Frontend Responsibilities

- Audio recording and blob creation
- Display preview confirmation modal
- Handle user confirmation/cancellation
- Call confirm endpoint when user approves
- Handle success/error responses
- Listen for Pusher events for real-time updates

### Backend Responsibilities

- Audio transcription (Whisper)
- Command parsing (regex)
- Validation (auth, stocktake access, lock check)
- Item matching (fuzzy search)
- Database updates (on confirm endpoint)
- Pusher broadcasting (automatic via serializer)

## Logging

All voice commands are logged with:

- User identifier
- Hotel identifier
- Stocktake ID
- Audio file size
- Transcription result
- Parse success/failure
- Error details

Example log output:

```
INFO: 🎤 Voice command from john@hotel.com | Hotel: killarney | Stocktake: 123 | Audio: 45678 bytes
INFO: 🎤 Transcribed: 'count guinness five point five'
INFO: 🔍 Parsing: 'count guinness 5.5' (from 'count guinness five point five')
INFO: ✓ Action: count (matched: count)
INFO: ✓ Parsed single value: 5.5
INFO: ✓ Item identifier: 'guinness'
INFO: ✅ Voice command parsed successfully
```

## Performance

- **Transcription**: ~1-3 seconds (depends on audio length and OpenAI API latency)
- **Parsing**: <10ms (regex-based, local)
- **Total response time**: ~1-3 seconds

## Future Enhancements (Not in Phase One)

- [ ] Voice command logging model for analytics
- [ ] Concurrent edit conflict detection
- [ ] Support for more natural language variations
- [ ] Multi-language support
- [ ] Offline transcription with local Whisper
- [ ] Voice confirmation responses
- [ ] Batch voice commands

## Troubleshooting

### "No action keyword found"

**Problem**: Voice command returns error: "No action keyword found in 'Budweiser 7 cases'"

**Solution**: Always start with an action word:
- ✅ "Count Budweiser 7 cases"
- ✅ "I have 7 cases of Budweiser"
- ❌ "Budweiser 7 cases" (missing action)

### "Stock item not found"

**Problem**: Confirm endpoint returns "Stock item not found: budwiser"

**Solution**: 
1. Check spelling in voice command
2. Verify item exists in hotel's stock items
3. Try using SKU code instead of name
4. Check item is marked as `is_active=True`

### Transcription Accuracy Issues

1. Check audio quality (background noise)
2. Speak clearly and slowly
3. Use product names as they appear in system
4. Mention SKU codes when possible
5. Avoid background music or conversations

### OpenAI API Errors

1. Verify `OPENAI_API_KEY` is set in environment
2. Check API key has credits/quota available
3. Ensure `openai>=1.0.0` is installed
4. Check network connectivity to OpenAI API

### Parse Failures

1. Check logs for transcription text
2. Verify action keywords are present (count, purchase, waste)
3. Ensure numeric values are spoken clearly
4. Review regex patterns in `command_parser.py`

### Item Identifier Extraction Issues

**Problem**: Item name has extra words like "budweiser bottle cas bo"

**Solution**: This was fixed in latest version. Parser now:
- Removes unit words (cases, bottles, kegs, etc.)
- Removes filler words (i, we, the, a, etc.)
- Cleans up whitespace properly

## Support

For issues or questions:
1. Check server logs for detailed error messages
2. Review transcription output to verify accuracy
3. Test with clear voice commands first
4. Verify OpenAI API is responding correctly
