# Backend Implementation Guide: Voice Recognition for Stocktake

## Overview

The frontend is **fully implemented** and ready. It sends audio blobs to Django, which needs to:
1. Transcribe the audio to text
2. Parse the command (action, item, value)
3. Return structured JSON response

The frontend handles all item matching, validation, execution, and Pusher broadcasting.

---

## 📍 Required Endpoint

### URL Pattern
```python
# In your urls.py
path('stock_tracker/<str:hotel_slug>/stocktake-lines/voice-command/', 
     VoiceCommandView.as_view(), 
     name='voice-command')
```

### HTTP Method
`POST`

### Request Format
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `audio` (File): Audio blob (WebM/Opus, MP4, or OGG format)
  - `stocktake_id` (string): Stocktake context for validation

### Example Request
```python
# Frontend sends:
FormData {
  'audio': <File: voice_command.webm>,
  'stocktake_id': '123'
}
```

---

## 🎯 Response Format

### Success Response
```json
{
  "success": true,
  "command": {
    "action": "count",           // 'count', 'purchase', or 'waste'
    "item_identifier": "guinness", // Product name or SKU from transcription
    "value": 5.5,                 // Numeric quantity
    "transcription": "count guinness five point five" // Raw text for debugging
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Could not parse command from transcription",
  "transcription": "count something unknown" // Optional: for debugging
}
```

---

## 🔧 Implementation Steps

### 1. Create Voice Recognition Module (Separate Package)

```
your_django_project/
├── voice_recognition/           # NEW MODULE
│   ├── __init__.py
│   ├── transcription.py        # Audio → text
│   ├── command_parser.py       # Text → structured command
│   └── views.py                # API endpoint
└── stock_tracker/
    └── views/
        └── stocktake_views.py  # Imports voice module
```

**Why separate?** Keeps voice logic isolated from core stocktake logic.

---

### 2. Transcription Service (`transcription.py`)

#### Recommended Services:
- **OpenAI Whisper API** (best accuracy, supports accents)
- **Google Cloud Speech-to-Text** (good for continuous deployment)
- **Azure Speech Services** (good for European deployments)
- **Local Whisper** (privacy-focused, requires GPU)

#### Example with OpenAI Whisper

```python
# voice_recognition/transcription.py
import openai
from django.conf import settings

def transcribe_audio(audio_file):
    """
    Transcribe audio file to text using OpenAI Whisper
    
    Args:
        audio_file: Django UploadedFile object
        
    Returns:
        str: Transcribed text
        
    Raises:
        Exception: If transcription fails
    """
    try:
        openai.api_key = settings.OPENAI_API_KEY
        
        # Whisper expects a file-like object
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file,
            language="en",  # Can detect automatically or specify
            prompt="Stocktake voice commands: count, purchase, waste, product names"
        )
        
        transcription = response['text'].strip()
        print(f"🎤 Transcription: {transcription}")
        
        return transcription
        
    except Exception as e:
        print(f"❌ Transcription error: {str(e)}")
        raise Exception(f"Audio transcription failed: {str(e)}")
```

#### Alternative: Google Speech-to-Text

```python
from google.cloud import speech

def transcribe_audio_google(audio_file):
    """Using Google Cloud Speech-to-Text"""
    client = speech.SpeechClient()
    
    audio_content = audio_file.read()
    audio = speech.RecognitionAudio(content=audio_content)
    
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code="en-US",
        enable_automatic_punctuation=True,
        speech_contexts=[{
            "phrases": ["count", "purchase", "waste", "guinness", "budweiser", "heineken"]
        }]
    )
    
    response = client.recognize(config=config, audio=audio)
    
    if response.results:
        return response.results[0].alternatives[0].transcript
    else:
        raise Exception("No transcription results")
```

---

### 3. Command Parser (`command_parser.py`)

Parse transcribed text into structured command.

