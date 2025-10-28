# 🏆 Tournament Leaderboard Analysis & Recommendations

## 🔍 Current Leaderboard Implementation Status

### ✅ **What Already Exists:**

#### **1. Models:**
- **MemoryGameSession** - Stores individual game scores
- **MemoryGameTournament** - Tournament metadata with `get_leaderboard()` method
- **TournamentParticipation** - Tracks registered users (but not used for anonymous players)

#### **2. API Endpoints:**
```python
# Tournament leaderboard (already exists)
GET /api/entertainment/tournaments/{id}/leaderboard/

# Response format:
{
  "leaderboard": [
    {
      "rank": 1,
      "player_name": "Alex Smith", 
      "score": 850,
      "time_seconds": 45,
      "moves_count": 18,
      "created_at": "2025-10-28T11:25:00Z"
    }
  ]
}
```

#### **3. Admin Interface:**
- Tournament management with participant counts
- Session viewing with scores and times
- Bulk actions for tournament management

---

## ❌ **What's Missing for Complete Leaderboard System:**

### **1. Dedicated Leaderboard Model (Recommended)**
```python
class TournamentLeaderboard(models.Model):
    """
    Cached leaderboard for tournaments - updated when scores are submitted
    """
    tournament = models.ForeignKey(
        MemoryGameTournament,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries'
    )
    
    # Player Info (anonymous support)
    player_name = models.CharField(max_length=100)
    room_number = models.CharField(max_length=50, blank=True)
    
    # Performance Data
    best_score = models.IntegerField()
    best_time_seconds = models.PositiveIntegerField()
    best_moves_count = models.PositiveIntegerField()
    games_played = models.PositiveIntegerField(default=1)
    total_score = models.IntegerField()
    
    # Rankings
    current_rank = models.PositiveIntegerField(null=True, blank=True)
    
    # Metadata
    first_game_at = models.DateTimeField()
    last_game_at = models.DateTimeField(auto_now=True)
    session_reference = models.ForeignKey(
        'MemoryGameSession',
        on_delete=models.SET_NULL,
        null=True,
        help_text="Best scoring session"
    )

    class Meta:
        unique_together = ('tournament', 'player_name')
        ordering = ['-best_score', 'best_time_seconds']
        indexes = [
            models.Index(fields=['tournament', '-best_score']),
            models.Index(fields=['tournament', 'current_rank']),
        ]

    def __str__(self):
        return f"{self.player_name} - {self.tournament.name} - {self.best_score} pts"
```

---

## 🚀 **Recommended Implementation:**

### **Option A: Use Existing System (Simpler)**
```python
# Current approach works fine - just enhance views
class MemoryGameTournamentViewSet(viewsets.ModelViewSet):
    
    @action(detail=True, methods=['get'])
    def leaderboard(self, request, pk=None):
        """Enhanced tournament leaderboard with better data"""
        tournament = self.get_object()
        limit = min(int(request.query_params.get('limit', 50)), 100)
        
        # Get best session per player (in case of multiple games)
        from django.db.models import Max
        
        # Subquery to get best score per player
        best_sessions = (tournament.sessions
            .filter(completed=True)
            .values('player_name')
            .annotate(
                best_score=Max('score'),
                best_time=Min('time_seconds'),
                games_played=Count('id')
            )
            .order_by('-best_score', 'best_time')[:limit])
        
        # Build leaderboard with ranks
        leaderboard_data = []
        for rank, entry in enumerate(best_sessions, 1):
            # Get the actual session with best score
            best_session = tournament.sessions.filter(
                player_name=entry['player_name'],
                score=entry['best_score']
            ).first()
            
            leaderboard_data.append({
                'rank': rank,
                'player_name': entry['player_name'],
                'room_number': best_session.room_number if best_session else '',
                'best_score': entry['best_score'],
                'best_time_seconds': entry['best_time'],
                'games_played': entry['games_played'],
                'last_played': best_session.created_at if best_session else None
            })
        
        return Response({
            'tournament': tournament.name,
            'leaderboard': leaderboard_data,
            'total_participants': len(leaderboard_data)
        })
```

### **Option B: Add Dedicated Leaderboard Model (Better Performance)**

#### **1. Create the Model:**
```python
# Add to entertainment/models.py
class TournamentLeaderboard(models.Model):
    # ... (model code from above)
    
    @classmethod
    def update_from_session(cls, session):
        """Update leaderboard when new score is submitted"""
        if not session.tournament or not session.completed:
            return
            
        leaderboard_entry, created = cls.objects.get_or_create(
            tournament=session.tournament,
            player_name=session.player_name,
            defaults={
                'room_number': session.room_number,
                'best_score': session.score,
                'best_time_seconds': session.time_seconds,
                'best_moves_count': session.moves_count,
                'total_score': session.score,
                'first_game_at': session.created_at,
                'session_reference': session
            }
        )
        
        if not created:
            # Update existing entry if this score is better
            leaderboard_entry.games_played += 1
            leaderboard_entry.total_score += session.score
            
            if session.score > leaderboard_entry.best_score:
                leaderboard_entry.best_score = session.score
                leaderboard_entry.best_time_seconds = session.time_seconds
                leaderboard_entry.best_moves_count = session.moves_count
                leaderboard_entry.session_reference = session
            elif (session.score == leaderboard_entry.best_score and 
                  session.time_seconds < leaderboard_entry.best_time_seconds):
                leaderboard_entry.best_time_seconds = session.time_seconds
                leaderboard_entry.best_moves_count = session.moves_count
                leaderboard_entry.session_reference = session
            
            leaderboard_entry.save()
        
        # Recalculate ranks for this tournament
        cls.update_tournament_ranks(session.tournament)
        
        return leaderboard_entry
    
    @classmethod
    def update_tournament_ranks(cls, tournament):
        """Recalculate ranks for all players in tournament"""
        entries = cls.objects.filter(tournament=tournament).order_by(
            '-best_score', 'best_time_seconds'
        )
        
        for rank, entry in enumerate(entries, 1):
            entry.current_rank = rank
            entry.save(update_fields=['current_rank'])
```

