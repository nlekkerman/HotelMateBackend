# 🎮 Frontend QR Code Generation Integration Guide

## 📋 Overview
This guide shows how to use the backend to generate QR codes for tournament play URLs instead of generating them on the frontend.

## 🔗 Backend API Endpoints

### 1. Tournament List
```javascript
GET /api/entertainment/tournaments/
```
Returns all tournaments with their current QR code URLs.

### 2. Generate QR Code for Tournament  
```javascript
POST /api/entertainment/tournaments/{id}/generate_qr_code/
```
Generates a new QR code for the tournament and returns the Cloudinary URL.

### 3. Get Tournament Details
```javascript
GET /api/entertainment/tournaments/{id}/
```
Returns tournament details including existing QR code URL.

## 🎯 Frontend Implementation

### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

const TournamentQRManager = ({ tournamentId }) => {
  const [tournament, setTournament] = useState(null);
  const [loading, setLoading] = useState(false);
  const [qrGenerating, setQrGenerating] = useState(false);

  // Fetch tournament details
  useEffect(() => {
    fetchTournament();
  }, [tournamentId]);

  const fetchTournament = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/entertainment/tournaments/${tournamentId}/`);
      const data = await response.json();
      setTournament(data);
    } catch (error) {
      console.error('Error fetching tournament:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateQRCode = async () => {
    try {
      setQrGenerating(true);
      const response = await fetch(
        `/api/entertainment/tournaments/${tournamentId}/generate_qr_code/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        // Update tournament with new QR code
        setTournament(prev => ({
          ...prev,
          qr_code_url: data.qr_code_url,
          qr_generated_at: data.generated_at
        }));
        
        console.log('QR Code generated:', data.qr_code_url);
        console.log('Play URL:', data.play_url);
      } else {
        throw new Error('Failed to generate QR code');
      }
    } catch (error) {
      console.error('Error generating QR code:', error);
      alert('Failed to generate QR code. Please try again.');
    } finally {
      setQrGenerating(false);
    }
  };

  if (loading) {
    return <div>Loading tournament...</div>;
  }

  if (!tournament) {
    return <div>Tournament not found</div>;
  }

  return (
    <div className="tournament-qr-manager">
      <h2>{tournament.name}</h2>
      
      {/* Tournament Info */}
      <div className="tournament-info">
        <p><strong>Date:</strong> {new Date(tournament.start_date).toLocaleDateString()}</p>
        <p><strong>Time:</strong> {new Date(tournament.start_date).toLocaleTimeString()} - {new Date(tournament.end_date).toLocaleTimeString()}</p>
        <p><strong>Status:</strong> {tournament.status}</p>
      </div>

      {/* QR Code Section */}
      <div className="qr-code-section">
        <h3>QR Code</h3>
        
        {tournament.qr_code_url ? (
          <div className="qr-code-display">
            <img 
              src={tournament.qr_code_url} 
              alt="Tournament QR Code"
              style={{ width: '200px', height: '200px' }}
            />
            <p><small>Generated: {new Date(tournament.qr_generated_at).toLocaleString()}</small></p>
            
            {/* Play URL for reference */}
            <div className="play-url">
              <strong>Play URL:</strong>
              <br />
              <code>
                https://hotelsmates.com/tournaments/{tournament.hotel.slug}/{tournament.slug}/play/
              </code>
            </div>
          </div>
        ) : (
          <p>No QR code generated yet.</p>
        )}

        {/* Generate/Regenerate Button */}
        <button 
          onClick={generateQRCode}
          disabled={qrGenerating}
          className="btn btn-primary"
        >
          {qrGenerating ? 'Generating...' : (tournament.qr_code_url ? 'Regenerate QR Code' : 'Generate QR Code')}
        </button>
      </div>

      {/* Download/Print Options */}
      {tournament.qr_code_url && (
        <div className="qr-actions">
          <a 
            href={tournament.qr_code_url}
            download={`tournament-${tournament.slug}-qr.png`}
            className="btn btn-secondary"
          >
            Download QR Code
          </a>
          
          <button 
            onClick={() => window.print()}
            className="btn btn-secondary"
          >
            Print QR Code
          </button>
        </div>
      )}
    </div>
  );
};

