"""
Script to create GitHub labels for Public Hotel API implementation.
Uses gh CLI to create labels.
"""

import subprocess

# Labels to create for public hotel API project
labels = [
    {
        "name": "hotel-public-api",
        "description": "Public hotel page API and booking logic",
        "color": "FF6B6B"  # Red/Pink
    },
    {
        "name": "model",
        "description": "Django model changes",
        "color": "5319E7"  # Purple
    },
    {
        "name": "serializer",
        "description": "DRF serializer changes",
        "color": "1D76DB"  # Blue
    },
    {
        "name": "api",
        "description": "API endpoint implementation",
        "color": "0E8A16"  # Green
    },
    {
        "name": "admin",
        "description": "Django admin interface",
        "color": "F9D0C4"  # Light Pink
    },
    {
        "name": "tests",
        "description": "Test coverage and quality",
        "color": "FBCA04"  # Yellow
    },
    {
        "name": "migration",
        "description": "Database migrations",
        "color": "BFD4F2"  # Light Blue
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
    print("Creating GitHub labels for Public Hotel API...\n")
    print("=" * 60)
    print()
    
    for label in labels:
        create_label(label["name"], label["description"], label["color"])
    
    print()
    print("=" * 60)
    print("\n✓ Label setup complete!")

if __name__ == "__main__":
    main()
