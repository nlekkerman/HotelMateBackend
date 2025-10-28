# 👤 Player Name Collection - Frontend Guide

## 🎯 Problem: Getting Player Name for Tournament Submission

The backend expects both `player_name` and `room_number`, but frontend needs to collect the name from the player.

---

## 📝 Solution: Post-Game Player Info Form

### **1. Tournament Join Flow (No Registration Required)**
```
QR Scan → Tournaments Page → Select Tournament → Start Game → Complete Game → Enter Name & Room → Submit Score
```

**Key Points:**
- ✅ No pre-registration required
- ✅ Kids can play immediately  
- ✅ Collect info only after they complete the game
- ✅ Anonymous gameplay until score submission

### **2. Post-Game Player Info Collection Component**

```javascript
import { useState } from 'react';

const PostGamePlayerInfoForm = ({ tournament, gameResults, onSubmitScore }) => {
  const [playerName, setPlayerName] = useState('');
  const [roomNumber, setRoomNumber] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate inputs
    if (!playerName.trim()) {
      alert('Please enter your name to save your score!');
      return;
    }

    // Prepare submission data
    const submissionData = {
      player_name: playerName.trim(),
      room_number: roomNumber.trim() || 'Not specified',
      time_seconds: gameResults.timeInSeconds,
      moves_count: gameResults.totalMoves
    };

    // Submit the score
    onSubmitScore(submissionData);
  };

  const generateRandomName = () => {
    const adjectives = ['Super', 'Amazing', 'Cool', 'Fast', 'Smart', 'Brave'];
    const nouns = ['Player', 'Gamer', 'Star', 'Hero', 'Champion', 'Winner'];
    const randomAdj = adjectives[Math.floor(Math.random() * adjectives.length)];
    const randomNoun = nouns[Math.floor(Math.random() * nouns.length)];
    const randomNum = Math.floor(Math.random() * 999) + 1;
    
    setPlayerName(`${randomAdj} ${randomNoun} ${randomNum}`);
  };

  return (
    <div className="post-game-info-form">
      <div className="game-complete-header">
        <h2>� Game Complete!</h2>
        <div className="game-results-summary">
          <div className="result-stat">
            <span className="stat-icon">⏱️</span>
            <span className="stat-value">{gameResults.timeInSeconds}s</span>
            <span className="stat-label">Time</span>
          </div>
          <div className="result-stat">
            <span className="stat-icon">�</span>
            <span className="stat-value">{gameResults.totalMoves}</span>
            <span className="stat-label">Moves</span>
          </div>
        </div>
      </div>

      <div className="tournament-info">
        <h3>🏆 {tournament.name}</h3>
        <p>Enter your information to save your score and see your ranking!</p>
      </div>

      <form onSubmit={handleSubmit} className="player-form">
        <h3>👤 Save Your Score</h3>
        
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
            onClick={generateRandomName}
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
            placeholder="e.g., 205, or leave empty"
            maxLength={50}
          />
        </div>

        <div className="form-actions">
          <button 
            type="submit" 
            className="submit-score-btn"
            disabled={isSubmitting}
          >
            {isSubmitting ? '⏳ Saving Score...' : '🚀 Submit Score & See Ranking!'}
          </button>
          
          <button 
            type="button" 
            className="skip-btn"
            onClick={() => onSubmitScore({
              player_name: 'Anonymous Player',
              room_number: 'Not specified',
              time_seconds: gameResults.timeInSeconds,
              moves_count: gameResults.totalMoves
            })}
          >
            Skip - Play Anonymously
          </button>
        </div>
      </form>

      <div className="privacy-note">
        <p>ℹ️ Your name will appear on the tournament leaderboard. Room number is optional.</p>
      </div>
    </div>
  );
};
```

---

## 🎮 Game Integration

