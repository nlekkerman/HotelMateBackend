# Quiz Game - Category by Category API

This document describes the **category-by-category API** that fetches questions **one category at a time** as the player progresses through the game.

---

## API Flow

### 1. Start Session (No Questions)
**POST** `/api/entertainment/quiz/game/start_session/`

**Request:**
```json
{
  "player_name": "John",
  "session_token": "unique-token-123",
  "is_tournament_mode": false
}
```

**Response:**
```json
{
  "session": {
    "id": "uuid-session-id",
    "player_name": "John",
    "session_token": "unique-token-123",
    "score": 0,
    "consecutive_correct": 0,
    "is_turbo_active": false,
    "current_category_index": 0,
    "current_question_index": 0,
    "is_completed": false
  },
  "categories": [
    {
      "id": 1,
      "name": "Classic Trivia",
      "slug": "classic-trivia",
      "order": 0,
      "is_math_category": false,
      "question_count": 10
    },
    {
      "id": 2,
      "name": "Odd One Out",
      "slug": "odd-one-out",
      "order": 1,
      "is_math_category": false,
      "question_count": 10
    },
    {
      "id": 3,
      "name": "Fill The Blank",
      "slug": "fill-the-blank",
      "order": 2,
      "is_math_category": false,
      "question_count": 10
    },
    {
      "id": 4,
      "name": "Quick Math",
      "slug": "dynamic-math",
      "order": 3,
      "is_math_category": true,
      "question_count": "Dynamic"
    },
    {
      "id": 5,
      "name": "Knowledge Trap",
      "slug": "knowledge-trap",
      "order": 4,
      "is_math_category": false,
      "question_count": 10
    }
  ],
  "total_categories": 5,
  "questions_per_category": 10,
  "game_rules": {
    "time_per_question_seconds": 5,
    "turbo_mode_threshold": 5,
    "turbo_multiplier": "2.0",
    "scoring": [
      "5 points for answer within 1 second",
      "4 points for answer within 2 seconds",
      "3 points for answer within 3 seconds",
      "2 points for answer within 4 seconds",
      "0 points for answer after 5 seconds or wrong answer"
    ],
    "turbo_mode": [
      "Get 5 consecutive correct answers to activate TURBO MODE",
      "TURBO MODE doubles your points (10-8-6-4-0)",
      "Wrong answer breaks your streak and deactivates Turbo Mode"
    ]
  }
}
```

---

### 2. Fetch Questions for a Category
**GET** `/api/entertainment/quiz/game/fetch_category_questions/?session_id={session_id}&category_slug={category_slug}`

**Parameters:**
- `session_id` - The UUID of the game session
- `category_slug` - The slug of the category (e.g., "classic-trivia")

**Example:**
```
GET /api/entertainment/quiz/game/fetch_category_questions/?session_id=abc-123&category_slug=classic-trivia
```

**Response:**
```json
{
  "category": {
    "id": 1,
    "name": "Classic Trivia",
    "slug": "classic-trivia",
    "order": 0,
    "is_math_category": false
  },
  "questions": [
    {
      "id": 123,
      "category_slug": "classic-trivia",
      "category_name": "Classic Trivia",
      "category_order": 0,
      "text": "What is the capital of France?",
      "image_url": null,
      "answers": [
        {"id": 1, "text": "Paris", "order": 0},
        {"id": 2, "text": "London", "order": 1},
        {"id": 3, "text": "Berlin", "order": 2},
        {"id": 4, "text": "Madrid", "order": 3}
      ]
    },
    {
      "id": 124,
      "category_slug": "classic-trivia",
      "category_name": "Classic Trivia",
      "category_order": 0,
      "text": "Who painted the Mona Lisa?",
      "image_url": null,
      "answers": [
        {"id": 5, "text": "Leonardo da Vinci", "order": 0},
        {"id": 6, "text": "Michelangelo", "order": 1},
        {"id": 7, "text": "Raphael", "order": 2},
        {"id": 8, "text": "Donatello", "order": 3}
      ]
    }
    // ... 8 more questions (total 10 per category)
  ],
  "question_count": 10
}
```

**For Math Category:**
```json
{
  "category": {
    "id": 4,
    "name": "Quick Math",
    "slug": "dynamic-math",
    "order": 3,
    "is_math_category": true
  },
  "questions": [
    {
      "id": null,
      "category_slug": "dynamic-math",
      "category_name": "Quick Math",
      "category_order": 3,
      "text": "7 × 8 = ?",
      "image_url": null,
      "answers": [
        {"id": 1, "text": "56", "order": 0},
        {"id": 2, "text": "54", "order": 1},
        {"id": 3, "text": "59", "order": 2},
        {"id": 4, "text": "53", "order": 3}
      ]
    }
    // ... 9 more dynamically generated math questions
  ],
  "question_count": 10
}
```

---

### 3. Submit Answer
**POST** `/api/entertainment/quiz/game/submit_answer/`

**Request:**
```json
{
  "session_id": "uuid-session-id",
  "category_slug": "classic-trivia",
  "question_id": 123,
  "answer_id": 1,
  "time_taken_seconds": 2.5
}
```

