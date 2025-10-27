# 🎮 Memory Match Game - Complete Frontend Integration Guide

## 🎯 **Complete Frontend Integration - Dashboard Architecture**

### **✅ Backend Status:**
- ✅ Fresh tournaments created (Oct 27 - Nov 2, 2025)
- ✅ All QR codes point to dashboard: `/games/memory-match/?hotel=hotel-killarney`
- ✅ Card API updated for 6 pairs (3x4 grid)
- ✅ Active tournaments API ready
- ✅ No registration required - anonymous play supported

### **URL Flow:**
- **QR Code → Dashboard**: `/games/memory-match/?hotel=hotel-killarney`
- **Dashboard → Practice**: `/games/memory-match/practice`
- **Dashboard → Tournament**: `/games/memory-match/tournament/{id}`
- **Post-game**: Submit score or save to localStorage

---

## 🔗 **API Endpoints Ready for Frontend**

### **1. Get 6 Card Pairs for 3x4 Grid:**
```javascript
GET /api/entertainment/memory-cards/for-game/
```

**Response:**
```json
{
  "grid_size": "3x4",
  "pairs_needed": 6,
  "cards_count": 6,
  "total_cards": 12,
  "cards": [
    {
      "id": 23,
      "name": "Halloween Cat",
      "slug": "halloween-cat",
      "image_url": "https://res.cloudinary.com/.../halloween-cat.png",
      "description": "Black Halloween cat"
    },
    // ... 5 more cards
  ],
  "game_config": {
    "grid_type": "3x4 grid (6 pairs)",
    "optimal_moves": 12,
    "scoring": {
      "base_score": 1000,
      "time_penalty": 2,
      "move_penalty": 5
    }
  }
}
```

### **2. Get Active Tournaments for Hotel:**
```javascript
GET /api/entertainment/tournaments/active_for_hotel/?hotel=hotel-killarney
```

**Response:**
```json
{
  "tournaments": [
    {
      "id": 16,
      "name": "Memory Match Daily - Monday",
      "description": "Daily Memory Match for October 27, 2025. 3x4 grid (6 pairs) - Scan QR to play!",
      "grid_size": "3x4 (6 pairs)",
      "participant_count": 0,
      "start_date": "2025-10-27T12:00:00Z",
      "end_date": "2025-10-27T19:00:00Z",
      "status": "active",
      "first_prize": "Hotel Game Room Pass",
      "second_prize": "Pool Day Pass",
      "third_prize": "Ice Cream Voucher"
    }
  ],
  "count": 1
}
```

### **3. Submit Tournament Score (Anonymous):**
```javascript
POST /api/entertainment/tournaments/{id}/submit_score/
Content-Type: application/json

{
  "player_name": "Alex",
  "room_number": "304",
  "time_seconds": 45,
  "moves_count": 14
}
```

**Response:**
```json
{
  "message": "Score submitted successfully",
  "score": 901,
  "rank": 2,
  "session_id": 42,
  "tournament": "Memory Match Daily - Monday"
}
```

---

## 🏗️ **Frontend Components**

### **1. Game Dashboard Component** 
**Route**: `/games/memory-match`