```python
# voice_recognition/command_parser.py
import re
from typing import Dict, Optional

# Action keywords (case-insensitive)
ACTION_KEYWORDS = {
    'count': ['count', 'counted', 'counting', 'total', 'have', 'got'],
    'purchase': ['purchase', 'purchased', 'buy', 'bought', 'received', 'delivery'],
    'waste': ['waste', 'wasted', 'broken', 'spoiled', 'spilled', 'breakage']
}

def parse_voice_command(transcription: str) -> Dict:
    """
    Parse transcribed text into command structure
    
    Args:
        transcription: Raw text from speech-to-text
        
    Returns:
        dict: {
            'action': str,
            'item_identifier': str,
            'value': float,
            'full_units': int (optional),
            'partial_units': float (optional)
        }
        
    Raises:
        ValueError: If command cannot be parsed
        
    Examples:
        "count guinness 5.5" → {'action': 'count', 'item_identifier': 'guinness', 'value': 5.5}
        "purchase jack daniels 2" → {'action': 'purchase', 'item_identifier': 'jack daniels', 'value': 2}
        "waste budweiser 1" → {'action': 'waste', 'item_identifier': 'budweiser', 'value': 1}
        "count heineken 3 cases 6 bottles" → {'action': 'count', 'item_identifier': 'heineken', 'full_units': 3, 'partial_units': 6}
    """
    
    text = transcription.lower().strip()
    print(f"🔍 Parsing: '{text}'")
    
    # 1. Detect action
    action = None
    for action_type, keywords in ACTION_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            action = action_type
            break
    
    if not action:
        raise ValueError(f"No action keyword found in '{transcription}'")
    
    # 2. Extract numeric value(s)
    # Pattern 1: Single value "count guinness 5.5"
    single_value_pattern = r'(\d+(?:\.\d+)?)\s*$'
    
    # Pattern 2: Full and partial "count heineken 3 cases 6 bottles"
    full_partial_pattern = r'(\d+)\s*(?:cases?|kegs?|boxes?|bottles?)?\s+(?:and\s+)?(\d+(?:\.\d+)?)\s*(?:bottles?|pints?|cans?)?'
    
    full_units = None
    partial_units = None
    value = None
    
    # Try full + partial pattern first
    full_partial_match = re.search(full_partial_pattern, text)
    if full_partial_match:
        full_units = int(full_partial_match.group(1))
        partial_units = float(full_partial_match.group(2))
        value = full_units + partial_units  # Combined for compatibility
        print(f"✅ Parsed full+partial: {full_units} full, {partial_units} partial")
    else:
        # Try single value pattern
        single_match = re.search(single_value_pattern, text)
        if single_match:
            value = float(single_match.group(1))
            print(f"✅ Parsed single value: {value}")
        else:
            raise ValueError(f"No numeric value found in '{transcription}'")
    
    # 3. Extract item identifier (everything between action and number)
    # Remove action keyword
    for keyword in ACTION_KEYWORDS[action]:
        if keyword in text:
            text = text.replace(keyword, '', 1).strip()
            break
    
    # Remove the numeric part at the end
    if full_partial_match:
        text = text[:full_partial_match.start()].strip()
    elif single_match:
        text = text[:single_match.start()].strip()
    
    item_identifier = text.strip()
    
    if not item_identifier:
        raise ValueError(f"No item identifier found in '{transcription}'")
    
    print(f"✅ Parsed command: action={action}, item={item_identifier}, value={value}")
    
    result = {
        'action': action,
        'item_identifier': item_identifier,
        'value': value,
        'transcription': transcription
    }
    
    # Add full/partial if detected
    if full_units is not None:
        result['full_units'] = full_units
        result['partial_units'] = partial_units
    
    return result
```

---

### 4. View Implementation (`views.py`)

```python
# voice_recognition/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from .transcription import transcribe_audio
from .command_parser import parse_voice_command

class VoiceCommandView(APIView):
    """
    Handle voice command transcription and parsing
    
    POST /stock_tracker/{hotel_slug}/stocktake-lines/voice-command/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, hotel_slug):
        try:
            # 1. Validate request
            audio_file = request.FILES.get('audio')
            stocktake_id = request.data.get('stocktake_id')
            
            if not audio_file:
                return Response({
                    'success': False,
                    'error': 'No audio file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not stocktake_id:
                return Response({
                    'success': False,
                    'error': 'No stocktake_id provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Optional: Validate audio file size
            max_size = 10 * 1024 * 1024  # 10MB
            if audio_file.size > max_size:
                return Response({
                    'success': False,
                    'error': f'Audio file too large (max {max_size/1024/1024}MB)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"🎤 Voice command request from {request.user.username}")
            print(f"   Hotel: {hotel_slug}")
            print(f"   Stocktake: {stocktake_id}")
            print(f"   Audio size: {audio_file.size} bytes")
            
            # 2. Transcribe audio to text
            try:
                transcription = transcribe_audio(audio_file)
            except Exception as e:
                return Response({
                    'success': False,
                    'error': f'Transcription failed: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 3. Parse command from transcription
            try:
                command = parse_voice_command(transcription)
            except ValueError as e:
                return Response({
                    'success': False,
                    'error': str(e),
                    'transcription': transcription
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 4. Return success response
            print(f"✅ Command parsed successfully: {command}")
            
            return Response({
                'success': True,
                'command': command
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## 🔐 Settings Configuration

Add to your `settings.py`:

```python
# Voice Recognition Settings
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')  # For Whisper API

# Or for Google Cloud
GOOGLE_CLOUD_PROJECT = env('GOOGLE_CLOUD_PROJECT', default='')
GOOGLE_APPLICATION_CREDENTIALS = env('GOOGLE_APPLICATION_CREDENTIALS', default='')

