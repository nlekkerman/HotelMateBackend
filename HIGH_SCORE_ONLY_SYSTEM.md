# 🏆 High Score Only Tournament System

## 🎯 New Approach: Only Save High Scores

### **Key Concept:**
- Players complete the game anonymously
- Calculate score on backend  
- **Only save to database if it's a high score** (Top 50)
- **If not high score: show encouragement, don't save**
- **If high score: collect name/room and save**

---

## 🔄 Updated Flow

### **1. Complete Tournament Flow:**
```
QR Scan → Tournament → Start Game → Complete Game → Backend Check Score → 
    ↓                                                                    ↓
High Score? → Collect Name/Room → Save & Show Ranking       Not High Score? → Show Encouragement, Try Again
```

### **2. Backend Logic:**
```python
# POST /tournaments/{id}/submit_score/
{
    "time_seconds": 45,
    "moves_count": 18
    # NO name/room needed initially
}

# Backend calculates score and checks if it's top 50
if is_high_score:
    return {
        "is_high_score": true,
        "score": 850,
        "message": "Congratulations! You made the leaderboard!"
        # Frontend then collects name/room for second API call
    }
else:
    return {
        "is_high_score": false, 
        "score": 720,
        "leaderboard_threshold": 800,
        "message": "Good job! You need 800+ points for the leaderboard. Try again!"
    }
```

---

## 🚀 Frontend Implementation

### **1. Game Completion Handler**
```javascript
const TournamentGame = ({ tournament }) => {
  const [gameState, setGameState] = useState('ready');
  const [gameResults, setGameResults] = useState(null);
  const [scoreCheckResult, setScoreCheckResult] = useState(null);

  const handleGameComplete = async (results) => {
    setGameResults(results);
    
    // Step 1: Check if score qualifies for leaderboard
    await checkScoreQuality(results);
  };

  const checkScoreQuality = async (results) => {
    try {
      const response = await fetch(
        `/api/entertainment/tournaments/${tournament.id}/submit_score/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            time_seconds: results.timeInSeconds,
            moves_count: results.totalMoves
            // No name/room at this stage
          })
        }
      );

      const result = await response.json();
      setScoreCheckResult(result);
      
      if (result.is_high_score) {
        // High score! Show name collection form
        setGameState('collect_info');
      } else {
        // Not high score, show encouragement
        setGameState('try_again');
      }
    } catch (error) {
      console.error('Score check failed:', error);
      // Fallback: show local score
      setScoreCheckResult({
        is_high_score: false,
        score: calculateLocalScore(results),
        message: 'Good job! Try playing again to improve your score.'
      });
      setGameState('try_again');
    }
  };

  // ... rest of component
};
```

### **2. High Score Name Collection**
```javascript
const HighScoreNameCollection = ({ 
  tournament, 
  gameResults, 
  scoreResult, 
  onSubmitHighScore 
}) => {
  const [playerName, setPlayerName] = useState('');
  const [roomNumber, setRoomNumber] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!playerName.trim()) {
      alert('Please enter your name for the leaderboard!');
      return;
    }

    setIsSubmitting(true);

    // Step 2: Save high score with player info
    const finalSubmission = {
      player_name: playerName.trim(),
      room_number: roomNumber.trim() || 'Not specified',
      time_seconds: gameResults.timeInSeconds,
      moves_count: gameResults.totalMoves
    };

    await onSubmitHighScore(finalSubmission);
  };

  return (
    <div className="high-score-collection">
      <div className="celebration-header">
        <h2>🎉 CONGRATULATIONS!</h2>
        <div className="score-highlight">
          <span className="score-value">{scoreResult.score}</span>
          <span className="score-label">points</span>
        </div>
        <p className="achievement-text">
          You made the tournament leaderboard! 🏆
        </p>
      </div>

      <div className="tournament-context">
        <h3>{tournament.name}</h3>
        <p>Enter your information to claim your spot on the leaderboard!</p>
      </div>

      <form onSubmit={handleSubmit} className="name-collection-form">
        <div className="form-group">
          <label htmlFor="playerName">
            <span className="required">*</span> Your Name:
          </label>
          <input
            type="text"
            id="playerName"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            placeholder="Enter your name for the leaderboard..."
            maxLength={100}
            required
            autoFocus
          />
          <button 
            type="button" 
            className="random-name-btn"
            onClick={() => setPlayerName(generateRandomName())}
          >
            🎲 Random Name
          </button>
        </div>

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

        <div className="leaderboard-preview">
          <h4>🏆 You're joining the leaderboard!</h4>
          <p>Your score of <strong>{scoreResult.score} points</strong> earned you a spot among the top players.</p>
        </div>

        <button 
          type="submit" 
          className="claim-spot-btn"
          disabled={isSubmitting}
        >
          {isSubmitting ? '⏳ Claiming Spot...' : '🚀 Claim My Leaderboard Spot!'}
        </button>
      </form>
    </div>
  );
};