```jsx
import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

const MemoryMatchDashboard = () => {
  const [searchParams] = useSearchParams();
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);
  const hotelSlug = searchParams.get('hotel');

  useEffect(() => {
    if (hotelSlug) {
      fetchActiveTournaments();
    }
  }, [hotelSlug]);

  const fetchActiveTournaments = async () => {
    try {
      const response = await fetch(
        `/api/entertainment/tournaments/active_for_hotel/?hotel=${hotelSlug}`
      );
      const data = await response.json();
      setTournaments(data.tournaments || []);
    } catch (error) {
      console.error('Error fetching tournaments:', error);
      setTournaments([]);
    } finally {
      setLoading(false);
    }
  };

  const startPractice = () => {
    window.location.href = '/games/memory-match/practice';
  };

  const startTournament = (tournament) => {
    window.location.href = `/games/memory-match/tournament/${tournament.id}`;
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <h2>🎮 Memory Match</h2>
        <p>Loading tournaments...</p>
      </div>
    );
  }

  return (
    <div className="memory-match-dashboard">
      <header className="dashboard-header">
        <h1>🎮 Memory Match</h1>
        <p>3×4 Grid • Match 6 Pairs • Test Your Memory!</p>
        {hotelSlug && <p className="hotel-info">🏨 Playing at: {hotelSlug}</p>}
      </header>

      <div className="game-modes">
        {/* Practice Mode Card */}
        <div className="game-mode-card practice-mode">
          <div className="mode-icon">🏃‍♀️</div>
          <h2>Practice Mode</h2>
          <p>Play without limits • Scores saved locally</p>
          <ul className="feature-list">
            <li>✅ No registration needed</li>
            <li>✅ Unlimited attempts</li>
            <li>✅ Track your best scores</li>
            <li>✅ Perfect for learning</li>
          </ul>
          <button 
            className="btn btn-practice"
            onClick={startPractice}
          >
            Start Practice Game
          </button>
        </div>

        {/* Tournament Mode Card */}
        <div className="game-mode-card tournament-mode">
          <div className="mode-icon">🏆</div>
          <h2>Tournament Mode</h2>
          <p>Compete with other guests • Win prizes!</p>
          
          {tournaments.length > 0 ? (
            <div className="tournaments-list">
              <p className="tournaments-header">🎯 Active Tournaments:</p>
              {tournaments.map(tournament => (
                <div key={tournament.id} className="tournament-option">
                  <div className="tournament-info">
                    <h3>{tournament.name}</h3>
                    <p>{tournament.description}</p>
                    <div className="tournament-details">
                      <span>👥 {tournament.participant_count} players</span>
                      <span>🎁 Prizes: {tournament.first_prize}</span>
                    </div>
                    <div className="tournament-time">
                      ⏰ Until {new Date(tournament.end_date).toLocaleTimeString()}
                    </div>
                  </div>
                  <button 
                    className="btn btn-tournament"
                    onClick={() => startTournament(tournament)}
                  >
                    Enter Tournament
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-tournaments">
              <p>🕒 No active tournaments right now</p>
              <p>Try practice mode or check back later!</p>
              <small>Tournaments run daily 12PM - 7PM</small>
            </div>
          )}
        </div>
      </div>

      <footer className="dashboard-footer">
        <div className="how-to-play">
          <h3>💡 How to Play:</h3>
          <p>Flip cards to find matching pairs. Complete all 6 pairs in the fewest moves and fastest time!</p>
          <p><strong>Scoring:</strong> 1000 base points - (time×2) - (extra moves×5)</p>
        </div>
      </footer>
    </div>
  );
};

export default MemoryMatchDashboard;
```