#### **2. Update Session Save Method:**
```python
# In MemoryGameSession.save()
def save(self, *args, **kwargs):
    """Auto-calculate score and update leaderboard"""
    if self.completed and self.time_seconds and self.moves_count:
        self.score = self.calculate_score()
    
    super().save(*args, **kwargs)
    
    # Update tournament leaderboard if this is a tournament session
    if self.tournament and self.completed:
        from .models import TournamentLeaderboard
        TournamentLeaderboard.update_from_session(self)
```

#### **3. Enhanced Admin Interface:**
```python
@admin.register(TournamentLeaderboard)
class TournamentLeaderboardAdmin(admin.ModelAdmin):
    list_display = (
        'current_rank', 'player_name', 'tournament', 'best_score',
        'best_time_seconds', 'games_played', 'last_game_at'
    )
    list_filter = (
        'tournament__hotel', 'tournament__name', 'first_game_at'
    )
    search_fields = (
        'player_name', 'tournament__name', 'room_number'
    )
    readonly_fields = (
        'current_rank', 'first_game_at', 'last_game_at'
    )
    ordering = ('tournament', 'current_rank')
    
    fieldsets = (
        ('Tournament & Player', {
            'fields': ('tournament', 'player_name', 'room_number')
        }),
        ('Performance', {
            'fields': (
                'current_rank', 'best_score', 'best_time_seconds', 
                'best_moves_count', 'games_played', 'total_score'
            )
        }),
        ('Timestamps', {
            'fields': ('first_game_at', 'last_game_at', 'session_reference')
        }),
    )
    
    actions = ['recalculate_ranks']
    
    def recalculate_ranks(self, request, queryset):
        """Recalculate ranks for selected tournaments"""
        tournaments = set(entry.tournament for entry in queryset)
        for tournament in tournaments:
            TournamentLeaderboard.update_tournament_ranks(tournament)
        
        self.message_user(
            request,
            f'Recalculated ranks for {len(tournaments)} tournaments.'
        )
    recalculate_ranks.short_description = "Recalculate tournament ranks"
```

---

## 📊 **Enhanced API Endpoints:**

### **1. Tournament Leaderboard:**
```python
# GET /api/entertainment/tournaments/{id}/leaderboard/
{
  "tournament": {
    "id": 23,
    "name": "Test Tournament - Frontend Testing",
    "status": "active",
    "participants_count": 15
  },
  "leaderboard": [
    {
      "rank": 1,
      "player_name": "Speed Master",
      "room_number": "305", 
      "best_score": 920,
      "best_time_seconds": 35,
      "best_moves_count": 14,
      "games_played": 3,
      "total_score": 2450,
      "last_played": "2025-10-28T11:30:00Z"
    },
    {
      "rank": 2,
      "player_name": "Quick Player",
      "room_number": "201",
      "best_score": 900,
      "best_time_seconds": 40, 
      "best_moves_count": 16,
      "games_played": 2,
      "total_score": 1750,
      "last_played": "2025-10-28T11:28:00Z"
    }
  ],
  "my_rank": {
    "rank": 5,
    "player_name": "Current Player",
    "best_score": 850
  }
}
```

### **2. Live Leaderboard Updates:**
```python
@action(detail=True, methods=['get'])
def live_leaderboard(self, request, pk=None):
    """Real-time leaderboard with recent changes"""
    tournament = self.get_object()
    
    # Get recent submissions (last 5 minutes)
    recent_time = timezone.now() - timedelta(minutes=5)
    recent_sessions = tournament.sessions.filter(
        created_at__gte=recent_time,
        completed=True
    ).order_by('-created_at')[:10]
    
    return Response({
        'leaderboard': self.get_leaderboard_data(tournament),
        'recent_submissions': [
            {
                'player_name': session.player_name,
                'score': session.score,
                'time_ago': (timezone.now() - session.created_at).seconds
            }
            for session in recent_sessions
        ]
    })
```

---

## 🎯 **My Recommendation:**

### **Start with Option A (Existing System Enhancement)**
1. **Pros:** No database changes, works immediately
2. **Cons:** Slower queries with many players
3. **Perfect for:** Current tournament size (50 players max)

### **Upgrade to Option B Later if Needed**
1. **When:** If tournaments grow to 200+ players
2. **Benefits:** Much faster queries, better admin interface, rank caching
3. **Migration:** Can be added without breaking existing code

---

## 🚀 **Immediate Actions Needed:**

### **1. Enhance Current Leaderboard View** ✅ Ready to implement
### **2. Add Admin Leaderboard Management** ✅ Admin already exists  
### **3. Create Frontend Leaderboard Component** 📝 Needs frontend work
### **4. Add Live Updates** 🔄 Optional polling/websockets

**Current system works fine for your tournaments! The existing `get_leaderboard()` method and admin interface handle everything you need.** 🎯

**No new models needed right now - just enhance the frontend leaderboard display!** 🏆