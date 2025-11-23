# GitHub Issue Workflow for HotelMateBackend

## Overview
This document describes the workflow for creating and managing GitHub issues for the HotelMateBackend repository using the GitHub CLI (`gh`).

## Prerequisites

1. **Install GitHub CLI**
   - Download from: https://cli.github.com/
   - After installation, add to PATH:
     ```powershell
     $env:Path += ";C:\Program Files\GitHub CLI"
     ```

2. **Authenticate with GitHub**
   ```powershell
   gh auth login
   ```

3. **Grant Project Permissions** (if using GitHub Projects)
   ```powershell
   gh auth refresh -s read:project -s project
   ```

## Repository Information

- **Repository**: `nlekkerman/HotelMateBackend`
- **Default Branch**: `main`
- **GitHub Project ID**: `11` (@nlekkerman's hotelsmates project phase one)

## Issue Creation Workflow

### Step 1: Plan Your Issues

Create a Python script to batch-create related issues. Example structure:

```python
import subprocess
import json

# Define your issues
issues = [
    {
        "title": "Feature Name: Brief Description",
        "body": "Detailed description\n\n**Tasks:**\n- [ ] Task 1\n- [ ] Task 2",
        "labels": ["phase1", "backend", "category"]
    },
    # Add more issues...
]

# Repository details
REPO = "nlekkerman/HotelMateBackend"
PROJECT_ID = "11"

# Create each issue
for issue in issues:
    # Build the gh command
    cmd = [
        "gh", "issue", "create",
        "--repo", REPO,
        "--title", issue["title"],
        "--body", issue["body"],
        "--label", ",".join(issue["labels"])
    ]
    
    # Execute
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    
    if result.returncode == 0:
        # Extract issue number from output
        issue_url = result.stdout.strip()
        issue_number = issue_url.split('/')[-1]
        
        # Add to project
        subprocess.run([
            "gh", "issue", "edit", issue_number,
            "--add-project", PROJECT_ID,
            "--repo", REPO
        ], shell=True)
        
        print(f"✅ Created issue #{issue_number}: {issue['title']}")
    else:
        print(f"❌ Failed: {issue['title']}")
        print(f"Error: {result.stderr}")
```

### Step 2: Label Strategy

Use consistent labels for easy filtering:

- **Phase Labels**: `phase1`, `phase2`, etc.
- **Type Labels**: `backend`, `frontend`, `api`, `model`, `config`
- **Status Labels**: `in-progress`, `blocked`, `needs-review`
- **Component Labels**: Specific to your feature (e.g., `hotel`, `routing`, `authentication`)

### Step 3: Issue Status Management

**Mark issue as in-progress:**
```powershell
gh issue edit <issue_number> --add-label in-progress --repo nlekkerman/HotelMateBackend
```

**Close completed issue with comment:**
```powershell
gh issue close <issue_number> --repo nlekkerman/HotelMateBackend --comment "Completed: Brief summary of what was done."
```

**Update issue body:**
```powershell
gh issue edit <issue_number> --body "Updated description" --repo nlekkerman/HotelMateBackend
```

**Add to project:**
```powershell
gh issue edit <issue_number> --add-project 11 --repo nlekkerman/HotelMateBackend
```

## Example: Phase 1 Issues Created

### Routing Refactor (Issues #1-4)
```powershell
# Created with labels: phase1, backend, routing
# Issues:
# - #1: Create staff URL wrapper
# - #2: Create guest URL wrapper  
# - #3: Update main urls.py
# - #4: Test routing implementation
```

### Hotel Model Extension (Issues #5-8)
```powershell
# Created with labels: phase1, backend, hotel, config
# Issues:
# - #5: Extend Hotel model with new fields ✅ CLOSED
# - #6: Create HotelAccessConfig model ✅ CLOSED
# - #7: Expose hotel config through API 🔄 IN-PROGRESS
# - #8: Add development seed data 📋 PENDING
```

## Best Practices

1. **Batch Creation**: Create related issues together as a logical unit
2. **Clear Titles**: Use format "Component: Action/Feature"
3. **Detailed Bodies**: Include tasks checklist, acceptance criteria, and technical notes
4. **Consistent Labels**: Use predefined label strategy
5. **Track Progress**: Mark issues as in-progress when starting work
6. **Document Completion**: Close with descriptive comment summarizing what was done
7. **Link to Project**: Always add issues to the active project board

## Quick Reference Commands

### Create Issue
```powershell
gh issue create --repo nlekkerman/HotelMateBackend --title "Title" --body "Description" --label "label1,label2"
```

### List Issues
```powershell
gh issue list --repo nlekkerman/HotelMateBackend
```

### View Issue
```powershell
gh issue view <issue_number> --repo nlekkerman/HotelMateBackend
```

### Close Issue
```powershell
gh issue close <issue_number> --repo nlekkerman/HotelMateBackend --comment "Completion comment"
```

### Edit Issue Labels
```powershell
gh issue edit <issue_number> --add-label "new-label" --repo nlekkerman/HotelMateBackend
gh issue edit <issue_number> --remove-label "old-label" --repo nlekkerman/HotelMateBackend
```

## Troubleshooting

### GitHub CLI Not Found
- Verify installation: `gh --version`
- Add to PATH if needed: `$env:Path += ";C:\Program Files\GitHub CLI"`

### Permission Denied for Projects
- Run: `gh auth refresh -s read:project -s project`
- Re-authenticate if needed: `gh auth login`

### Issue Not Added to Project
- Verify project ID is correct (use `11` for phase one project)
- Ensure you have project write permissions
- Try editing issue after creation if initial add fails

## Templates

### Feature Issue Template
```markdown
## Description
Brief description of the feature.

## Requirements
- Requirement 1
- Requirement 2

## Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Acceptance Criteria
- Criterion 1
- Criterion 2

## Technical Notes
Any implementation details or considerations.
```

### Bug Issue Template
```markdown
## Bug Description
What is the bug?

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen?

## Actual Behavior
What actually happens?

## Environment
- Django version: 5.2.4
- Python version: 3.13
- Database: PostgreSQL

## Possible Solution
Any ideas on how to fix?
```