### **2. Memory Game Engine Component**
```jsx
import React, { useState, useEffect } from 'react';

const MemoryGameEngine = ({ mode, tournamentId, onGameComplete }) => {
  const [cards, setCards] = useState([]);
  const [flippedCards, setFlippedCards] = useState([]);
  const [matchedCards, setMatchedCards] = useState([]);
  const [moves, setMoves] = useState(0);
  const [startTime, setStartTime] = useState(null);
  const [gameStarted, setGameStarted] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCards();
  }, []);

  const fetchCards = async () => {
    try {
      const response = await fetch('/api/entertainment/memory-cards/for-game/');
      const data = await response.json();
      
      // Create pairs: each card appears twice
      const cardPairs = [];
      data.cards.forEach(card => {
        cardPairs.push({ ...card, pairId: card.id, position: Math.random() });
        cardPairs.push({ ...card, pairId: card.id, position: Math.random() });
      });

      // Shuffle cards
      const shuffledCards = cardPairs
        .sort(() => Math.random() - 0.5)
        .map((card, index) => ({
          ...card,
          id: `card-${index}`,
          isFlipped: false,
          isMatched: false
        }));

      setCards(shuffledCards);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching cards:', error);
      setLoading(false);
    }
  };

  const handleCardClick = (cardId) => {
    if (!gameStarted) {
      setGameStarted(true);
      setStartTime(Date.now());
    }

    const card = cards.find(c => c.id === cardId);
    if (card.isFlipped || card.isMatched || flippedCards.length === 2) {
      return;
    }

    const newFlippedCards = [...flippedCards, cardId];
    setFlippedCards(newFlippedCards);

    // Update card state
    setCards(cards.map(c => 
      c.id === cardId ? { ...c, isFlipped: true } : c
    ));

    if (newFlippedCards.length === 2) {
      setMoves(moves + 1);
      
      // Check for match
      const card1 = cards.find(c => c.id === newFlippedCards[0]);
      const card2 = cards.find(c => c.id === newFlippedCards[1]);

      if (card1.pairId === card2.pairId) {
        // Match found!
        const newMatchedCards = [...matchedCards, ...newFlippedCards];
        setMatchedCards(newMatchedCards);
        
        setCards(cards.map(c => 
          newFlippedCards.includes(c.id) ? { ...c, isMatched: true } : c
        ));
        
        setFlippedCards([]);

        // Check if game is complete
        if (newMatchedCards.length === cards.length) {
          const endTime = Date.now();
          const timeSeconds = Math.round((endTime - startTime) / 1000);
          
          onGameComplete({
            timeSeconds,
            moves: moves + 1,
            completed: true
          });
        }
      } else {
        // No match - flip back after delay
        setTimeout(() => {
          setCards(cards.map(c => 
            newFlippedCards.includes(c.id) ? { ...c, isFlipped: false } : c
          ));
          setFlippedCards([]);
        }, 1000);
      }
    }
  };

  const getCurrentTime = () => {
    if (!gameStarted || !startTime) return 0;
    return Math.round((Date.now() - startTime) / 1000);
  };

  if (loading) {
    return <div className="game-loading">Loading cards...</div>;
  }

  return (
    <div className="memory-game-engine">
      <div className="game-stats">
        <div className="stat">
          <label>Moves:</label>
          <span>{moves}</span>
        </div>
        <div className="stat">
          <label>Time:</label>
          <span>{getCurrentTime()}s</span>
        </div>
        <div className="stat">
          <label>Pairs:</label>
          <span>{matchedCards.length / 2} / 6</span>
        </div>
      </div>

      <div className="game-grid">
        {cards.map((card) => (
          <div
            key={card.id}
            className={`memory-card ${card.isFlipped ? 'flipped' : ''} ${card.isMatched ? 'matched' : ''}`}
            onClick={() => handleCardClick(card.id)}
          >
            <div className="card-front">
              {card.isFlipped || card.isMatched ? (
                <img 
                  src={card.image_url} 
                  alt={card.name}
                  className="card-image"
                />
              ) : (
                <div className="card-back">🎮</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {!gameStarted && (
        <div className="game-instructions">
          <p>Click any card to start the game!</p>
        </div>
      )}
    </div>
  );
};

export default MemoryGameEngine;
```

