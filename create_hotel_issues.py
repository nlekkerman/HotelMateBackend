"""
Create GitHub issues for Hotel model extensions and assign to project.
"""

import subprocess
import json


issues = [
    {
        "title": "Extend Hotel model for multi-portal support",
        "body": """### Description
Add new fields and helper properties to Hotel model to support multi-portal architecture.

### Requirements
- Add new fields to Hotel model:
  - `is_active` (BooleanField)
  - `sort_order` (IntegerField)
  - `city` (CharField)
  - `country` (CharField)
  - `short_description` (TextField)

- Add helper URL properties:
  - `guest_base_path` - Returns `/api/guest/hotels/{slug}/`
  - `staff_base_path` - Returns `/api/staff/hotels/{slug}/`
  - `full_guest_url` - Returns complete guest portal URL
  - `full_staff_url` - Returns complete staff portal URL

### Acceptance Criteria
- [ ] Fields added with proper migrations
- [ ] Admin interface updated to show new fields
- [ ] Helper URL properties implemented and tested
- [ ] No breaking changes to existing functionality
- [ ] Documentation updated
""",
        "labels": ["phase1", "backend", "hotel", "config"]
    },
    {
        "title": "Create HotelAccessConfig model",
        "body": """### Description
Create a new HotelAccessConfig model with OneToOne relationship to Hotel for managing portal access settings.

### Requirements
Create HotelAccessConfig model with fields:
- `hotel` (OneToOneField to Hotel)
- `guest_portal_enabled` (BooleanField, default=True)
- `staff_portal_enabled` (BooleanField, default=True)
- `requires_room_pin` (BooleanField, default=False)
- `room_pin_length` (IntegerField, default=4)
- `rotate_pin_on_checkout` (BooleanField, default=True)
- `allow_multiple_guest_sessions` (BooleanField, default=True)
- `max_active_guest_devices_per_room` (IntegerField, default=5)

### Acceptance Criteria
- [ ] Model created with OneToOne relationship to Hotel
- [ ] Migration created and applied
- [ ] Admin interface allows editing config
- [ ] Default values match specification
- [ ] Signal created to auto-create config for new hotels
- [ ] Existing hotels have config created via data migration
""",
        "labels": ["phase1", "backend", "hotel", "config"]
    },
    {
        "title": "Expose hotel and portal config through API",
        "body": """### Description
Create API endpoint to expose hotel information and portal configuration for client applications.

### Requirements
Create API endpoint that returns:
- Hotel information:
  - `id`, `name`, `slug`
  - `city`, `country`
  - `short_description`
  - `logo` (URL)
- URL helpers:
  - `guest_base_path`
  - `staff_base_path`
- Portal configuration:
  - `guest_portal_enabled`
  - `staff_portal_enabled`

### Acceptance Criteria
- [ ] Only active hotels (`is_active=True`) are returned
- [ ] Branding information (logo, description) included
- [ ] URL helpers return correct paths
- [ ] Portal enabled flags from HotelAccessConfig included
- [ ] Endpoint smoke-tested with sample data
- [ ] Proper error handling for missing config
- [ ] Response format documented
""",
        "labels": ["phase1", "backend", "hotel", "config"]
    },
    {
        "title": "Add development seed data for hotels",
        "body": """### Description
Create management command or fixture to populate database with sample hotel data for development/testing.

### Requirements
- Create Django management command: `python manage.py seed_hotels`
- Generate sample hotels with:
  - Different cities/countries
  - Varied sort_order for display testing
  - Sample logos and descriptions
  - Associated HotelAccessConfig for each hotel

### Acceptance Criteria
- [ ] Command runs successfully on clean database
- [ ] Creates at least 3-5 sample hotels
- [ ] Sort order visible and functional on main listing
- [ ] All hotels have associated access_config
- [ ] Sample data is realistic and useful for testing
- [ ] Command is idempotent (can run multiple times safely)
- [ ] Documentation added to README or docs
""",
        "labels": ["phase1", "backend", "hotel", "config"]
    }
]


def create_issue(issue_data):
    """Create a GitHub issue using gh CLI"""
    title = issue_data["title"]
    body = issue_data["body"]
    labels = issue_data["labels"]
    
    cmd = [
        "gh", "issue", "create",
        "--repo", "nlekkerman/HotelMateBackend",
        "--title", title,
        "--body", body,
        "--assignee", "@me"
    ]
    
    for label in labels:
        cmd.extend(["--label", label])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issue_url = result.stdout.strip()
        issue_num = issue_url.split("/")[-1]
        print(f"✓ Created: {title}")
        print(f"  URL: {issue_url}\n")
        return {"title": title, "url": issue_url, "number": issue_num}
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create: {title}")
        print(f"  Error: {e.stderr}\n")
        return None


def get_project_id():
    """Get the project ID for '@nlekkerman's hotelsmates project phase one'"""
    cmd = [
        "gh", "project", "list",
        "--owner", "nlekkerman",
        "--format", "json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        projects = json.loads(result.stdout)
        
        for project in projects.get("projects", []):
            if "hotelsmates project phase one" in project.get("title", "").lower():
                project_number = project.get("number")
                print(f"✓ Found project: {project.get('title')}")
                print(f"  Project number: {project_number}\n")
                return project_number
        
        print("⚠ Could not find project 'hotelsmates project phase one'")
        return None
    except Exception as e:
        print(f"⚠ Error finding project: {e}")
        return None


def add_issue_to_project(issue_number, project_number):
    """Add issue to GitHub Project"""
    cmd = [
        "gh", "project", "item-add", str(project_number),
        "--owner", "nlekkerman",
        "--url", f"https://github.com/nlekkerman/HotelMateBackend/issues/{issue_number}"
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  ✓ Added issue #{issue_number} to project")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to add issue #{issue_number} to project: {e.stderr}")
        return False


def main():
    print("Creating GitHub issues for Hotel model extensions...\n")
    print("=" * 70)
    print()
    
    # Get project ID
    project_number = get_project_id()
    
    created_issues = []
    
    for issue in issues:
        result = create_issue(issue)
        if result:
            created_issues.append(result)
            
            # Add to project if found
            if project_number:
                add_issue_to_project(result["number"], project_number)
                print()
    
    print("=" * 70)
    print(f"\n✓ Created {len(created_issues)} issues\n")
    
    # Output Markdown list
    print("## Created Issues\n")
    for issue in created_issues:
        print(f"- #{issue['number']}: [{issue['title']}]({issue['url']})")
    
    # Mark first issue as in progress
    if created_issues:
        first_issue = created_issues[0]['number']
        print(f"\n\nMarking issue #{first_issue} as 'In Progress'...")
        
        cmd = [
            "gh", "issue", "edit", first_issue,
            "--repo", "nlekkerman/HotelMateBackend",
            "--add-label", "in-progress"
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✓ Issue #{first_issue} marked as 'In Progress'")
        except Exception as e:
            print(f"⚠ Could not mark as in progress: {e}")


if __name__ == "__main__":
    main()
