"""
Test voice command parsing for "5 cases 5 bottles"
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from voice_recognition.command_parser import parse_voice_command

# Test the specific case
test_commands = [
    "count budweiser 5 cases 5 bottles",
    "count budweiser bottle 5 cases 5 bottles",
    "count heineken 3 cases 6 bottles",
    "count guinness 2 kegs 20 pints",
]

print("\n" + "="*70)
print("TESTING: Full + Partial Unit Parsing")
print("="*70 + "\n")

for cmd in test_commands:
    print(f"Command: '{cmd}'")
    try:
        result = parse_voice_command(cmd)
        print(f"✓ Action: {result['action']}")
        print(f"✓ Item: {result['item_identifier']}")
        print(f"✓ Full Units: {result.get('full_units', 'N/A')}")
        print(f"✓ Partial Units: {result.get('partial_units', 'N/A')}")
        print(f"✓ Value: {result.get('value', 'N/A')}")
        print()
        
        # Verify correct parsing
        if 'full_units' in result and 'partial_units' in result:
            print(f"  ℹ️  Backend will calculate:")
            print(f"  counted_qty = (full_units × uom) + partial_units")
            
            if "cases" in cmd:
                uom = 12
                calculated = (result['full_units'] * uom) + result['partial_units']
                print(f"  Example (UOM=12): ({result['full_units']} × 12) + {result['partial_units']} = {calculated} bottles")
            elif "kegs" in cmd:
                uom = 88
                calculated = (result['full_units'] * uom) + result['partial_units']
                print(f"  Example (UOM=88): ({result['full_units']} × 88) + {result['partial_units']} = {calculated} pints")
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")

print("="*70)
