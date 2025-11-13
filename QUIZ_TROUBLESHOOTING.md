# Quiz Game - Frontend Troubleshooting Guide

## Common Issue: `404 Not Found - quiz-sessions/undefined/submit_answer/`

### Problem
Frontend is sending requests to:
```
POST /api/entertainment/quiz-sessions/undefined/submit_answer/
```

This returns **404 Not Found** because `undefined` is not a valid session ID.

### Root Cause
The session ID is `undefined`, which means:
1. The frontend hasn't created a session yet, OR
2. The session creation response wasn't stored properly, OR
3. The session ID variable wasn't initialized before submitting answers

---

## Correct Flow

### Step 1: Create a Quiz Session

**Before any gameplay**, you MUST create a session:

```javascript
// Create session first
const response = await fetch('/api/entertainment/quiz-sessions/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    quiz_slug: 'level-1-classic',  // Required
    hotel_identifier: 'killarney',  // Required
    player_name: 'John Doe',  // Required
    room_number: '305',  // Optional - required for tournament mode
    is_practice_mode: false,  // Optional - default false
    external_player_id: 'player123'  // Optional
  })
});

const sessionData = await response.json();
const sessionId = sessionData.id;  // ← THIS IS THE UUID YOU NEED

// Store it for later use
localStorage.setItem('currentQuizSessionId', sessionId);
```

**Response Example:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "hotel_identifier": "killarney",
  "quiz": {
    "id": 1,
    "slug": "level-1-classic",
    "title": "Level 1: Classic Trivia",
    "level": 1,
    "max_questions": 10
  },
  "player_name": "John Doe",
  "room_number": "305",
  "is_practice_mode": false,
  "score": 0,
  "started_at": "2025-11-13T19:45:00Z",
  "finished_at": null,
  "is_completed": false,
  "time_spent_seconds": 0,
  "current_question_index": 0,
  "submission_count": 0,
  "consecutive_correct": 0,
  "current_multiplier": 1
}
```

### Step 2: Submit Answers Using That Session ID

Now use the session ID from Step 1:

```javascript
// Get the stored session ID
const sessionId = localStorage.getItem('currentQuizSessionId');

// Verify it exists
if (!sessionId) {
  console.error('No active session! Create a session first.');
  return;
}

// Submit answer
const response = await fetch(
  `/api/entertainment/quiz-sessions/${sessionId}/submit_answer/`,
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session: sessionId,
      question: 'uuid-of-question',  // For regular questions
      selected_answer: 'Paris',
      time_taken_seconds: 3
    })
  }
);

const result = await response.json();
```

---

## Complete React Component Example

```jsx
import React, { useState, useEffect } from 'react';

