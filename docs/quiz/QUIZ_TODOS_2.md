# GUESSTICULATOR QUIZ GAME - PHASE 2 TODOS

## 🎯 CURRENT STATUS
Phase 1 (Backend) is **COMPLETE**! All models, serializers, views, and APIs are implemented.

---

## ✅ PHASE 2 TODO LIST

### 1. Run Migrations & Setup Database
**Status**: ⏳ PENDING  
**Priority**: HIGH  
**Description**: Initialize database with quiz models
```bash
python manage.py makemigrations entertainment
python manage.py migrate
```

---

### 2. Create Test Categories (10 Categories)
**Status**: ⏳ PENDING  
**Priority**: HIGH  
**Description**: Add 10 quiz categories via Django admin
- History 📚
- Science 🔬
- Sports ⚽
- Movies 🎬
- Music 🎵
- Geography 🗺️
- Food 🍔
- Art 🎨
- Literature 📖
- Technology 💻

**Admin URL**: `/admin/entertainment/quizcategory/add/`

---

### 3. Add Test Questions to Each Category
**Status**: ⏳ PENDING  
**Priority**: HIGH  
**Description**: Create at least 10 questions per category (100+ total)
- Mix of Easy, Medium, Hard difficulties
- All 4 options (A, B, C, D) filled
- Correct answer marked
- Optional: Add explanations

**Admin URL**: `/admin/entertainment/quizquestion/add/`

---

### 4. Test Slot Machine API
**Status**: ⏳ PENDING  
**Priority**: MEDIUM  
**Description**: Verify random category selection works
```bash
# Test endpoint
GET /api/entertainment/quiz-categories/random_selection/
GET /api/entertainment/quiz-categories/random_selection/?count=5

# Expected: Returns 5 random active categories
```

---

### 5. Test Casual Play Flow (End-to-End)
**Status**: ⏳ PENDING  
**Priority**: HIGH  
**Description**: Complete quiz flow test
```bash
# 1. Start quiz
POST /api/entertainment/quiz-sessions/start_quiz/
Body: {
  "player_name": "TestPlayer|player_abc123",
  "questions_per_quiz": 20
}
# Returns: session, categories, questions

# 2. Submit answers (for each question)
POST /api/entertainment/quiz-sessions/{id}/submit_answer/
Body: {
  "question_id": 1,
  "selected_answer": "A",
  "time_seconds": 8
}

# 3. Complete session
POST /api/entertainment/quiz-sessions/{id}/complete_session/
Body: {"time_seconds": 240}
# Calculates score & updates leaderboard

# 4. Check leaderboard
GET /api/entertainment/quiz-leaderboard/
```

---

### 6. Test General Leaderboard
**Status**: ⏳ PENDING  
**Priority**: MEDIUM  
**Description**: Verify best-score-per-player logic
- Play multiple casual games with same player token
- Check that only best score appears on leaderboard
- Test ranking calculation

**Endpoints**:
```bash
GET /api/entertainment/quiz-leaderboard/
GET /api/entertainment/quiz-leaderboard/my_rank/?player_token=player_abc123
```

---

### 7. Create Test Tournament
**Status**: ⏳ PENDING  
**Priority**: MEDIUM  
**Description**: Set up a tournament via admin
- Name, slug, dates
- Set status to 'active'
- Configure prizes
- Generate QR code

**Admin URL**: `/admin/entertainment/quiztournament/add/`

---

### 8. Test Tournament Play Flow
**Status**: ⏳ PENDING  
**Priority**: MEDIUM  
**Description**: Complete tournament quiz flow
```bash
# 1. List active tournaments
GET /api/entertainment/quiz-tournaments/?status=active

# 2. Start tournament quiz
POST /api/entertainment/quiz-sessions/start_quiz/
Body: {
  "player_name": "TournamentPlayer|player_xyz789",
  "tournament": 1,
  "questions_per_quiz": 20
}

# 3. Submit answers & complete (same as casual)

# 4. Check tournament leaderboard (ALL plays)
GET /api/entertainment/quiz-tournaments/1/leaderboard/

# 5. Check top 3 players (best per player)
GET /api/entertainment/quiz-tournaments/1/top_players/
```

---

### 9. Verify Scoring System
**Status**: ⏳ PENDING  
**Priority**: MEDIUM  
**Description**: Test score calculations
- Easy question (10 pts × 1.0 = 10)
- Medium question (10 pts × 1.5 = 15)
- Hard question (10 pts × 2.0 = 20)
- Time bonus: <10s = 1.2x, <20s = 1.1x
- Verify final score matches expected

---

### 10. Test Error Handling
**Status**: ⏳ PENDING  
**Priority**: LOW  
**Description**: Test edge cases
- Invalid player_name format
- Submitting answer to completed session
- Invalid question ID
- Invalid category selection
- Missing required fields

---

## 🚀 PHASE 3 (OPTIONAL ENHANCEMENTS)

### 11. Add More Question Types
- True/False questions
- Multiple correct answers
- Image-based questions

### 12. Add Analytics Dashboard
- Most popular categories
- Average scores by difficulty
- Player engagement metrics

### 13. Add Question Reporting
- Allow players to flag incorrect questions
- Admin review system

### 14. Add Social Features
- Share scores on social media
- Challenge friends

---

## 📝 TESTING CHECKLIST

### Backend API Tests
- [ ] Category slot machine returns 5 random categories
- [ ] Questions distributed evenly from selected categories
- [ ] Player validation (PlayerName|token format)
- [ ] Score calculation (base × difficulty × time bonus)
- [ ] General leaderboard updates (best score only)
- [ ] Tournament leaderboard shows all plays
- [ ] Session completion updates leaderboard
- [ ] Tournament QR code generation

### Casual Play Flow
- [ ] Start quiz endpoint works
- [ ] Questions returned match selected categories
- [ ] Answer submission validates correctly
- [ ] Session completion calculates score
- [ ] Leaderboard shows player's best score
- [ ] My rank endpoint returns correct rank

### Tournament Play Flow
- [ ] Active tournaments list works
- [ ] Tournament quiz creation works
- [ ] Tournament leaderboard shows all sessions
- [ ] Top players shows best per player (top 3)
- [ ] Tournament status filtering works

---

## 🔧 DEBUGGING TIPS

If you encounter errors:

1. **Migration errors**: Check model field definitions
2. **Validation errors**: Check serializer validation
3. **Scoring issues**: Check `calculate_score()` method
4. **Leaderboard not updating**: Check `complete_session()` method
5. **Questions not appearing**: Ensure `is_active=True` on categories & questions

---

## 📚 NEXT STEPS AFTER TESTING

1. ✅ Fix any bugs found during testing
2. ✅ Add more questions (aim for 20+ per category)
3. ✅ Create production tournament
4. ✅ Frontend integration (see QUIZ_API_DOCS.md)
5. ✅ Deploy to production
6. ✅ Monitor and iterate
