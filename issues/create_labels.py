"""
Script to create GitHub labels and issues for Phase 1 routing refactor.
Uses gh CLI to create labels.
"""

import subprocess
import sys

# Labels to create
labels = [
    {
        "name": "phase1",
        "description": "Phase 1 routing refactor tasks",
        "color": "0E8A16"  # Green
    },
    {
        "name": "backend",
        "description": "Backend/server-side work",
        "color": "1D76DB"  # Blue
    },
    {
        "name": "routing",
        "description": "URL routing and API structure",
        "color": "FBCA04"  # Yellow
    }
]

def create_label(name, description, color):
    """Create a GitHub label using gh CLI"""
    cmd = [
        "gh", "label", "create", name,
        "--description", description,
        "--color", color,
        "--repo", "nlekkerman/HotelMateBackend"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Created label: {name}")
        else:
            # Label might already exist
            if "already exists" in result.stderr:
                print(f"→ Label already exists: {name}")
            else:
                print(f"✗ Error creating label {name}: {result.stderr}")
    except Exception as e:
        print(f"✗ Failed to create label {name}: {e}")

def main():
    print("Creating GitHub labels for Phase 1...\n")
    
    for label in labels:
        create_label(label["name"], label["description"], label["color"])
    
    print("\n✓ Label setup complete!")

if __name__ == "__main__":
    main()
