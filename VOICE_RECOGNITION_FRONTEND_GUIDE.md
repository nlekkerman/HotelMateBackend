# Voice Recognition Frontend Integration Guide

## Overview
This guide covers the frontend implementation for the Phase One Voice Stocktake System. Users can record voice commands like "count Heineken 24" to update stock counts hands-free.

## Backend Endpoint

### POST `/api/stock_tracker/<hotel_identifier>/stocktake-lines/voice-command/`

**Authentication:** Required (Bearer Token)

**Request Format:** `multipart/form-data`
```javascript
{
  audio: File,           // Audio file (webm, mp4, mpeg, mpga, m4a, wav, mp3)
  stocktake_id: string   // ID of the active stocktake
}
```

**Response Format:**
```javascript
{
  success: boolean,
  command: {
    action: "count" | "purchase" | "waste",
    item_identifier: string,        // Product name from speech
    value: number,                  // Total value (bottles/units)
    full_units: number | null,      // For dozen products (e.g., 2 dozen)
    partial_units: number | null,   // For dozen products (e.g., 3 bottles)
    transcription: string           // Raw text from Whisper
  },
  stocktake_id: number
}
```

**Error Response:**
```javascript
{
  success: false,
  error: string,
  details?: object
}
```

## Voice Command Patterns

### Supported Actions
- **Count:** "count", "I have", "there are"
- **Purchase:** "purchase", "bought", "buy"
- **Waste:** "waste", "wasted", "damaged", "broken"

### Command Examples

**Simple Count (Bottles/Individual Units):**
- "count Heineken 24" → `{action: "count", item_identifier: "Heineken", value: 24}`
- "I have Coca-Cola 15" → `{action: "count", item_identifier: "Coca-Cola", value: 15}`
- "there are Guinness twelve" → `{action: "count", item_identifier: "Guinness", value: 12}`

**Dozen Products:**
- "count Heineken 2 dozen 3" → `{action: "count", item_identifier: "Heineken", value: 27, full_units: 2, partial_units: 3}`
- "I have Coke 1 dozen 6" → `{action: "count", item_identifier: "Coke", value: 18, full_units: 1, partial_units: 6}`

**Purchases:**
- "purchase Heineken 3 dozen" → `{action: "purchase", item_identifier: "Heineken", value: 36, full_units: 3}`
- "bought Guinness 24" → `{action: "purchase", item_identifier: "Guinness", value: 24}`

**Waste:**
- "waste Budweiser 2" → `{action: "waste", item_identifier: "Budweiser", value: 2}`
- "damaged Corona 5" → `{action: "waste", item_identifier: "Corona", value: 5}`

## Frontend Implementation

### 1. Recording Component

```typescript
import { useState, useRef } from 'react';

const VoiceRecorder = ({ stocktakeId, hotelIdentifier, onCommandReceived }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processVoiceCommand(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
    } catch (error) {
      console.error('Microphone access denied:', error);
      alert('Please enable microphone access to use voice commands');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const processVoiceCommand = async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'voice-command.webm');
      formData.append('stocktake_id', stocktakeId.toString());

      const response = await fetch(
        `/api/stock_tracker/${hotelIdentifier}/stocktake-lines/voice-command/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: formData
        }
      );

      const data = await response.json();

      if (data.success) {
        onCommandReceived(data.command);
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      console.error('Voice command processing failed:', error);
      alert('Failed to process voice command. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="voice-recorder">
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
        className={isRecording ? 'recording' : ''}
      >
        {isProcessing ? 'Processing...' : isRecording ? 'Stop Recording' : '🎤 Voice Command'}
      </button>
    </div>
  );
};

export default VoiceRecorder;
```

### 2. Preview Modal Component

```typescript
import { useState } from 'react';

