# Backend Voice Command API - Frontend Integration Guide

**Last Updated:** November 21, 2025

## Overview

The backend voice command system has been refactored into a **modular pipeline** that provides richer data for the frontend. The API remains backward compatible, but now returns additional fields for improved UX.

---

## What Changed (Backend)

### New Modules

1. **`transcription.py`** (refactored)
   - Saves uploaded audio to temp files for OpenAI compatibility
   - Returns plain text transcription
   - Raises `TranscriptionError` on failures

2. **`brand_synonyms.py`** (NEW)
   - Master dictionary of brand, packaging, modifier, and quantity synonyms
   - Used by fuzzy matcher to handle STT mistakes (e.g., "kors" → "coors")

3. **`fuzzy_matcher.py`** (NEW)
   - Uses `rapidfuzz` for intelligent item matching
   - Scores items based on SKU + name + package type (draught vs bottle)
   - Returns confidence score (0.0-1.0)

4. **`llm_reasoner.py`** (NEW, OPTIONAL)
   - Uses GPT-4o-mini to repair ambiguous transcriptions
   - Disambiguates between similar item names
   - Only runs if `VOICE_COMMAND_USE_LLM=True` in settings

5. **`voice_command_service.py`** (NEW)
   - Orchestrates the full pipeline:
     - Transcribe → Parse → Interpret units → Fuzzy match → (Optional) LLM repair
   - Returns structured output with all intermediate steps

6. **`views_voice.py`** (NEW)
   - Main API endpoints built on the new service
   - Returns enriched payloads with match confidence and unit details

---

## API Response Changes

### 1. `/api/stock_tracker/<hotel>/stocktake-lines/voice-command/` (Preview)

**Before:**
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

**Now (NEW FIELDS):**
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
  "stocktake_id": 123,
  "raw_transcription": "count guinness three kegs two point five pints",
  "unit_details": {
    "full_units": 3,
    "partial_units": 2.5,
    "total_value": 5.5,
    "pattern": "full_and_partial",
    "approximation": false
  },
  "match": {
    "item_id": 456,
    "sku": "GUIN-KEG",
    "name": "Guinness Draught Keg",
    "confidence": 0.92,
    "source": "fuzzy"
  }
}
```

**New Fields Explained:**

- **`raw_transcription`**: Original STT output before any LLM cleaning
- **`unit_details`**: Parsed unit information
  - `full_units`: Main containers (kegs, cases, bottles)
  - `partial_units`: Loose units (pints, bottles)
  - `total_value`: Combined quantity
  - `pattern`: How units were interpreted ("full_and_partial", "and_a_half", "single_value", etc.)
  - `approximation`: Boolean flag if user said "about", "roughly", etc.
- **`match`**: Fuzzy-matched item (null if not found)
  - `item_id`: Database ID for quick lookup
  - `sku`: Stock item SKU
  - `name`: Stock item name
  - `confidence`: Match score 0.0-1.0 (threshold: 0.55 default)
  - `source`: "fuzzy" or "llm" (if LLM fallback was used)

---

## Frontend Recommendations

### 1. **Display Match Confidence**
Show the matched item name and confidence score in the preview modal:

```jsx
{match && (
  <div className="match-preview">
    <span className="item-name">{match.name}</span>
    <span className="confidence">
      {(match.confidence * 100).toFixed(0)}% match
    </span>
  </div>
)}
```

### 2. **Handle Low Confidence**
If `match.confidence < 0.7`, show a warning:

```jsx
{match && match.confidence < 0.7 && (
  <Alert type="warning">
    Low confidence match. Please verify this is the correct item.
  </Alert>
)}
```

### 3. **Show Unit Breakdown**
Display `unit_details` when available:

```jsx
{unit_details && unit_details.pattern === "full_and_partial" && (
  <div className="unit-breakdown">
    {unit_details.full_units} cases + {unit_details.partial_units} bottles
    = {unit_details.total_value} total
  </div>
)}
```

### 4. **Approximation Flag**
If `unit_details.approximation === true`, show an indicator:

```jsx
{unit_details?.approximation && (
  <Badge variant="info">Approximate</Badge>
)}
```

### 5. **Pre-fill Item Selection**
If `match` exists, automatically select it in your item dropdown/search:

```jsx
const [selectedItem, setSelectedItem] = useState(null);

// After receiving voice command response:
if (response.match) {
  setSelectedItem({
    id: response.match.item_id,
    name: response.match.name,
    sku: response.match.sku,
  });
}
```

### 6. **Show Raw Transcription**
For debugging or user verification:

```jsx
<details>
  <summary>Debug Info</summary>
  <div>
    <strong>Raw:</strong> {raw_transcription}
    <br />
    <strong>Cleaned:</strong> {command.transcription}
  </div>
</details>
```

---

## Configuration (Backend Settings)

Add to your Django `settings.py`:

```python
# Voice Command Settings
VOICE_COMMAND_MIN_SCORE = 0.55  # Fuzzy match threshold (0.0-1.0)
VOICE_COMMAND_USE_LLM = False   # Enable GPT-4o fallback (requires OpenAI credits)
VOICE_COMMAND_DOMAIN_HINT = "Irish pub stocktake"  # Optional context for LLM
```

---

## Error Handling

The API returns more specific errors:

```json
{
  "success": false,
  "error": "No matching item found for 'unknown product'. Please try again or add the item manually."
}
```

**Frontend should:**
- Show the error message to the user
- Offer a manual item selection fallback
- Log to analytics for improving synonym dictionary

---

## Backward Compatibility

The API is **fully backward compatible**:
- Old fields (`action`, `item_identifier`, `value`, `transcription`) still present
- New fields are **additions only** (no breaking changes)
- Existing frontend code will continue to work
- You can adopt new fields incrementally

---

## Testing Checklist

1. **Basic Count**: "count guinness 5.5" → Verify `match` and `unit_details`
2. **Full + Partial**: "count budweiser 7 cases 7 bottles" → Check breakdown
3. **Approximation**: "count heineken about 3" → Verify `approximation: true`
4. **Misspelling**: "count kors battle" → Should match "Coors Bottle"
5. **Low Confidence**: "count xyz" → Show warning if confidence < 0.7
6. **No Match**: "count nonexistent" → Verify `match: null`

---

## Support

For backend questions or synonym additions:
- Check `voice_recognition/brand_synonyms.py` for existing mappings
- Add new brands/variants to `BRAND_SYNONYMS` dictionary
- Adjust `VOICE_COMMAND_MIN_SCORE` if too many false positives/negatives

---

## Summary for Frontend Team

**Action Required:**
1. Update preview modal to display `match.name` and `match.confidence`
2. Pre-fill item selection when `match` is present
3. Show unit breakdown (`full_units` + `partial_units`) for clarity
4. Add low-confidence warning when `confidence < 0.7`

**Optional Enhancements:**
- Display `approximation` badge when user says "about", "roughly"
- Show raw vs cleaned transcription in debug panel
- Track confidence scores in analytics to tune threshold

**No Breaking Changes:**
- Existing code continues to work
- All new fields are optional additions
