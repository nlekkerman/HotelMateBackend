# Backend Changes: Move to Next Question After Timeout

## ⚠️ CRITICAL ISSUE: FRONTEND NOT CHECKING THE FLAG ⚠️

**Status**: Backend is 100% working and returning the flag correctly.
**Problem**: Frontend code in `useQuizGame.js` is NOT checking `move_to_next_question` flag!

## Problem Reported

When a question times out, frontend shows the same question again instead of moving to next question.

## Backend Solution ✅ COMPLETE

Added explicit flags to the API response to tell frontend to move forward.
**TESTED AND VERIFIED - Backend returns `move_to_next_question: true` in ALL cases**

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

## 🚨 FRONTEND MUST IMPLEMENT THIS 🚨

**File**: `useQuizGame.js` (line ~326 in `handleAnswerSelect`)

### Current Broken Code:
```javascript
const handleAnswerSelect = async (answerId, answerText) => {
  try {
    const result = await submitAnswer(answerId, answerText);
    setLastSubmission(result.submission);
    // ❌ MISSING: Not checking result.move_to_next_question
  } catch (error) {
    console.error('Failed:', error);
  }
};
```

### Required Fix:
```javascript
const handleAnswerSelect = async (answerId, answerText) => {
  try {
    const result = await submitAnswer(answerId, answerText);
    
    // Show feedback
    setLastSubmission(result.submission);
    setShowFeedback(true);
    
    // ✅ CHECK THE FLAG FROM BACKEND
    if (result.move_to_next_question === true) {
      setTimeout(() => {
        setShowFeedback(false);
        // Move to next question
        setCurrentQuestionIndex(prev => prev + 1);
        // OR call your navigation function
        moveToNextQuestion();
      }, 2000);
    }
  } catch (error) {
    console.error('Failed:', error);
  }
};
```

## Expected Frontend Behavior

When receiving response:
1. Show feedback (correct/wrong/timeout) for 1-2 seconds
2. **CHECK `result.move_to_next_question` field** (backend always returns `true`)
3. If true, increment question index/counter
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

## Test Results

Run `python test_move_to_next_flag.py` to verify:

✅ Correct answer: Returns `move_to_next_question: true`  
✅ Wrong answer: Returns `move_to_next_question: true`  
✅ Timeout: Returns `move_to_next_question: true` AND `is_timeout: true`

**Example Response:**
```json
{
  "success": true,
  "submission": { "is_correct": false, "points_awarded": 0 },
  "session_updated": { "score": 4 },
  "game_completed": false,
  "is_timeout": true,
  "move_to_next_question": true  ← FRONTEND: CHECK THIS!
}
```

---

## 🎯 BETTER SOLUTION: Dedicated Timeout Endpoint

**NEW**: Created separate endpoint specifically for timeouts that GUARANTEES moving to next question.

### Use This Instead:
```
POST /api/entertainment/quiz/game/submit_timeout/
```

**See**: `TIMEOUT_ENDPOINT.md` for complete documentation

### Why This Is Better:
- ✅ Dedicated endpoint for timeout = no confusion
- ✅ Always returns `move_to_next_question: true`
- ✅ Simpler frontend logic
- ✅ Tested and working

---

**Backend Status**: ✅ 100% Complete and Tested  
**Timeout Endpoint**: ✅ NEW - Ready for production (see TIMEOUT_ENDPOINT.md)  
**Date**: November 14, 2025
