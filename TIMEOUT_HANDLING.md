# Timeout Handling - Quiz Game

## ✅ Backend Implementation Complete

### What Changed

The backend now properly handles timeout scenarios when:
1. Time exceeds 5 seconds (`time_taken_seconds > 5`)
2. User explicitly submits `"TIMEOUT"` as the answer

### Backend Behavior

**When Timeout Detected:**
- ❌ Marks answer as incorrect (`is_correct = false`)
- 🔢 Awards 0 points (`points_awarded = 0`)
- 💔 Resets consecutive correct streak to 0
- 🚫 Deactivates turbo mode
- 📝 Records answer as `"TIMEOUT"` in database
- ✅ Still returns the correct answer in response

### API Changes

**`POST /api/entertainment/quiz/game/submit_answer/`**

Updated validation:
```json
{
  "time_taken_seconds": 0-10  // Changed from 0-5
}
```

**Timeout Submission Example:**
```json
{
  "session_id": "uuid",
  "category_slug": "classic-trivia",
  "question_id": 123,
  "question_text": "What is the capital of Canada?",
  "selected_answer": "TIMEOUT",       // ← Special value
  "selected_answer_id": null,
  "time_taken_seconds": 6              // ← > 5 or use 6
}
```

**Response (Timeout):**
```json
{
  "success": true,
  "submission": {
    "id": "uuid",
    "selected_answer": "TIMEOUT",
    "correct_answer": "Ottawa",        // ← Still provided!
    "is_correct": false,
    "points_awarded": 0,
    "time_taken_seconds": 6
  },
  "session_updated": {
    "score": 0,
    "consecutive_correct": 0,          // ← Reset!
    "is_turbo_active": false           // ← Deactivated!
  }
}
```

---

## 🎯 Frontend Implementation Required

### 1. Timer Component

Add timeout handler that auto-submits when time expires:

```javascript
// In useQuizGame.js or timer component
const handleTimeout = async () => {
  if (hasAnswered || isSubmitting) return;
  
  console.log('⏰ Time expired! Auto-submitting...');
  setIsSubmitting(true);
  
  try {
    const result = await quizGameAPI.submitAnswer({
      sessionId: session.id,
      categorySlug: currentQuestion.category_slug,
      questionId: currentQuestion.id,
      questionText: currentQuestion.text,
      selectedAnswer: "TIMEOUT",          // ✅ Special value
      selectedAnswerId: null,
      timeTaken: 6,                       // ✅ Fixed value
      questionData: currentQuestion.question_data
    });
    
    setLastSubmission(result.submission);
    setHasAnswered(true);
    
    // Auto-advance after showing feedback
    setTimeout(() => {
      moveToNextQuestion();
    }, 2500);
    
  } catch (error) {
    console.error('Timeout submission failed:', error);
  } finally {
    setIsSubmitting(false);
  }
};
```

### 2. Watch Timer

```javascript
useEffect(() => {
  // When timer hits 0 or goes negative
  if (timeLeft <= 0 && !hasAnswered && !isSubmitting) {
    handleTimeout();
  }
}, [timeLeft, hasAnswered, isSubmitting]);
```

### 3. UI Feedback

```javascript
{lastSubmission && (
  <div className={`feedback ${
    lastSubmission.selected_answer === 'TIMEOUT' 
      ? 'timeout' 
      : lastSubmission.is_correct ? 'correct' : 'wrong'
  }`}>
    {lastSubmission.selected_answer === 'TIMEOUT' ? (
      <h3>⏰ TIME'S UP!</h3>
    ) : lastSubmission.is_correct ? (
      <h3>✅ CORRECT!</h3>
    ) : (
      <h3>❌ WRONG!</h3>
    )}
    
    {lastSubmission.selected_answer === 'TIMEOUT' ? (
      <p className="timeout-msg">⏰ You ran out of time!</p>
    ) : (
      <p>You selected: {lastSubmission.selected_answer}</p>
    )}
    
    <p>Correct answer: <strong>{lastSubmission.correct_answer}</strong></p>
    <p>Points: <strong>{lastSubmission.points_awarded}</strong></p>
    
    {lastSubmission.selected_answer === 'TIMEOUT' && (
      <>
        <p className="streak-lost">💔 Streak reset!</p>
        {lastSubmission.was_turbo_active && (
          <p className="turbo-lost">Turbo mode lost!</p>
        )}
      </>
    )}
  </div>
)}
```

