# 🎮 GUESSTICULATOR QUIZ - FRONTEND INTEGRATION GUIDE

## ✅ WHAT'S READY (BACKEND COMPLETE)

### Database Setup ✓
- All quiz tables migrated and ready
- 2 categories with questions loaded:
  - **History** 📚 (100 True/False questions)
  - **Music** 🎵 (70 Multiple choice questions)

### API Endpoints Available ✓
Base URL: `http://localhost:8000/api/entertainment/`

---

## 🚀 QUICK START FOR FRONTEND

### STEP 1: Start a Quiz Session
**Endpoint:** `POST /quiz-sessions/start_quiz/`

```javascript
// Generate unique player token
const playerToken = `player_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
const playerName = `${username}|${playerToken}`;

// Start quiz
const response = await fetch('http://localhost:8000/api/entertainment/quiz-sessions/start_quiz/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    player_name: playerName,
    questions_per_quiz: 20  // Can be any number
  })
});

const data = await response.json();
// Returns: { session, categories, questions }
```

**Response Example:**
```json
{
  "session": {
    "id": 1,
    "player_name": "Alice|player_abc123",
    "selected_categories": [1, 2],
    "total_questions": 20,
    "completed": false
  },
  "categories": [
    { "id": 1, "name": "History", "icon": "📚", "color": "#8B4513" },
    { "id": 2, "name": "Music", "icon": "🎵", "color": "#9333EA" }
  ],
  "questions": [
    {
      "id": 1,
      "category_name": "History",
      "question_text": "The Roman Empire fell in 476 AD.",
      "difficulty": "easy",
      "option_a": "True",
      "option_b": "False",
      "option_c": "",
      "option_d": "",
      "points": 10
    },
    {
      "id": 51,
      "category_name": "Music",
      "question_text": "The composer of 'The Four Seasons' was ______.",
      "difficulty": "medium",
      "option_a": "Bach",
      "option_b": "Vivaldi",
      "option_c": "Mozart",
      "option_d": "Beethoven",
      "points": 10
    }
    // ... 18 more questions
  ]
}
```

---

### STEP 2: Display Questions to Player

```javascript
// Store session info
localStorage.setItem('quiz_session_id', data.session.id);
localStorage.setItem('player_token', playerToken);

// Loop through questions and display
data.questions.forEach((question, index) => {
  // Render question UI
  const questionHTML = `
    <div class="question" data-question-id="${question.id}">
      <h3>Question ${index + 1}</h3>
      <p>${question.question_text}</p>
      <div class="options">
        <button onclick="selectAnswer(${question.id}, 'A')">${question.option_a}</button>
        <button onclick="selectAnswer(${question.id}, 'B')">${question.option_b}</button>
        ${question.option_c ? `<button onclick="selectAnswer(${question.id}, 'C')">${question.option_c}</button>` : ''}
        ${question.option_d ? `<button onclick="selectAnswer(${question.id}, 'D')">${question.option_d}</button>` : ''}
      </div>
    </div>
  `;
});
```

---

### STEP 3: Submit Each Answer

**Endpoint:** `POST /quiz-sessions/{session_id}/submit_answer/`

```javascript
const selectAnswer = async (questionId, selectedAnswer) => {
  const sessionId = localStorage.getItem('quiz_session_id');
  const timeSeconds = getTimeForQuestion(); // Your timer logic
  
  const response = await fetch(
    `http://localhost:8000/api/entertainment/quiz-sessions/${sessionId}/submit_answer/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_id: questionId,
        selected_answer: selectedAnswer,
        time_seconds: timeSeconds  // Optional
      })
    }
  );
  
  const answer = await response.json();
  
  // Show feedback
  if (answer.is_correct) {
    showCorrectFeedback();
  } else {
    showIncorrectFeedback();
  }
  
  // Move to next question
  nextQuestion();
};
```

**Response Example:**
```json
{
  "id": 1,
  "question": 1,
  "question_text": "The Roman Empire fell in 476 AD.",
  "category_name": "History",
  "selected_answer": "A",
  "is_correct": true,
  "time_seconds": 8,
  "answered_at": "2025-11-14T10:30:45Z"
}
```

---

### STEP 4: Complete the Quiz

**Endpoint:** `POST /quiz-sessions/{session_id}/complete_session/`

```javascript
const completeQuiz = async (totalTime) => {
  const sessionId = localStorage.getItem('quiz_session_id');
  
  const response = await fetch(
    `http://localhost:8000/api/entertainment/quiz-sessions/${sessionId}/complete_session/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        time_seconds: totalTime  // Optional: total quiz time
      })
    }
  );
  
  const session = await response.json();
  
  // Display results
  displayResults({
    score: session.score,
    correctAnswers: session.correct_answers,
    totalQuestions: session.total_questions
  });
};
```

**Response Example:**
```json
{
  "id": 1,
  "player_name": "Alice|player_abc123",
  "score": 285,
  "correct_answers": 15,
  "total_questions": 20,
  "completed": true,
  "answers": [
    {
      "question": 1,
      "selected_answer": "A",
      "is_correct": true,
      "time_seconds": 8
    }
    // ... all answers
  ]
}
```

---

### STEP 5: Show Leaderboard

**Endpoint:** `GET /quiz-leaderboard/`

```javascript
const fetchLeaderboard = async () => {
  const response = await fetch('http://localhost:8000/api/entertainment/quiz-leaderboard/');
  const leaderboard = await response.json();
  
  // Display top players
  leaderboard.forEach((entry, index) => {
    console.log(`${index + 1}. ${entry.player_display_name} - ${entry.best_score} points`);
  });
};
```

**Response Example:**
```json
[
  {
    "id": 1,
    "player_display_name": "Alice",
    "best_score": 350,
    "rank": 1,
    "total_games_played": 8
  },
  {
    "id": 2,
    "player_display_name": "Bob",
    "best_score": 320,
    "rank": 2,
    "total_games_played": 5
  }
]
```

---

### STEP 6: Get My Rank

**Endpoint:** `GET /quiz-leaderboard/my_rank/?player_token={token}`

```javascript
const fetchMyRank = async () => {
  const playerToken = localStorage.getItem('player_token');
  
  const response = await fetch(
    `http://localhost:8000/api/entertainment/quiz-leaderboard/my_rank/?player_token=${playerToken}`
  );
  
  if (response.ok) {
    const myEntry = await response.json();
    console.log(`Your rank: #${myEntry.rank} with ${myEntry.best_score} points`);
  } else {
    console.log("You're not on the leaderboard yet!");
  }
};
```

---

## 🎯 SCORING SYSTEM

### How Scores are Calculated:
```
Score = Σ (Question Points × Difficulty × Time Bonus)

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

