# GUESSTICULATOR QUIZ API DOCUMENTATION

## 🌐 BASE URL
```
Development: http://localhost:8000/api/entertainment/
Production: https://your-domain.com/api/entertainment/
```

---

## 📋 TABLE OF CONTENTS
1. [Quiz Categories](#quiz-categories)
2. [Quiz Questions](#quiz-questions)
3. [Quiz Sessions](#quiz-sessions)
4. [Quiz Leaderboard](#quiz-leaderboard)
5. [Quiz Tournaments](#quiz-tournaments)
6. [Serializers Reference](#serializers-reference)
7. [Error Codes](#error-codes)

---

## 🎯 QUIZ CATEGORIES

### List All Categories
**GET** `/quiz-categories/`

**Response**:
```json
[
  {
    "id": 1,
    "name": "History",
    "slug": "history",
    "description": "Test your knowledge of historical events",
    "icon": "📚",
    "color": "#4F46E5",
    "is_active": true,
    "display_order": 1,
    "question_count": 25
  }
]
```

### Get Category Details
**GET** `/quiz-categories/{id}/`

**Response**: Same as list item above

### Slot Machine - Random Selection
**GET** `/quiz-categories/random_selection/`  
**GET** `/quiz-categories/random_selection/?count=5`

**Query Parameters**:
- `count` (optional, default: 5): Number of categories to select

**Response**:
```json
[
  {
    "id": 1,
    "name": "History",
    "slug": "history",
    "icon": "📚",
    "color": "#4F46E5",
    "question_count": 25
  },
  {
    "id": 5,
    "name": "Music",
    "slug": "music",
    "icon": "🎵",
    "color": "#F59E0B",
    "question_count": 20
  }
  // ... 3 more random categories
]
```

---

## ❓ QUIZ QUESTIONS

### List Questions
**GET** `/quiz-questions/`

**Query Parameters**:
- `category` (optional): Filter by category ID
- `difficulty` (optional): Filter by difficulty (easy, medium, hard)

**Response**:
```json
[
  {
    "id": 1,
    "category": 1,
    "category_name": "History",
    "category_icon": "📚",
    "question_text": "What year did World War II end?",
    "difficulty": "medium",
    "difficulty_display": "Medium",
    "option_a": "1943",
    "option_b": "1945",
    "option_c": "1946",
    "option_d": "1947",
    "points": 10,
    "is_active": true
  }
]
```

**Note**: `correct_answer` and `explanation` are NOT included in list view for security

### Get Question Details (With Answer)
**GET** `/quiz-questions/{id}/`

**Response**:
```json
{
  "id": 1,
  "category": 1,
  "category_name": "History",
  "question_text": "What year did World War II end?",
  "difficulty": "medium",
  "difficulty_display": "Medium",
  "option_a": "1943",
  "option_b": "1945",
  "option_c": "1946",
  "option_d": "1947",
  "correct_answer": "B",
  "correct_option_text": "1945",
  "explanation": "World War II ended in 1945 with Germany's surrender in May and Japan's surrender in September.",
  "points": 10
}
```

**⚠️ Security Note**: Only use detail endpoint for admin/results review, not during active quiz!

---

## 🎮 QUIZ SESSIONS

### Start New Quiz (Slot Machine)
**POST** `/quiz-sessions/start_quiz/`

**Request Body**:
```json
{
  "player_name": "Alice|player_abc123",
  "hotel": 1,  // optional
  "tournament": null,  // optional, tournament ID for tournament play
  "questions_per_quiz": 20  // optional, default: 20
}
```

**Response**:
```json
{
  "session": {
    "id": 42,
    "player_name": "Alice|player_abc123",
    "player_display_name": "Alice",
    "hotel": 1,
    "hotel_name": "Grand Hotel",
    "tournament": null,
    "tournament_name": null,
    "selected_categories": [1, 3, 5, 7, 9],
    "total_questions": 20,
    "correct_answers": 0,
    "score": 0,
    "time_seconds": null,
    "completed": false,
    "started_at": "2025-11-14T10:30:00Z",
    "completed_at": null,
    "current_question_index": 0,
    "answers": []
  },
  "categories": [
    {
      "id": 1,
      "name": "History",
      "icon": "📚",
      "color": "#4F46E5"
    }
    // ... 4 more selected categories
  ],
  "questions": [
    {
      "id": 15,
      "category": 1,
      "category_name": "History",
      "question_text": "What year did World War II end?",
      "difficulty": "medium",
      "option_a": "1943",
      "option_b": "1945",
      "option_c": "1946",
      "option_d": "1947",
      "points": 10
    }
    // ... 19 more questions
  ]
}
```

### Submit Answer
**POST** `/quiz-sessions/{id}/submit_answer/`

**Request Body**:
```json
{
  "question_id": 15,
  "selected_answer": "B",
  "time_seconds": 8  // optional, time taken to answer
}
```

**Response**:
```json
{
  "id": 101,
  "question": 15,
  "question_text": "What year did World War II end?",
  "category_name": "History",
  "selected_answer": "B",
  "is_correct": true,
  "time_seconds": 8,
  "answered_at": "2025-11-14T10:30:45Z"
}
```

### Complete Quiz Session
**POST** `/quiz-sessions/{id}/complete_session/`

**Request Body**:
```json
{
  "time_seconds": 240  // optional, total time for entire quiz
}
```

**Response**:
```json
{
  "id": 42,
  "player_name": "Alice|player_abc123",
  "player_display_name": "Alice",
  "selected_categories": [1, 3, 5, 7, 9],
  "total_questions": 20,
  "correct_answers": 15,
  "score": 285,  // Calculated based on difficulty & time bonuses
  "time_seconds": 240,
  "completed": true,
  "started_at": "2025-11-14T10:30:00Z",
  "completed_at": "2025-11-14T10:34:00Z",
  "answers": [
    {
      "question": 15,
      "selected_answer": "B",
      "is_correct": true,
      "time_seconds": 8
    }
    // ... all 20 answers
  ]
}
```

### List Sessions
**GET** `/quiz-sessions/`

**Query Parameters**:
- `player_token` (optional): Filter by player token
- `tournament` (optional): Filter by tournament ID

**Response**: Array of session objects

### Get Session Details
**GET** `/quiz-sessions/{id}/`

**Response**: Single session object with all answers

---

## 🏆 QUIZ LEADERBOARD

### General Leaderboard (Best Score Per Player)
**GET** `/quiz-leaderboard/`

**Response**:
```json
[
  {
    "id": 1,
    "player_name": "Alice|player_abc123",
    "player_display_name": "Alice",
    "player_token": "player_abc123",
    "best_score": 350,
    "rank": 1,
    "total_games_played": 8,
    "best_score_achieved_at": "2025-11-14T10:34:00Z",
    "first_played_at": "2025-11-10T08:00:00Z",
    "last_played_at": "2025-11-14T10:30:00Z"
  },
  {
    "id": 2,
    "player_name": "Bob|player_xyz789",
    "player_display_name": "Bob",
    "player_token": "player_xyz789",
    "best_score": 320,
    "rank": 2,
    "total_games_played": 5,
    "best_score_achieved_at": "2025-11-13T15:20:00Z",
    "first_played_at": "2025-11-12T09:00:00Z",
    "last_played_at": "2025-11-13T15:20:00Z"
  }
  // ... more players
]
```

### Get My Rank
**GET** `/quiz-leaderboard/my_rank/?player_token=player_abc123`

**Response**:
```json
{
  "id": 1,
  "player_name": "Alice|player_abc123",
  "player_display_name": "Alice",
  "player_token": "player_abc123",
  "best_score": 350,
  "rank": 1,
  "total_games_played": 8,
  "best_score_achieved_at": "2025-11-14T10:34:00Z",
  "first_played_at": "2025-11-10T08:00:00Z",
  "last_played_at": "2025-11-14T10:30:00Z"
}
```

---

## 🎪 QUIZ TOURNAMENTS

### List Tournaments
**GET** `/quiz-tournaments/`

**Query Parameters**:
- `status` (optional): Filter by status (upcoming, active, completed, cancelled)
- `hotel` (optional): Filter by hotel ID

**Response**:
```json
[
  {
    "id": 1,
    "name": "Summer Quiz Championship 2025",
    "slug": "summer-quiz-2025",
    "hotel": 1,
    "hotel_name": "Grand Hotel",
    "description": "Test your knowledge across all categories!",
    "status": "active",
    "status_display": "Active",
    "max_participants": 100,
    "participant_count": 42,
    "questions_per_quiz": 20,
    "min_age": 13,
    "max_age": null,
    "start_date": "2025-11-14T00:00:00Z",
    "end_date": "2025-11-21T23:59:59Z",
    "registration_deadline": "2025-11-20T23:59:59Z",
    "is_registration_open": true,
    "is_active": true,
    "first_prize": "iPad Pro",
    "second_prize": "AirPods Pro",
    "third_prize": "$50 Gift Card",
    "rules": "Complete as many quizzes as you want. Your best score counts!",
    "qr_code_url": "https://cloudinary.com/...",
    "created_at": "2025-11-01T10:00:00Z"
  }
]
```

### Get Tournament Details
**GET** `/quiz-tournaments/{id}/`

**Response**: Same as list item above

### Tournament Leaderboard (All Plays)
**GET** `/quiz-tournaments/{id}/leaderboard/`  
**GET** `/quiz-tournaments/{id}/leaderboard/?limit=10`

**Query Parameters**:
- `limit` (optional): Limit number of results

**Response**:
```json
[
  {
    "id": 55,
    "player_name": "Alice|player_abc123",
    "player_display_name": "Alice",
    "score": 350,
    "correct_answers": 18,
    "total_questions": 20,
    "time_seconds": 240,
    "completed_at": "2025-11-14T10:34:00Z",
    "rank": 1
  },
  {
    "id": 62,
    "player_name": "Bob|player_xyz789",
    "player_display_name": "Bob",
    "score": 320,
    "correct_answers": 17,
    "total_questions": 20,
    "time_seconds": 280,
    "completed_at": "2025-11-14T11:15:00Z",
    "rank": 2
  },
  {
    "id": 48,
    "player_name": "Alice|player_abc123",
    "player_display_name": "Alice",
    "score": 280,
    "correct_answers": 15,
    "total_questions": 20,
    "time_seconds": 300,
    "completed_at": "2025-11-13T14:20:00Z",
    "rank": 3
  }
  // ... all tournament plays
]
```

**Note**: Tournament leaderboard shows ALL plays, including multiple plays by same player

### Tournament Top Players (Best Per Player)
**GET** `/quiz-tournaments/{id}/top_players/`

**Response**:
```json
{
  "tournament": {
    "id": 1,
    "name": "Summer Quiz Championship 2025",
    "status": "active"
  },
  "top_players": [
    {
      "session": {
        "id": 55,
        "player_name": "Alice|player_abc123",
        "score": 350,
        "time_seconds": 240
      },
      "score": 350,
      "name": "Alice"
    },
    {
      "session": {
        "id": 62,
        "player_name": "Bob|player_xyz789",
        "score": 320,
        "time_seconds": 280
      },
      "score": 320,
      "name": "Bob"
    },
    {
      "session": {
        "id": 71,
        "player_name": "Charlie|player_def456",
        "score": 305,
        "time_seconds": 260
      },
      "score": 305,
      "name": "Charlie"
    }
  ]
}
```

**Note**: Shows top 3 unique players with their BEST score

---

## 📦 SERIALIZERS REFERENCE

### QuizCategorySerializer
```python
{
  "id": int,
  "name": str,
  "slug": str,
  "description": str,
  "icon": str,
  "color": str (hex),
  "is_active": bool,
  "display_order": int,
  "question_count": int (read_only)
}
```

### QuizQuestionSerializer (List View)
```python
{
  "id": int,
  "category": int,
  "category_name": str (read_only),
  "category_icon": str (read_only),
  "question_text": str,
  "difficulty": str ("easy", "medium", "hard"),
  "difficulty_display": str (read_only),
  "option_a": str,
  "option_b": str,
  "option_c": str,
  "option_d": str,
  "points": int,
  "is_active": bool
}
```

### QuizQuestionDetailSerializer (Detail View)
```python
{
  "id": int,
  "category": int,
  "category_name": str (read_only),
  "question_text": str,
  "difficulty": str,
  "difficulty_display": str (read_only),
  "option_a": str,
  "option_b": str,
  "option_c": str,
  "option_d": str,
  "correct_answer": str ("A", "B", "C", "D"),
  "correct_option_text": str (read_only),
  "explanation": str,
  "points": int
}
```

### QuizSessionSerializer
```python
{
  "id": int,
  "player_name": str ("PlayerName|token"),
  "player_display_name": str (read_only),
  "hotel": int (nullable),
  "hotel_name": str (read_only, nullable),
  "tournament": int (nullable),
  "tournament_name": str (read_only, nullable),
  "selected_categories": list[int],
  "total_questions": int,
  "correct_answers": int,
  "score": int (read_only),
  "time_seconds": int (nullable),
  "completed": bool,
  "started_at": datetime (read_only),
  "completed_at": datetime (read_only, nullable),
  "current_question_index": int,
  "answers": list[QuizAnswerSerializer] (read_only)
}
```

### QuizAnswerSerializer
```python
{
  "id": int,
  "question": int,
  "question_text": str (read_only),
  "category_name": str (read_only),
  "selected_answer": str ("A", "B", "C", "D"),
  "is_correct": bool (read_only),
  "time_seconds": int (nullable),
  "answered_at": datetime (read_only)
}
```

### QuizLeaderboardSerializer
```python
{
  "id": int,
  "player_name": str,
  "player_display_name": str (read_only),
  "player_token": str,
  "best_score": int,
  "rank": int (read_only),
  "total_games_played": int,
  "best_score_achieved_at": datetime,
  "first_played_at": datetime,
  "last_played_at": datetime
}
```

### QuizTournamentSerializer
```python
{
  "id": int,
  "name": str,
  "slug": str,
  "hotel": int (nullable),
  "hotel_name": str (read_only, nullable),
  "description": str,
  "status": str ("upcoming", "active", "completed", "cancelled"),
  "status_display": str (read_only),
  "max_participants": int,
  "participant_count": int (read_only),
  "questions_per_quiz": int,
  "min_age": int (nullable),
  "max_age": int (nullable),
  "start_date": datetime,
  "end_date": datetime,
  "registration_deadline": datetime (nullable),
  "is_registration_open": bool (read_only),
  "is_active": bool (read_only),
  "first_prize": str,
  "second_prize": str,
  "third_prize": str,
  "rules": str,
  "qr_code_url": str (read_only),
  "created_at": datetime (read_only)
}
```

---

## ⚠️ ERROR CODES

### 400 Bad Request
```json
{
  "player_name": ["player_name must be in format: PlayerName|token"]
}
```

```json
{
  "error": "This quiz session is already completed"
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

```json
{
  "error": "Player not found on leaderboard"
}
```

---

## 🎯 FRONTEND INTEGRATION EXAMPLES

### Starting a Casual Quiz
```javascript
// 1. Generate player token
const playerToken = `player_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
const playerName = `${username}|${playerToken}`;

// 2. Start quiz
const response = await fetch('/api/entertainment/quiz-sessions/start_quiz/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    player_name: playerName,
    questions_per_quiz: 20
  })
});

const { session, categories, questions } = await response.json();

// 3. Store session ID and player token
localStorage.setItem('quiz_session_id', session.id);
localStorage.setItem('player_token', playerToken);

// 4. Display questions to player
questions.forEach((question, index) => {
  // Render question UI
});
```

### Submitting an Answer
```javascript
const submitAnswer = async (questionId, selectedAnswer, timeSeconds) => {
  const sessionId = localStorage.getItem('quiz_session_id');
  
  const response = await fetch(
    `/api/entertainment/quiz-sessions/${sessionId}/submit_answer/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_id: questionId,
        selected_answer: selectedAnswer,
        time_seconds: timeSeconds
      })
    }
  );
  
  const answer = await response.json();
  
  // Show immediate feedback
  if (answer.is_correct) {
    showCorrectFeedback();
  } else {
    showIncorrectFeedback();
  }
  
  return answer;
};
```

### Completing Quiz
```javascript
const completeQuiz = async (totalTime) => {
  const sessionId = localStorage.getItem('quiz_session_id');
  
  const response = await fetch(
    `/api/entertainment/quiz-sessions/${sessionId}/complete_session/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        time_seconds: totalTime
      })
    }
  );
  
  const session = await response.json();
  
  // Show results
  displayResults({
    score: session.score,
    correctAnswers: session.correct_answers,
    totalQuestions: session.total_questions,
    timeSeconds: session.time_seconds
  });
  
  // Show leaderboard position
  await fetchMyRank();
};
```

### Fetching Leaderboard
```javascript
const fetchLeaderboard = async () => {
  const response = await fetch('/api/entertainment/quiz-leaderboard/');
  const leaderboard = await response.json();
  
  // Display leaderboard
  leaderboard.forEach((entry, index) => {
    renderLeaderboardEntry(entry, index + 1);
  });
};

const fetchMyRank = async () => {
  const playerToken = localStorage.getItem('player_token');
  
  const response = await fetch(
    `/api/entertainment/quiz-leaderboard/my_rank/?player_token=${playerToken}`
  );
  
  if (response.ok) {
    const myEntry = await response.json();
    displayMyRank(myEntry);
  }
};
```

### Tournament Play
```javascript
// 1. List active tournaments
const fetchTournaments = async () => {
  const response = await fetch('/api/entertainment/quiz-tournaments/?status=active');
  const tournaments = await response.json();
  return tournaments;
};

// 2. Start tournament quiz (same as casual but with tournament ID)
const startTournamentQuiz = async (tournamentId) => {
  const playerToken = `player_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const playerName = `${username}|${playerToken}`;
  
  const response = await fetch('/api/entertainment/quiz-sessions/start_quiz/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_name: playerName,
      tournament: tournamentId,
      questions_per_quiz: 20
    })
  });
  
  return await response.json();
};

