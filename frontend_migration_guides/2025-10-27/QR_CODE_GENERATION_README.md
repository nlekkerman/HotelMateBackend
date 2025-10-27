# HotelMate Tournament QR Code Generation

## Overview

This guide provides complete instructions for generating and managing QR codes for HotelMate memory game tournaments. The QR codes enable guests to quickly access tournaments on their mobile devices without needing to download an app or create accounts.

## Backend Setup

### 1. Tournament Model
The `MemoryGameTournament` model automatically handles QR code generation:

```python
# The tournament model includes:
- qr_code_url: URLField storing the Cloudinary URL
- generate_qr_code(): Method that creates and uploads QR code
- ### Tournament URL Format
```
QR Code Points To:
https://hotelsmates.com/tournaments/{hotel_slug}/{tournament_slug}/play/

Examples (Generated Oct 27 - Nov 2, 2025):
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-27/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-28/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-29/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-30/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-31/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-11-01/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-11-02/play/
```
```

### 2. QR Code Generation Scripts

#### Quick Script for Killarney Hotel
```bash
python generate_killarney_tournament_qr.py
```

#### Full Management Script
```bash
python generate_tournament_qrs.py
```

## Frontend Implementation

### 1. Required Dependencies
```bash
npm install qrcode.react lucide-react
```

### 2. Key Components
- `TournamentQRGenerator`: Admin interface for managing QR codes
- `TournamentMobileDisplay`: Mobile-optimized tournament registration
- `useTournamentQR`: Hook for QR code management

### 3. Router Setup
```jsx
// Add these routes to your App.jsx
<Route path="/tournaments/:hotelSlug/:tournamentSlug/register" element={<TournamentMobileDisplay />} />
<Route path="/admin/tournaments/:id/qr" element={<TournamentQRGenerator />} />
```

## API Endpoints

### Tournament Management
```
GET  /api/entertainment/tournaments/                    # List tournaments
POST /api/entertainment/tournaments/                    # Create tournament  
GET  /api/entertainment/tournaments/{id}/               # Get tournament details
POST /api/entertainment/tournaments/{id}/play_session/ # Start anonymous game
GET  /api/entertainment/tournaments/{id}/leaderboard/  # Get leaderboard
```

### QR Code Management  
```
POST /api/entertainment/tournaments/{id}/generate-qr/   # Generate QR code
GET  /api/entertainment/tournaments/{id}/qr-code/       # Get QR code URL
```

## Usage Workflow

### 1. Create Tournament (Backend Admin)
```python
# Create tournament through Django admin or API
tournament = MemoryGameTournament.objects.create(
    name="Kids Halloween Memory Tournament",
    hotel_id=2,  # Killarney Hotel
    difficulty='intermediate',
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(hours=7),
    max_participants=50,
    min_age=6,
    max_age=12
)
```

### 2. Generate QR Code
```python
# Automatic generation during tournament creation
success = tournament.generate_qr_code()
print(f"QR Code URL: {tournament.qr_code_url}")
```

### 3. Display QR Code (Frontend)
```jsx
<TournamentQRGenerator 
  tournamentId={tournament.id} 
  hotel="killarney-hotel" 
/>
```

### 4. Mobile Access Flow
1. Guest scans QR code
2. Opens mobile tournament page
3. Enters name and room number
4. Starts playing immediately
5. Scores appear on leaderboard

## QR Code Features

### Print-Ready Format
- High resolution PNG format
- Includes tournament details
- Hotel branding ready
- Print multiple sizes

### Sharing Options
- Direct URL sharing
- Social media integration
- WhatsApp/SMS compatible
- Email attachments

### Mobile Optimization
- Full-screen tournament mode
- Touch-friendly interface
- 6x4 grid (12 pairs) for kids
- Anonymous player support

## File Structure