## ⚠️ IMPORTANT NOTES

### Current Limitation: Only 2 Categories
- We currently have **History** and **Music** categories
- The slot machine needs **at least 5 categories** to work properly
- **Frontend should NOT call the slot machine endpoint yet**
- Instead, use `start_quiz` which will distribute questions from available categories

### What Happens Now:
When you call `start_quiz`, the backend will:
1. Use all available categories (History + Music)
2. Distribute questions evenly between them
3. Return mixed questions from both categories

### When We Have 10 Categories:
The slot machine will:
1. Randomly select 5 from 10 categories
2. Each quiz session gets different category combinations
3. More variety and replayability

---

## 📝 FRONTEND TODO CHECKLIST

- [ ] Create quiz start screen (player name input)
- [ ] Implement question display UI
  - [ ] Handle True/False questions (only 2 options)
  - [ ] Handle Multiple choice questions (4 options)
- [ ] Add timer for each question (optional)
- [ ] Implement answer submission
- [ ] Show immediate feedback (correct/incorrect)
- [ ] Display final score screen
- [ ] Create leaderboard view
- [ ] Add "Play Again" functionality
- [ ] Handle errors gracefully

---

## 🎨 UI RECOMMENDATIONS

1. **Category Colors**: Use the color codes from API
   - History: `#8B4513` (brown)
   - Music: `#9333EA` (purple)

2. **Icons**: Display category icons
   - History: 📚
   - Music: 🎵

3. **Progress Bar**: Show question X of Y

4. **Score Animation**: Animate score updates

5. **Leaderboard**: Highlight current player

---

## 🔧 TESTING THE API

### Test with cURL or Postman:

```bash
# 1. Start a quiz
curl -X POST http://localhost:8000/api/entertainment/quiz-sessions/start_quiz/ \
  -H "Content-Type: application/json" \
  -d '{"player_name": "TestPlayer|player_test123", "questions_per_quiz": 10}'

# 2. Submit answer
curl -X POST http://localhost:8000/api/entertainment/quiz-sessions/1/submit_answer/ \
  -H "Content-Type: application/json" \
  -d '{"question_id": 1, "selected_answer": "A", "time_seconds": 5}'

# 3. Complete quiz
curl -X POST http://localhost:8000/api/entertainment/quiz-sessions/1/complete_session/ \
  -H "Content-Type: application/json" \
  -d '{"time_seconds": 120}'

# 4. Get leaderboard
curl http://localhost:8000/api/entertainment/quiz-leaderboard/
```

---

## 📚 FULL API DOCUMENTATION

See `QUIZ_API_DOCS.md` for complete API reference with all endpoints, parameters, and responses.

---

## ❓ NEED HELP?

**Backend is running at:** `http://localhost:8000`

**Admin panel:** `http://localhost:8000/admin`
- View all questions
- Check quiz sessions
- See leaderboard entries

**Questions?** Check the documentation or ask!

---

## 🚀 NEXT STEPS

1. **For Now**: Build frontend with 2 categories (History + Music)
2. **Later**: We'll add 8 more categories (10 total)
3. **Then**: Slot machine will activate automatically
4. **Finally**: Tournament mode integration

Start building the UI and test with the current 2 categories. The quiz system is fully functional!
