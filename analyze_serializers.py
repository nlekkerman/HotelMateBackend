import re

with open('hotel/serializers.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Find all serializer classes
pattern = r'class (\w+Serializer)\('
matches = re.findall(pattern, content)

print(f"Total Serializers Found: {len(matches)}\n")
for i, name in enumerate(matches, 1):
    print(f"{i}. {name}")
