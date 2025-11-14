# GUESSTICULATOR QUIZ GAME - DEVELOPMENT TODOS

## 🎯 OVERVIEW
Building a quiz game with:
- 🎰 **Slot Machine System**: Random selection of 5 from 10 categories
- 👥 **Anonymous Players**: Session token + player name (no auth required)
- 🎮 **Two Modes**: Casual Play & Tournament Mode
- 📊 **Two Leaderboards**: General (best per player) & Tournament (all active plays)

---

## ✅ TODO LIST

### 1. Design Quiz Models Structure
**Status**: Not Started  
**Description**: Create core models
- `QuizCategory` - 10 main categories with metadata
- `QuizQuestion` - Questions linked to categories with difficulty levels
- `QuizSession` - Tracks player+token, selected categories, score
- `QuizTournament` - Active/completed tournaments
- `QuizAnswer` - Player responses for each question

---

### 2. Implement Slot Machine Category Selection
**Status**: Not Started  
**Description**: Random category selection at quiz start
- Method to randomly select 5 from 10 available categories
- Store selected category IDs in `QuizSession.selected_categories` (JSONField)
- Ensure fair distribution and no duplicates in selection

---

### 3. Create Question Distribution Logic
**Status**: Not Started  
**Description**: Pull questions from selected categories
- Implement logic to fetch questions from the 5 selected categories
- Distribute questions evenly across selected categories
- Handle cases where categories have different question counts

---

### 4. Add Anonymous Player Support
**Status**: Not Started  
**Description**: Session-based player tracking
- Implement `player_name` + `session_token` system
- Format: `"PlayerName|token"` (e.g., `"Alice|player_abc123"`)
- Works for both casual and tournament play
- No user authentication required

---

### 5. Create Quiz Scoring System
**Status**: Not Started  
**Description**: Calculate and store scores
- Base points per correct answer
- Time penalties (if implemented)
- Difficulty bonuses (easy/medium/hard)
- Calculate final score and store in `QuizSession`

---

### 6. Build General Leaderboard System
**Status**: Not Started  
**Description**: Global best scores (no duplicates per player)
- Create `QuizLeaderboard` model
- Store BEST score per player only
- Use `player_token` as unique identifier
- Update only when new score beats existing score
- Show global ranking across all time

---

### 7. Build Tournament Mode & Tournament Leaderboard
**Status**: Not Started  
**Description**: Active tournament tracking
- Create `QuizTournament` model (active/completed status)
- Tournament leaderboard shows ALL plays during active period
- Separate from general leaderboard
- Tracks start_date, end_date, status

---

### 8. Add Tournament Features
**Status**: Not Started  
**Description**: Full tournament functionality
- QR code generation for tournament access
- Registration system (optional)
- Prize configuration (1st, 2nd, 3rd place)
- Age restrictions (min/max age)
- Tournament rules and description
- Mirror memory game tournament structure

---

### 9. Create Serializers & ViewSets
**Status**: Not Started  
**Description**: REST API implementation
- Quiz session endpoints (casual/tournament)
- General leaderboard endpoint
- Tournament leaderboard endpoint
- Category fetching endpoint
- Question retrieval endpoint
- Tournament management endpoints

---

### 10. Test Quiz System End-to-End
**Status**: Not Started  
**Description**: Full system testing
- Test slot machine category selection
- Test scoring calculations
- Test general leaderboard (best per player)
- Test tournament leaderboard (all plays)
- Test casual play flow
- Test tournament play flow

---

## 🎰 SLOT MACHINE SYSTEM DETAILS

### How It Works:
1. Quiz starts
2. System randomly selects 5 categories from 10 available
3. Selected categories stored in session
4. Questions pulled from these 5 categories only
5. Each quiz session has different category mix

### Example:
- **Available**: History, Science, Sports, Movies, Music, Geography, Food, Art, Literature, Technology
- **Selected for Session 1**: History, Movies, Music, Art, Technology
- **Selected for Session 2**: Science, Sports, Geography, Food, Literature

---

## 📊 LEADERBOARD SYSTEMS

### 1. GENERAL LEADERBOARD
- **Purpose**: Global all-time rankings
- **Rule**: ONE entry per player (best score only)
- **Update**: Only when new score > existing score
- **Identifier**: `player_token`
- **Display**: Rank, Player Name, Best Score, Date

### 2. TOURNAMENT LEADERBOARD
- **Purpose**: Active tournament rankings
- **Rule**: ALL entries during tournament period
- **Update**: Every tournament play
- **Identifier**: `session_id` + `player_token`
- **Display**: Rank, Player Name, Score, Time, Moves
- **Lifecycle**: Active only during tournament dates

---

## 🎮 PLAYER SYSTEM

### Anonymous Players:
```
Format: "PlayerName|session_token"
Example: "Alice|player_abc123"
```

### Storage:
- `player_name` field stores full string
- Token extraction: `player_name.split('|')[1]`
- Display name: `player_name.split('|')[0]`

### Use Cases:
- Casual play: Generate new token each session
- Tournament play: Token persists across tournament attempts
- Leaderboard tracking: Token identifies unique players

---

## 📝 NOTES

- Follow memory game patterns for consistency
- All sessions are anonymous (no user auth)
- Hotel field optional (for multi-hotel support)
- Questions must be pre-populated in admin
- Categories must be active to appear in slot machine
