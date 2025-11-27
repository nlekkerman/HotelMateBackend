# PowerShell script to create all GitHub issues for the refactoring work
# Run from the repository root: .\.github\create_issues.ps1

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Creating GitHub Issues for Backend Refactoring" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# Step 1: Create labels if they don't exist
Write-Host ""
Write-Host "Step 1: Creating labels..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------"

gh label create "refactoring" --description "Code restructuring and optimization" --color "fbca04" --force
gh label create "architecture" --description "System architecture improvements" --color "0e8a16" --force
gh label create "documentation" --description "Documentation improvements" --color "0075ca" --force
gh label create "backend" --description "Backend/API changes" --color "d876e3" --force
gh label create "enhancement" --description "New feature or improvement" --color "a2eeef" --force
gh label create "completed" --description "Work already completed" --color "5319e7" --force
gh label create "epic" --description "Epic issue tracking multiple stories" --color "3E4B9E" --force
gh label create "testing" --description "Test coverage and verification" --color "1d76db" --force
gh label create "configuration" --description "Configuration and setup" --color "c5def5" --force

Write-Host "✅ Labels created successfully" -ForegroundColor Green

# Step 2: Create Epic Issue
Write-Host ""
Write-Host "Step 2: Creating Epic Issue..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------"

gh issue create `
  --title "Epic: Backend Code Organization - Views & Serializers Separation" `
  --body-file .github/epic_1.md `
  --label "epic,refactoring,architecture,backend,completed"

Write-Host "✅ Epic created" -ForegroundColor Green

# Step 3: Create Issue #2 - View Separation
Write-Host ""
Write-Host "Step 3: Creating Issue #2 - View Separation..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------"

gh issue create `
  --title "Separate Hotel Views into Public, Staff, and Booking Modules" `
  --body-file .github/issue_2.md `
  --label "refactoring,backend,architecture,completed" `
  --assignee nlekkerman

Write-Host "✅ Issue #2 created" -ForegroundColor Green

# Step 4: Create Issue #3 - Serializer Separation
Write-Host ""
Write-Host "Step 4: Creating Issue #3 - Serializer Separation..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------"

gh issue create `
  --title "Separate Hotel Serializers into Base, Public, Booking, and Staff Modules" `
  --body-file .github/issue_3.md `
  --label "refactoring,backend,architecture,completed" `
  --assignee nlekkerman

Write-Host "✅ Issue #3 created" -ForegroundColor Green

# Step 5: Create Issue #4 - URL Updates
Write-Host ""
Write-Host "Step 5: Creating Issue #4 - URL Configuration..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------"

gh issue create `
  --title "Update All URL Files to Import from Separated Modules" `
  --body-file .github/issue_4.md `
  --label "refactoring,backend,configuration,completed" `
  --assignee nlekkerman

Write-Host "✅ Issue #4 created" -ForegroundColor Green

# Step 6: Create Issue #5 - Testing
Write-Host ""
Write-Host "Step 6: Creating Issue #5 - Testing..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------"

gh issue create `
  --title "Add Verification Tests for View and Serializer Separation" `
  --body-file .github/issue_5.md `
  --label "testing,refactoring,backend,completed" `
  --assignee nlekkerman

Write-Host "✅ Issue #5 created" -ForegroundColor Green

# Step 7: Create Issue #6 - Documentation
Write-Host ""
Write-Host "Step 7: Creating Issue #6 - Documentation..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------"

gh issue create `
  --title "Create Documentation for View/Serializer Separation Refactoring" `
  --body-file .github/issue_6.md `
  --label "documentation,refactoring,completed" `
  --assignee nlekkerman

Write-Host "✅ Issue #6 created" -ForegroundColor Green

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "✨ All issues created successfully!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:"
Write-Host "  - 1 Epic issue"
Write-Host "  - 5 Implementation issues"
Write-Host "  - All marked as completed"
Write-Host ""
Write-Host "View issues at: https://github.com/nlekkerman/HotelMateBackend/issues" -ForegroundColor Blue
Write-Host ""
