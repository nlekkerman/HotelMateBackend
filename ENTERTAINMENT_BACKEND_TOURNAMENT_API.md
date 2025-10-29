# Entertainment App — Backend API guidance for "Previous Tournament" and Full Results

This document is backend-focused guidance for the frontend team to reliably fetch the last finished (previous) tournament, its prizes, and the full set of results (not only winners). It includes recommended endpoints, Django view snippets, pagination and ranking suggestions, DB indexing recommendations, and curl examples.

Place this file next to `manage.py` for backend developer reference.

## Goals
- Provide a compact summary endpoint the frontend can call to find the last finished tournament for a hotel.
- Provide a paginated endpoint that returns *all* results for a given tournament ordered by score (desc) and time (asc), and optionally include a rank for each entry.
- Make the endpoints efficient for large datasets (indexes, pagination, DB-side ranking where possible).

## Existing endpoints (from current codebase)
- `GET /entertainment/tournaments/summary/?hotel={hotel_slug}` — returns `{ active, next, previous }`. `previous` contains `{ id, name, end_date }`.
- `GET /entertainment/tournaments/{id}/leaderboard/?limit={n}` — returns top `n` leaderboard entries (view's current implementation slices by limit).
- `GET /entertainment/memory-sessions/?tournament={id}` — can be used to list sessions filtered by tournament (may be paginated depending on project settings).
- `GET /entertainment/tournaments/{id}/` — returns full tournament detail, includes `first_prize`, `second_prize`, `third_prize` fields in `MemoryGameTournamentSerializer`.

These are sufficient for many frontends, but the `leaderboard` view returns only the top N entries. If the frontend needs *all* results (or all results ordered by score), prefer the approach below.

---

## Recommended API (backend changes)
Add a dedicated, paginated, server-side-ordered endpoint to return tournament results with optional rank calculation. Two options:

A) Add a `results` action to `MemoryGameTournamentViewSet` that returns a paginated list ordered by `-score, time_seconds` and supports `page`/`limit` (DRF pagination).

B) Enhance `memory-sessions` list view to accept ordering and `tournament` filter and ensure pagination is enabled. This re-uses the `MemoryGameSessionSerializer` and avoids duplicating code.

I recommend option A for a single, stable contract dedicated to tournament results.

Example view snippet to add to `entertainment/views.py` inside `MemoryGameTournamentViewSet`:

```python
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import TournamentLeaderboardSerializer, MemoryGameSessionSerializer

    @action(detail=True, methods=['get'], url_path='results')
    def results(self, request, pk=None):
        """Return paginated tournament results ordered by score desc, time asc.

        Query params:
        - limit (optional): number of items per page (DRF pagination preferred)
        - page (optional): page number (if using page-number pagination)
        """
        tournament = self.get_object()

        qs = MemoryGameSession.objects.filter(
            tournament=tournament,
            completed=True
        ).order_by('-score', 'time_seconds')

        # If your ViewSet has DRF pagination configured, use it
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = TournamentLeaderboardSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback: no pagination
        serializer = TournamentLeaderboardSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
```

Notes:
- Use `TournamentLeaderboardSerializer` if it returns the desired fields (it maps fields like `participant_name`, `score`, `time_seconds`, `moves_count`, etc.). If you prefer raw session fields, use `MemoryGameSessionSerializer`.
- Keep `permission_classes=[permissions.AllowAny]` (as already used) if this data should be public.

---

## Rank calculation (server-side recommendations)

If you want to return a `rank` with each row, you have two main approaches:

1) Database window functions (recommended for Postgres): compute rank in SQL and return it with each row. It's fast and scales well.
   - Example raw SQL (Postgres):

```sql
SELECT
  id AS session_id,
  player_name,
  room_number,
  score,
  time_seconds,
  moves_count,
  created_at,
  RANK() OVER (ORDER BY score DESC, time_seconds ASC) AS rank
FROM entertainment_memorygamesession
WHERE tournament_id = %s AND completed = true
ORDER BY score DESC, time_seconds ASC
LIMIT %s OFFSET %s;
```

   - You can expose this via a DRF view by using `raw()` or a custom manager, or by using Django ORM Window expressions if your Django version supports it. Example (Django ORM, Postgres):

```python
from django.db.models import F, Window
from django.db.models.functions import Rank

qs = MemoryGameSession.objects.filter(tournament=tournament, completed=True).annotate(
    rank=Window(expression=Rank(), order_by=[F('-score'), F('time_seconds')])
).order_by('-score', 'time_seconds')
```

   - Note: `Window` and `Rank` require a Django version that supports window expressions and a DB that implements them (Postgres does).

2) Lightweight server-side ranking for the top-N: if you only need ranks for the top 50 or so, compute ranks by fetching the top slice ordered by score/time and compute rank in Python (cheap for small slices).

