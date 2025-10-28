# 🎮 Save All Scores + Attempt Limit System

## 🎯 New Approach: Save Every Score, Limit Attempts Per Player

### **Key Changes:**
- ✅ **Save all scores** to database (not just high scores)
- ✅ **Limit attempts** per player (default: 3 attempts per tournament)
- ✅ **Track personal bests** for each player
- ✅ **Leaderboard ranks by best score** per player (not all attempts)

---

## 🔄 Updated Tournament Flow

### **1. Complete Flow:**
```
QR Scan → Tournament → Enter Name/Room → Start Game → Complete Game → Submit Score → Show Results
```

### **2. Attempt Tracking:**
```
Player "Alex" attempts:
1st attempt: 720 points ✅ Saved
2nd attempt: 850 points ✅ Saved (New Personal Best!)  
3rd attempt: 800 points ✅ Saved (Final attempt)
4th attempt: ❌ "You have reached the maximum of 3 attempts"
```

### **3. Leaderboard Logic:**
```
Leaderboard shows BEST SCORE per player:
1. Alex - 850 points (best of 3 attempts)
2. Sarah - 830 points (best of 2 attempts) 
3. Mike - 810 points (best of 1 attempt)
```

---

## 📡 Updated API Response

### **1. Successful Score Submission:**
```json
{
  "message": "Score submitted successfully!",
  "session_id": 456,
  "score": 850,
  "player_name": "Alex Smith",
  "rank": 5,
  "attempts_used": 2,
  "max_attempts": 3,
  "remaining_attempts": 1,
  "is_personal_best": true,
  "best_score": 850
}
```

### **2. Attempt Limit Reached:**
```json
{
  "error": "You have reached the maximum of 3 attempts for this tournament",
  "attempts_used": 3,
  "max_attempts": 3,
  "best_score": 850
}
```

---

## 🚀 Frontend Implementation

### **1. Pre-Game Player Info Collection**
```javascript
const PlayerInfoForm = ({ tournament, onStartGame }) => {
  const [playerName, setPlayerName] = useState('');
  const [roomNumber, setRoomNumber] = useState('');
  const [playerStats, setPlayerStats] = useState(null);

  // Check player's existing attempts when name is entered
  const checkPlayerAttempts = async (name) => {
    if (!name.trim()) return;
    
    try {
      const response = await fetch(
        `/api/entertainment/tournaments/${tournament.id}/player_stats/?name=${encodeURIComponent(name.trim())}`
      );
      
      if (response.ok) {
        const stats = await response.json();
        setPlayerStats(stats);
      }
    } catch (error) {
      console.error('Error checking player stats:', error);
    }
  };

  const handleNameChange = (e) => {
    const name = e.target.value;
    setPlayerName(name);
    
    // Debounce the API call
    clearTimeout(window.nameCheckTimeout);
    window.nameCheckTimeout = setTimeout(() => {
      checkPlayerAttempts(name);
    }, 500);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!playerName.trim()) {
      alert('Please enter your name!');
      return;
    }

    if (playerStats?.attempts_used >= playerStats?.max_attempts) {
      alert(`You have already used all ${playerStats.max_attempts} attempts for this tournament.`);
      return;
    }

    const playerData = {
      name: playerName.trim(),
      room: roomNumber.trim() || 'Not specified'
    };

    onStartGame(playerData);
  };

  return (
    <div className="player-info-form">
      <div className="tournament-header">
        <h2>🏆 {tournament.name}</h2>
        <p>Enter your information to start playing!</p>
      </div>

      <form onSubmit={handleSubmit} className="player-form">
        <div className="form-group">
          <label htmlFor="playerName">
            <span className="required">*</span> Your Name:
          </label>
          <input
            type="text"
            id="playerName"
            value={playerName}
            onChange={handleNameChange}
            placeholder="Enter your name..."
            maxLength={100}
            required
            autoFocus
          />
        </div>

        {playerStats && (
          <div className="player-stats">
            <h4>📊 Your Tournament Progress:</h4>
            <div className="stats-grid">
              <div className="stat">
                <span className="stat-label">Attempts Used:</span>
                <span className="stat-value">{playerStats.attempts_used} / {playerStats.max_attempts}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Best Score:</span>
                <span className="stat-value">{playerStats.best_score} points</span>
              </div>
              {playerStats.current_rank && (
                <div className="stat">
                  <span className="stat-label">Current Rank:</span>
                  <span className="stat-value">#{playerStats.current_rank}</span>
                </div>
              )}
            </div>
            
            {playerStats.attempts_used >= playerStats.max_attempts ? (
              <div className="attempts-exhausted">
                <p>❌ You have used all your attempts for this tournament.</p>
                <p>Your best score: <strong>{playerStats.best_score} points</strong></p>
              </div>
            ) : (
              <div className="attempts-remaining">
                <p>✅ You have {playerStats.max_attempts - playerStats.attempts_used} attempts remaining.</p>
                <p>Try to beat your best score of {playerStats.best_score} points!</p>
              </div>
            )}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="roomNumber">
            Room Number (Optional):
          </label>
          <input
            type="text"
            id="roomNumber"
            value={roomNumber}
            onChange={(e) => setRoomNumber(e.target.value)}
            placeholder="e.g., 205"
            maxLength={50}
          />
        </div>

        <button 
          type="submit" 
          className="start-game-btn"
          disabled={playerStats?.attempts_used >= playerStats?.max_attempts}
        >
          {playerStats?.attempts_used >= playerStats?.max_attempts 
            ? '❌ No Attempts Remaining' 
            : '🚀 Start Tournament Game!'
          }
        </button>
      </form>

      <div className="tournament-rules">
        <h4>🎮 Tournament Rules:</h4>
        <ul>
          <li>🎯 Maximum 3 attempts per player</li>
          <li>🏆 Leaderboard shows your best score</li>
          <li>⚡ Faster time + fewer moves = higher score</li>
          <li>🔄 You can improve with each attempt</li>
        </ul>
      </div>
    </div>
  );
};
```

