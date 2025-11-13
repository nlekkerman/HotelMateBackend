# Quiz Game - Complete Frontend Integration Guide

## 🎮 Game Overview

**Adult-oriented quiz game with 5 difficulty levels and turbo mode scoring**

### Key Features
- ⚡ **Turbo Mode**: Multiplier doubles on consecutive correct answers (1x→2x→4x→8x→16x→32x→64x→128x)
- ⏱️ **Fast-paced**: 5 seconds per question
- 🏆 **Two Leaderboard Systems**: General (all players) & Tournament (room-based competition)
- 🎯 **Practice Mode**: Play without affecting tournament rankings
- 📊 **Dynamic Scoring**: Points based on speed (0-5 base points × multiplier)

---

## 📋 Difficulty Levels

| Level | Name | Question Type | Count | Special Features |
|-------|------|---------------|-------|------------------|
| 1 | Classic Trivia - Easy | Multiple choice | 100 | Basic general knowledge |
| 2 | Odd One Out | Find the odd item | 100 | Pattern recognition |
| 3 | Fill the Blank | Complete the sentence | 100 | Context clues |
| 4 | Math Challenge | Dynamic arithmetic | ∞ | Randomly generated (0-10 range, +/-/×/÷) |
| 5 | Knowledge Trap - Expert | Tricky true/false | 100 | Scientifically accurate facts |

---

## ⚡ Turbo Mode Scoring System

### Timing & Base Points
```
Answer Time     Base Points
0 seconds       5 points (instant)
1 second        4 points
2 seconds       3 points
3 seconds       2 points
4 seconds       1 point
5 seconds       0 points (TIMEOUT - BREAKS STREAK)
```

### Multiplier System
- **Start**: 1x multiplier
- **Correct answer**: Double multiplier (capped at 128x)
- **Wrong answer OR timeout (0 points)**: Reset to 1x
- **Progression**: 1x → 2x → 4x → 8x → 16x → 32x → 64x → 128x

### Score Calculation
```javascript
// Example: Answer in 1 second (4 base pts) after 5 correct answers in a row
base_points = 5 - time_taken_seconds  // 5 - 1 = 4
multiplier = 32x  // After 5 consecutive correct
final_score = 4 × 32 = 128 points!
```

### Maximum Single Answer Score
```
4 base points (1 second) × 128x multiplier = 512 points
```

---

## 🎯 Game Modes

### Practice Mode
- **Purpose**: Learn and improve without pressure
- **Features**:
  - No room number required
  - Saves to general leaderboard
  - Does NOT appear on tournament leaderboard
  - Great for testing strategies
- **API**: Set `is_practice_mode: true`

### Tournament Mode
- **Purpose**: Compete for prizes/rankings
- **Requirements**:
  - Must provide `room_number`
  - Set `is_practice_mode: false`
- **Features**:
  - Appears on BOTH general and tournament leaderboards
  - Used to determine tournament winners
  - Verified by room number

---

## 🏆 Leaderboard System

### General Leaderboard
**Shows ALL completed sessions (practice + tournament)**

**Endpoint**: `GET /api/v1/entertainment/quiz-sessions/general_leaderboard/`

**Query Parameters**:
```
quiz: string (required) - Quiz slug
hotel: string (required) - Hotel identifier
period: string (optional) - 'daily' | 'weekly' | 'all' (default: 'all')
limit: number (optional) - Max results (default: 50)
```

**Response**:
```json
{
  "quiz": "classic-trivia-easy",
  "hotel": "paradise-hotel",
  "period": "all",
  "leaderboard_type": "general",
  "description": "All players (practice + tournament mode)",
  "count": 5,
  "leaderboard": [
    {
      "rank": 1,
      "player_name": "Alice",
      "room_number": "101",
      "score": 245,
      "time_spent_seconds": 45,
      "duration_formatted": "45s",
      "finished_at": "2025-11-13T10:30:00Z",
      "is_practice_mode": false,
      "hotel_identifier": "paradise-hotel"
    },
    {
      "rank": 2,
      "player_name": "Bob",
      "room_number": null,
      "score": 230,
      "time_spent_seconds": 50,
      "duration_formatted": "50s",
      "finished_at": "2025-11-13T11:00:00Z",
      "is_practice_mode": true,
      "hotel_identifier": "paradise-hotel"
    }
  ]
}
```

### Tournament Leaderboard
**Shows ONLY tournament mode sessions (with room numbers)**

