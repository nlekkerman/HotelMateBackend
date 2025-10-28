# 🎮 Frontend Tournament Integration Guide

## 📡 API Endpoints Overview

### **Base URL:** `https://your-backend-domain.com/api/entertainment/tournaments/`

---

## 🏆 1. Fetch Active Tournaments for Hotel

### **Endpoint:**
```
GET /api/entertainment/tournaments/active_for_hotel/?hotel={hotel_slug}
```

### **Frontend Implementation:**
```javascript
// React Hook for fetching tournaments
import { useState, useEffect } from 'react';

const useTournaments = (hotelSlug) => {
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!hotelSlug) return;
    
    fetchTournaments();
  }, [hotelSlug]);

  const fetchTournaments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(
        `/api/entertainment/tournaments/active_for_hotel/?hotel=${hotelSlug}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            // Add CORS headers if needed
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setTournaments(data.tournaments || []);
      
    } catch (err) {
      console.error('Error fetching tournaments:', err);
      setError(err.message);
      setTournaments([]);
    } finally {
      setLoading(false);
    }
  };

  return { tournaments, loading, error, refetch: fetchTournaments };
};

// Usage in component
const TournamentPage = () => {
  const [searchParams] = useSearchParams();
  const hotelSlug = searchParams.get('hotel'); // e.g., "hotel-killarney"
  
  const { tournaments, loading, error } = useTournaments(hotelSlug);

  if (loading) return <div>Loading tournaments...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>🏆 Memory Match Tournaments</h1>
      {tournaments.length > 0 ? (
        tournaments.map(tournament => (
          <TournamentCard key={tournament.id} tournament={tournament} />
        ))
      ) : (
        <div>No active tournaments found for {hotelSlug}</div>
      )}
    </div>
  );
};
```

### **Expected Response:**
```json
{
  "tournaments": [
    {
      "id": 23,
      "name": "🧪 TEST Tournament - Frontend Testing",
      "description": "Quick 10-minute test tournament for frontend development...",
      "hotel": {
        "id": 1,
        "name": "Hotel Killarney",
        "slug": "hotel-killarney"
      },
      "status": "active",
      "start_date": "2025-10-28T11:19:50.954770Z",
      "end_date": "2025-10-28T11:29:50.954770Z",
      "registration_deadline": "2025-10-28T11:29:50.954770Z",
      "first_prize": "🥇 Testing Champion Badge",
      "second_prize": "🥈 Frontend Hero Medal",
      "third_prize": "🥉 QR Code Master Certificate",
      "max_participants": 50,
      "participant_count": 0,
      "min_age": 6,
      "max_age": 18,
      "qr_code_url": "https://res.cloudinary.com/...",
      "is_active": true,
      "time_remaining": "8 minutes, 15 seconds"
    }
  ],
  "count": 1
}
```

---

## 🎯 2. Submit Tournament Score

### **Endpoint:**
```
POST /api/entertainment/tournaments/{tournament_id}/submit_score/
```

### **Frontend Implementation:**
```javascript
const submitTournamentScore = async (tournamentId, scoreData) => {
  try {
    const response = await fetch(
      `/api/entertainment/tournaments/${tournamentId}/submit_score/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(scoreData)
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result;
    
  } catch (error) {
    console.error('Error submitting score:', error);
    throw error;
  }
};

// Usage after game completion
const handleGameComplete = async (gameResults) => {
  const scoreData = {
    player_name: gameResults.playerName || "Anonymous Player",
    room_number: gameResults.roomNumber || "Not specified",
    time_seconds: gameResults.timeInSeconds,
    moves_count: gameResults.totalMoves
  };

  try {
    const result = await submitTournamentScore(tournamentId, scoreData);
    
    // Show success message
    console.log('Score submitted successfully!');
    console.log(`Your score: ${result.score}`);
    console.log(`Your rank: ${result.rank}`);
    console.log(`Message: ${result.message}`);
    
    // Redirect or show results
    showResultsScreen(result);
    
  } catch (error) {
    // Handle error gracefully for kids
    console.error('Score submission failed:', error);
    showResultsScreen({ 
      score: calculateLocalScore(gameResults),
      message: "Great job! Your score has been recorded."
    });
  }
};
```

### **Request Payload:**
```json
{
  "player_name": "Alex Smith",
  "room_number": "304",
  "time_seconds": 45,
  "moves_count": 18
}
```

### **Expected Response:**
```json
{
  "message": "Score submitted successfully!",
  "session_id": 456,
  "score": 850,
  "player_name": "Alex Smith",
  "rank": 3
}
```

---

## 🔄 3. Real-time Tournament Status

### **Polling Implementation:**
```javascript
const useTournamentPolling = (hotelSlug, intervalMs = 30000) => {
  const [tournaments, setTournaments] = useState([]);
  
  useEffect(() => {
    if (!hotelSlug) return;
    
    // Initial fetch
    fetchTournaments();
    
    // Set up polling
    const interval = setInterval(fetchTournaments, intervalMs);
    
    return () => clearInterval(interval);
  }, [hotelSlug, intervalMs]);
  
  const fetchTournaments = async () => {
    try {
      const response = await fetch(
        `/api/entertainment/tournaments/active_for_hotel/?hotel=${hotelSlug}`
      );
      const data = await response.json();
      setTournaments(data.tournaments || []);
    } catch (error) {
      console.error('Polling error:', error);
    }
  };
  
  return tournaments;
};
```

---

## 🎨 4. Tournament Card Component

```javascript
const TournamentCard = ({ tournament, onJoin }) => {
  const [timeLeft, setTimeLeft] = useState('');
  
  useEffect(() => {
    const updateTimeLeft = () => {
      const now = new Date();
      const endTime = new Date(tournament.end_date);
      const diff = endTime - now;
      
      if (diff > 0) {
        const minutes = Math.floor(diff / 60000);
        const seconds = Math.floor((diff % 60000) / 1000);
        setTimeLeft(`${minutes}m ${seconds}s`);
      } else {
        setTimeLeft('Expired');
      }
    };
    
    updateTimeLeft();
    const interval = setInterval(updateTimeLeft, 1000);
    
    return () => clearInterval(interval);
  }, [tournament.end_date]);
  
  const isActive = tournament.status === 'active' && timeLeft !== 'Expired';
  
  return (
    <div className={`tournament-card ${isActive ? 'active' : 'inactive'}`}>
      <div className="tournament-header">
        <h3>{tournament.name}</h3>
        <span className={`status ${tournament.status}`}>
          {tournament.status}
        </span>
      </div>
      
      <div className="tournament-info">
        <p className="description">{tournament.description}</p>
        
        <div className="tournament-details">
          <div className="detail">
            <span className="icon">⏰</span>
            <span>Time Left: {timeLeft}</span>
          </div>
          <div className="detail">
            <span className="icon">👥</span>
            <span>{tournament.participant_count} players</span>
          </div>
          <div className="detail">
            <span className="icon">🏆</span>
            <span>{tournament.first_prize}</span>
          </div>
        </div>
      </div>
      
      {isActive ? (
        <button 
          className="join-button active"
          onClick={() => onJoin(tournament)}
        >
          🚀 Join Tournament
        </button>
      ) : (
        <button className="join-button inactive" disabled>
          {tournament.status === 'completed' ? '✅ Completed' : '⏳ Not Available'}
        </button>
      )}
    </div>
  );
};
```

---

## 🛠️ 5. Error Handling & Fallbacks

```javascript
const TournamentErrorBoundary = ({ children }) => {
  const [hasError, setHasError] = useState(false);
  
  useEffect(() => {
    const handleError = (error) => {
      console.error('Tournament error:', error);
      setHasError(true);
    };
    
    window.addEventListener('unhandledrejection', handleError);
    return () => window.removeEventListener('unhandledrejection', handleError);
  }, []);
  
  if (hasError) {
    return (
      <div className="tournament-error">
        <h3>🚧 Tournaments Temporarily Unavailable</h3>
        <p>We're working to fix this issue. Try refreshing the page or play in practice mode.</p>
        <button onClick={() => window.location.reload()}>
          🔄 Refresh
        </button>
        <button onClick={() => window.location.href = '/games/memory-match/practice'}>
          🎮 Practice Mode
        </button>
      </div>
    );
  }
  
  return children;
};
```

---

## 🔧 6. Environment Configuration

```javascript
// config/api.js
const API_CONFIG = {
  development: {
    baseUrl: 'http://localhost:8000/api',
    timeout: 5000
  },
  production: {
    baseUrl: 'https://your-production-api.com/api',
    timeout: 10000
  }
};

export const getApiConfig = () => {
  const env = process.env.NODE_ENV || 'development';
  return API_CONFIG[env];
};

// api/tournaments.js
import { getApiConfig } from '../config/api';

const config = getApiConfig();

export const fetchTournaments = async (hotelSlug) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), config.timeout);
  
  try {
    const response = await fetch(
      `${config.baseUrl}/entertainment/tournaments/active_for_hotel/?hotel=${hotelSlug}`,
      {
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        }
      }
    );
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
};
```

---

## 🧪 7. Testing Current Tournament

### **Test Tournament Details:**
- **Tournament ID:** `23`
- **Name:** 🧪 TEST Tournament - Frontend Testing  
- **Hotel:** `hotel-killarney`
- **Status:** `active` (10 minutes duration)

### **Test URLs:**
```javascript
// Fetch active tournaments for testing
const testUrl = '/api/entertainment/tournaments/active_for_hotel/?hotel=hotel-killarney';

// Submit score for testing
const submitUrl = '/api/entertainment/tournaments/23/submit_score/';

// Test payload
const testPayload = {
  "player_name": "Test Player",
  "room_number": "123",
  "time_seconds": 45,
  "moves_count": 18
};
```

---

## ✅ 8. Integration Checklist

- [ ] **API Endpoints Working**: Test both GET and POST endpoints
- [ ] **CORS Configuration**: Ensure cross-origin requests work
- [ ] **Error Handling**: Graceful fallbacks for network issues
- [ ] **Real-time Updates**: Polling or websockets for live data
- [ ] **Tournament Status**: Handle active, upcoming, completed states
- [ ] **Score Submission**: Anonymous player support
- [ ] **Time Display**: Show remaining tournament time
- [ ] **Mobile Responsive**: Works on phones/tablets
- [ ] **QR Code Flow**: Test QR scanning → tournaments page
- [ ] **Practice Mode**: Fallback when no tournaments available

---

## 🚀 Quick Start for Testing

1. **Fetch tournaments:** `GET /api/entertainment/tournaments/active_for_hotel/?hotel=hotel-killarney`
2. **Verify active tournament:** Check `tournaments[0].is_active === true`
3. **Play memory game:** Complete 3×4 grid game
4. **Submit score:** `POST /api/entertainment/tournaments/23/submit_score/`
5. **Handle response:** Show score and rank to user

**The test tournament expires 10 minutes after creation, so test quickly!** ⏰