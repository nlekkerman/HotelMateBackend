# Timeout Endpoint - Dedicated Solution

## Problem Solved
Frontend was not reliably moving to next question after timeout because it wasn't checking the `move_to_next_question` flag from the regular submit endpoint.

## Solution
**NEW DEDICATED ENDPOINT** specifically for timeouts that GUARANTEES the frontend will move to the next question.

---

## New Endpoint

### `POST /api/entertainment/quiz/game/submit_timeout/`

**Purpose**: Submit a timeout when timer expires. Always gives 0 points, resets streak, and tells frontend to move to next question.

### Request

```json
{
  "session_id": "uuid-here",
  "category_slug": "classic-trivia",
  "question_id": 123,
  "question_text": "What is the capital of France?"
}
```

**For Math Questions:**
```json
{
  "session_id": "uuid-here",
  "category_slug": "dynamic-math",
  "question_text": "5 × 7 = ?",
  "question_data": {
    "num1": 5,
    "num2": 7,
    "operator": "*",
    "correct_answer": 35
  }
}
```

### Response

```json
{
  "success": true,
  "timeout": true,
  "submission": {
    "selected_answer": "TIMEOUT",
    "correct_answer": "Paris",
    "is_correct": false,
    "points_awarded": 0,
    "time_taken_seconds": 6
  },
  "session_updated": {
    "score": 20,
    "consecutive_correct": 0,
    "is_turbo_active": false,
    "is_completed": false,
    "total_questions_answered": 5,
    "total_questions": 50
  },
  "game_completed": false,
  "move_to_next_question": true
}
```

---

## Frontend Implementation

### When Timer Reaches 0:

```javascript
const handleTimeout = async () => {
  try {
    const response = await fetch('/api/entertainment/quiz/game/submit_timeout/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        category_slug: currentCategory.slug,
        question_id: currentQuestion.id,
        question_text: currentQuestion.text,
        question_data: currentQuestion.question_data // For math questions
      })
    });
    
    const result = await response.json();
    
    // Show timeout feedback
    showFeedback({
      isTimeout: true,
      correctAnswer: result.submission.correct_answer,
      message: 'Time\'s up!'
    });
    
    // ALWAYS move to next question after 2 seconds
    setTimeout(() => {
      moveToNextQuestion();
    }, 2000);
    
  } catch (error) {
    console.error('Timeout submission failed:', error);
    // Still move to next question
    setTimeout(() => moveToNextQuestion(), 2000);
  }
};
```

---

## Game Rules

### Total Questions: 50
- **4 regular categories** × 10 questions = 40 questions
- **1 math category** × 10 questions = 10 questions
- **Total = 50 questions**

### After 50 Questions:
- `game_completed` will be `true`
- Session is automatically completed
- Frontend should show final score screen

---

## Behavior

### What Happens on Timeout:
1. ✅ Records submission with `selected_answer = "TIMEOUT"`
2. ✅ Awards **0 points**
3. ✅ Resets `consecutive_correct` streak to **0**
4. ✅ Deactivates **turbo mode**
5. ✅ Returns `move_to_next_question: true`
6. ✅ Increments `total_questions_answered`
7. ✅ If 50 questions answered, auto-completes game

### Frontend Must:
1. Show timeout feedback for 2 seconds
2. Move to next question automatically
3. Check `game_completed` flag
4. If `game_completed === true`, show final score

---

## Testing

Run: `python test_timeout_endpoint.py`

✅ All tests pass - endpoint is ready for production

---

## API Endpoints Summary

| Endpoint | Purpose |
|----------|---------|
| `POST /quiz/game/start_session/` | Start new game |
| `GET /quiz/game/fetch_category_questions/` | Get questions for category |
| `POST /quiz/game/submit_answer/` | Submit regular answer |
| `POST /quiz/game/submit_timeout/` | ⭐ Submit timeout (NEW) |
| `POST /quiz/game/complete_session/` | Complete game manually |

---

**Status**: ✅ Complete and Tested  
**Date**: November 14, 2025