# Audio file limits
MAX_VOICE_COMMAND_SIZE = 10 * 1024 * 1024  # 10MB
```

---

## 📦 Required Dependencies

Add to `requirements.txt`:

```txt
# For OpenAI Whisper
openai>=1.0.0

# Or for Google Speech-to-Text
google-cloud-speech>=2.20.0

# Already have:
djangorestframework
pusher
```

---

## 🧪 Testing the Endpoint

### Manual Test with cURL

```bash
# Record a test audio file or use existing one
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
  }
}
```

---

## 🎭 Handle Full + Partial Units

Some items need separate full and partial units (e.g., "3 cases and 6 bottles").

### Enhanced Command Parser

The parser above already handles:
- **Single value**: `"count guinness 5.5"` → `value: 5.5`
- **Full + Partial**: `"count heineken 3 cases 6 bottles"` → `full_units: 3, partial_units: 6`

### Voice Command Examples

```
"count guinness 3 kegs 12 pints"
  → action: count, item: guinness, full_units: 3, partial_units: 12

"purchase budweiser 2 cases 8 bottles"
  → action: purchase, item: budweiser, full_units: 2, partial_units: 8

"waste jack daniels 1 bottle"
  → action: waste, item: jack daniels, value: 1
```

### Response Format for Full + Partial

```json
{
  "success": true,
  "command": {
    "action": "count",
    "item_identifier": "heineken",
    "value": 3.5,  // Combined for compatibility
    "full_units": 3,
    "partial_units": 0.5,
    "transcription": "count heineken three cases and six bottles"
  }
}
```

Frontend will use `full_units` and `partial_units` if present, otherwise use `value`.

---

## 🚨 Error Handling

### Common Errors

| Error | Cause | Response |
|-------|-------|----------|
| No audio file | Missing `audio` field | `400: No audio file provided` |
| Transcription failed | API error, bad audio | `500: Transcription failed` |
| No action keyword | Unclear command | `400: No action keyword found` |
| No item identifier | Missing product name | `400: No item identifier found` |
| No numeric value | Missing quantity | `400: No numeric value found` |

### Example Error Responses

```json
{
  "success": false,
  "error": "No action keyword found in 'something something five'",
  "transcription": "something something five"
}
```

---

## 🔒 Security & Permissions

### Authentication
- Use same permissions as stocktake editing
- Check user has access to hotel/stocktake

### Validation
```python
# In your view
from stock_tracker.models import Stocktake

# Verify stocktake exists and user has access
stocktake = Stocktake.objects.get(
    id=stocktake_id,
    hotel__slug=hotel_slug
)

# Check user permissions
if not request.user.has_perm('stock_tracker.change_stocktake'):
    return Response({'error': 'Permission denied'}, status=403)

# Check stocktake not locked
if stocktake.status == 'APPROVED':
    return Response({'error': 'Stocktake is locked'}, status=400)
```

---

## 📊 Logging & Analytics

Log all voice commands for debugging and analytics:

```python
# models.py
class VoiceCommandLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    stocktake = models.ForeignKey(Stocktake, on_delete=models.CASCADE)
    transcription = models.TextField()
    parsed_action = models.CharField(max_length=50, null=True)
    parsed_item = models.CharField(max_length=255, null=True)
    parsed_value = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

```python
# In view after parsing
VoiceCommandLog.objects.create(
    user=request.user,
    hotel_id=hotel.id,
    stocktake_id=stocktake_id,
    transcription=transcription,
    parsed_action=command.get('action'),
    parsed_item=command.get('item_identifier'),
    parsed_value=command.get('value'),
    success=True
)
```

---

## 🎯 Quick Start Checklist

- [ ] Install `openai` or `google-cloud-speech`
- [ ] Add API key to environment variables
- [ ] Create `voice_recognition/` module
- [ ] Implement `transcription.py`
- [ ] Implement `command_parser.py`
- [ ] Implement `views.py`
- [ ] Add URL pattern
- [ ] Test with cURL
- [ ] Test from frontend
- [ ] Add logging
- [ ] Deploy and monitor

---

## 💡 Frontend Already Handles

✅ **Item Matching** - Fuzzy search with 5-tier matching  
✅ **Validation** - Audio blob size, format checks  
✅ **Execution** - Calls appropriate stocktake API  
✅ **Pusher Broadcasting** - Real-time updates to all clients  
✅ **Error Display** - User-friendly error messages  
✅ **Loading States** - Recording, processing, success indicators  

Backend only needs: **Audio → Text → Structured JSON**

---

## 🆘 Support & Debugging

If transcription seems inaccurate:
1. Check audio quality (background noise)
2. Adjust transcription prompt/context
3. Try different model (Whisper large vs base)
4. Add product names to speech context hints

If parsing fails:
1. Log raw transcription
2. Check regex patterns match variations
3. Add more action keywords
4. Handle number words ("five" → 5)

Frontend has comprehensive logging - check browser console for detailed execution flow.