### **3. Practice Game Page**
```jsx
import React, { useState } from 'react';
import MemoryGameEngine from './MemoryGameEngine';

const PracticeGamePage = () => {
  const [gameCompleted, setGameCompleted] = useState(false);
  const [gameStats, setGameStats] = useState(null);

  const handleGameComplete = (stats) => {
    setGameStats(stats);
    setGameCompleted(true);
    savePracticeScore(stats);
  };

  const savePracticeScore = (stats) => {
    const score = calculateScore(stats.timeSeconds, stats.moves);
    const practiceScore = {
      score,
      time: stats.timeSeconds,
      moves: stats.moves,
      timestamp: new Date().toISOString(),
      date: new Date().toLocaleDateString()
    };
    
    let savedScores = JSON.parse(localStorage.getItem('practiceScores') || '[]');
    savedScores.push(practiceScore);
    savedScores.sort((a, b) => b.score - a.score); // Sort by score desc
    savedScores = savedScores.slice(0, 10); // Keep top 10 scores
    localStorage.setItem('practiceScores', JSON.stringify(savedScores));
  };

  const calculateScore = (timeSeconds, moves) => {
    const baseScore = 1000;
    const optimalMoves = 12;
    const timePenalty = timeSeconds * 2;
    const extraMoves = Math.max(0, moves - optimalMoves);
    const movesPenalty = extraMoves * 5;
    return Math.max(0, baseScore - timePenalty - movesPenalty);
  };

  const playAgain = () => {
    setGameCompleted(false);
    setGameStats(null);
  };

  const backToDashboard = () => {
    window.location.href = '/games/memory-match';
  };

  return (
    <div className="practice-game-page">
      <header className="game-header">
        <button onClick={backToDashboard} className="btn-back">
          ← Back to Dashboard
        </button>
        <h1>🏃‍♀️ Practice Mode</h1>
        <p>No pressure • Play at your own pace</p>
      </header>

      {!gameCompleted ? (
        <MemoryGameEngine 
          mode="practice"
          onGameComplete={handleGameComplete}
        />
      ) : (
        <div className="practice-complete">
          <h2>🎉 Practice Complete!</h2>
          <div className="game-results">
            <div className="stat-card">
              <div className="stat-icon">⏱️</div>
              <div className="stat-content">
                <span className="label">Time</span>
                <span className="value">{gameStats.timeSeconds}s</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🔄</div>
              <div className="stat-content">
                <span className="label">Moves</span>
                <span className="value">{gameStats.moves}</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🎯</div>
              <div className="stat-content">
                <span className="label">Score</span>
                <span className="value">{calculateScore(gameStats.timeSeconds, gameStats.moves)}</span>
              </div>
            </div>
          </div>
          
          <div className="practice-actions">
            <button onClick={playAgain} className="btn btn-primary">
              🔄 Play Again
            </button>
            <button onClick={backToDashboard} className="btn btn-secondary">
              🏠 Back to Dashboard
            </button>
          </div>
          
          <PracticeScoreHistory />
        </div>
      )}
    </div>
  );
};

const PracticeScoreHistory = () => {
  const [scores] = useState(() => {
    return JSON.parse(localStorage.getItem('practiceScores') || '[]');
  });

  return (
    <div className="practice-history">
      <h3>📊 Your Best Practice Scores</h3>
      {scores.length > 0 ? (
        <div className="scores-list">
          {scores.slice(0, 5).map((score, index) => (
            <div key={index} className="score-item">
              <span className="rank">#{index + 1}</span>
              <span className="score-value">{score.score}</span>
              <span className="score-details">
                {score.time}s • {score.moves} moves
              </span>
              <span className="score-date">{score.date}</span>
            </div>
          ))}
        </div>
      ) : (
        <p>No practice scores yet. Start playing to track your progress!</p>
      )}
    </div>
  );
};

export default PracticeGamePage;
```

### **4. Tournament Game Page**
```jsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import MemoryGameEngine from './MemoryGameEngine';

const TournamentGamePage = () => {
  const { id: tournamentId } = useParams();
  const [tournament, setTournament] = useState(null);
  const [gameCompleted, setGameCompleted] = useState(false);
  const [gameStats, setGameStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTournament();
  }, [tournamentId]);

  const fetchTournament = async () => {
    try {
      const response = await fetch(`/api/entertainment/tournaments/${tournamentId}/`);
      const data = await response.json();
      setTournament(data);
    } catch (error) {
      console.error('Error fetching tournament:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGameComplete = (stats) => {
    setGameStats(stats);
    setGameCompleted(true);
  };

  const handleScoreSubmission = async (playerName, roomNumber) => {
    try {
      const response = await fetch(
        `/api/entertainment/tournaments/${tournamentId}/submit_score/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            player_name: playerName,
            room_number: roomNumber,
            time_seconds: gameStats.timeSeconds,
            moves_count: gameStats.moves
          })
        }
      );

      const result = await response.json();
      
      if (response.ok) {
        // Show success message
        alert(`🎉 Score Submitted Successfully!\n\nYour Score: ${result.score}\nCurrent Rank: #${result.rank}\n\nGreat job ${playerName}!`);
        window.location.href = `/games/memory-match`;
      } else {
        alert(`❌ Error: ${result.error}`);
      }
    } catch (error) {
      console.error('Error submitting score:', error);
      alert('Failed to submit score. Please try again.');
    }
  };

  const backToDashboard = () => {
    window.location.href = '/games/memory-match';
  };

  if (loading) {
    return <div className="loading">Loading tournament...</div>;
  }

  if (!tournament) {
    return (
      <div className="error">
        <h2>Tournament not found</h2>
        <button onClick={backToDashboard}>Back to Dashboard</button>
      </div>
    );
  }

  return (
    <div className="tournament-game-page">
      <header className="tournament-header">
        <button onClick={backToDashboard} className="btn-back">
          ← Back to Dashboard
        </button>
        <h1>🏆 {tournament.name}</h1>
        <p>{tournament.description}</p>
        <div className="tournament-info">
          <span>👥 {tournament.participant_count} players joined</span>
          <span>🎯 3×4 Grid • 6 Pairs</span>
          <span>🎁 {tournament.first_prize}</span>
        </div>
      </header>

      {!gameCompleted ? (
        <div className="tournament-game-area">
          <div className="tournament-rules">
            <h3>🎮 Tournament Rules:</h3>
            <ul>
              <li>Match all 6 pairs as quickly as possible</li>
              <li>Fewer moves = higher score</li>
              <li>One attempt per tournament</li>
              <li>Winners announced at the end</li>
            </ul>
          </div>
          
          <MemoryGameEngine 
            mode="tournament"
            tournamentId={tournamentId}
            onGameComplete={handleGameComplete}
          />
        </div>
      ) : (
        <TournamentScoreSubmission 
          gameStats={gameStats}
          tournament={tournament}
          onSubmit={handleScoreSubmission}
        />
      )}
    </div>
  );
};

