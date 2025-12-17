#!/usr/bin/env python
"""
Check for party_members model field references in source code
"""

import os
import sys
import django
import re

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

def find_party_members_references():
    """Find all .party_members references in Python files"""
    pattern = re.compile(r'\.party_members\b')
    found = []
    
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['venv', '__pycache__', '.git', 'node_modules']):
            continue
            
        for file in files:
            if file.endswith('.py') and 'check_party_members.py' not in file:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = pattern.finditer(content)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            line = content.split('\n')[line_num - 1].strip()
                            found.append((filepath, line_num, line))
                except Exception as e:
                    pass
    
    return found

def check_booking_serializers():
    """Check specific booking_serializers content"""
    try:
        import inspect
        from hotel import booking_serializers
        source = inspect.getsource(booking_serializers)
        
        # Check for party_members references
        if 'party_members' in source:
            print("❌ booking_serializers still contains 'party_members'")
            
            # Find specific lines
            lines = source.split('\n')
            for i, line in enumerate(lines):
                if 'party_members' in line:
                    print(f"  Line {i+1}: {line.strip()}")
            return False
        else:
            print("✅ booking_serializers clean of party_members")
            return True
            
    except Exception as e:
        print(f"❌ Error checking booking_serializers: {e}")
        return False

if __name__ == '__main__':
    print("🔍 Searching for .party_members model field references...")
    
    references = find_party_members_references()
    
    if references:
        print(f"❌ Found {len(references)} .party_members references:")
        for filepath, line_num, line in references:
            print(f"  {filepath}:{line_num} - {line}")
    else:
        print("✅ No .party_members model field references found")
    
    print("\n🔍 Checking booking_serializers specifically...")
    serializers_clean = check_booking_serializers()
    
    if not references and serializers_clean:
        print("\n✅ ALL CLEAR - No party_members model references found!")
    else:
        print("\n❌ Issues found - party_members still present")