**For Math Questions:**
```json
{
  "session_id": "uuid-session-id",
  "category_slug": "dynamic-math",
  "answer_text": "56",
  "time_taken_seconds": 3.2,
  "question_data": {
    "text": "7 × 8 = ?",
    "correct_answer": "56"
  }
}
```

**Response:**
```json
{
  "correct": true,
  "points_earned": 3,
  "total_score": 3,
  "consecutive_correct": 1,
  "is_turbo_active": false,
  "turbo_progress": "1/5",
  "correct_answer": "Paris"
}
```

---

### 4. Complete Session
**POST** `/api/entertainment/quiz/game/complete_session/`

**Request:**
```json
{
  "session_id": "uuid-session-id"
}
```

**Response:**
```json
{
  "session": {
    "id": "uuid-session-id",
    "player_name": "John",
    "final_score": 185,
    "is_completed": true,
    "completed_at": "2025-11-14T10:30:00Z"
  },
  "leaderboard_rank": 5,
  "total_players": 42
}
```

---

## Frontend Implementation Guide

### Game Flow

1. **Start Game**
   - Call `start_session` to get session ID and categories list
   - Display game rules to player
   - Start with first category (order 0)

2. **For Each Category**
   - Call `fetch_category_questions` with session_id and category_slug
   - Store questions locally for this category
   - Display category transition animation
   - Show first question

3. **For Each Question**
   - Display question and answers
   - Start timer (5 seconds)
   - Wait for player to select answer
   - Call `submit_answer` with time taken
   - Show feedback (correct/wrong, points earned)
   - Move to next question

4. **Category Transition**
   - When all 10 questions in category are answered
   - Fetch next category's questions
   - Show category transition animation
   - Continue with next category

5. **Complete Game**
   - After all categories completed
   - Call `complete_session`
   - Display final score and leaderboard rank

---

## Example React Implementation

```javascript
const QuizGame = () => {
  const [session, setSession] = useState(null);
  const [categories, setCategories] = useState([]);
  const [currentCategoryIndex, setCurrentCategoryIndex] = useState(0);
  const [currentQuestions, setCurrentQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  // Step 1: Start session
  const startGame = async (playerName, sessionToken) => {
    const response = await fetch('/api/entertainment/quiz/game/start_session/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        player_name: playerName, 
        session_token: sessionToken 
      })
    });
    const data = await response.json();
    
    setSession(data.session);
    setCategories(data.categories);
    
    // Fetch first category questions
    fetchCategoryQuestions(data.session.id, data.categories[0].slug);
  };

  // Step 2: Fetch category questions
  const fetchCategoryQuestions = async (sessionId, categorySlug) => {
    const response = await fetch(
      `/api/entertainment/quiz/game/fetch_category_questions/?session_id=${sessionId}&category_slug=${categorySlug}`
    );
    const data = await response.json();
    
    setCurrentQuestions(data.questions);
    setCurrentQuestionIndex(0);
  };

  // Step 3: Submit answer
  const submitAnswer = async (answerId, timeTaken) => {
    const currentQuestion = currentQuestions[currentQuestionIndex];
    
    const response = await fetch('/api/entertainment/quiz/game/submit_answer/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: session.id,
        category_slug: currentQuestion.category_slug,
        question_id: currentQuestion.id,
        answer_id: answerId,
        time_taken_seconds: timeTaken
      })
    });
    const data = await response.json();
    
    // Update score
    setSession(prev => ({ ...prev, score: data.total_score }));
    
    // Show feedback
    showFeedback(data);
    
    // Move to next question or category
    if (currentQuestionIndex < currentQuestions.length - 1) {
      // Next question in same category
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else if (currentCategoryIndex < categories.length - 1) {
      // Next category
      const nextCategoryIndex = currentCategoryIndex + 1;
      setCurrentCategoryIndex(nextCategoryIndex);
      showCategoryTransition(categories[nextCategoryIndex].name);
      fetchCategoryQuestions(session.id, categories[nextCategoryIndex].slug);
    } else {
      // Game complete
      completeGame();
    }
  };

  // Step 4: Complete game
  const completeGame = async () => {
    const response = await fetch('/api/entertainment/quiz/game/complete_session/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: session.id })
    });
    const data = await response.json();
    
    showGameComplete(data);
  };

  return (
    <div>
      {/* Game UI components */}
    </div>
  );
};
```

---

## Key Benefits

✅ **One category at a time** - Load questions as needed  
✅ **Reduced initial load** - Faster game start  
✅ **Progressive loading** - Better UX with loading states  
✅ **Category transitions** - Clear separation between categories  
✅ **Streak always resets** - Fresh start every game  
✅ **Question tracking** - No repeats until all questions seen  

---

## Important Notes

- **No Resume Feature**: Each start_session creates a fresh game
- **Session Token**: Use unique token per player to track progress
- **Math Questions**: Generated dynamically, have `id: null`
- **Time Tracking**: Frontend must track time and submit with answer
- **Turbo Mode**: Activates after 5 consecutive correct answers
- **Points**: Based on time taken (5-4-3-2-0 points, doubled in turbo mode)