const TournamentScoreSubmission = ({ gameStats, tournament, onSubmit }) => {
  const [playerName, setPlayerName] = useState('');
  const [roomNumber, setRoomNumber] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const calculateScore = (timeSeconds, moves) => {
    const baseScore = 1000;
    const optimalMoves = 12;
    const timePenalty = timeSeconds * 2;
    const extraMoves = Math.max(0, moves - optimalMoves);
    const movesPenalty = extraMoves * 5;
    return Math.max(0, baseScore - timePenalty - movesPenalty);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!playerName.trim() || !roomNumber.trim() || submitting) return;

    setSubmitting(true);
    await onSubmit(playerName.trim(), roomNumber.trim());
    setSubmitting(false);
  };

  const finalScore = calculateScore(gameStats.timeSeconds, gameStats.moves);

  return (
    <div className="tournament-score-submission">
      <div className="game-complete-header">
        <h2>🎉 Tournament Game Complete!</h2>
        <p>Excellent work! Here are your results:</p>
      </div>

      <div className="final-stats">
        <div className="stat-card time-stat">
          <div className="stat-icon">⏱️</div>
          <h3>Time</h3>
          <p className="stat-value">{gameStats.timeSeconds}s</p>
        </div>
        <div className="stat-card moves-stat">
          <div className="stat-icon">🔄</div>
          <h3>Moves</h3>
          <p className="stat-value">{gameStats.moves}</p>
        </div>
        <div className="stat-card score-stat">
          <div className="stat-icon">🎯</div>
          <h3>Final Score</h3>
          <p className="stat-value">{finalScore}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="score-form">
        <div className="form-header">
          <h3>📝 Submit Your Tournament Score</h3>
          <p>Enter your details to join the leaderboard and compete for prizes!</p>
        </div>
        
        <div className="form-fields">
          <div className="form-group">
            <label htmlFor="playerName">
              <span className="label-icon">👤</span>
              Your Name:
            </label>
            <input
              type="text"
              id="playerName"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              placeholder="Enter your name"
              maxLength="50"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="roomNumber">
              <span className="label-icon">🏠</span>
              Room Number:
            </label>
            <input
              type="text"
              id="roomNumber"
              value={roomNumber}
              onChange={(e) => setRoomNumber(e.target.value)}
              placeholder="Enter your room number"
              maxLength="20"
              required
            />
          </div>
        </div>
        
        <button 
          type="submit" 
          className="btn btn-submit"
          disabled={!playerName.trim() || !roomNumber.trim() || submitting}
        >
          {submitting ? (
            <>
              <span className="spinner">⏳</span>
              Submitting Score...
            </>
          ) : (
            <>
              🏆 Submit to Tournament Leaderboard
            </>
          )}
        </button>

        <div className="tournament-prizes">
          <h4>🎁 Tournament Prizes:</h4>
          <div className="prizes-list">
            <div className="prize">🥇 1st: {tournament.first_prize}</div>
            <div className="prize">🥈 2nd: {tournament.second_prize}</div>
            <div className="prize">🥉 3rd: {tournament.third_prize}</div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default TournamentGamePage;
```

---

## 🎨 **CSS Styles (Basic Structure)**

```css
/* Dashboard Styles */
.memory-match-dashboard {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 30px;
}

.dashboard-header h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  color: #333;
}

.game-modes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

