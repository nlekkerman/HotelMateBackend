# HotelMate Tournament QR Code Generation - Frontend Implementation Guide (Updated)

## Overview
This guide explains how to implement QR code generation and display for HotelMate memory game tournaments. The QR codes enable guests to quickly access tournaments on mobile devices **without registration**. Players simply scan, enter their name and room number, and start playing immediately.

## Important Changes
- **No Registration Required**: QR codes now point directly to tournament play pages
- **Unlimited Participants**: No maximum participant limits
- **Direct Play Access**: URL structure changed from `/register/` to `/play/`
- **Anonymous Players**: Only name and room number required

## Backend API Endpoints

### 1. Tournament Management
- **GET** `/api/entertainment/tournaments/` - List all tournaments
- **POST** `/api/entertainment/tournaments/` - Create new tournament
- **GET** `/api/entertainment/tournaments/{id}/` - Get tournament details
- **POST** `/api/entertainment/tournaments/{id}/generate-qr/` - Generate QR code
- **GET** `/api/entertainment/tournaments/{id}/qr-code/` - Get QR code URL

### 2. Tournament QR Code Data Structure
```json
{
  "id": 1,
  "name": "Kids Memory Challenge - Monday",
  "slug": "kids-memory-2025-10-27",
  "hotel": {
    "id": 2,
    "name": "Hotel Killarney", 
    "slug": "hotel-killarney"
  },
  "qr_code_url": "https://res.cloudinary.com/dg0ssec7u/image/upload/v1761565774/tournament_qr/hotel-killarney_kids-memory-2025-10-27.png",
  "start_date": "2025-10-27T12:00:00Z",
  "end_date": "2025-10-27T19:00:00Z", 
  "status": "active",
  "max_participants": 999,
  "difficulty": "intermediate"
}
```

## Frontend Implementation

### 1. React Tournament QR Code Generator Component

```jsx
// components/TournamentQRGenerator.jsx
import React, { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Download, Share2, Printer } from 'lucide-react';

const TournamentQRGenerator = ({ tournamentId, hotel }) => {
  const [tournament, setTournament] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTournamentData();
  }, [tournamentId]);

  const fetchTournamentData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/entertainment/tournaments/${tournamentId}/`);
      const data = await response.json();
      setTournament(data);
      
      // Generate QR code if not exists
      if (!data.qr_code_url) {
        await generateQRCode();
      }
    } catch (err) {
      setError('Failed to fetch tournament data');
    } finally {
      setLoading(false);
    }
  };

  const generateQRCode = async () => {
    try {
      const response = await fetch(`/api/entertainment/tournaments/${tournamentId}/generate-qr/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTournament(prev => ({ ...prev, qr_code_url: data.qr_code_url }));
      }
    } catch (err) {
      setError('Failed to generate QR code');
    }
  };

  const downloadQRCode = () => {
    if (tournament?.qr_code_url) {
      const link = document.createElement('a');
      link.href = tournament.qr_code_url;
      link.download = `${tournament.slug}-qr-code.png`;
      link.click();
    }
  };

  const shareQRCode = async () => {
    if (navigator.share && tournament) {
      try {
        await navigator.share({
          title: `Join ${tournament.name}`,
          text: `Scan this QR code to join the tournament!`,
          url: tournament.qr_code_url
        });
      } catch (err) {
        // Fallback to clipboard
        navigator.clipboard.writeText(tournament.qr_code_url);
      }
    }
  };

  const printQRCode = () => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Tournament QR Code - ${tournament?.name}</title>
          <style>
            body { 
              font-family: Arial, sans-serif; 
              text-align: center; 
              padding: 20px; 
            }
            .qr-container { 
              margin: 20px auto; 
              max-width: 400px; 
            }
            .tournament-info { 
              margin-bottom: 20px; 
            }
            @media print {
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          <div class="tournament-info">
            <h1>${tournament?.name}</h1>
            <p>Hotel: ${tournament?.hotel?.name}</p>
            <p>Date: ${new Date(tournament?.start_date).toLocaleDateString()}</p>
            <p>Time: ${new Date(tournament?.start_date).toLocaleTimeString()} - ${new Date(tournament?.end_date).toLocaleTimeString()}</p>
          </div>
          <div class="qr-container">
            <img src="${tournament?.qr_code_url}" alt="Tournament QR Code" style="max-width: 100%;" />
          </div>
          <p><strong>Scan to join the tournament!</strong></p>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  if (loading) return <div className="loading">Generating QR Code...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!tournament) return null;

  return (
    <div className="tournament-qr-generator">
      <div className="tournament-info">
        <h3>{tournament.name}</h3>
        <p>Hotel: {tournament.hotel?.name}</p>
        <p>Status: {tournament.status}</p>
      </div>

      <div className="qr-code-container">
        {tournament.qr_code_url ? (
          <img 
            src={tournament.qr_code_url} 
            alt="Tournament QR Code"
            className="qr-code-image"
          />
        ) : (
          <QRCodeSVG
            value={`https://hotelsmates.com/tournaments/${hotel}/${tournament.slug}/play/`}
            size={256}
            level="M"
            includeMargin={true}
          />
        )}
      </div>

      <div className="qr-actions">
        <button onClick={downloadQRCode} className="btn btn-primary">
          <Download size={16} /> Download
        </button>
        <button onClick={shareQRCode} className="btn btn-secondary">
          <Share2 size={16} /> Share
        </button>
        <button onClick={printQRCode} className="btn btn-outline">
          <Printer size={16} /> Print
        </button>
      </div>

      <div className="qr-url-info">
        <p><strong>Tournament URL:</strong></p>
        <code>https://hotelsmates.com/tournaments/{hotel}/{tournament.slug}/play/</code>
      </div>
    </div>
  );
};

