# Backend Changes: Move to Next Question After Timeout

## Problem Reported

When a question times out, frontend shows the same question again instead of moving to next question.

## Backend Solution

Added explicit flags to the API response to tell frontend to move forward.

## Updated Response Structure

**Endpoint**: `POST /api/entertainment/quiz/game/submit_answer/`

The backend now returns these flags:

```json
{
  "success": true,
  "submission": {
    "is_correct": false,
    "points_awarded": 0,
    "selected_answer": "TIMEOUT",
    "correct_answer": "Paris"
  },
  "session_updated": { ... },
  "is_timeout": true,              // ← NEW: Was this a timeout?
  "move_to_next_question": true    // ← NEW: Always true - tells frontend to advance
}
```

## Field Descriptions

- **`is_timeout`**: Boolean, `true` if this submission was a timeout
- **`move_to_next_question`**: Boolean, always `true` - explicit signal to advance

## Expected Frontend Behavior

When receiving response:
1. Show feedback (correct/wrong/timeout) for 1-2 seconds
2. Check `move_to_next_question` field (always true)
3. Increment question index/counter
4. Load next question

## What Changed in Backend

**File**: `entertainment/views.py`  
**Method**: `submit_answer` (line ~1448)

Added two fields to response:
```python
return Response({
    'success': True,
    'submission': QuizSubmissionSerializer(submission).data,
    'session_updated': { ... },
    'game_completed': game_completed,
    'is_timeout': is_timeout,           # NEW
    'move_to_next_question': True       # NEW - Always true
})
```

## Backend Testing Results

Test file: `test_timeout_submission.py`

✅ Time > 5 seconds: Returns `is_timeout: true`  
✅ Answer = "TIMEOUT": Returns `is_timeout: true`  
✅ Both give 0 points  
✅ Both reset streak  
✅ Response includes new fields

---

**Backend Status**: ✅ Complete  
**Date**: November 14, 2025