@media (max-width: 768px) {
  .game-modes {
    grid-template-columns: 1fr;
  }
}

.game-mode-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border: 2px solid #f0f0f0;
  transition: transform 0.2s, box-shadow 0.2s;
}

.game-mode-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}

.practice-mode {
  border-left: 4px solid #4CAF50;
}

.tournament-mode {
  border-left: 4px solid #FF9800;
}

.mode-icon {
  font-size: 3rem;
  text-align: center;
  margin-bottom: 16px;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 16px 0;
}

.feature-list li {
  padding: 4px 0;
  font-size: 0.9rem;
  color: #666;
}

.btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  width: 100%;
}

.btn:hover {
  background: #0056b3;
}

.btn-practice {
  background: #4CAF50;
}

.btn-practice:hover {
  background: #45a049;
}

.btn-tournament {
  background: #FF9800;
}

.btn-tournament:hover {
  background: #f57c00;
}

/* Game Engine Styles */
.memory-game-engine {
  max-width: 600px;
  margin: 0 auto;
}

.game-stats {
  display: flex;
  justify-content: space-around;
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.game-stats .stat {
  text-align: center;
}

.game-stats .stat label {
  display: block;
  font-weight: 600;
  color: #666;
  font-size: 0.9rem;
}

.game-stats .stat span {
  display: block;
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
}

.game-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 0 auto;
  max-width: 400px;
}

.memory-card {
  aspect-ratio: 1;
  background: #007bff;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  user-select: none;
}

.memory-card:hover {
  transform: scale(1.05);
}

.memory-card.flipped {
  background: white;
  border: 2px solid #007bff;
}

.memory-card.matched {
  background: #4CAF50;
  border: 2px solid #45a049;
  cursor: default;
}

.card-image {
  width: 80%;
  height: 80%;
  object-fit: contain;
  border-radius: 4px;
}

.card-back {
  color: white;
  font-size: 1.5rem;
}

/* Tournament Submission Styles */
.tournament-score-submission {
  max-width: 500px;
  margin: 0 auto;
}

.final-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 30px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stat-icon {
  font-size: 2rem;
  margin-bottom: 8px;
}

.stat-card h3 {
  margin: 8px 0 4px 0;
  color: #666;
  font-size: 0.9rem;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: bold;
  color: #333;
}