3) Client-side ranking: fetch ordered pages and compute rank as index + offset. This is valid when rows are strictly ordered and there are no ties needing dense rank handling.

---

## Pagination
- Use DRF pagination (PageNumberPagination or LimitOffsetPagination). Page sizes should be reasonable (20/50/100). Provide `limit` parameter if you use LimitOffsetPagination.
- When implementing the `results` action, support DRF pagination by calling `self.paginate_queryset(qs)` and `self.get_paginated_response(serializer.data)` as in the example.
- Return unambiguous JSON shape for paginated responses: `{ count, next, previous, results: [...] }`.

Frontend notes for pagination: the frontend should follow `next` links to load more pages, or request a larger limit for full exports (but be mindful of size).

---

## Indexing / Performance
For large tournaments, make sure the database has appropriate indexes. Recommended indexes (Postgres example):

- Index to support leaderboard ordering and filtering:

```sql
CREATE INDEX CONCURRENTLY idx_memsession_tournament_completed_score_time
ON entertainment_memorygamesession (tournament_id, completed, score DESC, time_seconds ASC);
```

- Index to support queries by tournament and created date (if you often list by created_at):

```sql
CREATE INDEX CONCURRENTLY idx_memsession_tournament_created_at
ON entertainment_memorygamesession (tournament_id, created_at DESC);
```

If you prefer to add indexes via Django migrations, add a migration that runs the SQL with `RunSQL` or add `indexes` to the `MemoryGameSession` model (note: Django's `models.Index` doesn't accept DESC in `fields` across all DBs; for DESC index you may need `django.contrib.postgres.indexes` or `RunSQL`).

Also ensure foreign keys (e.g. `tournament_id`) are indexed by default (Django usually creates this index on FK columns).

---

## Sample Django migration snippet (RunSQL) to add Postgres index

```python
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('entertainment', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memsession_tournament_completed_score_time
            ON entertainment_memorygamesession (tournament_id, completed, score DESC, time_seconds ASC);
            """,
            reverse_sql="DROP INDEX CONCURRENTLY IF EXISTS idx_memsession_tournament_completed_score_time;"
        ),
    ]
```

Note: Use `CONCURRENTLY` on production Postgres to avoid locking writes. If your DB isn't Postgres, adapt index syntax appropriately.

---

## API examples (curl)

Get summary (to find the last finished tournament for a hotel):

```bash
curl -s "http://localhost:8000/entertainment/tournaments/summary/?hotel=my-hotel-slug"
```

Get tournament detail (includes prizes):

```bash
curl -s "http://localhost:8000/entertainment/tournaments/123/"
```

Get top leaderboard entries (existing endpoint):

```bash
curl -s "http://localhost:8000/entertainment/tournaments/123/leaderboard/?limit=20"
```

Get paginated full results (recommended new endpoint):

```bash
curl -s "http://localhost:8000/entertainment/tournaments/123/results/?page=1&limit=50"
```

Or use the `memory-sessions` listing endpoint (if you prefer):

```bash
curl -s "http://localhost:8000/entertainment/memory-sessions/?tournament=123&page=1&limit=100"
```

---

## Response shapes (recommended)
- `GET /entertainment/tournaments/summary/` (existing):

```json
{
  "active": null,
  "next": null,
  "previous": { "id": 123, "name": "...", "end_date": "..." }
}
```

- `GET /entertainment/tournaments/{id}/results/` (recommended paginated):

```json
{
  "count": 1234,
  "next": "http://.../results/?page=2",
  "previous": null,
  "results": [
    { "session_id": 1, "player_name": "Alice", "room_number": "101", "score": 980, "time_seconds": 40, "moves_count": 14, "created_at": "...", "rank": 1 },
    ...
  ]
}
```

If you can't compute `rank` server-side, omit `rank` and let the frontend compute `rank` as `offset + index + 1` (ties may need DB-side handling).

---

## Small implementation checklist for backend devs
1. Add `results` action to `MemoryGameTournamentViewSet` returning a paginated queryset ordered by `-score, time_seconds`.
2. Ensure DRF pagination is enabled and documented (page size, limit parameter if using LimitOffsetPagination).
3. Add DB index(es) for tournament/score/time performance.
4. (Optional) Implement server-side rank using DB window functions (Postgres) or return `rank` via raw SQL/annotate.
5. Add tests: endpoint returns correct ordering, pagination works, and `previous` from `summary` corresponds to the most recently completed tournament.

---

## Security and other notes
- Data is currently `AllowAny` for summary and leaderboard — review if you need authentication for some fields.
- Consider rate-limiting or caching expensive leaderboard/large-results requests.

---

If you'd like, I can now:
- Create the exact `results` action code and open a small PR-style patch against `entertainment/views.py` (include tests), or
- Create the migration that adds the recommended index.

Tell me which backend change you want me to implement next and I will prepare the code.