function QuizGame({ quizSlug, hotelId, playerName, roomNumber, isPractice }) {
  const [sessionId, setSessionId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [score, setScore] = useState(0);
  const [multiplier, setMultiplier] = useState(1);
  const [timeLeft, setTimeLeft] = useState(5);
  const [isAnswered, setIsAnswered] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState(null);

  // Step 1: Initialize session and get 10 random questions
  useEffect(() => {
    initializeQuizSession();
  }, []);

  // Step 2: Timer for each question
  useEffect(() => {
    if (timeLeft > 0 && !isAnswered && !isComplete) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0 && !isAnswered) {
      // Time's up - auto-submit with no answer
      handleTimeout();
    }
  }, [timeLeft, isAnswered, isComplete]);

  async function initializeQuizSession() {
    try {
      const response = await fetch('/api/entertainment/quiz-sessions/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quiz_slug: quizSlug,
          hotel_identifier: hotelId,
          player_name: playerName,
          room_number: roomNumber || null,
          is_practice_mode: isPractice
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to create session: ${response.status}`);
      }

      const data = await response.json();
      setSessionId(data.id);
      setQuestions(data.questions);  // 10 random questions
      setMultiplier(data.current_multiplier);
      console.log('Session created with', data.questions.length, 'questions');
    } catch (err) {
      setError('Failed to start quiz: ' + err.message);
      console.error(err);
    }
  }

  async function submitAnswer(selectedAnswer) {
    if (!sessionId || isAnswered) return;

    setIsAnswered(true);
    const timeTaken = 5 - timeLeft;

    try {
      const response = await fetch(
        `/api/entertainment/quiz-sessions/${sessionId}/submit_answer/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session: sessionId,
            question: questions[currentQuestionIndex].id,
            selected_answer: selectedAnswer,
            time_taken_seconds: timeTaken
          })
        }
      );

      if (!response.ok) {
        throw new Error(`Submit failed: ${response.status}`);
      }

      const result = await response.json();
      
      // Update score and multiplier
      setScore(prev => prev + result.points_awarded);
      setMultiplier(result.multiplier_used);

      // Show feedback with correct answer
      if (result.is_correct) {
        setFeedback({
          type: 'correct',
          message: `Correct! +${result.points_awarded} points`,
          multiplier: result.multiplier_used
        });
      } else {
        setFeedback({
          type: 'wrong',
          message: `Wrong! The answer was: ${result.correct_answer}`,
          correctAnswer: result.correct_answer
        });
      }

      // Move to next question after 2 seconds
      setTimeout(() => {
        moveToNextQuestion();
      }, 2000);

    } catch (err) {
      setError('Failed to submit answer: ' + err.message);
      console.error(err);
    }
  }

  async function handleTimeout() {
    if (!sessionId || isAnswered) return;

    setIsAnswered(true);

    try {
      const response = await fetch(
        `/api/entertainment/quiz-sessions/${sessionId}/submit_answer/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session: sessionId,
            question: questions[currentQuestionIndex].id,
            selected_answer: '',  // No answer
            time_taken_seconds: 5  // Full time used
          })
        }
      );

      const result = await response.json();
      
      // Show timeout feedback with correct answer
      setFeedback({
        type: 'timeout',
        message: `Time's up! The answer was: ${result.correct_answer}`,
        correctAnswer: result.correct_answer
      });

      // Multiplier is reset to 1 on timeout
      setMultiplier(1);

      setTimeout(() => {
        moveToNextQuestion();
      }, 2000);

    } catch (err) {
      console.error('Timeout submission failed:', err);
      moveToNextQuestion();
    }
  }

  async function moveToNextQuestion() {
    setFeedback(null);
    setIsAnswered(false);
    setTimeLeft(5);

    if (currentQuestionIndex + 1 >= questions.length) {
      // Quiz complete
      await completeSession();
    } else {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  }

  async function completeSession() {
    try {
      const response = await fetch(
        `/api/entertainment/quiz-sessions/${sessionId}/complete/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        }
      );

      if (!response.ok) {
        throw new Error(`Complete failed: ${response.status}`);
      }

      const result = await response.json();
      setIsComplete(true);
      console.log('Quiz completed:', result);
    } catch (err) {
      console.error('Failed to complete session:', err);
      setIsComplete(true);  // Show results anyway
    }
  }

  if (error) {
    return (
      <div className="quiz-error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  if (!sessionId || questions.length === 0) {
    return <div className="quiz-loading">Loading quiz...</div>;
  }

  if (isComplete) {
    return (
      <div className="quiz-complete">
        <h2>Quiz Complete!</h2>
        <p className="final-score">Final Score: {score}</p>
        <p>Questions Answered: {questions.length}</p>
        <button onClick={() => window.location.href = '/leaderboard'}>
          View Leaderboard
        </button>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className="quiz-game">
      <div className="quiz-header">
        <div className="score">Score: {score}</div>
        <div className="multiplier">Multiplier: {multiplier}x</div>
        <div className="progress">
          Question {currentQuestionIndex + 1} / {questions.length}
        </div>
        <div className={`timer ${timeLeft <= 2 ? 'warning' : ''}`}>
          Time: {timeLeft}s
        </div>
      </div>

      <div className="question-container">
        <h2 className="question-text">{currentQuestion.text}</h2>
        
        {currentQuestion.image_url && (
          <img 
            src={currentQuestion.image_url} 
            alt="Question" 
            className="question-image"
          />
        )}

        <div className="answers-grid">
          {currentQuestion.answers.map((answer) => (
            <button
              key={answer.id}
              className={`answer-button ${isAnswered ? 'disabled' : ''}`}
              onClick={() => submitAnswer(answer.text)}
              disabled={isAnswered}
            >
              {answer.text}
            </button>
          ))}
        </div>

        {feedback && (
          <div className={`feedback feedback-${feedback.type}`}>
            <p className="feedback-message">{feedback.message}</p>
            {feedback.multiplier && feedback.multiplier > 1 && (
              <p className="streak-bonus">
                🔥 {feedback.multiplier}x Streak!
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default QuizGame;
```

## CSS Styles for Feedback

```css
.feedback {
  padding: 20px;
  margin-top: 20px;
  border-radius: 8px;
  text-align: center;
  animation: slideIn 0.3s ease-out;
}

.feedback-correct {
  background: #4caf50;
  color: white;
}

.feedback-wrong {
  background: #f44336;
  color: white;
}

.feedback-timeout {
  background: #ff9800;
  color: white;
}

.feedback-message {
  font-size: 1.2em;
  font-weight: bold;
  margin: 0;
}

.streak-bonus {
  font-size: 1.5em;
  margin-top: 10px;
  animation: pulse 0.5s ease-in-out;
}

.timer.warning {
  color: #f44336;
  animation: pulse 0.5s infinite;
}

@keyframes slideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
```

---

## Common Mistakes & Fixes

### ❌ Mistake 1: Not creating session before gameplay
```javascript
// WRONG - trying to submit without session
const sessionId = undefined;  // Never set!
fetch(`/api/quiz-sessions/${sessionId}/submit_answer/`);  // 404 Error
```

**✅ Fix:** Always create session first
```javascript
const sessionResponse = await createSession();
const sessionId = sessionResponse.id;
```

---

### ❌ Mistake 2: Not waiting for session creation
```javascript
// WRONG - race condition
let sessionId;
createSession().then(data => sessionId = data.id);
submitAnswer();  // sessionId is still undefined!
```

**✅ Fix:** Use async/await properly
```javascript
const sessionData = await createSession();
const sessionId = sessionData.id;
await submitAnswer(sessionId);
```

---

### ❌ Mistake 3: Using wrong variable name
```javascript
// WRONG - typo in property name
const response = await createSession();
const sessionId = response.session_id;  // Doesn't exist!
```

**✅ Fix:** Use correct property name
```javascript
const response = await createSession();
const sessionId = response.id;  // Correct property
```

---

## Debugging Checklist

When you see `undefined` in the URL:

1. ✅ **Check session creation response:**
   ```javascript
   const response = await createSession();
   console.log('Session response:', response);
   console.log('Session ID:', response.id);
   ```

2. ✅ **Verify ID is stored:**
   ```javascript
   setSessionId(response.id);
   console.log('Stored session ID:', sessionId);
   ```

3. ✅ **Check ID before submitting:**
   ```javascript
   console.log('About to submit with ID:', sessionId);
   if (!sessionId) {
     console.error('Session ID is missing!');
     return;
   }
   ```

4. ✅ **Inspect the actual HTTP request:**
   - Open browser DevTools → Network tab
   - Look for the submit_answer request
   - Check the URL - it should be: `/api/entertainment/quiz-sessions/a1b2c3d4-.../submit_answer/`
   - If you see `undefined`, the session ID wasn't set

---

## Complete API Reference

### 1. Get Available Quizzes
```
GET /api/entertainment/quizzes/
```
**Query params:** `difficulty`, `category`, `is_daily`

**Response:**
```json
[
  {
    "id": 1,
    "slug": "classic-trivia-easy",
    "title": "Classic Trivia - Easy",
    "description": "Test your general knowledge",
    "difficulty_level": 1,
    "is_active": true,
    "max_questions": 10,
    "time_per_question": 5
  }
]
```

### 2. Create Session (Start Game)
```
POST /api/entertainment/quiz-sessions/
```

**Request Body:**
```json
{
  "quiz_slug": "classic-trivia-easy",
  "hotel_identifier": "killarney",
  "player_name": "John Doe",
  "room_number": "305",
  "is_practice_mode": false
}
```

**Response (includes 10 random questions):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "hotel_identifier": "killarney",
  "quiz": {
    "slug": "classic-trivia-easy",
    "title": "Classic Trivia - Easy",
    "level": 1,
    "max_questions": 10
  },
  "player_name": "John Doe",
  "room_number": "305",
  "is_practice_mode": false,
  "score": 0,
  "consecutive_correct": 0,
  "current_multiplier": 1,
  "questions": [
    {
      "id": "q-uuid-1",
      "text": "What is the capital of France?",
      "image_url": null,
      "base_points": 10,
      "answers": [
        {"id": "a1", "text": "Paris"},
        {"id": "a2", "text": "London"},
        {"id": "a3", "text": "Berlin"},
        {"id": "a4", "text": "Madrid"}
      ]
    }
    // ... 9 more questions
  ]
}
```

### 3. Generate Math Question (Level 4 Only)
```
POST /api/entertainment/quizzes/dynamic-math-expert/generate_math_question/
```

**Response:**
```json
{
  "question_text": "What is 7 × 8?",
  "answers": ["56", "54", "58", "49"],
  "question_data": {
    "num1": 7,
    "num2": 8,
    "operation": "×",
    "correct_answer": 56
  },
  "base_points": 10,
  "time_limit": 5
}
```

### 4. Submit Answer
```
POST /api/entertainment/quiz-sessions/{session_id}/submit_answer/
```

**Request Body (Regular Questions):**
```json
{
  "session": "session-uuid",
  "question": "question-uuid",
  "selected_answer": "Paris",
  "time_taken_seconds": 3
}
```

**Request Body (Math Questions):**
```json
{
  "session": "session-uuid",
  "question_text": "What is 7 × 8?",
  "question_data": {
    "num1": 7,
    "num2": 8,
    "operation": "×",
    "correct_answer": 56
  },
  "selected_answer": "56",
  "time_taken_seconds": 4
}
```

**Response:**
```json
{
  "id": "submission-uuid",
  "question": "question-uuid",
  "selected_answer": "Paris",
  "correct_answer": "Paris",
  "is_correct": true,
  "base_points": 10,
  "points_awarded": 30,
  "multiplier_used": 2,
  "time_taken_seconds": 3
}
```

### 5. Complete Session
```
POST /api/entertainment/quiz-sessions/{session_id}/complete/
```

**Response:**
```json
{
  "id": "session-uuid",
  "score": 150,
  "is_completed": true,
  "time_spent_seconds": 45,
  "duration_formatted": "45s"
}
```

### 6. Get Leaderboards
```
GET /api/entertainment/quiz-sessions/general_leaderboard/?quiz=classic-trivia-easy&hotel=killarney
GET /api/entertainment/quiz-sessions/tournament_leaderboard/?quiz=classic-trivia-easy&hotel=killarney
```

**Response:**
```json
{
  "leaderboard_type": "general",
  "results": [
    {
      "player_name": "John Doe",
      "room_number": "305",
      "score": 150,
      "time_spent_seconds": 45,
      "is_practice_mode": false,
      "finished_at": "2025-11-13T20:00:00Z"
    }
  ]
}
```

---

## Session Lifecycle

```
1. User clicks "Start Quiz"
   ↓
2. Frontend calls POST /quiz-sessions/
   ↓
3. Backend creates session with UUID
   ↓
4. Frontend receives: { id: "a1b2c3d4-..." }
   ↓
5. Frontend stores: sessionId = response.id
   ↓
6. User answers questions
   ↓
7. Frontend calls POST /quiz-sessions/{sessionId}/submit_answer/
   (Repeat for each question)
   ↓
8. After 10 questions, frontend calls POST /quiz-sessions/{sessionId}/complete/
   ↓
9. Quiz ends, show results/leaderboard
```

---

## Testing Your Fix

1. **Test session creation:**
   ```javascript
   const session = await createSession();
   console.assert(session.id, 'Session ID should exist');
   console.assert(session.id !== 'undefined', 'Session ID should not be string "undefined"');
   ```

2. **Test answer submission:**
   ```javascript
   const sessionId = session.id;
   const url = `/api/entertainment/quiz-sessions/${sessionId}/submit_answer/`;
   console.log('Submitting to URL:', url);
   // Should print: /api/entertainment/quiz-sessions/a1b2c3d4-.../submit_answer/
   // NOT: /api/entertainment/quiz-sessions/undefined/submit_answer/
   ```

3. **Monitor browser console:**
   - No errors about undefined
   - All URLs contain valid UUIDs
   - HTTP status codes are 200/201, not 404

---

## Need More Help?

Check these documentation files:
- **QUIZ_FRONTEND_GUIDE.md** - Complete integration guide
- **QUIZ_GAME_API.md** - Detailed API reference
- **QUIZ_CORRECT_ANSWER_UPDATE.md** - Correct answer feedback feature

**Backend Logs:**
If you see this error in Django logs:
```
Not Found: /api/entertainment/quiz-sessions/undefined/submit_answer/
```

The problem is **definitely on the frontend** - the session ID wasn't properly stored or passed.