export default TournamentQRGenerator;
```

### 2. Tournament Display Component for Mobile

```jsx
// components/TournamentMobileDisplay.jsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

const TournamentMobileDisplay = () => {
  const { hotelSlug, tournamentSlug } = useParams();
  const [tournament, setTournament] = useState(null);
  const [gameMode, setGameMode] = useState('practice'); // 'practice' or 'tournament'
  const [playerData, setPlayerData] = useState({
    player_name: '',
    room_number: ''
  });
  
  // Load practice scores from localStorage
  const [practiceScores, setPracticeScores] = useState([]);

  useEffect(() => {
    fetchTournament();
    loadPracticeScores();
  }, [hotelSlug, tournamentSlug]);

  const loadPracticeScores = () => {
    const saved = localStorage.getItem('practiceScores');
    if (saved) {
      setPracticeScores(JSON.parse(saved));
    }
  };

  const savePracticeScore = (scoreData) => {
    const newScores = [...practiceScores, {
      ...scoreData,
      timestamp: new Date().toISOString()
    }].slice(-10); // Keep last 10 scores
    setPracticeScores(newScores);
    localStorage.setItem('practiceScores', JSON.stringify(newScores));
  };

  useEffect(() => {
    fetchTournament();
  }, [hotelSlug, tournamentSlug]);

  const fetchTournament = async () => {
    try {
      const response = await fetch(`/api/entertainment/tournaments/?hotel=${hotelSlug}&slug=${tournamentSlug}`);
      const data = await response.json();
      setTournament(data.results[0]);
    } catch (err) {
      console.error('Failed to fetch tournament');
    }
  };

  const handlePracticeGame = async (gameResults) => {
    try {
      const response = await fetch('/api/entertainment/memory-sessions/practice/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          time_seconds: gameResults.timeSeconds,
          moves_count: gameResults.moves,
          difficulty: tournament?.difficulty || 'intermediate'
        })
      });

      if (response.ok) {
        const scoreData = await response.json();
        savePracticeScore(scoreData);
        alert(`Practice complete! Your score: ${scoreData.score}`);
      }
    } catch (err) {
      console.error('Failed to submit practice score');
    }
  };

  const handleTournamentSubmit = async (gameResults) => {
    // This is called AFTER the game is completed
    // Player enters name and room number at the END
    
    const playerName = prompt('Enter your name:');
    const roomNumber = prompt('Enter your room number:');
    
    if (!playerName || !roomNumber) {
      alert('Name and room number are required to submit your score');
      return;
    }

    try {
      const response = await fetch(`/api/entertainment/tournaments/${tournament.id}/submit_score/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          player_name: playerName,
          room_number: roomNumber,
          time_seconds: gameResults.timeSeconds,
          moves_count: gameResults.moves
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Score submitted! Your score: ${result.score} (Rank: #${result.rank})`);
        // Redirect to leaderboard
        window.location.href = `/tournaments/${hotelSlug}/${tournamentSlug}/leaderboard`;
      }
    } catch (err) {
      console.error('Failed to submit tournament score');
      alert('Failed to submit score. Please try again.');
    }
  };

  const startGame = (mode) => {
    setGameMode(mode);
    // Redirect to game component with mode parameter
    const gameUrl = `/game/memory-match?tournament=${tournament?.id}&mode=${mode}`;
    window.location.href = gameUrl;
  };

  if (!tournament) return <div>Loading tournament...</div>;

  return (
    <div className="tournament-mobile-display">
      <div className="tournament-header">
        <h1>{tournament.name}</h1>
        <p>{tournament.hotel?.name}</p>
        <div className="tournament-status">
          Status: <span className={`status-${tournament.status}`}>{tournament.status}</span>
        </div>
      </div>

      <div className="tournament-details">
        <div className="detail-item">
          <strong>Difficulty:</strong> {tournament.difficulty}
        </div>
        <div className="detail-item">
          <strong>Time:</strong> {new Date(tournament.start_date).toLocaleTimeString()} - {new Date(tournament.end_date).toLocaleTimeString()}
        </div>
        <div className="detail-item">
          <strong>Participants:</strong> {tournament.participant_count || 0} / {tournament.max_participants}
        </div>
      </div>

      <div className="game-modes">
        <div className="practice-mode">
          <h3>🎯 Practice Mode</h3>
          <p>Play to improve your skills! Scores saved locally on your device.</p>
          <button onClick={() => startGame('practice')} className="btn btn-secondary btn-large">
            🎮 Practice Now (Free Play)
          </button>
          
          {practiceScores.length > 0 && (
            <div className="practice-scores">
              <h4>Your Practice Scores:</h4>
              {practiceScores.slice(-3).map((score, idx) => (
                <div key={idx} className="score-item">
                  Score: {score.score} | Time: {score.time_seconds}s | Moves: {score.moves_count}
                </div>
              ))}
            </div>
          )}
        </div>

        {tournament && tournament.is_active && (
          <div className="tournament-mode">
            <h3>🏆 Tournament Mode</h3>
            <p>Compete for prizes! Play now, enter details after you finish:</p>
            <button 
              onClick={() => startGame('tournament')} 
              className="btn btn-primary btn-large"
            >
              🎮 Play Tournament Now!
            </button>
            <p className="tournament-info">
              ⭐ No registration needed!<br/>
              ⭐ Play first, enter name & room after!<br/>
              ⭐ Unlimited attempts allowed!
            </p>
            <p className="participant-info">
              Current players: {tournament.participant_count || 0}
            </p>
          </div>
        )}
      </div>

      {tournament.status === 'completed' && (
        <div className="tournament-completed">
          <h3>Tournament Completed</h3>
          <p>Check out the leaderboard to see the results!</p>
          <button onClick={() => window.location.href = `/tournaments/${hotelSlug}/${tournamentSlug}/leaderboard`}>
            View Leaderboard
          </button>
        </div>
      )}
    </div>
  );
};

