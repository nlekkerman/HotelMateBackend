# Quiz Game API - Correct Answer in Response (NEW)

## 🆕 Important Update: Correct Answer Now Included in Response

The API now returns the **correct answer** in every submission response. This allows the frontend to display the correct answer when a player selects the wrong answer or runs out of time.

---

## 📡 Updated Submit Answer Response

### Endpoint
```http
POST /api/v1/entertainment/quiz-sessions/{session_id}/submit_answer/
```

### Response Structure (UPDATED)

```json
{
  "submission": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "question": 123,
    "question_number": 3,
    "question_text": "What is the capital of France?",
    "selected_answer": "London",
    "correct_answer": "Paris",
    "is_correct": false,
    "base_points": 10,
    "points_awarded": 0,
    "time_taken_seconds": 3,
    "multiplier_used": 1,
    "answered_at": "2025-11-13T10:00:05Z"
  },
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "score": 28,
    "consecutive_correct": 0,
    "current_multiplier": 1,
    "current_question_index": 3
  },
  "quiz_completed": false
}
```

### Key Changes

**NEW FIELD**: `correct_answer` in submission object

This field contains:
- For regular questions: The text of the correct answer from the database
- For math questions: The correct calculation result from `question_data`
- Always present, regardless of whether the player answered correctly or not

---

## 🎨 Frontend Implementation

### Display Correct Answer on Wrong Selection

```javascript
const handleSubmissionResponse = (response) => {
  const { submission, session } = response;
  
  if (!submission.is_correct) {
    // Player selected wrong answer
    showWrongAnswerFeedback({
      selected: submission.selected_answer,
      correct: submission.correct_answer,
      points: submission.points_awarded,
      multiplier_reset: true
    });
  } else if (submission.points_awarded === 0) {
    // Player got it right but timed out (5 seconds)
    showTimeoutFeedback({
      correct: submission.correct_answer,
      multiplier_reset: true
    });
  } else {
    // Player answered correctly in time
    showCorrectAnswerFeedback({
      points: submission.points_awarded,
      multiplier: submission.multiplier_used,
      next_multiplier: session.current_multiplier
    });
  }
};
```

---

## 📱 UI Examples

### 1. Wrong Answer Screen
```
┌─────────────────────────────────┐
│  ✗ Wrong Answer!                │
├─────────────────────────────────┤
│                                 │
│  Question:                      │
│  What is the capital of France? │
│                                 │
│  You selected: London           │
│  Correct answer: Paris          │
│                                 │
│  Points earned: 0               │
│  Multiplier reset to 1x         │
│                                 │
│  [Next Question]                │
│                                 │
└─────────────────────────────────┘
```

### 2. Timeout Screen (Still Correct but 0 Points)
```
┌─────────────────────────────────┐
│  ⏱️ Time's Up!                   │
├─────────────────────────────────┤
│                                 │
│  You took too long!             │
│  Time limit: 5 seconds          │
│                                 │
│  Correct answer: Paris          │
│                                 │
│  Points earned: 0 (timeout)     │
│  Streak broken - Reset to 1x    │
│                                 │
│  [Next Question]                │
│                                 │
└─────────────────────────────────┘
```

### 3. Correct Answer Screen (No Change)
```
┌─────────────────────────────────┐
│  ✓ Correct!                     │
├─────────────────────────────────┤
│                                 │
│  Time: 2 seconds                │
│  Base Points: 3                 │
│  Multiplier: 4x                 │
│  Points Earned: 12              │
│                                 │
│  🔥 Streak: 3 correct           │
│  Next multiplier: 8x            │
│                                 │
│  Total Score: 40                │
│                                 │
│  [Next Question]                │
│                                 │
└─────────────────────────────────┘
```

---

## 🔧 Response Scenarios

### Scenario 1: Wrong Answer
```json
{
  "submission": {
    "selected_answer": "London",
    "correct_answer": "Paris",
    "is_correct": false,
    "points_awarded": 0,
    "time_taken_seconds": 3
  }
}
```
**Display**: Show both selected and correct answer, emphasize the mistake

---

### Scenario 2: Timeout (5 seconds, but correct selection)
```json
{
  "submission": {
    "selected_answer": "Paris",
    "correct_answer": "Paris",
    "is_correct": true,
    "points_awarded": 0,
    "time_taken_seconds": 5
  }
}
```
**Display**: Show timeout message with correct answer for learning