### **2. Post-Game Results Display**
```javascript
const TournamentResults = ({ results, onPlayAgain }) => {
  const canPlayAgain = results.remaining_attempts > 0;
  
  return (
    <div className="tournament-results">
      <div className="results-header">
        <h2>🎮 Game Complete!</h2>
        <div className="player-info">
          <h3>👤 {results.player_name}</h3>
        </div>
      </div>

      <div className="score-display">
        <div className="current-score">
          <span className="score-label">This Game</span>
          <span className="score-value">{results.score}</span>
          {results.is_personal_best && (
            <span className="personal-best">🌟 Personal Best!</span>
          )}
        </div>

        <div className="best-score">
          <span className="score-label">Your Best</span>
          <span className="score-value">{results.best_score}</span>
        </div>
      </div>

      <div className="ranking-info">
        <div className="rank-display">
          <span className="rank-label">Current Rank</span>
          <span className="rank-value">#{results.rank}</span>
        </div>
      </div>

      <div className="attempts-info">
        <h4>📊 Attempt Progress:</h4>
        <div className="attempts-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${(results.attempts_used / results.max_attempts) * 100}%` }}
            ></div>
          </div>
          <span className="progress-text">
            {results.attempts_used} / {results.max_attempts} attempts used
          </span>
        </div>

        {canPlayAgain ? (
          <div className="can-play-again">
            <p>✅ You have {results.remaining_attempts} attempts remaining!</p>
            <p>💡 Try to beat your best score of {results.best_score} points</p>
          </div>
        ) : (
          <div className="no-attempts-left">
            <p>🏁 You have used all your attempts for this tournament.</p>
            <p>🏆 Your final best score: {results.best_score} points</p>
          </div>
        )}
      </div>

      <div className="action-buttons">
        {canPlayAgain ? (
          <button 
            onClick={onPlayAgain}
            className="play-again-btn primary"
          >
            🔄 Play Again ({results.remaining_attempts} left)
          </button>
        ) : (
          <div className="final-actions">
            <button 
              onClick={() => window.location.href = '/tournaments'}
              className="other-tournaments-btn"
            >
              🏆 View Other Tournaments
            </button>
            <button 
              onClick={() => window.location.href = `/tournaments/${results.tournament_id}/leaderboard`}
              className="leaderboard-btn"
            >
              📊 View Final Leaderboard
            </button>
          </div>
        )}
      </div>

      {results.is_personal_best && (
        <div className="achievement-celebration">
          <div className="celebration-animation">🎉</div>
          <p>Congratulations on your new personal best!</p>
        </div>
      )}
    </div>
  );
};
```

### **3. Player Stats API Endpoint (To Add)**
```python
# Add to MemoryGameTournamentViewSet
@action(detail=True, methods=['get'])
def player_stats(self, request, pk=None):
    """Get player's stats for this tournament"""
    tournament = self.get_object()
    player_name = request.query_params.get('name')
    
    if not player_name:
        return Response({'error': 'Player name is required'}, status=400)
    
    sessions = MemoryGameSession.objects.filter(
        tournament=tournament,
        player_name=player_name,
        completed=True
    )
    
    attempts_used = sessions.count()
    max_attempts = 3  # Configurable
    best_score = sessions.aggregate(Max('score'))['score__max'] or 0
    
    # Calculate current rank based on best score
    if best_score > 0:
        better_players = (MemoryGameSession.objects
            .filter(tournament=tournament, completed=True)
            .values('player_name')
            .annotate(best_score=Max('score'))
            .filter(best_score__gt=best_score)
            .count())
        current_rank = better_players + 1
    else:
        current_rank = None
    
    return Response({
        'player_name': player_name,
        'attempts_used': attempts_used,
        'max_attempts': max_attempts,
        'remaining_attempts': max_attempts - attempts_used,
        'best_score': best_score,
        'current_rank': current_rank,
        'can_play': attempts_used < max_attempts
    })
```

---

## 📊 Benefits of This System

### **1. Complete Data Collection:**
- ✅ All scores saved for analytics
- ✅ Track player improvement over attempts
- ✅ Better tournament insights

### **2. Fair Competition:**
- ✅ Everyone gets same number of attempts
- ✅ Prevents spam/cheating
- ✅ Encourages strategic play

### **3. Engagement:**
- ✅ Players know their progress
- ✅ Clear goals for improvement
- ✅ Personal best tracking motivates

### **4. Database Benefits:**
- ✅ All game data preserved
- ✅ Manageable size (max 3 × players per tournament)
- ✅ Rich analytics possible

---

## ✅ Implementation Summary

### **Backend Changes Made:**
- [x] Save all scores to database
- [x] Check attempt limits per player
- [x] Track personal bests
- [x] Rank by best score per player
- [x] Return attempt status in API

### **Frontend Changes Needed:**
- [ ] Pre-game name collection with attempt checking
- [ ] Show player's existing stats when name entered
- [ ] Display attempt progress in results
- [ ] Personal best celebration
- [ ] Handle attempt limit exceeded

**This system gives you complete tournament data while maintaining fairness and engagement!** 🏆