```
backend/
├── generate_tournament_qrs.py          # Full management script
├── generate_killarney_tournament_qr.py # Quick Killarney script
└── frontend_migration_guides/
    └── 2025-10-27/
        └── tournament-qr-code-generation.md

frontend/
├── components/
│   ├── TournamentQRGenerator.jsx      # Admin QR management
│   ├── TournamentMobileDisplay.jsx    # Mobile tournament page  
│   └── TournamentLeaderboard.jsx      # Results display
├── hooks/
│   └── useTournamentQR.js             # QR management hook
└── styles/
    └── TournamentQR.css               # QR code styling
```

### Example URLs (Live Tournaments Oct 27 - Nov 2, 2025)

### QR Code Target URLs
```
# Direct tournament play pages (no registration required)
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-27/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-28/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-29/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-30/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-31/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-11-01/play/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-11-02/play/

# Leaderboard pages
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-27/leaderboard/
https://hotelsmates.com/tournaments/hotel-killarney/kids-memory-2025-10-28/leaderboard/
# ... (same pattern for all dates)

# Game play (after entering name/room)
https://hotelsmates.com/game/memory-match/{session_id}
```

### Cloudinary QR Code URLs (Generated)
```
# Live QR code images for Oct 27 - Nov 2, 2025
https://res.cloudinary.com/dg0ssec7u/image/upload/v1761565774/tournament_qr/hotel-killarney_kids-memory-2025-10-27.png
https://res.cloudinary.com/dg0ssec7u/image/upload/v1761565776/tournament_qr/hotel-killarney_kids-memory-2025-10-28.png
https://res.cloudinary.com/dg0ssec7u/image/upload/v1761565777/tournament_qr/hotel-killarney_kids-memory-2025-10-29.png
https://res.cloudinary.com/dg0ssec7u/image/upload/v1761565777/tournament_qr/hotel-killarney_kids-memory-2025-10-30.png
https://res.cloudinary.com/dg0ssec7u/image/upload/v1761565779/tournament_qr/hotel-killarney_kids-memory-2025-10-31.png
https://res.cloudinary.com/dg0ssec7u/image/upload/v1761565779/tournament_qr/hotel-killarney_kids-memory-2025-11-01.png
https://res.cloudinary.com/dg0ssec7u/image/upload/v1761565780/tournament_qr/hotel-killarney_kids-memory-2025-11-02.png
```

## Best Practices

### 1. QR Code Placement
- Hotel lobby displays
- Room service menus  
- Kids club areas
- Pool/recreation areas
- Restaurant table tents

### 2. Tournament Timing
- Daily tournaments: 12 PM - 7 PM
- Weekend specials: Extended hours
- Holiday themes: Special tournaments
- Age groups: Separate tournaments

### 3. Mobile Experience
- Fast loading pages
- Minimal form fields
- Clear instructions
- Instant game start
- Real-time leaderboards

### 4. Analytics & Monitoring
- Track QR code scans
- Monitor conversion rates
- Game completion rates
- Popular time slots
- Device usage stats

## Troubleshooting

### Common Issues
1. **QR Code Not Generating**
   - Check Cloudinary configuration
   - Verify hotel slug exists
   - Ensure tournament has valid data

2. **Mobile Page Not Loading**
   - Verify frontend routes are configured
   - Check API endpoints are accessible
   - Test tournament slug format

3. **Anonymous Players Not Working**
   - Confirm is_anonymous field is set
   - Verify room number validation
   - Check user field is optional

### Debug Commands
```bash
# Test QR generation
python manage.py shell
>>> from entertainment.models import MemoryGameTournament
>>> t = MemoryGameTournament.objects.first()
>>> t.generate_qr_code()

# Check tournament data
>>> t.qr_code_url
>>> t.hotel.slug
>>> t.slug
```

## Security Considerations

- QR codes are public URLs
- No authentication required for tournament access
- Room numbers used for identification only
- Anonymous data stored temporarily
- Leaderboards show first names only

This system provides a seamless, mobile-first tournament experience that requires minimal setup from guests while maintaining hotel branding and engagement tracking capabilities.