const generateRandomName = () => {
  const adjectives = ['Lightning', 'Super', 'Amazing', 'Speedy', 'Brilliant'];
  const nouns = ['Champion', 'Star', 'Hero', 'Ace', 'Master'];
  const randomAdj = adjectives[Math.floor(Math.random() * adjectives.length)];
  const randomNoun = nouns[Math.floor(Math.random() * nouns.length)];
  const randomNum = Math.floor(Math.random() * 999) + 1;
  return `${randomAdj} ${randomNoun} ${randomNum}`;
};
```

### **3. Try Again Screen (Not High Score)**
```javascript
const TryAgainScreen = ({ 
  tournament, 
  gameResults, 
  scoreResult, 
  onPlayAgain 
}) => {
  return (
    <div className="try-again-screen">
      <div className="score-display">
        <h2>🎮 Good Job!</h2>
        <div className="your-score">
          <span className="score-value">{scoreResult.score}</span>
          <span className="score-label">points</span>
        </div>
      </div>

      <div className="game-stats">
        <div className="stat">
          <span className="stat-icon">⏱️</span>
          <span className="stat-value">{gameResults.timeInSeconds}s</span>
          <span className="stat-label">Time</span>
        </div>
        <div className="stat">
          <span className="stat-icon">🔄</span>
          <span className="stat-value">{gameResults.totalMoves}</span>
          <span className="stat-label">Moves</span>
        </div>
      </div>

      <div className="leaderboard-info">
        <h3>🏆 Leaderboard Challenge</h3>
        <p>You need <strong>{scoreResult.leaderboard_threshold}+ points</strong> to make the leaderboard!</p>
        
        <div className="improvement-tips">
          <h4>💡 Tips to improve:</h4>
          <ul>
            <li>⚡ Play faster (less time = higher score)</li>
            <li>🎯 Use fewer moves (12 moves = perfect game)</li>
            <li>🧠 Remember card positions</li>
          </ul>
        </div>
      </div>

      <div className="action-buttons">
        <button 
          onClick={onPlayAgain}
          className="play-again-btn primary"
        >
          🔄 Try Again for High Score!
        </button>
        
        <button 
          onClick={() => window.location.href = `/tournaments/${tournament.id}/leaderboard`}
          className="view-leaderboard-btn"
        >
          👀 View Current Leaderboard
        </button>
      </div>

      <div className="encouragement">
        <p>🌟 Keep playing! Every game makes you better!</p>
      </div>
    </div>
  );
};
```

---

## 🎯 Backend API Updates

### **1. Modified Submit Score Response:**
```python
# High Score Response
{
    "is_high_score": true,
    "saved": true,
    "message": "Congratulations! New high score!",
    "session_id": 123,
    "score": 850,
    "player_name": "Speed Master",
    "rank": 5
}

# Not High Score Response  
{
    "is_high_score": false,
    "saved": false,
    "message": "Good job! Try again to get a higher score.",
    "score": 720,
    "leaderboard_threshold": 800
}
```

### **2. Two-Step Submission Process:**
```javascript
// Step 1: Check score quality (anonymous)
POST /tournaments/23/submit_score/
{
    "time_seconds": 45,
    "moves_count": 18
}

// Step 2: Save high score with name (only if step 1 returned is_high_score: true)
POST /tournaments/23/submit_score/  
{
    "player_name": "Speed Master",
    "room_number": "305", 
    "time_seconds": 45,
    "moves_count": 18
}
```

---

## 📊 Benefits of This Approach

### **1. Database Efficiency:**
- ✅ Only stores meaningful scores (top 50 per tournament)
- ✅ No clutter from low scores
- ✅ Faster leaderboard queries
- ✅ Reduced storage requirements

### **2. Better User Experience:**
- ✅ No barriers to entry - play immediately
- ✅ Collect info only from high scorers (more motivated to provide it)
- ✅ Clear feedback on performance
- ✅ Encouragement to try again

### **3. Gamification:**
- ✅ Making the leaderboard feels like an achievement
- ✅ Clear goals ("You need 800+ points")
- ✅ Motivation to improve and try again

---

## ✅ Implementation Steps

### **Backend (Ready):**
- [x] Modified `submit_score` endpoint
- [x] Added score calculation method
- [x] Added high score checking logic
- [x] Added leaderboard threshold calculation

### **Frontend (To Do):**
- [ ] Two-step score submission flow
- [ ] High score celebration screen
- [ ] Name collection form (only for high scores)
- [ ] Try again screen with improvement tips
- [ ] Score threshold display
- [ ] Leaderboard preview

**This approach creates a much more engaging tournament experience while keeping the database clean!** 🚀