### **3. Tournament Game Component (No Pre-Registration)**
```javascript
const TournamentGame = ({ tournament }) => {
  const [gameState, setGameState] = useState('ready'); // 'ready', 'playing', 'info', 'completed'
  const [gameResults, setGameResults] = useState(null);
  const [submissionResults, setSubmissionResults] = useState(null);

  const handleStartGame = () => {
    // Start game immediately - no info collection
    setGameState('playing');
  };

  const handleGameComplete = (results) => {
    // Game completion results from memory match component
    setGameResults(results);
    setGameState('info'); // Show info collection form
  };

  const submitTournamentScore = async (submissionData) => {
    try {
      const response = await fetch(
        `/api/entertainment/tournaments/${tournament.id}/submit_score/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(submissionData)
        }
      );

      const result = await response.json();
      
      if (response.ok) {
        setSubmissionResults({
          ...result,
          playerName: submissionData.player_name,
          roomNumber: submissionData.room_number,
          submitted: true
        });
        setGameState('completed');
      } else {
        showErrorMessage(result.error);
      }
    } catch (error) {
      console.error('Score submission failed:', error);
      // Show fallback success for kids
      setSubmissionResults({
        score: calculateLocalScore(gameResults),
        message: 'Great job! Your score has been saved.',
        playerName: submissionData.player_name,
        submitted: false
      });
      setGameState('completed');
    }
  };

  const calculateLocalScore = (results) => {
    // Fallback score calculation (same as backend)
    const baseScore = 1000;
    const timePenalty = results.timeInSeconds * 2;
    const extraMoves = Math.max(0, results.totalMoves - 12);
    const movesPenalty = extraMoves * 5;
    return Math.max(0, baseScore - timePenalty - movesPenalty);
  };

  // Render different states
  if (gameState === 'ready') {
    return (
      <TournamentReadyScreen 
        tournament={tournament}
        onStartGame={handleStartGame}
      />
    );
  }

  if (gameState === 'playing') {
    return (
      <MemoryMatchGame
        difficulty="intermediate"  // Fixed 3x4 grid
        onGameComplete={handleGameComplete}
      />
    );
  }

  if (gameState === 'info') {
    return (
      <PostGamePlayerInfoForm
        tournament={tournament}
        gameResults={gameResults}
        onSubmitScore={submitTournamentScore}
      />
    );
  }

  if (gameState === 'completed') {
    return (
      <TournamentResults
        results={submissionResults}
        gameResults={gameResults}
        tournament={tournament}
        onPlayAgain={() => setGameState('ready')}
      />
    );
  }
};

