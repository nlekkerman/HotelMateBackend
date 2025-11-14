# Quiz Correct Answer API Response

## Endpoint
`POST /api/entertainment/quiz/game/submit_answer/`

## Response Structure

```json
{
  "success": true,
  "submission": {
    "id": "uuid-here",
    "category": 1,
    "question_text": "What is 2 + 2?",
    "selected_answer": "4",
    "correct_answer": "4",
    "is_correct": true,
    "time_taken_seconds": 2,
    "was_turbo_active": false,
    "points_awarded": 4,
    "answered_at": "2025-11-14T10:30:00Z"
  },
  "session_updated": {
    "score": 4,
    "consecutive_correct": 1,
    "is_turbo_active": false
  }
}
```

## Frontend Usage Examples

### 1. Show Correct Answer After Wrong Answer

```javascript
const response = await submitAnswer(answerData);

if (response.submission.is_correct) {
  showMessage("Correct! ✓");
} else {
  showMessage(`Wrong! The correct answer was: ${response.submission.correct_answer}`);
}
```

### 2. Display Feedback with Comparison

```javascript
const { submission } = response;

if (!submission.is_correct) {
  displayFeedback({
    yourAnswer: submission.selected_answer,
    correctAnswer: submission.correct_answer,
    points: submission.points_awarded
  });
}
```

### 3. Review Screen at End of Game

```javascript
submissions.forEach(sub => {
  console.log(`Q: ${sub.question_text}`);
  console.log(`Your answer: ${sub.selected_answer}`);
  console.log(`Correct answer: ${sub.correct_answer}`);
  console.log(`Result: ${sub.is_correct ? '✓' : '✗'}`);
});
```

## Key Fields

- `correct_answer` - The correct answer text (always included in response)
- `is_correct` - Boolean indicating if the answer was correct
- `points_awarded` - Points earned for this answer
- `selected_answer` - The answer the user selected
