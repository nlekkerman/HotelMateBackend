#!/bin/bash
# Script to create all GitHub issues for the refactoring work
# Run from the repository root: bash .github/create_issues.sh

echo "======================================================================"
echo "Creating GitHub Issues for Backend Refactoring"
echo "======================================================================"

# Step 1: Create labels if they don't exist
echo ""
echo "Step 1: Creating labels..."
echo "----------------------------------------------------------------------"

gh label create "refactoring" --description "Code restructuring and optimization" --color "fbca04" --force
gh label create "architecture" --description "System architecture improvements" --color "0e8a16" --force
gh label create "documentation" --description "Documentation improvements" --color "0075ca" --force
gh label create "backend" --description "Backend/API changes" --color "d876e3" --force
gh label create "enhancement" --description "New feature or improvement" --color "a2eeef" --force
gh label create "completed" --description "Work already completed" --color "5319e7" --force
gh label create "epic" --description "Epic issue tracking multiple stories" --color "3E4B9E" --force
gh label create "testing" --description "Test coverage and verification" --color "1d76db" --force
gh label create "configuration" --description "Configuration and setup" --color "c5def5" --force

echo "✅ Labels created successfully"

# Step 2: Create Epic Issue
echo ""
echo "Step 2: Creating Epic Issue..."
echo "----------------------------------------------------------------------"

gh issue create \
  --title "Epic: Backend Code Organization - Views & Serializers Separation" \
  --body-file .github/epic_1.md \
  --label "epic,refactoring,architecture,backend,completed"

echo "✅ Epic created"

# Step 3: Create Issue #2 - View Separation
echo ""
echo "Step 3: Creating Issue #2 - View Separation..."
echo "----------------------------------------------------------------------"

gh issue create \
  --title "Separate Hotel Views into Public, Staff, and Booking Modules" \
  --body-file .github/issue_2.md \
  --label "refactoring,backend,architecture,completed" \
  --assignee nlekkerman

echo "✅ Issue #2 created"

# Step 4: Create Issue #3 - Serializer Separation
echo ""
echo "Step 4: Creating Issue #3 - Serializer Separation..."
echo "----------------------------------------------------------------------"

gh issue create \
  --title "Separate Hotel Serializers into Base, Public, Booking, and Staff Modules" \
  --body-file .github/issue_3.md \
  --label "refactoring,backend,architecture,completed" \
  --assignee nlekkerman

echo "✅ Issue #3 created"

# Step 5: Create Issue #4 - URL Updates
echo ""
echo "Step 5: Creating Issue #4 - URL Configuration..."
echo "----------------------------------------------------------------------"

gh issue create \
  --title "Update All URL Files to Import from Separated Modules" \
  --body-file .github/issue_4.md \
  --label "refactoring,backend,configuration,completed" \
  --assignee nlekkerman

echo "✅ Issue #4 created"

# Step 6: Create Issue #5 - Testing
echo ""
echo "Step 6: Creating Issue #5 - Testing..."
echo "----------------------------------------------------------------------"

gh issue create \
  --title "Add Verification Tests for View and Serializer Separation" \
  --body-file .github/issue_5.md \
  --label "testing,refactoring,backend,completed" \
  --assignee nlekkerman

echo "✅ Issue #5 created"

# Step 7: Create Issue #6 - Documentation
echo ""
echo "Step 7: Creating Issue #6 - Documentation..."
echo "----------------------------------------------------------------------"

gh issue create \
  --title "Create Documentation for View/Serializer Separation Refactoring" \
  --body-file .github/issue_6.md \
  --label "documentation,refactoring,completed" \
  --assignee nlekkerman

echo "✅ Issue #6 created"

echo ""
echo "======================================================================"
echo "✨ All issues created successfully!"
echo "======================================================================"
echo ""
echo "Summary:"
echo "  - 1 Epic issue"
echo "  - 5 Implementation issues"
echo "  - All marked as completed"
echo ""
echo "View issues at: https://github.com/nlekkerman/HotelMateBackend/issues"
echo ""
