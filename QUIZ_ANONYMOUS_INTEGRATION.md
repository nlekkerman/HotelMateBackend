# Quiz Game - Anonymous Play Integration Guide

## 🎯 Overview

The quiz game is now **fully anonymous** with no hotel or room number tracking. Players can enjoy:
- **Casual Play**: Practice and play for fun
- **Tournament Mode**: Compete on tournament leaderboard

## 🔑 Key Changes

### ✅ Removed
- ❌ `hotel_identifier` - No hotel tracking
- ❌ `room_number` - No room validation
- ❌ `is_practice_mode` - Replaced with simpler system

### ✅ Added
- ✨ `is_tournament` - Boolean flag to distinguish tournament vs casual play

---

## 📡 API Endpoints

### 1. List Available Quizzes
```http
GET /api/entertainment/quizzes/
```

**Response:**
```json
[
  {
    "id": 1,
    "slug": "classic-trivia-easy",
    "title": "Classic Trivia - Easy",
    "difficulty_level": 1,
    "difficulty_display": "Level 1: Classic Trivia",
    "max_questions": 10,
    "time_per_question": 5,
    "is_active": true
  }
]
```

---

### 2. Create Quiz Session (Start Game)

```http
POST /api/entertainment/quiz-sessions/
```

**Request Body - Casual Play:**
```json
{
  "quiz_slug": "classic-trivia-easy",
  "player_name": "Alice",
  "is_tournament": false
}
```

**Request Body - Tournament Mode:**
```json
{
  "quiz_slug": "classic-trivia-easy",
  "player_name": "Bob",
  "is_tournament": true
}
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "quiz": {
    "slug": "classic-trivia-easy",
    "title": "Classic Trivia - Easy",
    "difficulty_level": 1,
    "max_questions": 10
  },
  "player_name": "Alice",
  "is_tournament": false,
  "score": 0,
  "started_at": "2025-11-13T20:00:00Z",
  "is_completed": false,
  "current_multiplier": 1,
  "consecutive_correct": 0,
  "questions": [
    {
      "id": 1,
      "text": "What is the capital of France?",
      "order": 0,
      "base_points": 5,
      "answers": [
        {"id": 1, "text": "Paris", "order": 0},
        {"id": 2, "text": "London", "order": 1},
        {"id": 3, "text": "Berlin", "order": 2},
        {"id": 4, "text": "Madrid", "order": 3}
      ]
    }
    // ... 9 more questions
  ]
}
```

---

### 3. Submit Answer

```http
POST /api/entertainment/quiz-sessions/{session_id}/submit_answer/
```

**Request Body:**
```json
{
  "session": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "question": 1,
  "selected_answer": "Paris",
  "selected_answer_id": 1,
  "time_taken_seconds": 2
}
```

**Response:**
```json
{
  "submission": {
    "id": "sub-uuid",
    "is_correct": true,
    "points_awarded": 6,
    "base_points": 5,
    "time_taken_seconds": 2,
    "multiplier_used": 2
  },
  "session": {
    "score": 6,
    "current_multiplier": 4,
    "consecutive_correct": 2,
    "current_question_index": 1
  },
  "quiz_completed": false
}
```

---

### 4. Generate Math Question (Level 4 Only)

```http
POST /api/entertainment/quizzes/{slug}/generate_math_question/
```

**Response:**
```json
{
  "question_text": "What is 7 + 3?",
  "answers": ["10", "8", "12", "9"],
  "question_data": {
    "num1": 7,
    "num2": 3,
    "operation": "+",
    "correct_answer": "10"
  },
  "base_points": 10,
  "time_limit": 5
}
```

---

### 5. Complete Session

```http
POST /api/entertainment/quiz-sessions/{session_id}/complete/
```

**Response:**
```json
{
  "message": "Session completed",
  "session": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "score": 280,
    "is_completed": true,
    "time_spent_seconds": 45,
    "duration_formatted": "45s",
    "finished_at": "2025-11-13T20:05:00Z"
  }
}
```

---

## 🏆 Leaderboards

### All-Time Leaderboard (All Players)
Shows **all completed sessions** - both casual and tournament.

```http
GET /api/entertainment/quiz-sessions/all_time_leaderboard/?quiz={slug}&period={period}&limit={limit}
```

**Query Parameters:**
- `quiz` (required): Quiz slug
- `period` (optional): `daily`, `weekly`, `all` (default: `all`)
- `limit` (optional): Number of results (default: 50)

**Response:**
```json
{
  "quiz": "classic-trivia-easy",
  "period": "all",
  "leaderboard_type": "all_time",
  "description": "All players (casual + tournament)",
  "count": 10,
  "leaderboard": [
    {
      "rank": 1,
      "player_name": "Alice",
      "score": 300,
      "time_spent_seconds": 40,
      "duration_formatted": "40s",
      "finished_at": "2025-11-13T20:00:00Z",
      "is_tournament": true
    },
    {
      "rank": 2,
      "player_name": "Bob",
      "score": 280,
      "time_spent_seconds": 45,
      "duration_formatted": "45s",
      "finished_at": "2025-11-13T20:05:00Z",
      "is_tournament": false
    }
  ]
}
```