export default TournamentMobileDisplay;
```

### 3. CSS Styles

```css
/* TournamentQR.css */
.tournament-qr-generator {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
  text-align: center;
}

.tournament-info {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}

.qr-code-container {
  margin: 20px 0;
  padding: 20px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  display: inline-block;
}

.qr-code-image {
  max-width: 256px;
  width: 100%;
  height: auto;
}

.qr-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin: 20px 0;
}

.qr-actions button {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 10px 15px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary { background: #007bff; color: white; }
.btn-secondary { background: #6c757d; color: white; }
.btn-outline { background: transparent; border: 1px solid #007bff; color: #007bff; }

.qr-url-info {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 5px;
  font-size: 12px;
}

.qr-url-info code {
  display: block;
  margin-top: 5px;
  padding: 5px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 3px;
  word-break: break-all;
}

/* Mobile Tournament Display */
.tournament-mobile-display {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.tournament-header {
  text-align: center;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
}

.tournament-header h1 {
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: 700;
}

.status-active { 
  background: #28a745;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}
.status-upcoming { 
  background: #ffc107;
  color: #212529;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}
.status-completed { 
  background: #6c757d;
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.tournament-details {
  margin: 20px 0;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
}

.detail-item {
  padding: 8px 0;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
}

.detail-item:last-child {
  border-bottom: none;
}

.game-modes {
  margin: 20px 0;
}

.practice-mode {
  margin: 20px 0;
  padding: 20px;
  background: linear-gradient(135deg, #a8e6cf 0%, #dcedc8 100%);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.tournament-mode {
  margin: 20px 0;
  padding: 25px;
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.practice-scores {
  margin-top: 15px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 8px;
}

.score-item {
  padding: 5px 0;
  font-size: 12px;
  color: #2e7d32;
  font-weight: 500;
}

.tournament-info {
  text-align: center;
  margin: 15px 0;
  padding: 10px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  font-size: 14px;
  color: #2e2e2e;
  font-weight: 500;
}

.participant-info {
  text-align: center;
  margin-top: 10px;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-group {
  margin: 15px 0;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 16px;
}

.btn-large {
  width: 100%;
  padding: 15px;
  font-size: 18px;
  font-weight: bold;
}
```

### 4. React Router Configuration

```jsx
// App.jsx - Add these routes
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import TournamentMobileDisplay from './components/TournamentMobileDisplay';
import TournamentQRGenerator from './components/TournamentQRGenerator';

function App() {
  return (
    <Router>
      <Routes>
        {/* Tournament QR Code Routes */}
        <Route 
          path="/tournaments/:hotelSlug/:tournamentSlug/play" 
          element={<TournamentMobileDisplay />} 
        />
        <Route 
          path="/tournaments/:hotelSlug/:tournamentSlug/leaderboard" 
          element={<TournamentLeaderboard />} 
        />
        <Route 
          path="/admin/tournaments/:id/qr" 
          element={<TournamentQRGenerator />} 
        />
        
        {/* Other routes... */}
      </Routes>
    </Router>
  );
}
```

### 5. QR Code Management Hook

```jsx
// hooks/useTournamentQR.js
import { useState, useCallback } from 'react';

export const useTournamentQR = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateQRCode = useCallback(async (tournamentId) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/entertainment/tournaments/${tournamentId}/generate-qr/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to generate QR code');
      
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const bulkGenerateQRCodes = useCallback(async (tournamentIds) => {
    const results = [];
    
    for (const id of tournamentIds) {
      try {
        const result = await generateQRCode(id);
        results.push({ id, success: true, data: result });
      } catch (err) {
        results.push({ id, success: false, error: err.message });
      }
    }
    
    return results;
  }, [generateQRCode]);

  return {
    generateQRCode,
    bulkGenerateQRCodes,
    loading,
    error
  };
};
```

## Backend Management Script

Create this script to bulk generate QR codes for tournaments:

```python
# generate_tournament_qrs.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from entertainment.models import MemoryGameTournament

def generate_qrs_for_all_tournaments():
    tournaments = MemoryGameTournament.objects.filter(
        qr_code_url__isnull=True,
        status__in=['upcoming', 'active']
    )
    
    for tournament in tournaments:
        try:
            success = tournament.generate_qr_code()
            if success:
                print(f"✅ Generated QR code for: {tournament.name}")
            else:
                print(f"❌ Failed to generate QR code for: {tournament.name}")
        except Exception as e:
            print(f"❌ Error generating QR code for {tournament.name}: {e}")

if __name__ == "__main__":
    generate_qrs_for_all_tournaments()
    print("🎉 Done!")
```

## Usage Instructions

1. **Create Tournament**: Use the backend API to create a tournament
2. **Generate QR Code**: The QR code is automatically generated when the tournament is created
3. **Display QR Code**: Use the `TournamentQRGenerator` component in your admin interface
4. **Mobile Access**: The QR code links to the mobile-optimized tournament page
5. **Anonymous Play**: Users can play without accounts using just name and room number

## Key Features

- **Automatic QR Generation**: QR codes are generated automatically and stored on Cloudinary
- **Mobile Optimized**: The tournament display is optimized for mobile devices
- **Anonymous Access**: No authentication required for tournament participation
- **Print/Share Support**: QR codes can be printed or shared easily
- **Bulk Generation**: Script provided for generating multiple QR codes at once

The QR codes will link directly to the tournament registration page where kids can enter their name and room number to start playing immediately.