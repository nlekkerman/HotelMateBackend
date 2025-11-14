# Backend Changes - Timeout Handling

## 🔴 Problem Reported

When question times out, frontend shows the same question again instead of moving to next question.

## ✅ Backend Changes Made

### 1. Updated Response Structure

**File**: `entertainment/views.py`  
**Method**: `submit_answer`

Added two new fields to the API response:

```json
{
  "success": true,
  "submission": {
    "is_correct": false,
    "selected_answer": "TIMEOUT",
    "correct_answer": "The Right Answer",
    "points_awarded": 0
  },
  "session_updated": { ... },
  "game_completed": false,
  "is_timeout": true,              ← NEW FIELD
  "move_to_next_question": true    ← NEW FIELD
}
```

### 2. What These Fields Mean

- **`is_timeout`**: `true` if this was a timeout submission, `false` otherwise
- **`move_to_next_question`**: Always `true` - signals frontend to advance to next question

### 3. Existing Timeout Behavior (Already Working)

- When `time_taken_seconds > 5` OR `selected_answer == "TIMEOUT"`:
  - Sets `is_correct = false`
  - Sets `points_awarded = 0`
  - Resets `consecutive_correct = 0`
  - Deactivates turbo mode
  - Records answer as "TIMEOUT" in database

### 4. Code Changes

**Location**: `entertainment/views.py` line ~1448

**Before**:
```python
return Response({
    'success': True,
    'submission': QuizSubmissionSerializer(submission).data,
    'session_updated': { ... },
    'game_completed': game_completed
})
```

**After**:
```python
return Response({
    'success': True,
    'submission': QuizSubmissionSerializer(submission).data,
    'session_updated': { ... },
    'game_completed': game_completed,
    'is_timeout': is_timeout,           # NEW
    'move_to_next_question': True       # NEW
})
```

## 📋 What Frontend Needs to Do

1. Check `move_to_next_question` field in response (always `true`)
2. After showing feedback (1-2 seconds), move to next question
3. Do NOT reload the same question on timeout
4. Treat timeout same as wrong answer (move forward)

## ✅ Backend Testing

Tested with `test_timeout_submission.py`:
- ✅ Time > 5 seconds → Returns `is_timeout: true`
- ✅ Answer = "TIMEOUT" → Returns `is_timeout: true`
- ✅ Both cases give 0 points
- ✅ Both cases reset streak
- ✅ Response includes new fields

---

**Date**: November 14, 2025  
**Changes**: Added `is_timeout` and `move_to_next_question` fields to submit_answer response  
**Testing**: Passed all timeout tests  
**Status**: ✅ Backend complete