.score-form {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
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

.form-group input {
  width: 100%;
  padding: 12px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}

.form-group input:focus {
  outline: none;
  border-color: #007bff;
}

.tournament-prizes {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.prizes-list {
  display: grid;
  gap: 8px;
}

.prize {
  padding: 8px;
  background: white;
  border-radius: 6px;
  font-weight: 600;
}

/* Responsive Design */
@media (max-width: 768px) {
  .final-stats {
    grid-template-columns: 1fr;
  }
  
  .game-grid {
    max-width: 320px;
    gap: 8px;
  }
  
  .memory-card {
    font-size: 0.8rem;
  }
}
```

---

## � **QR Code Management (Admin/Staff)**

### **⚠️ IMPORTANT: DO NOT Generate QR Codes in Frontend**
- QR codes are already generated and stored in the backend
- Frontend should only **FETCH and DISPLAY** existing QR codes
- Use tournament API to get QR URLs, don't create new ones

### **QR Code Display Component**
```jsx
import React, { useState, useEffect } from 'react';

const TournamentQRManager = () => {
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllTournaments();
  }, []);

  const fetchAllTournaments = async () => {
    try {
      const response = await fetch('/api/entertainment/tournaments/?hotel=hotel-killarney');
      const data = await response.json();
      setTournaments(data.results || []);
    } catch (error) {
      console.error('Error fetching tournaments:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadQR = async (tournament) => {
    if (!tournament.qr_code_url) {
      alert('QR code not available for this tournament');
      return;
    }

    try {
      // Create a styled QR code image with tournament info
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      // Set canvas size
      canvas.width = 400;
      canvas.height = 500;
      
      // Create QR image
      const qrImg = new Image();
      qrImg.crossOrigin = 'anonymous';
      
      qrImg.onload = () => {
        // Background
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, 400, 500);
        
        // Tournament header
        ctx.fillStyle = '#007bff';
        ctx.fillRect(0, 0, 400, 80);
        
        // Hotel name
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 18px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Hotel Killarney', 200, 30);
        
        // Tournament name
        ctx.font = 'bold 16px Arial';
        ctx.fillText('Memory Match Tournament', 200, 55);
        
        // QR Code
        const qrSize = 250;
        const qrX = (400 - qrSize) / 2;
        const qrY = 100;
        ctx.drawImage(qrImg, qrX, qrY, qrSize, qrSize);
        
        // Tournament details
        ctx.fillStyle = '#333333';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        
        const date = new Date(tournament.start_date).toLocaleDateString('en-US', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        });
        
        const time = new Date(tournament.start_date).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit'
        });
        
        ctx.fillText(date, 200, 380);
        ctx.fillText(`${time} - ${new Date(tournament.end_date).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit'
        })}`, 200, 400);
        
        // Instructions
        ctx.font = '12px Arial';
        ctx.fillStyle = '#666666';
        ctx.fillText('Scan to play Memory Match', 200, 430);
        ctx.fillText('3×4 Grid • 6 Pairs • Win Prizes!', 200, 450);
        
        // Prize info
        ctx.fillText(`1st Prize: ${tournament.first_prize}`, 200, 480);
        
        // Download
        const link = document.createElement('a');
        link.download = `memory-match-qr-${tournament.slug}.png`;
        link.href = canvas.toDataURL();
        link.click();
      };
      
      qrImg.src = tournament.qr_code_url;
      
    } catch (error) {
      console.error('Error downloading QR code:', error);
      // Fallback: direct download
      const link = document.createElement('a');
      link.href = tournament.qr_code_url;
      link.download = `qr-${tournament.slug}.png`;
      link.target = '_blank';
      link.click();
    }
  };

  const copyQRUrl = (tournament) => {
    navigator.clipboard.writeText(tournament.qr_code_url);
    alert('QR code URL copied to clipboard!');
  };

  if (loading) {
    return <div className="loading">Loading tournaments...</div>;
  }

  return (
    <div className="tournament-qr-manager">
      <div className="manager-header">
        <h2>📱 Tournament QR Codes</h2>
        <p>Download and share QR codes for hotel guests</p>
      </div>

      <div className="tournaments-grid">
        {tournaments.map(tournament => (
          <div key={tournament.id} className="tournament-qr-card">
            <div className="tournament-info">
              <h3>{tournament.name}</h3>
              <div className="tournament-meta">
                <span className="date">
                  📅 {new Date(tournament.start_date).toLocaleDateString()}
                </span>
                <span className="status">
                  <span className={`status-badge ${tournament.status}`}>
                    {tournament.status}
                  </span>
                </span>
              </div>
              <div className="tournament-time">
                ⏰ {new Date(tournament.start_date).toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit'
                })} - {new Date(tournament.end_date).toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            </div>

            {tournament.qr_code_url ? (
              <div className="qr-section">
                <div className="qr-preview">
                  <img 
                    src={tournament.qr_code_url} 
                    alt={`QR Code for ${tournament.name}`}
                    className="qr-image"
                  />
                </div>
                <div className="qr-actions">
                  <button 
                    onClick={() => downloadQR(tournament)}
                    className="btn btn-primary"
                    title="Download styled QR code with tournament info"
                  >
                    📥 Download QR
                  </button>
                  <button 
                    onClick={() => copyQRUrl(tournament)}
                    className="btn btn-secondary"
                    title="Copy QR code URL"
                  >
                    📋 Copy URL
                  </button>
                </div>
              </div>
            ) : (
              <div className="no-qr">
                <p>❌ QR code not generated</p>
                <small>Contact admin to generate QR code</small>
              </div>
            )}

            <div className="tournament-stats">
              <div className="stat">
                <span>👥 Players</span>
                <span>{tournament.participant_count || 0}</span>
              </div>
              <div className="stat">
                <span>🎁 Prize</span>
                <span>{tournament.first_prize}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="qr-instructions">
        <h3>📋 QR Code Usage Instructions:</h3>
        <ul>
          <li>🖨️ Print QR codes for display around the hotel</li>
          <li>📱 Share QR URLs in hotel app or website</li>
          <li>🎯 Each QR code leads to the game dashboard</li>
          <li>🏆 Guests can choose Practice or Tournament mode</li>
          <li>⚡ No app installation required - works in any browser</li>
        </ul>
      </div>
    </div>
  );
};

export default TournamentQRManager;
```

### **QR Code Styles**
```css
.tournament-qr-manager {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.manager-header {
  text-align: center;
  margin-bottom: 30px;
}

.tournaments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.tournament-qr-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border: 1px solid #e1e5e9;
}

.tournament-info h3 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 1.1rem;
}