const VoiceCommandPreview = ({ command, onConfirm, onCancel }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleConfirm = async () => {
    setIsSubmitting(true);
    await onConfirm(command);
    setIsSubmitting(false);
  };

  const formatAction = (action) => {
    return action.charAt(0).toUpperCase() + action.slice(1);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Confirm Voice Command</h2>
        
        <div className="command-preview">
          <div className="preview-row">
            <span className="label">Action:</span>
            <span className="value">{formatAction(command.action)}</span>
          </div>
          
          <div className="preview-row">
            <span className="label">Product:</span>
            <span className="value">{command.item_identifier}</span>
          </div>
          
          {command.full_units !== null && (
            <div className="preview-row">
              <span className="label">Dozen:</span>
              <span className="value">{command.full_units}</span>
            </div>
          )}
          
          {command.partial_units !== null && (
            <div className="preview-row">
              <span className="label">Bottles:</span>
              <span className="value">{command.partial_units}</span>
            </div>
          )}
          
          <div className="preview-row total">
            <span className="label">Total:</span>
            <span className="value">{command.value}</span>
          </div>
          
          <div className="preview-row transcription">
            <span className="label">You said:</span>
            <span className="value">"{command.transcription}"</span>
          </div>
        </div>
        
        <div className="modal-actions">
          <button 
            onClick={onCancel} 
            disabled={isSubmitting}
            className="btn-cancel"
          >
            Cancel
          </button>
          <button 
            onClick={handleConfirm} 
            disabled={isSubmitting}
            className="btn-confirm"
          >
            {isSubmitting ? 'Updating...' : 'Confirm'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoiceCommandPreview;
```

### 3. Integration Example

```typescript
import { useState } from 'react';
import VoiceRecorder from './VoiceRecorder';
import VoiceCommandPreview from './VoiceCommandPreview';

const StocktakePage = ({ stocktake, hotelIdentifier }) => {
  const [previewCommand, setPreviewCommand] = useState(null);

  const handleCommandReceived = (command) => {
    setPreviewCommand(command);
  };

  const handleConfirmCommand = async (command) => {
    try {
      // Find matching stock item
      const stockItem = stocktake.lines.find(line => 
        line.stock_item.name.toLowerCase().includes(command.item_identifier.toLowerCase())
      );

      if (!stockItem) {
        alert(`Product "${command.item_identifier}" not found in stocktake`);
        setPreviewCommand(null);
        return;
      }

      // Update the stock count using existing API
      let updateData = {};
      
      if (command.action === 'count') {
        // For dozen products
        if (command.full_units !== null) {
          updateData = {
            counted_full_units: command.full_units,
            counted_partial_units: command.partial_units || 0
          };
        } else {
          // For individual/bottle products
          updateData = {
            counted_quantity: command.value
          };
        }
      } else if (command.action === 'purchase') {
        if (command.full_units !== null) {
          updateData = {
            purchases_full_units: command.full_units,
            purchases_partial_units: command.partial_units || 0
          };
        } else {
          updateData = {
            purchases: command.value
          };
        }
      } else if (command.action === 'waste') {
        if (command.full_units !== null) {
          updateData = {
            waste_full_units: command.full_units,
            waste_partial_units: command.partial_units || 0
          };
        } else {
          updateData = {
            waste: command.value
          };
        }
      }

      // Call existing update API
      const response = await fetch(
        `/api/stock_tracker/${hotelIdentifier}/stocktake-lines/${stockItem.id}/`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(updateData)
        }
      );

      if (response.ok) {
        setPreviewCommand(null);
        // Pusher will automatically broadcast the update
      } else {
        const error = await response.json();
        alert(`Failed to update: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Update failed:', error);
      alert('Failed to update stock count');
    }
  };

  const handleCancelCommand = () => {
    setPreviewCommand(null);
  };

  return (
    <div className="stocktake-page">
      <h1>Stocktake - {stocktake.name}</h1>
      
      <VoiceRecorder
        stocktakeId={stocktake.id}
        hotelIdentifier={hotelIdentifier}
        onCommandReceived={handleCommandReceived}
      />

      {previewCommand && (
        <VoiceCommandPreview
          command={previewCommand}
          onConfirm={handleConfirmCommand}
          onCancel={handleCancelCommand}
        />
      )}

      {/* Your existing stocktake UI */}
    </div>
  );
};

export default StocktakePage;
```

## Real-Time Updates

Voice command updates trigger Pusher broadcasts automatically through the existing `broadcast_line_counted_updated()` function. No additional Pusher integration needed.

**Pusher Channel:** `{hotel_identifier}-stocktake-{stocktake_id}`  
**Pusher Event:** `line-counted-updated`

**Event Payload:**
```javascript
{
  line_id: number,
  counted_quantity: number,
  counted_full_units: number,
  counted_partial_units: number,
  variance: number,
  variance_full_units: number,
  variance_partial_units: number,
  purchases: number,
  waste: number,
  // ... other fields
}
```

Subscribe to updates in your frontend:
```typescript
const pusher = new Pusher(PUSHER_KEY, { cluster: PUSHER_CLUSTER });
const channel = pusher.subscribe(`${hotelIdentifier}-stocktake-${stocktakeId}`);

channel.bind('line-counted-updated', (data) => {
  // Update the UI with new values
  updateStockLine(data);
});
```

## Error Handling

### Common Errors

**Audio File Too Large:**
```javascript
{
  success: false,
  error: "Audio file too large. Maximum size is 10MB"
}
```

**Stocktake Not Found:**
```javascript
{
  success: false,
  error: "Stocktake not found or you don't have access to it"
}
```

**Locked Stocktake:**
```javascript
{
  success: false,
  error: "This stocktake is locked and cannot be modified"
}
```

**Transcription Failed:**
```javascript
{
  success: false,
  error: "Failed to transcribe audio"
}
```

**Invalid Command Format:**
```javascript
{
  success: false,
  error: "Could not parse voice command. Please try: 'count [product] [number]'"
}
```

## Testing

### Manual Testing with cURL

```bash
# Record audio file (use browser recording or mobile app)
# Save as test_audio.webm

curl -X POST \
  http://localhost:8000/api/stock_tracker/your-hotel/stocktake-lines/voice-command/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio=@test_audio.webm" \
  -F "stocktake_id=123"
```

### Test Commands

Try these voice commands:
- "count Heineken 24"
- "I have Coca-Cola 2 dozen 6"
- "purchase Guinness 3 dozen"
- "waste Budweiser 2"
- "there are twelve Corona"

## Best Practices

1. **Microphone Permissions:** Always handle denied microphone access gracefully
2. **Visual Feedback:** Show recording status (red dot, animation)
3. **Processing State:** Display loading indicator during transcription
4. **Preview Modal:** Always show preview before confirming
5. **Error Messages:** Provide clear, actionable error messages
6. **Product Matching:** Use fuzzy matching to find products (e.g., "Heineken" matches "Heineken Lager")
7. **Timeout:** Set reasonable timeout for recording (e.g., 10 seconds max)
8. **Audio Quality:** Use high-quality audio codec (opus in webm)

## Styling Example

```css
.voice-recorder button {
  padding: 12px 24px;
  font-size: 16px;
  border-radius: 8px;
  border: 2px solid #007bff;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
}

.voice-recorder button.recording {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 24px;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
}

.command-preview {
  margin: 20px 0;
}

.preview-row {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid #eee;
}

.preview-row.total {
  font-weight: bold;
  font-size: 18px;
  border-top: 2px solid #007bff;
  margin-top: 8px;
}

.preview-row.transcription {
  background: #f8f9fa;
  font-style: italic;
  color: #666;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.modal-actions button {
  flex: 1;
  padding: 12px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 16px;
}

.btn-cancel {
  background: #6c757d;
  color: white;
}

.btn-confirm {
  background: #28a745;
  color: white;
}
```

## Security Notes

1. **Authentication Required:** All requests must include valid Bearer token
2. **Hotel Access:** Backend validates user has access to the hotel
3. **Stocktake Access:** Backend validates stocktake belongs to hotel
4. **File Validation:** Backend checks file type and size (10MB max)
5. **No Storage:** Audio files are not stored, only processed in memory

## Phase Two (Future)

Phase Two will add:
- Voice command history/logging
- Analytics on voice command usage
- Custom vocabulary training
- Multi-language support
- Offline mode with local processing

For now, Phase One provides core voice recognition functionality without database logging.