**Endpoint**: `GET /api/v1/entertainment/quiz-sessions/tournament_leaderboard/`

**Query Parameters**: Same as general leaderboard

**Filtering Logic**:
```python
is_practice_mode=False AND room_number IS NOT NULL
```

**Response**: Same structure as general leaderboard but only includes tournament entries

---

## 📡 API Endpoints

### Base URL
```
/api/v1/entertainment/
```

### 1. List Available Quizzes
```http
GET /quizzes/
```

**Query Parameters**:
- `difficulty_level`: Filter by level (1-5)
- `is_active`: Filter by active status

**Response**:
```json
[
  {
    "id": 1,
    "slug": "classic-trivia-easy",
    "title": "Classic Trivia - Easy",
    "description": "Test your general knowledge",
    "difficulty_level": 1,
    "category": {
      "id": 1,
      "name": "General Knowledge"
    },
    "max_questions": 10,
    "time_per_question_seconds": 5,
    "is_active": true,
    "question_count": 100
  }
]
```

### 2. Get Quiz Details
```http
GET /quizzes/{slug}/
```

**Response**: Includes full quiz info + sample questions

### 3. Generate Math Question (Level 4 Only)
```http
POST /quizzes/{slug}/generate_math_question/
```

**Request Body**:
```json
{
  "hotel_identifier": "paradise-hotel"
}
```

**Response**:
```json
{
  "question_text": "What is 7 + 3?",
  "answers": [
    {"text": "10", "id": 0},
    {"text": "8", "id": 1},
    {"text": "12", "id": 2},
    {"text": "9", "id": 3}
  ],
  "correct_answer": "10",
  "question_data": {
    "operand1": 7,
    "operand2": 3,
    "operator": "+",
    "correct_answer": "10"
  }
}
```

### 4. Create Quiz Session
```http
POST /quiz-sessions/
```

**Request Body**:
```json
{
  "quiz_id": 1,
  "hotel_identifier": "paradise-hotel",
  "player_name": "Alice",
  "room_number": "101",
  "is_practice_mode": false
}
```

**For Practice Mode**:
```json
{
  "quiz_id": 1,
  "hotel_identifier": "paradise-hotel",
  "player_name": "Bob",
  "room_number": null,
  "is_practice_mode": true
}
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "hotel_identifier": "paradise-hotel",
  "quiz": {
    "id": 1,
    "slug": "classic-trivia-easy",
    "title": "Classic Trivia - Easy"
  },
  "player_name": "Alice",
  "room_number": "101",
  "is_practice_mode": false,
  "score": 0,
  "started_at": "2025-11-13T10:00:00Z",
  "finished_at": null,
  "is_completed": false,
  "time_spent_seconds": 0,
  "duration_formatted": "0s",
  "current_question_index": 0,
  "submission_count": 0,
  "consecutive_correct": 0,
  "current_multiplier": 1
}
```

### 5. Submit Answer
```http
POST /quiz-sessions/{session_id}/submit_answer/
```

**Request Body**:
```json
{
  "session": "550e8400-e29b-41d4-a716-446655440000",
  "question": 123,
  "question_text": "What is the capital of France?",
  "selected_answer": "Paris",
  "selected_answer_id": 1,
  "time_taken_seconds": 2
}
```

**For Math Questions** (no question ID):
```json
{
  "session": "550e8400-e29b-41d4-a716-446655440000",
  "question": null,
  "question_text": "What is 7 + 3?",
  "question_data": {
    "operand1": 7,
    "operand2": 3,
    "operator": "+",
    "correct_answer": "10"
  },
  "selected_answer": "10",
  "time_taken_seconds": 1
}
```

**Response**:
```json
{
  "submission": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "is_correct": true,
    "points_awarded": 12,
    "time_taken_seconds": 2,
    "multiplier_used": 4,
    "answered_at": "2025-11-13T10:00:05Z"
  },
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "score": 36,
    "consecutive_correct": 3,
    "current_multiplier": 8,
    "current_question_index": 3
  },
  "quiz_completed": false
}
```

### 6. Complete Session
```http
POST /quiz-sessions/{session_id}/complete/
```

**Response**: Updated session with `is_completed: true`

### 7. Get General Leaderboard
```http
GET /quiz-sessions/general_leaderboard/?quiz=classic-trivia-easy&hotel=paradise-hotel&period=daily&limit=50
```

### 8. Get Tournament Leaderboard
```http
GET /quiz-sessions/tournament_leaderboard/?quiz=classic-trivia-easy&hotel=paradise-hotel&period=weekly&limit=20
```

