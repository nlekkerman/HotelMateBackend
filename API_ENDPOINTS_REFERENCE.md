# HotelMate Entertainment API Endpoints

## Available API Endpoints

### Router-based Endpoints (REST API)
```
GET    /api/entertainment/games/                     # List all games
GET    /api/entertainment/games/{id}/                # Get specific game
GET    /api/entertainment/memory-cards/              # List memory game cards  
GET    /api/entertainment/memory-cards/{id}/         # Get specific card
GET    /api/entertainment/memory-sessions/           # List memory sessions (user-filtered)
POST   /api/entertainment/memory-sessions/           # Create new session
GET    /api/entertainment/memory-sessions/{id}/      # Get specific session
PUT    /api/entertainment/memory-sessions/{id}/      # Update session
DELETE /api/entertainment/memory-sessions/{id}/      # Delete session
GET    /api/entertainment/tournaments/               # List tournaments
POST   /api/entertainment/tournaments/               # Create tournament
GET    /api/entertainment/tournaments/{id}/          # Get tournament details
PUT    /api/entertainment/tournaments/{id}/          # Update tournament
DELETE /api/entertainment/tournaments/{id}/          # Delete tournament
GET    /api/entertainment/achievements/              # List achievements
GET    /api/entertainment/achievements/{id}/         # Get specific achievement
GET    /api/entertainment/dashboard/                 # Dashboard endpoints
```

### Legacy Endpoints (Backward Compatibility)
```
GET    /api/entertainment/games/                     # Games list
GET    /api/entertainment/games/highscores/          # List highscores
POST   /api/entertainment/games/highscores/          # Create highscore
GET    /api/entertainment/games/qrcodes/             # List QR codes
```

### Memory Game Specific Endpoints
```
GET    /api/entertainment/memory-sessions/my-stats/       # User's game statistics
GET    /api/entertainment/memory-sessions/leaderboard/    # Memory game leaderboard
```

### Tournament Specific Endpoints
```
POST   /api/entertainment/tournaments/{id}/register/      # Register for tournament (legacy)
POST   /api/entertainment/tournaments/{id}/play_session/  # Create anonymous game session ⭐ NEW
GET    /api/entertainment/tournaments/{id}/leaderboard/   # Tournament leaderboard
GET    /api/entertainment/tournaments/{id}/participants/  # Tournament participants
POST   /api/entertainment/tournaments/{id}/start/         # Start tournament (admin)
POST   /api/entertainment/tournaments/{id}/end/           # End tournament (admin)
```

### Achievement Endpoints
```
GET    /api/entertainment/achievements/my-achievements/   # User's unlocked achievements
```

### Dashboard Endpoints
```
GET    /api/entertainment/dashboard/stats/               # Dashboard statistics
```

## Key Endpoints for Tournament System

### 🎮 Anonymous Tournament Play (Main Flow)
```
POST   /api/entertainment/tournaments/{id}/play_session/
```
**Request Body:**
```json
{
  "player_name": "Alex",
  "room_number": "205", 
  "is_anonymous": true,
  "difficulty": "intermediate",
  "time_seconds": 120,
  "moves_count": 24,
  "completed": true
}
```

**Response:**
```json
{
  "id": 123,
  "player_name": "Alex",
  "room_number": "205",
  "is_anonymous": true,
  "difficulty": "intermediate", 
  "score": 850,
  "time_seconds": 120,
  "moves_count": 24,
  "completed": true,
  "tournament": 5,
  "created_at": "2025-10-27T14:30:00Z"
}
```

### 📊 Tournament Leaderboard
```
GET    /api/entertainment/tournaments/{id}/leaderboard/
```
**Response:**
```json
[
  {
    "id": 123,
    "participant_name": "Alex",
    "score": 850,
    "time_seconds": 120,
    "moves_count": 24,
    "rank": 1,
    "room_number": "205",
    "is_anonymous": true,
    "created_at": "2025-10-27T14:30:00Z"
  }
]
```

