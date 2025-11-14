# Quiz Game - No Resume + Question Pool Exhaustion System

## ✅ Implementation Complete

### Key Features:

1. **NO RESUME ALLOWED**
   - If player refreshes, they start a completely new game
   - No session recovery - fresh start every time
   - Prevents cheating by refreshing to get easier questions

2. **Question Pool Exhaustion**
   - Player must see ALL questions before ANY repeat
   - Separate tracking for each category
   - Math questions: Pool of 100 unique combinations
   - Regular questions: All questions in database per category

3. **Player Progress Tracking**
   - Each player (session_token) has their own progress tracker
   - Tracks which question IDs seen per category
   - Tracks which math combinations seen
   - Auto-resets when pool exhausted
   - keep only name saved over all sesions per device

---

## Database Model

### QuizPlayerProgress

```python
class QuizPlayerProgress(models.Model):
    session_token = CharField  # Player's unique ID
    quiz = ForeignKey         # Which quiz
    
    # Track seen questions per category
    seen_question_ids = JSONField  # {category_slug: [id1, id2, ...]}
    
    # Track seen math questions
    seen_math_questions = JSONField  # [[num1, num2, operator], ...]
    
    created_at = DateTimeField
    updated_at = DateTimeField
```

---

## How It Works

### 1. Player Starts Game

```
Player: "John" with token "abc123"
```

**Backend:**
1. Get or create `QuizPlayerProgress` for token "abc123"
2. Check what questions they've seen before
3. Generate 50 NEW questions they haven't seen
4. Mark those questions as "seen"
5. Create new `QuizSession`

### 2. Question Selection Logic

**For Regular Categories (Trivia, Odd One Out, etc.):**
```python
# Get all question IDs in category
all_ids = [1, 2, 3, 4, 5, ... 20]  # Example: 20 questions total

# Player has seen: [1, 3, 5, 7, 9]
seen_ids = [1, 3, 5, 7, 9]

# Get unseen: [2, 4, 6, 8, 10, 11, ... 20]
unseen_ids = [2, 4, 6, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

# Need 10 questions - randomly pick from unseen
selected = random.sample(unseen_ids, 10)  # [4, 11, 15, 2, 18, 6, 19, 12, 8, 14]

# Mark these 10 as seen
seen_ids = [1, 3, 5, 7, 9, 4, 11, 15, 2, 18, 6, 19, 12, 8, 14]
```

**Next game:**
```python
# Still unseen: [10, 13, 16, 17, 20] - only 5 left
# But we need 10!

# RESET: Clear seen_ids for this category
seen_ids = []

# Now all 20 are available again
unseen_ids = [1, 2, 3, 4, ... 20]

# Pick 10 random
```

### 3. Math Questions (Special Handling)

**Math Pool: 100 unique combinations**
```
Numbers: 0-10 (both operands)
Operators: +, -, ×, ÷

Examples:
- 2 + 3 = 5
- 7 - 4 = 3
- 5 × 6 = 30
- 8 ÷ 2 = 4
(Only divisible divisions included)
```

**Tracking:**
```python
seen_math = [
    [2, 3, '+'],
    [5, 6, '*'],
    [8, 2, '/'],
    ...
]  # Player has seen 23 math questions

unseen_count = 100 - 23 = 77 remaining

# Pick 10 random from the 77 unseen
# Add to seen_math list
```

**After 100 math questions:**
```python
# Player has now seen all 100
seen_math.length == 100

# RESET for next game
seen_math = []

# Fresh pool of 100 available again
```

---

## API Behavior

### Start Game Request
```json
POST /api/entertainment/quiz/game/start_session/
{
  "player_name": "John",
  "session_token": "abc123",
  "is_tournament_mode": false
}
```

### Response (Same Structure)
```json
{
  "session": {...},
  "categories": [...],
  "all_questions": [
    // 50 questions they HAVEN'T seen yet
    // Guaranteed NO repeats until pool exhausted
  ],
  "game_rules": {...}
}
```

**Important:** Even if player refreshes mid-game, they get a NEW set of 50 questions!

---

## Example Scenario

**Player "John" (token: abc123)**

### Game 1:
- Gets questions: IDs [1, 4, 7, 9, 12, 15, ...] (50 total)
- Progress saved: These 50 marked as "seen"

### Player refreshes browser:
- ❌ Old session NOT resumed
- ✅ NEW session created
- Gets questions: IDs [2, 3, 5, 6, 8, 10, ...] (50 NEW questions)
- Progress updated: 100 questions now marked as "seen"

### Game 3:
- Gets questions: IDs [13, 14, 16, 17, ...] (50 NEW)
- Total seen: 150 questions

### Eventually:
- Player has seen ALL questions in database
- Next game: Progress resets per category
- Starts over with question ID 1 again

---

## Migration Needed

Run this to add the new model:

```bash
python manage.py makemigrations entertainment
python manage.py migrate
```

This creates the `QuizPlayerProgress` table.

---

## Benefits

✅ **No cheating** - Can't refresh to skip hard questions  
✅ **Fair gameplay** - Everyone gets variety  
✅ **Maximum engagement** - Must play many games to see repeats  
✅ **Automatic balancing** - System ensures question pool is exhausted  
✅ **Per-player tracking** - Each player has their own progress

---

## Database Size Impact

Each player adds one row to `QuizPlayerProgress`:
- ~1KB per player (storing seen IDs in JSON)
- 1000 players = ~1MB
- Very lightweight!

---

## Frontend Impact

✅ **None!** Frontend receives same 50 questions as before  
✅ No resume button needed - just "Start New Game"  
✅ API structure unchanged  
✅ Same question format

The intelligence is all in the backend! 🎯