---

## 🎨 Frontend Implementation Guide

### Game Flow

```javascript
// 1. Initialize Game
const startQuiz = async () => {
  // Choose mode
  const isPractice = askUserMode(); // true or false
  const roomNumber = isPractice ? null : askRoomNumber();
  
  // Create session
  const session = await createSession({
    quiz_id: selectedQuiz.id,
    hotel_identifier: hotelId,
    player_name: playerName,
    room_number: roomNumber,
    is_practice_mode: isPractice
  });
  
  return session;
};

// 2. Question Loop
const playQuiz = async (session) => {
  for (let i = 0; i < maxQuestions; i++) {
    // Get question (fetch from quiz or generate math)
    const question = await getQuestion(session.quiz, i);
    
    // Start timer
    const startTime = Date.now();
    
    // Show question and wait for answer
    const answer = await showQuestionAndWaitForAnswer(question);
    
    // Calculate time taken
    const timeTaken = Math.floor((Date.now() - startTime) / 1000);
    
    // Submit answer
    const result = await submitAnswer({
      session: session.id,
      question: question.id,
      question_text: question.text,
      selected_answer: answer.text,
      selected_answer_id: answer.id,
      time_taken_seconds: Math.min(timeTaken, 5)
    });
    
    // Update UI with results
    updateUI(result);
    
    // Check if quiz complete
    if (result.quiz_completed) {
      break;
    }
  }
  
  // Complete session
  await completeSession(session.id);
};

// 3. Show Results
const showResults = async (session) => {
  // Fetch updated session
  const finalSession = await getSession(session.id);
  
  // Show score breakdown
  displayScore(finalSession.score);
  
  // Show leaderboard position
  if (finalSession.is_practice_mode) {
    // Show only general leaderboard
    const leaderboard = await getGeneralLeaderboard();
    displayLeaderboard(leaderboard, 'Practice + Tournament');
  } else {
    // Show both leaderboards
    const general = await getGeneralLeaderboard();
    const tournament = await getTournamentLeaderboard();
    
    displayBothLeaderboards(general, tournament);
  }
};
```

### UI Components Needed

#### 1. Mode Selection Screen
```
┌─────────────────────────────────┐
│  Choose Game Mode               │
├─────────────────────────────────┤
│                                 │
│  🎯 TOURNAMENT MODE             │
│  Compete for prizes!            │
│  • Requires room number         │
│  • Appears on tournament board  │
│                                 │
│  [Enter Tournament]             │
│                                 │
│  ─────────────────────          │
│                                 │
│  🎮 PRACTICE MODE               │
│  Play for fun and practice      │
│  • No room number needed        │
│  • Won't affect tournament      │
│                                 │
│  [Practice]                     │
│                                 │
└─────────────────────────────────┘
```

#### 2. Question Screen
```
┌─────────────────────────────────┐
│  Question 3/10     ⏱️ 5s        │
│  Multiplier: 4x  🔥 Streak: 2   │
├─────────────────────────────────┤
│                                 │
│  What is the capital of         │
│  France?                        │
│                                 │
│  [A] London                     │
│  [B] Paris      ✓               │
│  [C] Berlin                     │
│  [D] Madrid                     │
│                                 │
│  ████████░░ 3s                  │
│                                 │
└─────────────────────────────────┘
```

#### 3. Answer Feedback
```
┌─────────────────────────────────┐
│  ✓ CORRECT!                     │
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
│  Total Score: 28                │
│                                 │
└─────────────────────────────────┘
```

#### 4. Results Screen (Tournament Mode)
```
┌─────────────────────────────────┐
│  🏆 Quiz Complete!              │
├─────────────────────────────────┤
│                                 │
│  Your Score: 245 points         │
│  Room: 101                      │
│  Time: 45s                      │
│                                 │
│  ═══════════════════            │
│                                 │
│  📊 TOURNAMENT LEADERBOARD      │
│  1. Alice (101) - 245 pts ⭐    │
│  2. Bob (102) - 230 pts         │
│  3. Charlie (103) - 210 pts     │
│                                 │
│  ═══════════════════            │
│                                 │
│  📈 GENERAL LEADERBOARD         │
│  1. Alice (101) - 245 pts ⭐    │
│  2. Diana (Practice) - 240 pts  │
│  3. Bob (102) - 230 pts         │
│                                 │
│  [Play Again] [Exit]            │
│                                 │
└─────────────────────────────────┘
```