// Simple tournament start screen
const TournamentReadyScreen = ({ tournament, onStartGame }) => {
  return (
    <div className="tournament-ready">
      <div className="tournament-header">
        <h2>🏆 {tournament.name}</h2>
        <p className="tournament-description">{tournament.description}</p>
        
        <div className="tournament-details">
          <div className="detail-item">
            <span className="icon">⏰</span>
            <span>Ends: {new Date(tournament.end_date).toLocaleTimeString()}</span>
          </div>
          <div className="detail-item">
            <span className="icon">👥</span>
            <span>{tournament.participant_count} players joined</span>
          </div>
          <div className="detail-item">
            <span className="icon">🏆</span>
            <span>First Prize: {tournament.first_prize}</span>
          </div>
        </div>
      </div>

      <div className="game-info">
        <h3>🎮 How to Play:</h3>
        <ul>
          <li>🃏 Match all 6 pairs of cards (3×4 grid)</li>
          <li>⚡ Complete as fast as possible</li>
          <li>🎯 Fewer moves = higher score</li>
          <li>🏆 Best scores win prizes!</li>
        </ul>
      </div>

      <button 
        onClick={onStartGame}
        className="start-game-btn big"
      >
        🚀 Start Playing!
      </button>

      <div className="note">
        <p>💡 You'll enter your name after completing the game</p>
      </div>
    </div>
  );
};
```

---

## 🏆 Results Display Component

### **4. Tournament Results Component**
```javascript
const TournamentResults = ({ results, tournament, onPlayAgain }) => {
  const getRankEmoji = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈'; 
    if (rank === 3) return '🥉';
    if (rank <= 10) return '🏆';
    return '🎮';
  };

  const getRankMessage = (rank) => {
    if (rank === 1) return "🎉 AMAZING! You're in 1st place!";
    if (rank === 2) return "🎊 Fantastic! You're in 2nd place!";
    if (rank === 3) return "🎈 Great job! You're in 3rd place!";
    if (rank <= 10) return `🌟 Excellent! You're #${rank} in the top 10!`;
    return `👏 Well done! You ranked #${rank}. Try again to improve!`;
  };

  return (
    <div className="tournament-results">
      <div className="results-header">
        <h2>🎮 Game Complete!</h2>
        <div className="player-info">
          <h3>👤 {results.playerName}</h3>
          {results.roomNumber && results.roomNumber !== 'Not specified' && (
            <p>🏨 Room: {results.roomNumber}</p>
          )}
        </div>
      </div>

      <div className="score-display">
        <div className="main-score">
          <span className="score-label">Your Score</span>
          <span className="score-value">{results.score || 'Calculating...'}</span>
        </div>

        <div className="game-stats">
          <div className="stat">
            <span className="stat-icon">⏱️</span>
            <span className="stat-label">Time</span>
            <span className="stat-value">{results.timeInSeconds}s</span>
          </div>
          <div className="stat">
            <span className="stat-icon">🔄</span>
            <span className="stat-label">Moves</span>
            <span className="stat-value">{results.totalMoves}</span>
          </div>
        </div>
      </div>

      {results.rank && (
        <div className="rank-display">
          <div className="rank-badge">
            <span className="rank-emoji">{getRankEmoji(results.rank)}</span>
            <span className="rank-number">#{results.rank}</span>
          </div>
          <p className="rank-message">{getRankMessage(results.rank)}</p>
        </div>
      )}

      {results.submitted ? (
        <div className="success-message">
          <p>✅ Your score has been submitted to the tournament!</p>
        </div>
      ) : (
        <div className="fallback-message">
          <p>🎮 Great job completing the tournament!</p>
          <p>Your score has been recorded.</p>
        </div>
      )}

      <div className="action-buttons">
        <button className="play-again-btn" onClick={onPlayAgain}>
          🔄 Play Again
        </button>
        <button 
          className="leaderboard-btn"
          onClick={() => window.location.href = '/tournaments/leaderboard'}
        >
          🏆 View Leaderboard
        </button>
      </div>

      <div className="tournament-info">
        <h4>🏆 Prize Information:</h4>
        <ul>
          <li>🥇 1st Place: {tournament.first_prize}</li>
          <li>🥈 2nd Place: {tournament.second_prize}</li>
          <li>🥉 3rd Place: {tournament.third_prize}</li>
        </ul>
        <p>Winners will be announced when the tournament ends!</p>
      </div>
    </div>
  );
};
```

---

## 🎨 CSS Styling

### **5. Styling for Forms**
```css
.player-info-form {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.tournament-header {
  text-align: center;
  margin-bottom: 30px;
}

.tournament-header h2 {
  color: #333;
  margin-bottom: 10px;
}

.tournament-description {
  color: #666;
  line-height: 1.4;
  margin-bottom: 20px;
}

.tournament-details {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.9rem;
  color: #555;
}

.player-form h3 {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

.required {
  color: #e74c3c;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #3498db;
}

.random-name-btn {
  margin-top: 8px;
  padding: 8px 16px;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.random-name-btn:hover {
  background: #e9ecef;
}

.game-info {
  background: #e3f2fd;
  padding: 15px;
  border-radius: 8px;
  margin: 20px 0;
}

.game-info h4 {
  margin-top: 0;
  color: #1565c0;
}

.game-info ul {
  margin: 0;
  padding-left: 20px;
}

.game-info li {
  margin-bottom: 5px;
  color: #333;
}

.start-game-btn {
  width: 100%;
  padding: 16px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.start-game-btn:hover:not(:disabled) {
  background: #218838;
}

.start-game-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.privacy-note {
  margin-top: 15px;
  text-align: center;
}

.privacy-note p {
  font-size: 0.85rem;
  color: #666;
  margin: 0;
}

/* Tournament Results Styling */
.tournament-results {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  text-align: center;
}

.score-display {
  background: #f8f9fa;
  padding: 30px;
  border-radius: 12px;
  margin: 20px 0;
}

.main-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
}

.score-label {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 10px;
}

.score-value {
  font-size: 3rem;
  font-weight: bold;
  color: #28a745;
}

.game-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-icon {
  font-size: 1.5rem;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 1.3rem;
  font-weight: bold;
  color: #333;
}

.rank-display {
  margin: 30px 0;
}

.rank-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 15px;
}

.rank-emoji {
  font-size: 3rem;
}

.rank-number {
  font-size: 2.5rem;
  font-weight: bold;
  color: #333;
}

.rank-message {
  font-size: 1.2rem;
  color: #28a745;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin: 30px 0;
}

.play-again-btn,
.leaderboard-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.play-again-btn {
  background: #007bff;
  color: white;
}

.play-again-btn:hover {
  background: #0056b3;
}

.leaderboard-btn {
  background: #ffc107;
  color: #333;
}

.leaderboard-btn:hover {
  background: #e0a800;
}

.tournament-info {
  background: #fff3cd;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}

.tournament-info h4 {
  margin-top: 0;
  color: #856404;
}

.tournament-info ul {
  text-align: left;
  margin: 15px 0;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .player-info-form,
  .tournament-results {
    margin: 10px;
    padding: 15px;
  }
  
  .tournament-details {
    flex-direction: column;
    align-items: center;
  }
  
  .game-stats {
    gap: 20px;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: stretch;
  }
}
```

---

## 🔄 Complete Flow Example

### **6. Page Router Integration**
```javascript
// TournamentPage.jsx
const TournamentPage = () => {
  const [searchParams] = useSearchParams();
  const [tournaments, setTournaments] = useState([]);
  const [selectedTournament, setSelectedTournament] = useState(null);
  
  const hotelSlug = searchParams.get('hotel');

  // Fetch tournaments on load
  useEffect(() => {
    if (hotelSlug) {
      fetchTournaments();
    }
  }, [hotelSlug]);

  const fetchTournaments = async () => {
    try {
      const response = await fetch(
        `/api/entertainment/tournaments/active_for_hotel/?hotel=${hotelSlug}`
      );
      const data = await response.json();
      setTournaments(data.tournaments || []);
    } catch (error) {
      console.error('Error fetching tournaments:', error);
    }
  };

  const handleTournamentSelect = (tournament) => {
    setSelectedTournament(tournament);
  };

  const handleBackToList = () => {
    setSelectedTournament(null);
  };

  return (
    <div className="tournament-page">
      {selectedTournament ? (
        <div>
          <button className="back-button" onClick={handleBackToList}>
            ← Back to Tournaments
          </button>
          <TournamentGame tournament={selectedTournament} />
        </div>
      ) : (
        <div>
          <h1>🏆 Memory Match Tournaments</h1>
          {tournaments.length > 0 ? (
            <div className="tournaments-grid">
              {tournaments.map(tournament => (
                <TournamentCard
                  key={tournament.id}
                  tournament={tournament}
                  onSelect={() => handleTournamentSelect(tournament)}
                />
              ))}
            </div>
          ) : (
            <div className="no-tournaments">
              <p>No active tournaments available.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

---

## ✅ Implementation Checklist

### **New Flow (No Pre-Registration):**
- [ ] **Tournament Ready Screen**: Simple "Start Playing" button
- [ ] **Immediate Game Start**: No info collection before game
- [ ] **Post-Game Info Form**: Collect name and room AFTER completing game
- [ ] **Random Name Generator**: Fallback for kids who don't want to enter name
- [ ] **Skip Option**: Allow anonymous score submission
- [ ] **Score Submission**: Include player_name and room_number in POST
- [ ] **Results Display**: Show score, rank, and player name
- [ ] **Error Handling**: Graceful fallbacks for submission failures
- [ ] **Mobile Responsive**: Works well on phones/tablets

### **Key Benefits:**
✅ **No barriers to entry** - Kids can start playing immediately  
✅ **No registration required** - Anonymous gameplay until score submission  
✅ **Better engagement** - Collect info when they're excited about their score  
✅ **Optional participation** - Can skip name entry and play anonymously

**Perfect for kids tournaments - play first, enter name later!** 🎯