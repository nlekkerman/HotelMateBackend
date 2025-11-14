# Frontend Bug Fix Guide - Quiz Game

## 🔴 Issue Summary

Four critical frontend bugs preventing the quiz from working:

1. **400 Bad Request Error** - Missing required fields in API request
2. **"Correct answer: Unknown"** - Not displaying the correct answer from response
3. **Timeout Handling** - Need to submit special answer when time runs out
4. **Game Not Finishing** - Auto-completion now handled by backend after 50 questions

---

## ✅ Backend Auto-Completion (NEW!)

**The backend now automatically completes the game after 50 questions!**

When you submit the 50th answer:
- Backend detects all questions answered (5 categories × 10 questions)
- Automatically calls `session.complete_session()`
- Returns `game_completed: true` in response
- Session is marked as `is_completed: true`

**Frontend just needs to:**
1. Watch for `game_completed: true` in submit_answer response
2. Navigate to results/leaderboard screen
3. No need to manually call `complete_session` endpoint anymore

---

## ✅ Backend Confirmed Working

Test results show backend correctly returns:
```json
{
  "submission": {
    "id": "872335f2-b005-4378-8d90-1a41f7725ec8",
    "selected_answer": "Toronto",
    "correct_answer": "Ottawa",        ← Backend IS sending this
    "is_correct": false,
    "points_awarded": 0
  }
}
```

---

## 🐛 Bug #1: Missing Request Fields (400 Error)

### Current Broken Request
```javascript
// ❌ This causes 400 Bad Request
{
  session_id: "uuid",
  category_slug: "classic-trivia",
  question_id: 123,
  time_taken_seconds: 2
  // Missing: question_text ❌
  // Missing: selected_answer ❌
}
```

### Backend Error Response
```json
{
  "question_text": ["This field is required."],
  "selected_answer": ["This field is required."]
}
```

### ✅ Fixed Request
```javascript
{
  session_id: sessionId,
  category_slug: currentQuestion.category_slug,
  question_id: currentQuestion.id,           // Required (except math)
  question_text: currentQuestion.text,       // ✅ ADD THIS
  selected_answer: selectedAnswer.text,      // ✅ ADD THIS
  selected_answer_id: selectedAnswer.id,     // Optional but recommended
  time_taken_seconds: timeTaken,
  question_data: currentQuestion.question_data  // For math questions only
}
```

---

## 🐛 Bug #2: Timeout Handling

### Problem
When timer expires (>5 seconds), frontend tries to submit invalid data or doesn't submit at all.

### ✅ Backend Solution Implemented
Backend now accepts:
- `time_taken_seconds` up to 10 (grace period)
- `selected_answer: "TIMEOUT"` for expired timers
- Automatically gives 0 points and resets streak

### ✅ Frontend Fix Required

**When timer expires (hits 0 or goes negative):**
```javascript
// Auto-submit timeout answer
const handleTimeout = async () => {
  if (hasAnswered) return;
  
  console.log('⏰ Time expired! Auto-submitting timeout...');
  
  await quizGameAPI.submitAnswer({
    sessionId: session.id,
    categorySlug: currentCategory.slug,
    questionId: currentQuestion.id,
    questionText: currentQuestion.text,
    selectedAnswer: "TIMEOUT",          // ✅ Special value
    selectedAnswerId: null,
    timeTaken: 6,                       // ✅ Fixed value for timeout
    questionData: currentQuestion.question_data
  });
  
  setHasAnswered(true);
};
```

**Timer component should trigger this:**
```javascript
useEffect(() => {
  if (timeLeft <= 0 && !hasAnswered) {
    handleTimeout();
  }
}, [timeLeft, hasAnswered]);
```

---

## 🐛 Bug #3: Not Displaying Correct Answer

### Problem
Frontend receives `submission.correct_answer` but displays "Unknown"

### ✅ Fix
```javascript
// ❌ WRONG (probably doing this):
<p>Correct answer: {correctAnswer || "Unknown"}</p>

// ✅ CORRECT (use response data):
<p>Correct answer: {result.submission.correct_answer}</p>
```

---

## 🎮 Bonus Game Timeout Handling

**Same logic applies for bonus/memory game:**
- When timer expires, submit with `selected_answer: "TIMEOUT"`
- Backend will record 0 points and reset any streaks/multipliers
- Display timeout feedback to user

---

## 📝 Files to Fix

### 1. `quizGameAPI.js` (Line ~174)

**Current (broken):**
```javascript
export const submitAnswer = async (answerData) => {
  const response = await axios.post(
    `${API_BASE_URL}/quiz/game/submit_answer/`,
    {
      session_id: answerData.sessionId,
      category_slug: answerData.categorySlug,
      question_id: answerData.questionId,
      selected_answer_id: answerData.selectedAnswerId,
      time_taken_seconds: answerData.timeTaken
    }
  );
  return response.data;
};
```

