# 🎤 Voice Recognition Frontend Implementation Guide

Complete guide for implementing voice recognition in the stocktake page with confirmation modal.

---

## Overview

**Two-step workflow:**
1. **Parse** → User speaks, backend transcribes & parses (preview only)
2. **Confirm** → User reviews modal, clicks confirm, backend updates database

**Backend handles ALL matching** - Frontend just displays results and sends confirmation.

---

## Key Points

✅ **Backend does fuzzy matching** - "bud botle" will match "Budweiser Bottle"  
✅ **No frontend matching needed** - Just pass the `item_identifier` as-is  
✅ **Confirmation modal required** - User must review before applying  
✅ **Action can be anywhere** - "count budweiser 7" or "budweiser 7 count"  

---

## API Endpoints

### 1. Parse Voice Command (Preview)

**POST** `/api/stock_tracker/{hotel}/stocktake-lines/voice-command/`

**Request:**
```typescript
const formData = new FormData();
formData.append('audio', audioBlob);
formData.append('stocktake_id', stocktakeId.toString());

fetch(`/api/stock_tracker/${hotelId}/stocktake-lines/voice-command/`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});
```

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
    "transcription": "count budweiser seven cases"
  },
  "stocktake_id": 123
}
```

---

### 2. Confirm Voice Command (Update)

**POST** `/api/stock_tracker/{hotel}/stocktake-lines/voice-command/confirm/`

**Request:**
```typescript
fetch(`/api/stock_tracker/${hotelId}/stocktake-lines/voice-command/confirm/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    stocktake_id: stocktakeId,
    command: command  // Pass entire command object from parse response
  })
});
```

**Response:**
```json
{
  "success": true,
  "line": {
    "id": 456,
    "item": {
      "id": 789,
      "sku": "B0070",
      "name": "Budweiser Bottle"
    },
    "counted_full_units": 7,
    "counted_partial_units": 0,
    "counted_qty": 7,
    "variance_qty": -1
  },
  "message": "Counted 7 units of Budweiser Bottle",
  "item_name": "Budweiser Bottle",
  "item_sku": "B0070"
}
```

---

## Frontend Implementation

### 1. Voice Recording Hook

```typescript
// hooks/useVoiceRecording.ts
import { useState, useRef } from 'react';

export const useVoiceRecording = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      throw error;
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const clearAudio = () => {
    setAudioBlob(null);
  };

  return {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording,
    clearAudio
  };
};
```

---

### 2. Voice Command Service

```typescript
// services/voiceCommandService.ts
import { apiClient } from './api';

export interface VoiceCommand {
  action: 'count' | 'purchase' | 'waste';
  item_identifier: string;
  value: number;
  full_units?: number;
  partial_units?: number;
  transcription: string;
}

export interface ParseResult {
  success: boolean;
  command?: VoiceCommand;
  stocktake_id?: number;
  error?: string;
  transcription?: string;
}

export interface ConfirmResult {
  success: boolean;
  line?: any;
  message?: string;
  item_name?: string;
  item_sku?: string;
  error?: string;
}

export const voiceCommandService = {
  /**
   * Parse voice command (preview only - no database changes)
   */
  async parseVoiceCommand(
    hotelId: string,
    audioBlob: Blob,
    stocktakeId: number
  ): Promise<ParseResult> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'voice-command.webm');
    formData.append('stocktake_id', stocktakeId.toString());

    const response = await apiClient.post(
      `/stock_tracker/${hotelId}/stocktake-lines/voice-command/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    );

    return response.data;
  },

  /**
   * Confirm voice command (updates database)
   */
  async confirmVoiceCommand(
    hotelId: string,
    stocktakeId: number,
    command: VoiceCommand
  ): Promise<ConfirmResult> {
    const response = await apiClient.post(
      `/stock_tracker/${hotelId}/stocktake-lines/voice-command/confirm/`,
      {
        stocktake_id: stocktakeId,
        command: command
      }
    );

    return response.data;
  }
};
```

---

### 3. Confirmation Modal Component

```typescript
// components/VoiceCommandConfirmModal.tsx
import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { VoiceCommand } from '@/services/voiceCommandService';
import { Mic, Package, TrendingUp, Trash2 } from 'lucide-react';

