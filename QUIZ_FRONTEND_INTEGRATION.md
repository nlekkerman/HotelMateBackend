# Quiz Game Frontend Integration Guide

## 🎮 Complete API Documentation for Frontend Integration

### Base URL
```
Production: https://hotel-porter-d25ad83b12cf.herokuapp.com/api/v1/entertainment
Local Dev: http://localhost:8000/api/v1/entertainment
```

---

## 📋 Table of Contents
1. [Quiz Endpoints](#quiz-endpoints)
2. [Category Endpoints](#category-endpoints)
3. [Game Session Flow](#game-session-flow)
4. [Tournament Endpoints](#tournament-endpoints)
5. [Leaderboard Endpoints](#leaderboard-endpoints)
6. [Complete Game Flow Example](#complete-game-flow-example)

---

## 1. Quiz Endpoints

### Get All Quizzes
**GET** `/quizzes/`

**Response:**
```json
[
  {
    "id": 1,
    "title": "Guessticulator The Quizculator",
    "slug": "guessticulator",
    "description": "The ultimate quiz game",
    "questions_per_category": 10,
    "time_per_question_seconds": 5,
    "turbo_mode_threshold": 5,
    "turbo_multiplier": "2.0",
    "is_active": true,
    "qr_code_url": "https://res.cloudinary.com/dg0ssec7u/image/upload/...",
    "qr_generated_at": "2025-11-13T23:00:00Z"
  }
]
```

### Get Quiz Detail
**GET** `/quizzes/{slug}/`

**Example:** `/quizzes/guessticulator/`

**Response:** Same as above but single object

---

## 2. Category Endpoints

### Get All Categories
**GET** `/quiz-categories/`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Classic Trivia",
    "slug": "classic-trivia",
    "description": "General knowledge questions",
    "order": 1,
    "is_math_category": false,
    "is_active": true,
    "question_count": 50
  },
  {
    "id": 2,
    "name": "Dynamic Math",
    "slug": "dynamic-math",
    "description": "Math challenges",
    "order": 2,
    "is_math_category": true,
    "is_active": true,
    "question_count": "Dynamic"
  }
]
```

### Get Category Detail
**GET** `/quiz-categories/{slug}/`

**Example:** `/quiz-categories/classic-trivia/`

---

## 3. Game Session Flow

### 🚀 Step 1: Start Session
**POST** `/quiz/game/start_session/`

**Request Body:**
```json
{
  "player_name": "PlayerName",
  "session_token": "uuid-generated-on-frontend",
  "is_tournament_mode": false,
  "tournament_slug": null
}
```

**For Tournament Mode:**
```json
{
  "player_name": "PlayerName",
  "session_token": "uuid-generated-on-frontend",
  "is_tournament_mode": true,
  "tournament_slug": "weekend-challenge"
}
```

**Response:**
```json
{
  "session": {
    "id": "a1b2c3d4-uuid",
    "player_name": "PlayerName",
    "session_token": "uuid-generated-on-frontend",
    "score": 0,
    "is_turbo_active": false,
    "consecutive_correct": 0,
    "started_at": "2025-11-13T23:00:00Z",
    "is_completed": false,
    "is_tournament_mode": false
  },
  "current_category": {
    "id": 1,
    "name": "Classic Trivia",
    "slug": "classic-trivia",
    "description": "General knowledge questions",
    "order": 1,
    "is_math_category": false
  },
  "questions": [
    {
      "id": 123,
      "category_slug": "classic-trivia",
      "text": "What is the capital of France?",
      "image_url": null,
      "answers": [
        {
          "id": 1,
          "text": "Paris",
          "order": 0
        },
        {
          "id": 2,
          "text": "London",
          "order": 1
        },
        {
          "id": 3,
          "text": "Berlin",
          "order": 2
        },
        {
          "id": 4,
          "text": "Madrid",
          "order": 3
        }
      ]
    }
    // ... 9 more questions
  ],
  "total_categories": 5,
  "questions_per_category": 10
}
```

**Math Category Questions:**
```json
{
  "id": null,
  "category_slug": "dynamic-math",
  "text": "5 × 7 = ?",
  "image_url": null,
  "answers": [
    {
      "id": 1,
      "text": "35",
      "order": 0
    },
    {
      "id": 2,
      "text": "32",
      "order": 1
    },
    {
      "id": 3,
      "text": "38",
      "order": 2
    },
    {
      "id": 4,
      "text": "33",
      "order": 3
    }
  ],
  "question_data": {
    "num1": 5,
    "num2": 7,
    "operator": "*",
    "correct_answer": 35
  }
}
```

### ✅ Step 2: Submit Answer
**POST** `/quiz/game/submit_answer/`

**Request Body (Regular Question):**
```json
{
  "session_id": "a1b2c3d4-uuid",
  "category_slug": "classic-trivia",
  "question_id": 123,
  "question_text": "What is the capital of France?",
  "selected_answer": "Paris",
  "selected_answer_id": 1,
  "time_taken_seconds": 2
}
```

**Request Body (Math Question):**
```json
{
  "session_id": "a1b2c3d4-uuid",
  "category_slug": "dynamic-math",
  "question_text": "5 × 7 = ?",
  "selected_answer": "35",
  "time_taken_seconds": 3,
  "question_data": {
    "num1": 5,
    "num2": 7,
    "operator": "*",
    "correct_answer": 35
  }
}
```

**Response:**
```json
{
  "success": true,
  "submission": {
    "id": "sub-uuid",
    "is_correct": true,
    "time_taken_seconds": 2,
    "points_awarded": 4,
    "was_turbo_active": false,
    "answered_at": "2025-11-13T23:00:05Z"
  },
  "session_updated": {
    "score": 4,
    "consecutive_correct": 1,
    "is_turbo_active": false
  }
}
```

**Point System:**
- **Normal Mode:** 5-4-3-2-1-0 points (based on 1-5 seconds, 5+ seconds = 0)
- **Turbo Mode:** 10-8-6-4-2-0 points (2x multiplier)
- **Turbo activates** after 5 consecutive correct answers
- **Turbo deactivates** on first wrong answer

### 🏁 Step 3: Complete Session
**POST** `/quiz/game/complete_session/`

**Request Body:**
```json
{
  "session_id": "a1b2c3d4-uuid"
}
```

**Response:**
```json
{
  "success": true,
  "session": {
    "id": "a1b2c3d4-uuid",
    "player_name": "PlayerName",
    "score": 185,
    "is_completed": true,
    "finished_at": "2025-11-13T23:10:00Z",
    "time_spent_seconds": 600,
    "duration_formatted": "10m 0s"
  },
  "leaderboard_entry": {
    "player_name": "PlayerName",
    "best_score": 185,
    "games_played": 1,
    "rank": 5
  }
}
```

---

## 4. Tournament Endpoints

### Get All Tournaments
**GET** `/quiz-tournaments/`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Weekend Challenge",
    "slug": "weekend-challenge",
    "description": "24-hour weekend tournament",
    "quiz": "Guessticulator The Quizculator",
    "start_date": "2025-11-13T23:04:11Z",
    "end_date": "2025-11-14T23:04:11Z",
    "status": "active",
    "first_prize": "Trophy + $100",
    "second_prize": "Medal + $50",
    "third_prize": "Certificate + $25",
    "qr_code_url": "https://res.cloudinary.com/dg0ssec7u/...",
    "is_active": true,
    "created_at": "2025-11-13T22:00:00Z"
  },
  {
    "id": 2,
    "name": "Test 24-Hour Quiz Tournament",
    "slug": "test-tournament-24h",
    "status": "upcoming",
    "start_date": "2025-11-14T00:33:29Z",
    "end_date": "2025-11-15T00:33:29Z",
    "qr_code_url": "https://res.cloudinary.com/dg0ssec7u/...",
    "is_active": false
  }
]
```

### Get Tournament Detail
**GET** `/quiz-tournaments/{slug}/`

**Example:** `/quiz-tournaments/weekend-challenge/`

### Get Tournament Leaderboard
**GET** `/quiz-tournaments/{slug}/leaderboard/`

**Response:**
```json
[
  {
    "rank": 1,
    "player_name": "TopPlayer",
    "session_token": "uuid-1",
    "best_score": 250,
    "games_played": 3,
    "best_time": 480
  },
  {
    "rank": 2,
    "player_name": "SecondPlace",
    "session_token": "uuid-2",
    "best_score": 230,
    "games_played": 2,
    "best_time": 500
  }
]
```

---

## 5. Leaderboard Endpoints

### Get All-Time Leaderboard
**GET** `/quiz/leaderboard/all-time/`

**Query Parameters (optional):**
- `limit` - number of entries (default: 10)

**Response:**
```json
[
  {
    "rank": 1,
    "player_name": "ChampionPlayer",
    "best_score": 285,
    "games_played": 15,
    "last_played": "2025-11-13T22:00:00Z"
  }
]
```

### Get Player Stats
**GET** `/quiz/leaderboard/player-stats/`

**Query Parameters (required):**
- `session_token` - player's unique token

**Example:** `/quiz/leaderboard/player-stats/?session_token=abc123`

**Response:**
```json
{
  "player_name": "PlayerName",
  "session_token": "abc123",
  "best_score": 185,
  "games_played": 5,
  "last_played": "2025-11-13T23:00:00Z",
  "rank": 12,
  "recent_sessions": [
    {
      "id": "uuid",
      "score": 185,
      "completed_at": "2025-11-13T23:00:00Z",
      "duration": "10m 0s"
    }
  ]
}
```

---

## 6. Complete Game Flow Example

### Frontend Implementation (React/Vue/Vanilla JS)

```javascript
// ===== STEP 1: Initialize Game =====
import { v4 as uuidv4 } from 'uuid'; // or any UUID generator

// Generate or retrieve session token
let sessionToken = localStorage.getItem('quiz_session_token');
if (!sessionToken) {
  sessionToken = uuidv4();
  localStorage.setItem('quiz_session_token', sessionToken);
}

// ===== STEP 2: Start Session =====
async function startQuizSession(playerName, isTournament = false, tournamentSlug = null) {
  const response = await fetch('https://hotel-porter-d25ad83b12cf.herokuapp.com/api/v1/entertainment/quiz/game/start_session/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      player_name: playerName,
      session_token: sessionToken,
      is_tournament_mode: isTournament,
      tournament_slug: tournamentSlug
    })
  });
  
  const data = await response.json();
  
  // Store session data
  sessionStorage.setItem('current_session', JSON.stringify(data.session));
  sessionStorage.setItem('current_questions', JSON.stringify(data.questions));
  sessionStorage.setItem('current_category', JSON.stringify(data.current_category));
  
  return data;
}

// ===== STEP 3: Display Questions =====
function displayQuestion(question, index) {
  // Shuffle answers (they come in order)
  const shuffledAnswers = [...question.answers].sort(() => Math.random() - 0.5);
  
  return `
    <div class="question">
      <h2>Question ${index + 1}/10</h2>
      ${question.image_url ? `<img src="${question.image_url}" alt="Question image" />` : ''}
      <p>${question.text}</p>
      <div class="answers">
        ${shuffledAnswers.map(answer => `
          <button 
            class="answer-btn" 
            data-answer="${answer.text}"
            data-answer-id="${answer.id}">
            ${answer.text}
          </button>
        `).join('')}
      </div>
      <div class="timer">Time: <span id="timer">5</span>s</div>
    </div>
  `;
}

// ===== STEP 4: Submit Answer =====
async function submitAnswer(sessionId, question, selectedAnswer, selectedAnswerId, timeTaken) {
  const body = {
    session_id: sessionId,
    category_slug: question.category_slug,
    question_text: question.text,
    selected_answer: selectedAnswer,
    time_taken_seconds: timeTaken
  };
  
  // Add question_id for regular questions
  if (question.id) {
    body.question_id = question.id;
    body.selected_answer_id = selectedAnswerId;
  }
  
  // Add question_data for math questions
  if (question.question_data) {
    body.question_data = question.question_data;
  }
  
  const response = await fetch('https://hotel-porter-d25ad83b12cf.herokuapp.com/api/v1/entertainment/quiz/game/submit_answer/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body)
  });
  
  return await response.json();
}

// ===== STEP 5: Handle Answer Result =====
function handleAnswerResult(result) {
  const { submission, session_updated } = result;
  
  // Show result to user
  if (submission.is_correct) {
    console.log(`✅ Correct! +${submission.points_awarded} points`);
  } else {
    console.log(`❌ Wrong answer! 0 points`);
  }
  
  // Check turbo mode
  if (session_updated.is_turbo_active && !previousTurboState) {
    console.log('🔥 TURBO MODE ACTIVATED!');
    // Show turbo mode animation
  } else if (!session_updated.is_turbo_active && previousTurboState) {
    console.log('⚡ Turbo mode deactivated');
  }
  
  // Update UI with current score
  updateScoreDisplay(session_updated.score);
  updateStreakDisplay(session_updated.consecutive_correct);
}

// ===== STEP 6: Move to Next Category =====
async function moveToNextCategory(sessionId, nextCategorySlug) {
  // Frontend fetches next category questions
  const response = await fetch(`https://hotel-porter-d25ad83b12cf.herokuapp.com/api/v1/entertainment/quiz-categories/${nextCategorySlug}/`);
  const category = await response.json();
  
  // Display category transition
  showCategoryTransition(category);
}

// ===== STEP 7: Complete Session =====
async function completeSession(sessionId) {
  const response = await fetch('https://hotel-porter-d25ad83b12cf.herokuapp.com/api/v1/entertainment/quiz/game/complete_session/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: sessionId })
  });
  
  const result = await response.json();
  
  // Show final results
  displayFinalResults(result);
  
  // Clear session storage
  sessionStorage.removeItem('current_session');
  sessionStorage.removeItem('current_questions');
  sessionStorage.removeItem('current_category');
  
  return result;
}

// ===== STEP 8: Display Final Results =====
function displayFinalResults(result) {
  const { session, leaderboard_entry } = result;
  
  return `
    <div class="results">
      <h1>Game Complete! 🎉</h1>
      <div class="final-score">
        <h2>${session.score} Points</h2>
        <p>Time: ${session.duration_formatted}</p>
      </div>
      ${leaderboard_entry ? `
        <div class="leaderboard-position">
          <p>Your Rank: #${leaderboard_entry.rank}</p>
          <p>Games Played: ${leaderboard_entry.games_played}</p>
          ${leaderboard_entry.is_new_best ? '<p class="highlight">🏆 New Personal Best!</p>' : ''}
        </div>
      ` : ''}
      <button onclick="playAgain()">Play Again</button>
      <button onclick="viewLeaderboard()">View Leaderboard</button>
    </div>
  `;
}

// ===== Additional: Load Tournaments =====
async function loadTournaments() {
  const response = await fetch('https://hotel-porter-d25ad83b12cf.herokuapp.com/api/v1/entertainment/quiz-tournaments/');
  const tournaments = await response.json();
  
  // Filter active tournaments
  const activeTournaments = tournaments.filter(t => t.is_active);
  
  return activeTournaments;
}

// ===== Additional: Load Leaderboard =====
async function loadLeaderboard(limit = 10) {
  const response = await fetch(`https://hotel-porter-d25ad83b12cf.herokuapp.com/api/v1/entertainment/quiz/leaderboard/all-time/?limit=${limit}`);
  return await response.json();
}
```

---

## 🎯 Game Flow Summary

1. **Initialize** - Generate or retrieve session_token
2. **Start Session** - POST to `/quiz/game/start_session/`
3. **Display Questions** - Show 10 questions from first category
4. **Submit Answers** - POST each answer to `/quiz/game/submit_answer/`
5. **Update UI** - Show score, streak, turbo mode status
6. **Next Category** - After 10 questions, fetch next category
7. **Repeat** - Steps 3-6 for all 5 categories (50 total questions)
8. **Complete** - POST to `/quiz/game/complete_session/`
9. **Results** - Display final score and leaderboard position

---

## 🔥 Turbo Mode Logic

- Activates after **5 consecutive correct answers**
- **Doubles** all points (2x multiplier)
- Deactivates on **first wrong answer**
- Visual indicator should be prominent!

---

## ⏱️ Timer Logic

- Each question has **5 seconds** to answer
- Points: 5→4→3→2→1→0 (by second)
- In Turbo: 10→8→6→4→2→0

---

## 🏆 Tournament Mode

Start with tournament slug:
```javascript
startQuizSession('PlayerName', true, 'weekend-challenge');
```

Tournament URL from QR code:
```
https://hotelsmates.com/games/quiz?tournament=weekend-challenge
```

Frontend should parse URL and extract tournament slug.

---

## 📱 QR Code URLs

### Quiz QR Code:
```
https://res.cloudinary.com/dg0ssec7u/image/upload/v1763076810/quiz_qr/guessticulator.png
```

### Tournament QR Codes:
```
Weekend Challenge:
https://res.cloudinary.com/dg0ssec7u/image/upload/v1763075051/quiz_tournament_qr/weekend-challenge.png

Test Tournament:
https://res.cloudinary.com/dg0ssec7u/image/upload/v1763076810/quiz_tournament_qr/test-tournament-24h.png
```

---

## ✅ Testing Checklist

- [ ] Can start a casual game session
- [ ] Can start a tournament game session
- [ ] Questions display correctly (including math questions)
- [ ] Timer counts down properly
- [ ] Answer submission works
- [ ] Points calculate correctly
- [ ] Turbo mode activates at 5 correct answers
- [ ] Turbo mode deactivates on wrong answer
- [ ] Score updates in real-time
- [ ] Can complete all 5 categories (50 questions)
- [ ] Session completion works
- [ ] Leaderboard displays correctly
- [ ] Player stats are accurate
- [ ] QR codes scan correctly
- [ ] Tournament mode works differently from casual

---

## 🐛 Common Issues

1. **CORS Errors**: Backend has ALLOWED_HOSTS configured for hotelsmates.com
2. **Session Token**: Must be consistent for same player
3. **Math Questions**: Don't have question_id, use question_data instead
4. **Timer**: Frontend responsibility, backend just receives time_taken_seconds
5. **Categories**: Come in order 1-5, frontend should not shuffle

---

## 📞 Support

Backend Repository: https://github.com/nlekkerman/HotelMateBackend
Production API: https://hotel-porter-d25ad83b12cf.herokuapp.com/api/v1/entertainment

---

**Last Updated:** November 13, 2025
**API Version:** v1