---

### Scenario 3: Correct & Fast
```json
{
  "submission": {
    "selected_answer": "Paris",
    "correct_answer": "Paris",
    "is_correct": true,
    "points_awarded": 12,
    "time_taken_seconds": 2,
    "multiplier_used": 4
  }
}
```
**Display**: Celebrate success, show points calculation

---

### Scenario 4: Math Question (Wrong)
```json
{
  "submission": {
    "question_text": "What is 7 + 3?",
    "selected_answer": "12",
    "correct_answer": "10",
    "is_correct": false,
    "points_awarded": 0
  }
}
```
**Display**: Show calculation with correct result

---

## 💡 Frontend Tips

### 1. Visual Feedback Colors
```css
/* Correct answer */
.correct-answer {
  color: #10b981; /* green */
  font-weight: bold;
}

/* Wrong answer */
.wrong-answer {
  color: #ef4444; /* red */
  text-decoration: line-through;
}

/* Timeout */
.timeout {
  color: #f59e0b; /* orange */
}
```

### 2. Display Logic
```javascript
const renderAnswerFeedback = (submission) => {
  // Always show the correct answer for learning
  const correctAnswerElement = (
    <div className="correct-answer-display">
      <span className="label">Correct Answer:</span>
      <span className="answer">{submission.correct_answer}</span>
    </div>
  );
  
  if (!submission.is_correct) {
    // Wrong answer: show both
    return (
      <div className="feedback wrong">
        <h2>✗ Wrong Answer</h2>
        <div className="your-answer wrong-answer">
          You selected: {submission.selected_answer}
        </div>
        {correctAnswerElement}
        <div className="points">Points: 0</div>
        <div className="multiplier-reset">Streak broken - Back to 1x</div>
      </div>
    );
  } else if (submission.points_awarded === 0) {
    // Timeout: emphasize time limit
    return (
      <div className="feedback timeout">
        <h2>⏱️ Time's Up!</h2>
        <div className="timeout-message">
          You took {submission.time_taken_seconds} seconds (limit: 5s)
        </div>
        {correctAnswerElement}
        <div className="points">Points: 0 (timeout)</div>
        <div className="multiplier-reset">Streak broken - Back to 1x</div>
      </div>
    );
  } else {
    // Correct and on time: celebrate!
    return (
      <div className="feedback correct">
        <h2>✓ Correct!</h2>
        <div className="score-breakdown">
          <div>Base Points: {5 - submission.time_taken_seconds}</div>
          <div>Multiplier: {submission.multiplier_used}x</div>
          <div>Points Earned: {submission.points_awarded}</div>
        </div>
        <div className="streak">
          🔥 Next multiplier: {session.current_multiplier}x
        </div>
      </div>
    );
  }
};
```

### 3. Accessibility
```javascript
// Announce feedback to screen readers
const announceResult = (submission) => {
  const message = submission.is_correct
    ? `Correct! You earned ${submission.points_awarded} points`
    : `Wrong answer. The correct answer was ${submission.correct_answer}`;
  
  // Use ARIA live region
  document.getElementById('sr-announcement').textContent = message;
};
```

---

## 📊 Testing

Test all scenarios with the backend test:
```bash
python test_correct_answer_response.py
```

This validates:
- ✓ Correct answer returned for regular questions
- ✓ Correct answer returned for math questions
- ✓ Available for wrong answers
- ✓ Available for timeouts
- ✓ Matches database values

---

## 🎯 Summary

### What Changed
- **NEW**: `correct_answer` field in submission response
- **Always present**: Available for correct, wrong, and timeout scenarios
- **Works for all question types**: Regular questions and dynamic math

### Why This Matters
- **Better UX**: Players learn from mistakes
- **Transparency**: Always show what the right answer was
- **Educational**: Timeout players still see correct answer

### Frontend Action Items
- [ ] Update submission response handling
- [ ] Display correct answer on wrong selection
- [ ] Display correct answer on timeout
- [ ] Add visual distinction (colors, icons)
- [ ] Test all feedback scenarios

---

**The API now provides everything needed for complete answer feedback! 🎮✨**