#### 5. Results Screen (Practice Mode)
```
┌─────────────────────────────────┐
│  🎮 Practice Complete!          │
├─────────────────────────────────┤
│                                 │
│  Your Score: 240 points         │
│  Mode: Practice                 │
│  Time: 48s                      │
│                                 │
│  ═══════════════════            │
│                                 │
│  📈 GENERAL LEADERBOARD         │
│  1. Alice (101) - 245 pts       │
│  2. You (Practice) - 240 pts ⭐ │
│  3. Bob (102) - 230 pts         │
│                                 │
│  💡 Want to compete?            │
│  Try Tournament Mode!           │
│                                 │
│  [Play Tournament] [Exit]       │
│                                 │
└─────────────────────────────────┘
```

---

## 🔧 Technical Details

### Database Models

#### QuizSession
```python
{
  "id": UUID,
  "hotel_identifier": string,
  "quiz": FK(Quiz),
  "player_name": string (max 100 chars),
  "room_number": string | null (max 50 chars),
  "external_player_id": string | null,
  "is_practice_mode": boolean (default: false),
  "score": integer (default: 0),
  "started_at": datetime,
  "finished_at": datetime | null,
  "is_completed": boolean,
  "time_spent_seconds": integer,
  "current_question_index": integer,
  "consecutive_correct": integer (default: 0),
  "current_multiplier": integer (default: 1, max: 128)
}
```

#### QuizSubmission
```python
{
  "id": UUID,
  "hotel_identifier": string,
  "session": FK(QuizSession),
  "question": FK(QuizQuestion) | null,  # null for math
  "question_text": string,
  "question_data": JSON | null,  # for math questions
  "selected_answer": string,
  "selected_answer_id": integer | null,
  "is_correct": boolean,
  "base_points": integer,
  "points_awarded": integer,
  "time_taken_seconds": integer,
  "multiplier_used": integer,
  "answered_at": datetime
}
```

### Serializers

All serializers include the new fields:
- `QuizSessionSerializer`: Includes `room_number`, `is_practice_mode`, `consecutive_correct`, `current_multiplier`
- `QuizLeaderboardSerializer`: Includes `room_number`, `is_practice_mode`

### Admin Panel

Updated to show:
- Room number in list view
- Practice mode indicator
- Current multiplier
- Consecutive correct count
- Separate fieldset for "Turbo Mode" stats

---

## 🚀 Quick Start Checklist

### Backend (Completed ✓)
- [x] 5 difficulty levels with 100 questions each (+ dynamic math)
- [x] Turbo mode scoring (multiplier doubling, timeout breaks streak)
- [x] Room number field for tournament entries
- [x] Practice mode flag
- [x] Two leaderboard endpoints (general & tournament)
- [x] Updated serializers with new fields
- [x] Updated admin panel
- [x] URL routes configured

### Frontend (To Do)
- [ ] Mode selection screen (tournament vs practice)
- [ ] Room number input for tournament mode
- [ ] Question display with timer
- [ ] Real-time multiplier display
- [ ] Answer feedback showing points calculation
- [ ] Results screen with both leaderboards
- [ ] Different result screens for practice vs tournament
- [ ] Leaderboard fetching and display

---

## 📊 Testing Data

Use `test_leaderboards.py` to generate sample data:
- Creates 5 sessions (3 tournament, 2 practice)
- Verifies both leaderboards work correctly
- Confirms practice mode exclusion from tournament board

---

## 🎯 Best Practices

### For Tournament Mode
1. Always validate room numbers
2. Clearly indicate tournament status to players
3. Show both leaderboards in results
4. Highlight player's position in tournament

### For Practice Mode
5. Make it clear scores won't count for prizes
6. Encourage players to try tournament mode
7. Show general leaderboard only
8. Use different visual styling

### For Turbo Mode
9. Show current multiplier prominently
10. Display streak counter
11. Animate multiplier changes
12. Show "STREAK BROKEN" on timeout/wrong answer
13. Celebrate high multipliers (8x+)

### For UX
14. 5-second countdown is critical - make it visual
15. Disable answer selection after time runs out
16. Show points calculation breakdown
17. Provide instant feedback on correct/wrong answers

---

## 📞 Support

For questions or issues:
- Check admin panel at `/admin/entertainment/`
- Review test files: `test_leaderboards.py`, `test_timing_points.py`
- API documentation: `QUIZ_GAME_API.md`

---

**Game is ready for frontend integration! 🎮🚀**