**✅ Fixed:**
```javascript
export const submitAnswer = async (answerData) => {
  const response = await axios.post(
    `${API_BASE_URL}/quiz/game/submit_answer/`,
    {
      session_id: answerData.sessionId,
      category_slug: answerData.categorySlug,
      question_id: answerData.questionId,
      question_text: answerData.questionText,        // ✅ ADD
      selected_answer: answerData.selectedAnswer,    // ✅ ADD
      selected_answer_id: answerData.selectedAnswerId,
      time_taken_seconds: answerData.timeTaken,
      question_data: answerData.questionData         // For math
    }
  );
  return response.data;
};
```

---

### 2. `useQuizGame.js` (Line ~273)

**Current (broken):**
```javascript
const submitAnswer = async (answerId) => {
  try {
    const result = await quizGameAPI.submitAnswer({
      sessionId: session.id,
      categorySlug: currentCategory.slug,
      questionId: currentQuestion.id,
      selectedAnswerId: answerId,
      timeTaken: calculateTimeTaken()
    });
    // Handle result...
  } catch (error) {
    console.error('Failed to submit:', error);
  }
};
```

**✅ Fixed:**
```javascript
const submitAnswer = async (answerId, answerText) => {
  try {
    const result = await quizGameAPI.submitAnswer({
      sessionId: session.id,
      categorySlug: currentCategory.slug,
      questionId: currentQuestion.id,
      questionText: currentQuestion.text,              // ✅ ADD
      selectedAnswer: answerText,                      // ✅ ADD
      selectedAnswerId: answerId,
      timeTaken: calculateTimeTaken(),
      questionData: currentQuestion.question_data      // For math
    });
    
    // ✅ Store submission result for display
    setLastSubmission(result.submission);
    
    // Handle result...
  } catch (error) {
    console.error('Failed to submit:', error);
  }
};
```

---

### 3. `useQuizGame.js` (Line ~227)

**Update handleAnswerSelect:**
```javascript
const handleAnswerSelect = async (answerId, answerText) => {  // ✅ Add answerText param
  if (isSubmitting || hasAnswered) return;
  
  setIsSubmitting(true);
  setSelectedAnswerId(answerId);
  
  try {
    await submitAnswer(answerId, answerText);  // ✅ Pass answerText
  } finally {
    setIsSubmitting(false);
  }
};
```

---

### 4. Timer Component / `useQuizGame.js`

**Add timeout handler:**
```javascript
// In useQuizGame.js or wherever timer is managed
const handleTimeout = async () => {
  if (hasAnswered || isSubmitting) return;
  
  console.log('⏰ Time expired! Auto-submitting timeout...');
  setIsSubmitting(true);
  
  try {
    const result = await quizGameAPI.submitAnswer({
      sessionId: session.id,
      categorySlug: currentQuestion.category_slug,
      questionId: currentQuestion.id,
      questionText: currentQuestion.text,
      selectedAnswer: "TIMEOUT",          // ✅ Special timeout value
      selectedAnswerId: null,
      timeTaken: 6,                       // ✅ Fixed value > 5 for timeout
      questionData: currentQuestion.question_data
    });
    
    setLastSubmission(result.submission);
    setHasAnswered(true);
    
    // Show timeout feedback
    showTimeoutFeedback();
    
    // Auto-advance after delay
    setTimeout(() => {
      moveToNextQuestion();
    }, 2500);
    
  } catch (error) {
    console.error('Timeout submission failed:', error);
  } finally {
    setIsSubmitting(false);
  }
};

// Watch timer and trigger timeout
useEffect(() => {
  if (timeLeft <= 0 && !hasAnswered && !isSubmitting) {
    handleTimeout();
  }
}, [timeLeft, hasAnswered, isSubmitting]);
```

---

### 5. `QuizQuestion.jsx` (Line ~95)

**Current (broken):**
```javascript
<button
  onClick={() => handleAnswerSelect(answer.id)}
  className="answer-button"
>
  {answer.text}
</button>
```

**✅ Fixed:**
```javascript
<button
  onClick={() => handleAnswerSelect(answer.id, answer.text)}  // ✅ Pass text
  className="answer-button"
>
  {answer.text}
</button>
```

---

### 6. Result Display Component

**Create or update answer feedback component:**

```javascript
{lastSubmission && (
  <div className={`answer-feedback ${lastSubmission.is_correct ? 'correct' : 'wrong'}`}>
    <div className="feedback-header">
      {lastSubmission.selected_answer === 'TIMEOUT' ? (
        <h3>⏰ TIME'S UP!</h3>
      ) : lastSubmission.is_correct ? (
        <h3>✅ CORRECT!</h3>
      ) : (
        <h3>❌ WRONG!</h3>
      )}
    </div>
    
    <div className="feedback-details">
      {lastSubmission.selected_answer === 'TIMEOUT' ? (
        <p className="timeout-message">⏰ You ran out of time!</p>
      ) : (
        <p>You selected: <strong>{lastSubmission.selected_answer}</strong></p>
      )}
      <p>Correct answer: <strong>{lastSubmission.correct_answer}</strong></p>  {/* ✅ THIS */}
      <p>Time: {lastSubmission.time_taken_seconds}s</p>
      <p>Points earned: <strong>{lastSubmission.points_awarded}</strong></p>
      {lastSubmission.was_turbo_active && (
        <p className="turbo-badge">🔥 TURBO MODE ACTIVE!</p>
      )}
      {lastSubmission.selected_answer === 'TIMEOUT' && (
        <p className="streak-lost">💔 Streak reset!</p>
      )}
    </div>
  </div>
)}
```

