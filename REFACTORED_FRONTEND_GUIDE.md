# 🎮 Memory Match Game - Frontend Implementation Guide

## 🎯 **New Refactored Flow**

### **URL Structure:**
- **QR Code → Dashboard**: `/games/memory-match/?hotel=hotel-killarney`
- **Dashboard → Practice**: Immediate game start
- **Dashboard → Tournament**: Select tournament → Start game
- **Post-game**: Submit score or save to localStorage

## 🏗️ **Frontend Architecture**

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
        `/api/entertainment/tournaments/active/?hotel=${hotelSlug}`
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
    // Navigate to practice game
    window.location.href = '/games/memory-match/practice';
  };

  const startTournament = (tournament) => {
    // Navigate to tournament game with tournament ID
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
      </header>

      <div className="game-modes">
        {/* Practice Mode */}
        <div className="game-mode-card practice-mode">
          <h2>🏃‍♀️ Practice Mode</h2>
          <p>Play without limits • Scores saved locally</p>
          <ul>
            <li>✅ No registration needed</li>
            <li>✅ Unlimited attempts</li>
            <li>✅ Track your best scores</li>
          </ul>
          <button 
            className="btn btn-practice"
            onClick={startPractice}
          >
            Start Practice
          </button>
        </div>

        {/* Tournament Mode */}
        <div className="game-mode-card tournament-mode">
          <h2>🏆 Tournament Mode</h2>
          <p>Compete with other guests • Win prizes!</p>
          
          {tournaments.length > 0 ? (
            <div className="tournaments-list">
              <p>Active Tournaments:</p>
              {tournaments.map(tournament => (
                <div key={tournament.id} className="tournament-option">
                  <div className="tournament-info">
                    <h3>{tournament.name}</h3>
                    <p>{tournament.description}</p>
                    <small>
                      {new Date(tournament.start_date).toLocaleDateString()} • 
                      {tournament.participant_count} players joined
                    </small>
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
            </div>
          )}
        </div>
      </div>

      <footer className="dashboard-footer">
        <p>💡 <strong>How to Play:</strong> Flip cards to find matching pairs. Complete all 6 pairs in the fewest moves and fastest time!</p>
      </footer>
    </div>
  );
};

export default MemoryMatchDashboard;
```

### **2. Practice Game Page**
**Route**: `/games/memory-match/practice`

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
    savedScores = savedScores.slice(-10); // Keep last 10 scores
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
            <div className="stat">
              <span className="label">Time:</span>
              <span className="value">{gameStats.timeSeconds}s</span>
            </div>
            <div className="stat">
              <span className="label">Moves:</span>
              <span className="value">{gameStats.moves}</span>
            </div>
            <div className="stat">
              <span className="label">Score:</span>
              <span className="value">{calculateScore(gameStats.timeSeconds, gameStats.moves)}</span>
            </div>
          </div>
          
          <div className="practice-actions">
            <button onClick={playAgain} className="btn btn-primary">
              Play Again
            </button>
            <button onClick={backToDashboard} className="btn btn-secondary">
              Back to Dashboard
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
      <h3>📊 Your Recent Practice Scores</h3>
      {scores.length > 0 ? (
        <div className="scores-list">
          {scores.slice(-5).reverse().map((score, index) => (
            <div key={index} className="score-item">
              <span className="score-value">{score.score}</span>
              <span className="score-details">
                {score.time}s • {score.moves} moves • {score.date}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p>No practice scores yet. Start playing to see your progress!</p>
      )}
    </div>
  );
};
```

### **3. Tournament Game Page**
**Route**: `/games/memory-match/tournament/:id`

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
        // Show success message and redirect to leaderboard
        alert(`🎉 Score Submitted!\n\nScore: ${result.score}\nRank: #${result.rank}\n\nGreat job!`);
        window.location.href = `/tournaments/${tournamentId}/leaderboard`;
      } else {
        alert(`Error submitting score: ${result.error}`);
      }
    } catch (error) {
      console.error('Error submitting score:', error);
      alert('Failed to submit score. Please try again.');
    }
  };

  if (loading) {
    return <div className="loading">Loading tournament...</div>;
  }

  if (!tournament) {
    return <div className="error">Tournament not found</div>;
  }

  return (
    <div className="tournament-game-page">
      <header className="tournament-header">
        <h1>🏆 {tournament.name}</h1>
        <p>{tournament.description}</p>
        <div className="tournament-stats">
          <span>👥 {tournament.participant_count} players</span>
          <span>🎯 3×4 Grid • 6 Pairs</span>
        </div>
      </header>

      {!gameCompleted ? (
        <MemoryGameEngine 
          mode="tournament"
          tournamentId={tournamentId}
          onGameComplete={handleGameComplete}
        />
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
    if (!playerName.trim() || !roomNumber.trim()) return;

    setSubmitting(true);
    await onSubmit(playerName.trim(), roomNumber.trim());
    setSubmitting(false);
  };

  return (
    <div className="tournament-score-submission">
      <div className="game-complete">
        <h2>🎉 Tournament Game Complete!</h2>
        <div className="final-stats">
          <div className="stat-card">
            <h3>⏱️ Time</h3>
            <p>{gameStats.timeSeconds} seconds</p>
          </div>
          <div className="stat-card">
            <h3>🔄 Moves</h3>
            <p>{gameStats.moves} moves</p>
          </div>
          <div className="stat-card">
            <h3>🎯 Score</h3>
            <p>{calculateScore(gameStats.timeSeconds, gameStats.moves)} points</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="score-form">
        <h3>📝 Enter Your Details</h3>
        <p>Submit your score to join the tournament leaderboard!</p>
        
        <div className="form-group">
          <label htmlFor="playerName">Your Name:</label>
          <input
            type="text"
            id="playerName"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            placeholder="Enter your name"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="roomNumber">Room Number:</label>
          <input
            type="text"
            id="roomNumber"
            value={roomNumber}
            onChange={(e) => setRoomNumber(e.target.value)}
            placeholder="Enter room number"
            required
          />
        </div>
        
        <button 
          type="submit" 
          className="btn btn-submit"
          disabled={!playerName.trim() || !roomNumber.trim() || submitting}
        >
          {submitting ? 'Submitting...' : 'Submit Score to Tournament'}
        </button>
      </form>
    </div>
  );
};
```

## 🔗 **Updated API Endpoints**

### **Get Active Tournaments for Hotel:**
```javascript
GET /api/entertainment/tournaments/active/?hotel=hotel-killarney
```

**Response:**
```json
{
  "tournaments": [
    {
      "id": 9,
      "name": "Kids Memory Challenge - Monday",
      "description": "3x4 grid (6 pairs) - Play anonymously!",
      "grid_size": "3x4 (6 pairs)",
      "participant_count": 4,
      "start_date": "2025-10-27T12:00:00Z",
      "end_date": "2025-10-27T19:00:00Z"
    }
  ],
  "count": 1
}
```

## 🎯 **Key Implementation Points**

### **1. Dashboard Flow:**
- QR scan → `/games/memory-match/?hotel=hotel-killarney`
- Show 2 options: Practice & Tournament
- Fetch active tournaments for the hotel

### **2. Practice Flow:**
- Immediate game start (no forms)
- Score saved to localStorage only
- Show score history from localStorage

### **3. Tournament Flow:**
- Select tournament from dashboard
- Play game immediately
- Post-game: Enter name + room → Submit score

### **4. Updated QR Codes:**
- All QR codes now point to: `/games/memory-match/?hotel={hotel-slug}`
- Single entry point for all tournaments

This refactored approach provides a much cleaner user experience with a central dashboard! 🚀