---

## 🎮 Bonus Game / Memory Game

**Same logic applies:**
- When bonus game timer expires, submit with `selected_answer: "TIMEOUT"`
- Backend will handle it the same way (0 points, reset streaks)
- Display timeout feedback

```javascript
// In bonus game component
const handleBonusTimeout = async () => {
  await submitBonusAnswer({
    // ... other fields
    selectedAnswer: "TIMEOUT",
    timeTaken: 6
  });
};
```

---

## 🧪 Testing Timeout

### Manual Test
1. Start a quiz game
2. Let timer run down to 0 without selecting an answer
3. Verify auto-submission happens
4. Check feedback shows "TIME'S UP!"
5. Verify 0 points awarded
6. Verify correct answer is displayed
7. Verify streak reset to 0
8. Move to next question automatically

### Console Logs to Add
```javascript
console.log('⏰ Timer expired at:', timeLeft);
console.log('📤 Submitting timeout answer...');
console.log('📥 Timeout response:', result);
console.log('💔 Streak reset:', result.session_updated.consecutive_correct);
```

---

## 🐛 Edge Cases Handled

### Backend Handles:
- ✅ Time > 5 seconds → Treated as timeout
- ✅ Answer = "TIMEOUT" → Treated as timeout (even if time < 5)
- ✅ Time > 10 seconds → Validation error (grace period exceeded)
- ✅ Resets streak even if had turbo mode active
- ✅ Still returns correct answer for learning

### Frontend Should Handle:
- ⏰ Timer expires mid-game
- 🔒 Prevent double submission
- 🎨 Show clear timeout feedback
- ⏭️ Auto-advance to next question
- 🎯 Update score display immediately

---

## 📊 Scoring Logic

### Normal Answer (Time ≤ 5s)
```
0s → 5 points (normal) / 10 points (turbo)
1s → 5 points / 10 points
2s → 4 points / 8 points
3s → 3 points / 6 points
4s → 2 points / 4 points
5s → 0 points / 0 points (too slow)
```

### Timeout (Time > 5s or answer = "TIMEOUT")
```
Always → 0 points
Always → Reset streak
Always → Deactivate turbo
```

---

## 🔍 Backend Code Reference

**File:** `entertainment/serializers.py`
```python
time_taken_seconds = serializers.IntegerField(
    min_value=0, 
    max_value=10  # ← Changed from 5
)
```

**File:** `entertainment/views.py`
```python
# Check if timeout
is_timeout = time_taken > 5 or selected_answer.upper() == 'TIMEOUT'

if is_timeout:
    is_correct = False
    time_taken = min(time_taken, 6)
else:
    is_correct = selected_answer == correct_answer_value

# Record with TIMEOUT label if timeout
selected_answer=selected_answer if not is_timeout else 'TIMEOUT'

# Reset streak on timeout
if is_correct and points > 0 and not is_timeout:
    session.consecutive_correct += 1
else:
    session.consecutive_correct = 0
    session.is_turbo_active = False
```

---

## ✅ Summary

**Backend:**
- ✅ Accepts time up to 10 seconds
- ✅ Recognizes "TIMEOUT" answer
- ✅ Gives 0 points for timeouts
- ✅ Resets streaks and turbo mode
- ✅ Returns correct answer in response

**Frontend TODO:**
- [ ] Add timeout handler function
- [ ] Add useEffect to watch timer
- [ ] Submit "TIMEOUT" when timer expires
- [ ] Show timeout feedback UI
- [ ] Test timeout scenario
- [ ] Apply same logic to bonus game

**User Experience:**
- Timer expires → Auto-submit → Show feedback → Display correct answer → Move to next question
- Clear visual feedback that time ran out
- No confusion about what the correct answer was
- Fair gameplay (0 points, reset streak)

---

**Updated:** November 14, 2025  
**Backend Status:** ✅ Complete  
**Frontend Status:** 🟡 Implementation Required
