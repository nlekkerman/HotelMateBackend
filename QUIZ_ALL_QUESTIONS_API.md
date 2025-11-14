# Quiz Game - All Questions at Once API

## Changes Made ✅

### Backend Updates:
1. **Streak resets** on every game start and resume (consecutive_correct = 0, is_turbo_active = false)
2. **All 50 questions sent at once** - No need for multiple API calls per category
3. **Game rules included** in start_session response

---

## API Response Structure

### POST `/api/entertainment/quiz/game/start_session/`

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
    "id": "uuid",
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
  "all_questions": [
    // Questions 0-9: Category 1 (Classic Trivia)
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
    // ... 9 more questions for category 1
    
    // Questions 10-19: Category 2 (Odd One Out)
    {
      "id": 234,
      "category_slug": "odd-one-out",
      "category_name": "Odd One Out",
      "category_order": 1,
      "text": "Which one doesn't belong?",
      "image_url": null,
      "answers": [...]
    },
    // ... 9 more questions for category 2
    
    // Questions 20-29: Category 3 (Fill The Blank)
    // Questions 30-39: Category 4 (Quick Math)
    {
      "id": null,
      "category_slug": "dynamic-math",
      "category_name": "Quick Math",
      "category_order": 3,
      "text": "5 × 7 = ?",
      "image_url": null,
      "answers": [
        {"id": 1, "text": "35", "order": 0},
        {"id": 2, "text": "32", "order": 1},
        {"id": 3, "text": "38", "order": 2},
        {"id": 4, "text": "40", "order": 3}
      ],
      "question_data": {
        "num1": 5,
        "num2": 7,
        "operator": "*",
        "correct_answer": 35
      }
    },
    // ... 9 more math questions
    
    // Questions 40-49: Category 5 (Knowledge Trap)
    // Total: 50 questions
  ],
  "total_categories": 5,
  "questions_per_category": 10,
  "total_questions": 50,
  "game_rules": {
    "time_per_question": 5,
    "turbo_mode_threshold": 5,
    "turbo_multiplier": 2.0,
    "scoring": {
      "normal": {
        "0s": 5,
        "1s": 5,
        "2s": 4,
        "3s": 3,
        "4s": 2,
        "5s": 0
      },
      "turbo": {
        "0s": 10,
        "1s": 10,
        "2s": 8,
        "3s": 6,
        "4s": 4,
        "5s": 0
      }
    },
    "instructions": [
      "Answer 10 questions from each of the 5 categories",
      "You have 5 seconds per question",
      "Get 5 correct answers in a row to activate TURBO MODE (2x points)",
      "Wrong answer breaks your streak and deactivates Turbo Mode",
      "Faster answers = more points (5-4-3-2-0 points)",
      "Complete all 50 questions to finish the game"
    ]
  }
}
```

---

## Frontend Implementation Guide

### 1. Store All Questions on Game Start

```javascript
const startGame = async (playerName, sessionToken, isTournament = false) => {
  const response = await fetch('/api/entertainment/quiz/game/start_session/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_name: playerName,
      session_token: sessionToken,
      is_tournament_mode: isTournament
    })
  });
  
  const data = await response.json();
  
  // Store everything in state
  setSession(data.session);
  setCategories(data.categories);
  setAllQuestions(data.all_questions);
  setGameRules(data.game_rules);
  setCurrentQuestionIndex(0);
  
  return data;
};
```

### 2. Navigate Through Questions by Index

```javascript
const QuizGame = () => {
  const [allQuestions, setAllQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [session, setSession] = useState(null);
  
  const currentQuestion = allQuestions[currentIndex];
  const currentCategory = currentQuestion?.category_name;
  const categoryOrder = currentQuestion?.category_order;
  
  // Category progress (0-9 for each category)
  const categoryProgress = currentIndex % 10;
  
  // Overall progress (0-49)
  const overallProgress = currentIndex;
  
  const handleNextQuestion = () => {
    if (currentIndex < allQuestions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      
      // Check if entering new category
      const newQuestion = allQuestions[currentIndex + 1];
      if (newQuestion.category_order !== currentQuestion.category_order) {
        showCategoryTransition(newQuestion.category_name);
      }
    } else {
      completeGame();
    }
  };
  
  return (
    <div>
      <CategoryIndicator 
        currentCategory={currentCategory}
        categoryOrder={categoryOrder}
      />
      
      <ProgressBar 
        current={overallProgress + 1}
        total={allQuestions.length}
      />
      
      <Question question={currentQuestion} />
      
      <QuestionCounter>
        Question {categoryProgress + 1} of 10 (Category {categoryOrder + 1})
      </QuestionCounter>
    </div>
  );
};
```

### 3. Category Recognition

```javascript
// Show which category you're in
const CategoryIndicator = ({ currentCategory, categoryOrder }) => {
  const categoryColors = [
    '#ef4444', // red - Classic Trivia
    '#f59e0b', // orange - Odd One Out
    '#eab308', // yellow - Fill The Blank
    '#22c55e', // green - Quick Math
    '#3b82f6'  // blue - Knowledge Trap
  ];
  
  return (
    <div 
      className="category-badge"
      style={{ backgroundColor: categoryColors[categoryOrder] }}
    >
      <span>Category {categoryOrder + 1}</span>
      <h3>{currentCategory}</h3>
    </div>
  );
};
```

### 4. Category Transition Animation

```javascript
const showCategoryTransition = (newCategoryName) => {
  // Show full-screen category transition
  setShowTransition(true);
  
  setTimeout(() => {
    setShowTransition(false);
  }, 2000);
};

// Component
{showTransition && (
  <div className="category-transition">
    <h2>Next Category</h2>
    <h1>{allQuestions[currentIndex].category_name}</h1>
    <p>Get ready! 10 questions coming up...</p>
  </div>
)}
```

### 5. Show Game Rules at Start

```javascript
const GameRulesScreen = ({ rules, onStart }) => {
  return (
    <div className="rules-screen">
      <h1>How to Play</h1>
      
      <div className="rules-list">
        {rules.instructions.map((instruction, i) => (
          <div key={i} className="rule-item">
            <span className="rule-number">{i + 1}</span>
            <p>{instruction}</p>
          </div>
        ))}
      </div>
      
      <div className="scoring-info">
        <h3>Scoring</h3>
        <div className="scoring-grid">
          <div>
            <h4>Normal Mode</h4>
            <ul>
              <li>0-1 seconds: 5 points</li>
              <li>2 seconds: 4 points</li>
              <li>3 seconds: 3 points</li>
              <li>4 seconds: 2 points</li>
              <li>5+ seconds: 0 points</li>
            </ul>
          </div>
          <div>
            <h4>🔥 Turbo Mode (2x)</h4>
            <ul>
              <li>0-1 seconds: 10 points</li>
              <li>2 seconds: 8 points</li>
              <li>3 seconds: 6 points</li>
              <li>4 seconds: 4 points</li>
              <li>5+ seconds: 0 points</li>
            </ul>
          </div>
        </div>
      </div>
      
      <button onClick={onStart}>Start Game</button>
    </div>
  );
};
```

---

## Key Benefits

✅ **Single API call** - Get all 50 questions at once  
✅ **No loading between categories** - Smooth gameplay  
✅ **Category recognition** - Each question has `category_name` and `category_order`  
✅ **Game rules included** - Show instructions before starting  
✅ **Streak always resets** - Fresh start every game  
✅ **Offline-capable** - Can play without internet after initial load

---

## Question Array Structure

```javascript
// Questions are ordered by category
// Index 0-9: Category 1
// Index 10-19: Category 2
// Index 20-29: Category 3
// Index 30-39: Category 4
// Index 40-49: Category 5

const getCurrentCategory = (index) => {
  return Math.floor(index / 10); // Returns 0-4
};

const getCategoryProgress = (index) => {
  return (index % 10) + 1; // Returns 1-10
};

// Example: Question 23
// Category: Math.floor(23 / 10) = 2 (3rd category)
// Progress: (23 % 10) + 1 = 4 (4th question in category)
```