interface VoiceCommandConfirmModalProps {
  open: boolean;
  command: VoiceCommand;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export const VoiceCommandConfirmModal: React.FC<VoiceCommandConfirmModalProps> = ({
  open,
  command,
  onConfirm,
  onCancel,
  isLoading = false
}) => {
  const getActionIcon = () => {
    switch (command.action) {
      case 'count':
        return <Package className="w-5 h-5 text-blue-500" />;
      case 'purchase':
        return <TrendingUp className="w-5 h-5 text-green-500" />;
      case 'waste':
        return <Trash2 className="w-5 h-5 text-red-500" />;
    }
  };

  const getActionLabel = () => {
    switch (command.action) {
      case 'count':
        return 'Count';
      case 'purchase':
        return 'Purchase';
      case 'waste':
        return 'Waste';
    }
  };

  const getActionColor = () => {
    switch (command.action) {
      case 'count':
        return 'text-blue-600';
      case 'purchase':
        return 'text-green-600';
      case 'waste':
        return 'text-red-600';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onCancel}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mic className="w-5 h-5" />
            Confirm Voice Command
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Transcription */}
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">You said:</p>
            <p className="text-sm italic">"{command.transcription}"</p>
          </div>

          {/* Parsed Command */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-3">
              {getActionIcon()}
              <div>
                <p className="text-xs text-gray-500">Action</p>
                <p className={`text-lg font-semibold ${getActionColor()}`}>
                  {getActionLabel()}
                </p>
              </div>
            </div>

            <div>
              <p className="text-xs text-gray-500">Product</p>
              <p className="text-lg font-semibold capitalize">
                {command.item_identifier}
              </p>
            </div>

            {command.full_units !== undefined && command.partial_units !== undefined ? (
              <div>
                <p className="text-xs text-gray-500">Quantity</p>
                <p className="text-lg font-semibold">
                  {command.full_units} cases + {command.partial_units} bottles
                </p>
                <p className="text-sm text-gray-500">
                  Total: {command.value} units
                </p>
              </div>
            ) : (
              <div>
                <p className="text-xs text-gray-500">Quantity</p>
                <p className="text-lg font-semibold">
                  {command.value} units
                </p>
              </div>
            )}
          </div>

          {/* Warning for non-count actions */}
          {command.action !== 'count' && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-xs text-yellow-800">
                This will {command.action === 'purchase' ? 'add' : 'record'} {command.value} units 
                {command.action === 'purchase' ? ' to purchases' : ' as waste'}.
              </p>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isLoading}
            className="min-w-24"
          >
            {isLoading ? 'Applying...' : 'Confirm'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

---

### 4. Voice Recording Button Component

```typescript
// components/VoiceRecordButton.tsx
import React, { useState } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useVoiceRecording } from '@/hooks/useVoiceRecording';
import { voiceCommandService, VoiceCommand } from '@/services/voiceCommandService';
import { VoiceCommandConfirmModal } from './VoiceCommandConfirmModal';
import { toast } from 'sonner';

interface VoiceRecordButtonProps {
  hotelId: string;
  stocktakeId: number;
  onSuccess?: () => void;
}

export const VoiceRecordButton: React.FC<VoiceRecordButtonProps> = ({
  hotelId,
  stocktakeId,
  onSuccess
}) => {
  const {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording,
    clearAudio
  } = useVoiceRecording();

  const [isParsing, setIsParsing] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [parsedCommand, setParsedCommand] = useState<VoiceCommand | null>(null);

  // Handle recording toggle
  const handleRecordClick = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      try {
        await startRecording();
      } catch (error) {
        toast.error('Failed to access microphone');
      }
    }
  };

  // Parse audio when recording stops
  React.useEffect(() => {
    if (audioBlob && !isRecording) {
      handleParse();
    }
  }, [audioBlob, isRecording]);

  // Parse the audio command
  const handleParse = async () => {
    if (!audioBlob) return;

    setIsParsing(true);

    try {
      const result = await voiceCommandService.parseVoiceCommand(
        hotelId,
        audioBlob,
        stocktakeId
      );

      if (result.success && result.command) {
        setParsedCommand(result.command);
        setShowConfirmModal(true);
      } else {
        toast.error(result.error || 'Could not understand command');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to parse voice command');
    } finally {
      setIsParsing(false);
      clearAudio();
    }
  };

  // Confirm and apply the command
  const handleConfirm = async () => {
    if (!parsedCommand) return;

    setIsConfirming(true);

    try {
      const result = await voiceCommandService.confirmVoiceCommand(
        hotelId,
        stocktakeId,
        parsedCommand
      );

      if (result.success) {
        toast.success(result.message || 'Command applied successfully');
        setShowConfirmModal(false);
        setParsedCommand(null);
        onSuccess?.();
      } else {
        toast.error(result.error || 'Failed to apply command');
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to apply command');
    } finally {
      setIsConfirming(false);
    }
  };

  // Cancel confirmation
  const handleCancel = () => {
    setShowConfirmModal(false);
    setParsedCommand(null);
  };

  return (
    <>
      <Button
        variant={isRecording ? 'destructive' : 'outline'}
        size="icon"
        onClick={handleRecordClick}
        disabled={isParsing}
        className={isRecording ? 'animate-pulse' : ''}
      >
        {isParsing ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : isRecording ? (
          <MicOff className="w-4 h-4" />
        ) : (
          <Mic className="w-4 h-4" />
        )}
      </Button>

      {parsedCommand && (
        <VoiceCommandConfirmModal
          open={showConfirmModal}
          command={parsedCommand}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
          isLoading={isConfirming}
        />
      )}
    </>
  );
};
```

---

### 5. Integration into Stocktake Page

```typescript
// pages/stocktake/[id].tsx
import { VoiceRecordButton } from '@/components/VoiceRecordButton';

export const StocktakePage = () => {
  const { hotelId, stocktakeId } = useParams();
  const { refetch } = useStocktakeLines(stocktakeId);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1>Stocktake #{stocktakeId}</h1>
        
        <div className="flex gap-2">
          {/* Voice Recording Button */}
          <VoiceRecordButton
            hotelId={hotelId}
            stocktakeId={stocktakeId}
            onSuccess={() => refetch()}
          />
          
          {/* Other buttons */}
        </div>
      </div>

      {/* Stocktake table... */}
    </div>
  );
};
```

---

## Backend Fuzzy Matching (No Frontend Work Needed!)

The backend now uses **rapidfuzz** for intelligent matching:

### Handles Partial Names
- ✅ "bud" → matches "Budweiser Bottle"
- ✅ "bud botle" → matches "Budweiser Bottle"
- ✅ "heiny" → matches "Heineken Bottle"
- ✅ "smithix" → matches "Smithwicks Bottle"

### Handles Misspellings
- ✅ "budwiser" → "Budweiser"
- ✅ "guiness" → "Guinness"
- ✅ "heinikn" → "Heineken"

### Handles Synonyms
- ✅ "draft" → "Draught"
- ✅ "botl" → "Bottle"
- ✅ "keg" → "Draught"

**Frontend just passes the `item_identifier` as-is** - backend does all the matching!

---

## Error Handling

```typescript
try {
  const result = await voiceCommandService.parseVoiceCommand(...);
  
  if (!result.success) {
    // Show specific error
    if (result.error.includes('No action keyword')) {
      toast.error('Please say "count", "purchase", or "waste"');
    } else if (result.error.includes('No numeric value')) {
      toast.error('Please say the quantity clearly');
    } else {
      toast.error(result.error);
    }
  }
} catch (error) {
  // Network or API error
  toast.error('Failed to process voice command');
}
```

---

## Testing

### Test Parse Endpoint
```bash
curl -X POST \
  http://localhost:8000/api/stock_tracker/killarney/stocktake-lines/voice-command/ \
  -H "Authorization: Bearer TOKEN" \
  -F "audio=@test.webm" \
  -F "stocktake_id=123"
```

### Test Confirm Endpoint
```bash
curl -X POST \
  http://localhost:8000/api/stock_tracker/killarney/stocktake-lines/voice-command/confirm/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stocktake_id": 123,
    "command": {
      "action": "count",
      "item_identifier": "budweiser",
      "value": 7
    }
  }'
```

---

## Summary

| Responsibility | Who Does It |
|----------------|-------------|
| Audio recording | Frontend |
| Transcription (Whisper) | Backend |
| Command parsing | Backend |
| Fuzzy item matching | **Backend** ✅ |
| Display confirmation | Frontend |
| Database update | Backend |
| Real-time broadcast | Backend (Pusher) |

**Frontend is simple** - just record, show modal, send confirmation. Backend handles all the complexity!