.tournament-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.active {
  background: #d4edda;
  color: #155724;
}

.status-badge.upcoming {
  background: #fff3cd;
  color: #856404;
}

.status-badge.completed {
  background: #d1ecf1;
  color: #0c5460;
}

.qr-section {
  margin: 20px 0;
  text-align: center;
}

.qr-preview {
  margin-bottom: 15px;
}

.qr-image {
  width: 150px;
  height: 150px;
  border: 2px solid #f0f0f0;
  border-radius: 8px;
}

.qr-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.qr-actions .btn {
  padding: 8px 16px;
  font-size: 0.9rem;
}

.tournament-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.tournament-stats .stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 0.9rem;
}

.tournament-stats .stat span:first-child {
  color: #666;
  margin-bottom: 4px;
}

.tournament-stats .stat span:last-child {
  font-weight: 600;
  color: #333;
}

.qr-instructions {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.qr-instructions h3 {
  margin-top: 0;
  color: #333;
}

.qr-instructions ul {
  margin: 0;
  padding-left: 20px;
}

.qr-instructions li {
  margin-bottom: 8px;
  color: #555;
}

.no-qr {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  margin: 15px 0;
}
```

---

## �🚀 **Implementation Checklist**

### **Frontend Tasks:**
- [ ] Create `/games/memory-match` dashboard route
- [ ] Create `/games/memory-match/practice` route  
- [ ] Create `/games/memory-match/tournament/:id` route
- [ ] Implement `MemoryGameEngine` component
- [ ] Add card flip animations
- [ ] Implement localStorage for practice scores
- [ ] Add responsive mobile design
- [ ] **QR Code Management (Admin/Staff):**
  - [ ] Create `TournamentQRManager` component
  - [ ] Fetch existing QR codes (DO NOT generate new ones)
  - [ ] Add styled QR download with tournament info
  - [ ] Add QR URL copy functionality
  - [ ] Display tournament status and details
- [ ] Test API integrations

### **API Integrations:**
- [x] ✅ Cards API: `/api/entertainment/memory-cards/for-game/`
- [x] ✅ Active Tournaments: `/api/entertainment/tournaments/active_for_hotel/?hotel=hotel-killarney`
- [x] ✅ All Tournaments (for QR management): `/api/entertainment/tournaments/?hotel=hotel-killarney`
- [x] ✅ Submit Score: `/api/entertainment/tournaments/{id}/submit_score/`

### **QR Code Flow:**
- [x] ✅ QR codes point to: `/games/memory-match/?hotel=hotel-killarney`
- [x] ✅ Dashboard detects hotel parameter
- [x] ✅ Dashboard fetches active tournaments for hotel

---

## 🎯 **Key Features Implemented**

1. **🔄 Dashboard Architecture**: Single entry point for all games
2. **🎮 6-Card System**: Fixed 3x4 grid with 6 pairs from backend
3. **🏃‍♀️ Practice Mode**: Unlimited play with localStorage scoring  
4. **🏆 Tournament Mode**: Anonymous entry with real-time scoring
5. **📱 QR Code Management**: Fetch, display, and download existing QR codes with styled tournament info
6. **📱 Mobile Optimized**: Responsive design for mobile scanning
7. **🎁 Prize Integration**: Shows tournament rewards
8. **⚡ Fast Loading**: Optimized API calls and caching

## ⚠️ **Critical QR Code Guidelines**

### **DO NOT Generate QR Codes in Frontend:**
- ❌ Never create new QR codes in frontend
- ✅ Always fetch existing QR codes from backend API
- ✅ QR codes are pre-generated and stored in Cloudinary
- ✅ Use tournament API to get `qr_code_url` field

### **QR Code Download Features:**
- 📥 Styled QR downloads with tournament date/time
- 📋 Copy QR URL to clipboard
- 🖨️ Print-ready format with hotel branding
- 📊 Tournament status and participant count
- 🎁 Prize information display

**Ready for production deployment!** 🚀