// 3. Fetch tournament leaderboard
const fetchTournamentLeaderboard = async (tournamentId) => {
  const response = await fetch(
    `/api/entertainment/quiz-tournaments/${tournamentId}/leaderboard/?limit=50`
  );
  return await response.json();
};
```

---

## 🔒 SECURITY NOTES

1. **No Authentication Required**: All endpoints are public (AllowAny permission)
2. **Player Identification**: Done via player token in player_name field
3. **Correct Answers**: Only exposed in detail view, not during active quiz
4. **Validation**: Player name format, answer choices, category selection all validated server-side
5. **Score Calculation**: Always done server-side, frontend cannot manipulate scores

---

## 📊 SCORING FORMULA

```
Base Score = Σ (Question Points × Difficulty Multiplier × Time Bonus)

Difficulty Multipliers:
- Easy: 1.0x
- Medium: 1.5x
- Hard: 2.0x

Time Bonuses (per question):
- < 10 seconds: 1.2x
- < 20 seconds: 1.1x
- ≥ 20 seconds: 1.0x

Example:
Medium question (10 pts) answered in 8 seconds:
= 10 × 1.5 × 1.2 = 18 points
```

---

## 🎨 UI/UX RECOMMENDATIONS

1. **Category Display**: Show icons and colors from API for visual appeal
2. **Progress Bar**: Track questions answered / total questions
3. **Timer**: Show countdown per question and total quiz time
4. **Immediate Feedback**: Show if answer was correct after each submission
5. **Score Animation**: Animate score updates
6. **Leaderboard Highlights**: Highlight current player's position
7. **Tournament Badge**: Show special badge for tournament play
8. **Results Summary**: Show breakdown by category and difficulty

---

## 🚀 QUICK START FRONTEND CHECKLIST

- [ ] Generate unique player token
- [ ] Call start_quiz endpoint
- [ ] Store session ID and player token in localStorage
- [ ] Display questions one by one or all at once
- [ ] Track time per question
- [ ] Submit answers via submit_answer endpoint
- [ ] Complete quiz via complete_session endpoint
- [ ] Display final score and rank
- [ ] Show leaderboard
- [ ] Handle errors gracefully

---

**Need Help?** Check the backend code or Django admin for live examples!
