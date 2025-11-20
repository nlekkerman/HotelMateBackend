# Voice Recognition for Stocktake - Phase One

## Overview

Voice recognition system for hands-free stocktake counting using OpenAI Whisper for speech-to-text and regex-based command parsing. Returns preview JSON only - frontend handles item matching and database updates.

## Architecture

```
voice_recognition/
├── __init__.py           # Module initialization
├── apps.py               # Django app configuration
├── transcription.py      # OpenAI Whisper API integration
├── command_parser.py     # Regex-based command parsing
└── views.py              # VoiceCommandView API endpoint
```

## Endpoint

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

## Voice Commands

### Supported Actions

- **Count**: count, counted, counting, total, have, got, stock
- **Purchase**: purchase, purchased, buy, bought, received, delivery, delivered
- **Waste**: waste, wasted, broken, spoiled, spilled, breakage, damaged

### Examples

| Voice Command | Parsed Result |
|--------------|---------------|
| "count guinness 5.5" | `{action: 'count', item_identifier: 'guinness', value: 5.5}` |
| "purchase jack daniels 2 bottles" | `{action: 'purchase', item_identifier: 'jack daniels', value: 2}` |
| "count heineken 3 cases 6 bottles" | `{action: 'count', item_identifier: 'heineken', full_units: 3, partial_units: 6}` |
| "waste budweiser one point five" | `{action: 'waste', item_identifier: 'budweiser', value: 1.5}` |

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

### Workflow

1. User clicks mic → records audio
2. Frontend sends audio blob + stocktake_id to voice endpoint
3. Backend returns parsed command (preview only)
4. Frontend shows confirmation modal with parsed data
5. User confirms → frontend calls existing update API
6. Pusher broadcasts update to all clients

### Frontend Responsibilities

- Audio recording and blob creation
- Item matching (SKU or fuzzy name search)
- Validation and confirmation modal
- Calling existing stocktake line update API
- Handling Pusher events for real-time updates

### Backend Responsibilities

- Audio transcription (Whisper)
- Command parsing (regex)
- Validation (auth, stocktake access, lock check)
- Return preview JSON only
- **Does NOT** update database directly

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

### Transcription Accuracy Issues

1. Check audio quality (background noise)
2. Speak clearly and slowly
3. Use product names as they appear in system
4. Mention SKU codes when possible

### OpenAI API Errors

1. Verify `OPENAI_API_KEY` is set in environment
2. Check API key has credits/quota available
3. Ensure `openai>=1.0.0` is installed
4. Check network connectivity to OpenAI API

### Parse Failures

1. Check logs for transcription text
2. Verify action keywords are present
3. Ensure numeric values are spoken clearly
4. Review regex patterns in `command_parser.py`

## Support

For issues or questions:
1. Check server logs for detailed error messages
2. Review transcription output to verify accuracy
3. Test with clear voice commands first
4. Verify OpenAI API is responding correctly