export default TournamentQRManager;
```

### Tournament List with QR Generation

```jsx
const TournamentList = () => {
  const [tournaments, setTournaments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTournaments();
  }, []);

  const fetchTournaments = async () => {
    try {
      const response = await fetch('/api/entertainment/tournaments/');
      const data = await response.json();
      setTournaments(data.results || data);
    } catch (error) {
      console.error('Error fetching tournaments:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateQRForTournament = async (tournamentId) => {
    try {
      const response = await fetch(
        `/api/entertainment/tournaments/${tournamentId}/generate_qr_code/`,
        { method: 'POST' }
      );

      if (response.ok) {
        const data = await response.json();
        
        // Update the tournament in the list
        setTournaments(prev => 
          prev.map(tournament => 
            tournament.id === tournamentId 
              ? { ...tournament, qr_code_url: data.qr_code_url, qr_generated_at: data.generated_at }
              : tournament
          )
        );
        
        alert('QR code generated successfully!');
      }
    } catch (error) {
      console.error('Error generating QR:', error);
      alert('Failed to generate QR code');
    }
  };

  if (loading) {
    return <div>Loading tournaments...</div>;
  }

  return (
    <div className="tournament-list">
      <h1>🎮 Memory Match Tournaments</h1>
      
      {tournaments.map(tournament => (
        <div key={tournament.id} className="tournament-card">
          <h3>{tournament.name}</h3>
          <p>{tournament.description}</p>
          <p><strong>Date:</strong> {new Date(tournament.start_date).toLocaleDateString()}</p>
          
          <div className="qr-section">
            {tournament.qr_code_url ? (
              <div>
                <img 
                  src={tournament.qr_code_url} 
                  alt="QR Code"
                  style={{ width: '100px', height: '100px' }}
                />
                <button 
                  onClick={() => generateQRForTournament(tournament.id)}
                  className="btn btn-sm btn-secondary"
                >
                  Regenerate QR
                </button>
              </div>
            ) : (
              <button 
                onClick={() => generateQRForTournament(tournament.id)}
                className="btn btn-sm btn-primary"
              >
                Generate QR Code
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
```

## 🎯 Key Frontend Integration Points

### 1. Tournament Display Page
- Show existing QR code if available
- Button to generate/regenerate QR code
- Display the play URL that QR code points to

### 2. Admin Tournament Management
- Bulk QR generation for multiple tournaments
- QR code status indicator
- Direct download/print functionality

### 3. Mobile Optimization
- Responsive QR code display
- Touch-friendly generate buttons
- Easy sharing options

## 📱 QR Code Usage Flow

### For Staff/Admin:
1. **View Tournament** → Click "Generate QR Code" → QR appears
2. **Download/Print** → Share QR code with guests
3. **Guests Scan** → Direct to play URL (no registration needed)

### For Guests:
1. **Scan QR Code** → Redirected to tournament play page
2. **Play Game** → Memory match game loads
3. **Complete Game** → Enter name & room number
4. **Submit Score** → See rank and results

## 🔗 API Response Examples

### Generate QR Code Response:
```json
{
  "message": "QR code generated successfully",
  "qr_code_url": "https://res.cloudinary.com/dg0ssec7u/image/upload/v1234567890/tournament_qr/hotel-killarney_kids-memory-2025-10-27.png",
  "play_url": "https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-27/play/",
  "generated_at": "2025-10-27T12:00:00Z"
}
```

### Tournament Details Response:
```json
{
  "id": 7,
  "name": "Kids Memory Challenge - Sunday",
  "slug": "kids-memory-2025-10-27",
  "description": "Daily kids memory tournament...",
  "hotel": {
    "id": 2,
    "name": "Killarney Hotel",
    "slug": "hotel-killarney"
  },
  "difficulty": "intermediate",
  "start_date": "2025-10-27T12:00:00Z",
  "end_date": "2025-10-27T19:00:00Z",
  "status": "active",
  "qr_code_url": "https://res.cloudinary.com/dg0ssec7u/image/...",
  "qr_generated_at": "2025-10-27T12:00:00Z",
  "max_participants": 999,
  "participant_count": 0,
  "is_active": true
}
```

## 🚀 Implementation Checklist

### Backend (✅ Already Done):
- [x] QR code generation endpoint
- [x] Tournament model with QR fields  
- [x] Cloudinary integration
- [x] Anonymous player support
- [x] Score submission endpoint

### Frontend (📋 To Do):
- [ ] Tournament management component
- [ ] QR code generation UI
- [ ] Tournament play page
- [ ] Score submission form
- [ ] Leaderboard display
- [ ] Mobile responsive design

## 💡 Best Practices

1. **Error Handling**: Always handle API failures gracefully
2. **Loading States**: Show loading indicators during QR generation
3. **Caching**: Store tournament data to minimize API calls
4. **Responsive**: Ensure QR codes display well on all devices
5. **Accessibility**: Include alt text and proper labels
6. **Performance**: Lazy load QR images when possible

## 🔧 Testing

### Manual Testing:
1. Generate QR code via API
2. Scan QR code with mobile device
3. Verify it opens correct tournament play URL
4. Complete game flow and submit score
5. Verify score appears in leaderboard

### API Testing:
```bash
# Generate QR code
curl -X POST http://localhost:8000/api/entertainment/tournaments/7/generate_qr_code/

# Get tournament details
curl http://localhost:8000/api/entertainment/tournaments/7/
```

This approach ensures QR codes are generated server-side with consistent URLs and proper Cloudinary hosting! 🎯