### 🏆 Tournament Details
```
GET    /api/entertainment/tournaments/{id}/
```
**Response:**
```json
{
  "id": 5,
  "name": "Kids Memory Challenge - Monday",
  "slug": "kids-memory-2025-10-27", 
  "hotel": {
    "id": 2,
    "name": "Hotel Killarney",
    "slug": "hotel-killarney"
  },
  "difficulty": "intermediate",
  "start_date": "2025-10-27T12:00:00Z",
  "end_date": "2025-10-27T19:00:00Z",
  "status": "active",
  "max_participants": 999,
  "qr_code_url": "https://res.cloudinary.com/dg0ssec7u/image/upload/v1761565774/tournament_qr/hotel-killarney_kids-memory-2025-10-27.png",
  "is_active": true,
  "participant_count": 12
}
```

## Example API Calls for Current Tournaments

### Get Today's Tournament (Oct 27, 2025)
```bash
GET /api/entertainment/tournaments/
?hotel=hotel-killarney&status=active&start_date__date=2025-10-27
```

### Create Anonymous Game Session
```bash
POST /api/entertainment/tournaments/5/play_session/
Content-Type: application/json

{
  "player_name": "Emma",
  "room_number": "312",
  "is_anonymous": true,
  "difficulty": "intermediate",
  "time_seconds": 95,
  "moves_count": 20,
  "completed": true
}
```

### Get Tournament Leaderboard
```bash
GET /api/entertainment/tournaments/5/leaderboard/?limit=20
```

## Frontend Integration

### React API Calls
```javascript
// Get tournament details
const tournament = await fetch(`/api/entertainment/tournaments/${tournamentId}/`);

// Create anonymous game session
const session = await fetch(`/api/entertainment/tournaments/${tournamentId}/play_session/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    player_name: playerName,
    room_number: roomNumber, 
    is_anonymous: true,
    difficulty: 'intermediate',
    time_seconds: gameTime,
    moves_count: totalMoves,
    completed: true
  })
});

// Get leaderboard
const leaderboard = await fetch(`/api/entertainment/tournaments/${tournamentId}/leaderboard/`);
```

### URL Mapping to Frontend Routes
```
API Tournament ID → Frontend Route
=================================
Tournament 5 (Oct 27) → /tournaments/hotel-killarney/kids-memory-2025-10-27/play/
Tournament 6 (Oct 28) → /tournaments/hotel-killarney/kids-memory-2025-10-28/play/
Tournament 7 (Oct 29) → /tournaments/hotel-killarney/kids-memory-2025-10-29/play/
Tournament 8 (Oct 30) → /tournaments/hotel-killarney/kids-memory-2025-10-30/play/
Tournament 9 (Oct 31) → /tournaments/hotel-killarney/kids-memory-2025-10-31/play/
Tournament 10 (Nov 1) → /tournaments/hotel-killarney/kids-memory-2025-11-01/play/
Tournament 11 (Nov 2) → /tournaments/hotel-killarney/kids-memory-2025-11-02/play/
```

## Authentication & Permissions

### Anonymous Access (No Auth Required)
- ✅ `GET /tournaments/{id}/` - Tournament details
- ✅ `POST /tournaments/{id}/play_session/` - Create game session
- ✅ `GET /tournaments/{id}/leaderboard/` - View leaderboard

### Authenticated Access Required
- 🔐 `POST /tournaments/` - Create tournament (staff)
- 🔐 `POST /tournaments/{id}/start/` - Start tournament (admin)
- 🔐 `POST /tournaments/{id}/end/` - End tournament (admin)
- 🔐 `GET /memory-sessions/my-stats/` - Personal statistics
- 🔐 `GET /achievements/my-achievements/` - Personal achievements

This API structure supports the complete tournament flow from QR code scanning to anonymous gameplay and real-time leaderboards.