---

## 🧪 Testing Steps

### 1. Test Answer Submission
```javascript
// In browser console:
const testAnswer = {
  sessionId: "your-session-id",
  categorySlug: "classic-trivia",
  questionId: 123,
  questionText: "What is 2 + 2?",        // ✅ Must include
  selectedAnswer: "4",                   // ✅ Must include
  selectedAnswerId: 1,
  timeTaken: 2
};

// Should return 200 OK with correct_answer in response
```

### 2. Verify Response Structure
```javascript
// Expected response:
{
  "success": true,
  "submission": {
    "id": "uuid",
    "question_text": "What is 2 + 2?",
    "selected_answer": "4",
    "correct_answer": "4",              // ✅ Check this exists
    "is_correct": true,
    "points_awarded": 4,
    "time_taken_seconds": 2,
    "was_turbo_active": false,
    "answered_at": "2025-11-14T10:00:00Z"
  },
  "session_updated": {
    "score": 4,
    "consecutive_correct": 1,
    "is_turbo_active": false
  }
}
```

---

## 📊 Backend API Reference

### Submit Answer Endpoint

**URL:** `POST /api/entertainment/quiz/game/submit_answer/`

**Required Headers:**
```
Content-Type: application/json
```

**Required Body Fields:**
```json
{
  "session_id": "uuid (string)",
  "category_slug": "string",
  "question_text": "string - REQUIRED",
  "selected_answer": "string - REQUIRED (use 'TIMEOUT' if timer expired)",
  "time_taken_seconds": "integer (0-10, use 6 for timeout)"
}
```

**Optional Fields:**
```json
{
  "question_id": "integer (required for non-math)",
  "selected_answer_id": "integer",
  "question_data": {
    "num1": 5,
    "num2": 7,
    "operator": "*",
    "correct_answer": 35
  }
}
```

---

## 🎯 Expected Behavior After Fix

### Success Flow
1. User clicks answer button
2. Frontend sends complete request with `question_text` and `selected_answer`
3. Backend returns 200 OK with `correct_answer` in response
4. UI displays feedback with correct answer visible
5. Score updates correctly

### Error Handling
```javascript
try {
  const result = await submitAnswer(answerId, answerText);
  setLastSubmission(result.submission);
} catch (error) {
  if (error.response?.status === 400) {
    console.error('Missing fields:', error.response.data);
    alert('Error submitting answer. Please try again.');
  }
}
```

---

## 🔍 Debugging Tips

### Check Request Payload
```javascript
// Add before axios.post:
console.log('📤 Submitting answer:', {
  session_id: answerData.sessionId,
  category_slug: answerData.categorySlug,
  question_text: answerData.questionText,      // Should NOT be undefined
  selected_answer: answerData.selectedAnswer,  // Should NOT be undefined
  time_taken_seconds: answerData.timeTaken
});
```

### Check Response
```javascript
// Add after receiving response:
console.log('📥 Response:', result);
console.log('✅ Correct answer:', result.submission.correct_answer);  // Should show value
```

### Network Tab
- Open DevTools → Network
- Filter: `submit_answer`
- Check Request Payload has `question_text` and `selected_answer`
- Check Response contains `correct_answer` with actual value (not null/undefined)

---

## ⚡ Quick Fix Checklist

- [ ] Add `question_text` to submitAnswer API call
- [ ] Add `selected_answer` to submitAnswer API call
- [ ] Pass `answerText` parameter through the call chain
- [ ] Update `QuizQuestion.jsx` onClick to pass `answer.text`
- [ ] Display `submission.correct_answer` in feedback UI
- [ ] **Add timeout handler** that submits `"TIMEOUT"` when timer expires
- [ ] **Add useEffect** to trigger timeout submission at 0 seconds
- [ ] Test with both correct and wrong answers
- [ ] **Test timeout scenario** (let timer expire without selecting)
- [ ] Test with math questions (dynamic generation)
- [ ] Verify no 400 errors in console
- [ ] Verify correct answer displays properly
- [ ] **Verify timeout shows 0 points and correct answer**

---

## 📞 Questions?

If issues persist after these fixes:
1. Check browser console for errors
2. Verify `currentQuestion` object has `.text` property
3. Verify `answer` object has `.text` property
4. Check Network tab for actual request/response data
5. Ensure no middleware is stripping fields from request

---

**Last Updated:** November 14, 2025  
**Backend Test:** ✅ Passing (correct_answer properly returned)  
**Frontend Status:** 🔴 Needs fixes described above
