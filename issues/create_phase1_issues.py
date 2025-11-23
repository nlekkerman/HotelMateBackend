"""
Create GitHub issues for Phase 1 routing refactor.
"""

import subprocess
import json

# Issue definitions based on hotelmate_phase1_routes_spec.md
issues = [
    {
        "title": "[Phase 1] Add STAFF route namespace wrapper",
        "body": """### Description
Implement new STAFF zone routing that wraps all existing Django apps under `/api/staff/hotels/<hotel_slug>/<app_name>/`

### Spec Reference
From `hotelmate_phase1_routes_spec.md`:
> All current Django apps (rooms, bookings, stock_tracker, etc.) must also be reachable via:
> `/api/staff/hotels/<hotel_slug>/<app_name>/`
> 
> No logic changes inside apps.
> No serializer changes.
> No model changes.
> Just wrap them in a new prefix.

### Requirements
- Create `staff_urls.py` wrapper file at project root
- Include all 16 apps: attendance, bookings, chat, common, entertainment, guests, home, hotel, hotel_info, maintenance, notifications, room_services, rooms, staff, staff_chat, stock_tracker
- NO logic changes inside apps
- NO serializer changes
- NO model changes
- Just wrap existing URLs in new prefix

### Acceptance Criteria
- [ ] `staff_urls.py` created with all app includes
- [ ] All apps accessible via `/api/staff/hotels/<hotel_slug>/<app_name>/`
- [ ] No changes to existing app code
- [ ] URL patterns registered in main `urls.py`
- [ ] Tested that wrapped routes resolve correctly
""",
        "labels": ["phase1", "backend", "routing"]
    },
    {
        "title": "[Phase 1] Add GUEST route namespace with stub endpoints",
        "body": """### Description
Create guest-facing API section with stub JSON endpoints for hotel public pages.

### Spec Reference
From `hotelmate_phase1_routes_spec.md`:
> Create a guest-facing API section with endpoints like:
> - `/api/guest/hotels/<hotel_slug>/site/home/`
> - `/api/guest/hotels/<hotel_slug>/site/rooms/`
> - `/api/guest/hotels/<hotel_slug>/site/offers/`
> 
> In Phase 1 these endpoints can return **stub JSON**.
> Later they will be wired to real hotel data.

### Requirements
- Create `guest_urls.py` at project root
- Implement stub views returning placeholder JSON
- Include endpoints for: home, rooms, offers
- All endpoints should accept `hotel_slug` parameter

### Acceptance Criteria
- [ ] `guest_urls.py` created with stub views
- [ ] `/api/guest/hotels/<hotel_slug>/site/home/` returns stub JSON
- [ ] `/api/guest/hotels/<hotel_slug>/site/rooms/` returns stub JSON
- [ ] `/api/guest/hotels/<hotel_slug>/site/offers/` returns stub JSON
- [ ] URL patterns registered in main `urls.py`
- [ ] Tested that all guest endpoints are accessible
""",
        "labels": ["phase1", "backend", "routing"]
    },
    {
        "title": "[Phase 1] Update main urls.py to include new namespaces",
        "body": """### Description
Register new STAFF and GUEST route namespaces in main `HotelMateBackend/urls.py` while preserving all legacy routes.

### Spec Reference
From `hotelmate_phase1_routes_spec.md`:
> Phase 1 tasks:
> - Add new STAFF route namespace.
> - Add new GUEST route namespace.
> - Keep all current `/api/<app>/` endpoints untouched.
> - Do NOT rewrite existing app URLs.

### Requirements
- Add `path('api/staff/', include('staff_urls'))` to urlpatterns
- Add `path('api/guest/', include('guest_urls'))` to urlpatterns
- Place new routes BEFORE legacy app routes
- Keep all existing `/api/<app>/` routes unchanged

### Acceptance Criteria
- [ ] `staff_urls` included in main urlpatterns
- [ ] `guest_urls` included in main urlpatterns
- [ ] New routes placed before legacy routes
- [ ] All legacy `/api/<app>/` routes still work
- [ ] No existing app URLs modified
- [ ] Server starts without errors
""",
        "labels": ["phase1", "backend", "routing"]
    },
    {
        "title": "[Phase 1] Verify all routing layers coexist without conflicts",
        "body": """### Description
Test and verify that STAFF, GUEST, and LEGACY routing layers all work simultaneously without conflicts.

### Spec Reference
From `hotelmate_phase1_routes_spec.md`:
> Result after Phase 1:
> ```
> /api/staff/hotels/<slug>/rooms/
> /api/staff/hotels/<slug>/bookings/
> /api/staff/hotels/<slug>/stock_tracker/
> /api/staff/hotels/<slug>/attendance/
> 
> + new guest:
> /api/guest/hotels/<slug>/site/home/
> /api/guest/hotels/<slug>/site/rooms/
> 
> /api/<app>/           (legacy but still active)
> ```
> 
> Nothing breaks.

### Requirements
- Test STAFF routes resolve correctly
- Test GUEST routes return stub JSON
- Test LEGACY routes still work unchanged
- Verify no URL conflicts or namespace collisions
- Document any warnings (e.g., namespace uniqueness)

### Acceptance Criteria
- [ ] STAFF routes accessible: `/api/staff/hotels/<slug>/rooms/` etc.
- [ ] GUEST routes accessible: `/api/guest/hotels/<slug>/site/home/` etc.
- [ ] LEGACY routes still work: `/api/rooms/` etc.
- [ ] Server starts successfully
- [ ] No breaking changes to existing functionality
- [ ] All three routing layers coexist
- [ ] Documentation updated with new URL structure
""",
        "labels": ["phase1", "backend", "routing"]
    }
]


def create_issue(issue_data):
    """Create a GitHub issue using gh CLI"""
    title = issue_data["title"]
    body = issue_data["body"]
    labels = issue_data["labels"]
    
    # Build command
    cmd = [
        "gh", "issue", "create",
        "--repo", "nlekkerman/HotelMateBackend",
        "--title", title,
        "--body", body,
        "--assignee", "@me"
    ]
    
    # Add labels individually
    for label in labels:
        cmd.extend(["--label", label])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issue_url = result.stdout.strip()
        print(f"✓ Created: {title}")
        print(f"  URL: {issue_url}\n")
        return {"title": title, "url": issue_url}
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create: {title}")
        print(f"  Error: {e.stderr}\n")
        return None


def main():
    print("Creating GitHub issues for Phase 1 routing refactor...\n")
    print("=" * 70)
    print()
    
    created_issues = []
    
    for issue in issues:
        result = create_issue(issue)
        if result:
            created_issues.append(result)
    
    print("=" * 70)
    print(f"\n✓ Created {len(created_issues)} issues\n")
    
    # Output Markdown list
    print("## Created Issues\n")
    for issue in created_issues:
        # Extract issue number from URL
        issue_num = issue["url"].split("/")[-1]
        print(f"- #{issue_num}: [{issue['title']}]({issue['url']})")


if __name__ == "__main__":
    main()