---

### Tournament Leaderboard (Winners Only)
Shows **only tournament sessions** (`is_tournament: true`).

```http
GET /api/entertainment/quiz-sessions/tournament_leaderboard/?quiz={slug}&period={period}&limit={limit}
```

**Query Parameters:**
- `quiz` (required): Quiz slug
- `period` (optional): `daily`, `weekly`, `all` (default: `all`)
- `limit` (optional): Number of results (default: 50)

**Response:**
```json
{
  "quiz": "classic-trivia-easy",
  "period": "daily",
  "leaderboard_type": "tournament",
  "description": "Tournament players only",
  "count": 5,
  "leaderboard": [
    {
      "rank": 1,
      "player_name": "Charlie",
      "score": 320,
      "time_spent_seconds": 38,
      "duration_formatted": "38s",
      "finished_at": "2025-11-13T21:00:00Z",
      "is_tournament": true
    }
  ]
}
```

---

## 🎮 Frontend Implementation

### Complete React Example

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = '/api/entertainment';

function QuizGame() {
  const [quizzes, setQuizzes] = useState([]);
  const [selectedQuiz, setSelectedQuiz] = useState(null);
  const [playerName, setPlayerName] = useState('');
  const [isTournament, setIsTournament] = useState(false);
  const [session, setSession] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [score, setScore] = useState(0);
  const [multiplier, setMultiplier] = useState(1);
  const [timeLeft, setTimeLeft] = useState(5);
  const [isComplete, setIsComplete] = useState(false);

  // 1. Load available quizzes
  useEffect(() => {
    loadQuizzes();
  }, []);

  const loadQuizzes = async () => {
    const { data } = await axios.get(`${API_BASE}/quizzes/`);
    setQuizzes(data.filter(q => q.is_active));
  };

  // 2. Start quiz
  const startQuiz = async () => {
    if (!playerName || !selectedQuiz) {
      alert('Please enter your name and select a quiz');
      return;
    }

    try {
      const { data } = await axios.post(`${API_BASE}/quiz-sessions/`, {
        quiz_slug: selectedQuiz.slug,
        player_name: playerName,
        is_tournament: isTournament
      });

      setSession(data);
      setScore(data.score);
      setMultiplier(data.current_multiplier);
      setCurrentQuestionIndex(0);
      setTimeLeft(selectedQuiz.time_per_question || 5);
    } catch (error) {
      console.error('Failed to start quiz:', error);
      alert('Failed to start quiz. Please try again.');
    }
  };

  // 3. Timer countdown
  useEffect(() => {
    if (!session || isComplete || timeLeft === 0) return;

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          handleTimeout();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [session, currentQuestionIndex, timeLeft, isComplete]);

  // 4. Handle answer submission
  const submitAnswer = async (answer, answerId) => {
    if (timeLeft === 0) return;

    const timeTaken = (selectedQuiz.time_per_question || 5) - timeLeft;

    try {
      const { data } = await axios.post(
        `${API_BASE}/quiz-sessions/${session.id}/submit_answer/`,
        {
          session: session.id,
          question: session.questions[currentQuestionIndex].id,
          selected_answer: answer,
          selected_answer_id: answerId,
          time_taken_seconds: timeTaken
        }
      );

      // Update state
      setScore(data.session.score);
      setMultiplier(data.session.current_multiplier);

      // Show feedback
      showFeedback(data.submission.is_correct, data.submission.points_awarded);

      // Move to next question or complete
      if (data.quiz_completed) {
        setIsComplete(true);
        showResults();
      } else {
        setTimeout(() => {
          moveToNextQuestion();
        }, 1500);
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  // 5. Handle timeout
  const handleTimeout = async () => {
    const timeTaken = selectedQuiz.time_per_question || 5;

    try {
      await axios.post(
        `${API_BASE}/quiz-sessions/${session.id}/submit_answer/`,
        {
          session: session.id,
          question: session.questions[currentQuestionIndex].id,
          selected_answer: '',
          selected_answer_id: null,
          time_taken_seconds: timeTaken
        }
      );

      setMultiplier(1); // Timeout breaks streak
      showFeedback(false, 0);

      setTimeout(() => {
        moveToNextQuestion();
      }, 1500);
    } catch (error) {
      console.error('Failed to handle timeout:', error);
    }
  };

  const moveToNextQuestion = () => {
    const nextIndex = currentQuestionIndex + 1;
    if (nextIndex < session.questions.length) {
      setCurrentQuestionIndex(nextIndex);
      setTimeLeft(selectedQuiz.time_per_question || 5);
    } else {
      completeQuiz();
    }
  };

  const completeQuiz = async () => {
    try {
      const { data } = await axios.post(
        `${API_BASE}/quiz-sessions/${session.id}/complete/`
      );
      setIsComplete(true);
      setSession(data.session);
      showResults();
    } catch (error) {
      console.error('Failed to complete quiz:', error);
    }
  };

  const showFeedback = (isCorrect, points) => {
    // Show visual feedback (toast, modal, etc.)
    const message = isCorrect 
      ? `✓ Correct! +${points} points (${multiplier}x multiplier)`
      : '✗ Wrong answer!';
    alert(message);
  };

  const showResults = () => {
    // Navigate to results page or show modal
    console.log('Quiz completed!', session);
  };

  // Render quiz selection
  if (!session) {
    return (
      <div>
        <h1>Quiz Game</h1>
        <input
          type="text"
          placeholder="Enter your name"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
        />
        
        <div>
          <label>
            <input
              type="radio"
              checked={!isTournament}
              onChange={() => setIsTournament(false)}
            />
            Casual Play
          </label>
          <label>
            <input
              type="radio"
              checked={isTournament}
              onChange={() => setIsTournament(true)}
            />
            Tournament Mode
          </label>
        </div>

        <select onChange={(e) => setSelectedQuiz(quizzes.find(q => q.slug === e.target.value))}>
          <option value="">Select a quiz</option>
          {quizzes.map(quiz => (
            <option key={quiz.id} value={quiz.slug}>
              {quiz.title} - {quiz.difficulty_display}
            </option>
          ))}
        </select>

        <button onClick={startQuiz}>Start Quiz</button>
      </div>
    );
  }

  // Render quiz game
  if (!isComplete && session.questions[currentQuestionIndex]) {
    const question = session.questions[currentQuestionIndex];

    return (
      <div>
        <div>Score: {score} | Multiplier: {multiplier}x | Time: {timeLeft}s</div>
        <h2>Question {currentQuestionIndex + 1}/{session.questions.length}</h2>
        <p>{question.text}</p>
        <div>
          {question.answers.map(answer => (
            <button
              key={answer.id}
              onClick={() => submitAnswer(answer.text, answer.id)}
              disabled={timeLeft === 0}
            >
              {answer.text}
            </button>
          ))}
        </div>
      </div>
    );
  }

  // Render results
  return (
    <div>
      <h1>Quiz Complete!</h1>
      <p>Final Score: {session.score}</p>
      <p>Time: {session.duration_formatted}</p>
      <p>Mode: {session.is_tournament ? 'Tournament' : 'Casual'}</p>
      <button onClick={() => window.location.reload()}>Play Again</button>
    </div>
  );
}

export default QuizGame;
```

---

## 🏅 Leaderboard Implementation

```jsx
function Leaderboard({ quizSlug }) {
  const [allTimeLeaderboard, setAllTimeLeaderboard] = useState([]);
  const [tournamentLeaderboard, setTournamentLeaderboard] = useState([]);
  const [activeTab, setActiveTab] = useState('all_time');

  useEffect(() => {
    loadLeaderboards();
  }, [quizSlug]);

  const loadLeaderboards = async () => {
    // Load all-time leaderboard
    const { data: allTime } = await axios.get(
      `${API_BASE}/quiz-sessions/all_time_leaderboard/?quiz=${quizSlug}&period=all&limit=50`
    );
    setAllTimeLeaderboard(allTime.leaderboard);

    // Load tournament leaderboard
    const { data: tournament } = await axios.get(
      `${API_BASE}/quiz-sessions/tournament_leaderboard/?quiz=${quizSlug}&period=all&limit=50`
    );
    setTournamentLeaderboard(tournament.leaderboard);
  };

  const currentLeaderboard = activeTab === 'all_time' 
    ? allTimeLeaderboard 
    : tournamentLeaderboard;

  return (
    <div>
      <h1>Leaderboard</h1>
      
      <div>
        <button onClick={() => setActiveTab('all_time')}>
          All-Time Top Players
        </button>
        <button onClick={() => setActiveTab('tournament')}>
          Tournament Winners
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Player</th>
            <th>Score</th>
            <th>Time</th>
            <th>Mode</th>
          </tr>
        </thead>
        <tbody>
          {currentLeaderboard.map(entry => (
            <tr key={entry.rank}>
              <td>{entry.rank}</td>
              <td>{entry.player_name}</td>
              <td>{entry.score}</td>
              <td>{entry.duration_formatted}</td>
              <td>{entry.is_tournament ? '🏆 Tournament' : '🎮 Casual'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## 📋 Summary

### What Changed
1. **Removed**: `hotel_identifier`, `room_number`, `is_practice_mode`
2. **Added**: `is_tournament` (boolean)
3. **Simplified**: No hotel/room validation needed

### Two Leaderboards
1. **All-Time**: Shows ALL completed sessions (casual + tournament)
2. **Tournament**: Shows ONLY tournament sessions (`is_tournament: true`)

### Benefits
- ✅ Fully anonymous - no personal data needed
- ✅ Simple implementation - no hotel/room tracking
- ✅ Tournament tracking for winners
- ✅ Casual play always available
- ✅ All tournament scores appear in all-time leaderboard too

### API Endpoints Summary
- `POST /quiz-sessions/` - Start game (set `is_tournament: true/false`)
- `POST /quiz-sessions/{id}/submit_answer/` - Submit answer
- `POST /quiz-sessions/{id}/complete/` - Complete game
- `GET /quiz-sessions/all_time_leaderboard/` - All players
- `GET /quiz-sessions/tournament_leaderboard/` - Tournament winners only
