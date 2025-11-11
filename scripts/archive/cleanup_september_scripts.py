"""
Clean up temporary September stocktake scripts.
This removes all the check, populate, fix, and analysis scripts we created.
"""
import os
import glob

# Root directory
root = os.path.dirname(os.path.abspath(__file__))

# Patterns to match
patterns = [
    'add_*.py',
    'analyze_*.py',
    'check_*.py',
    'copy_*.py',
    'comprehensive_*.py',
    'find_*.py',
    'fix_*.py',
    'populate_september_*.py',
    'quick_*.py',
    'final_september_*.py',
]

# Files to keep (not September-related)
keep_files = [
    'check_periods.py',
    'check_sales_by_period.py',
]

print("=" * 80)
print("CLEANING UP TEMPORARY SEPTEMBER STOCKTAKE SCRIPTS")
print("=" * 80)
print()

files_to_delete = []

for pattern in patterns:
    matches = glob.glob(os.path.join(root, pattern))
    for file_path in matches:
        filename = os.path.basename(file_path)
        if filename not in keep_files:
            files_to_delete.append(file_path)

# Remove duplicates and sort
files_to_delete = sorted(set(files_to_delete))

print(f"Found {len(files_to_delete)} temporary files to delete:")
print("-" * 80)

for file_path in files_to_delete:
    filename = os.path.basename(file_path)
    print(f"  {filename}")

print()
response = input("Delete these files? (yes/no): ")

if response.lower() == 'yes':
    deleted = 0
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            deleted += 1
        except Exception as e:
            print(f"✗ Error deleting {os.path.basename(file_path)}: {e}")
    
    print()
    print(f"✅ Deleted {deleted} files successfully!")
else:
    print()
    print("❌ Cleanup cancelled.")

print()
print("=" * 80)
